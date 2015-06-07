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
from contextlib import nested
from mock import patch, call

import awslimitchecker.runner as runner
import awslimitchecker.version as version


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
                patch('awslimitchecker.runner.get_version',
                      spec_set=version.get_version),
                patch('awslimitchecker.runner.get_project_url',
                      spec_set=version.get_project_url),
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
                                'that awslimitchecker knows how to check and '
                                'exit'),
            call().add_argument('-l', '--list-limits', action='store_true',
                                default=False,
                                help='print all default limits in '
                                '"service_name/limit_name" '
                                'format and exit'),
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
                patch('awslimitchecker.runner.get_version',
                      spec_set=version.get_version),
                patch('awslimitchecker.runner.get_project_url',
                      spec_set=version.get_project_url),
                pytest.raises(SystemExit),
        ) as (
            mock_argv,
            mocK_version,
            mock_url,
            excinfo,
        ):
            mocK_version.return_value = 'myver'
            mock_url.return_value = 'myurl'
            runner.console_entry_point()
        out, err = capsys.readouterr()
        assert out == expected
        assert excinfo.value.code == 0
