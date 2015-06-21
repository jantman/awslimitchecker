"""
awslimitchecker/tests/services/test_vpc.py

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

import sys

from boto.vpc import VPCConnection
from boto.vpc.vpc import VPC
from boto.vpc.subnet import Subnet
from boto.vpc.networkacl import NetworkAcl
from boto.vpc.routetable import RouteTable

from awslimitchecker.services.vpc import _VpcService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT


class Test_VpcService(object):

    pb = 'awslimitchecker.services.vpc._VpcService'  # patch base path

    def test_init(self):
        """test __init__()"""
        cls = _VpcService(21, 43)
        assert cls.service_name == 'VPC'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_connect(self):
        """test connect()"""
        mock_conn = Mock()
        cls = _VpcService(21, 43)
        with patch('awslimitchecker.services.vpc.boto.connect_vpc') as mock_vpc:
            mock_vpc.return_value = mock_conn
            cls.connect()
        assert mock_vpc.mock_calls == [call()]
        assert mock_conn.mock_calls == []

    def test_connect_again(self):
        """make sure we re-use the connection"""
        mock_conn = Mock()
        cls = _VpcService(21, 43)
        cls.conn = mock_conn
        with patch('awslimitchecker.services.vpc.boto.connect_vpc') as mock_vpc:
            mock_vpc.return_value = mock_conn
            cls.connect()
        assert mock_vpc.mock_calls == []
        assert mock_conn.mock_calls == []

    def test_get_limits(self):
        cls = _VpcService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Entries per route table',
            'VPCs',
            'Subnets per VPC',
            'Network ACLs per VPC',
            'Rules per network ACL',
            'Route tables per VPC',
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _VpcService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage_vpc(self):
        mock1 = Mock(spec_set=VPC)
        type(mock1).id = 'vpc-1'
        mock2 = Mock(spec_set=VPC)
        type(mock2).id = 'vpc-2'

        vpcs = [mock1, mock2]
        subnets = []
        acls = []
        tables = []

        mock_conn = Mock(spec_set=VPCConnection)
        mock_conn.get_all_vpcs.return_value = vpcs
        mock_conn.get_all_subnets.return_value = subnets
        mock_conn.get_all_network_acls.return_value = acls
        mock_conn.get_all_route_tables.return_value = tables

        with patch('%s.connect' % self.pb) as mock_connect:
            cls = _VpcService(21, 43)
            cls.conn = mock_conn
            assert cls._have_usage is False
            cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        assert len(cls.limits['VPCs'].get_current_usage()) == 1
        assert cls.limits['VPCs'].get_current_usage()[0].get_value() == 2
        assert mock_conn.mock_calls == [
            call.get_all_vpcs(),
            call.get_all_subnets(),
            call.get_all_network_acls(),
            call.get_all_route_tables(),
        ]

    def test_find_usage_subnets(self):
        mock1 = Mock(spec_set=Subnet)
        type(mock1).vpc_id = 'vpc-1'
        mock2 = Mock(spec_set=Subnet)
        type(mock2).vpc_id = 'vpc-1'
        mock3 = Mock(spec_set=Subnet)
        type(mock3).vpc_id = 'vpc-2'

        vpcs = []
        subnets = [mock1, mock2, mock3]
        acls = []
        tables = []

        mock_conn = Mock(spec_set=VPCConnection)
        mock_conn.get_all_vpcs.return_value = vpcs
        mock_conn.get_all_subnets.return_value = subnets
        mock_conn.get_all_network_acls.return_value = acls
        mock_conn.get_all_route_tables.return_value = tables

        with patch('%s.connect' % self.pb) as mock_connect:
            cls = _VpcService(21, 43)
            cls.conn = mock_conn
            assert cls._have_usage is False
            cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        assert cls.limits['VPCs'].get_current_usage()[0].get_value() == 0
        usage = sorted(cls.limits['Subnets per VPC'].get_current_usage())
        assert len(usage) == 2
        assert usage[0].get_value() == 1
        assert usage[0].id == 'vpc-2'
        assert usage[1].get_value() == 2
        assert usage[1].id == 'vpc-1'
        assert mock_conn.mock_calls == [
            call.get_all_vpcs(),
            call.get_all_subnets(),
            call.get_all_network_acls(),
            call.get_all_route_tables(),
        ]

    def test_find_usage_acls(self):
        mock1 = Mock(spec_set=NetworkAcl)
        type(mock1).id = 'acl-1'
        type(mock1).vpc_id = 'vpc-1'
        type(mock1).network_acl_entries = [1, 2, 3]
        mock2 = Mock(spec_set=NetworkAcl)
        type(mock2).id = 'acl-2'
        type(mock2).vpc_id = 'vpc-1'
        type(mock2).network_acl_entries = [1]
        mock3 = Mock(spec_set=NetworkAcl)
        type(mock3).id = 'acl-3'
        type(mock3).vpc_id = 'vpc-2'
        type(mock3).network_acl_entries = [1, 2, 3, 4, 5]

        vpcs = []
        subnets = []
        acls = [mock1, mock2, mock3]
        tables = []

        mock_conn = Mock(spec_set=VPCConnection)
        mock_conn.get_all_vpcs.return_value = vpcs
        mock_conn.get_all_subnets.return_value = subnets
        mock_conn.get_all_network_acls.return_value = acls
        mock_conn.get_all_route_tables.return_value = tables

        with patch('%s.connect' % self.pb) as mock_connect:
            cls = _VpcService(21, 43)
            cls.conn = mock_conn
            assert cls._have_usage is False
            cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        usage = sorted(cls.limits['Network ACLs per VPC'].get_current_usage())
        assert len(usage) == 2
        assert usage[0].get_value() == 1
        assert usage[0].id == 'vpc-2'
        assert usage[1].get_value() == 2
        assert usage[1].id == 'vpc-1'
        entries = sorted(cls.limits['Rules per network '
                                    'ACL'].get_current_usage())
        assert len(entries) == 3
        assert entries[0].id == 'acl-2'
        assert entries[0].get_value() == 1
        assert entries[1].id == 'acl-1'
        assert entries[1].get_value() == 3
        assert entries[2].id == 'acl-3'
        assert entries[2].get_value() == 5
        assert mock_conn.mock_calls == [
            call.get_all_vpcs(),
            call.get_all_subnets(),
            call.get_all_network_acls(),
            call.get_all_route_tables(),
        ]

    def test_find_usage_route_tables(self):
        mock1 = Mock(spec_set=RouteTable)
        type(mock1).id = 'rt-1'
        type(mock1).vpc_id = 'vpc-1'
        type(mock1).routes = [1, 2, 3]
        mock2 = Mock(spec_set=RouteTable)
        type(mock2).id = 'rt-2'
        type(mock2).vpc_id = 'vpc-1'
        type(mock2).routes = [1]
        mock3 = Mock(spec_set=RouteTable)
        type(mock3).id = 'rt-3'
        type(mock3).vpc_id = 'vpc-2'
        type(mock3).routes = [1, 2, 3, 4, 5]

        vpcs = []
        subnets = []
        acls = []
        tables = [mock1, mock2, mock3]

        mock_conn = Mock(spec_set=VPCConnection)
        mock_conn.get_all_vpcs.return_value = vpcs
        mock_conn.get_all_subnets.return_value = subnets
        mock_conn.get_all_network_acls.return_value = acls
        mock_conn.get_all_route_tables.return_value = tables

        with patch('%s.connect' % self.pb) as mock_connect:
            cls = _VpcService(21, 43)
            cls.conn = mock_conn
            assert cls._have_usage is False
            cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        usage = sorted(cls.limits['Route tables per VPC'].get_current_usage())
        assert len(usage) == 2
        assert usage[0].get_value() == 1
        assert usage[0].id == 'vpc-2'
        assert usage[1].get_value() == 2
        assert usage[1].id == 'vpc-1'
        entries = sorted(cls.limits['Entries per route '
                                    'table'].get_current_usage())
        assert len(entries) == 3
        assert entries[0].id == 'rt-2'
        assert entries[0].get_value() == 1
        assert entries[1].id == 'rt-1'
        assert entries[1].get_value() == 3
        assert entries[2].id == 'rt-3'
        assert entries[2].get_value() == 5
        assert mock_conn.mock_calls == [
            call.get_all_vpcs(),
            call.get_all_subnets(),
            call.get_all_network_acls(),
            call.get_all_route_tables(),
        ]

    def test_required_iam_permissions(self):
        cls = _VpcService(21, 43)
        assert cls.required_iam_permissions() == [
            'ec2:DescribeNetworkAcls',
            'ec2:DescribeRouteTables',
            'ec2:DescribeSubnets',
            'ec2:DescribeVpcs',
        ]
