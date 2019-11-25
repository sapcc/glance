#    Copyright 2014 IBM Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import sys

import glance_store as store_api
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import encodeutils
import six.moves.urllib.parse as urlparse

import glance.db as db_api
from glance.i18n import _LE, _LW
from glance import scrubber

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
CONF.import_opt('use_user_token', 'glance.registry.client')

RESTRICTED_URI_SCHEMAS = frozenset(['file', 'filesystem', 'swift+config'])


def check_reserved_stores(enabled_stores):
    for store in enabled_stores:
        if store.startswith("os_glance_"):
            return True
    return False


def safe_delete_from_backend(context, image_id, location):
    """
    Given a location, delete an image from the store and
    update location status to db.

    This function try to handle all known exceptions which might be raised
    by those calls on store and DB modules in its implementation.

    :param context: The request context
    :param image_id: The image identifier
    :param location: The image location entry
    """

    try:
        if CONF.enabled_backends:
            backend = location['metadata'].get('store')
            ret = store_api.delete(location['url'],
                                   backend,
                                   context=context)
        else:
            ret = store_api.delete_from_backend(location['url'],
                                                context=context)

        location['status'] = 'deleted'
        if 'id' in location:
            db_api.get_api().image_location_delete(context, image_id,
                                                   location['id'], 'deleted')
        return ret
    except store_api.NotFound:
        msg = _LW('Failed to delete image %s in store from URI') % image_id
        LOG.warn(msg)
    except store_api.StoreDeleteNotSupported as e:
        LOG.warn(encodeutils.exception_to_unicode(e))
    except store_api.UnsupportedBackend:
        exc_type = sys.exc_info()[0].__name__
        msg = (_LE('Failed to delete image %(image_id)s from store: %(exc)s') %
               dict(image_id=image_id, exc=exc_type))
        LOG.error(msg)


def schedule_delayed_delete_from_backend(context, image_id, location):
    """
    Given a location, schedule the deletion of an image location and
    update location status to db.

    :param context: The request context
    :param image_id: The image identifier
    :param location: The image location entry
    """

    db_queue = scrubber.get_scrub_queue()

    if not CONF.use_user_token:
        context = None

    ret = db_queue.add_location(image_id, location)
    if ret:
        location['status'] = 'pending_delete'
        if 'id' in location:
            # NOTE(zhiyan): New added image location entry will has no 'id'
            # field since it has not been saved to DB.
            db_api.get_api().image_location_delete(context, image_id,
                                                   location['id'],
                                                   'pending_delete')
        else:
            db_api.get_api().image_location_add(context, image_id, location)

    return ret


def delete_image_location_from_backend(context, image_id, location):
    """
    Given a location, immediately or schedule the deletion of an image
    location and update location status to db.

    :param context: The request context
    :param image_id: The image identifier
    :param location: The image location entry
    """

    deleted = False
    if CONF.delayed_delete:
        deleted = schedule_delayed_delete_from_backend(context,
                                                       image_id, location)
    if not deleted:
        # NOTE(zhiyan) If image metadata has not been saved to DB
        # such as uploading process failure then we can't use
        # location status mechanism to support image pending delete.
        safe_delete_from_backend(context, image_id, location)


def validate_external_location(uri):
    """
    Validate if URI of external location are supported.

    Only over non-local store types are OK, i.e. Swift,
    HTTP. Note the absence of 'file://' for security reasons,
    see LP bug #942118, 1400966, 'swift+config://' is also
    absent for security reasons, see LP bug #1334196.

    :param uri: The URI of external image location.
    :returns: Whether given URI of external image location are OK.
    """
    if not uri:
        return False

    # TODO(zhiyan): This function could be moved to glance_store.
    # TODO(gm): Use a whitelist of allowed schemes
    scheme = urlparse.urlparse(uri).scheme
    known_schemes = store_api.get_known_schemes()
    if CONF.enabled_backends:
        known_schemes = store_api.get_known_schemes_for_multi_store()

    return (scheme in known_schemes and
            scheme not in RESTRICTED_URI_SCHEMAS)


def _get_store_id_from_uri(uri):
    scheme = urlparse.urlparse(uri).scheme
    location_map = store_api.location.SCHEME_TO_CLS_BACKEND_MAP
    url_matched = False
    if scheme not in location_map:
        LOG.warning("Unknown scheme '%(scheme)s' found in uri '%(uri)s'", {
            'scheme': scheme, 'uri': uri})
        return
    for store in location_map[scheme]:
        store_instance = location_map[scheme][store]['store']
        url_prefix = store_instance.url_prefix
        if url_prefix and uri.startswith(url_prefix):
            url_matched = True
            break

    if url_matched:
        return store
    else:
        LOG.warning("Invalid location uri %s", uri)
        return


def update_store_in_locations(locations, image_id):
    for loc in locations:
        store_id = _get_store_id_from_uri(loc['url'])
        if store_id:
            if 'store' in loc['metadata']:
                old_store = loc['metadata']['store']
                if old_store != store_id:
                    LOG.debug("Store '%(old)s' has changed to "
                              "'%(new)s' by operator, updating "
                              "the same in the location of image "
                              "'%(id)s'", {'old': old_store,
                                           'new': store_id,
                                           'id': image_id})

            loc['metadata']['store'] = store_id
