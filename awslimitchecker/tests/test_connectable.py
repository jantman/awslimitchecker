"""
awslimitchecker/tests/test_connectable.py

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

from awslimitchecker.connectable import Connectable, ConnectableCredentials
from datetime import datetime
import sys

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, PropertyMock
else:
    from unittest.mock import patch, call, Mock, PropertyMock


pbm = 'awslimitchecker.connectable'
pb = '%s.Connectable' % pbm


class ConnectableTester(Connectable):
    """example class to test Connectable"""

    service_name = 'connectable_tester'

    def __init__(self, account_id=None, account_role=None, region=None,
                 external_id=None, mfa_serial_number=None, mfa_token=None,
                 profile_name=None):
        self.account_id = account_id
        self.account_role = account_role
        self.region = region
        self.conn = None
        self.resource_conn = None
        self.external_id = external_id
        self.mfa_serial_number = mfa_serial_number
        self.mfa_token = mfa_token
        self.profile_name = profile_name


class Test_Connectable(object):

    def test_connect(self):
        mock_conn = Mock()
        mock_cc = Mock()
        type(mock_cc).region_name = 'myregion'
        type(mock_conn)._client_config = mock_cc

        cls = ConnectableTester()
        cls.api_name = 'myapi'
        kwargs = {'foo': 'fooval', 'bar': 'barval'}

        with patch('%s._boto3_connection_kwargs' % pb,
                   new_callable=PropertyMock, create=True) as mock_kwargs:
            mock_kwargs.return_value = kwargs
            with patch('%s.logger' % pbm) as mock_logger:
                with patch('%s.boto3.client' % pbm) as mock_client:
                    mock_client.return_value = mock_conn
                    cls.connect()
        assert mock_kwargs.mock_calls == [call()]
        assert mock_logger.mock_calls == [
            call.info("Connected to %s in region %s",
                      'myapi',
                      'myregion')
        ]
        assert mock_client.mock_calls == [
            call(
                'myapi',
                foo='fooval',
                bar='barval'
            )
        ]
        assert cls.conn == mock_client.return_value

    def test_connect_again(self):
        mock_conn = Mock()
        mock_cc = Mock()
        type(mock_cc).region_name = 'myregion'
        type(mock_conn)._client_config = mock_cc

        cls = ConnectableTester()
        cls.conn = mock_conn
        cls.api_name = 'myapi'
        kwargs = {'foo': 'fooval', 'bar': 'barval'}

        with patch('%s._boto3_connection_kwargs' % pb,
                   new_callable=PropertyMock, create=True) as mock_kwargs:
            mock_kwargs.return_value = kwargs
            with patch('%s.logger' % pbm) as mock_logger:
                with patch('%s.boto3.client' % pbm) as mock_client:
                    mock_client.return_value = mock_conn
                    cls.connect()
        assert mock_kwargs.mock_calls == []
        assert mock_logger.mock_calls == []
        assert mock_client.mock_calls == []
        assert cls.conn == mock_conn

    def test_connect_resource(self):
        mock_conn = Mock()
        mock_meta = Mock()
        mock_client = Mock()
        mock_cc = Mock()
        type(mock_cc).region_name = 'myregion'
        type(mock_client)._client_config = mock_cc
        type(mock_meta).client = mock_client
        type(mock_conn).meta = mock_meta

        cls = ConnectableTester()
        cls.api_name = 'myapi'
        kwargs = {'foo': 'fooval', 'bar': 'barval'}

        with patch('%s._boto3_connection_kwargs' % pb,
                   new_callable=PropertyMock, create=True) as mock_kwargs:
            mock_kwargs.return_value = kwargs
            with patch('%s.logger' % pbm) as mock_logger:
                with patch('%s.boto3.resource' % pbm) as mock_resource:
                    mock_resource.return_value = mock_conn
                    cls.connect_resource()
        assert mock_kwargs.mock_calls == [call()]
        assert mock_logger.mock_calls == [
            call.info("Connected to %s (resource) in region %s",
                      'myapi',
                      'myregion')
        ]
        assert mock_resource.mock_calls == [
            call(
                'myapi',
                foo='fooval',
                bar='barval'
            )
        ]
        assert cls.resource_conn == mock_resource.return_value

    def test_connect_resource_again(self):
        mock_conn = Mock()
        mock_meta = Mock()
        mock_client = Mock()
        mock_cc = Mock()
        type(mock_cc).region_name = 'myregion'
        type(mock_client)._client_config = mock_cc
        type(mock_meta).client = mock_client
        type(mock_conn).meta = mock_meta

        cls = ConnectableTester()

        cls.api_name = 'myapi'
        cls.resource_conn = mock_conn
        kwargs = {'foo': 'fooval', 'bar': 'barval'}

        with patch('%s._boto3_connection_kwargs' % pb,
                   new_callable=PropertyMock, create=True) as mock_kwargs:
            mock_kwargs.return_value = kwargs
            with patch('%s.logger' % pbm) as mock_logger:
                with patch('%s.boto3.resource' % pbm) as mock_resource:
                    mock_resource.return_value = mock_conn
                    cls.connect_resource()
        assert mock_kwargs.mock_calls == []
        assert mock_logger.mock_calls == []
        assert mock_resource.mock_calls == []
        assert cls.resource_conn == mock_conn


class TestConnectableCredentials(object):

    def test_connectable_credentials(self):
        result = {
            'Credentials': {
                'AccessKeyId': 'akid',
                'SecretAccessKey': 'secret',
                'SessionToken': 'token',
                'Expiration': datetime(2015, 1, 1)
            },
            'AssumedRoleUser': {
                'AssumedRoleId': 'roleid',
                'Arn': 'arn'
            },
            'PackedPolicySize': 123
        }
        c = ConnectableCredentials(result)
        assert c.access_key == 'akid'
        assert c.secret_key == 'secret'
        assert c.session_token == 'token'
        assert c.expiration == datetime(2015, 1, 1)
        assert c.assumed_role_id == 'roleid'
        assert c.assumed_role_arn == 'arn'
