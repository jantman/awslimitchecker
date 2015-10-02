"""
awslimitchecker/tests/services/test_elb.py

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

import sys
from boto.ec2.elb import ELBConnection
from boto.ec2.elb.loadbalancer import LoadBalancer
from boto.ec2.elb import connect_to_region
from awslimitchecker.services.elb import _ElbService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock


class Test_ElbService(object):

    pb = 'awslimitchecker.services.elb._ElbService'  # patch base path
    pbm = 'awslimitchecker.services.elb'  # patch base path - module

    def test_init(self):
        """test __init__()"""
        cls = _ElbService(21, 43)
        assert cls.service_name == 'ELB'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_connect(self):
        """test connect()"""
        mock_conn = Mock()
        mock_conn_via = Mock()
        cls = _ElbService(21, 43)
        with patch('%s.boto.connect_elb' % self.pbm) as mock_elb:
            with patch('%s.connect_via' % self.pb) as mock_connect_via:
                mock_elb.return_value = mock_conn
                mock_connect_via.return_value = mock_conn_via
                cls.connect()
        assert mock_elb.mock_calls == [call()]
        assert mock_conn.mock_calls == []
        assert mock_connect_via.mock_calls == []
        assert cls.conn == mock_conn

    def test_connect_region(self):
        """test connect()"""
        mock_conn = Mock()
        mock_conn_via = Mock()
        cls = _ElbService(21, 43, region='myregion')
        with patch('%s.boto.connect_elb' % self.pbm) as mock_elb:
            with patch('%s.connect_via' % self.pb) as mock_connect_via:
                mock_elb.return_value = mock_conn
                mock_connect_via.return_value = mock_conn_via
                cls.connect()
        assert mock_elb.mock_calls == []
        assert mock_conn.mock_calls == []
        assert mock_connect_via.mock_calls == [
            call(connect_to_region)
        ]
        assert cls.conn == mock_conn_via

    def test_connect_again(self):
        """make sure we re-use the connection"""
        mock_conn = Mock()
        cls = _ElbService(21, 43)
        cls.conn = mock_conn
        with patch('awslimitchecker.services.elb.boto.connect_elb') as mock_elb:
            with patch('%s.connect_via' % self.pb) as mock_connect_via:
                mock_elb.return_value = mock_conn
                cls.connect()
        assert mock_elb.mock_calls == []
        assert mock_conn.mock_calls == []
        assert mock_connect_via.mock_calls == []

    def test_get_limits(self):
        cls = _ElbService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Active load balancers',
            'Listeners per load balancer',
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _ElbService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        mock_elb1 = Mock(spec_set=LoadBalancer)
        type(mock_elb1).name = 'elb-1'
        type(mock_elb1).listeners = [1]

        mock_elb2 = Mock(spec_set=LoadBalancer)
        type(mock_elb2).name = 'elb-2'
        type(mock_elb2).listeners = [1, 2]

        mock_elb3 = Mock(spec_set=LoadBalancer)
        type(mock_elb3).name = 'elb-3'
        type(mock_elb3).listeners = [1, 2, 3]

        mock_elb4 = Mock(spec_set=LoadBalancer)
        type(mock_elb4).name = 'elb-4'
        type(mock_elb4).listeners = [1, 2, 3, 4, 5, 6]

        mock_conn = Mock(spec_set=ELBConnection)
        mock_conn.get_all_load_balancers.return_value = [
            mock_elb1,
            mock_elb2,
            mock_elb3,
            mock_elb4
        ]
        with patch('%s.connect' % self.pb) as mock_connect:
            cls = _ElbService(21, 43)
            cls.conn = mock_conn
            assert cls._have_usage is False
            cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        assert mock_conn.get_all_load_balancers.mock_calls == [call()]
        assert len(cls.limits['Active load balancers'].get_current_usage()) == 1
        assert cls.limits['Active load balancers'
                          ''].get_current_usage()[0].get_value() == 4
        entries = sorted(cls.limits['Listeners per load balancer'
                                    ''].get_current_usage())
        assert len(entries) == 4
        assert entries[0].resource_id == 'elb-1'
        assert entries[0].get_value() == 1
        assert entries[1].resource_id == 'elb-2'
        assert entries[1].get_value() == 2
        assert entries[2].resource_id == 'elb-3'
        assert entries[2].get_value() == 3
        assert entries[3].resource_id == 'elb-4'
        assert entries[3].get_value() == 6

    def test_required_iam_permissions(self):
        cls = _ElbService(21, 43)
        assert cls.required_iam_permissions() == [
            "elasticloadbalancing:DescribeLoadBalancers"
        ]
