"""
awslimitchecker/tests/services/test_cognito.py

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
from awslimitchecker.services.cognito import _CognitoService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock


pbm = 'awslimitchecker.services.cognito'  # module patch base
pb = '%s._CognitoService' % pbm  # class patch pase


class Test_CognitoService(object):

    def test_init(self):
        """test __init__()"""
        cls = _CognitoService(21, 43, {}, None)
        assert cls.service_name == 'Cognito'
        assert cls.api_name == 'cognito-idp'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _CognitoService(21, 43, {}, None)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'User Pools',
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _CognitoService(21, 43, {}, None)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        response = result_fixtures.Cognito.test_find_usage_user_pools
        mock_conn = Mock()
        mock_conn.list_user_pools.return_value = response
        with patch('%s.connect' % pb) as mock_connect:
            cls = _CognitoService(21, 43, {}, None)
            cls.conn = mock_conn
            assert cls._have_usage is False
            cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert mock_conn.mock_calls == [call.list_user_pools(MaxResults=60)]
        assert cls._have_usage is True
        usp = cls.limits["User Pools"].get_current_usage()
        print(len(usp))
        assert len(usp) == 1
        assert usp[0].get_value() == 2

    def test_required_iam_permissions(self):
        cls = _CognitoService(21, 43, {}, None)
        assert cls.required_iam_permissions() == [
            "cognito-idp:ListUserPools",
        ]
