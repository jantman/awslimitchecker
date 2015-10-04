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
bugs please submit them at <https://github.com/jantman/awslimitchecker> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

import sys

from awslimitchecker.services.base import _AwsService
from awslimitchecker.checker import AwsLimitChecker
from awslimitchecker.version import _get_version_info
from awslimitchecker.limit import AwsLimit
from awslimitchecker.trustedadvisor import TrustedAdvisor
from .support import sample_limits


# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT


class TestAwsLimitChecker(object):

    def setup(self):
        self.mock_ver_info = Mock(
            release='1.2.3',
            url='http://myurl',
            commit='abcd',
            tag='mytag',
            version_str='1.2.3@mytag'
        )

        self.mock_svc1 = Mock(spec_set=_AwsService)
        self.mock_svc2 = Mock(spec_set=_AwsService)
        self.mock_foo = Mock(spec_set=_AwsService)
        self.mock_bar = Mock(spec_set=_AwsService)
        self.mock_ta = Mock(spec_set=TrustedAdvisor)
        self.mock_foo.return_value = self.mock_svc1
        self.mock_bar.return_value = self.mock_svc2
        self.svcs = {'SvcFoo': self.mock_foo, 'SvcBar': self.mock_bar}
        with patch.dict('awslimitchecker.checker._services',
                        values=self.svcs, clear=True):
            with patch.multiple(
                    'awslimitchecker.checker',
                    logger=DEFAULT,
                    _get_version_info=DEFAULT,
                    TrustedAdvisor=DEFAULT,
                    autospec=True,
            ) as mocks:
                self.mock_logger = mocks['logger']
                self.mock_version = mocks['_get_version_info']
                self.mock_ta_constr = mocks['TrustedAdvisor']
                mocks['TrustedAdvisor'].return_value = self.mock_ta
                self.mock_version.return_value = self.mock_ver_info
                self.cls = AwsLimitChecker()

    def test_init(self):
        # dict should be of _AwsService instances
        assert self.cls.services == {
            'SvcFoo': self.mock_svc1,
            'SvcBar': self.mock_svc2
        }
        # _AwsService instances should exist, but have no other calls
        assert self.mock_foo.mock_calls == [
            call(80, 99, None, None, None, None)
        ]
        assert self.mock_bar.mock_calls == [
            call(80, 99, None, None, None, None)
        ]
        assert self.mock_ta_constr.mock_calls == [
            call(account_id=None, account_role=None, region=None,
                 external_id=None)
        ]
        assert self.mock_svc1.mock_calls == []
        assert self.mock_svc2.mock_calls == []
        assert self.cls.ta == self.mock_ta
        assert self.mock_version.mock_calls == [call()]
        assert self.cls.vinfo == self.mock_ver_info
        assert self.mock_logger.mock_calls == []

    def test_init_AGPL_message(self, capsys):
        # get rid of the class
        self.cls = None
        # clear out/err
        out, err = capsys.readouterr()
        # run setup again
        self.setup()
        # check out/err
        out, err = capsys.readouterr()
        assert out == ''
        assert (err) == (
            "awslimitchecker 1.2.3@mytag is AGPL-licensed free software; "
            "all users have a right to the full source code of "
            "this version. See <http://myurl>\n")

    def test_init_thresholds(self):
        mock_svc1 = Mock(spec_set=_AwsService)
        mock_svc2 = Mock(spec_set=_AwsService)
        mock_foo = Mock(spec_set=_AwsService)
        mock_bar = Mock(spec_set=_AwsService)
        mock_ta = Mock(spec_set=TrustedAdvisor)
        mock_foo.return_value = mock_svc1
        mock_bar.return_value = mock_svc2
        svcs = {'SvcFoo': mock_foo, 'SvcBar': mock_bar}
        with patch.dict('awslimitchecker.checker._services',
                        values=svcs, clear=True):
            with patch.multiple(
                    'awslimitchecker.checker',
                    logger=DEFAULT,
                    _get_version_info=DEFAULT,
                    TrustedAdvisor=DEFAULT,
                    autospec=True,
            ) as mocks:
                mock_version = mocks['_get_version_info']
                mock_version.return_value = self.mock_ver_info
                mock_ta_constr = mocks['TrustedAdvisor']
                mocks['TrustedAdvisor'].return_value = mock_ta
                cls = AwsLimitChecker(
                    warning_threshold=5,
                    critical_threshold=22,
                )
        # dict should be of _AwsService instances
        assert cls.services == {
            'SvcFoo': mock_svc1,
            'SvcBar': mock_svc2
        }
        # _AwsService instances should exist, but have no other calls
        assert mock_foo.mock_calls == [call(5, 22, None, None, None, None)]
        assert mock_bar.mock_calls == [call(5, 22, None, None, None, None)]
        assert mock_ta_constr.mock_calls == [
            call(account_id=None, account_role=None, region=None,
                 external_id=None)
        ]
        assert mock_svc1.mock_calls == []
        assert mock_svc2.mock_calls == []
        assert self.mock_version.mock_calls == [call()]
        assert self.cls.vinfo == self.mock_ver_info

    def test_init_region(self):
        mock_svc1 = Mock(spec_set=_AwsService)
        mock_svc2 = Mock(spec_set=_AwsService)
        mock_foo = Mock(spec_set=_AwsService)
        mock_bar = Mock(spec_set=_AwsService)
        mock_ta = Mock(spec_set=TrustedAdvisor)
        mock_foo.return_value = mock_svc1
        mock_bar.return_value = mock_svc2
        svcs = {'SvcFoo': mock_foo, 'SvcBar': mock_bar}
        with patch.dict('awslimitchecker.checker._services',
                        values=svcs, clear=True):
            with patch.multiple(
                    'awslimitchecker.checker',
                    logger=DEFAULT,
                    _get_version_info=DEFAULT,
                    TrustedAdvisor=DEFAULT,
                    autospec=True,
            ) as mocks:
                mock_version = mocks['_get_version_info']
                mock_version.return_value = self.mock_ver_info
                mock_ta_constr = mocks['TrustedAdvisor']
                mocks['TrustedAdvisor'].return_value = mock_ta
                cls = AwsLimitChecker(region='myregion')
        # dict should be of _AwsService instances
        assert cls.services == {
            'SvcFoo': mock_svc1,
            'SvcBar': mock_svc2
        }
        # _AwsService instances should exist, but have no other calls
        assert mock_foo.mock_calls == [
            call(80, 99, None, None, 'myregion', None)
        ]
        assert mock_bar.mock_calls == [
            call(80, 99, None, None, 'myregion', None)
        ]
        assert mock_ta_constr.mock_calls == [
            call(account_id=None, account_role=None, region='myregion',
                 external_id=None)
        ]
        assert mock_svc1.mock_calls == []
        assert mock_svc2.mock_calls == []
        assert self.mock_version.mock_calls == [call()]
        assert self.cls.vinfo == self.mock_ver_info

    def test_init_sts(self):
        mock_svc1 = Mock(spec_set=_AwsService)
        mock_svc2 = Mock(spec_set=_AwsService)
        mock_foo = Mock(spec_set=_AwsService)
        mock_bar = Mock(spec_set=_AwsService)
        mock_ta = Mock(spec_set=TrustedAdvisor)
        mock_foo.return_value = mock_svc1
        mock_bar.return_value = mock_svc2
        svcs = {'SvcFoo': mock_foo, 'SvcBar': mock_bar}
        with patch.dict('awslimitchecker.checker._services',
                        values=svcs, clear=True):
            with patch.multiple(
                    'awslimitchecker.checker',
                    logger=DEFAULT,
                    _get_version_info=DEFAULT,
                    TrustedAdvisor=DEFAULT,
                    autospec=True,
            ) as mocks:
                mock_version = mocks['_get_version_info']
                mock_version.return_value = self.mock_ver_info
                mock_ta_constr = mocks['TrustedAdvisor']
                mocks['TrustedAdvisor'].return_value = mock_ta
                cls = AwsLimitChecker(
                    account_id='123456789012',
                    account_role='myrole',
                    region='myregion'
                )
        # dict should be of _AwsService instances
        assert cls.services == {
            'SvcFoo': mock_svc1,
            'SvcBar': mock_svc2
        }
        # _AwsService instances should exist, but have no other calls
        assert mock_foo.mock_calls == [
            call(80, 99, '123456789012', 'myrole', 'myregion', None)
        ]
        assert mock_bar.mock_calls == [
            call(80, 99, '123456789012', 'myrole', 'myregion', None)
        ]
        assert mock_ta_constr.mock_calls == [
            call(
                account_id='123456789012',
                account_role='myrole',
                region='myregion',
                external_id=None
            )
        ]
        assert mock_svc1.mock_calls == []
        assert mock_svc2.mock_calls == []
        assert self.mock_version.mock_calls == [call()]
        assert self.cls.vinfo == self.mock_ver_info

    def test_init_sts_external_id(self):
        mock_svc1 = Mock(spec_set=_AwsService)
        mock_svc2 = Mock(spec_set=_AwsService)
        mock_foo = Mock(spec_set=_AwsService)
        mock_bar = Mock(spec_set=_AwsService)
        mock_ta = Mock(spec_set=TrustedAdvisor)
        mock_foo.return_value = mock_svc1
        mock_bar.return_value = mock_svc2
        svcs = {'SvcFoo': mock_foo, 'SvcBar': mock_bar}
        with patch.dict('awslimitchecker.checker._services',
                        values=svcs, clear=True):
            with patch.multiple(
                    'awslimitchecker.checker',
                    logger=DEFAULT,
                    _get_version_info=DEFAULT,
                    TrustedAdvisor=DEFAULT,
                    autospec=True,
            ) as mocks:
                mock_version = mocks['_get_version_info']
                mock_version.return_value = self.mock_ver_info
                mock_ta_constr = mocks['TrustedAdvisor']
                mocks['TrustedAdvisor'].return_value = mock_ta
                cls = AwsLimitChecker(
                    account_id='123456789012',
                    account_role='myrole',
                    region='myregion',
                    external_id='myextid'
                )
        # dict should be of _AwsService instances
        assert cls.services == {
            'SvcFoo': mock_svc1,
            'SvcBar': mock_svc2
        }
        # _AwsService instances should exist, but have no other calls
        assert mock_foo.mock_calls == [
            call(80, 99, '123456789012', 'myrole', 'myregion', 'myextid')
        ]
        assert mock_bar.mock_calls == [
            call(80, 99, '123456789012', 'myrole', 'myregion', 'myextid')
        ]
        assert mock_ta_constr.mock_calls == [
            call(
                account_id='123456789012',
                account_role='myrole',
                region='myregion',
                external_id='myextid'
            )
        ]
        assert mock_svc1.mock_calls == []
        assert mock_svc2.mock_calls == []
        assert self.mock_version.mock_calls == [call()]
        assert self.cls.vinfo == self.mock_ver_info

    def test_get_version(self):
        with patch('awslimitchecker.checker._get_version_info',
                   spec_set=_get_version_info) as mock_version:
            self.cls.vinfo = self.mock_ver_info
            res = self.cls.get_version()
        assert res == '1.2.3@mytag'
        assert mock_version.mock_calls == []

    def test_get_project_url(self):
        with patch('awslimitchecker.checker._get_version_info',
                   spec_set=_get_version_info) as mock_version:
            self.cls.vinfo = self.mock_ver_info
            res = self.cls.get_project_url()
        assert res == 'http://myurl'
        assert mock_version.mock_calls == []

    def test_get_service_names(self):
        res = self.cls.get_service_names()
        assert res == ['SvcBar', 'SvcFoo']

    def test_get_limits(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.mock_svc2.get_limits.return_value = limits['SvcBar']
        res = self.cls.get_limits()
        assert res == limits
        assert self.mock_ta.mock_calls == [
            call.update_limits({
                'SvcFoo': self.mock_svc1,
                'SvcBar': self.mock_svc2,
            })
        ]

    def test_get_limits_no_ta(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.mock_svc2.get_limits.return_value = limits['SvcBar']
        res = self.cls.get_limits(use_ta=False)
        assert res == limits
        assert self.mock_ta.mock_calls == []

    def test_get_limits_service(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.mock_svc2.get_limits.return_value = limits['SvcBar']
        res = self.cls.get_limits(service='SvcFoo')
        assert res == {'SvcFoo': limits['SvcFoo']}
        assert self.mock_ta.mock_calls == [
            call.update_limits({
                'SvcFoo': self.mock_svc1,
            })
        ]

    def test_find_usage(self):
        self.cls.find_usage()
        assert self.mock_svc1.mock_calls == [
            call.find_usage()
        ]
        assert self.mock_svc2.mock_calls == [
            call.find_usage()
        ]
        assert self.mock_ta.mock_calls == [
            call.update_limits({
                'SvcFoo': self.mock_svc1,
                'SvcBar': self.mock_svc2,
            })
        ]

    def test_find_usage_no_ta(self):
        self.cls.find_usage(use_ta=False)
        assert self.mock_svc1.mock_calls == [
            call.find_usage()
        ]
        assert self.mock_svc2.mock_calls == [
            call.find_usage()
        ]
        assert self.mock_ta.mock_calls == []

    def test_find_usage_service(self):
        self.cls.find_usage(service='SvcFoo')
        assert self.mock_svc1.mock_calls == [
            call.find_usage()
        ]
        assert self.mock_svc2.mock_calls == []
        assert self.mock_ta.mock_calls == [
            call.update_limits({'SvcFoo': self.mock_svc1})
        ]

    def test_set_threshold_overrides(self):
        limits = sample_limits()
        limits['SvcFoo']['zz3'] = AwsLimit(
            'zz3',
            self.mock_svc1,
            1,
            2,
            3,
        )
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.mock_svc2.get_limits.return_value = limits['SvcBar']
        overrides = {
            'SvcBar': {
                'barlimit1': {
                    'warning': {
                        'percent': 10,
                        'count': 12
                    },
                    'critical': {
                        'percent': 14,
                        'count': 16
                    }
                },
                'bar limit2': {
                    'critical': {
                        'count': 15,
                    }
                },
                'zz3': {
                    'warning': {
                        'count': 41
                    },
                    'critical': {
                        'percent': 52
                    }
                }
            },
            'SvcFoo': {
                'foo limit3': {
                    'warning': {
                        'percent': 91
                    },
                }
            },
        }
        self.cls.set_threshold_overrides(overrides)
        assert self.mock_svc1.mock_calls == [
            call.set_threshold_override(
                'foo limit3',
                warn_percent=91,
            )
        ]
        assert self.mock_svc2.mock_calls == [
            call.set_threshold_override(
                'bar limit2',
                crit_count=15
            ),
            call.set_threshold_override(
                'barlimit1',
                warn_percent=10,
                warn_count=12,
                crit_percent=14,
                crit_count=16
            ),
            call.set_threshold_override(
                'zz3',
                warn_count=41,
                crit_percent=52
            ),
        ]

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

    def test_set_limit_override(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.cls.set_limit_override('SvcFoo', 'foo limit3', 99)
        assert self.mock_svc1.mock_calls == [
            call.set_limit_override('foo limit3', 99, override_ta=True)
        ]

    def test_set_limit_override_ta(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.cls.set_limit_override(
            'SvcFoo',
            'foo limit3',
            99,
            override_ta=False
        )
        assert self.mock_svc1.mock_calls == [
            call.set_limit_override(
                'foo limit3',
                99,
                override_ta=False
            )
        ]

    def test_set_threshold_override(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.cls.set_threshold_override(
            'SvcFoo',
            'foo limit3',
            warn_percent=10,
            warn_count=12,
            crit_percent=14,
            crit_count=16
        )
        assert self.mock_svc1.mock_calls == [
            call.set_threshold_override(
                'foo limit3',
                warn_percent=10,
                warn_count=12,
                crit_percent=14,
                crit_count=16
            )
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
                    'support:*',
                    'trustedadvisor:Describe*'
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

    def test_check_thresholds(self):
        self.mock_svc1.check_thresholds.return_value = {
            'foo': 'bar',
            'baz': 'blam',
        }
        self.mock_svc2.check_thresholds.return_value = {}
        res = self.cls.check_thresholds()
        assert res == {
            'SvcFoo': {
                'foo': 'bar',
                'baz': 'blam',
            }
        }
        assert self.mock_ta.mock_calls == [
            call.update_limits({
                'SvcFoo': self.mock_svc1,
                'SvcBar': self.mock_svc2
            }),
        ]

    def test_check_thresholds_service(self):
        self.mock_svc1.check_thresholds.return_value = {'foo': 'bar'}
        self.mock_svc2.check_thresholds.return_value = {'baz': 'blam'}
        res = self.cls.check_thresholds(service='SvcFoo')
        assert res == {
            'SvcFoo': {
                'foo': 'bar',
            }
        }
        assert self.mock_ta.mock_calls == [
            call.update_limits({'SvcFoo': self.mock_svc1})
        ]

    def test_check_thresholds_no_ta(self):
        self.mock_svc1.check_thresholds.return_value = {
            'foo': 'bar',
            'baz': 'blam',
        }
        self.mock_svc2.check_thresholds.return_value = {}
        self.cls.use_ta = False
        res = self.cls.check_thresholds(use_ta=False)
        assert res == {
            'SvcFoo': {
                'foo': 'bar',
                'baz': 'blam',
            }
        }
        assert self.mock_ta.mock_calls == []
