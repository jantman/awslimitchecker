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
from awslimitchecker.services.ec2 import Ec2Service
from awslimitchecker.limit import _AwsLimit


class TestEc2Service(object):

    def test_init(self):
        """test __init__()"""
        cls = Ec2Service()
        assert cls.service_name == 'EC2'
        assert cls.conn is None

    def test_connect(self):
        """test connect()"""
        mock_conn = Mock()
        cls = Ec2Service()
        with patch('awslimitchecker.services.ec2.boto.connect_ec2') as mock_ec2:
            mock_ec2.return_value = mock_conn
            cls.connect()
        assert mock_ec2.mock_calls == [call()]
        assert mock_conn.mock_calls == []

    def test_connect_again(self):
        """make sure we re-use the connection"""
        mock_conn = Mock()
        cls = Ec2Service()
        cls.conn = mock_conn
        with patch('awslimitchecker.services.ec2.boto.connect_ec2') as mock_ec2:
            mock_ec2.return_value = mock_conn
            cls.connect()
        assert mock_ec2.mock_calls == []
        assert mock_conn.mock_calls == []

    def test_instance_types(self):
        cls = Ec2Service()
        types = cls._instance_types()
        assert len(types) == 32
        assert 't2.micro' in types
        assert 'r3.8xlarge' in types
        assert 'c3.large' in types
        assert 'i2.4xlarge' in types
        assert 'd2.2xlarge' in types
        assert 'g2.8xlarge' in types

    def test_get_limits(self):
        cls = Ec2Service()
        init_limits = cls.limits
        limits = cls.get_limits()
        assert limits == init_limits
        assert len(limits) == 32
        for x in limits:
            assert isinstance(limits[x], _AwsLimit)
            assert limits[x].service_name == 'EC2'
        # check a random subset of limits
        t2_micro = limits['Running On-Demand t2.micro Instances']
        assert t2_micro.default_limit == 20
        assert t2_micro.limit_type == 'On-Demand Instances'
        assert t2_micro.limit_subtype == 't2.micro'
        c4_8xlarge = limits['Running On-Demand c4.8xlarge Instances']
        assert c4_8xlarge.default_limit == 5
        assert c4_8xlarge.limit_type == 'On-Demand Instances'
        assert c4_8xlarge.limit_subtype == 'c4.8xlarge'
        i2_8xlarge = limits['Running On-Demand i2.8xlarge Instances']
        assert i2_8xlarge.default_limit == 2
        assert i2_8xlarge.limit_type == 'On-Demand Instances'
        assert i2_8xlarge.limit_subtype == 'i2.8xlarge'
