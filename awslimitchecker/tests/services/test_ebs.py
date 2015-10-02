"""
awslimitchecker/tests/services/test_ebs.py

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
from boto.ec2.connection import EC2Connection
from boto.ec2.volume import Volume
from boto.ec2.snapshot import Snapshot
from boto.ec2 import connect_to_region
from awslimitchecker.services.ebs import _EbsService
from awslimitchecker.limit import AwsLimit

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT


class Test_EbsService(object):

    pb = 'awslimitchecker.services.ebs._EbsService'  # patch base path
    pbm = 'awslimitchecker.services.ebs'  # patch base path for module

    def test_init(self):
        """test __init__()"""
        cls = _EbsService(21, 43)
        assert cls.service_name == 'EBS'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_connect(self):
        """test connect()"""
        mock_conn = Mock()
        mock_conn_via = Mock()
        cls = _EbsService(21, 43)
        with patch('%s.boto.connect_ec2' % self.pbm) as mock_ec2:
            with patch('%s.connect_via' % self.pb) as mock_connect_via:
                mock_ec2.return_value = mock_conn
                mock_connect_via.return_value = mock_conn_via
                cls.connect()
        assert mock_ec2.mock_calls == [call()]
        assert mock_conn.mock_calls == []
        assert mock_connect_via.mock_calls == []
        assert cls.conn == mock_conn

    def test_connect_region(self):
        """test connect()"""
        mock_conn = Mock()
        mock_conn_via = Mock()
        cls = _EbsService(21, 43, region='foo')
        with patch('%s.boto.connect_ec2' % self.pbm) as mock_ec2:
            with patch('%s.connect_via' % self.pb) as mock_connect_via:
                mock_ec2.return_value = mock_conn
                mock_connect_via.return_value = mock_conn_via
                cls.connect()
        assert mock_ec2.mock_calls == []
        assert mock_conn.mock_calls == []
        assert mock_connect_via.mock_calls == [call(connect_to_region)]
        assert cls.conn == mock_conn_via

    def test_connect_again(self):
        """make sure we re-use the connection"""
        mock_conn = Mock()
        cls = _EbsService(21, 43)
        cls.conn = mock_conn
        with patch('%s.boto.connect_ec2' % self.pbm) as mock_ec2:
            with patch('%s.connect_via' % self.pb) as mock_connect_via:
                mock_ec2.return_value = mock_conn
                cls.connect()
        assert mock_ec2.mock_calls == []
        assert mock_conn.mock_calls == []
        assert mock_connect_via.mock_calls == []

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        cls = _EbsService(21, 43)
        cls.limits = {'foo': 'bar'}
        with patch('%s._get_limits_ebs' % self.pb) as mock_ebs:
            res = cls.get_limits()
        assert res == {'foo': 'bar'}
        assert mock_ebs.mock_calls == []

    def test_get_limits(self):
        """test some things all limits should conform to"""
        cls = _EbsService(21, 43)
        limits = cls.get_limits()
        for x in limits:
            assert isinstance(limits[x], AwsLimit)
            assert x == limits[x].name
            assert limits[x].service == cls
        assert len(limits) == 6
        piops = limits['Provisioned IOPS']
        assert piops.limit_type == 'AWS::EC2::Volume'
        assert piops.limit_subtype == 'io1'
        assert piops.default_limit == 40000
        piops_tb = limits['Provisioned IOPS (SSD) storage (GiB)']
        assert piops_tb.limit_type == 'AWS::EC2::Volume'
        assert piops_tb.limit_subtype == 'io1'
        assert piops_tb.default_limit == 20480
        gp_tb = limits['General Purpose (SSD) volume storage (GiB)']
        assert gp_tb.limit_type == 'AWS::EC2::Volume'
        assert gp_tb.limit_subtype == 'gp2'
        assert gp_tb.default_limit == 20480
        mag_tb = limits['Magnetic volume storage (GiB)']
        assert mag_tb.limit_type == 'AWS::EC2::Volume'
        assert mag_tb.limit_subtype == 'standard'
        assert mag_tb.default_limit == 20480
        act_snaps = limits['Active snapshots']
        assert act_snaps.limit_type == 'AWS::EC2::VolumeSnapshot'
        act_vols = limits['Active volumes']
        assert act_vols.limit_type == 'AWS::EC2::Volume'

    def test_find_usage(self):
        with patch.multiple(
                self.pb,
                connect=DEFAULT,
                _find_usage_ebs=DEFAULT,
                _find_usage_snapshots=DEFAULT,
                autospec=True,
        ) as mocks:
            cls = _EbsService(21, 43)
            assert cls._have_usage is False
            cls.find_usage()
        assert cls._have_usage is True
        assert len(mocks) == 3
        for m in mocks:
            assert mocks[m].mock_calls == [call(cls)]

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
        cls = _EbsService(21, 43)
        cls.conn = mock_conn
        with patch('awslimitchecker.services.ebs.logger') as mock_logger:
            cls._find_usage_ebs()
        assert mock_logger.mock_calls == [
            call.debug("Getting usage for EBS volumes"),
            call.error(
                "ERROR - unknown volume type '%s' for volume "
                "%s; not counting", 'othertype', 'vol-7')
        ]
        assert len(cls.limits['Provisioned IOPS'].get_current_usage()) == 1
        assert cls.limits['Provisioned IOPS'
                          ''].get_current_usage()[0].get_value() == 1000
        assert len(cls.limits['Provisioned IOPS (SSD) storage '
                              '(GiB)'].get_current_usage()) == 1
        assert cls.limits['Provisioned IOPS (SSD) storage '
                          '(GiB)'].get_current_usage()[0].get_value() == 500
        assert len(cls.limits['General Purpose (SSD) volume storage '
                              '(GiB)'].get_current_usage()) == 1
        assert cls.limits['General Purpose (SSD) volume storage '
                          '(GiB)'].get_current_usage()[0].get_value() == 45
        assert len(cls.limits['Magnetic volume storage '
                              '(GiB)'].get_current_usage()) == 1
        assert cls.limits['Magnetic volume storage '
                          '(GiB)'].get_current_usage()[0].get_value() == 508
        assert len(cls.limits['Active volumes'].get_current_usage()) == 1
        assert cls.limits['Active volumes'
                          ''].get_current_usage()[0].get_value() == 7

    def test_find_usage_snapshots(self):
        mock_snap1 = Mock(spec_set=Snapshot)
        type(mock_snap1).id = 'snap-1'

        mock_snap2 = Mock(spec_set=Snapshot)
        type(mock_snap2).id = 'snap-2'

        mock_snap3 = Mock(spec_set=Snapshot)
        type(mock_snap3).id = 'snap-3'

        mock_conn = Mock(spec_set=EC2Connection)
        mock_conn.get_all_snapshots.return_value = [
            mock_snap1,
            mock_snap2,
            mock_snap3,
        ]
        cls = _EbsService(21, 43)
        cls.conn = mock_conn
        with patch('awslimitchecker.services.ebs.logger') as mock_logger:
            cls._find_usage_snapshots()
        assert mock_logger.mock_calls == [
            call.debug("Getting usage for EBS snapshots"),
        ]
        assert len(cls.limits['Active snapshots'].get_current_usage()) == 1
        assert cls.limits['Active snapshots'
                          ''].get_current_usage()[0].get_value() == 3
        assert mock_conn.mock_calls == [
            call.get_all_snapshots(owner='self')
        ]

    def test_required_iam_permissions(self):
        cls = _EbsService(21, 43)
        assert cls.required_iam_permissions() == [
            "ec2:DescribeVolumes",
            "ec2:DescribeSnapshots"
        ]
