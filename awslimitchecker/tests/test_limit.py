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

from awslimitchecker.limit import AwsLimit


class TestAwsLimit(object):

    def test_init(self):
        a = AwsLimit(
            'limitname',
            'svcname',
            3
        )
        assert a.name == 'limitname'
        assert a.service_name == 'svcname'
        assert a.default_limit == 3
        assert a.limit_type is None
        assert a.limit_subtype is None

    def test_init_type(self):
        a = AwsLimit(
            'limitname',
            'svcname',
            1,
            limit_type='foo',
            limit_subtype='bar',
        )
        assert a.name == 'limitname'
        assert a.service_name == 'svcname'
        assert a.default_limit == 1
        assert a.limit_type == 'foo'
        assert a.limit_subtype == 'bar'
