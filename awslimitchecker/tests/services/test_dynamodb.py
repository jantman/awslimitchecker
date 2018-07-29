"""
awslimitchecker/tests/services/test_dynamodb.py

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
from awslimitchecker.limit import AwsLimit
from awslimitchecker.services.dynamodb import _DynamodbService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock


pb = 'awslimitchecker.services.dynamodb._DynamodbService'  # class patch base
pbm = 'awslimitchecker.services.dynamodb'  # module patch base


class Test_DynamodbService(object):

    def test_init(self):
        """test __init__()"""
        with patch('%s.get_limits' % pb):
            cls = _DynamodbService(21, 43)
        assert cls.service_name == 'DynamoDB'
        assert cls.api_name == 'dynamodb'
        assert cls.conn is None
        assert cls.resource_conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits_other_region(self):
        mock_conn = Mock()
        m_client = Mock()
        type(m_client).region_name = 'foo'
        type(mock_conn)._client_config = m_client

        def se_conn(cls):
            cls.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as mock_connect:
            mock_connect.side_effect = se_conn
            cls = _DynamodbService(21, 43)

        limits = cls.limits
        for x in limits:
            assert isinstance(limits[x], AwsLimit)
            assert x == limits[x].name
            assert limits[x].service == cls
        assert len(limits) == 7
        table_count = limits['Tables Per Region']
        assert table_count.limit_type == 'AWS::DynamoDB::Table'
        assert table_count.default_limit == 256
        write_capacity_region = limits['Account Max Write Capacity Units']
        assert write_capacity_region.limit_type == 'AWS::DynamoDB::Table'
        write_capacity_table = limits['Table Max Write Capacity Units']
        assert write_capacity_table.limit_type == 'AWS::DynamoDB::Table'
        read_capacity_region = limits['Account Max Read Capacity Units']
        assert read_capacity_region.limit_type == 'AWS::DynamoDB::Table'
        read_capacity_table = limits['Table Max Read Capacity Units']
        assert read_capacity_table.limit_type == 'AWS::DynamoDB::Table'
        global_secondary_index = limits['Global Secondary Indexes']
        assert global_secondary_index.limit_type == 'AWS::DynamoDB::Table'
        assert global_secondary_index.default_limit == 5
        local_secondary_index = limits['Local Secondary Indexes']
        assert local_secondary_index.limit_type == 'AWS::DynamoDB::Table'
        assert local_secondary_index.default_limit == 5
        # NOT us-east-1
        assert write_capacity_region.default_limit == 20000
        assert write_capacity_table.default_limit == 10000
        assert read_capacity_region.default_limit == 20000
        assert read_capacity_table.default_limit == 10000

    def test_get_limits_us_east_1(self):
        mock_conn = Mock()
        m_client = Mock()
        type(m_client).region_name = 'us-east-1'
        type(mock_conn)._client_config = m_client

        def se_conn(cls):
            cls.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as mock_connect:
            mock_connect.side_effect = se_conn
            cls = _DynamodbService(21, 43)

        limits = cls.limits
        for x in limits:
            assert isinstance(limits[x], AwsLimit)
            assert x == limits[x].name
            assert limits[x].service == cls
        assert len(limits) == 7
        table_count = limits['Tables Per Region']
        assert table_count.limit_type == 'AWS::DynamoDB::Table'
        assert table_count.default_limit == 256
        write_capacity_region = limits['Account Max Write Capacity Units']
        assert write_capacity_region.limit_type == 'AWS::DynamoDB::Table'
        write_capacity_table = limits['Table Max Write Capacity Units']
        assert write_capacity_table.limit_type == 'AWS::DynamoDB::Table'
        read_capacity_region = limits['Account Max Read Capacity Units']
        assert read_capacity_region.limit_type == 'AWS::DynamoDB::Table'
        read_capacity_table = limits['Table Max Read Capacity Units']
        assert read_capacity_table.limit_type == 'AWS::DynamoDB::Table'
        global_secondary_index = limits['Global Secondary Indexes']
        assert global_secondary_index.limit_type == 'AWS::DynamoDB::Table'
        assert global_secondary_index.default_limit == 5
        local_secondary_index = limits['Local Secondary Indexes']
        assert local_secondary_index.limit_type == 'AWS::DynamoDB::Table'
        assert local_secondary_index.default_limit == 5
        # us-east-1
        assert write_capacity_region.default_limit == 80000
        assert write_capacity_table.default_limit == 40000
        assert read_capacity_region.default_limit == 80000
        assert read_capacity_table.default_limit == 40000

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock(spec_set=AwsLimit)
        cls = _DynamodbService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_update_limits_from_api(self):
        response = result_fixtures.DynamoDB.test_update_limits_from_api
        mock_conn = Mock()
        mock_conn.describe_limits.return_value = response
        m_client = Mock()
        type(m_client).region_name = 'foo'
        type(mock_conn)._client_config = m_client

        def se_conn(cls):
            cls.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as mock_connect:
            mock_connect.side_effect = se_conn
            cls = _DynamodbService(21, 43)
            cls.conn = mock_conn
            cls._update_limits_from_api()
        assert cls.limits['Account Max Read Capacity Units'].api_limit == 111
        assert cls.limits['Account Max Write Capacity Units'].api_limit == 222
        assert cls.limits['Table Max Read Capacity Units'].api_limit == 333
        assert cls.limits['Table Max Write Capacity Units'].api_limit == 444
        assert mock_connect.mock_calls == [
            call(cls), call(cls)
        ]
        assert mock_conn.mock_calls == [call.describe_limits()]

    def test_find_usage(self):
        mock_conn = Mock()
        m_client = Mock()
        type(m_client).region_name = 'foo'
        type(mock_conn)._client_config = m_client

        def se_conn(cls):
            cls.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as mock_connect:
            with patch('%s._find_usage_dynamodb' % pb, autospec=True) as m_fud:
                with patch(
                    '%s.connect_resource' % pb, autospec=True
                ) as mock_conn_res:
                    mock_connect.side_effect = se_conn
                    cls = _DynamodbService(21, 43)
                    cls.conn = mock_conn
                    assert cls._have_usage is False
                    cls.find_usage()
        assert mock_connect.mock_calls == [call(cls)]
        assert mock_conn_res.mock_calls == [call(cls)]
        assert mock_conn.mock_calls == []
        assert m_client.mock_calls == []
        assert m_fud.mock_calls == [call(cls)]
        assert cls._have_usage is True

    def test_find_usage_dynamodb(self):
        response = result_fixtures.DynamoDB.test_find_usage_dynamodb
        mock_conn = Mock()
        mock_conn.describe_limits.return_value = response
        m_client = Mock()
        type(m_client).region_name = 'foo'
        type(mock_conn)._client_config = m_client

        def se_conn(cls):
            cls.conn = mock_conn

        mock_tables = Mock()
        mock_tables.all.return_value = response
        mock_res_conn = Mock()
        type(mock_res_conn).tables = mock_tables

        with patch('%s.connect' % pb, autospec=True) as mock_connect:
            mock_connect.side_effect = se_conn
            cls = _DynamodbService(21, 43)
            cls.conn = mock_conn
            cls.resource_conn = mock_res_conn
            cls._find_usage_dynamodb()
        # Account/Region wide limits
        u = cls.limits['Tables Per Region'].get_current_usage()
        assert len(u) == 1
        assert u[0].get_value() == 3
        u = cls.limits['Account Max Write Capacity Units'].get_current_usage()
        assert len(u) == 1
        assert u[0].get_value() == 1355
        u = cls.limits['Account Max Read Capacity Units'].get_current_usage()
        assert len(u) == 1
        assert u[0].get_value() == 1000
        # Per Table Limits
        u = cls.limits['Global Secondary Indexes'].get_current_usage()
        assert len(u) == 3
        assert u[0].resource_id == 'table1'
        assert u[0].get_value() == 2
        assert u[1].resource_id == 'table2'
        assert u[1].get_value() == 1
        assert u[2].resource_id == 'table3'
        assert u[2].get_value() == 0
        u = cls.limits['Local Secondary Indexes'].get_current_usage()
        assert len(u) == 3
        assert u[0].resource_id == 'table1'
        assert u[0].get_value() == 3
        assert u[1].resource_id == 'table2'
        assert u[1].get_value() == 1
        assert u[2].resource_id == 'table3'
        assert u[2].get_value() == 0
        u = cls.limits['Table Max Write Capacity Units'].get_current_usage()
        assert len(u) == 3
        assert u[0].resource_id == 'table1'
        assert u[0].get_value() == 106
        assert u[1].resource_id == 'table2'
        assert u[1].get_value() == 449
        assert u[2].resource_id == 'table3'
        assert u[2].get_value() == 800
        u = cls.limits['Table Max Read Capacity Units'].get_current_usage()
        assert len(u) == 3
        assert u[0].resource_id == 'table1'
        assert u[0].get_value() == 64
        assert u[1].resource_id == 'table2'
        assert u[1].get_value() == 336
        assert u[2].resource_id == 'table3'
        assert u[2].get_value() == 600

    def test_required_iam_permissions(self):
        cls = _DynamodbService(21, 43)
        assert cls.required_iam_permissions() == [
            "dynamodb:DescribeLimits",
            "dynamodb:DescribeTable",
            "dynamodb:ListTables"
        ]
