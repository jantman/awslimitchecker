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
bugs please submit them at <https://github.com/jantman/pydnstest> or
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
from contextlib import nested
from mock import patch, call

import awslimitchecker.runner as runner
import awslimitchecker.version as version
from awslimitchecker.checker import AwsLimitChecker
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
               'their limits.'
        epilog = 'awslimitchecker is AGPLv3-licensed Free Software. Anyone ' \
                 'using this program, even remotely over a network, is ' \
                 'entitled to a copy of the source code. You can obtain ' \
                 'the source code of awslimitchecker myver from: <myurl>'
        with nested(
                patch('awslimitchecker.runner.argparse.ArgumentParser',
                      spec_set=argparse.ArgumentParser),
                patch('awslimitchecker.runner._get_version',
                      spec_set=version._get_version),
                patch('awslimitchecker.runner._get_project_url',
                      spec_set=version._get_project_url),
        ) as (
            mock_parser,
            mock_version,
            mock_url,
        ):
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
            call().add_argument('-u', '--show-usage', action='store_true',
                                default=False,
                                help='find and print the current usage of '
                                'all AWS services with known limits'),
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
        with nested(
                patch.object(sys, 'argv', argv),
                patch('awslimitchecker.runner._get_version',
                      spec_set=version._get_version),
                patch('awslimitchecker.runner._get_project_url',
                      spec_set=version._get_project_url),
                patch('awslimitchecker.runner.AwsLimitChecker',
                      spec_set=AwsLimitChecker),
                pytest.raises(SystemExit),
        ) as (
            mock_argv,
            mocK_version,
            mock_url,
            mock_checker,
            excinfo,
        ):
            mocK_version.return_value = 'myver'
            mock_url.return_value = 'myurl'
            runner.console_entry_point()
        out, err = capsys.readouterr()
        assert out == expected
        assert err == ''
        assert excinfo.value.code == 0
        assert mock_checker.mock_calls == []

    def test_entry_list_services(self, capsys):
        argv = ['awslimitchecker', '-s']
        expected = 'Bar\nFoo\n'
        with nested(
                patch.object(sys, 'argv', argv),
                patch('awslimitchecker.runner.AwsLimitChecker',
                      spec_set=AwsLimitChecker),
                pytest.raises(SystemExit),
        ) as (
            mock_argv,
            mock_checker,
            excinfo,
        ):
            mock_checker.return_value.get_service_names.return_value = [
                'Foo',
                'Bar'
            ]
            runner.console_entry_point()
        out, err = capsys.readouterr()
        assert out == expected
        assert err == ''
        assert excinfo.value.code == 0
        assert mock_checker.mock_calls == [
            call(),
            call().get_service_names()
        ]

    def test_entry_list_limits(self, capsys):
        argv = ['awslimitchecker', '-l']
        expected = 'SvcBar/bar limit2\t2\n' + \
                   'SvcBar/barlimit1\t1\n' + \
                   'SvcFoo/foo limit3\t3\n'
        with nested(
                patch.object(sys, 'argv', argv),
                patch('awslimitchecker.runner.AwsLimitChecker',
                      spec_set=AwsLimitChecker),
                pytest.raises(SystemExit),
        ) as (
            mock_argv,
            mock_checker,
            excinfo,
        ):
            mock_checker.return_value.get_limits.return_value \
                = sample_limits()
            runner.console_entry_point()
        out, err = capsys.readouterr()
        assert out == expected
        assert err == ''
        assert excinfo.value.code == 0
        assert mock_checker.mock_calls == [
            call(),
            call().get_limits()
        ]

    def test_entry_show_usage(self, capsys):
        limits = sample_limits()
        limits['SvcFoo']['foo limit3'].current_usage = 33
        limits['SvcBar']['bar limit2'].current_usage = 22
        limits['SvcBar']['barlimit1'].current_usage = 11
        argv = ['awslimitchecker', '-u']
        expected = 'SvcBar/bar limit2\t22\n' + \
                   'SvcBar/barlimit1\t11\n' + \
                   'SvcFoo/foo limit3\t33\n'
        with nested(
                patch.object(sys, 'argv', argv),
                patch('awslimitchecker.runner.AwsLimitChecker',
                      spec_set=AwsLimitChecker),
                pytest.raises(SystemExit),
        ) as (
            mock_argv,
            mock_checker,
            excinfo,
        ):
            mock_checker.return_value.get_limits.return_value \
                = limits
            runner.console_entry_point()
        out, err = capsys.readouterr()
        assert out == expected
        assert err == ''
        assert excinfo.value.code == 0
        assert mock_checker.mock_calls == [
            call(),
            call().find_usage(),
            call().get_limits()
        ]

    def test_entry_verbose(self, capsys):
        argv = ['awslimitchecker', '-v']
        expected = 'ERROR: no action specified. Please see -h|--help.\n'
        with nested(
                patch.object(sys, 'argv', argv),
                patch('awslimitchecker.runner.AwsLimitChecker',
                      spec_set=AwsLimitChecker),
                patch('awslimitchecker.runner.logger.setLevel'),
                pytest.raises(SystemExit),
        ) as (
            mock_argv,
            mock_checker,
            mock_set_level,
            excinfo,
        ):
            runner.console_entry_point()
        out, err = capsys.readouterr()
        assert err == expected
        assert out == ''
        assert excinfo.value.code == 1
        assert mock_checker.mock_calls == [call()]
        assert mock_set_level.mock_calls == [call(logging.INFO)]

    def test_entry_debug(self, capsys):
        argv = ['awslimitchecker', '-vv']
        expected = 'ERROR: no action specified. Please see -h|--help.\n'
        with nested(
                patch.object(sys, 'argv', argv),
                patch('awslimitchecker.runner.AwsLimitChecker',
                      spec_set=AwsLimitChecker),
                patch('awslimitchecker.runner.logger.setLevel'),
                pytest.raises(SystemExit),
        ) as (
            mock_argv,
            mock_checker,
            mock_set_level,
            excinfo,
        ):
            runner.console_entry_point()
        out, err = capsys.readouterr()
        assert err == expected
        assert out == ''
        assert excinfo.value.code == 1
        assert mock_checker.mock_calls == [call()]
        assert mock_set_level.mock_calls == [call(logging.DEBUG)]

    def test_entry_no_action(self, capsys):
        argv = ['awslimitchecker']
        expected = 'ERROR: no action specified. Please see -h|--help.\n'
        with nested(
                patch.object(sys, 'argv', argv),
                patch('awslimitchecker.runner.AwsLimitChecker',
                      spec_set=AwsLimitChecker),
                pytest.raises(SystemExit),
        ) as (
            mock_argv,
            mock_checker,
            excinfo,
        ):
            runner.console_entry_point()
        out, err = capsys.readouterr()
        assert err == expected
        assert out == ''
        assert excinfo.value.code == 1
        assert mock_checker.mock_calls == [call()]
