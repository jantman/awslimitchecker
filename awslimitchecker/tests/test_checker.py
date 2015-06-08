"""
awslimitchecker/tests/test_checker.py

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
from awslimitchecker.services.base import _AwsService
from awslimitchecker.checker import _AwsLimitChecker
from .support import sample_limits


class Test_AwsLimitChecker(object):

    def test_init(self):
        mock_svc1 = Mock(spec_set=_AwsService)
        mock_svc2 = Mock(spec_set=_AwsService)
        mock_foo = Mock(spec_set=_AwsService)
        mock_bar = Mock(spec_set=_AwsService)
        mock_foo.return_value = mock_svc1
        mock_bar.return_value = mock_svc2
        svcs = {'foo': mock_foo, 'bar': mock_bar}
        with patch.dict('awslimitchecker.checker.services',
                        values=svcs, clear=True):
            cls = _AwsLimitChecker()
        # dict should be of _AwsService instances
        assert cls.services == {'foo': mock_svc1, 'bar': mock_svc2}
        # _AwsService instances should exist, but have no other calls
        assert mock_foo.mock_calls == [call()]
        assert mock_bar.mock_calls == [call()]
        assert mock_svc1.mock_calls == []
        assert mock_svc2.mock_calls == []

    def test_get_service_names(self):
        mock_svc1 = Mock(spec_set=_AwsService)
        mock_svc2 = Mock(spec_set=_AwsService)
        mock_bar = Mock(spec_set=_AwsService)
        mock_foo = Mock(spec_set=_AwsService)
        mock_bar.return_value = mock_svc1
        mock_foo.return_value = mock_svc2
        svcs = {'SvcFoo': mock_foo, 'SvcBar': mock_bar}
        with patch.dict('awslimitchecker.checker.services',
                        values=svcs, clear=True):
            cls = _AwsLimitChecker()
            res = cls.get_service_names()
        assert res == ['SvcBar', 'SvcFoo']

    def test_get_limits(self):
        limits = sample_limits()
        mock_svc1 = Mock(spec_set=_AwsService)
        mock_svc1.get_limits.return_value = limits['SvcBar']
        mock_svc2 = Mock(spec_set=_AwsService)
        mock_svc2.get_limits.return_value = limits['SvcFoo']
        mock_bar = Mock(spec_set=_AwsService)
        mock_foo = Mock(spec_set=_AwsService)
        mock_bar.return_value = mock_svc1
        mock_foo.return_value = mock_svc2
        svcs = {'SvcFoo': mock_foo, 'SvcBar': mock_bar}
        with patch.dict('awslimitchecker.checker.services',
                        values=svcs, clear=True):
            cls = _AwsLimitChecker()
            res = cls.get_limits()
        assert res == limits

    def test_get_limits_service(self):
        limits = sample_limits()
        mock_svc1 = Mock(spec_set=_AwsService)
        mock_svc1.get_limits.return_value = limits['SvcBar']
        mock_svc2 = Mock(spec_set=_AwsService)
        mock_svc2.get_limits.return_value = limits['SvcFoo']
        mock_bar = Mock(spec_set=_AwsService)
        mock_foo = Mock(spec_set=_AwsService)
        mock_bar.return_value = mock_svc1
        mock_foo.return_value = mock_svc2
        svcs = {'SvcFoo': mock_foo, 'SvcBar': mock_bar}
        with patch.dict('awslimitchecker.checker.services',
                        values=svcs, clear=True):
            cls = _AwsLimitChecker()
            res = cls.get_limits(service='SvcFoo')
        assert res == limits['SvcFoo']
