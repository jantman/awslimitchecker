"""
awslimitchecker/tests/services/test_dynamodb.py

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


pb = 'awslimitchecker.services.dynamodb._DynamodbService'  # class patch pase
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

    def test_get_limits(self):
        cls = _DynamodbService(21, 43)
        region_name = cls.conn._client_config.region_name
        limits = cls.get_limits()
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

        if region_name == 'us-east-1':
            assert write_capacity_region.default_limit == 80000
            assert write_capacity_table.default_limit == 40000
            assert read_capacity_region.default_limit == 80000
            assert read_capacity_table.default_limit == 40000
        else:
            assert write_capacity_region.default_limit == 20000
            assert write_capacity_table.default_limit == 10000
            assert read_capacity_region.default_limit == 20000
            assert read_capacity_table.default_limit == 10000

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock(spec_set=AwsLimit)
        cls = _DynamodbService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    """
    def test_update_limits_from_api(self):
        response = result_fixtures.Dynamodb.test_update_limits_from_api
        mock_conn = Mock()
        mock_conn.describe_account_attributes.return_value = response
        with patch('%s.logger' % pbm) as mock_logger:
            with patch('%s.connect' % pb) as mock_connect:
                cls = _DynamodbService(21, 43)
                cls.conn = mock_conn

    def test_find_usage(self):
        mock_conn = Mock()
        mock_conn.some_method.return_value =   # some logical return value
        with patch('%s.connect' % pb) as mock_connect:
            cls = _DynamodbService(21, 43)
            cls.conn = mock_conn
            assert cls._have_usage is False
            cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        assert mock_conn.mock_calls == [call.some_method()]
    """

    def test_required_iam_permissions(self):
        cls = _DynamodbService(21, 43)
        assert cls.required_iam_permissions() == [
            "dynamodb:DescribeTable",
            "dynamodb:DescribeLimits"
        ]
