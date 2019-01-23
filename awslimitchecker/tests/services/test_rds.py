"""
awslimitchecker/tests/services/test_rds.py

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
from awslimitchecker.services.rds import _RDSService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT


class Test_RDSService(object):

    pb = 'awslimitchecker.services.rds._RDSService'  # patch base path
    pbm = 'awslimitchecker.services.rds'  # patch base path - module

    def test_init(self):
        """test __init__()"""
        cls = _RDSService(21, 43)
        assert cls.service_name == 'RDS'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _RDSService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            # TA  # non-TA / service doc name
            'DB instances',  # 'Instances'
            'Max auths per security group',
            'Storage quota (GB)',  # 'Total storage for all DB instances'
            'DB snapshots per user',  # 'Manual Snapshots'
            'DB security groups',  # 'Security Groups'
            # non-TA
            'Reserved Instances',
            'DB parameter groups',
            'VPC Security Groups',
            'Subnet Groups',
            'Subnets per Subnet Group',
            'Option Groups',
            'Event Subscriptions',
            'Read replicas per master',
            'DB Clusters',
            'DB Cluster Parameter Groups'
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _RDSService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        mock_conn = Mock()

        with patch('%s.connect' % self.pb) as mock_connect:
            with patch.multiple(
                    self.pb,
                    _find_usage_instances=DEFAULT,
                    _find_usage_subnet_groups=DEFAULT,
                    _find_usage_security_groups=DEFAULT,
                    _update_limits_from_api=DEFAULT,
            ) as mocks:
                cls = _RDSService(21, 43)
                cls.conn = mock_conn
                assert cls._have_usage is False
                cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        for x in [
                '_find_usage_instances',
                '_find_usage_subnet_groups',
                '_find_usage_security_groups',
                '_update_limits_from_api',
        ]:
            assert mocks[x].mock_calls == [call()]

    def test_required_iam_permissions(self):
        cls = _RDSService(21, 43)
        assert cls.required_iam_permissions() == [
            "rds:DescribeAccountAttributes",
            "rds:DescribeDBInstances",
            "rds:DescribeDBParameterGroups",
            "rds:DescribeDBSecurityGroups",
            "rds:DescribeDBSnapshots",
            "rds:DescribeDBSubnetGroups",
            "rds:DescribeEventSubscriptions",
            "rds:DescribeOptionGroups",
            "rds:DescribeReservedDBInstances",
        ]

    def test_find_usage_instances(self):
        instances = result_fixtures.RDS.test_find_usage_instances

        mock_conn = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = instances
        mock_conn.get_paginator.return_value = mock_paginator

        cls = _RDSService(21, 43)
        cls.conn = mock_conn

        cls._find_usage_instances()

        assert mock_conn.mock_calls == [
            call.get_paginator('describe_db_instances'),
            call.get_paginator().paginate()
        ]
        assert mock_paginator.mock_calls == [
            call.paginate()
        ]

        usage = sorted(
            cls.limits['Read replicas per master'].get_current_usage()
        )
        assert len(usage) == 2
        assert usage[0].get_value() == 0
        assert usage[0].resource_id == 'foo'
        assert usage[1].get_value() == 2
        assert usage[1].resource_id == 'baz'

    def test_find_usage_subnet_groups(self):
        data = result_fixtures.RDS.test_find_usage_subnet_groups

        mock_conn = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = data
        mock_conn.get_paginator.return_value = mock_paginator

        cls = _RDSService(21, 43)
        cls.conn = mock_conn

        cls._find_usage_subnet_groups()

        assert mock_conn.mock_calls == [
            call.get_paginator('describe_db_subnet_groups'),
            call.get_paginator().paginate()
        ]
        assert mock_paginator.mock_calls == [
            call.paginate()
        ]

        usage = sorted(
            cls.limits['Subnets per Subnet Group'].get_current_usage()
        )
        assert len(usage) == 3
        assert usage[0].get_value() == 1
        assert usage[0].aws_type == 'AWS::RDS::DBSubnetGroup'
        assert usage[0].resource_id == "SubnetGroup2"
        assert usage[1].get_value() == 2
        assert usage[1].aws_type == 'AWS::RDS::DBSubnetGroup'
        assert usage[1].resource_id == "SubnetGroup1"
        assert usage[2].get_value() == 3
        assert usage[2].aws_type == 'AWS::RDS::DBSubnetGroup'
        assert usage[2].resource_id == "default"

    def test_find_usage_security_groups(self):
        data = result_fixtures.RDS.test_find_usage_security_groups

        mock_conn = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = data
        mock_conn.get_paginator.return_value = mock_paginator

        cls = _RDSService(21, 43)
        cls.conn = mock_conn

        cls._find_usage_security_groups()

        assert mock_conn.mock_calls == [
            call.get_paginator('describe_db_security_groups'),
            call.get_paginator().paginate()
        ]
        assert mock_paginator.mock_calls == [
            call.paginate()
        ]

        usage = sorted(cls.limits['VPC Security Groups'].get_current_usage())
        assert len(usage) == 1
        assert usage[0].get_value() == 2
        assert usage[0].aws_type == 'AWS::RDS::DBSecurityGroup'

        usage = sorted(cls.limits[
                           'Max auths per security group'].get_current_usage())
        assert len(usage) == 5
        assert usage[0].get_value() == 0
        assert usage[0].resource_id == 'MyEmptySecurityGroup'
        assert usage[0].aws_type == 'AWS::RDS::DBSecurityGroup'
        assert usage[1].get_value() == 0
        assert usage[1].resource_id == 'default:vpc-a926c2cc'
        assert usage[1].aws_type == 'AWS::RDS::DBSecurityGroup'
        assert usage[2].get_value() == 1
        assert usage[2].resource_id == 'SecurityGroup1'
        assert usage[2].aws_type == 'AWS::RDS::DBSecurityGroup'
        assert usage[3].get_value() == 2
        assert usage[3].resource_id == 'alctest'
        assert usage[3].aws_type == 'AWS::RDS::DBSecurityGroup'
        assert usage[4].get_value() == 3
        assert usage[4].resource_id == 'SecurityGroup2'
        assert usage[4].aws_type == 'AWS::RDS::DBSecurityGroup'

    def test_update_limits_from_api(self):
        response = result_fixtures.RDS.test_update_limits_from_api

        mock_conn = Mock()
        mock_conn.describe_account_attributes.return_value = response
        with patch('%s.logger' % self.pbm) as mock_logger:
            with patch('%s.connect' % self.pb) as mock_connect:
                cls = _RDSService(21, 43)
                cls.conn = mock_conn
                # limits that we still calculate usage for
                cls.limits['Max auths per security group']._add_current_usage(1)
                cls.limits['Subnets per Subnet Group']._add_current_usage(1)
                cls.limits['Read replicas per master']._add_current_usage(1)
                usage_auths = cls.limits[
                    'Max auths per security group'].get_current_usage()
                usage_subnets = cls.limits[
                    'Subnets per Subnet Group'].get_current_usage()
                usage_replicas = cls.limits[
                    'Read replicas per master'].get_current_usage()
                cls._update_limits_from_api()
        assert mock_connect.mock_calls == [call()]
        assert mock_conn.mock_calls == [
            call.describe_account_attributes()
        ]
        assert mock_logger.mock_calls == [
            call.info('Querying RDS DescribeAccountAttributes for limits'),
            call.info(
                'RDS DescribeAccountAttributes returned unknown'
                'limit: %s (max: %s; used: %s)',
                'Foo', 98, 99
            ),
            call.debug('Done setting limits from API.')
        ]

        lim = cls.limits['DB instances']
        assert lim.api_limit == 200
        assert lim.get_current_usage()[0].get_value() == 124

        lim = cls.limits['Reserved Instances']
        assert lim.api_limit == 201
        assert lim.get_current_usage()[0].get_value() == 96

        lim = cls.limits['Storage quota (GB)']
        assert lim.api_limit == 100000
        assert lim.get_current_usage()[0].get_value() == 8320

        lim = cls.limits['DB security groups']
        assert lim.api_limit == 25
        assert lim.get_current_usage()[0].get_value() == 15

        lim = cls.limits['Max auths per security group']
        assert lim.api_limit == 20
        assert lim.get_current_usage() == usage_auths

        lim = cls.limits['DB parameter groups']
        assert lim.api_limit == 50
        assert lim.get_current_usage()[0].get_value() == 39

        lim = cls.limits['DB snapshots per user']
        assert lim.api_limit == 150
        assert lim.get_current_usage()[0].get_value() == 76

        lim = cls.limits['Event Subscriptions']
        assert lim.api_limit == 21
        assert lim.get_current_usage()[0].get_value() == 1

        lim = cls.limits['Subnet Groups']
        assert lim.api_limit == 202
        assert lim.get_current_usage()[0].get_value() == 89

        lim = cls.limits['Option Groups']
        assert lim.api_limit == 22
        assert lim.get_current_usage()[0].get_value() == 2

        lim = cls.limits['Subnets per Subnet Group']
        assert lim.api_limit == 23
        assert lim.get_current_usage() == usage_subnets

        lim = cls.limits['Read replicas per master']
        assert lim.api_limit == 5
        assert lim.get_current_usage() == usage_replicas

        lim = cls.limits['DB Clusters']
        assert lim.api_limit == 40
        assert lim.get_current_usage()[0].get_value() == 3

        lim = cls.limits['DB Cluster Parameter Groups']
        assert lim.api_limit == 51
        assert lim.get_current_usage()[0].get_value() == 6
