# Copyright 2026 OpenStack Foundation
# All Rights Reserved.
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

"""Utilities for domain-scoped image visibility.

This module provides functionality to resolve project-to-domain mappings
and check domain membership for domain-scoped image visibility.
"""

from oslo_cache import core as cache
from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

# Cache configuration for domain lookups
CACHE_REGION = None

domain_opts = [
    cfg.IntOpt('domain_cache_time',
               default=300,
               help='Time in seconds to cache project-to-domain mappings. '
                    'Set to 0 to disable caching.'),
    cfg.BoolOpt('domain_visibility_enabled',
                default=True,
                help='Enable domain-scoped image visibility feature.'),
]

CONF.register_opts(domain_opts)


def _get_cache_region():
    """Get or create the cache region for domain lookups."""
    global CACHE_REGION
    if CACHE_REGION is None:
        CACHE_REGION = cache.create_region()
        cache.configure_cache_region(CONF, CACHE_REGION)
    return CACHE_REGION


class DomainResolver:
    """Resolves project-to-domain mappings with caching.

    This class provides methods to determine domain membership for projects,
    which is used to enforce domain-scoped image visibility.
    """

    def __init__(self, context):
        """Initialize the DomainResolver.

        :param context: The request context containing authentication info
        """
        self.context = context
        self._keystone_client = None
        self._domain_cache = {}

    @property
    def keystone_client(self):
        """Lazy-load the Keystone client."""
        if self._keystone_client is None:
            from keystoneauth1 import session
            from keystoneauth1 import token_endpoint
            from keystoneclient.v3 import client as ks_client

            auth = token_endpoint.Token(
                CONF.keystone_authtoken.identity_uri,
                self.context.auth_token
            )
            sess = session.Session(auth=auth)
            self._keystone_client = ks_client.Client(session=sess)
        return self._keystone_client

    def get_project_domain_id(self, project_id):
        """Get the domain_id for a given project_id.

        This method first checks the request context for domain information,
        then falls back to querying Keystone if needed.

        :param project_id: The project ID to look up
        :returns: The domain ID for the project, or None if not found
        """
        # Check if this is the current project and we have domain info
        if (project_id == self.context.project_id and
                hasattr(self.context, 'project_domain_id') and
                self.context.project_domain_id):
            return self.context.project_domain_id

        # Check local cache
        if project_id in self._domain_cache:
            return self._domain_cache[project_id]

        # Query Keystone
        try:
            project = self.keystone_client.projects.get(project_id)
            domain_id = project.domain_id
            self._domain_cache[project_id] = domain_id
            LOG.debug("Resolved project %s to domain %s",
                      project_id, domain_id)
            return domain_id
        except Exception as e:
            LOG.warning("Failed to resolve domain for project %s: %s",
                        project_id, e)
            return None

    def get_requester_domain_id(self):
        """Get the domain ID of the requesting project.

        :returns: The domain ID of the requester's project
        """
        # First try to get from context directly
        if (hasattr(self.context, 'project_domain_id') and
                self.context.project_domain_id):
            return self.context.project_domain_id

        # Fall back to looking up the project
        if self.context.project_id:
            return self.get_project_domain_id(self.context.project_id)

        return None

    def is_same_domain(self, project_id_1, project_id_2):
        """Check if two projects belong to the same domain.

        :param project_id_1: First project ID
        :param project_id_2: Second project ID
        :returns: True if both projects are in the same domain
        """
        if not project_id_1 or not project_id_2:
            return False

        domain_1 = self.get_project_domain_id(project_id_1)
        domain_2 = self.get_project_domain_id(project_id_2)

        if not domain_1 or not domain_2:
            return False

        return domain_1 == domain_2

    def can_access_domain_image(self, image_owner, requester_project=None):
        """Check if requester can access a domain-scoped image.

        A user can access a domain-scoped image if:
        1. They are an admin
        2. They own the image
        3. Their project is in the same domain as the image owner's project

        :param image_owner: The project ID that owns the image
        :param requester_project: The project ID of the requester
                                  (defaults to context.project_id)
        :returns: True if the requester can access the image
        """
        if not CONF.domain_visibility_enabled:
            LOG.debug("Domain visibility is disabled")
            return False

        # Admins can access all images
        if self.context.is_admin:
            return True

        requester = requester_project or self.context.project_id

        # Owner can always access their own images
        if image_owner == requester:
            return True

        # Check if both projects are in the same domain
        return self.is_same_domain(image_owner, requester)


def check_domain_access(context, image_owner):
    """Convenience function to check domain access.

    :param context: The request context
    :param image_owner: The project ID that owns the image
    :returns: True if the requester can access the domain-scoped image
    """
    resolver = DomainResolver(context)
    return resolver.can_access_domain_image(image_owner)


def get_domain_id_for_project(context, project_id):
    """Convenience function to get domain ID for a project.

    :param context: The request context
    :param project_id: The project ID to look up
    :returns: The domain ID for the project
    """
    resolver = DomainResolver(context)
    return resolver.get_project_domain_id(project_id)