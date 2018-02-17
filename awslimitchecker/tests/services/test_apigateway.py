"""
awslimitchecker/tests/services/test_apigateway.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2015-2018 Jason Antman <jason@jasonantman.com>

    This file is part of awslimitchecker, also known as awslimitchecker.

    awslimitchecker is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    awslimitchecker is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with awslimitchecker.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)
################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/awslimitchecker> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

import sys
from copy import deepcopy
from awslimitchecker.tests.services import result_fixtures
from awslimitchecker.services.apigateway import _ApigatewayService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT


pbm = 'awslimitchecker.services.apigateway'  # module patch base
pb = '%s._ApigatewayService' % pbm  # class patch pase


class Test_ApigatewayService(object):

    def test_init(self):
        """test __init__()"""
        cls = _ApigatewayService(21, 43)
        assert cls.service_name == 'ApiGateway'
        assert cls.api_name == 'apigateway'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _ApigatewayService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'API keys per account',
            'APIs per account',
            'Client certificates per account',
            'Custom authorizers per API',
            'Documentation parts per API',
            'Resources per API',
            'Stages per API',
            'Usage plans per account'
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _ApigatewayService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        mock_conn = Mock()
        with patch('%s.connect' % pb) as mock_connect:
            with patch.multiple(
                pb,
                autospec=True,
                _find_usage_apis=DEFAULT,
                _find_usage_api_keys=DEFAULT,
                _find_usage_certs=DEFAULT,
                _find_usage_plans=DEFAULT
            ) as mocks:
                cls = _ApigatewayService(21, 43)
                cls.conn = mock_conn
                assert cls._have_usage is False
                cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        assert mock_conn.mock_calls == []
        assert mocks['_find_usage_apis'].mock_calls == [call(cls)]
        assert mocks['_find_usage_api_keys'].mock_calls == [call(cls)]
        assert mocks['_find_usage_certs'].mock_calls == [call(cls)]
        assert mocks['_find_usage_plans'].mock_calls == [call(cls)]

    def test_find_usage_apis(self):
        mock_conn = Mock()
        res = result_fixtures.ApiGateway.get_rest_apis
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = res

        def se_res_paginate(restApiId=None):
            return result_fixtures.ApiGateway.get_resources[restApiId]

        mock_res_paginator = Mock()
        mock_res_paginator.paginate.side_effect = se_res_paginate

        def se_get_paginator(api_name):
            if api_name == 'get_rest_apis':
                return mock_paginator
            elif api_name == 'get_resources':
                return mock_res_paginator

        def se_paginate_dict(*args, **kwargs):
            if args[0] == mock_conn.get_documentation_parts:
                return result_fixtures.ApiGateway.doc_parts[kwargs['restApiId']]
            if args[0] == mock_conn.get_authorizers:
                return result_fixtures.ApiGateway.authorizers[
                    kwargs['restApiId']
                ]

        def se_get_stages(restApiId=None):
            return result_fixtures.ApiGateway.stages[restApiId]

        mock_conn.get_paginator.side_effect = se_get_paginator
        mock_conn.get_stages.side_effect = se_get_stages
        cls = _ApigatewayService(21, 43)
        cls.conn = mock_conn
        with patch('%s.paginate_dict' % pbm, autospec=True) as mock_pd:
            with patch('%s.logger' % pbm) as mock_logger:
                mock_pd.side_effect = se_paginate_dict
                cls._find_usage_apis()
        # APIs usage
        usage = cls.limits['APIs per account'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 3
        # Resources usage
        usage = cls.limits['Resources per API'].get_current_usage()
        assert len(usage) == 3
        assert usage[0].resource_id == 'api3'
        assert usage[0].get_value() == 0
        assert usage[1].resource_id == 'api2'
        assert usage[1].get_value() == 2
        assert usage[2].resource_id == 'api1'
        assert usage[2].get_value() == 3
        usage = cls.limits['Documentation parts per API'].get_current_usage()
        assert len(usage) == 3
        assert usage[0].resource_id == 'api3'
        assert usage[0].get_value() == 2
        assert usage[1].resource_id == 'api2'
        assert usage[1].get_value() == 1
        assert usage[2].resource_id == 'api1'
        assert usage[2].get_value() == 4
        usage = cls.limits['Stages per API'].get_current_usage()
        assert len(usage) == 3
        assert usage[0].resource_id == 'api3'
        assert usage[0].get_value() == 2
        assert usage[1].resource_id == 'api2'
        assert usage[1].get_value() == 1
        assert usage[2].resource_id == 'api1'
        assert usage[2].get_value() == 3
        usage = cls.limits['Custom authorizers per API'].get_current_usage()
        assert len(usage) == 3
        assert usage[0].resource_id == 'api3'
        assert usage[0].get_value() == 0
        assert usage[1].resource_id == 'api2'
        assert usage[1].get_value() == 2
        assert usage[2].resource_id == 'api1'
        assert usage[2].get_value() == 1
        assert mock_conn.mock_calls == [
            call.get_paginator('get_rest_apis'),
            call.get_paginator('get_resources'),
            call.get_stages(restApiId='api3'),
            call.get_paginator('get_resources'),
            call.get_stages(restApiId='api2'),
            call.get_paginator('get_resources'),
            call.get_stages(restApiId='api1')
        ]
        assert mock_paginator.mock_calls == [call.paginate()]
        assert mock_res_paginator.mock_calls == [
            call.paginate(restApiId='api3'),
            call.paginate(restApiId='api2'),
            call.paginate(restApiId='api1')
        ]
        assert mock_pd.mock_calls == [
            call(
                mock_conn.get_documentation_parts,
                restApiId='api3',
                alc_marker_path=['position'],
                alc_data_path=['items'],
                alc_marker_param='position'
            ),
            call(
                mock_conn.get_authorizers,
                restApiId='api3',
                alc_marker_path=['position'],
                alc_data_path=['items'],
                alc_marker_param='position'
            ),
            call(
                mock_conn.get_documentation_parts,
                restApiId='api2',
                alc_marker_path=['position'],
                alc_data_path=['items'],
                alc_marker_param='position'
            ),
            call(
                mock_conn.get_authorizers,
                restApiId='api2',
                alc_marker_path=['position'],
                alc_data_path=['items'],
                alc_marker_param='position'
            ),
            call(
                mock_conn.get_documentation_parts,
                restApiId='api1',
                alc_marker_path=['position'],
                alc_data_path=['items'],
                alc_marker_param='position'
            ),
            call(
                mock_conn.get_authorizers,
                restApiId='api1',
                alc_marker_path=['position'],
                alc_data_path=['items'],
                alc_marker_param='position'
            ),
        ]
        assert mock_logger.mock_calls == [
            call.debug('Finding usage for APIs'),
            call.debug('Found %d APIs', 3),
            call.debug('Finding usage for per-API limits')
        ]

    def test_find_usage_apis_stages_now_paginated(self):
        mock_conn = Mock()
        res = result_fixtures.ApiGateway.get_rest_apis
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = res

        def se_res_paginate(restApiId=None):
            return result_fixtures.ApiGateway.get_resources[restApiId]

        mock_res_paginator = Mock()
        mock_res_paginator.paginate.side_effect = se_res_paginate

        def se_get_paginator(api_name):
            if api_name == 'get_rest_apis':
                return mock_paginator
            elif api_name == 'get_resources':
                return mock_res_paginator

        def se_paginate_dict(*args, **kwargs):
            if args[0] == mock_conn.get_documentation_parts:
                return result_fixtures.ApiGateway.doc_parts[kwargs['restApiId']]
            if args[0] == mock_conn.get_authorizers:
                return result_fixtures.ApiGateway.authorizers[
                    kwargs['restApiId']
                ]

        def se_get_stages(restApiId=None):
            r = deepcopy(result_fixtures.ApiGateway.stages[restApiId])
            r['position'] = 'foo'
            return r

        mock_conn.get_paginator.side_effect = se_get_paginator
        mock_conn.get_stages.side_effect = se_get_stages
        cls = _ApigatewayService(21, 43)
        cls.conn = mock_conn
        with patch('%s.paginate_dict' % pbm, autospec=True) as mock_pd:
            with patch('%s.logger' % pbm) as mock_logger:
                mock_pd.side_effect = se_paginate_dict
                cls._find_usage_apis()
        assert mock_logger.mock_calls == [
            call.debug('Finding usage for APIs'),
            call.debug('Found %d APIs', 3),
            call.debug('Finding usage for per-API limits'),
            call.warning(
                'APIGateway get_stages returned more keys than present in '
                'boto3 docs: %s', ['item', 'position']
            )
        ]

    def test_find_usage_plans(self):
        mock_conn = Mock()
        res = result_fixtures.ApiGateway.plans
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = res

        mock_conn.get_paginator.return_value = mock_paginator
        cls = _ApigatewayService(21, 43)
        cls.conn = mock_conn
        with patch('%s.logger' % pbm) as mock_logger:
            cls._find_usage_plans()
        # APIs usage
        usage = cls.limits['Usage plans per account'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 4
        assert mock_conn.mock_calls == [
            call.get_paginator('get_usage_plans'),
            call.get_paginator().paginate()
        ]
        assert mock_paginator.mock_calls == [call.paginate()]
        assert mock_logger.mock_calls == [
            call.debug('Finding usage for Usage Plans')
        ]

    def test_find_usage_certs(self):
        mock_conn = Mock()
        res = result_fixtures.ApiGateway.certs
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = res

        mock_conn.get_paginator.return_value = mock_paginator
        cls = _ApigatewayService(21, 43)
        cls.conn = mock_conn
        with patch('%s.logger' % pbm) as mock_logger:
            cls._find_usage_certs()
        # APIs usage
        usage = cls.limits[
            'Client certificates per account'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 2
        assert mock_conn.mock_calls == [
            call.get_paginator('get_client_certificates'),
            call.get_paginator().paginate()
        ]
        assert mock_paginator.mock_calls == [call.paginate()]
        assert mock_logger.mock_calls == [
            call.debug('Finding usage for Client Certificates')
        ]

    def test_find_usage_api_keys(self):
        mock_conn = Mock()
        res = result_fixtures.ApiGateway.api_keys
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = res

        mock_conn.get_paginator.return_value = mock_paginator
        cls = _ApigatewayService(21, 43)
        cls.conn = mock_conn
        with patch('%s.logger' % pbm) as mock_logger:
            cls._find_usage_api_keys()
        # API Keys usage
        usage = cls.limits[
            'API keys per account'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 4
        assert mock_conn.mock_calls == [
            call.get_paginator('get_api_keys'),
            call.get_paginator().paginate()
        ]
        assert mock_paginator.mock_calls == [call.paginate()]
        assert mock_logger.mock_calls == [
            call.debug('Finding usage for API Keys')
        ]

    def test_required_iam_permissions(self):
        cls = _ApigatewayService(21, 43)
        assert cls.required_iam_permissions() == [
            "apigateway:GET",
            "apigateway:HEAD",
            "apigateway:OPTIONS"
        ]
