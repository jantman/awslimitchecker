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
from contextlib import nested
from awslimitchecker.services.base import _AwsService
from awslimitchecker.checker import AwsLimitChecker
from awslimitchecker.version import _get_version, _get_project_url
from .support import sample_limits


class TestAwsLimitChecker(object):

    def setup(self, svcs=None):
        if svcs is None:
            self.mock_svc1 = Mock(spec_set=_AwsService)
            self.mock_svc2 = Mock(spec_set=_AwsService)
            self.mock_foo = Mock(spec_set=_AwsService)
            self.mock_bar = Mock(spec_set=_AwsService)
            self.mock_foo.return_value = self.mock_svc1
            self.mock_bar.return_value = self.mock_svc2
            self.svcs = {'SvcFoo': self.mock_foo, 'SvcBar': self.mock_bar}
            svcs = self.svcs
        with nested(
                patch.dict('awslimitchecker.checker._services',
                           values=svcs, clear=True),
                patch('awslimitchecker.checker.logger',
                      autospec=True),
                patch('awslimitchecker.checker._get_version',
                      spec_set=_get_version),
                patch('awslimitchecker.checker._get_project_url',
                      spec_set=_get_project_url)
        ) as (
            mock_services,
            self.mock_logger,
            self.mock_version,
            self.mock_project_url,
        ):
            self.mock_version.return_value = 'MVER'
            self.mock_project_url.return_value = 'PURL'
            self.cls = AwsLimitChecker()

    def test_init(self):
        # dict should be of _AwsService instances
        assert self.cls.services == {
            'SvcFoo': self.mock_svc1,
            'SvcBar': self.mock_svc2
        }
        # _AwsService instances should exist, but have no other calls
        assert self.mock_foo.mock_calls == [call()]
        assert self.mock_bar.mock_calls == [call()]
        assert self.mock_svc1.mock_calls == []
        assert self.mock_svc2.mock_calls == []

    def test_init_logger(self):
        """ensure we log a license message"""
        assert self.mock_logger.mock_calls == [
            call.warning("awslimitchecker MVER is AGPL-licensed free software; "
                         "all users have a right to the full source code of "
                         "this version. See <PURL>")
        ]

    def test_get_version(self):
        with patch('awslimitchecker.checker._get_version',
                   spec_set=_get_version) as mock_version:
            mock_version.return_value = 'a.b.c'
            res = self.cls.get_version()
        assert res == 'a.b.c'
        assert mock_version.mock_calls == [call()]

    def test_get_project_url(self):
        with patch('awslimitchecker.checker._get_project_url',
                   spec_set=_get_project_url) as mock_url:
            mock_url.return_value = 'myurl'
            res = self.cls.get_project_url()
        assert res == 'myurl'
        assert mock_url.mock_calls == [call()]

    def test_get_service_names(self):
        res = self.cls.get_service_names()
        assert res == ['SvcBar', 'SvcFoo']

    def test_get_limits(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.mock_svc2.get_limits.return_value = limits['SvcBar']
        res = self.cls.get_limits()
        assert res == limits

    def test_get_limits_service(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.mock_svc2.get_limits.return_value = limits['SvcBar']
        res = self.cls.get_limits(service='SvcFoo')
        assert sorted(res) == sorted(limits['SvcFoo'])

    def test_find_usage(self):
        self.cls.find_usage()
        assert self.mock_svc1.mock_calls == [
            call.find_usage()
        ]
        assert self.mock_svc2.mock_calls == [
            call.find_usage()
        ]

    def test_find_usage_service(self):
        self.cls.find_usage(service='SvcFoo')
        assert self.mock_svc1.mock_calls == [
            call.find_usage()
        ]
        assert self.mock_svc2.mock_calls == []

    def test_set_limit_overrides(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.mock_svc2.get_limits.return_value = limits['SvcBar']
        overrides = {
            'SvcBar': {
                'barlimit1': 100,
            },
            'SvcFoo': {
                'foo limit3': 99,
            },
        }
        self.cls.set_limit_overrides(overrides)
        assert self.mock_svc1.mock_calls == [
            call.set_limit_override('foo limit3', 99, override_ta=True)
        ]
        assert self.mock_svc2.mock_calls == [
            call.set_limit_override('barlimit1', 100, override_ta=True)
        ]

    def test_set_limit_overrides_ta(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.mock_svc2.get_limits.return_value = limits['SvcBar']
        overrides = {
            'SvcBar': {
                'bar limit2': 100,
            },
            'SvcFoo': {
                'foo limit3': 3,
            },
        }
        self.cls.set_limit_overrides(overrides, override_ta=False)
        assert self.mock_svc1.mock_calls == [
            call.set_limit_override('foo limit3', 3, override_ta=False)
        ]
        assert self.mock_svc2.mock_calls == [
            call.set_limit_override('bar limit2', 100, override_ta=False)
        ]

    def test_get_required_iam_policy(self):
        expected = {
            'Version': '2012-10-17',
            'Statement': [{
                'Effect': 'Allow',
                'Resource': '*',
                'Action': [
                    'ec2:bar',
                    'ec2:foo',
                    'foo:perm1',
                    'foo:perm2',
                ],
            }],
        }
        self.mock_svc1.required_iam_permissions.return_value = [
            'ec2:foo',
            'ec2:bar',
        ]
        self.mock_svc2.required_iam_permissions.return_value = [
            'foo:perm1',
            'foo:perm2',
        ]
        res = self.cls.get_required_iam_policy()
        assert res == expected
        assert self.mock_svc1.mock_calls == [call.required_iam_permissions()]
        assert self.mock_svc2.mock_calls == [call.required_iam_permissions()]
