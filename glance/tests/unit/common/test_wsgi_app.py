# -*- coding: utf-8 -*-
# Copyright 2020, Red Hat, Inc.
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

from unittest import mock

from glance.api import common
from glance.api.v2 import cached_images
import glance.async_
from glance.common import exception
from glance.common import wsgi_app
from glance.tests import utils as test_utils


class TestWsgiAppInit(test_utils.BaseTestCase):
    @mock.patch('glance.common.config.load_paste_app')
    @mock.patch('glance.async_.set_threadpool_model')
    @mock.patch('glance.common.wsgi_app._get_config_files')
    def test_wsgi_init_sets_thread_settings(self, mock_config_files,
                                            mock_set_model,
                                            mock_load):
        mock_config_files.return_value = []
        self.config(task_pool_threads=123, group='wsgi')
        common.DEFAULT_POOL_SIZE = 1024
        wsgi_app.init_app()
        # Make sure we declared the system threadpool model as native
        mock_set_model.assert_called_once_with('native')
        # Make sure we set the default pool size
        self.assertEqual(123, common.DEFAULT_POOL_SIZE)
        mock_load.assert_called_once_with('glance-api')

    @mock.patch('atexit.register')
    @mock.patch('glance.common.config.load_paste_app')
    @mock.patch('glance.async_.set_threadpool_model')
    @mock.patch('glance.common.wsgi_app._get_config_files')
    def test_wsgi_init_registers_exit_handler(self, mock_config_files,
                                              mock_set_model,
                                              mock_load, mock_exit):
        mock_config_files.return_value = []
        wsgi_app.init_app()
        mock_exit.assert_called_once_with(wsgi_app.drain_workers)

    @mock.patch('glance.common.config.load_paste_app')
    @mock.patch('glance.async_.set_threadpool_model')
    @mock.patch('glance.common.wsgi_app._get_config_files')
    def test_uwsgi_init_registers_exit_handler(self, mock_config_files,
                                               mock_set_model,
                                               mock_load):
        mock_config_files.return_value = []
        with mock.patch.object(wsgi_app, 'uwsgi') as mock_u:
            wsgi_app.init_app()
            self.assertEqual(mock_u.atexit, wsgi_app.drain_workers)

    @mock.patch('glance.api.v2.cached_images.WORKER')
    @mock.patch('glance.async_._THREADPOOL_MODEL', new=None)
    def test_drain_workers(self, mock_cache_worker):
        # Initialize the thread pool model and tasks_pool, like API
        # under WSGI would, and so we have a pointer to that exact
        # pool object in the cache
        glance.async_.set_threadpool_model('native')
        model = common.get_thread_pool('tasks_pool')

        with mock.patch.object(model.pool, 'shutdown') as mock_shutdown:
            wsgi_app.drain_workers()
            # Make sure that shutdown() was called on the tasks_pool
            # ThreadPoolExecutor
            mock_shutdown.assert_called_once_with()

            # Make sure we terminated the cache worker, if present.
            mock_cache_worker.terminate.assert_called_once_with()

    @mock.patch('glance.async_._THREADPOOL_MODEL', new=None)
    def test_drain_workers_no_cache(self):
        glance.async_.set_threadpool_model('native')
        model = common.get_thread_pool('tasks_pool')

        with mock.patch.object(model.pool, 'shutdown'):
            # Make sure that with no WORKER initialized, we do not fail
            wsgi_app.drain_workers()
            self.assertIsNone(cached_images.WORKER)

    @mock.patch('glance.common.config.load_paste_app')
    @mock.patch('glance.async_.set_threadpool_model')
    @mock.patch('glance.common.wsgi_app._get_config_files')
    def test_policy_enforcement_kills_service_if_misconfigured(
            self, mock_load_app, mock_set, mock_config_files):
        self.config(enforce_new_defaults=True, group='oslo_policy')
        self.config(enforce_secure_rbac=False)
        self.assertRaises(exception.ServerError, wsgi_app.init_app)

        self.config(enforce_new_defaults=False, group='oslo_policy')
        self.config(enforce_secure_rbac=True)
        self.assertRaises(exception.ServerError, wsgi_app.init_app)

    @mock.patch('glance.common.config.load_paste_app')
    @mock.patch('glance.async_.set_threadpool_model')
    @mock.patch('glance.common.wsgi_app._get_config_files')
    def test_policy_enforcement_valid_truthy_configuration(
            self, mock_load_app, mock_set, mock_config_files):
        self.config(enforce_new_defaults=True, group='oslo_policy')
        self.config(enforce_secure_rbac=True)
        self.assertTrue(wsgi_app.init_app())

    @mock.patch('glance.common.config.load_paste_app')
    @mock.patch('glance.async_.set_threadpool_model')
    @mock.patch('glance.common.wsgi_app._get_config_files')
    def test_policy_enforcement_valid_falsy_configuration(
            self, mock_load_app, mock_set, mock_config_files):
        # This is effectively testing the default values, but we're doing that
        # to make sure nothing bad happens at runtime in the default case when
        # validating policy enforcement configuration.
        self.config(enforce_new_defaults=False, group='oslo_policy')
        self.config(enforce_secure_rbac=False)
        self.assertTrue(wsgi_app.init_app())

    @mock.patch('glance.async_._THREADPOOL_MODEL', new=None)
    @mock.patch('glance.common.config.load_paste_app')
    @mock.patch('glance.common.wsgi_app._get_config_files')
    @mock.patch('threading.Thread')
    @mock.patch('glance.housekeeping.StagingStoreCleaner')
    def test_runs_staging_cleanup(self, mock_cleaner, mock_Thread, mock_conf,
                                  mock_load):
        mock_conf.return_value = []
        wsgi_app.init_app()
        mock_Thread.assert_called_once_with(
            target=mock_cleaner().clean_orphaned_staging_residue,
            daemon=True)
        mock_Thread.return_value.start.assert_called_once_with()

    @mock.patch('glance.async_._THREADPOOL_MODEL', new=None)
    @mock.patch('glance.common.config.load_paste_app')
    @mock.patch('glance.common.wsgi_app._get_config_files')
    @mock.patch('threading.Timer')
    @mock.patch('glance.image_cache.prefetcher.Prefetcher')
    def test_run_cache_prefetcher_middleware_disabled(
            self, mock_prefetcher, mock_Timer, mock_conf, mock_load):
        mock_conf.return_value = []
        wsgi_app.init_app()
        mock_Timer.assert_not_called()

    @mock.patch('glance.common.wsgi_app._get_config_files')
    @mock.patch('glance.async_._THREADPOOL_MODEL', new=None)
    @mock.patch('glance.common.config.load_paste_app', new=mock.MagicMock())
    def test_staging_store_uri_assertion(self, mock_conf):
        self.config(node_staging_uri='http://good.luck')
        mock_conf.return_value = []
        # Make sure a staging URI with a bad scheme will abort startup
        self.assertRaises(exception.GlanceException, wsgi_app.init_app)

    @mock.patch('glance.common.wsgi_app._get_config_files')
    @mock.patch('glance.async_._THREADPOOL_MODEL', new=None)
    @mock.patch('glance.common.config.load_paste_app', new=mock.MagicMock())
    @mock.patch('os.path.exists')
    def test_staging_store_path_check(self, mock_exists, mock_conf):
        mock_exists.return_value = False
        mock_conf.return_value = []
        with mock.patch.object(wsgi_app, 'LOG') as mock_log:
            wsgi_app.init_app()
            # Make sure that a missing staging directory will log a warning.
            mock_log.warning.assert_called_once_with(
                'Import methods are enabled but staging directory '
                '%(path)s does not exist; Imports will fail!',
                {'path': '/tmp/staging/'})
