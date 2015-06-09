"""
awslimitchecker/tests/services/test_ec2.py

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
bugs please submit them at <https://github.com/jantman/pydnstest> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

from mock import Mock, patch, call
from contextlib import nested
from boto.ec2.connection import EC2Connection
from boto.ec2.instance import Instance, Reservation
from boto.ec2.reservedinstance import ReservedInstance
from boto.ec2.securitygroup import SecurityGroup
from boto.ec2.volume import Volume
from awslimitchecker.services.ec2 import _Ec2Service
from awslimitchecker.limit import AwsLimit


class Test_Ec2Service(object):

    pb = 'awslimitchecker.services.ec2._Ec2Service'  # patch base path

    def test_init(self):
        """test __init__()"""
        cls = _Ec2Service(21, 43)
        assert cls.service_name == 'EC2'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_connect(self):
        """test connect()"""
        mock_conn = Mock()
        cls = _Ec2Service(21, 43)
        with patch('awslimitchecker.services.ec2.boto.connect_ec2') as mock_ec2:
            mock_ec2.return_value = mock_conn
            cls.connect()
        assert mock_ec2.mock_calls == [call()]
        assert mock_conn.mock_calls == []

    def test_connect_again(self):
        """make sure we re-use the connection"""
        mock_conn = Mock()
        cls = _Ec2Service(21, 43)
        cls.conn = mock_conn
        with patch('awslimitchecker.services.ec2.boto.connect_ec2') as mock_ec2:
            mock_ec2.return_value = mock_conn
            cls.connect()
        assert mock_ec2.mock_calls == []
        assert mock_conn.mock_calls == []

    def test_instance_types(self):
        cls = _Ec2Service(21, 43)
        types = cls._instance_types()
        assert len(types) == 47
        assert 't2.micro' in types
        assert 'r3.8xlarge' in types
        assert 'c3.large' in types
        assert 'i2.4xlarge' in types
        assert 'd2.2xlarge' in types
        assert 'g2.8xlarge' in types
        assert 'hs1.8xlarge' in types
        assert 'cg1.4xlarge' in types

    def test_get_limits(self):
        cls = _Ec2Service(21, 43)
        cls.limits = {}
        with nested(
                patch('%s._get_limits_instances' % self.pb),
                patch('%s._get_limits_ebs' % self.pb),
                patch('%s._get_limits_vpc' % self.pb),
        ) as (
            mock_instances,
            mock_ebs,
            mock_vpc
        ):
            mock_instances.return_value = {'ec2lname': 'ec2lval'}
            mock_ebs.return_value = {'ebslname': 'ebslval'}
            mock_vpc.return_value = {'vpck': 'vpcv'}
            res = cls.get_limits()
        assert res == {
            'ec2lname': 'ec2lval',
            'ebslname': 'ebslval',
            'vpck': 'vpcv',
        }
        assert mock_instances.mock_calls == [call()]
        assert mock_ebs.mock_calls == [call()]
        assert mock_vpc.mock_calls == [call()]

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        cls = _Ec2Service(21, 43)
        cls.limits = {'foo': 'bar'}
        with nested(
                patch('%s._get_limits_instances' % self.pb),
                patch('%s._get_limits_ebs' % self.pb),
                patch('%s._get_limits_vpc' % self.pb),
        ) as (
            mock_instances,
            mock_ebs,
            mock_vpc,
        ):
            res = cls.get_limits()
        assert res == {'foo': 'bar'}
        assert mock_instances.mock_calls == []
        assert mock_ebs.mock_calls == []
        assert mock_vpc.mock_calls == []

    def test_get_limits_all(self):
        """test some things all limits should conform to"""
        cls = _Ec2Service(21, 43)
        limits = cls.get_limits()
        for x in limits:
            assert isinstance(limits[x], AwsLimit)
            assert x == limits[x].name
            assert limits[x].service_name == 'EC2'

    def test_get_limits_ebs(self):
        cls = _Ec2Service(21, 43)
        limits = cls._get_limits_ebs()
        assert len(limits) == 4
        piops = limits['Provisioned IOPS']
        assert piops.limit_type == 'AWS::EC2::Volume'
        assert piops.limit_subtype == 'io1'
        piops_tb = limits['Provisioned IOPS (SSD) volume storage (TiB)']
        assert piops_tb.limit_type == 'AWS::EC2::Volume'
        assert piops_tb.limit_subtype == 'io1'
        gp_tb = limits['General Purpose (SSD) volume storage (TiB)']
        assert gp_tb.limit_type == 'AWS::EC2::Volume'
        assert gp_tb.limit_subtype == 'gp2'
        mag_tb = limits['Magnetic volume storage (TiB)']
        assert mag_tb.limit_type == 'AWS::EC2::Volume'
        assert mag_tb.limit_subtype == 'standard'

    def test_get_limits_instances(self):
        cls = _Ec2Service(21, 43)
        limits = cls._get_limits_instances()
        assert len(limits) == 48
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
        all_ec2 = limits['Running On-Demand EC2 instances']
        assert all_ec2.default_limit == 20
        assert all_ec2.limit_type == 'On-Demand instances'
        assert all_ec2.limit_subtype is None

    def test_find_usage(self):
        with nested(
                patch('%s.connect' % self.pb, autospec=True),
                patch('%s._find_usage_instances' % self.pb, autospec=True),
                patch('%s._find_usage_ebs' % self.pb, autospec=True),
                patch('%s._find_usage_vpc' % self.pb, autospec=True),
        ) as (
            mock_connect,
            mock_instances,
            mock_ebs,
            mock_vpc,
        ):
            cls = _Ec2Service(21, 43)
            assert cls._have_usage is False
            cls.find_usage()
        assert cls._have_usage is True
        assert mock_connect.mock_calls == [call(cls)]
        assert mock_instances.mock_calls == [call(cls)]
        assert mock_ebs.mock_calls == [call(cls)]
        assert mock_vpc.mock_calls == [call(cls)]

    def test_instance_usage(self):
        mock_t2_micro = Mock(spec_set=AwsLimit)
        mock_r3_2xlarge = Mock(spec_set=AwsLimit)
        mock_c4_4xlarge = Mock(spec_set=AwsLimit)
        limits = {
            'Running On-Demand t2.micro instances': mock_t2_micro,
            'Running On-Demand r3.2xlarge instances': mock_r3_2xlarge,
            'Running On-Demand c4.4xlarge instances': mock_c4_4xlarge,
        }

        cls = _Ec2Service(21, 43)
        mock_inst1A = Mock(spec_set=Instance)
        type(mock_inst1A).id = '1A'
        type(mock_inst1A).instance_type = 't2.micro'
        type(mock_inst1A).spot_instance_request_id = None
        type(mock_inst1A).placement = 'az1a'

        mock_inst1B = Mock(spec_set=Instance)
        type(mock_inst1B).id = '1B'
        type(mock_inst1B).instance_type = 'r3.2xlarge'
        type(mock_inst1B).spot_instance_request_id = None
        type(mock_inst1B).placement = 'az1a'

        mock_res1 = Mock(spec_set=Reservation)
        type(mock_res1).instances = [mock_inst1A, mock_inst1B]

        mock_inst2A = Mock(spec_set=Instance)
        type(mock_inst2A).id = '2A'
        type(mock_inst2A).instance_type = 'c4.4xlarge'
        type(mock_inst2A).spot_instance_request_id = None
        type(mock_inst2A).placement = 'az1a'

        mock_inst2B = Mock(spec_set=Instance)
        type(mock_inst2B).id = '2B'
        type(mock_inst2B).instance_type = 't2.micro'
        type(mock_inst2B).spot_instance_request_id = '1234'
        type(mock_inst2B).placement = 'az1a'

        mock_res2 = Mock(spec_set=Reservation)
        type(mock_res2).instances = [mock_inst2A, mock_inst2B]

        mock_conn = Mock(spec_set=EC2Connection)
        mock_conn.get_all_reservations.return_value = [
            mock_res1,
            mock_res2
        ]
        cls.conn = mock_conn
        cls.limits = limits
        with patch('awslimitchecker.services.ec2._Ec2Service._instance_types',
                   autospec=True) as mock_itypes:
            mock_itypes.return_value = [
                't2.micro',
                'r3.2xlarge',
                'c4.4xlarge',
            ]
            res = cls._instance_usage()
        assert res == {
            'az1a': {
                't2.micro': 1,
                'r3.2xlarge': 1,
                'c4.4xlarge': 1,
            }
        }

    def test_get_reserved_instance_count(self):
        mock_res1 = Mock(spec_set=ReservedInstance)
        type(mock_res1).state = 'active'
        type(mock_res1).id = 'res1'
        type(mock_res1).availability_zone = 'az1'
        type(mock_res1).instance_type = 'it1'
        type(mock_res1).instance_count = 1

        mock_res2 = Mock(spec_set=ReservedInstance)
        type(mock_res2).state = 'inactive'
        type(mock_res2).id = 'res2'
        type(mock_res2).availability_zone = 'az1'
        type(mock_res2).instance_type = 'it2'
        type(mock_res2).instance_count = 1

        mock_res3 = Mock(spec_set=ReservedInstance)
        type(mock_res3).state = 'active'
        type(mock_res3).id = 'res3'
        type(mock_res3).availability_zone = 'az1'
        type(mock_res3).instance_type = 'it1'
        type(mock_res3).instance_count = 9

        mock_res4 = Mock(spec_set=ReservedInstance)
        type(mock_res4).state = 'active'
        type(mock_res4).id = 'res4'
        type(mock_res4).availability_zone = 'az2'
        type(mock_res4).instance_type = 'it2'
        type(mock_res4).instance_count = 98

        cls = _Ec2Service(21, 43)
        mock_conn = Mock(spec_set=EC2Connection)
        mock_conn.get_all_reserved_instances.return_value = [
            mock_res1,
            mock_res2,
            mock_res3,
            mock_res4
        ]
        cls.conn = mock_conn
        res = cls._get_reserved_instance_count()
        assert res == {
            'az1': {
                'it1': 10,
            },
            'az2': {
                'it2': 98,
            },
        }
        assert mock_conn.mock_calls == [call.get_all_reserved_instances()]

    def test_find_usage_instances(self):
        iusage = {
            'us-east-1': {
                't2.micro': 2,
                'r3.2xlarge': 10,
                'c4.4xlarge': 3,
            },
            'fooaz': {
                't2.micro': 32,
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
        }

        mock_t2_micro = Mock(spec_set=AwsLimit)
        mock_r3_2xlarge = Mock(spec_set=AwsLimit)
        mock_c4_4xlarge = Mock(spec_set=AwsLimit)
        mock_all_ec2 = Mock(spec_set=AwsLimit)
        limits = {
            'Running On-Demand t2.micro instances': mock_t2_micro,
            'Running On-Demand r3.2xlarge instances': mock_r3_2xlarge,
            'Running On-Demand c4.4xlarge instances': mock_c4_4xlarge,
            'Running On-Demand EC2 instances': mock_all_ec2,
        }

        cls = _Ec2Service(21, 43)
        mock_conn = Mock(spec_set=EC2Connection)
        cls.conn = mock_conn
        cls.limits = limits
        with nested(
                patch('awslimitchecker.services.ec2._Ec2Service.'
                      '_instance_usage', autospec=True),
                patch('awslimitchecker.services.ec2._Ec2Service.'
                      '_get_reserved_instance_count', autospec=True),
        ) as (
            mock_inst_usage,
            mock_res_inst_count,
        ):
            mock_inst_usage.return_value = iusage
            mock_res_inst_count.return_value = ri_count
            cls._find_usage_instances()
        assert mock_t2_micro.mock_calls == [call._add_current_usage(
            36,
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
        assert mock_all_ec2.mock_calls == [call._add_current_usage(
            49,
            aws_type='AWS::EC2::Instance'
        )]
        assert mock_inst_usage.mock_calls == [call(cls)]
        assert mock_res_inst_count.mock_calls == [call(cls)]

    def test_find_usage_instances_key_error(self):
        mock_inst1A = Mock(spec_set=Instance)
        type(mock_inst1A).id = '1A'
        type(mock_inst1A).instance_type = 'foobar'
        type(mock_inst1A).spot_instance_request_id = None
        mock_res1 = Mock(spec_set=Reservation)
        type(mock_res1).instances = [mock_inst1A]

        mock_conn = Mock(spec_set=EC2Connection)
        mock_conn.get_all_reservations.return_value = [mock_res1]
        cls = _Ec2Service(21, 43)
        cls.conn = mock_conn
        cls.limits = {'Running On-Demand t2.micro instances': Mock()}
        with patch('awslimitchecker.services.ec2._Ec2Service._instance_types',
                   autospec=True) as mock_itypes:
            mock_itypes.return_value = ['t2.micro']
            with patch('awslimitchecker.services.ec2.logger') as mock_logger:
                cls._instance_usage()
        assert mock_logger.mock_calls == [
            call.debug('Getting usage for on-demand instances'),
            call.error("ERROR - unknown instance type 'foobar'; not counting"),
        ]

    def test_find_usage_ebs(self):
        # 500G magnetic
        mock_vol1 = Mock(spec_set=Volume)
        type(mock_vol1).id = 'vol-1'
        type(mock_vol1).type = 'standard'  # magnetic
        type(mock_vol1).size = 500
        type(mock_vol1).iops = None

        # 8G magnetic
        mock_vol2 = Mock(spec_set=Volume)
        type(mock_vol2).id = 'vol-2'
        type(mock_vol2).type = 'standard'  # magnetic
        type(mock_vol2).size = 8
        type(mock_vol2).iops = None

        # 15G general purpose SSD, 45 IOPS
        mock_vol3 = Mock(spec_set=Volume)
        type(mock_vol3).id = 'vol-3'
        type(mock_vol3).type = 'gp2'
        type(mock_vol3).size = 15
        type(mock_vol3).iops = 45

        # 30G general purpose SSD, 90 IOPS
        mock_vol4 = Mock(spec_set=Volume)
        type(mock_vol4).id = 'vol-4'
        type(mock_vol4).type = 'gp2'
        type(mock_vol4).size = 30
        type(mock_vol4).iops = 90

        # 400G PIOPS, 700 IOPS
        mock_vol5 = Mock(spec_set=Volume)
        type(mock_vol5).id = 'vol-5'
        type(mock_vol5).type = 'io1'
        type(mock_vol5).size = 400
        type(mock_vol5).iops = 700

        # 100G PIOPS, 300 IOPS
        mock_vol6 = Mock(spec_set=Volume)
        type(mock_vol6).id = 'vol-6'
        type(mock_vol6).type = 'io1'
        type(mock_vol6).size = 100
        type(mock_vol6).iops = 300

        mock_vol7 = Mock(spec_set=Volume)
        type(mock_vol7).id = 'vol-7'
        type(mock_vol7).type = 'othertype'

        mock_conn = Mock(spec_set=EC2Connection)
        mock_conn.get_all_volumes.return_value = [
            mock_vol1,
            mock_vol2,
            mock_vol3,
            mock_vol4,
            mock_vol5,
            mock_vol6,
            mock_vol7
        ]
        cls = _Ec2Service(21, 43)
        cls.conn = mock_conn
        with patch('awslimitchecker.services.ec2.logger') as mock_logger:
            cls._find_usage_ebs()
        assert mock_logger.mock_calls == [
            call.debug("Getting usage for EBS volumes"),
            call.error("ERROR - unknown volume type 'othertype' for volume "
                       "vol-7; not counting")
        ]
        assert len(cls.limits['Provisioned IOPS'].get_current_usage()) == 1
        assert cls.limits['Provisioned IOPS'
                          ''].get_current_usage()[0].get_value() == 1000
        assert len(cls.limits['Provisioned IOPS (SSD) volume storage '
                              '(TiB)'].get_current_usage()) == 1
        assert cls.limits['Provisioned IOPS (SSD) volume storage '
                          '(TiB)'].get_current_usage()[0].get_value() == 0.5
        assert len(cls.limits['General Purpose (SSD) volume storage '
                              '(TiB)'].get_current_usage()) == 1
        assert cls.limits['General Purpose (SSD) volume storage '
                          '(TiB)'].get_current_usage()[0].get_value() == 0.045
        assert len(cls.limits['Magnetic volume storage '
                              '(TiB)'].get_current_usage()) == 1
        assert cls.limits['Magnetic volume storage '
                          '(TiB)'].get_current_usage()[0].get_value() == 0.508

    def test_required_iam_permissions(self):
        cls = _Ec2Service(21, 43)
        assert cls.required_iam_permissions() == [
            "ec2:DescribeInstances",
            "ec2:DescribeReservedInstances",
            "ec2:DescribeVolumes",
            "ec2:DescribeSecurityGroups",
        ]

    def test_find_usage_vpc(self):
        mock_sg1 = Mock(spec_set=SecurityGroup)
        type(mock_sg1).id = 'sg-1'
        type(mock_sg1).vpc_id = 'vpc-aaa'
        mock_sg2 = Mock(spec_set=SecurityGroup)
        type(mock_sg2).id = 'sg-2'
        type(mock_sg2).vpc_id = None
        mock_sg3 = Mock(spec_set=SecurityGroup)
        type(mock_sg3).id = 'sg-3'
        type(mock_sg3).vpc_id = 'vpc-bbb'
        mock_sg4 = Mock(spec_set=SecurityGroup)
        type(mock_sg4).id = 'sg-4'
        type(mock_sg4).vpc_id = 'vpc-aaa'

        mock_conn = Mock(spec_set=EC2Connection)
        mock_conn.get_all_security_groups.return_value = [
            mock_sg1,
            mock_sg2,
            mock_sg3,
            mock_sg4,
        ]
        cls = _Ec2Service(21, 43)
        cls.conn = mock_conn
        with patch('awslimitchecker.services.ec2.logger') as mock_logger:
            cls._find_usage_vpc()
        assert mock_logger.mock_calls == [
            call.debug("Getting usage for EC2 VPC resources"),
        ]
        limit = cls.limits['Security groups per VPC']
        # relies on AwsLimitUsage sorting by numeric usage value
        sorted_usage = sorted(limit.get_current_usage())
        assert len(sorted_usage) == 2
        assert sorted_usage[0].limit == limit
        assert sorted_usage[0].get_value() == 1
        assert sorted_usage[0].id == 'vpc-bbb'
        assert sorted_usage[0].aws_type == 'AWS::EC2::VPC'
        assert sorted_usage[1].limit == limit
        assert sorted_usage[1].get_value() == 2
        assert sorted_usage[1].id == 'vpc-aaa'
        assert sorted_usage[1].aws_type == 'AWS::EC2::VPC'

    def test_get_limits_vpc(self):
        cls = _Ec2Service(21, 43)
        limits = cls._get_limits_vpc()
        assert len(limits) == 1
        for x in limits:
            assert limits[x].limit_type == 'AWS::EC2::VPC'
        assert 'Security groups per VPC' in limits
