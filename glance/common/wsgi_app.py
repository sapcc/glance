# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

import glance_store
from oslo_config import cfg
from oslo_log import log as logging
import osprofiler.initializer

from glance.common import config
from glance.common import store_utils
from glance import notifier

CONF = cfg.CONF
CONF.import_group("profiler", "glance.common.wsgi")
CONF.import_opt("enabled_backends", "glance.common.wsgi")
logging.register_options(CONF)

CONFIG_FILES = ['glance-api-paste.ini',
                'glance-image-import.conf',
                'glance-api.conf']

# Reserved file stores for staging and tasks operations
RESERVED_STORES = {
    'os_glance_staging_store': 'file',
    'os_glance_tasks_store': 'file'
}


def _get_config_files(env=None):
    if env is None:
        env = os.environ
    dirname = env.get('OS_GLANCE_CONFIG_DIR', '/etc/glance').strip()
    config_files = []
    for config_file in CONFIG_FILES:
        cfg_file = os.path.join(dirname, config_file)
        # As 'glance-image-import.conf' is optional conf file
        # so include it only if it's existing.
        if config_file == 'glance-image-import.conf' and (
                not os.path.exists(cfg_file)):
            continue
        config_files.append(cfg_file)

    return config_files


def _setup_os_profiler():
    notifier.set_defaults()
    if CONF.profiler.enabled:
        osprofiler.initializer.init_from_conf(conf=CONF,
                                              context={},
                                              project='glance',
                                              service='api',
                                              host=CONF.bind_host)


def init_app():
    config_files = _get_config_files()
    CONF([], project='glance', default_config_files=config_files)
    logging.setup(CONF, "glance")

    if CONF.enabled_backends:
        if store_utils.check_reserved_stores(CONF.enabled_backends):
            msg = _("'os_glance_' prefix should not be used in "
                    "enabled_backends config option. It is reserved "
                    "for internal use only.")
            raise RuntimeError(msg)
        glance_store.register_store_opts(CONF, reserved_stores=RESERVED_STORES)
        glance_store.create_multi_stores(CONF, reserved_stores=RESERVED_STORES)
        glance_store.verify_store()
    else:
        glance_store.register_opts(CONF)
        glance_store.create_stores(CONF)
        glance_store.verify_default_store()

    _setup_os_profiler()
    return config.load_paste_app('glance-api')
