"""
awslimitchecker/tests/services/test_ec2.py

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
import pytest
import botocore
from awslimitchecker.tests.services import result_fixtures
from awslimitchecker.services.ec2 import _Ec2Service
from awslimitchecker.limit import AwsLimit
from awslimitchecker.services.ec2 import RI_NO_AZ

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT

fixtures = result_fixtures.EC2()


class Test_Ec2Service(object):

    pb = 'awslimitchecker.services.ec2._Ec2Service'  # patch base path
    pbm = 'awslimitchecker.services.ec2'  # module patch base path

    def test_init(self):
        """test __init__()"""
        cls = _Ec2Service(21, 43)
        assert cls.service_name == 'EC2'
        assert cls.conn is None
        assert cls.resource_conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_instance_types(self):
        cls = _Ec2Service(21, 43)
        types = cls._instance_types()
        assert len(types) == 76
        assert 't2.micro' in types
        assert 'r3.8xlarge' in types
        assert 'c3.large' in types
        assert 'i2.4xlarge' in types
        assert 'i3.16xlarge' in types
        assert 'd2.2xlarge' in types
        assert 'g2.8xlarge' in types
        assert 'hs1.8xlarge' in types
        assert 'cg1.4xlarge' in types
        assert 'm4.4xlarge' in types
        assert 'p2.16xlarge' in types
        assert 'm4.16xlarge' in types
        assert 'x1.32xlarge' in types

    def test_get_limits(self):
        cls = _Ec2Service(21, 43)
        cls.limits = {}
        with patch('%s._get_limits_instances' % self.pb) as mock_instances:
            with patch('%s._get_limits_networking' % self.pb) as mock_vpc:
                with patch('%s._get_limits_spot' % self.pb) as mock_spot:
                    mock_instances.return_value = {'ec2lname': 'ec2lval'}
                    mock_vpc.return_value = {'vpck': 'vpcv'}
                    mock_spot.return_value = {'spotk': 'spotv'}
                    res = cls.get_limits()
        assert res == {
            'ec2lname': 'ec2lval',
            'spotk': 'spotv',
            'vpck': 'vpcv',
        }
        assert mock_instances.mock_calls == [call()]
        assert mock_vpc.mock_calls == [call()]
        assert mock_spot.mock_calls == [call()]

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        cls = _Ec2Service(21, 43)
        cls.limits = {'foo': 'bar'}
        with patch('%s._get_limits_instances' % self.pb) as mock_instances:
            with patch('%s._get_limits_networking' % self.pb) as mock_vpc:
                with patch('%s._get_limits_spot' % self.pb) as mock_spot:
                    res = cls.get_limits()
        assert res == {'foo': 'bar'}
        assert mock_instances.mock_calls == []
        assert mock_vpc.mock_calls == []
        assert mock_spot.mock_calls == []

    def test_get_limits_all(self):
        """test some things all limits should conform to"""
        cls = _Ec2Service(21, 43)
        limits = cls.get_limits()
        for x in limits:
            assert isinstance(limits[x], AwsLimit)
            assert x == limits[x].name
            assert limits[x].service == cls

    def test_get_limits_instances(self):
        cls = _Ec2Service(21, 43)
        limits = cls._get_limits_instances()
        assert len(limits) == 77
        # check a random subset of limits
        t2_micro = limits['Running On-Demand t2.micro instances']
        assert t2_micro.default_limit == 20
        assert t2_micro.limit_type == 'On-Demand instances'
        assert t2_micro.limit_subtype == 't2.micro'
        c4_8xlarge = limits['Running On-Demand c4.8xlarge instances']
        assert c4_8xlarge.default_limit == 5
        assert c4_8xlarge.limit_type == 'On-Demand instances'
        assert c4_8xlarge.limit_subtype == 'c4.8xlarge'
        i2_8xlarge = limits['Running On-Demand i2.8xlarge instances']
        assert i2_8xlarge.default_limit == 2
        assert i2_8xlarge.limit_type == 'On-Demand instances'
        assert i2_8xlarge.limit_subtype == 'i2.8xlarge'
        i3_16xlarge = limits['Running On-Demand i3.16xlarge instances']
        assert i3_16xlarge.default_limit == 2
        assert i3_16xlarge.limit_type == 'On-Demand instances'
        assert i3_16xlarge.limit_subtype == 'i3.16xlarge'
        m4_16xlarge = limits['Running On-Demand m4.16xlarge instances']
        assert m4_16xlarge.default_limit == 5
        assert m4_16xlarge.limit_type == 'On-Demand instances'
        assert m4_16xlarge.limit_subtype == 'm4.16xlarge'
        p2_16xlarge = limits['Running On-Demand p2.16xlarge instances']
        assert p2_16xlarge.default_limit == 1
        assert p2_16xlarge.limit_type == 'On-Demand instances'
        assert p2_16xlarge.limit_subtype == 'p2.16xlarge'
        all_ec2 = limits['Running On-Demand EC2 instances']
        assert all_ec2.default_limit == 20
        assert all_ec2.limit_type == 'On-Demand instances'
        assert all_ec2.limit_subtype is None
        assert 'Running On-Demand m4.4xlarge instances' in limits
        for lname, lim in limits.items():
            assert lim.limit_type == 'On-Demand instances'
            itype = lim.limit_subtype
            if itype is not None:
                assert lname == 'Running On-Demand %s instances' % itype
                assert lim.ta_limit_name == 'On-Demand instances - %s' % itype

    def test_find_usage(self):
        with patch.multiple(
                self.pb,
                connect=DEFAULT,
                _find_usage_instances=DEFAULT,
                _find_usage_networking_sgs=DEFAULT,
                _find_usage_networking_eips=DEFAULT,
                _find_usage_networking_eni_sg=DEFAULT,
                _find_usage_spot_instances=DEFAULT,
                _find_usage_spot_fleets=DEFAULT,
                autospec=True,
        ) as mocks:
            cls = _Ec2Service(21, 43)
            assert cls._have_usage is False
            cls.find_usage()
        assert cls._have_usage is True
        assert len(mocks) == 7
        for m in mocks:
            assert mocks[m].mock_calls == [call(cls)]

    def test_instance_usage(self):
        mock_t2_micro = Mock(spec_set=AwsLimit)
        mock_r3_2xlarge = Mock(spec_set=AwsLimit)
        mock_c4_4xlarge = Mock(spec_set=AwsLimit)
        mock_m4_8xlarge = Mock(spec_set=AwsLimit)
        limits = {
            'Running On-Demand t2.micro instances': mock_t2_micro,
            'Running On-Demand r3.2xlarge instances': mock_r3_2xlarge,
            'Running On-Demand c4.4xlarge instances': mock_c4_4xlarge,
            'Running On-Demand m4.8xlarge instances': mock_m4_8xlarge,
        }

        cls = _Ec2Service(21, 43)
        mock_conn = Mock()

        retval = fixtures.test_instance_usage
        mock_conn.instances.all.return_value = retval

        cls.resource_conn = mock_conn
        cls.limits = limits

        with patch('awslimitchecker.services.ec2._Ec2Service._instance_types',
                   autospec=True) as mock_itypes:
            mock_itypes.return_value = [
                't2.micro',
                'r3.2xlarge',
                'c4.4xlarge',
                'm4.8xlarge',
            ]
            res = cls._instance_usage()
        assert res == {
            'az1a': {
                't2.micro': 1,
                'r3.2xlarge': 1,
                'c4.4xlarge': 1,
                'm4.8xlarge': 1,
            }
        }
        assert mock_conn.mock_calls == [
            call.instances.all()
        ]

    def test_get_reserved_instance_count(self):
        response = fixtures.test_get_reserved_instance_count

        cls = _Ec2Service(21, 43)
        mock_client_conn = Mock()
        cls.conn = mock_client_conn
        mock_client_conn.describe_reserved_instances.return_value = response
        mock_conn = Mock()
        cls.resource_conn = mock_conn

        res = cls._get_reserved_instance_count()
        assert res == {
            'az1': {
                'it1': 10,
            },
            'az2': {
                'it2': 98,
            },
            RI_NO_AZ: {
                'it2': 9,
                'it3': 6
            }
        }
        assert mock_conn.mock_calls == []
        assert mock_client_conn.mock_calls == [
            call.describe_reserved_instances()
        ]

    def test_find_usage_instances(self):
        iusage = {
            'us-east-1': {
                't2.micro': 2,
                'r3.2xlarge': 10,
                'c4.4xlarge': 3,
                'c4.large': 2,
            },
            'fooaz': {
                't2.micro': 32,
                'c4.large': 2,
            },
            'us-west-1': {
                't2.micro': 5,
                'r3.2xlarge': 5,
                'c4.4xlarge': 2,
            },
        }

        ri_count = {
            'us-east-1': {
                't2.micro': 10,
                'r3.2xlarge': 2,
            },
            'us-west-1': {
                't2.micro': 1,
                'r3.2xlarge': 5,
            },
            RI_NO_AZ: {
                't2.micro': 1,
                'c4.large': 50,
            }
        }

        mock_t2_micro = Mock(spec_set=AwsLimit)
        mock_r3_2xlarge = Mock(spec_set=AwsLimit)
        mock_c4_4xlarge = Mock(spec_set=AwsLimit)
        mock_c4_large = Mock(spec_set=AwsLimit)
        mock_all_ec2 = Mock(spec_set=AwsLimit)
        limits = {
            'Running On-Demand t2.micro instances': mock_t2_micro,
            'Running On-Demand r3.2xlarge instances': mock_r3_2xlarge,
            'Running On-Demand c4.4xlarge instances': mock_c4_4xlarge,
            'Running On-Demand c4.large instances': mock_c4_large,
            'Running On-Demand EC2 instances': mock_all_ec2,
        }

        cls = _Ec2Service(21, 43)
        mock_conn = Mock()
        cls.resource_conn = mock_conn
        cls.limits = limits
        with patch('%s._instance_usage' % self.pb,
                   autospec=True) as mock_inst_usage:
            with patch('%s._get_reserved_instance_count' % self.pb,
                       autospec=True) as mock_res_inst_count:
                mock_inst_usage.return_value = iusage
                mock_res_inst_count.return_value = ri_count
                cls._find_usage_instances()
        assert mock_t2_micro.mock_calls == [call._add_current_usage(
            35,
            aws_type='AWS::EC2::Instance'
        )]
        assert mock_r3_2xlarge.mock_calls == [call._add_current_usage(
            8,
            aws_type='AWS::EC2::Instance'
        )]
        assert mock_c4_4xlarge.mock_calls == [call._add_current_usage(
            5,
            aws_type='AWS::EC2::Instance'
        )]
        assert mock_c4_large.mock_calls == [call._add_current_usage(
            0,
            aws_type='AWS::EC2::Instance'
        )]
        assert mock_all_ec2.mock_calls == [call._add_current_usage(
            48,
            aws_type='AWS::EC2::Instance'
        )]
        assert mock_inst_usage.mock_calls == [call(cls)]
        assert mock_res_inst_count.mock_calls == [call(cls)]
        assert mock_conn.mock_calls == []

    def test_instance_usage_key_error(self):
        mock_conn = Mock()
        data = fixtures.test_instance_usage_key_error
        mock_conn.instances.all.return_value = data
        cls = _Ec2Service(21, 43)
        cls.resource_conn = mock_conn
        cls.limits = {'Running On-Demand t2.micro instances': Mock()}

        with patch(
                '%s._instance_types' % self.pb,
                autospec=True) as mock_itypes:
            with patch('awslimitchecker.services.ec2.logger') as mock_logger:
                mock_itypes.return_value = ['t2.micro']
                cls._instance_usage()
        assert mock_logger.mock_calls == [
            call.debug('Getting usage for on-demand instances'),
            call.error("ERROR - unknown instance type '%s'; not counting",
                       'foobar'),
        ]
        assert mock_conn.mock_calls == [
            call.instances.all()
        ]

    def test_required_iam_permissions(self):
        cls = _Ec2Service(21, 43)
        assert len(cls.required_iam_permissions()) == 19
        assert cls.required_iam_permissions() == [
            "ec2:DescribeAccountAttributes",
            "ec2:DescribeAddresses",
            "ec2:DescribeInstances",
            "ec2:DescribeInternetGateways",
            "ec2:DescribeNetworkAcls",
            "ec2:DescribeNetworkInterfaces",
            "ec2:DescribeReservedInstances",
            "ec2:DescribeRouteTables",
            "ec2:DescribeSecurityGroups",
            "ec2:DescribeSnapshots",
            "ec2:DescribeSpotDatafeedSubscription",
            "ec2:DescribeSpotFleetInstances",
            "ec2:DescribeSpotFleetRequestHistory",
            "ec2:DescribeSpotFleetRequests",
            "ec2:DescribeSpotInstanceRequests",
            "ec2:DescribeSpotPriceHistory",
            "ec2:DescribeSubnets",
            "ec2:DescribeVolumes",
            "ec2:DescribeVpcs",
        ]

    def test_find_usage_networking_sgs(self):
        mocks = fixtures.test_find_usage_networking_sgs

        mock_conn = Mock()
        mock_conn.security_groups.all.return_value = mocks

        cls = _Ec2Service(21, 43)
        cls.resource_conn = mock_conn

        with patch('awslimitchecker.services.ec2.logger') as mock_logger:
            cls._find_usage_networking_sgs()
        assert mock_logger.mock_calls == [
            call.debug("Getting usage for EC2 VPC resources"),
        ]
        limit = cls.limits['Security groups per VPC']
        # relies on AwsLimitUsage sorting by numeric usage value
        sorted_usage = sorted(limit.get_current_usage())
        assert len(sorted_usage) == 2
        assert sorted_usage[0].limit == limit
        assert sorted_usage[0].get_value() == 1
        assert sorted_usage[0].resource_id == 'vpc-bbb'
        assert sorted_usage[0].aws_type == 'AWS::EC2::VPC'
        assert sorted_usage[1].limit == limit
        assert sorted_usage[1].get_value() == 2
        assert sorted_usage[1].resource_id == 'vpc-aaa'
        assert sorted_usage[1].aws_type == 'AWS::EC2::VPC'

        limit = cls.limits['Rules per VPC security group']
        sorted_usage = sorted(limit.get_current_usage())
        assert len(sorted_usage) == 3
        assert sorted_usage[0].limit == limit
        assert sorted_usage[0].resource_id == 'sg-1'
        assert sorted_usage[0].get_value() == 0
        assert sorted_usage[1].limit == limit
        assert sorted_usage[1].resource_id == 'sg-4'
        assert sorted_usage[1].get_value() == 3
        assert sorted_usage[2].limit == limit
        assert sorted_usage[2].resource_id == 'sg-3'
        assert sorted_usage[2].get_value() == 9
        assert mock_conn.mock_calls == [
            call.security_groups.all()
        ]

    def test_find_usage_networking_eips(self):
        mocks = fixtures.test_find_usage_networking_eips

        mock_conn = Mock()
        mock_conn.classic_addresses.all.return_value = mocks['Classic']
        mock_conn.vpc_addresses.all.return_value = mocks['Vpc']
        cls = _Ec2Service(21, 43)
        cls.resource_conn = mock_conn

        with patch('awslimitchecker.services.ec2.logger') as mock_logger:
            cls._find_usage_networking_eips()
        assert mock_logger.mock_calls == [
            call.debug("Getting usage for EC2 EIPs"),
        ]
        limit = cls.limits['VPC Elastic IP addresses (EIPs)']
        usage = limit.get_current_usage()
        assert len(usage) == 1
        assert usage[0].limit == limit
        assert usage[0].get_value() == 2
        assert usage[0].resource_id is None
        assert usage[0].aws_type == 'AWS::EC2::EIP'

        limit = cls.limits['Elastic IP addresses (EIPs)']
        usage = limit.get_current_usage()
        assert len(usage) == 1
        assert usage[0].limit == limit
        assert usage[0].get_value() == 1
        assert usage[0].resource_id is None
        assert usage[0].aws_type == 'AWS::EC2::EIP'

        assert mock_conn.mock_calls == [
            call.vpc_addresses.all(),
            call.classic_addresses.all()
        ]

    def test_find_usage_networking_eni_sg(self):
        mocks = fixtures.test_find_usage_networking_eni_sg

        mock_conn = Mock()
        mock_conn.network_interfaces.all.return_value = mocks
        cls = _Ec2Service(21, 43)
        cls.resource_conn = mock_conn
        with patch('awslimitchecker.services.ec2.logger') as mock_logger:
            cls._find_usage_networking_eni_sg()
        assert mock_logger.mock_calls == [
            call.debug("Getting usage for EC2 Network Interfaces"),
        ]
        limit = cls.limits['VPC security groups per elastic network interface']
        sorted_usage = sorted(limit.get_current_usage())
        assert len(sorted_usage) == 3
        assert sorted_usage[0].limit == limit
        assert sorted_usage[0].resource_id == 'if-1'
        assert sorted_usage[0].get_value() == 0
        assert sorted_usage[1].limit == limit
        assert sorted_usage[1].resource_id == 'if-2'
        assert sorted_usage[1].get_value() == 3
        assert sorted_usage[2].limit == limit
        assert sorted_usage[2].resource_id == 'if-3'
        assert sorted_usage[2].get_value() == 8
        assert mock_conn.mock_calls == [
            call.network_interfaces.all()
        ]

    def test_get_limits_networking(self):
        cls = _Ec2Service(21, 43)
        limits = cls._get_limits_networking()
        expected = [
            'Security groups per VPC',
            'Rules per VPC security group',
            'VPC Elastic IP addresses (EIPs)',
            'Elastic IP addresses (EIPs)',
            'VPC security groups per elastic network interface',
        ]
        assert sorted(limits.keys()) == sorted(expected)
        assert limits[
                   'VPC Elastic IP addresses (EIPs)'].ta_service_name == 'VPC'

    def test_get_limits_spot(self):
        cls = _Ec2Service(21, 43)
        limits = cls._get_limits_spot()
        expected = [
            'Max spot instance requests per region',
            'Max active spot fleets per region',
            'Max launch specifications per spot fleet',
            'Max target capacity per spot fleet',
            'Max target capacity for all spot fleets in region'
        ]
        assert sorted(limits.keys()) == sorted(expected)

    def test_find_usage_spot_instances(self):
        data = fixtures.test_find_usage_spot_instances
        mock_conn = Mock()
        mock_client_conn = Mock()
        mock_client_conn.describe_spot_instance_requests.return_value = data
        cls = _Ec2Service(21, 43)
        cls.resource_conn = mock_conn
        cls.conn = mock_client_conn
        with patch('awslimitchecker.services.ec2.logger') as mock_logger:
            cls._find_usage_spot_instances()
        assert mock_conn.mock_calls == []
        assert mock_client_conn.mock_calls == [
            call.describe_spot_instance_requests()
        ]
        lim = cls.limits['Max spot instance requests per region']
        usage = lim.get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 2
        assert mock_logger.mock_calls == [
            call.debug('Getting spot instance request usage'),
            call.debug('NOT counting spot instance request %s state=%s',
                       'reqID1', 'closed'),
            call.debug('Counting spot instance request %s state=%s',
                       'reqID2', 'active'),
            call.debug('Counting spot instance request %s state=%s',
                       'reqID3', 'open'),
            call.debug('NOT counting spot instance request %s state=%s',
                       'reqID4', 'failed')
        ]

    def test_find_usage_spot_instances_unsupported(self):
        mock_client_conn = Mock()
        err = botocore.exceptions.ClientError(
            {'Error': {'Code': 'UnsupportedOperation'}},
            'operation',
        )
        mock_client_conn.describe_spot_instance_requests.side_effect = err
        cls = _Ec2Service(21, 43)
        cls.conn = mock_client_conn
        cls._find_usage_spot_instances()
        lim = cls.limits['Max spot instance requests per region']
        usage = lim.get_current_usage()
        assert len(usage) == 0

    def test_find_usage_spot_instances_unknown_code(self):
        mock_client_conn = Mock()
        err = botocore.exceptions.ClientError(
            {'Error': {'Code': 'SomeCode'}},
            'operation',
        )
        mock_client_conn.describe_spot_instance_requests.side_effect = err
        cls = _Ec2Service(21, 43)
        cls.conn = mock_client_conn
        with pytest.raises(botocore.exceptions.ClientError):
            cls._find_usage_spot_instances()

    def test_find_usage_spot_instances_unknown_error(self):
        mock_client_conn = Mock()
        err = RuntimeError
        mock_client_conn.describe_spot_instance_requests.side_effect = err
        cls = _Ec2Service(21, 43)
        cls.conn = mock_client_conn
        with pytest.raises(RuntimeError):
            cls._find_usage_spot_instances()

    def test_find_usage_spot_fleets(self):
        data = fixtures.test_find_usage_spot_fleets
        mock_conn = Mock()
        mock_client_conn = Mock()
        mock_client_conn.describe_spot_fleet_requests.return_value = data
        cls = _Ec2Service(21, 43)
        cls.resource_conn = mock_conn
        cls.conn = mock_client_conn
        with patch('awslimitchecker.services.ec2.logger') as mock_logger:
            cls._find_usage_spot_fleets()
        assert mock_conn.mock_calls == []
        assert mock_client_conn.mock_calls == [
            call.describe_spot_fleet_requests()
        ]

        total = cls.limits['Max active spot fleets per '
                           'region'].get_current_usage()
        assert len(total) == 1
        assert total[0].get_value() == 2

        totalcap = cls.limits['Max target capacity for all spot fleets '
                              'in region'].get_current_usage()
        assert len(totalcap) == 1
        assert totalcap[0].get_value() == 44

        cap_per_fleet = cls.limits['Max target capacity per spot '
                                   'fleet'].get_current_usage()
        assert len(cap_per_fleet) == 2
        assert cap_per_fleet[0].get_value() == 11
        assert cap_per_fleet[0].resource_id == 'req2'
        assert cap_per_fleet[1].get_value() == 33
        assert cap_per_fleet[1].resource_id == 'req4'

        launch_specs = cls.limits['Max launch specifications '
                                  'per spot fleet'].get_current_usage()
        assert len(launch_specs) == 2
        assert launch_specs[0].get_value() == 3
        assert launch_specs[0].resource_id == 'req2'
        assert launch_specs[1].get_value() == 1
        assert launch_specs[1].resource_id == 'req4'

        assert mock_logger.mock_calls == [
            call.debug('Getting spot fleet request usage'),
            call.debug('Skipping spot fleet request %s in state %s', 'req1',
                       'failed'),
            call.debug('Skipping spot fleet request %s in state %s',
                       'req3', 'modifying')
        ]

    def test_find_usage_spot_fleets_paginated(self):
        data = deepcopy(fixtures.test_find_usage_spot_fleets)
        data['NextToken'] = 'string'
        mock_conn = Mock()
        mock_client_conn = Mock()
        mock_client_conn.describe_spot_fleet_requests.return_value = data
        cls = _Ec2Service(21, 43)
        cls.resource_conn = mock_conn
        cls.conn = mock_client_conn
        with patch('awslimitchecker.services.ec2.logger') as mock_logger:
            cls._find_usage_spot_fleets()
        assert mock_conn.mock_calls == []
        assert mock_client_conn.mock_calls == [
            call.describe_spot_fleet_requests()
        ]

        total = cls.limits['Max active spot fleets per '
                           'region'].get_current_usage()
        assert len(total) == 1
        assert total[0].get_value() == 2

        totalcap = cls.limits['Max target capacity for all spot fleets '
                              'in region'].get_current_usage()
        assert len(totalcap) == 1
        assert totalcap[0].get_value() == 44

        cap_per_fleet = cls.limits['Max target capacity per spot '
                                   'fleet'].get_current_usage()
        assert len(cap_per_fleet) == 2
        assert cap_per_fleet[0].get_value() == 11
        assert cap_per_fleet[0].resource_id == 'req2'
        assert cap_per_fleet[1].get_value() == 33
        assert cap_per_fleet[1].resource_id == 'req4'

        launch_specs = cls.limits['Max launch specifications '
                                  'per spot fleet'].get_current_usage()
        assert len(launch_specs) == 2
        assert launch_specs[0].get_value() == 3
        assert launch_specs[0].resource_id == 'req2'
        assert launch_specs[1].get_value() == 1
        assert launch_specs[1].resource_id == 'req4'

        assert mock_logger.mock_calls == [
            call.debug('Getting spot fleet request usage'),
            call.error('Error: describe_spot_fleet_requests() response '
                       'includes pagination token, but pagination not '
                       'configured in awslimitchecker.'),
            call.debug('Skipping spot fleet request %s in state %s', 'req1',
                       'failed'),
            call.debug('Skipping spot fleet request %s in state %s',
                       'req3', 'modifying')
        ]

    def test_find_usage_spot_fleets_unsupported(self):
        mock_client_conn = Mock()
        err = botocore.exceptions.ClientError(
            {'Error': {'Code': 'UnsupportedOperation'}},
            'operation',
        )
        mock_client_conn.describe_spot_fleet_requests.side_effect = err
        cls = _Ec2Service(21, 43)
        cls.conn = mock_client_conn
        cls._find_usage_spot_fleets()
        total = cls.limits['Max active spot fleets per '
                           'region'].get_current_usage()
        assert len(total) == 0

    def test_find_usage_spot_fleets_unknown_code(self):
        mock_client_conn = Mock()
        err = botocore.exceptions.ClientError(
            {'Error': {'Code': 'SomeCode'}},
            'operation',
        )
        mock_client_conn.describe_spot_fleet_requests.side_effect = err
        cls = _Ec2Service(21, 43)
        cls.conn = mock_client_conn
        with pytest.raises(botocore.exceptions.ClientError):
            cls._find_usage_spot_fleets()

    def test_find_usage_spot_fleets_unknown_error(self):
        mock_client_conn = Mock()
        mock_client_conn.describe_spot_fleet_requests.side_effect = RuntimeError
        cls = _Ec2Service(21, 43)
        cls.conn = mock_client_conn
        with pytest.raises(RuntimeError):
            cls._find_usage_spot_fleets()

    def test_update_limits_from_api(self):
        data = fixtures.test_update_limits_from_api
        mock_conn = Mock()
        mock_client_conn = Mock()
        mock_client_conn.describe_account_attributes.return_value = data

        cls = _Ec2Service(21, 43)
        cls.resource_conn = mock_conn
        cls.conn = mock_client_conn
        with patch('awslimitchecker.services.ec2.logger') as mock_logger:
            cls._update_limits_from_api()
        assert mock_conn.mock_calls == []
        assert mock_client_conn.mock_calls == [
            call.describe_account_attributes()
        ]
        assert mock_logger.mock_calls == [
            call.info("Querying EC2 DescribeAccountAttributes for limits"),
            call.debug('Done setting limits from API')
        ]
        assert cls.limits['Elastic IP addresses (EIPs)'].api_limit == 40
        assert cls.limits['Running On-Demand EC2 instances'].api_limit == 400
        assert cls.limits['VPC Elastic IP addresses (EIPs)'].api_limit == 200
        assert cls.limits['VPC security groups per elastic '
                          'network interface'].api_limit == 5

    def test_update_limits_from_api_unsupported(self):
        data = fixtures.test_update_limits_from_api_unsupported
        mock_client_conn = Mock()
        mock_client_conn.describe_account_attributes.return_value = data

        cls = _Ec2Service(21, 43)
        cls.conn = mock_client_conn
        cls._update_limits_from_api()
        lim = cls.limits['Elastic IP addresses (EIPs)']
        usage = lim.get_current_usage()
        assert len(usage) == 0
