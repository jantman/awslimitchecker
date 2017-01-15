"""
awslimitchecker/tests/services/test_ses.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2015-2017 Jason Antman <jason@jasonantman.com>

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
bugs please submit them at <https://github.com/jantman/pydnstest> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

import sys
from awslimitchecker.services.ses import _SesService
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


pbm = 'awslimitchecker.services.ses'  # module patch base
pb = '%s._SesService' % pbm  # class patch pase


class Test_SesService(object):

    def test_init(self):
        """test __init__()"""
        cls = _SesService(21, 43)
        assert cls.service_name == 'SES'
        assert cls.api_name == 'ses'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _SesService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Daily sending quota',
        ])
        limit = cls.limits['Daily sending quota']
        assert limit.service == cls
        assert limit.def_warning_threshold == 21
        assert limit.def_critical_threshold == 43
        assert limit.default_limit == 200

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _SesService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        mock_conn = Mock()
        mock_conn.get_send_quota.return_value = {
            'Max24HourSend': 123.0,
            'MaxSendRate': 12.0,
            'SentLast24Hours': 122.0
        }

        with patch('%s.connect' % pb) as mock_connect:
            cls = _SesService(21, 43)
            cls.conn = mock_conn
            assert cls._have_usage is False
            cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        assert mock_conn.mock_calls == [call.get_send_quota()]
        assert len(cls.limits['Daily sending quota'].get_current_usage()) == 1
        assert cls.limits['Daily sending quota'].get_current_usage()[
                   0].get_value() == 122.0

    def test_find_usage_invalid_region(self):
        def se_get():
            raise EndpointConnectionError(endpoint_url='myurl')

        mock_conn = Mock()
        mock_conn.get_send_quota.side_effect = se_get

        with patch('%s.connect' % pb) as mock_connect:
            with patch('%s.logger' % pbm) as mock_logger:
                cls = _SesService(21, 43)
                cls.conn = mock_conn
                assert cls._have_usage is False
                cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is False
        assert mock_logger.mock_calls == [
            call.debug('Checking usage for service %s', 'SES'),
            call.warn(
                'Skipping SES: %s',
                'Could not connect to the endpoint URL: "myurl"'
            )
        ]
        assert mock_conn.mock_calls == [call.get_send_quota()]
        assert len(cls.limits['Daily sending quota'].get_current_usage()) == 0

    def test_update_limits_from_api(self):
        mock_conn = Mock()
        mock_conn.get_send_quota.return_value = {
            'Max24HourSend': 123.0,
            'MaxSendRate': 12.0,
            'SentLast24Hours': 122.0
        }

        with patch('%s.connect' % pb) as mock_connect:
            cls = _SesService(21, 43)
            cls.conn = mock_conn
            cls._update_limits_from_api()
        assert mock_connect.mock_calls == [call()]
        assert mock_conn.mock_calls == [call.get_send_quota()]
        assert cls.limits['Daily sending quota'].api_limit == 123.0

    def test_update_limits_from_api_invalid_region(self):
        def se_get():
            raise EndpointConnectionError(endpoint_url='myurl')

        mock_conn = Mock()
        mock_conn.get_send_quota.side_effect = se_get

        with patch('%s.connect' % pb) as mock_connect:
            with patch('%s.logger' % pbm) as mock_logger:
                cls = _SesService(21, 43)
                cls.conn = mock_conn
                cls._update_limits_from_api()
        assert mock_connect.mock_calls == [call()]
        assert mock_conn.mock_calls == [call.get_send_quota()]
        assert mock_logger.mock_calls == [
            call.warn(
                'Skipping SES: %s',
                'Could not connect to the endpoint URL: "myurl"'
            )
        ]
        assert cls.limits['Daily sending quota'].api_limit is None

    def test_required_iam_permissions(self):
        cls = _SesService(21, 43)
        assert cls.required_iam_permissions() == [
            'ses:GetSendQuota'
        ]
