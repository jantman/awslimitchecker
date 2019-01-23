"""
awslimitchecker/docs/examples/test_check_aws_limits.py

pytest tests for check_aws_limits.py

Requires ``mock``, ``pytest``, ``pytest-cov``, ``pytest-flakes`` and ``pytest-pep8``.

To run: ``py.test -vv -s --cov-report term-missing --cov-report html --cov=check_aws_limits.py test_check_aws_limits.py``

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
from awslimitchecker.limit import AwsLimit, AwsLimitUsage
from mock import Mock, patch, call, PropertyMock, MagicMock
from termcolor import colored
import pytest
import check_aws_limits

class Test_CheckAWSLimits(object):
    """ class to test cm.commands.CheckAWSLimits """

    def test_parser(self):
        """test parser"""
        res = check_aws_limits.parse_args([])
        assert res.error_on_warning is False
        assert res.verbose is False
        res = check_aws_limits.parse_args(['--error-on-warning'])
        assert res.error_on_warning is True
        assert res.verbose is False
        res = check_aws_limits.parse_args(['-v'])
        assert res.error_on_warning is False
        assert res.verbose is True
        res = check_aws_limits.parse_args(['--error-on-warning', '--verbose'])
        assert res.error_on_warning is True
        assert res.verbose is True

    def test_check_limits_ok(self, capsys):
        with patch('check_aws_limits.AwsLimitChecker',
                   create=True) as mock_checker:
            type(mock_checker.return_value).warning_threshold = 60
            type(mock_checker.return_value).critical_threshold = 90
            mock_checker.return_value.check_thresholds.return_value = {}
            mock_checker.return_value.get_limits.return_value = {}
            cmd = check_aws_limits.CheckAWSLimits()
            res = cmd.check_limits()
        assert res == ([], [])
        out, err = capsys.readouterr()
        assert out == 'Checking AWS resource usage; WARNING threshold 60% of ' \
            'limit, CRITICAL threshold 90% of limit\n'
        assert err == ''
        assert mock_checker.mock_calls == [
            call(),
            call().set_threshold_overrides(check_aws_limits.AWS_THRESHOLD_OVERRIDES),
            call().set_limit_overrides(check_aws_limits.AWS_LIMIT_OVERRIDES),
            call().check_thresholds(),
            call().get_limits()
        ]

    def test_check_limits_ok_verbose(self, capsys):
        mock_foo_limit1 = Mock()
        mock_foo_limit1.get_warnings.return_value = []
        mock_foo_limit1.get_criticals.return_value = []
        mock_foo_limit1.get_current_usage_str.return_value = 'foo1_usage'
        mock_foo_limit1.get_limit.return_value = 'foo1_limit'
        mock_bar_limit1 = Mock()
        mock_bar_limit1.get_warnings.return_value = []
        mock_bar_limit1.get_criticals.return_value = []
        mock_bar_limit1.get_current_usage_str.return_value = 'bar1_usage'
        mock_bar_limit1.get_limit.return_value = 'bar1_limit'
        mock_bar_limit2 = Mock()
        mock_bar_limit2.get_warnings.return_value = []
        mock_bar_limit2.get_criticals.return_value = []
        mock_bar_limit2.get_current_usage_str.return_value = 'bar2_usage'
        mock_bar_limit2.get_limit.return_value = 'bar2_limit'

        result = {
            'FooSvc': {
                'FooLimit1': mock_foo_limit1,
            },
            'BarSvc': {
                'BarLimit1': mock_bar_limit1,
                'BarLimit2': mock_bar_limit2,
            },
        }
        with patch('check_aws_limits.AwsLimitChecker',
                   create=True) as mock_checker:
            type(mock_checker.return_value).warning_threshold = 60
            type(mock_checker.return_value).critical_threshold = 90
            mock_checker.return_value.check_thresholds.return_value = {}
            mock_checker.return_value.get_limits.return_value = result
            cmd = check_aws_limits.CheckAWSLimits()
            res = cmd.check_limits(verbose=True)
        assert res == ([], [])
        out, err = capsys.readouterr()
        assert out == 'Checking AWS resource usage; WARNING threshold 60% of ' \
            'limit, CRITICAL threshold 90% of limit\n' \
            "BarSvc 'BarLimit1' OK: bar1_usage (limit=bar1_limit)\n" \
            "BarSvc 'BarLimit2' OK: bar2_usage (limit=bar2_limit)\n" \
            "FooSvc 'FooLimit1' OK: foo1_usage (limit=foo1_limit)\n" \
            "\n\n\n"
        assert err == ''
        assert mock_checker.mock_calls == [
            call(),
            call().set_threshold_overrides(check_aws_limits.AWS_THRESHOLD_OVERRIDES),
            call().set_limit_overrides(check_aws_limits.AWS_LIMIT_OVERRIDES),
            call().check_thresholds(),
            call().get_limits()
        ]

    @patch('check_aws_limits.colored')
    def test_check_limits_warn(self, colored, capsys):
        def se_colored(s, color):
            return "(%s)%s" % (color, s)

        colored.side_effect = se_colored

        mock_foo_limit1 = Mock()
        mock_foo_limit1.get_warnings.return_value = []
        mock_foo_limit1.get_criticals.return_value = []
        mock_foo_limit1.get_current_usage_str.return_value = 'foo1_usage'
        mock_foo_limit1.get_limit.return_value = 'foo1_limit'
        mock_bar_limit1 = Mock()
        usage1 = AwsLimitUsage(mock_bar_limit1, 85)
        mock_bar_limit1.get_warnings.return_value = [usage1]
        mock_bar_limit1.get_criticals.return_value = []
        mock_bar_limit1.get_current_usage_str.return_value = 'bar1_usage'
        mock_bar_limit1.get_limit.return_value = 'bar1_limit'
        mock_bar_limit2 = Mock()
        mock_bar_limit2.get_warnings.return_value = []
        mock_bar_limit2.get_criticals.return_value = []
        mock_bar_limit2.get_current_usage_str.return_value = 'bar2_usage'
        mock_bar_limit2.get_limit.return_value = 'bar2_limit'

        result = {
            'FooSvc': {
                'FooLimit1': mock_foo_limit1,
            },
            'BarSvc': {
                'BarLimit1': mock_bar_limit1,
                'BarLimit2': mock_bar_limit2,
            },
        }
        with patch('check_aws_limits.AwsLimitChecker',
                   create=True) as mock_checker:
            type(mock_checker.return_value).warning_threshold = 60
            type(mock_checker.return_value).critical_threshold = 90
            mock_checker.return_value.check_thresholds.return_value = {}
            mock_checker.return_value.get_limits.return_value = result
            cmd = check_aws_limits.CheckAWSLimits()
            res = cmd.check_limits()
        assert res == (
            ["(yellow)BarSvc 'BarLimit1' usage (85) exceeds warning threshold (limit=bar1_limit)"],
            []
        )
        out, err = capsys.readouterr()
        assert out == 'Checking AWS resource usage; WARNING threshold 60% of ' \
            'limit, CRITICAL threshold 90% of limit\n'
        assert err == ''
        assert mock_checker.mock_calls == [
            call(),
            call().set_threshold_overrides(check_aws_limits.AWS_THRESHOLD_OVERRIDES),
            call().set_limit_overrides(check_aws_limits.AWS_LIMIT_OVERRIDES),
            call().check_thresholds(),
            call().get_limits()
        ]

    @patch('check_aws_limits.colored')
    def test_check_limits_warn_verbose(self, colored, capsys):
        def se_colored(s, color):
            return "(%s)%s" % (color, s)

        colored.side_effect = se_colored

        mock_foo_limit1 = Mock()
        mock_foo_limit1.get_warnings.return_value = []
        mock_foo_limit1.get_criticals.return_value = []
        mock_foo_limit1.get_current_usage_str.return_value = 'foo1_usage'
        mock_foo_limit1.get_limit.return_value = 'foo1_limit'
        mock_bar_limit1 = Mock()
        usage1 = AwsLimitUsage(mock_bar_limit1, 85)
        mock_bar_limit1.get_warnings.return_value = [usage1]
        mock_bar_limit1.get_criticals.return_value = []
        mock_bar_limit1.get_current_usage_str.return_value = 'bar1_usage'
        mock_bar_limit1.get_limit.return_value = 'bar1_limit'
        mock_bar_limit2 = Mock()
        mock_bar_limit2.get_warnings.return_value = []
        mock_bar_limit2.get_criticals.return_value = []
        mock_bar_limit2.get_current_usage_str.return_value = 'bar2_usage'
        mock_bar_limit2.get_limit.return_value = 'bar2_limit'

        result = {
            'FooSvc': {
                'FooLimit1': mock_foo_limit1,
            },
            'BarSvc': {
                'BarLimit1': mock_bar_limit1,
                'BarLimit2': mock_bar_limit2,
            },
        }
        with patch('check_aws_limits.AwsLimitChecker',
                   create=True) as mock_checker:
            type(mock_checker.return_value).warning_threshold = 60
            type(mock_checker.return_value).critical_threshold = 90
            mock_checker.return_value.check_thresholds.return_value = {}
            mock_checker.return_value.get_limits.return_value = result
            cmd = check_aws_limits.CheckAWSLimits()
            res = cmd.check_limits(verbose=True)
        assert res == (
            ["(yellow)BarSvc 'BarLimit1' usage (85) exceeds warning threshold (limit=bar1_limit)"],
            []
        )
        out, err = capsys.readouterr()
        assert out == 'Checking AWS resource usage; WARNING threshold 60% of ' \
            'limit, CRITICAL threshold 90% of limit\n' \
            "BarSvc 'BarLimit2' OK: bar2_usage (limit=bar2_limit)\n" \
            "FooSvc 'FooLimit1' OK: foo1_usage (limit=foo1_limit)\n" \
            "\n\n\n"
        assert err == ''
        assert mock_checker.mock_calls == [
            call(),
            call().set_threshold_overrides(check_aws_limits.AWS_THRESHOLD_OVERRIDES),
            call().set_limit_overrides(check_aws_limits.AWS_LIMIT_OVERRIDES),
            call().check_thresholds(),
            call().get_limits()
        ]

    @patch('check_aws_limits.colored')
    def test_check_limits_crit(self, colored, capsys):
        def se_colored(s, color):
            return "(%s)%s" % (color, s)

        colored.side_effect = se_colored

        mock_foo_limit1 = Mock()
        mock_foo_limit1.get_warnings.return_value = []
        mock_foo_limit1.get_criticals.return_value = []
        mock_foo_limit1.get_current_usage_str.return_value = 'foo1_usage'
        mock_foo_limit1.get_limit.return_value = 'foo1_limit'
        mock_bar_limit1 = Mock()
        usage1 = AwsLimitUsage(mock_bar_limit1, 95)
        mock_bar_limit1.get_warnings.return_value = []
        mock_bar_limit1.get_criticals.return_value = [usage1]
        mock_bar_limit1.get_current_usage_str.return_value = 'bar1_usage'
        mock_bar_limit1.get_limit.return_value = 'bar1_limit'
        mock_bar_limit2 = Mock()
        mock_bar_limit2.get_warnings.return_value = []
        mock_bar_limit2.get_criticals.return_value = []
        mock_bar_limit2.get_current_usage_str.return_value = 'bar2_usage'
        mock_bar_limit2.get_limit.return_value = 'bar2_limit'

        result = {
            'FooSvc': {
                'FooLimit1': mock_foo_limit1,
            },
            'BarSvc': {
                'BarLimit1': mock_bar_limit1,
                'BarLimit2': mock_bar_limit2,
            },
        }
        with patch('check_aws_limits.AwsLimitChecker',
                   create=True) as mock_checker:
            type(mock_checker.return_value).warning_threshold = 60
            type(mock_checker.return_value).critical_threshold = 90
            mock_checker.return_value.check_thresholds.return_value = {}
            mock_checker.return_value.get_limits.return_value = result
            cmd = check_aws_limits.CheckAWSLimits()
            res = cmd.check_limits()
        assert res == (
            [],
            ["(red)BarSvc 'BarLimit1' usage (95) exceeds critical threshold (limit=bar1_limit)"]
        )
        out, err = capsys.readouterr()
        assert out == 'Checking AWS resource usage; WARNING threshold 60% of ' \
            'limit, CRITICAL threshold 90% of limit\n'
        assert err == ''
        assert mock_checker.mock_calls == [
            call(),
            call().set_threshold_overrides(check_aws_limits.AWS_THRESHOLD_OVERRIDES),
            call().set_limit_overrides(check_aws_limits.AWS_LIMIT_OVERRIDES),
            call().check_thresholds(),
            call().get_limits()
        ]

    @patch('check_aws_limits.colored')
    def test_check_limits_crit_verbose(self, colored, capsys):
        def se_colored(s, color):
            return "(%s)%s" % (color, s)

        colored.side_effect = se_colored

        mock_foo_limit1 = Mock()
        mock_foo_limit1.get_warnings.return_value = []
        mock_foo_limit1.get_criticals.return_value = []
        mock_foo_limit1.get_current_usage_str.return_value = 'foo1_usage'
        mock_foo_limit1.get_limit.return_value = 'foo1_limit'
        mock_bar_limit1 = Mock()
        usage1 = AwsLimitUsage(mock_bar_limit1, 95)
        mock_bar_limit1.get_warnings.return_value = []
        mock_bar_limit1.get_criticals.return_value = [usage1]
        mock_bar_limit1.get_current_usage_str.return_value = 'bar1_usage'
        mock_bar_limit1.get_limit.return_value = 'bar1_limit'
        mock_bar_limit2 = Mock()
        mock_bar_limit2.get_warnings.return_value = []
        mock_bar_limit2.get_criticals.return_value = []
        mock_bar_limit2.get_current_usage_str.return_value = 'bar2_usage'
        mock_bar_limit2.get_limit.return_value = 'bar2_limit'

        result = {
            'FooSvc': {
                'FooLimit1': mock_foo_limit1,
            },
            'BarSvc': {
                'BarLimit1': mock_bar_limit1,
                'BarLimit2': mock_bar_limit2,
            },
        }
        with patch('check_aws_limits.AwsLimitChecker',
                   create=True) as mock_checker:
            type(mock_checker.return_value).warning_threshold = 60
            type(mock_checker.return_value).critical_threshold = 90
            mock_checker.return_value.check_thresholds.return_value = {}
            mock_checker.return_value.get_limits.return_value = result
            cmd = check_aws_limits.CheckAWSLimits()
            res = cmd.check_limits(verbose=True)
        assert res == (
            [],
            ["(red)BarSvc 'BarLimit1' usage (95) exceeds critical threshold (limit=bar1_limit)"]
        )
        out, err = capsys.readouterr()
        assert out == 'Checking AWS resource usage; WARNING threshold 60% of ' \
            'limit, CRITICAL threshold 90% of limit\n' \
            "BarSvc 'BarLimit2' OK: bar2_usage (limit=bar2_limit)\n" \
            "FooSvc 'FooLimit1' OK: foo1_usage (limit=foo1_limit)\n" \
            "\n\n\n"
        assert err == ''
        assert mock_checker.mock_calls == [
            call(),
            call().set_threshold_overrides(check_aws_limits.AWS_THRESHOLD_OVERRIDES),
            call().set_limit_overrides(check_aws_limits.AWS_LIMIT_OVERRIDES),
            call().check_thresholds(),
            call().get_limits()
        ]

    def test_run_ok(self, capsys):
        cls = check_aws_limits.CheckAWSLimits()
        with patch('check_aws_limits.CheckAWSLimits.check_limits') as mock_check:
            mock_check.return_value = ([], [])
            cls.run(verbose=True)
        assert mock_check.mock_calls == [call.check_limits(verbose=True)]
        out, err = capsys.readouterr()
        assert out == "All limits are within thresholds.\n"
        assert err == ''

    def test_run_warn(self, capsys):
        cls = check_aws_limits.CheckAWSLimits()
        with patch('check_aws_limits.CheckAWSLimits.check_limits') as mock_check:
            mock_check.return_value = (
                ['warn1', 'warn2'],
                []
            )
            cls.run()
        assert mock_check.mock_calls == [call.check_limits(verbose=False)]
        out, err = capsys.readouterr()
        assert out == "\nWARNING:\n\n" \
            "warn1\n" \
            "warn2\n" \
            "\n0 limit(s) above CRITICAL threshold; 2 limit(s) above WARNING threshold\n"
        assert err == ''

    def test_run_warn_error_on_warning(self, capsys):
        cls = check_aws_limits.CheckAWSLimits()
        with patch('check_aws_limits.CheckAWSLimits.check_limits') as mock_check:
            mock_check.return_value = (
                ['warn1', 'warn2'],
                []
            )
            with pytest.raises(SystemExit) as excinfo:
                cls.run(error_on_warning=True)
            assert excinfo.value.code == 1
        assert mock_check.mock_calls == [call.check_limits(verbose=False)]
        out, err = capsys.readouterr()
        assert out == "\nWARNING:\n\n" \
            "warn1\n" \
            "warn2\n" \
            "\n0 limit(s) above CRITICAL threshold; 2 limit(s) above WARNING threshold\n"
        assert err == ''

    def test_run_crit(self, capsys):
        cls = check_aws_limits.CheckAWSLimits()
        with patch('check_aws_limits.CheckAWSLimits.check_limits') as mock_check:
            mock_check.return_value = (
                [],
                ['crit1']
            )
            with pytest.raises(SystemExit) as excinfo:
                cls.run(error_on_warning=True)
            assert excinfo.value.code == 1
        assert mock_check.mock_calls == [call.check_limits(verbose=False)]
        out, err = capsys.readouterr()
        assert out == "\nCRITICAL:\n\n" \
            "crit1\n" \
            "\n1 limit(s) above CRITICAL threshold; 0 limit(s) above WARNING threshold\n"
        assert err == ''

    def test_run_warn_and_crit(self, capsys):
        cls = check_aws_limits.CheckAWSLimits()
        with patch('check_aws_limits.CheckAWSLimits.check_limits') as mock_check:
            mock_check.return_value = (
                ['warn1', 'warn2'],
                ['crit1']
            )
            with pytest.raises(SystemExit) as excinfo:
                cls.run(error_on_warning=True)
            assert excinfo.value.code == 1
        assert mock_check.mock_calls == [call.check_limits(verbose=False)]
        out, err = capsys.readouterr()
        assert out == "\nWARNING:\n\n" \
            "warn1\n" \
            "warn2\n" \
            "\nCRITICAL:\n\n" \
            "crit1\n" \
            "\n1 limit(s) above CRITICAL threshold; 2 limit(s) above WARNING threshold\n"
        assert err == ''
