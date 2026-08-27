# Copyright 2026 SAP SE
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

from oslo_config import cfg

from glance.common import trust_auth
import glance.tests.utils as test_utils


class TestTrustAuthSessionOpts(test_utils.BaseTestCase):
    """Test session option registration for the trustee client"""

    def test_register_skips_options_already_registered(self):
        """
        Test that registering session options skips options that are already
        registered
        """
        conf = cfg.ConfigOpts()
        # Simulate pre-existing session option registered by keystonemiddleware
        conf.register_opt(cfg.StrOpt('cafile', default='sentinel'),
                          group='keystone_authtoken')
        conf([])
        with mock.patch.object(trust_auth, 'CONF', conf):
            trust_auth._register_session_conf_opts()
        # The pre-existing definition is retained
        self.assertEqual('sentinel', conf.keystone_authtoken.cafile)

    @mock.patch.object(trust_auth, 'ks_client')
    @mock.patch.object(trust_auth.ka_loading, 'load_auth_from_conf_options')
    def test_token_refresher_init_registers_session_options(
            self, mock_load_auth, mock_ks_client):
        """
        Test that TokenRefresher initialization registers session options
        """
        conf = cfg.ConfigOpts()
        conf([])
        with mock.patch.object(trust_auth, 'CONF', conf):
            refresher = trust_auth.TokenRefresher(
                mock.Mock(), 'project-id', ['member'])
        self.assertIsNone(refresher.trustee_client)
        # Assert that session option 'timeout' is registered
        conf.keystone_authtoken.timeout
