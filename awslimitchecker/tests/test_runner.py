"""
awslimitchecker/tests/test_runner.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

##############################################################################
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
##############################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/awslimitchecker> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
##############################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
##############################################################################
"""

import argparse
import pytest
import sys
import logging
import json
from mock import patch, call, Mock, DEFAULT

import awslimitchecker.runner as runner
import awslimitchecker.version as version
from awslimitchecker.checker import AwsLimitChecker
from awslimitchecker.limit import AwsLimit, AwsLimitUsage
from awslimitchecker.utils import StoreKeyValuePair
from .support import sample_limits


class TestAwsLimitCheckerRunner(object):

    def test_parse_args(self):
        argv = ['-V']
        res = runner.parse_args(argv)
        assert isinstance(res, argparse.Namespace)
        assert res.version is True

    def test_parse_args_parser(self):
        argv = ['-V']
        desc = 'Report on AWS service limits and usage via boto, optionally ' \
               'warn about any services with usage nearing or exceeding ' \
               'their limits. For further help, see ' \
               '<http://awslimitchecker.readthedocs.org/>'
        epilog = 'awslimitchecker is AGPLv3-licensed Free Software. Anyone ' \
                 'using this program, even remotely over a network, is ' \
                 'entitled to a copy of the source code. You can obtain ' \
                 'the source code of awslimitchecker myver from: <myurl>'
        with patch('awslimitchecker.runner.argparse.ArgumentParser',
                   spec_set=argparse.ArgumentParser) as mock_parser:
            with patch('awslimitchecker.runner._get_version',
                       spec_set=version._get_version) as mock_version:
                with patch('awslimitchecker.runner._get_project_url',
                           spec_set=version._get_project_url) as mock_url:
                    mock_version.return_value = 'myver'
                    mock_url.return_value = 'myurl'
                    runner.parse_args(argv)
        assert mock_parser.mock_calls == [
            call(description=desc, epilog=epilog),
            call().add_argument('-s', '--list-services',
                                default=False, action='store_true',
                                help='print a list of all AWS service types '
                                'that awslimitchecker knows how to check'),
            call().add_argument('-l', '--list-defaults', action='store_true',
                                default=False,
                                help='print all AWS default limits in '
                                '"service_name/limit_name" format'),
            call().add_argument('-L', '--limit', action=StoreKeyValuePair,
                                help='override a single AWS limit, specified in'
                                ' "service_name/limit_name=value" format; can '
                                'be specified multiple times.'),
            call().add_argument('-u', '--show-usage', action='store_true',
                                default=False,
                                help='find and print the current usage of '
                                'all AWS services with known limits'),
            call().add_argument('--iam-policy', action='store_true',
                                default=False,
                                help='output a JSON serialized IAM Policy '
                                'listing the required permissions for '
                                'awslimitchecker to run correctly.'),
            call().add_argument('-W', '--warning-threshold', action='store',
                                type=int, default=80,
                                help='default warning threshold (percentage of '
                                'limit); default: 80'),
            call().add_argument('-C', '--critical-threshold', action='store',
                                type=int, default=99,
                                help='default critical threshold (percentage '
                                'of limit); default: 99'),
            call().add_argument('-v', '--verbose', dest='verbose',
                                action='count',
                                default=0,
                                help='verbose output. specify twice '
                                'for debug-level output.'),
            call().add_argument('-V', '--version', dest='version',
                                action='store_true',
                                default=False,
                                help='print version number and exit.'),
            call().parse_args(argv),
        ]
        assert mock_version.mock_calls == [call()]
        assert mock_url.mock_calls == [call()]

    def test_entry_version(self, capsys):
        argv = ['awslimitchecker', '-V']
        expected = 'awslimitchecker myver (see <myurl> for source code)\n'
        with patch.object(sys, 'argv', argv):
            with patch.multiple(
                    'awslimitchecker.runner',
                    _get_version=DEFAULT,
                    _get_project_url=DEFAULT,
                    AwsLimitChecker=DEFAULT,
            ) as mocks:
                with pytest.raises(SystemExit) as excinfo:
                    mocks['_get_version'].return_value = 'myver'
                    mocks['_get_project_url'].return_value = 'myurl'
                    runner.console_entry_point()
        out, err = capsys.readouterr()
        assert out == expected
        assert err == ''
        assert excinfo.value.code == 0
        assert mocks['AwsLimitChecker'].mock_calls == []

    def test_entry_list_services(self):
        argv = ['awslimitchecker', '-s']
        with patch.object(sys, 'argv', argv):
            with patch.multiple(
                    'awslimitchecker.runner',
                    AwsLimitChecker=DEFAULT,
                    list_services=DEFAULT,
            ) as mocks:
                with pytest.raises(SystemExit) as excinfo:
                    runner.console_entry_point()
        assert excinfo.value.code == 0
        assert mocks['list_services'].mock_calls == [
            call(mocks['AwsLimitChecker'].return_value)
        ]

    def test_list_services(self, capsys):
        expected = 'Bar\nFoo\n'
        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.get_service_names.return_value = [
            'Foo',
            'Bar'
        ]
        runner.list_services(mock_checker)
        out, err = capsys.readouterr()
        assert out == expected
        assert err == ''
        assert mock_checker.mock_calls == [
            call.get_service_names()
        ]

    def test_entry_iam_policy(self):
        argv = ['awslimitchecker', '--iam-policy']
        with patch.object(sys, 'argv', argv):
            with patch.multiple(
                    'awslimitchecker.runner',
                    AwsLimitChecker=DEFAULT,
                    iam_policy=DEFAULT,
            ) as mocks:
                with pytest.raises(SystemExit) as excinfo:
                    runner.console_entry_point()
        assert excinfo.value.code == 0
        assert mocks['iam_policy'].mock_calls == [
            call(mocks['AwsLimitChecker'].return_value)
        ]

    def test_iam_policy(self, capsys):
        expected = {"baz": "blam", "foo": "bar"}
        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.get_required_iam_policy.return_value = {
            'foo': 'bar',
            'baz': 'blam',
        }
        runner.iam_policy(mock_checker)
        out, err = capsys.readouterr()
        assert json.loads(out) == expected
        assert err == ''
        assert mock_checker.mock_calls == [
            call.get_required_iam_policy()
        ]

    def test_entry_list_limits(self):
        argv = ['awslimitchecker', '-l']
        with patch.object(sys, 'argv', argv):
            with patch.multiple(
                    'awslimitchecker.runner',
                    AwsLimitChecker=DEFAULT,
                    list_limits=DEFAULT,
            ) as mocks:
                with pytest.raises(SystemExit) as excinfo:
                    runner.console_entry_point()
        assert excinfo.value.code == 0
        assert mocks['list_limits'].mock_calls == [
            call(mocks['AwsLimitChecker'].return_value)
        ]

    def test_list_limits(self, capsys):
        expected = 'SvcBar/bar limit2\t99\n' + \
                   'SvcBar/barlimit1\t1\n' + \
                   'SvcFoo/foo limit3\t3\n'
        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.get_limits.return_value = sample_limits()
        runner.list_limits(mock_checker)
        out, err = capsys.readouterr()
        assert out == expected
        assert err == ''
        assert mock_checker.mock_calls == [
            call.get_limits()
        ]

    def test_entry_limit(self):
        argv = ['awslimitchecker', '-L', 'foo=bar']
        with patch.object(sys, 'argv', argv):
            with patch.multiple(
                    'awslimitchecker.runner',
                    AwsLimitChecker=DEFAULT,
                    check_thresholds=DEFAULT,
                    set_limit_overrides=DEFAULT,
            ) as mocks:
                mocks['check_thresholds'].return_value = 0
                with pytest.raises(SystemExit) as excinfo:
                    runner.console_entry_point()
        assert excinfo.value.code == 0
        assert mocks['set_limit_overrides'].mock_calls == [
            call(mocks['AwsLimitChecker'].return_value, {'foo': 'bar'})
        ]

    def test_entry_limit_multi(self):
        argv = ['awslimitchecker', '--limit=foo=bar', '--limit=baz=blam']
        with patch.object(sys, 'argv', argv):
            with patch.multiple(
                    'awslimitchecker.runner',
                    AwsLimitChecker=DEFAULT,
                    check_thresholds=DEFAULT,
                    set_limit_overrides=DEFAULT,
            ) as mocks:
                mocks['check_thresholds'].return_value = 0
                with pytest.raises(SystemExit) as excinfo:
                    runner.console_entry_point()
        assert excinfo.value.code == 0
        assert mocks['set_limit_overrides'].mock_calls == [
            call(mocks['AwsLimitChecker'].return_value,
                 {'foo': 'bar', 'baz': 'blam'})
        ]

    def test_set_limit_overrides(self):
        overrides = {
            'EC2/Foo bar': "2",
            'ElastiCache/Cache cluster subnet groups': "100",
        }
        mock_checker = Mock(spec_set=AwsLimitChecker)
        runner.set_limit_overrides(mock_checker, overrides)
        assert mock_checker.mock_calls == [
            call.set_limit_override('EC2', 'Foo bar', 2),
            call.set_limit_override(
                'ElastiCache',
                'Cache cluster subnet groups',
                100
            )
        ]

    def test_set_limit_overrides_error(self):
        overrides = {
            'EC2': 2,
        }
        mock_checker = Mock(spec_set=AwsLimitChecker)
        with pytest.raises(ValueError) as excinfo:
            runner.set_limit_overrides(mock_checker, overrides)
        assert mock_checker.mock_calls == []
        if sys.version_info[0] > 2:
            msg = excinfo.value.args[0]
        else:
            msg = excinfo.value.message
        assert msg == "Limit names must be in " \
            "'service/limit' format; EC2 is invalid."

    def test_entry_show_usage(self):
        argv = ['awslimitchecker', '-u']
        with patch.object(sys, 'argv', argv):
            with patch.multiple(
                    'awslimitchecker.runner',
                    AwsLimitChecker=DEFAULT,
                    show_usage=DEFAULT,
            ) as mocks:
                with pytest.raises(SystemExit) as excinfo:
                    runner.console_entry_point()
        assert excinfo.value.code == 0
        assert mocks['show_usage'].mock_calls == [
            call(mocks['AwsLimitChecker'].return_value)
        ]

    def test_show_usage(self, capsys):
        limits = sample_limits()
        limits['SvcFoo']['foo limit3']._add_current_usage(33)
        limits['SvcBar']['bar limit2']._add_current_usage(22)
        limits['SvcBar']['barlimit1']._add_current_usage(11)
        expected = 'SvcBar/bar limit2\t22\n' + \
                   'SvcBar/barlimit1\t11\n' + \
                   'SvcFoo/foo limit3\t33\n'
        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.get_limits.return_value = limits
        runner.show_usage(mock_checker)
        out, err = capsys.readouterr()
        assert out == expected
        assert err == ''
        assert mock_checker.mock_calls == [
            call.find_usage(),
            call.get_limits()
        ]

    def test_entry_verbose(self, capsys):
        argv = ['awslimitchecker', '-v']
        with patch.object(sys, 'argv', argv):
            with patch.multiple(
                    'awslimitchecker.runner',
                    AwsLimitChecker=DEFAULT,
                    check_thresholds=DEFAULT,
            ) as mocks:
                with patch('awslimitchecker.runner.logger.setLevel'
                           '') as mock_set_level:
                    with pytest.raises(SystemExit) as excinfo:
                        mocks['check_thresholds'].return_value = 6
                        runner.console_entry_point()
        out, err = capsys.readouterr()
        assert err == ''
        assert out == ''
        assert excinfo.value.code == 6
        assert mock_set_level.mock_calls == [call(logging.INFO)]

    def test_entry_debug(self, capsys):
        argv = ['awslimitchecker', '-vv']
        with patch.object(sys, 'argv', argv):
            with patch.multiple(
                    'awslimitchecker.runner',
                    AwsLimitChecker=DEFAULT,
                    check_thresholds=DEFAULT,
            ) as mocks:
                with patch('awslimitchecker.runner.logger.setLevel'
                           '') as mock_set_level:
                    with pytest.raises(SystemExit) as excinfo:
                        mocks['check_thresholds'].return_value = 7
                        runner.console_entry_point()
        out, err = capsys.readouterr()
        assert err == ''
        assert out == ''
        assert excinfo.value.args[0] == 7
        assert mock_set_level.mock_calls == [call(logging.DEBUG)]

    def test_entry_warning(self):
        argv = ['awslimitchecker', '-W', '50']
        with patch.object(sys, 'argv', argv):
            with patch.multiple(
                    'awslimitchecker.runner',
                    AwsLimitChecker=DEFAULT,
                    check_thresholds=DEFAULT,
            ) as mocks:
                with pytest.raises(SystemExit) as excinfo:
                    mocks['check_thresholds'].return_value = 8
                    runner.console_entry_point()
        assert excinfo.value.code == 8
        assert mocks['AwsLimitChecker'].mock_calls == [
            call(warning_threshold=50, critical_threshold=99)
        ]

    def test_entry_critical(self):
        argv = ['awslimitchecker', '-C', '95']
        with patch.object(sys, 'argv', argv):
            with patch.multiple(
                    'awslimitchecker.runner',
                    AwsLimitChecker=DEFAULT,
                    check_thresholds=DEFAULT,
            ) as mocks:
                with pytest.raises(SystemExit) as excinfo:
                    mocks['check_thresholds'].return_value = 9
                    runner.console_entry_point()
        assert excinfo.value.code == 9
        assert mocks['AwsLimitChecker'].mock_calls == [
            call(warning_threshold=80, critical_threshold=95)
        ]

    def test_entry_check_thresholds(self):
        argv = ['awslimitchecker']
        with patch.object(sys, 'argv', argv):
            with patch.multiple(
                    'awslimitchecker.runner',
                    AwsLimitChecker=DEFAULT,
                    check_thresholds=DEFAULT,
            ) as mocks:
                with pytest.raises(SystemExit) as excinfo:
                    mocks['check_thresholds'].return_value = 10
                    runner.console_entry_point()
        assert excinfo.value.code == 10
        assert mocks['check_thresholds'].mock_calls == [
            call(mocks['AwsLimitChecker'].return_value)
        ]

    def test_check_thresholds_ok(self, capsys):
        """no problems, return 0 and print nothing"""
        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.check_thresholds.return_value = {}
        res = runner.check_thresholds(mock_checker)
        out, err = capsys.readouterr()
        assert out == ''
        assert err == ''
        assert mock_checker.mock_calls == [
            call.check_thresholds()
        ]
        assert res == 0

    def test_check_thresholds_many_problems(self):
        """lots of problems"""
        mock_limit1 = Mock(spec_set=AwsLimit)
        mock_w1 = Mock(spec_set=AwsLimitUsage)
        mock_limit1.get_warnings.return_value = [mock_w1]
        mock_c1 = Mock(spec_set=AwsLimitUsage)
        mock_limit1.get_criticals.return_value = [mock_c1]

        mock_limit2 = Mock(spec_set=AwsLimit)
        mock_w2 = Mock(spec_set=AwsLimitUsage)
        mock_limit2.get_warnings.return_value = [mock_w2]
        mock_limit2.get_criticals.return_value = []

        mock_limit3 = Mock(spec_set=AwsLimit)
        mock_w3 = Mock(spec_set=AwsLimitUsage)
        mock_limit3.get_warnings.return_value = [mock_w3]
        mock_limit3.get_criticals.return_value = []

        mock_limit4 = Mock(spec_set=AwsLimit)
        mock_limit4.get_warnings.return_value = []
        mock_c2 = Mock(spec_set=AwsLimitUsage)
        mock_limit4.get_criticals.return_value = [mock_c2]

        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.check_thresholds.return_value = {
            'svc2': {
                'limit3': mock_limit3,
                'limit4': mock_limit4,
            },
            'svc1': {
                'limit1': mock_limit1,
                'limit2': mock_limit2,
            },
        }
        with patch('awslimitchecker.runner.print_issue') as mock_print:
            mock_print.return_value = ''
            res = runner.check_thresholds(mock_checker)
        assert mock_checker.mock_calls == [
            call.check_thresholds()
        ]
        assert mock_print.mock_calls == [
            call('svc1', mock_limit1, [mock_c1], [mock_w1]),
            call('svc1', mock_limit2, [], [mock_w2]),
            call('svc2', mock_limit3, [], [mock_w3]),
            call('svc2', mock_limit4, [mock_c2], []),
        ]
        assert res == 2

    def test_check_thresholds_warn(self):
        """just warnings"""
        mock_limit1 = Mock(spec_set=AwsLimit)
        mock_w1 = Mock(spec_set=AwsLimitUsage)
        mock_w2 = Mock(spec_set=AwsLimitUsage)
        mock_limit1.get_warnings.return_value = [mock_w1, mock_w2]
        mock_limit1.get_criticals.return_value = []

        mock_limit2 = Mock(spec_set=AwsLimit)
        mock_w3 = Mock(spec_set=AwsLimitUsage)
        mock_limit2.get_warnings.return_value = [mock_w3]
        mock_limit2.get_criticals.return_value = []

        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.check_thresholds.return_value = {
            'svc2': {
                'limit2': mock_limit2,
            },
            'svc1': {
                'limit1': mock_limit1,
            },
        }
        with patch('awslimitchecker.runner.print_issue') as mock_print:
            mock_print.return_value = ''
            res = runner.check_thresholds(mock_checker)
        assert mock_checker.mock_calls == [
            call.check_thresholds()
        ]
        assert mock_print.mock_calls == [
            call('svc1', mock_limit1, [], [mock_w1, mock_w2]),
            call('svc2', mock_limit2, [], [mock_w3]),
        ]
        assert res == 1

    def test_check_thresholds_crit(self):
        """only critical"""
        mock_limit1 = Mock(spec_set=AwsLimit)
        mock_limit1.get_warnings.return_value = []
        mock_c1 = Mock(spec_set=AwsLimitUsage)
        mock_c2 = Mock(spec_set=AwsLimitUsage)
        mock_limit1.get_criticals.return_value = [mock_c1, mock_c2]

        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.check_thresholds.return_value = {
            'svc1': {
                'limit1': mock_limit1,
            },
        }
        with patch('awslimitchecker.runner.print_issue') as mock_print:
            mock_print.return_value = ''
            res = runner.check_thresholds(mock_checker)
        assert mock_checker.mock_calls == [
            call.check_thresholds()
        ]
        assert mock_print.mock_calls == [
            call('svc1', mock_limit1, [mock_c1, mock_c2], []),
        ]
        assert res == 2

    def test_print_issue_crit_one(self):
        mock_limit = Mock(spec_set=AwsLimit)
        type(mock_limit).name = 'limitname'
        mock_limit.get_limit.return_value = 12

        c1 = AwsLimitUsage(mock_limit, 56)

        res = runner.print_issue(
            'svcname',
            mock_limit,
            [c1],
            []
        )
        assert res == 'svcname/limitname (limit 12) CRITICAL: 56'

    def test_print_issue_crit_multi(self):
        mock_limit = Mock(spec_set=AwsLimit)
        type(mock_limit).name = 'limitname'
        mock_limit.get_limit.return_value = 5

        c1 = AwsLimitUsage(mock_limit, 10)
        c2 = AwsLimitUsage(mock_limit, 12, id='c2id')
        c3 = AwsLimitUsage(mock_limit, 8)

        res = runner.print_issue(
            'svcname',
            mock_limit,
            [c1, c2, c3],
            []
        )
        assert res == 'svcname/limitname (limit 5) ' \
            'CRITICAL: 8, 10, c2id=12'

    def test_print_issue_warn_one(self):
        mock_limit = Mock(spec_set=AwsLimit)
        type(mock_limit).name = 'limitname'
        mock_limit.get_limit.return_value = 12

        w1 = AwsLimitUsage(mock_limit, 11)

        res = runner.print_issue(
            'svcname',
            mock_limit,
            [],
            [w1]
        )
        assert res == 'svcname/limitname (limit 12) WARNING: 11'

    def test_print_issue_warn_multi(self):
        mock_limit = Mock(spec_set=AwsLimit)
        type(mock_limit).name = 'limitname'
        mock_limit.get_limit.return_value = 12

        w1 = AwsLimitUsage(mock_limit, 11)
        w2 = AwsLimitUsage(mock_limit, 10, id='w2id')
        w3 = AwsLimitUsage(mock_limit, 10, id='w3id')

        res = runner.print_issue(
            'svcname',
            mock_limit,
            [],
            [w1, w2, w3]
        )
        assert res == 'svcname/limitname (limit 12) WARNING: ' \
            'w2id=10, w3id=10, 11'

    def test_print_issue_both_one(self):
        mock_limit = Mock(spec_set=AwsLimit)
        type(mock_limit).name = 'limitname'
        mock_limit.get_limit.return_value = 12

        c1 = AwsLimitUsage(mock_limit, 10)
        w1 = AwsLimitUsage(mock_limit, 10, id='w3id')

        res = runner.print_issue(
            'svcname',
            mock_limit,
            [c1],
            [w1]
        )
        assert res == 'svcname/limitname (limit 12) ' \
            'CRITICAL: 10 ' \
            'WARNING: w3id=10'

    def test_print_issue_both_multi(self):
        mock_limit = Mock(spec_set=AwsLimit)
        type(mock_limit).name = 'limitname'
        mock_limit.get_limit.return_value = 12

        c1 = AwsLimitUsage(mock_limit, 10)
        c2 = AwsLimitUsage(mock_limit, 12, id='c2id')
        c3 = AwsLimitUsage(mock_limit, 8)
        w1 = AwsLimitUsage(mock_limit, 11)
        w2 = AwsLimitUsage(mock_limit, 10, id='w2id')
        w3 = AwsLimitUsage(mock_limit, 10, id='w3id')

        res = runner.print_issue(
            'svcname',
            mock_limit,
            [c1, c2, c3],
            [w1, w2, w3]
        )
        assert res == 'svcname/limitname (limit 12) ' \
            'CRITICAL: 8, 10, c2id=12 ' \
            'WARNING: w2id=10, w3id=10, 11'
