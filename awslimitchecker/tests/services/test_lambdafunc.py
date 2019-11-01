"""
awslimitchecker/tests/services/test_lambdafunc.py

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
from awslimitchecker.tests.services import result_fixtures
from awslimitchecker.services.lambdafunc import _LambdaService
from botocore.exceptions import EndpointConnectionError

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock


pbm = 'awslimitchecker.services.lambdafunc'  # class patch base
pb = '%s._LambdaService' % pbm  # class patch pase


class Test_LambdaService(object):

    def test_init(self):
        """test __init__()"""
        cls = _LambdaService(21, 43, {}, None)
        assert cls.service_name == 'Lambda'
        assert cls.api_name == 'lambda'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _LambdaService(21, 43, {}, None)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == [
            'Code Size Unzipped (MiB) per Function',
            'Code Size Zipped (MiB) per Function',
            'Concurrent Executions',
            'Function Count',
            'Total Code Size (MiB)',
            'Unreserved Concurrent Executions'
        ]
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _LambdaService(21, 43, {}, None)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_update_limits_from_api(self):
        response = result_fixtures.Lambda.test_lambda_response
        mock_conn = Mock()
        mock_conn.get_account_settings.return_value = response

        with patch('%s.connect' % pb) as mock_connect:
            cls = _LambdaService(21, 43, {}, None)
            assert len(cls.limits) == 6
            cls.conn = mock_conn
            cls._update_limits_from_api()

        assert mock_connect.mock_calls == [call()]
        assert mock_conn.mock_calls == [call.get_account_settings()]
        assert len(cls.limits) == 6
        lim = cls.limits['Code Size Unzipped (MiB) per Function'].get_limit()
        assert lim == 250
        lim = cls.limits['Code Size Zipped (MiB) per Function'].get_limit()
        assert lim == 50
        lim = cls.limits['Total Code Size (MiB)'].get_limit()
        assert lim == 76800
        lim = cls.limits['Unreserved Concurrent Executions'].get_limit()
        assert lim == 1000
        lim = cls.limits['Concurrent Executions'].get_limit()
        assert lim == 1000

    def test_update_limits_from_api_exit_early(self):
        response = result_fixtures.Lambda.test_lambda_response
        mock_conn = Mock()
        mock_conn.get_account_settings.return_value = response

        with patch('%s.connect' % pb) as mock_connect:
            cls = _LambdaService(21, 43, {}, None)
            assert len(cls.limits) == 6
            cls.limits = {"a": None, "b": None}
            cls.conn = mock_conn
            cls._update_limits_from_api()
        assert mock_connect.mock_calls == []

    def test_find_usage_connection_fail(self):
        def conn_err():
            raise EndpointConnectionError(endpoint_url='myurl')

        mock_conn = Mock()
        mock_conn.get_account_settings.side_effect = conn_err

        with patch('%s.connect' % pb) as mock_connect:
            with patch('%s.logger' % pbm) as mock_logger:
                cls = _LambdaService(21, 43, {}, None)
                cls.conn = mock_conn
                cls.find_usage()

        assert len(cls.limits) == 6
        assert mock_connect.mock_calls == [call()]
        assert mock_conn.mock_calls == [call.get_account_settings()]
        assert mock_logger.mock_calls == [
            call.debug('Getting limits for Lambda'),
            call.debug('Getting usage for Lambda metrics'),
            call.warn('Skipping Lambda: %s',
                      'Could not connect to the endpoint URL: "myurl"')
        ]

    def test_find_usage(self):
        response = result_fixtures.Lambda.test_lambda_response
        mock_conn = Mock()
        mock_conn.get_account_settings.return_value = response

        with patch('%s.connect' % pb) as mock_connect:
            cls = _LambdaService(21, 43, {}, None)
            cls.conn = mock_conn
            assert cls._have_usage is False
            cls.get_limits()
            cls.find_usage()

        assert mock_connect.mock_calls == [call()]
        assert mock_conn.mock_calls == [call.get_account_settings()]
        assert cls._have_usage is True
        assert len(cls.limits) == 6
        u = cls.limits['Function Count'].get_current_usage()
        assert len(u) == 1
        assert u[0].get_value() == 12
        u = cls.limits['Total Code Size (MiB)'].get_current_usage()
        assert len(u) == 1
        assert u[0].get_value() == 2

    def test_required_iam_permissions(self):
        cls = _LambdaService(21, 43, {}, None)
        assert cls.required_iam_permissions() == [
            'lambda:GetAccountSettings'
        ]
