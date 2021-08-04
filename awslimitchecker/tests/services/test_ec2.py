"""
awslimitchecker/tests/services/test_ec2.py

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

import os
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
    from mock import patch, call, Mock, DEFAULT, PropertyMock
else:
    from unittest.mock import patch, call, Mock, DEFAULT, PropertyMock

fixtures = result_fixtures.EC2()
pb = 'awslimitchecker.services.ec2._Ec2Service'  # patch base path


class TestInit(object):

    def test_simple(self):
        """test __init__()"""
        cls = _Ec2Service(21, 43, {}, None)
        assert cls.service_name == 'EC2'
        assert cls.conn is None
        assert cls.resource_conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43
        assert cls.quotas_service_code == 'ec2'


class TestInstanceTypes(object):

    def test_simple(self):
        cls = _Ec2Service(21, 43, {}, None)
        types = cls._instance_types()
        # NOTE hi1.4xlarge is no longer in the instance type listings,
        # but some accounts might still have a limit for it
        assert len(set(types)) == len(types)
        assert len(types) == 268
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
        assert 'z1d.12xlarge' in types
        assert 'u-24tb1.metal' in types
        assert 'm5n.metal' in types


class TestGetLimits(object):

    def test_nonvcpu(self):
        cls = _Ec2Service(21, 43, {}, None)
        cls.limits = {}
        with patch.multiple(
            pb,
            _get_limits_instances_nonvcpu=DEFAULT,
            _get_limits_instances_vcpu=DEFAULT,
            _get_limits_networking=DEFAULT,
            _get_limits_spot=DEFAULT,
            autospec=True
        ) as mocks:
            mocks['_get_limits_instances_nonvcpu'].return_value = {
                'ec2lname': 'ec2lval'
            }
            mocks['_get_limits_instances_vcpu'].return_value = {
                'fooname': 'fooval'
            }
            mocks['_get_limits_networking'].return_value = {'vpck': 'vpcv'}
            mocks['_get_limits_spot'].return_value = {'spotk': 'spotv'}
            with patch(
                '%s._use_vcpu_limits' % pb, new_callable=PropertyMock
            ) as m_use_vcpu:
                m_use_vcpu.return_value = False
                res = cls.get_limits()
        assert res == {
            'ec2lname': 'ec2lval',
            'spotk': 'spotv',
            'vpck': 'vpcv',
        }
        assert mocks['_get_limits_instances_nonvcpu'].mock_calls == [
            call(cls)
        ]
        assert mocks['_get_limits_instances_vcpu'].mock_calls == []
        assert mocks['_get_limits_networking'].mock_calls == [call(cls)]
        assert mocks['_get_limits_spot'].mock_calls == [call(cls)]

    def test_vcpu(self):
        cls = _Ec2Service(21, 43, {}, None)
        cls.limits = {}
        with patch.multiple(
            pb,
            _get_limits_instances_nonvcpu=DEFAULT,
            _get_limits_instances_vcpu=DEFAULT,
            _get_limits_networking=DEFAULT,
            _get_limits_spot=DEFAULT,
            autospec=True
        ) as mocks:
            mocks['_get_limits_instances_nonvcpu'].return_value = {
                'ec2lname': 'ec2lval'
            }
            mocks['_get_limits_instances_vcpu'].return_value = {
                'fooname': 'fooval'
            }
            mocks['_get_limits_networking'].return_value = {'vpck': 'vpcv'}
            mocks['_get_limits_spot'].return_value = {'spotk': 'spotv'}
            with patch(
                '%s._use_vcpu_limits' % pb, new_callable=PropertyMock
            ) as m_use_vcpu:
                m_use_vcpu.return_value = True
                res = cls.get_limits()
        assert res == {
            'fooname': 'fooval',
            'spotk': 'spotv',
            'vpck': 'vpcv',
        }
        assert mocks['_get_limits_instances_nonvcpu'].mock_calls == []
        assert mocks['_get_limits_instances_vcpu'].mock_calls == [call(cls)]
        assert mocks['_get_limits_networking'].mock_calls == [call(cls)]
        assert mocks['_get_limits_spot'].mock_calls == [call(cls)]

    def test_get_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        cls = _Ec2Service(21, 43, {}, None)
        cls.limits = {'foo': 'bar'}
        with patch.multiple(
            pb,
            _get_limits_instances_nonvcpu=DEFAULT,
            _get_limits_instances_vcpu=DEFAULT,
            _get_limits_networking=DEFAULT,
            _get_limits_spot=DEFAULT,
            autospec=True
        ) as mocks:
            mocks['_get_limits_instances_nonvcpu'].return_value = {
                'ec2lname': 'ec2lval'
            }
            mocks['_get_limits_instances_vcpu'].return_value = {
                'fooname': 'fooval'
            }
            mocks['_get_limits_networking'].return_value = {'vpck': 'vpcv'}
            mocks['_get_limits_spot'].return_value = {'spotk': 'spotv'}
            with patch(
                '%s._use_vcpu_limits' % pb, new_callable=PropertyMock
            ) as m_use_vcpu:
                m_use_vcpu.return_value = False
                res = cls.get_limits()
        assert res == {'foo': 'bar'}
        assert mocks['_get_limits_instances_nonvcpu'].mock_calls == []
        assert mocks['_get_limits_instances_vcpu'].mock_calls == []
        assert mocks['_get_limits_networking'].mock_calls == []
        assert mocks['_get_limits_spot'].mock_calls == []

    def test_all_nonvcpu(self):
        """test some things all limits should conform to"""
        with patch(
                '%s._use_vcpu_limits' % pb, new_callable=PropertyMock
        ) as m_use_vcpu:
            m_use_vcpu.return_value = False
            cls = _Ec2Service(21, 43, {}, None)
            limits = cls.get_limits()
        for x in limits:
            assert isinstance(limits[x], AwsLimit)
            assert x == limits[x].name
            assert limits[x].service == cls

    def test_all_vcpu(self):
        """test some things all limits should conform to"""
        with patch(
                '%s._use_vcpu_limits' % pb, new_callable=PropertyMock
        ) as m_use_vcpu:
            m_use_vcpu.return_value = True
            cls = _Ec2Service(21, 43, {}, None)
            limits = cls.get_limits()
        for x in limits:
            assert isinstance(limits[x], AwsLimit)
            assert x == limits[x].name
            assert limits[x].service == cls


class TestGetLimitsInstancesNonvcpu(object):

    def test_simple(self):
        cls = _Ec2Service(21, 43, {}, None)
        limits = cls._get_limits_instances_nonvcpu()
        assert len(limits) == 269
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


class TestGetLimitsInstancesVcpu(object):

    def test_simple(self):
        cls = _Ec2Service(21, 43, {}, None)
        limits = cls._get_limits_instances_vcpu()
        assert len(limits) == 5
        for k in ['f', 'g', 'p', 'x']:
            lim = limits['Running On-Demand All %s instances' % k.upper()]
            assert lim.default_limit == 128
            assert lim.limit_type == 'On-Demand instances'
            assert lim.limit_subtype == k.upper()
        k = 'Running On-Demand All Standard ' \
            '(A, C, D, H, I, M, R, T, Z) instances'
        lim = limits[k]
        assert lim.default_limit == 1152
        assert lim.limit_type == 'On-Demand instances'
        assert lim.limit_subtype == 'Standard'


class TestFindUsage(object):

    def test_nonvcpu(self):
        with patch.multiple(
                pb,
                connect=DEFAULT,
                _find_usage_instances_nonvcpu=DEFAULT,
                _find_usage_instances_vcpu=DEFAULT,
                _find_usage_networking_sgs=DEFAULT,
                _find_usage_networking_eips=DEFAULT,
                _find_usage_networking_eni_sg=DEFAULT,
                _find_usage_spot_instances=DEFAULT,
                _find_usage_spot_fleets=DEFAULT,
                autospec=True,
        ) as mocks:
            with patch(
                    '%s._use_vcpu_limits' % pb, new_callable=PropertyMock
            ) as m_use_vcpu:
                m_use_vcpu.return_value = False
                cls = _Ec2Service(21, 43, {}, None)
                assert cls._have_usage is False
                cls.find_usage()
        assert cls._have_usage is True
        assert mocks['_find_usage_instances_nonvcpu'].mock_calls == [
            call(cls)
        ]
        assert mocks['_find_usage_instances_vcpu'].mock_calls == []
        assert mocks['_find_usage_networking_sgs'].mock_calls == [
            call(cls)
        ]
        assert mocks['_find_usage_networking_eips'].mock_calls == [
            call(cls)
        ]
        assert mocks['_find_usage_networking_eni_sg'].mock_calls == [
            call(cls)
        ]
        assert mocks['_find_usage_spot_instances'].mock_calls == [
            call(cls)
        ]
        assert mocks['_find_usage_spot_fleets'].mock_calls == [
            call(cls)
        ]

    def test_vcpu(self):
        with patch.multiple(
                pb,
                connect=DEFAULT,
                _find_usage_instances_nonvcpu=DEFAULT,
                _find_usage_instances_vcpu=DEFAULT,
                _find_usage_networking_sgs=DEFAULT,
                _find_usage_networking_eips=DEFAULT,
                _find_usage_networking_eni_sg=DEFAULT,
                _find_usage_spot_instances=DEFAULT,
                _find_usage_spot_fleets=DEFAULT,
                autospec=True,
        ) as mocks:
            with patch(
                    '%s._use_vcpu_limits' % pb, new_callable=PropertyMock
            ) as m_use_vcpu:
                m_use_vcpu.return_value = True
                cls = _Ec2Service(21, 43, {}, None)
                assert cls._have_usage is False
                cls.find_usage()
        assert cls._have_usage is True
        assert mocks['_find_usage_instances_nonvcpu'].mock_calls == []
        assert mocks['_find_usage_instances_vcpu'].mock_calls == [
            call(cls)
        ]
        assert mocks['_find_usage_networking_sgs'].mock_calls == [
            call(cls)
        ]
        assert mocks['_find_usage_networking_eips'].mock_calls == [
            call(cls)
        ]
        assert mocks['_find_usage_networking_eni_sg'].mock_calls == [
            call(cls)
        ]
        assert mocks['_find_usage_spot_instances'].mock_calls == [
            call(cls)
        ]
        assert mocks['_find_usage_spot_fleets'].mock_calls == [
            call(cls)
        ]


class TestInstanceUsage(object):

    def test_simple(self):
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

        cls = _Ec2Service(21, 43, {}, None)
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

    def test_key_error(self):
        mock_conn = Mock()
        data = fixtures.test_instance_usage_key_error
        mock_conn.instances.all.return_value = data
        cls = _Ec2Service(21, 43, {}, None)
        cls.resource_conn = mock_conn
        cls.limits = {'Running On-Demand t2.micro instances': Mock()}

        with patch(
                '%s._instance_types' % pb,
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


class TestInstanceUsageVcpu(object):

    def test_no_RIs(self):
        cls = _Ec2Service(21, 43, {}, None)
        mock_conn = Mock()
        retval = fixtures.test_instance_usage_vcpu
        mock_conn.instances.all.return_value = retval
        cls.resource_conn = mock_conn

        res = cls._instance_usage_vcpu({})
        assert res == {
            'c': 16,
            'f': 72,
            'g': 48,
            'm': 32,
            'r': 16,
            't': 2,
            'p': 128,
            'x': 256,
        }
        assert mock_conn.mock_calls == [
            call.instances.all()
        ]

    def test_with_RIs(self):
        cls = _Ec2Service(21, 43, {}, None)
        mock_conn = Mock()
        retval = fixtures.test_instance_usage_vcpu
        mock_conn.instances.all.return_value = retval
        cls.resource_conn = mock_conn

        res = cls._instance_usage_vcpu({
            'az1a': {
                'f1.2xlarge': 10,
                'c4.4xlarge': 8,
                'c4.2xlarge': 16,
            },
            'az1c': {
                'x1e.32xlarge': 1,
                'p2.8xlarge': 1,
                'p2.16xlarge': 1
            }
        })
        assert res == {
            'f': 64,
            'g': 48,
            'm': 32,
            'r': 16,
            't': 2,
            'p': 32,
            'x': 128,
        }
        assert mock_conn.mock_calls == [
            call.instances.all()
        ]


class TestGetReservedInstanceCount(object):

    def test_simple(self):
        response = fixtures.test_get_reserved_instance_count

        cls = _Ec2Service(21, 43, {}, None)
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


class TestFindUsageInstancesNonvcpu(object):

    def test_simple(self):
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

        cls = _Ec2Service(21, 43, {}, None)
        mock_conn = Mock()
        cls.resource_conn = mock_conn
        cls.limits = limits
        with patch('%s._instance_usage' % pb,
                   autospec=True) as mock_inst_usage:
            with patch('%s._get_reserved_instance_count' % pb,
                       autospec=True) as mock_res_inst_count:
                mock_inst_usage.return_value = iusage
                mock_res_inst_count.return_value = ri_count
                cls._find_usage_instances_nonvcpu()
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
        assert mock_c4_large.mock_calls == [call._add_current_usage(
            4,
            aws_type='AWS::EC2::Instance'
        )]
        assert mock_all_ec2.mock_calls == [call._add_current_usage(
            53,
            aws_type='AWS::EC2::Instance'
        )]
        assert mock_inst_usage.mock_calls == [call(cls)]
        assert mock_res_inst_count.mock_calls == [call(cls)]
        assert mock_conn.mock_calls == []


class TestFindUsageInstancesVcpu(object):

    def test_happy_path(self):
        usage = {
            'c': 16,
            'f': 72,
            'g': 48,
            'm': 32,
            'r': 16,
            't': 2,
            'p': 128,
            'x': 256,
            'a': 512,
            'k': 3
        }

        mock_f = Mock(spec_set=AwsLimit)
        mock_g = Mock(spec_set=AwsLimit)
        mock_p = Mock(spec_set=AwsLimit)
        mock_x = Mock(spec_set=AwsLimit)
        mock_std = Mock(spec_set=AwsLimit)
        limits = {
            'Running On-Demand All F instances': mock_f,
            'Running On-Demand All G instances': mock_g,
            'Running On-Demand All P instances': mock_p,
            'Running On-Demand All X instances': mock_x,
            'Running On-Demand All Standard '
            '(A, C, D, H, I, M, R, T, Z) instances': mock_std
        }

        cls = _Ec2Service(21, 43, {}, None)
        cls.limits = limits

        with patch(
            '%s._get_reserved_instance_count' % pb, autospec=True
        ) as m_gric:
            with patch('%s._instance_usage_vcpu' % pb, autospec=True) as m_iuv:
                m_gric.return_value = {'res': 'inst'}
                m_iuv.return_value = usage
                cls._find_usage_instances_vcpu()
        assert m_gric.mock_calls == [call(cls)]
        assert m_iuv.mock_calls == [call(cls, {'res': 'inst'})]
        assert mock_f.mock_calls == [
            call._add_current_usage(72, aws_type='AWS::EC2::Instance')
        ]
        assert mock_g.mock_calls == [
            call._add_current_usage(48, aws_type='AWS::EC2::Instance')
        ]
        assert mock_p.mock_calls == [
            call._add_current_usage(128, aws_type='AWS::EC2::Instance')
        ]
        assert mock_x.mock_calls == [
            call._add_current_usage(256, aws_type='AWS::EC2::Instance')
        ]
        assert mock_std.mock_calls == [
            call._add_current_usage(581, aws_type='AWS::EC2::Instance')
        ]

    def test_default_zero(self):
        usage = {
            'c': 16,
            'm': 32,
            'r': 16,
            't': 2,
            'p': 128,
            'x': 256,
            'a': 512,
            'k': 3
        }

        mock_f = Mock(spec_set=AwsLimit)
        mock_g = Mock(spec_set=AwsLimit)
        mock_p = Mock(spec_set=AwsLimit)
        mock_x = Mock(spec_set=AwsLimit)
        mock_std = Mock(spec_set=AwsLimit)
        limits = {
            'Running On-Demand All F instances': mock_f,
            'Running On-Demand All G instances': mock_g,
            'Running On-Demand All P instances': mock_p,
            'Running On-Demand All X instances': mock_x,
            'Running On-Demand All Standard '
            '(A, C, D, H, I, M, R, T, Z) instances': mock_std
        }

        cls = _Ec2Service(21, 43, {}, None)
        cls.limits = limits

        with patch(
            '%s._get_reserved_instance_count' % pb, autospec=True
        ) as m_gric:
            with patch('%s._instance_usage_vcpu' % pb, autospec=True) as m_iuv:
                m_gric.return_value = {'res': 'inst'}
                m_iuv.return_value = usage
                cls._find_usage_instances_vcpu()
        assert m_gric.mock_calls == [call(cls)]
        assert m_iuv.mock_calls == [call(cls, {'res': 'inst'})]
        assert mock_f.mock_calls == [
            call._add_current_usage(0, aws_type='AWS::EC2::Instance')
        ]
        assert mock_g.mock_calls == [
            call._add_current_usage(0, aws_type='AWS::EC2::Instance')
        ]
        assert mock_p.mock_calls == [
            call._add_current_usage(128, aws_type='AWS::EC2::Instance')
        ]
        assert mock_x.mock_calls == [
            call._add_current_usage(256, aws_type='AWS::EC2::Instance')
        ]
        assert mock_std.mock_calls == [
            call._add_current_usage(581, aws_type='AWS::EC2::Instance')
        ]


class TestRequiredIamPermissions(object):

    def test_simple(self):
        cls = _Ec2Service(21, 43, {}, None)
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
            "ec2:DescribeSpotPriceHistory",
            "ec2:DescribeSubnets",
            "ec2:DescribeVolumes",
            "ec2:DescribeVpcs",
            "cloudwatch:GetMetricData",
        ]


class TestFindUsageNetworkingSgs(object):

    def test_simple(self):
        mocks = fixtures.test_find_usage_networking_sgs

        mock_conn = Mock()
        mock_conn.security_groups.filter.return_value = mocks

        cls = _Ec2Service(21, 43, {}, None)
        cls._current_account_id = "1234567890"
        cls.resource_conn = mock_conn

        with patch('awslimitchecker.services.ec2.logger') as mock_logger:
            cls._find_usage_networking_sgs()
        assert mock_logger.mock_calls == [
            call.debug("Getting usage for EC2 VPC resources"),
        ]
        limit = cls.limits['VPC security groups per Region']
        # relies on AwsLimitUsage sorting by numeric usage value
        sorted_usage = sorted(limit.get_current_usage())
        assert len(sorted_usage) == 1
        assert sorted_usage[0].limit == limit
        assert sorted_usage[0].get_value() == 3
        assert sorted_usage[0].aws_type == 'AWS::EC2::SecurityGroup'

        limit = cls.limits['Rules per VPC security group']
        sorted_usage = sorted(limit.get_current_usage())
        assert len(sorted_usage) == 3
        assert sorted_usage[0].limit == limit
        assert sorted_usage[0].resource_id == 'sg-1'
        assert sorted_usage[0].get_value() == 0
        assert sorted_usage[1].limit == limit
        assert sorted_usage[1].resource_id == 'sg-2'
        # ingress: IPv4 = 15; IPv6 = 13
        # egress: IPv4 = 5; IPv6 = 7
        assert sorted_usage[1].get_value() == 15
        assert sorted_usage[2].limit == limit
        assert sorted_usage[2].resource_id == 'sg-3'
        # ingress: IPv4 = 4; IPv6 = 5
        # egress: IPv4 = 22; IPv6 = 29
        assert sorted_usage[2].get_value() == 29
        assert mock_conn.mock_calls == [
            call.security_groups.filter(
                Filters=[{'Name': 'owner-id', 'Values': ['1234567890']}]
            )
        ]


class TestFindUsageNetworkingEips(object):

    def test_simple(self):
        mocks = fixtures.test_find_usage_networking_eips

        mock_conn = Mock()
        mock_conn.classic_addresses.all.return_value = mocks['Classic']
        mock_conn.vpc_addresses.all.return_value = mocks['Vpc']
        cls = _Ec2Service(21, 43, {}, None)
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


class TestFindUsageNetworkingEniSg(object):

    def test_simple(self):
        mocks = fixtures.test_find_usage_networking_eni_sg

        mock_conn = Mock()
        mock_conn.network_interfaces.all.return_value = mocks
        cls = _Ec2Service(21, 43, {}, None)
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


class TestGetLimitsNetworking(object):

    def test_simple(self):
        cls = _Ec2Service(21, 43, {}, None)
        limits = cls._get_limits_networking()
        expected = [
            'VPC security groups per Region',
            'Rules per VPC security group',
            'VPC Elastic IP addresses (EIPs)',
            'Elastic IP addresses (EIPs)',
            'VPC security groups per elastic network interface',
        ]
        assert sorted(limits.keys()) == sorted(expected)
        assert limits[
            'VPC Elastic IP addresses (EIPs)'].ta_service_name == 'VPC'
        assert limits[
            'VPC Elastic IP addresses (EIPs)'
        ].quotas_service_code == 'ec2'
        assert limits[
            'VPC Elastic IP addresses (EIPs)'
        ].quota_name == 'EC2-VPC Elastic IPs'
        assert limits[
            'VPC Elastic IP addresses (EIPs)'
        ].quotas_unit == 'None'
        assert limits[
            'Elastic IP addresses (EIPs)'
        ].quotas_service_code == 'ec2'
        assert limits[
            'Elastic IP addresses (EIPs)'
        ].quota_name == 'EC2-Classic Elastic IPs'
        assert limits[
            'Elastic IP addresses (EIPs)'
        ].quotas_unit == 'None'
        vpcsg = limits['VPC security groups per Region']
        assert vpcsg.quota_name == 'VPC security groups per Region'
        assert vpcsg.quotas_service_code == 'vpc'
        assert vpcsg.default_limit == 2500


class TestGetLimitsSpot(object):

    def test_simple(self):
        cls = _Ec2Service(21, 43, {}, None)
        limits = cls._get_limits_spot()
        expected = [
            'All F Spot Instance Requests',
            'All G Spot Instance Requests',
            'All Inf Spot Instance Requests',
            'All P Spot Instance Requests',
            'All X Spot Instance Requests',
            'All Standard (A, C, D, H, I, M, R, T, Z) Spot Instance Requests',
            'Max active spot fleets per region',
            'Max launch specifications per spot fleet',
            'Max target capacity per spot fleet',
            'Max target capacity for all spot fleets in region'
        ]
        assert sorted(limits.keys()) == sorted(expected)


class TestFindUsageSpotInstances(object):

    def test_find_usage_spot_instances(self):
        def get_cw_usage(klass, dims, metric_name='ResourceCount', period=60):
            dim_dict = {x['Name']: x['Value'] for x in dims}
            if dim_dict['Class'] == 'F/Spot':
                return 2.0
            if dim_dict['Class'] == 'G/Spot':
                return 3.0
            if dim_dict['Class'] == 'Inf/Spot':
                return 4.0
            if dim_dict['Class'] == 'P/Spot':
                return 5.0
            if dim_dict['Class'] == 'X/Spot':
                return 6.0
            if dim_dict['Class'] == 'Standard/Spot':
                return 7.0
            return 0

        with patch(
            '%s._get_cloudwatch_usage_latest' % pb, autospec=True
        ) as mock:
            mock.side_effect = get_cw_usage
            cls = _Ec2Service(21, 43, {}, None)
            cls._find_usage_spot_instances()

        usage = cls.limits['All F Spot Instance Requests']\
            .get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 2.0
        assert usage[0].resource_id is None

        usage = cls.limits['All G Spot Instance Requests']\
            .get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 3.0
        assert usage[0].resource_id is None

        usage = cls.limits['All Inf Spot Instance Requests']\
            .get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 4.0
        assert usage[0].resource_id is None

        usage = cls.limits['All P Spot Instance Requests']\
            .get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 5.0
        assert usage[0].resource_id is None

        usage = cls.limits['All X Spot Instance Requests']\
            .get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 6.0
        assert usage[0].resource_id is None

        usage = cls.limits[
            'All Standard (A, C, D, H, I, M, R, T, Z) Spot Instance Requests'
        ].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 7.0
        assert usage[0].resource_id is None


class TestFindUsageSpotFleets(object):

    def test_simple(self):
        data = fixtures.test_find_usage_spot_fleets
        mock_conn = Mock()
        mock_client_conn = Mock()
        mock_client_conn.describe_spot_fleet_requests.return_value = data
        cls = _Ec2Service(21, 43, {}, None)
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

    def test_paginated(self):
        data = deepcopy(fixtures.test_find_usage_spot_fleets)
        data['NextToken'] = 'string'
        mock_conn = Mock()
        mock_client_conn = Mock()
        mock_client_conn.describe_spot_fleet_requests.return_value = data
        cls = _Ec2Service(21, 43, {}, None)
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

    def test_unsupported(self):
        mock_client_conn = Mock()
        err = botocore.exceptions.ClientError(
            {'Error': {'Code': 'UnsupportedOperation'}},
            'operation',
        )
        mock_client_conn.describe_spot_fleet_requests.side_effect = err
        cls = _Ec2Service(21, 43, {}, None)
        cls.conn = mock_client_conn
        cls._find_usage_spot_fleets()
        total = cls.limits['Max active spot fleets per '
                           'region'].get_current_usage()
        assert len(total) == 0

    def test_unknown_code(self):
        mock_client_conn = Mock()
        err = botocore.exceptions.ClientError(
            {'Error': {'Code': 'SomeCode'}},
            'operation',
        )
        mock_client_conn.describe_spot_fleet_requests.side_effect = err
        cls = _Ec2Service(21, 43, {}, None)
        cls.conn = mock_client_conn
        with pytest.raises(botocore.exceptions.ClientError):
            cls._find_usage_spot_fleets()

    def test_unknown_error(self):
        mock_client_conn = Mock()
        mock_client_conn.describe_spot_fleet_requests.side_effect = RuntimeError
        cls = _Ec2Service(21, 43, {}, None)
        cls.conn = mock_client_conn
        with pytest.raises(RuntimeError):
            cls._find_usage_spot_fleets()


class TestUpdateLimitsFromApi(object):

    def test_happy_path(self):
        data = fixtures.test_update_limits_from_api
        mock_conn = Mock()
        mock_client_conn = Mock()
        mock_client_conn.describe_account_attributes.return_value = data

        with patch(
                '%s._use_vcpu_limits' % pb, new_callable=PropertyMock
        ) as m_use_vcpu:
            m_use_vcpu.return_value = False
            cls = _Ec2Service(21, 43, {}, None)
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

    def test_vcpu(self):
        data = fixtures.test_update_limits_from_api_vcpu
        mock_conn = Mock()
        mock_client_conn = Mock()
        mock_client_conn.describe_account_attributes.return_value = data

        with patch(
                '%s._use_vcpu_limits' % pb, new_callable=PropertyMock
        ) as m_use_vcpu:
            m_use_vcpu.return_value = False
            cls = _Ec2Service(21, 43, {}, None)
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
        assert cls.limits['VPC Elastic IP addresses (EIPs)'].api_limit == 200
        assert cls.limits['VPC security groups per elastic '
                          'network interface'].api_limit == 5

    def test_unsupported(self):
        data = fixtures.test_update_limits_from_api_unsupported
        mock_client_conn = Mock()
        mock_client_conn.describe_account_attributes.return_value = data

        cls = _Ec2Service(21, 43, {}, None)
        cls.conn = mock_client_conn
        cls._update_limits_from_api()
        lim = cls.limits['Elastic IP addresses (EIPs)']
        usage = lim.get_current_usage()
        assert len(usage) == 0


class TestUseVcpuLimits(object):

    @patch.dict(
        os.environ,
        {},
        clear=True
    )
    def test_useast1(self):
        with patch('%s.get_limits' % pb):
            cls = _Ec2Service(21, 43, {}, None)
        mock_orig_conn = Mock()
        cls.conn = mock_orig_conn

        def se_conn(klass):
            mock_conn = Mock()
            mock_conf = Mock()
            type(mock_conf).region_name = PropertyMock(
                return_value='us-east-1'
            )
            type(mock_conn)._client_config = PropertyMock(
                return_value=mock_conf
            )
            klass.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_conn
            res = cls._use_vcpu_limits
        assert res is True
        assert cls.conn == mock_orig_conn

    @patch.dict(
        os.environ,
        {},
        clear=True
    )
    def test_beijing(self):
        with patch('%s.get_limits' % pb):
            cls = _Ec2Service(21, 43, {}, None)
        mock_orig_conn = Mock()
        cls.conn = mock_orig_conn

        def se_conn(klass):
            mock_conn = Mock()
            mock_conf = Mock()
            type(mock_conf).region_name = PropertyMock(
                return_value='cn-north-1'
            )
            type(mock_conn)._client_config = PropertyMock(
                return_value=mock_conf
            )
            klass.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_conn
            res = cls._use_vcpu_limits
        assert res is False
        assert cls.conn == mock_orig_conn

    @patch.dict(
        os.environ,
        {},
        clear=True
    )
    def test_ningxia(self):
        with patch('%s.get_limits' % pb):
            cls = _Ec2Service(21, 43, {}, None)
        mock_orig_conn = Mock()
        cls.conn = mock_orig_conn

        def se_conn(klass):
            mock_conn = Mock()
            mock_conf = Mock()
            type(mock_conf).region_name = PropertyMock(
                return_value='cn-northwest-1'
            )
            type(mock_conn)._client_config = PropertyMock(
                return_value=mock_conf
            )
            klass.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_conn
            res = cls._use_vcpu_limits
        assert res is False
        assert cls.conn == mock_orig_conn

    @patch.dict(
        os.environ,
        {},
        clear=True
    )
    def test_gov_west1(self):
        with patch('%s.get_limits' % pb):
            cls = _Ec2Service(21, 43, {}, None)
        mock_orig_conn = Mock()
        cls.conn = mock_orig_conn

        def se_conn(klass):
            mock_conn = Mock()
            mock_conf = Mock()
            type(mock_conf).region_name = PropertyMock(
                return_value='us-gov-west-1'
            )
            type(mock_conn)._client_config = PropertyMock(
                return_value=mock_conf
            )
            klass.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_conn
            res = cls._use_vcpu_limits
        assert res is False
        assert cls.conn == mock_orig_conn

    @patch.dict(
        os.environ,
        {'USE_VCPU_LIMITS': 'true'},
        clear=True
    )
    def test_useast1_env_true(self):
        cls = _Ec2Service(21, 43, {}, None)
        mock_orig_conn = Mock()
        cls.conn = mock_orig_conn

        def se_conn(klass):
            mock_conn = Mock()
            mock_conf = Mock()
            type(mock_conf).region_name = PropertyMock(
                return_value='us-east-1'
            )
            type(mock_conn)._client_config = PropertyMock(
                return_value=mock_conf
            )
            klass.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_conn
            res = cls._use_vcpu_limits
        assert res is True
        assert cls.conn == mock_orig_conn

    @patch.dict(
        os.environ,
        {'USE_VCPU_LIMITS': 'true'},
        clear=True
    )
    def test_beijing_env_true(self):
        cls = _Ec2Service(21, 43, {}, None)
        mock_orig_conn = Mock()
        cls.conn = mock_orig_conn

        def se_conn(klass):
            mock_conn = Mock()
            mock_conf = Mock()
            type(mock_conf).region_name = PropertyMock(
                return_value='cn-north-1'
            )
            type(mock_conn)._client_config = PropertyMock(
                return_value=mock_conf
            )
            klass.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_conn
            res = cls._use_vcpu_limits
        assert res is True
        assert cls.conn == mock_orig_conn

    @patch.dict(
        os.environ,
        {'USE_VCPU_LIMITS': 'true'},
        clear=True
    )
    def test_ningxia_env_true(self):
        cls = _Ec2Service(21, 43, {}, None)
        mock_orig_conn = Mock()
        cls.conn = mock_orig_conn

        def se_conn(klass):
            mock_conn = Mock()
            mock_conf = Mock()
            type(mock_conf).region_name = PropertyMock(
                return_value='cn-northwest-1'
            )
            type(mock_conn)._client_config = PropertyMock(
                return_value=mock_conf
            )
            klass.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_conn
            res = cls._use_vcpu_limits
        assert res is True
        assert cls.conn == mock_orig_conn

    @patch.dict(
        os.environ,
        {'USE_VCPU_LIMITS': 'true'},
        clear=True
    )
    def test_gov_west1_env_true(self):
        cls = _Ec2Service(21, 43, {}, None)
        mock_orig_conn = Mock()
        cls.conn = mock_orig_conn

        def se_conn(klass):
            mock_conn = Mock()
            mock_conf = Mock()
            type(mock_conf).region_name = PropertyMock(
                return_value='us-gov-west-1'
            )
            type(mock_conn)._client_config = PropertyMock(
                return_value=mock_conf
            )
            klass.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_conn
            res = cls._use_vcpu_limits
        assert res is True
        assert cls.conn == mock_orig_conn

    @patch.dict(
        os.environ,
        {'USE_VCPU_LIMITS': 'false'},
        clear=True
    )
    def test_useast1_env_false(self):
        cls = _Ec2Service(21, 43, {}, None)
        mock_orig_conn = Mock()
        cls.conn = mock_orig_conn

        def se_conn(klass):
            mock_conn = Mock()
            mock_conf = Mock()
            type(mock_conf).region_name = PropertyMock(
                return_value='us-east-1'
            )
            type(mock_conn)._client_config = PropertyMock(
                return_value=mock_conf
            )
            klass.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_conn
            res = cls._use_vcpu_limits
        assert res is False
        assert cls.conn == mock_orig_conn

    @patch.dict(
        os.environ,
        {'USE_VCPU_LIMITS': 'false'},
        clear=True
    )
    def test_beijing_env_false(self):
        cls = _Ec2Service(21, 43, {}, None)
        mock_orig_conn = Mock()
        cls.conn = mock_orig_conn

        def se_conn(klass):
            mock_conn = Mock()
            mock_conf = Mock()
            type(mock_conf).region_name = PropertyMock(
                return_value='cn-north-1'
            )
            type(mock_conn)._client_config = PropertyMock(
                return_value=mock_conf
            )
            klass.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_conn
            res = cls._use_vcpu_limits
        assert res is False
        assert cls.conn == mock_orig_conn

    @patch.dict(
        os.environ,
        {'USE_VCPU_LIMITS': 'false'},
        clear=True
    )
    def test_ningxia_env_false(self):
        cls = _Ec2Service(21, 43, {}, None)
        mock_orig_conn = Mock()
        cls.conn = mock_orig_conn

        def se_conn(klass):
            mock_conn = Mock()
            mock_conf = Mock()
            type(mock_conf).region_name = PropertyMock(
                return_value='cn-northwest-1'
            )
            type(mock_conn)._client_config = PropertyMock(
                return_value=mock_conf
            )
            klass.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_conn
            res = cls._use_vcpu_limits
        assert res is False
        assert cls.conn == mock_orig_conn

    @patch.dict(
        os.environ,
        {'USE_VCPU_LIMITS': 'false'},
        clear=True
    )
    def test_gov_west1_env_false(self):
        cls = _Ec2Service(21, 43, {}, None)
        mock_orig_conn = Mock()
        cls.conn = mock_orig_conn

        def se_conn(klass):
            mock_conn = Mock()
            mock_conf = Mock()
            type(mock_conf).region_name = PropertyMock(
                return_value='us-gov-west-1'
            )
            type(mock_conn)._client_config = PropertyMock(
                return_value=mock_conf
            )
            klass.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_conn
            res = cls._use_vcpu_limits
        assert res is False
        assert cls.conn == mock_orig_conn
