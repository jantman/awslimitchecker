"""
awslimitchecker/tests/test_limit.py

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

from mock import Mock
from awslimitchecker.limit import AwsLimit, AwsLimitUsage


class TestAwsLimit(object):

    def test_init(self):
        limit = AwsLimit(
            'limitname',
            'svcname',
            3
        )
        assert limit.name == 'limitname'
        assert limit.service_name == 'svcname'
        assert limit.default_limit == 3
        assert limit.limit_type is None
        assert limit.limit_subtype is None
        assert limit.limit_override is None
        assert limit.override_ta is True

    def test_init_type(self):
        limit = AwsLimit(
            'limitname',
            'svcname',
            1,
            limit_type='foo',
            limit_subtype='bar',
        )
        assert limit.name == 'limitname'
        assert limit.service_name == 'svcname'
        assert limit.default_limit == 1
        assert limit.limit_type == 'foo'
        assert limit.limit_subtype == 'bar'
        assert limit.limit_override is None
        assert limit.override_ta is True

    def test_set_limit_override(self):
        limit = AwsLimit(
            'limitname',
            'svcname',
            3
        )
        limit.set_limit_override(10)
        assert limit.limit_override == 10
        assert limit.default_limit == 3
        assert limit.override_ta is True

    def test_set_limit_override_ta_False(self):
        limit = AwsLimit(
            'limitname',
            'svcname',
            3
        )
        limit.set_limit_override(1, override_ta=False)
        assert limit.limit_override == 1
        assert limit.default_limit == 3
        assert limit.override_ta is False

    def test_add_current_usage(self):
        limit = AwsLimit(
            'limitname',
            'svcname',
            3
        )
        assert limit._current_usage == []
        limit._add_current_usage(2)
        assert len(limit.get_current_usage()) == 1
        assert limit._current_usage[0].get_value() == 2
        limit._add_current_usage(4)
        assert len(limit.get_current_usage()) == 2
        assert limit._current_usage[1].get_value() == 4

    def test_get_current_usage(self):
        limit = AwsLimit(
            'limitname',
            'svcname',
            3
        )
        limit._current_usage = 2
        assert limit.get_current_usage() == 2

    def test_get_current_usage_str(self):
        limit = AwsLimit(
            'limitname',
            'svcname',
            3
        )
        limit._add_current_usage(4)
        assert limit.get_current_usage_str() == '4'

    def test_get_current_usage_str_id(self):
        limit = AwsLimit(
            'limitname',
            'svcname',
            3
        )
        limit._add_current_usage(4, id='foobar')
        assert limit.get_current_usage_str() == 'foobar=4'

    def test_get_current_usage_str_multi(self):
        limit = AwsLimit(
            'limitname',
            'svcname',
            3
        )
        limit._add_current_usage(4)
        limit._add_current_usage(3)
        limit._add_current_usage(2)
        assert limit.get_current_usage_str() == 'max: 4 (2, 3, 4)'

    def test_get_current_usage_str_multi_id(self):
        limit = AwsLimit(
            'limitname',
            'svcname',
            3
        )
        limit._add_current_usage(4, id='foo4bar')
        limit._add_current_usage(3, id='foo3bar')
        limit._add_current_usage(2, id='foo2bar')
        assert limit.get_current_usage_str() == 'max: foo4bar=4 (foo2bar=2, ' \
            'foo3bar=3, foo4bar=4)'


class TestAwsLimitUsage(object):

    def test_init(self):
        mock_limit = Mock(spec_set=AwsLimit)
        u = AwsLimitUsage(
            mock_limit,
            1.23,
        )
        assert u.limit == mock_limit
        assert u.value == 1.23
        assert u.id is None
        assert u.aws_type is None

        u2 = AwsLimitUsage(
            mock_limit,
            3,
            id='foobar',
            aws_type='mytype',
        )
        assert u2.limit == mock_limit
        assert u2.value == 3
        assert u2.id == 'foobar'
        assert u2.aws_type == 'mytype'

    def test_get_value(self):
        mock_limit = Mock(spec_set=AwsLimit)
        u = AwsLimitUsage(
            mock_limit,
            3.456
        )
        assert u.get_value() == 3.456

    def test_repr(self):
        mock_limit = Mock(spec_set=AwsLimit)
        u = AwsLimitUsage(
            mock_limit,
            3.456
        )
        assert str(u) == '3.456'

        u2 = AwsLimitUsage(
            mock_limit,
            3.456,
            id='foobar'
        )
        assert str(u2) == 'foobar=3.456'

    def test_comparable(self):
        mock_limit = Mock(spec_set=AwsLimit)
        u1 = AwsLimitUsage(
            mock_limit,
            3.456
        )
        u2 = AwsLimitUsage(
            mock_limit,
            3
        )
        u3 = AwsLimitUsage(
            mock_limit,
            4
        )
        u1b = AwsLimitUsage(
            mock_limit,
            3.456
        )
        assert u1 == u1b
        assert u1 != u2
        assert u1 < u3
        assert u1 > u2
