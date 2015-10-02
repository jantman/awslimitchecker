"""
awslimitchecker/tests/test_connectable.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2015 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

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

from awslimitchecker.connectable import Connectable
import sys

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock


class ConnectableTester(Connectable):
    """example class to test Connectable"""

    service_name = 'connectable_tester'

    def __init__(self, account_id=None, account_role=None, region=None,
                 external_id=None):
        self.account_id = account_id
        self.account_role = account_role
        self.region = region
        self.conn = None
        self.external_id = external_id


class Test_Connectable(object):

    def test_connect_via_no_region(self):
        cls = ConnectableTester()
        mock_driver = Mock()
        res = cls.connect_via(mock_driver)
        assert mock_driver.mock_calls == [
            call(None)
        ]
        assert res == mock_driver.return_value

    def test_connect_via_with_region(self):
        cls = ConnectableTester(region='foo')
        mock_driver = Mock()
        with patch('awslimitchecker.connectable.Connectable._get_sts_token'
                   '') as mock_get_sts:
            res = cls.connect_via(mock_driver)
        assert mock_get_sts.mock_calls == []
        assert mock_driver.mock_calls == [
            call('foo')
        ]
        assert res == mock_driver.return_value

    def test_connect_via_sts(self):
        cls = ConnectableTester(account_id='123', account_role='myrole',
                                region='myregion')
        mock_driver = Mock()
        mock_creds = Mock()
        type(mock_creds).access_key = 'sts_ak'
        type(mock_creds).secret_key = 'sts_sk'
        type(mock_creds).session_token = 'sts_token'

        with patch('awslimitchecker.connectable.Connectable._get_sts_token'
                   '') as mock_get_sts:
            mock_get_sts.return_value = mock_creds
            res = cls.connect_via(mock_driver)
        assert mock_get_sts.mock_calls == [call()]
        assert mock_driver.mock_calls == [
            call(
                'myregion',
                aws_access_key_id='sts_ak',
                aws_secret_access_key='sts_sk',
                security_token='sts_token'
            )
        ]
        assert res == mock_driver.return_value

    def test_get_sts_token(self):
        cls = ConnectableTester(account_id='789',
                                account_role='myr', region='foobar')
        with patch('awslimitchecker.connectable.boto.sts.connect_to_region'
                   '') as mock_connect:
            res = cls._get_sts_token()
        arn = 'arn:aws:iam::789:role/myr'
        assert mock_connect.mock_calls == [
            call('foobar'),
            call().assume_role(arn, 'awslimitchecker', external_id=None),
        ]
        assume_role_ret = mock_connect.return_value.assume_role.return_value
        assert res == assume_role_ret.credentials

    def test_get_sts_token_external_id(self):
        cls = ConnectableTester(account_id='789',
                                account_role='myr', region='foobar',
                                external_id='myextid')
        with patch('awslimitchecker.connectable.boto.sts.connect_to_region'
                   '') as mock_connect:
            res = cls._get_sts_token()
        arn = 'arn:aws:iam::789:role/myr'
        assert mock_connect.mock_calls == [
            call('foobar'),
            call().assume_role(arn, 'awslimitchecker', external_id='myextid'),
        ]
        assume_role_ret = mock_connect.return_value.assume_role.return_value
        assert res == assume_role_ret.credentials
