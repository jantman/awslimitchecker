"""
awslimitchecker/tests/test_runner.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

##############################################################################
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
import termcolor
from freezegun import freeze_time

from awslimitchecker.runner import Runner, console_entry_point
from awslimitchecker.checker import AwsLimitChecker
from awslimitchecker.limit import AwsLimit, AwsLimitUsage
from awslimitchecker.utils import StoreKeyValuePair
from .support import sample_limits, sample_limits_api

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, mock_open, PropertyMock
else:
    from unittest.mock import patch, call, Mock, mock_open, PropertyMock


def red(s):
    return termcolor.colored(s, 'red')


def yellow(s):
    return termcolor.colored(s, 'yellow')


# patch base
pb = 'awslimitchecker.runner'


class RunnerTester(object):

    def setup(self):
        self.cls = Runner()
        self.mock_ver_info = Mock(
            release='1.2.3',
            url='http://myurl',
            commit='abcd',
            tag='mytag',
            version_str='1.2.3@mytag'
        )


class TestModule(RunnerTester):

    def test_module_entry_point(self):
        with patch('%s.Runner' % pb) as mock_runner:
            console_entry_point()
        assert mock_runner.mock_calls == [
            call(),
            call().console_entry_point(),
        ]


class TestInit(RunnerTester):

    def test_init(self):
        assert self.cls.colorize is True
        assert self.cls.checker is None
        assert self.cls.skip_ta is False
        assert self.cls.service_name is None
        assert len(self.cls.skip_check) == 0


class TestParseArgs(RunnerTester):

    def test_simple(self):
        argv = ['-V']
        res = self.cls.parse_args(argv)
        assert isinstance(res, argparse.Namespace)
        assert res.version is True
        assert res.ta_refresh_mode is None
        assert res.limit == {}
        assert res.limit_override_json is None
        assert res.threshold_override_json is None
        assert res.list_metrics_providers is False
        assert res.metrics_provider is None
        assert res.metrics_config == {}
        assert res.list_alert_providers is False
        assert res.alert_provider is None
        assert res.alert_config == {}
        assert res.role_partition == 'aws'
        assert res.ta_api_region == 'us-east-1'
        assert res.skip_quotas is False

    def test_parser(self):
        argv = ['-V']
        desc = 'Report on AWS service limits and usage via boto3, optionally ' \
               'warn about any services with usage nearing or exceeding ' \
               'their limits. For further help, see ' \
               '<http://awslimitchecker.readthedocs.org/>'
        epilog = 'awslimitchecker is AGPLv3-licensed Free Software. Anyone ' \
                 'using this program, even remotely over a network, is ' \
                 'entitled to a copy of the source code. Use `--version` for '\
                 'information on the source code location.'
        with patch('awslimitchecker.runner.argparse.ArgumentParser',
                   spec_set=argparse.ArgumentParser) as mock_parser:
            mock_result = Mock(ta_refresh_wait=True)
            mock_parser.return_value.parse_args.return_value = mock_result
            self.cls.parse_args(argv)
        assert mock_parser.mock_calls == [
            call(description=desc, epilog=epilog),
            call().add_argument('-S', '--service', action='store', nargs='*',
                                help='perform action for only the specified '
                                     'service name; see -s|--list-services for '
                                     'valid names'),
            call().add_argument('--skip-service', action='append',
                                dest='skip_service', default=[],
                                help='avoid performing actions for the '
                                     'specified service name; see '
                                     '-s|--list-services for valid names'),
            call().add_argument('--skip-check', action='append',
                                dest='skip_check', default=[],
                                help='avoid performing actions for the '
                                     'specified check name'),
            call().add_argument('-s', '--list-services',
                                default=False, action='store_true',
                                help='print a list of all AWS service types '
                                'that awslimitchecker knows how to check'),
            call().add_argument('-l', '--list-limits', action='store_true',
                                default=False,
                                help='print all AWS effective limits in '
                                '"service_name/limit_name" format'),
            call().add_argument('--list-defaults', action='store_true',
                                default=False,
                                help='print all AWS default limits in '
                                '"service_name/limit_name" format'),
            call().add_argument('-L', '--limit', action=StoreKeyValuePair,
                                help='override a single AWS limit, specified in'
                                ' "service_name/limit_name=value" format; can '
                                'be specified multiple times.'),
            call().add_argument('--limit-override-json', action='store',
                                type=str, default=None,
                                help='Absolute or relative path, or s3:// URL, '
                                     'to a JSON file specifying limit '
                                     'overrides. See docs for expected format.'
                                ),
            call().add_argument('--threshold-override-json', action='store',
                                type=str, default=None,
                                help='Absolute or relative path, or s3:// URL,'
                                     ' to a JSON file specifying threshold '
                                     'overrides. See docs for expected format.'
                                ),
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
            call().add_argument('-P', '--profile', action='store',
                                dest='profile_name', type=str, default=None,
                                help='Name of profile in the AWS cross-sdk '
                                     'credentials file to use credentials from;'
                                     ' similar to the corresponding awscli '
                                     'option'),
            call().add_argument('-A', '--sts-account-id', action='store',
                                type=str, default=None,
                                help='for use with STS, the Account ID of the '
                                'destination account (account to assume a role'
                                ' in)'),
            call().add_argument('-R', '--sts-account-role', action='store',
                                type=str, default=None,
                                help='for use with STS, the name of the IAM '
                                'role to assume'),
            call().add_argument('-E', '--external-id', action='store', type=str,
                                default=None, help='External ID to use when '
                                'assuming a role via STS'),
            call().add_argument('-M', '--mfa-serial-number', action='store',
                                type=str, default=None, help='MFA Serial '
                                'Number to use when assuming a role via STS'),
            call().add_argument('-T', '--mfa-token', action='store', type=str,
                                default=None, help='MFA Token to use when '
                                'assuming a role via STS'),
            call().add_argument('-r', '--region', action='store',
                                type=str, default=None,
                                help='AWS region name to connect to; required '
                                'for STS'),
            call().add_argument('--role-partition', action='store', type=str,
                                default='aws',
                                help='AWS partition name to use for '
                                     'account_role when connecting via STS; '
                                     'see documentation for more information'
                                     ' (default: "aws")'),
            call().add_argument('--ta-api-region', action='store', type=str,
                                default='us-east-1',
                                help='Region to use for Trusted Advisor / '
                                     'Support API (default: us-east-1)'),
            call().add_argument('--skip-ta', action='store_true', default=False,
                                help='do not attempt to pull *any* information '
                                'on limits from Trusted Advisor'),
            call().add_argument('--skip-quotas', action='store_true',
                                default=False,
                                help='Do not attempt to connect to Service '
                                     'Quotas service or use its data for '
                                     'current limits'),
            call().add_mutually_exclusive_group(),
            call().add_mutually_exclusive_group().add_argument(
                '--ta-refresh-wait', action='store_true', default=False,
                dest='ta_refresh_wait',
                help='If applicable, refresh all Trusted Advisor limit-related '
                     'checks, and wait for the refresh to complete before '
                     'continuing.'),
            call().add_mutually_exclusive_group().add_argument(
                '--ta-refresh-trigger', action='store_true', default=False,
                dest='ta_refresh_trigger',
                help='If applicable, trigger refreshes for all Trusted '
                     'Advisor limit-related checks, but do not wait for '
                     'them to finish refreshing; trigger the refresh and '
                     'continue on (useful to ensure checks are refreshed '
                     'before the next scheduled run).'),
            call().add_mutually_exclusive_group().add_argument(
                '--ta-refresh-older', action='store', default=None,
                dest='ta_refresh_older',
                help='If applicable, trigger refreshes for all Trusted '
                     'Advisor limit-related checks with results more than '
                     'this number of seconds old. Wait for the refresh to '
                     'complete before continuing.',
                type=int),
            call().add_argument('--ta-refresh-timeout', action='store',
                                default=None, dest='ta_refresh_timeout',
                                help='If waiting for TA checks to refresh, '
                                     'wait up to this number of seconds '
                                     'before continuing on anyway.',
                                type=int),
            call().add_argument('--no-color', action='store_true',
                                default=False,
                                help='do not colorize output'),
            call().add_argument('--no-check-version', action='store_false',
                                default=True, dest='check_version',
                                help='do not check latest version at startup'),
            call().add_argument('-v', '--verbose', dest='verbose',
                                action='count',
                                default=0,
                                help='verbose output. specify twice '
                                'for debug-level output.'),
            call().add_argument('-V', '--version', dest='version',
                                action='store_true',
                                default=False,
                                help='print version number and exit.'),
            call().add_argument('--list-metrics-providers',
                                dest='list_metrics_providers',
                                action='store_true', default=False,
                                help='List available metrics providers and exit'
                                ),
            call().add_argument('--metrics-provider', dest='metrics_provider',
                                type=str,
                                action='store', default=None,
                                help='Metrics provider class name, to enable '
                                     'sending metrics'
                                ),
            call().add_argument('--metrics-config', action=StoreKeyValuePair,
                                dest='metrics_config',
                                help='Specify key/value parameters for the '
                                     'metrics provider constructor. See '
                                     'documentation for further information.'),
            call().add_argument('--list-alert-providers',
                                dest='list_alert_providers',
                                action='store_true', default=False,
                                help='List available alert providers '
                                     'and exit'),
            call().add_argument('--alert-provider', dest='alert_provider',
                                type=str, action='store', default=None,
                                help='Alert provider class name, to enable '
                                     'sending notifications'),
            call().add_argument('--alert-config', action=StoreKeyValuePair,
                                dest='alert_config',
                                help='Specify key/value parameters for the '
                                     'alert provider constructor. See '
                                     'documentation for further information.'
                                ),
            call().parse_args(argv)
        ]

    def test_multiple_ta(self):
        argv = ['--ta-refresh-wait', '--ta-refresh-older=100']
        with pytest.raises(SystemExit):
            self.cls.parse_args(argv)

    def test_ta_refresh_wait(self):
        argv = ['--ta-refresh-wait']
        res = self.cls.parse_args(argv)
        assert isinstance(res, argparse.Namespace)
        assert res.ta_refresh_mode == 'wait'

    def test_ta_refresh_trigger(self):
        argv = ['--ta-refresh-trigger']
        res = self.cls.parse_args(argv)
        assert isinstance(res, argparse.Namespace)
        assert res.ta_refresh_mode == 'trigger'

    def test_skip_quotas(self):
        argv = ['--skip-quotas']
        res = self.cls.parse_args(argv)
        assert isinstance(res, argparse.Namespace)
        assert res.skip_quotas is True

    def test_ta_refresh_older(self):
        argv = ['--ta-refresh-older=123']
        res = self.cls.parse_args(argv)
        assert isinstance(res, argparse.Namespace)
        assert res.ta_refresh_mode == 123

    def test_skip_service_none(self):
        argv = []
        res = self.cls.parse_args(argv)
        assert res.skip_service == []

    def test_skip_service_one(self):
        argv = ['--skip-service', 'foo']
        res = self.cls.parse_args(argv)
        assert res.skip_service == ['foo']

    def test_skip_service_multiple(self):
        argv = [
            '--skip-service', 'foo',
            '--skip-service', 'bar',
            '--skip-service=baz'
        ]
        res = self.cls.parse_args(argv)
        assert res.skip_service == ['foo', 'bar', 'baz']

    def test_skip_check(self):
        argv = [
            '--skip-check', 'EC2/Running On-Demand x1e.8xlarge instances',
        ]
        res = self.cls.parse_args(argv)
        assert res.skip_check == ['EC2/Running On-Demand x1e.8xlarge instances']

    def test_skip_check_multiple(self):
        argv = [
            '--skip-check', 'EC2/Running On-Demand x1e.8xlarge instances',
            '--skip-check', 'EC2/Running On-Demand c5.9xlarge instances',
        ]
        res = self.cls.parse_args(argv)
        assert res.skip_check == [
            'EC2/Running On-Demand x1e.8xlarge instances',
            'EC2/Running On-Demand c5.9xlarge instances',
        ]

    def test_list_metrics_providers(self):
        res = self.cls.parse_args(['--list-metrics-providers'])
        assert res.list_metrics_providers is True

    def test_metrics_provider(self):
        res = self.cls.parse_args([
            '--metrics-provider=ClassName',
            '--metrics-config=foo=bar',
            '--metrics-config=baz=blam'
        ])
        assert res.metrics_provider == 'ClassName'
        assert res.metrics_config == {'foo': 'bar', 'baz': 'blam'}

    def test_list_alert_providers(self):
        res = self.cls.parse_args(['--list-alert-providers'])
        assert res.list_alert_providers is True

    def test_alert_provider(self):
        res = self.cls.parse_args([
            '--alert-provider=ClassName',
            '--alert-config=foo=bar',
            '--alert-config=baz=blam'
        ])
        assert res.alert_provider == 'ClassName'
        assert res.alert_config == {'foo': 'bar', 'baz': 'blam'}

    def test_role_partition_ta_api_region(self):
        argv = [
            '--role-partition=foo',
            '--ta-api-region=bar'
        ]
        res = self.cls.parse_args(argv)
        assert res.role_partition == 'foo'
        assert res.ta_api_region == 'bar'


class TestListServices(RunnerTester):

    def test_happy_path(self, capsys):
        expected = 'Bar\nFoo\n'
        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.get_service_names.return_value = [
            'Foo',
            'Bar'
        ]
        self.cls.checker = mock_checker
        self.cls.list_services()
        out, err = capsys.readouterr()
        assert out == expected
        assert mock_checker.mock_calls == [
            call.get_service_names()
        ]


class TestIamPolicy(RunnerTester):

    def test_happy_path(self, capsys):
        expected = {"baz": "blam", "foo": "bar"}
        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.get_required_iam_policy.return_value = {
            'foo': 'bar',
            'baz': 'blam',
        }
        self.cls.checker = mock_checker
        self.cls.iam_policy()
        out, err = capsys.readouterr()
        assert json.loads(out) == expected
        assert mock_checker.mock_calls == [
            call.get_required_iam_policy()
        ]


class TestListDefaults(RunnerTester):

    def test_simple(self, capsys):
        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.get_limits.return_value = sample_limits()
        self.cls.checker = mock_checker
        with patch('awslimitchecker.runner.dict2cols',
                   autospec=True) as mock_d2c:
            mock_d2c.return_value = 'd2cval'
            self.cls.list_defaults()
        out, err = capsys.readouterr()
        assert out == 'd2cval\n'
        assert mock_checker.mock_calls == [
            call.get_limits(service=None)
        ]
        assert mock_d2c.mock_calls == [
            call({
                'SvcBar/bar limit2': '2',
                'SvcBar/barlimit1': '1',
                'SvcFoo/foo limit3': '3',
            })
        ]

    def test_one_service(self, capsys):
        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.get_limits.return_value = {
            'SvcFoo': sample_limits()['SvcFoo'],
        }
        self.cls.checker = mock_checker
        self.cls.service_name = ['SvcFoo']
        with patch('awslimitchecker.runner.dict2cols',
                   autospec=True) as mock_d2c:
            mock_d2c.return_value = 'd2cval'
            self.cls.list_defaults()
        out, err = capsys.readouterr()
        assert out == 'd2cval\n'
        assert mock_checker.mock_calls == [
            call.get_limits(service=['SvcFoo'])
        ]
        assert mock_d2c.mock_calls == [
            call({
                'SvcFoo/foo limit3': '3',
            })
        ]


class TestListLimits(RunnerTester):

    def test_simple(self, capsys):
        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.get_limits.return_value = sample_limits_api()
        self.cls.checker = mock_checker
        with patch('awslimitchecker.runner.dict2cols') as mock_d2c:
            mock_d2c.return_value = 'd2cval'
            self.cls.list_limits()
        out, err = capsys.readouterr()
        assert out == 'd2cval\n'
        assert mock_checker.mock_calls == [
            call.get_limits(use_ta=True, service=None)
        ]
        assert mock_d2c.mock_calls == [
            call({
                'SvcBar/bar limit2': '99',
                'SvcBar/barlimit1': '1',
                'SvcFoo/foo limit3': '10 (TA)',
                'SvcFoo/zzz limit4': '34 (API)',
                'SvcFoo/limit with usage maximums/res_id': '10 (API)',
                'SvcFoo/zzz limit5': '60.0 (Quotas)'
            })
        ]

    def test_one_service(self, capsys):
        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.get_limits.return_value = {
            'SvcFoo': sample_limits_api()['SvcFoo'],
        }
        self.cls.checker = mock_checker
        self.cls.service_name = ['SvcFoo']
        with patch('awslimitchecker.runner.dict2cols') as mock_d2c:
            mock_d2c.return_value = 'd2cval'
            self.cls.list_limits()
        out, err = capsys.readouterr()
        assert out == 'd2cval\n'
        assert mock_checker.mock_calls == [
            call.get_limits(use_ta=True, service=['SvcFoo'])
        ]
        assert mock_d2c.mock_calls == [
            call({
                'SvcFoo/foo limit3': '10 (TA)',
                'SvcFoo/zzz limit4': '34 (API)',
                'SvcFoo/limit with usage maximums/res_id': '10 (API)',
                'SvcFoo/zzz limit5': '60.0 (Quotas)'
            })
        ]


class TestSetLimitOverride(RunnerTester):

    def test_simple(self):
        overrides = {
            'EC2/Foo bar': "2",
            'ElastiCache/Cache cluster subnet groups': "100",
        }
        mock_checker = Mock(spec_set=AwsLimitChecker)
        self.cls.checker = mock_checker
        self.cls.set_limit_overrides(overrides)
        assert mock_checker.mock_calls == [
            call.set_limit_override('EC2', 'Foo bar', 2),
            call.set_limit_override(
                'ElastiCache',
                'Cache cluster subnet groups',
                100
            )
        ]

    def test_error(self):
        overrides = {
            'EC2': 2,
        }
        mock_checker = Mock(spec_set=AwsLimitChecker)
        self.cls.checker = mock_checker
        with pytest.raises(ValueError) as excinfo:
            self.cls.set_limit_overrides(overrides)
        assert mock_checker.mock_calls == []
        if sys.version_info[0] > 2:
            msg = excinfo.value.args[0]
        else:
            msg = excinfo.value.message
        assert msg == "Limit names must be in " \
            "'service/limit' format; EC2 is invalid."


class TestLoadJson(RunnerTester):

    def test_local_file_py27(self):
        data = u'{"Foo": {"bar": 23, "baz": 6}, "Blam": {"Blarg": 73}}'
        mock_body = Mock()
        mock_body.read.return_value = '{"Foo": {"bar": 23, "baz": 6}}'
        mock_client = Mock()
        mock_client.get_object.return_value = {'Body': mock_body}
        with patch(
            '%s.open' % pb, mock_open(read_data=data), create=True
        ) as m_open:
            with patch('%s.boto3.client' % pb) as m_client:
                m_client.return_value = mock_client
                res = self.cls.load_json('/foo/bar/baz.json')
        assert m_open.mock_calls == [
            call('/foo/bar/baz.json', 'r'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None)
        ]
        assert m_client.mock_calls == []
        assert res == {
            'Foo': {'bar': 23, 'baz': 6},
            'Blam': {'Blarg': 73}
        }

    def test_s3_py27(self):
        data = '{"Foo": {"bar": 23, "baz": 6}, "Blam": {"Blarg": 73}}'
        mock_body = Mock()
        mock_body.read.return_value = data
        mock_client = Mock()
        mock_client.get_object.return_value = {'Body': mock_body}
        with patch(
            '%s.open' % pb, mock_open(read_data=data), create=True
        ) as m_open:
            with patch('%s.boto3.client' % pb) as m_client:
                m_client.return_value = mock_client
                res = self.cls.load_json(
                    's3://bucketname/key/foo/bar/baz.json'
                )
        assert m_open.mock_calls == []
        assert m_client.mock_calls == [
            call('s3'),
            call().get_object(Bucket='bucketname', Key='key/foo/bar/baz.json')
        ]
        assert res == {
            'Foo': {'bar': 23, 'baz': 6},
            'Blam': {'Blarg': 73}
        }

    def test_local_file_py37(self):
        data = '{"Foo": {"bar": 23, "baz": 6}, "Blam": {"Blarg": 73}}'
        mock_body = Mock()
        mock_body.read.return_value = '{"Foo": {"bar": 23, "baz": 6}}'
        mock_client = Mock()
        mock_client.get_object.return_value = {'Body': mock_body}
        with patch(
            '%s.open' % pb, mock_open(read_data=data), create=True
        ) as m_open:
            with patch('%s.boto3.client' % pb) as m_client:
                m_client.return_value = mock_client
                res = self.cls.load_json('/foo/bar/baz.json')
        assert m_open.mock_calls == [
            call('/foo/bar/baz.json', 'r'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None)
        ]
        assert m_client.mock_calls == []
        assert res == {
            'Foo': {'bar': 23, 'baz': 6},
            'Blam': {'Blarg': 73}
        }

    def test_s3_py37(self):
        data = b'{"Foo": {"bar": 23, "baz": 6}, "Blam": {"Blarg": 73}}'
        mock_body = Mock()
        mock_body.read.return_value = data
        mock_client = Mock()
        mock_client.get_object.return_value = {'Body': mock_body}
        with patch(
            '%s.open' % pb, mock_open(read_data=data), create=True
        ) as m_open:
            with patch('%s.boto3.client' % pb) as m_client:
                m_client.return_value = mock_client
                res = self.cls.load_json(
                    's3://bucketname/key/foo/bar/baz.json'
                )
        assert m_open.mock_calls == []
        assert m_client.mock_calls == [
            call('s3'),
            call().get_object(Bucket='bucketname', Key='key/foo/bar/baz.json')
        ]
        assert res == {
            'Foo': {'bar': 23, 'baz': 6},
            'Blam': {'Blarg': 73}
        }


class TestSetLimitOverridesFromJson(RunnerTester):

    def test_happy_path(self):
        mock_checker = Mock(spec_set=AwsLimitChecker)
        self.cls.checker = mock_checker
        with patch('%s.Runner.load_json' % pb, autospec=True) as m_load:
            m_load.return_value = {
                'Foo': {'bar': 23, 'baz': 6},
                'Blam': {'Blarg': 73}
            }
            self.cls.set_limit_overrides_from_json('/foo/bar/baz.json')
        assert m_load.mock_calls == [
            call(self.cls, '/foo/bar/baz.json')
        ]
        assert self.cls.checker.mock_calls == [
            call.set_limit_overrides({
                'Foo': {'bar': 23, 'baz': 6},
                'Blam': {'Blarg': 73}
            })
        ]


class TestSetThresholdOverridesFromJson(RunnerTester):

    def test_happy_path(self):
        mock_checker = Mock(spec_set=AwsLimitChecker)
        self.cls.checker = mock_checker
        with patch('%s.Runner.load_json' % pb, autospec=True) as m_load:
            m_load.return_value = {
                'Foo': {
                    'bar': {
                        'warning': {
                            'percent': 90,
                            'count': 10
                        },
                        'critical': {
                            'percent': 95
                        }
                    }
                }
            }
            self.cls.set_threshold_overrides_from_json('/foo/bar/baz.json')
        assert m_load.mock_calls == [
            call(self.cls, '/foo/bar/baz.json')
        ]
        assert self.cls.checker.mock_calls == [
            call.set_threshold_overrides({
                'Foo': {
                    'bar': {
                        'warning': {
                            'percent': 90,
                            'count': 10
                        },
                        'critical': {
                            'percent': 95
                        }
                    }
                }
            })
        ]


class TestShowUsage(RunnerTester):

    def test_default(self, capsys):
        limits = sample_limits()
        limits['SvcFoo']['foo limit3']._add_current_usage(33)
        limits['SvcBar']['bar limit2']._add_current_usage(22)
        limits['SvcBar']['barlimit1']._add_current_usage(11)
        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.get_limits.return_value = limits
        self.cls.checker = mock_checker
        with patch('awslimitchecker.runner.dict2cols') as mock_d2c:
            mock_d2c.return_value = 'd2cval'
            self.cls.show_usage()
        out, err = capsys.readouterr()
        assert out == 'd2cval\n'
        assert mock_checker.mock_calls == [
            call.find_usage(service=None, use_ta=True),
            call.get_limits(service=None, use_ta=True)
        ]
        assert mock_d2c.mock_calls == [
            call({
                'SvcBar/bar limit2': '22',
                'SvcBar/barlimit1': '11',
                'SvcFoo/foo limit3': '33',
            })
        ]

    def test_one_service(self, capsys):
        limits = {
            'SvcFoo': sample_limits()['SvcFoo'],
        }
        limits['SvcFoo']['foo limit3']._add_current_usage(33)
        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.get_limits.return_value = limits
        self.cls.checker = mock_checker
        self.cls.service_name = ['SvcFoo']
        self.cls.skip_ta = True
        with patch('awslimitchecker.runner.dict2cols') as mock_d2c:
            mock_d2c.return_value = 'd2cval'
            self.cls.show_usage()
        out, err = capsys.readouterr()
        assert out == 'd2cval\n'
        assert mock_checker.mock_calls == [
            call.find_usage(service=['SvcFoo'], use_ta=False),
            call.get_limits(service=['SvcFoo'], use_ta=False)
        ]
        assert mock_d2c.mock_calls == [
            call({
                'SvcFoo/foo limit3': '33',
            })
        ]


class TestCheckThresholds(RunnerTester):

    def test_ok(self, capsys):
        """no problems, return 0 and print nothing"""
        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.check_thresholds.return_value = {}
        mock_checker.get_limits.return_value = {}
        self.cls.checker = mock_checker
        with patch('awslimitchecker.runner.dict2cols') as mock_d2c:
            mock_d2c.return_value = ''
            res = self.cls.check_thresholds()
        out, err = capsys.readouterr()
        assert out == '\n'
        assert mock_checker.mock_calls == [
            call.check_thresholds(use_ta=True, service=None)
        ]
        assert res == (0, {}, '')

    def test_metrics(self, capsys):
        """no problems, return 0 and print nothing; send metrics"""
        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.check_thresholds.return_value = {}
        mock_lim1 = Mock()
        mock_lim2 = Mock()
        mock_lim3 = Mock()
        mock_checker.get_limits.return_value = {
            'S1': {
                'lim1': mock_lim1,
                'lim2': mock_lim2
            },
            'S2': {
                'lim3': mock_lim3
            }
        }
        mock_metrics = Mock()
        self.cls.checker = mock_checker
        self.cls.service_name = ['S1']
        with patch('awslimitchecker.runner.dict2cols') as mock_d2c:
            mock_d2c.return_value = ''
            res = self.cls.check_thresholds(metrics=mock_metrics)
        out, err = capsys.readouterr()
        assert out == '\n'
        assert mock_checker.mock_calls == [
            call.check_thresholds(use_ta=True, service=['S1']),
            call.get_limits()
        ]
        assert res == (0, {}, '')
        assert mock_metrics.mock_calls == [
            call.add_limit(mock_lim1),
            call.add_limit(mock_lim2)
        ]

    def test_many_problems(self):
        """lots of problems"""
        mock_limit1 = Mock(spec_set=AwsLimit)
        type(mock_limit1).name = 'limit1'
        mock_w1 = Mock(spec_set=AwsLimitUsage)
        mock_limit1.get_warnings.return_value = [mock_w1]
        mock_c1 = Mock(spec_set=AwsLimitUsage)
        mock_limit1.get_criticals.return_value = [mock_c1]

        mock_limit2 = Mock(spec_set=AwsLimit)
        type(mock_limit2).name = 'limit2'
        mock_w2 = Mock(spec_set=AwsLimitUsage)
        mock_limit2.get_warnings.return_value = [mock_w2]
        mock_limit2.get_criticals.return_value = []

        mock_limit3 = Mock(spec_set=AwsLimit)
        type(mock_limit3).name = 'limit3'
        mock_w3 = Mock(spec_set=AwsLimitUsage)
        mock_limit3.get_warnings.return_value = [mock_w3]
        mock_limit3.get_criticals.return_value = []

        mock_limit4 = Mock(spec_set=AwsLimit)
        type(mock_limit4).name = 'limit4'
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
        mock_checker.get_limits.return_value = {}

        def se_print(s, l, c, w, colorize=True):
            return ('{s}/{l}'.format(s=s, l=l.name), '')

        self.cls.checker = mock_checker
        self.cls.colorize = False
        with patch('%s.issue_string_tuple' % pb,
                   autospec=True) as mock_print:
            mock_print.side_effect = se_print
            with patch('awslimitchecker.runner.dict2cols') as mock_d2c:
                mock_d2c.return_value = 'd2cval'
                res = self.cls.check_thresholds()
        assert mock_checker.mock_calls == [
            call.check_thresholds(use_ta=True, service=None)
        ]
        assert mock_print.mock_calls == [
            call(
                'svc1', mock_limit1, [mock_c1], [mock_w1],
                colorize=False
            ),
            call(
                'svc1', mock_limit2, [], [mock_w2], colorize=False
            ),
            call(
                'svc2', mock_limit3, [], [mock_w3], colorize=False
            ),
            call(
                'svc2', mock_limit4, [mock_c2], [], colorize=False
            ),
        ]
        assert mock_d2c.mock_calls == [
            call({
                'svc1/limit1': '',
                'svc1/limit2': '',
                'svc2/limit3': '',
                'svc2/limit4': '',
            })
        ]
        assert res == (2, {
            'svc2': {
                'limit3': mock_limit3,
                'limit4': mock_limit4,
            },
            'svc1': {
                'limit1': mock_limit1,
                'limit2': mock_limit2,
            },
        }, 'd2cval')

    def test_when_skip_check(self):
        """lots of problems"""
        mock_limit1 = Mock(spec_set=AwsLimit)
        type(mock_limit1).name = 'limit1'
        mock_w1 = Mock(spec_set=AwsLimitUsage)
        mock_limit1.get_warnings.return_value = [mock_w1]
        mock_c1 = Mock(spec_set=AwsLimitUsage)
        mock_limit1.get_criticals.return_value = [mock_c1]

        mock_limit2 = Mock(spec_set=AwsLimit)
        type(mock_limit2).name = 'limit2'
        mock_w2 = Mock(spec_set=AwsLimitUsage)
        mock_limit2.get_warnings.return_value = [mock_w2]
        mock_limit2.get_criticals.return_value = []

        mock_checker = Mock(spec_set=AwsLimitChecker)
        mock_checker.check_thresholds.return_value = {
            'svc1': {
                'limit1': mock_limit1,
                'limit2': mock_limit2,
            },
        }
        mock_checker.get_limits.return_value = {}

        def se_print(s, l, c, w, colorize=True):
            return ('{s}/{l}'.format(s=s, l=l.name), '')

        self.cls.checker = mock_checker
        self.cls.skip_check = ['svc1/limit1']
        with patch('%s.issue_string_tuple' % pb,
                   autospec=True) as mock_print:
            mock_print.side_effect = se_print
            with patch('awslimitchecker.runner.dict2cols') as mock_d2c:
                mock_d2c.return_value = 'd2cval'
                res = self.cls.check_thresholds()

        assert mock_checker.mock_calls == [
            call.check_thresholds(use_ta=True, service=None)
        ]
        assert mock_print.mock_calls == [
            call(
                'svc1', mock_limit2, [], [mock_w2], colorize=True
            ),
        ]
        assert mock_d2c.mock_calls == [
            call({
                'svc1/limit2': '',
            })
        ]
        assert res == (1, {
            'svc1': {
                'limit1': mock_limit1,
                'limit2': mock_limit2,
            },
        }, 'd2cval')

    def test_warn(self):
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
        mock_checker.get_limits.return_value = {}

        self.cls.checker = mock_checker
        with patch('%s.issue_string_tuple' % pb,
                   autospec=True) as mock_print:
            mock_print.return_value = ('', '')
            with patch('awslimitchecker.runner.dict2cols') as mock_d2c:
                mock_d2c.return_value = 'd2cval'
                res = self.cls.check_thresholds()
        assert mock_checker.mock_calls == [
            call.check_thresholds(use_ta=True, service=None)
        ]
        assert mock_print.mock_calls == [
            call(
                'svc1', mock_limit1, [], [mock_w1, mock_w2],
                colorize=True
            ),
            call(
                'svc2', mock_limit2, [], [mock_w3], colorize=True
            ),
        ]
        assert res == (1, {
            'svc2': {
                'limit2': mock_limit2,
            },
            'svc1': {
                'limit1': mock_limit1,
            },
        }, 'd2cval')

    def test_warn_one_service(self):
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
        }
        mock_checker.get_limits.return_value = {}

        self.cls.checker = mock_checker
        self.cls.service_name = ['svc2']
        with patch('%s.issue_string_tuple' % pb,
                   autospec=True) as mock_print:
            mock_print.return_value = ('', '')
            with patch('awslimitchecker.runner.dict2cols') as mock_d2c:
                mock_d2c.return_value = 'd2cval'
                res = self.cls.check_thresholds()
        assert mock_checker.mock_calls == [
            call.check_thresholds(use_ta=True, service=['svc2'])
        ]
        assert mock_print.mock_calls == [
            call(
                'svc2', mock_limit2, [], [mock_w3], colorize=True
            ),
        ]
        assert res == (1, {
            'svc2': {
                'limit2': mock_limit2,
            },
        }, 'd2cval')

    def test_crit(self):
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
        mock_checker.get_limits.return_value = {}

        self.cls.checker = mock_checker
        self.cls.skip_ta = True
        with patch('%s.issue_string_tuple' % pb,
                   autospec=True) as mock_print:
            mock_print.return_value = ('', '')
            with patch('awslimitchecker.runner.dict2cols') as mock_d2c:
                mock_d2c.return_value = 'd2cval'
            res = self.cls.check_thresholds()
        assert mock_checker.mock_calls == [
            call.check_thresholds(use_ta=False, service=None)
        ]
        assert mock_print.mock_calls == [
            call(
                'svc1', mock_limit1, [mock_c1, mock_c2], [],
                colorize=True
            ),
        ]
        assert res == (2, {
            'svc1': {
                'limit1': mock_limit1,
            },
        }, '  \n')


class TestConsoleEntryPoint(RunnerTester):

    def test_version(self, capsys):
        argv = ['awslimitchecker', '-V']
        expected = 'awslimitchecker ver (see <foo> for source code)\n'
        with patch.object(sys, 'argv', argv):
            with patch('%s.AwsLimitChecker' % pb,
                       spec_set=AwsLimitChecker) as mock_alc:
                mock_alc.return_value.get_project_url.return_value = 'foo'
                mock_alc.return_value.get_version.return_value = 'ver'
                with pytest.raises(SystemExit) as excinfo:
                    self.cls.console_entry_point()
        out, err = capsys.readouterr()
        assert out == expected
        assert excinfo.value.code == 0
        assert mock_alc.mock_calls == [
            call(
                warning_threshold=80,
                critical_threshold=99,
                account_id=None,
                account_role=None,
                region=None,
                external_id=None,
                mfa_serial_number=None,
                mfa_token=None,
                profile_name=None,
                ta_refresh_mode=None,
                ta_refresh_timeout=None,
                check_version=True,
                role_partition='aws',
                ta_api_region='us-east-1',
                skip_quotas=False
            ),
            call().get_project_url(),
            call().get_version()
        ]

    def test_list_services(self):
        argv = ['awslimitchecker', '-s']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.list_services' % pb,
                       autospec=True) as mock_list:
                with pytest.raises(SystemExit) as excinfo:
                    self.cls.console_entry_point()
        assert excinfo.value.code == 0
        assert mock_list.mock_calls == [
            call(self.cls)
        ]

    def test_iam_policy(self):
        argv = ['awslimitchecker', '--iam-policy']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.iam_policy' % pb, autospec=True) as mock_iam:
                with pytest.raises(SystemExit) as excinfo:
                    self.cls.console_entry_point()
        assert excinfo.value.code == 0
        assert mock_iam.mock_calls == [
            call(self.cls)
        ]

    def test_list_defaults_skip_quotas(self):
        argv = ['awslimitchecker', '--list-defaults', '--skip-quotas']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.list_defaults' % pb,
                       autospec=True) as mock_list:
                with pytest.raises(SystemExit) as excinfo:
                    self.cls.console_entry_point()
        assert excinfo.value.code == 0
        assert mock_list.mock_calls == [
            call(self.cls)
        ]

    def test_list_limits(self):
        argv = ['awslimitchecker', '-l']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.list_limits' % pb,
                       autospec=True) as mock_list:
                with pytest.raises(SystemExit) as excinfo:
                    self.cls.console_entry_point()
        assert excinfo.value.code == 0
        assert mock_list.mock_calls == [
            call(self.cls)
        ]

    def test_skip_service_none(self):
        argv = ['awslimitchecker']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_check:
                mock_check.return_value = 2, {'Foo': {'Bar': Mock()}}, 'foo'
                with patch('%s.AwsLimitChecker' % pb, autospec=True) as mock_c:
                    with pytest.raises(SystemExit) as excinfo:
                        self.cls.console_entry_point()
        assert excinfo.value.code == 2
        assert mock_c.mock_calls == [
            call(account_id=None, account_role=None, critical_threshold=99,
                 external_id=None, mfa_serial_number=None, mfa_token=None,
                 profile_name=None, region=None, ta_refresh_mode=None,
                 ta_refresh_timeout=None, warning_threshold=80,
                 check_version=True, role_partition='aws',
                 ta_api_region='us-east-1', skip_quotas=False)
        ]

    def test_role_partition(self):
        argv = ['awslimitchecker', '--role-partition=foo']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_check:
                mock_check.return_value = 2, {'Foo': {'Bar': Mock()}}, 'foo'
                with patch('%s.AwsLimitChecker' % pb, autospec=True) as mock_c:
                    with pytest.raises(SystemExit) as excinfo:
                        self.cls.console_entry_point()
        assert excinfo.value.code == 2
        assert mock_c.mock_calls == [
            call(account_id=None, account_role=None, critical_threshold=99,
                 external_id=None, mfa_serial_number=None, mfa_token=None,
                 profile_name=None, region=None, ta_refresh_mode=None,
                 ta_refresh_timeout=None, warning_threshold=80,
                 check_version=True, role_partition='foo',
                 ta_api_region='us-east-1', skip_quotas=False)
        ]

    def test_ta_api_region_skip_quotas(self):
        argv = ['awslimitchecker', '--ta-api-region=foo', '--skip-quotas']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_check:
                mock_check.return_value = 2, {'Foo': {'Bar': Mock()}}, 'foo'
                with patch('%s.AwsLimitChecker' % pb, autospec=True) as mock_c:
                    with pytest.raises(SystemExit) as excinfo:
                        self.cls.console_entry_point()
        assert excinfo.value.code == 2
        assert mock_c.mock_calls == [
            call(account_id=None, account_role=None, critical_threshold=99,
                 external_id=None, mfa_serial_number=None, mfa_token=None,
                 profile_name=None, region=None, ta_refresh_mode=None,
                 ta_refresh_timeout=None, warning_threshold=80,
                 check_version=True, role_partition='aws',
                 ta_api_region='foo', skip_quotas=True)
        ]

    def test_skip_service(self):
        argv = ['awslimitchecker', '--skip-service=foo']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_check:
                mock_check.return_value = 2, {'Foo': {'Bar': Mock()}}, 'foo'
                with patch('%s.AwsLimitChecker' % pb, autospec=True) as mock_c:
                    with pytest.raises(SystemExit) as excinfo:
                        self.cls.console_entry_point()
        assert excinfo.value.code == 2
        assert mock_c.mock_calls == [
            call(account_id=None, account_role=None, critical_threshold=99,
                 external_id=None, mfa_serial_number=None, mfa_token=None,
                 profile_name=None, region=None, ta_refresh_mode=None,
                 ta_refresh_timeout=None, warning_threshold=80,
                 check_version=True, role_partition='aws',
                 ta_api_region='us-east-1', skip_quotas=False),
            call().remove_services(['foo'])
        ]

    def test_skip_service_multi(self):
        argv = [
            'awslimitchecker',
            '--skip-service=foo',
            '--skip-service', 'bar'
        ]
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_check:
                mock_check.return_value = 2, {'Foo': {'Bar': Mock()}}, 'foo'
                with patch('%s.AwsLimitChecker' % pb, autospec=True) as mock_c:
                    with pytest.raises(SystemExit) as excinfo:
                        self.cls.console_entry_point()
        assert excinfo.value.code == 2
        assert mock_c.mock_calls == [
            call(account_id=None, account_role=None, critical_threshold=99,
                 external_id=None, mfa_serial_number=None, mfa_token=None,
                 profile_name=None, region=None, ta_refresh_mode=None,
                 ta_refresh_timeout=None, warning_threshold=80,
                 check_version=True, role_partition='aws',
                 ta_api_region='us-east-1', skip_quotas=False),
            call().remove_services(['foo', 'bar'])
        ]

    def test_skip_check(self):
        argv = [
            'awslimitchecker',
            '--skip-check=EC2/Max launch specifications per spot fleet'
        ]
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_check:
                mock_check.return_value = 2, {'Foo': {'Bar': Mock()}}, 'foo'
                with patch('%s.AwsLimitChecker' % pb, autospec=True) as mock_c:
                    with pytest.raises(SystemExit) as excinfo:
                        self.cls.console_entry_point()
        assert excinfo.value.code == 2
        assert mock_c.mock_calls == [
            call(account_id=None, account_role=None, critical_threshold=99,
                 external_id=None, mfa_serial_number=None, mfa_token=None,
                 profile_name=None, region=None, ta_refresh_mode=None,
                 ta_refresh_timeout=None, warning_threshold=80,
                 check_version=True, role_partition='aws',
                 ta_api_region='us-east-1', skip_quotas=False),
        ]
        assert self.cls.skip_check == [
            'EC2/Max launch specifications per spot fleet',
        ]

    def test_skip_check_multi(self):
        argv = [
            'awslimitchecker',
            '--skip-check=EC2/Max launch specifications per spot fleet',
            '--skip-check', 'EC2/Running On-Demand i3.large instances',
        ]
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_check:
                mock_check.return_value = 2, {'Foo': {'Bar': Mock()}}, 'foo'
                with patch('%s.AwsLimitChecker' % pb, autospec=True) as mock_c:
                    with pytest.raises(SystemExit) as excinfo:
                        self.cls.console_entry_point()
        assert excinfo.value.code == 2
        assert mock_c.mock_calls == [
            call(account_id=None, account_role=None, critical_threshold=99,
                 external_id=None, mfa_serial_number=None, mfa_token=None,
                 profile_name=None, region=None, ta_refresh_mode=None,
                 ta_refresh_timeout=None, warning_threshold=80,
                 check_version=True, role_partition='aws',
                 ta_api_region='us-east-1', skip_quotas=False),
        ]
        assert self.cls.skip_check == [
            'EC2/Max launch specifications per spot fleet',
            'EC2/Running On-Demand i3.large instances',
        ]

    def test_limit(self):
        argv = ['awslimitchecker', '-L', 'foo=bar']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb) as mock_ct:
                with patch('%s.Runner.set_limit_overrides'
                           '' % pb, autospec=True) as mock_slo:
                    mock_ct.return_value = 0, {}, 'foo'
                    with pytest.raises(SystemExit) as excinfo:
                        self.cls.console_entry_point()
        assert excinfo.value.code == 0
        assert mock_slo.mock_calls == [
            call(self.cls, {'foo': 'bar'})
        ]

    def test_limit_multi(self):
        argv = ['awslimitchecker', '--limit=foo=bar', '--limit=baz=blam']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_ct:
                with patch('%s.Runner.set_limit_overrides'
                           '' % pb, autospec=True) as mock_slo:
                    mock_ct.return_value = 0, {}, 'foo'
                    with pytest.raises(SystemExit) as excinfo:
                        self.cls.console_entry_point()
        assert excinfo.value.code == 0
        assert mock_slo.mock_calls == [
            call(self.cls, {'foo': 'bar', 'baz': 'blam'})
        ]

    def test_limit_json(self):
        argv = [
            'awslimitchecker',
            '--limit-override-json=/path/to/file.json'
        ]
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb) as mock_ct:
                with patch(
                    '%s.Runner.set_limit_overrides_from_json' % pb,
                    autospec=True
                ) as mock_slo:
                    mock_ct.return_value = 0, {}, 'foo'
                    with pytest.raises(SystemExit) as excinfo:
                        self.cls.console_entry_point()
        assert excinfo.value.code == 0
        assert mock_slo.mock_calls == [
            call(self.cls, '/path/to/file.json')
        ]

    def test_threshold_override_json(self):
        argv = [
            'awslimitchecker',
            '--threshold-override-json=/path/to/file.json'
        ]
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb) as mock_ct:
                with patch(
                        '%s.Runner.set_threshold_overrides_from_json' % pb,
                        autospec=True
                ) as mock_tlo:
                    mock_ct.return_value = 0, {}, 'foo'
                    with pytest.raises(SystemExit) as excinfo:
                        self.cls.console_entry_point()
        assert excinfo.value.code == 0
        assert mock_tlo.mock_calls == [
            call(self.cls, '/path/to/file.json')
        ]

    def test_show_usage(self):
        argv = ['awslimitchecker', '-u']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.show_usage' % pb, autospec=True) as mock_show:
                with pytest.raises(SystemExit) as excinfo:
                    self.cls.console_entry_point()
        assert excinfo.value.code == 0
        assert mock_show.mock_calls == [
            call(self.cls)
        ]

    def test_skip_ta(self, capsys):
        argv = ['awslimitchecker', '--skip-ta']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_ct:
                with pytest.raises(SystemExit) as excinfo:
                    mock_ct.return_value = 6, {'Foo': {'Bar': Mock()}}, 'foo'
                    self.cls.console_entry_point()
        out, err = capsys.readouterr()
        assert out == ''
        assert excinfo.value.code == 6
        assert self.cls.skip_ta is True

    def test_service_name(self, capsys):
        argv = ['awslimitchecker', '-S', 'foo']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_ct:
                with pytest.raises(SystemExit) as excinfo:
                    mock_ct.return_value = 6, {'Foo': {'Bar': Mock()}}, 'foo'
                    self.cls.console_entry_point()
        out, err = capsys.readouterr()
        assert out == ''
        assert excinfo.value.code == 6
        assert self.cls.service_name == ['foo']

    def test_no_service_name(self, capsys):
        argv = ['awslimitchecker']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_ct:
                with pytest.raises(SystemExit) as excinfo:
                    mock_ct.return_value = 6, {'Foo': {'Bar': Mock()}}, 'foo'
                    self.cls.console_entry_point()
        out, err = capsys.readouterr()
        assert out == ''
        assert excinfo.value.code == 6
        assert self.cls.service_name is None

    def test_no_service_name_region(self, capsys):
        argv = ['awslimitchecker', '-r', 'myregion']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_ct:
                with patch('%s.AwsLimitChecker' % pb,
                           spec_set=AwsLimitChecker) as mock_alc:
                    with pytest.raises(SystemExit) as excinfo:
                        mock_ct.return_value = 6, {'Foo': {'Bar': Mock()}}, 'f'
                        self.cls.console_entry_point()
        out, err = capsys.readouterr()
        assert out == ''
        assert excinfo.value.code == 6
        assert mock_alc.mock_calls == [
            call(
                warning_threshold=80,
                critical_threshold=99,
                account_id=None,
                account_role=None,
                region='myregion',
                external_id=None,
                mfa_serial_number=None,
                mfa_token=None,
                profile_name=None,
                ta_refresh_mode=None,
                ta_refresh_timeout=None,
                check_version=True,
                role_partition='aws',
                ta_api_region='us-east-1',
                skip_quotas=False
            )
        ]
        assert self.cls.service_name is None

    def test_no_service_name_sts(self, capsys):
        argv = [
            'awslimitchecker',
            '-r',
            'myregion',
            '-A',
            '098765432109',
            '-R',
            'myrole'
        ]
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_ct:
                with patch('%s.AwsLimitChecker' % pb,
                           spec_set=AwsLimitChecker) as mock_alc:
                    with pytest.raises(SystemExit) as excinfo:
                        mock_ct.return_value = 6, {'Foo': {'Bar': Mock()}}, 'f'
                        self.cls.console_entry_point()
        out, err = capsys.readouterr()
        assert out == ''
        assert excinfo.value.code == 6
        assert mock_alc.mock_calls == [
            call(
                warning_threshold=80,
                critical_threshold=99,
                account_id='098765432109',
                account_role='myrole',
                region='myregion',
                external_id=None,
                mfa_serial_number=None,
                mfa_token=None,
                profile_name=None,
                ta_refresh_mode=None,
                ta_refresh_timeout=None,
                check_version=True,
                role_partition='aws',
                ta_api_region='us-east-1',
                skip_quotas=False
            )
        ]
        assert self.cls.service_name is None

    def test_no_service_name_sts_external_id(self, capsys):
        argv = [
            'awslimitchecker',
            '-r',
            'myregion',
            '-A',
            '098765432109',
            '-R',
            'myrole',
            '-E',
            'myextid',
            '--no-check-version'
        ]
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_ct:
                with patch('%s.AwsLimitChecker' % pb,
                           spec_set=AwsLimitChecker) as mock_alc:
                    with pytest.raises(SystemExit) as excinfo:
                        mock_ct.return_value = 6, {'Foo': {'Bar': Mock()}}, 'f'
                        self.cls.console_entry_point()
        out, err = capsys.readouterr()
        assert out == ''
        assert excinfo.value.code == 6
        assert mock_alc.mock_calls == [
            call(
                warning_threshold=80,
                critical_threshold=99,
                account_id='098765432109',
                account_role='myrole',
                region='myregion',
                external_id='myextid',
                mfa_serial_number=None,
                mfa_token=None,
                profile_name=None,
                ta_refresh_mode=None,
                ta_refresh_timeout=None,
                check_version=False,
                role_partition='aws',
                ta_api_region='us-east-1',
                skip_quotas=False
            )
        ]
        assert self.cls.service_name is None

    def test_verbose(self, capsys):
        argv = ['awslimitchecker', '-v']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_ct:
                with patch('awslimitchecker.runner.logger.setLevel'
                           '') as mock_set_level:
                    with pytest.raises(SystemExit) as excinfo:
                        mock_ct.return_value = 6, {'Foo': {'Bar': Mock()}}, 'f'
                        self.cls.console_entry_point()
        out, err = capsys.readouterr()
        assert out == ''
        assert excinfo.value.code == 6
        assert mock_set_level.mock_calls == [call(logging.INFO)]

    def test_debug(self, capsys):
        argv = ['awslimitchecker', '-vv']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_ct:
                with patch('awslimitchecker.runner.logger.setLevel'
                           '') as mock_set_level:
                    with pytest.raises(SystemExit) as excinfo:
                        mock_ct.return_value = 7, {'Foo': {'Bar': Mock()}}, 'f'
                        self.cls.console_entry_point()
        out, err = capsys.readouterr()
        assert out == ''
        assert excinfo.value.args[0] == 7
        assert mock_set_level.mock_calls == [call(logging.DEBUG)]

    def test_warning(self):
        argv = ['awslimitchecker', '-W', '50']
        with patch.object(sys, 'argv', argv):
            with patch('%s.AwsLimitChecker' % pb, autospec=True) as mock_alc:
                with patch('%s.Runner.check_thresholds' % pb,
                           autospec=True) as mock_ct:
                    with pytest.raises(SystemExit) as excinfo:
                        mock_ct.return_value = 8, {'Foo': {'Bar': Mock()}}, 'f'
                        self.cls.console_entry_point()
        assert excinfo.value.code == 8
        assert mock_alc.mock_calls == [
            call(
                warning_threshold=50,
                critical_threshold=99,
                account_id=None,
                account_role=None,
                region=None,
                external_id=None,
                mfa_serial_number=None,
                mfa_token=None,
                profile_name=None,
                ta_refresh_mode=None,
                ta_refresh_timeout=None,
                check_version=True,
                role_partition='aws',
                ta_api_region='us-east-1',
                skip_quotas=False
            )
        ]

    def test_warning_profile_name(self):
        argv = ['awslimitchecker', '-W', '50', '-P', 'myprof']
        with patch.object(sys, 'argv', argv):
            with patch('%s.AwsLimitChecker' % pb, autospec=True) as mock_alc:
                with patch('%s.Runner.check_thresholds' % pb,
                           autospec=True) as mock_ct:
                    with pytest.raises(SystemExit) as excinfo:
                        mock_ct.return_value = 8, {'Foo': {'Bar': Mock()}}, 'f'
                        self.cls.console_entry_point()
        assert excinfo.value.code == 8
        assert mock_alc.mock_calls == [
            call(
                warning_threshold=50,
                critical_threshold=99,
                account_id=None,
                account_role=None,
                region=None,
                external_id=None,
                mfa_serial_number=None,
                mfa_token=None,
                profile_name='myprof',
                ta_refresh_mode=None,
                ta_refresh_timeout=None,
                check_version=True,
                role_partition='aws',
                ta_api_region='us-east-1',
                skip_quotas=False
            )
        ]

    def test_critical(self):
        argv = ['awslimitchecker', '-C', '95']
        with patch.object(sys, 'argv', argv):
            with patch('%s.AwsLimitChecker' % pb, autospec=True) as mock_alc:
                with patch('%s.Runner.check_thresholds' % pb,
                           autospec=True) as mock_ct:
                    with pytest.raises(SystemExit) as excinfo:
                        mock_ct.return_value = 9, {'Foo': {'Bar': Mock()}}, 'f'
                        self.cls.console_entry_point()
        assert excinfo.value.code == 9
        assert mock_alc.mock_calls == [
            call(
                warning_threshold=80,
                critical_threshold=95,
                account_id=None,
                account_role=None,
                region=None,
                external_id=None,
                mfa_serial_number=None,
                mfa_token=None,
                profile_name=None,
                ta_refresh_mode=None,
                ta_refresh_timeout=None,
                check_version=True,
                role_partition='aws',
                ta_api_region='us-east-1',
                skip_quotas=False
            )
        ]

    def test_critical_ta_refresh(self):
        argv = ['awslimitchecker', '-C', '95', '--ta-refresh-timeout=123',
                '--ta-refresh-older=456']
        with patch.object(sys, 'argv', argv):
            with patch('%s.AwsLimitChecker' % pb, autospec=True) as mock_alc:
                with patch('%s.Runner.check_thresholds' % pb,
                           autospec=True) as mock_ct:
                    with pytest.raises(SystemExit) as excinfo:
                        mock_ct.return_value = 9, {'Foo': {}}, 'foo'
                        self.cls.console_entry_point()
        assert excinfo.value.code == 9
        assert mock_alc.mock_calls == [
            call(
                warning_threshold=80,
                critical_threshold=95,
                account_id=None,
                account_role=None,
                region=None,
                external_id=None,
                mfa_serial_number=None,
                mfa_token=None,
                profile_name=None,
                ta_refresh_mode=456,
                ta_refresh_timeout=123,
                check_version=True,
                role_partition='aws',
                ta_api_region='us-east-1',
                skip_quotas=False
            )
        ]

    def test_check_thresholds(self):
        argv = ['awslimitchecker']
        with patch.object(sys, 'argv', argv):
            with patch(
                '%s.Runner.check_thresholds' % pb, autospec=True
            ) as mock_ct:
                with pytest.raises(SystemExit) as excinfo:
                    mock_ct.return_value = 10, {}, 'foo'
                    self.cls.console_entry_point()
        assert excinfo.value.code == 10
        assert mock_ct.mock_calls == [
            call(self.cls, None)
        ]

    def test_check_thresholds_exception(self):
        argv = ['awslimitchecker']
        exc = RuntimeError()
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb) as mock_ct:
                with pytest.raises(RuntimeError) as excinfo:
                    mock_ct.side_effect = exc
                    self.cls.console_entry_point()
        assert excinfo.value == exc
        assert mock_ct.mock_calls == [
            call(None)
        ]

    @freeze_time("2016-12-16 10:40:42", tz_offset=0, auto_tick_seconds=6)
    def test_check_thresholds_exception_with_alerter(self):
        argv = [
            'awslimitchecker',
            '--alert-provider=MyAlerter',
            '--alert-config=foo=bar',
            '--alert-config=baz=blam'
        ]
        mock_alerter = Mock()
        mock_rn = PropertyMock(return_value='rname')
        exc = RuntimeError('foo')
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb) as mock_ct:
                with patch(
                    '%s.AlertProvider.get_provider_by_name' % pb
                ) as m_gpbn:
                    m_gpbn.return_value = mock_alerter
                    with pytest.raises(RuntimeError) as excinfo:
                        with patch(
                                '%s.AwsLimitChecker' % pb,
                                spec_set=AwsLimitChecker
                        ) as mock_alc:
                            type(mock_alc.return_value).region_name = mock_rn
                            mock_ct.side_effect = exc
                            self.cls.console_entry_point()
        assert excinfo.value == exc
        assert mock_ct.mock_calls == [
            call(None)
        ]
        assert m_gpbn.mock_calls == [
            call('MyAlerter'),
            call()('rname', foo='bar', baz='blam'),
            call()().on_critical(None, None, exc=exc, duration=6)
        ]

    @freeze_time("2016-12-16 10:40:42", tz_offset=0, auto_tick_seconds=6)
    def test_check_thresholds_ok_with_alerter(self):
        argv = [
            'awslimitchecker',
            '--alert-provider=MyAlerter',
            '--alert-config=foo=bar',
            '--alert-config=baz=blam'
        ]
        mock_alerter = Mock()
        mock_rn = PropertyMock(return_value='rname')
        with patch.object(sys, 'argv', argv):
            with patch(
                '%s.Runner.check_thresholds' % pb, autospec=True
            ) as mock_ct:
                with patch(
                    '%s.AlertProvider.get_provider_by_name' % pb
                ) as m_gpbn:
                    m_gpbn.return_value = mock_alerter
                    with pytest.raises(SystemExit) as excinfo:
                        with patch(
                                '%s.AwsLimitChecker' % pb,
                                spec_set=AwsLimitChecker
                        ) as mock_alc:
                            type(mock_alc.return_value).region_name = mock_rn
                            mock_ct.return_value = 0, {}, ''
                            self.cls.console_entry_point()
        assert excinfo.value.code == 0
        assert mock_ct.mock_calls == [
            call(self.cls, None)
        ]
        assert m_gpbn.mock_calls == [
            call('MyAlerter'),
            call()('rname', foo='bar', baz='blam'),
            call()().on_success(duration=12)
        ]

    @freeze_time("2016-12-16 10:40:42", tz_offset=0, auto_tick_seconds=6)
    def test_check_thresholds_warn_with_alerter(self):
        argv = [
            'awslimitchecker',
            '--alert-provider=MyAlerter',
            '--alert-config=foo=bar',
            '--alert-config=baz=blam'
        ]
        mock_alerter = Mock()
        mock_rn = PropertyMock(return_value='rname')
        with patch.object(sys, 'argv', argv):
            with patch(
                '%s.Runner.check_thresholds' % pb, autospec=True
            ) as mock_ct:
                with patch(
                    '%s.AlertProvider.get_provider_by_name' % pb
                ) as m_gpbn:
                    m_gpbn.return_value = mock_alerter
                    with pytest.raises(SystemExit) as excinfo:
                        with patch(
                                '%s.AwsLimitChecker' % pb,
                                spec_set=AwsLimitChecker
                        ) as mock_alc:
                            type(mock_alc.return_value).region_name = mock_rn
                            mock_ct.return_value = 1, {'Foo': 'bar'}, 'FooBar'
                            self.cls.console_entry_point()
        assert excinfo.value.code == 0
        assert mock_ct.mock_calls == [
            call(self.cls, None)
        ]
        assert m_gpbn.mock_calls == [
            call('MyAlerter'),
            call()('rname', foo='bar', baz='blam'),
            call()().on_warning({'Foo': 'bar'}, 'FooBar', duration=12)
        ]

    @freeze_time("2016-12-16 10:40:42", tz_offset=0, auto_tick_seconds=6)
    def test_check_thresholds_crit_with_alerter(self):
        argv = [
            'awslimitchecker',
            '--alert-provider=MyAlerter',
            '--alert-config=foo=bar',
            '--alert-config=baz=blam'
        ]
        mock_alerter = Mock()
        mock_rn = PropertyMock(return_value='rname')
        with patch.object(sys, 'argv', argv):
            with patch(
                '%s.Runner.check_thresholds' % pb, autospec=True
            ) as mock_ct:
                with patch(
                    '%s.AlertProvider.get_provider_by_name' % pb
                ) as m_gpbn:
                    m_gpbn.return_value = mock_alerter
                    with pytest.raises(SystemExit) as excinfo:
                        with patch(
                                '%s.AwsLimitChecker' % pb,
                                spec_set=AwsLimitChecker
                        ) as mock_alc:
                            type(mock_alc.return_value).region_name = mock_rn
                            mock_ct.return_value = 2, {'Foo': 'bar'}, 'FooBar'
                            self.cls.console_entry_point()
        assert excinfo.value.code == 0
        assert mock_ct.mock_calls == [
            call(self.cls, None)
        ]
        assert m_gpbn.mock_calls == [
            call('MyAlerter'),
            call()('rname', foo='bar', baz='blam'),
            call()().on_critical({'Foo': 'bar'}, 'FooBar', duration=12)
        ]

    @freeze_time("2016-12-16 10:40:42", tz_offset=0, auto_tick_seconds=6)
    def test_check_thresholds_with_metrics(self):
        argv = [
            'awslimitchecker',
            '--metrics-provider=FooProvider',
            '--metrics-config=foo=bar',
            '--metrics-config=baz=blam'
        ]
        mock_prov = Mock()
        mock_rn = PropertyMock(return_value='rname')
        with patch.object(sys, 'argv', argv):
            with patch(
                '%s.Runner.check_thresholds' % pb, autospec=True
            ) as mock_ct:
                with patch(
                    '%s.MetricsProvider.get_provider_by_name' % pb
                ) as m_gpbn:
                    m_gpbn.return_value = mock_prov
                    with patch(
                        '%s.AwsLimitChecker' % pb, spec_set=AwsLimitChecker
                    ) as mock_alc:
                        type(mock_alc.return_value).region_name = mock_rn
                        with pytest.raises(SystemExit) as excinfo:
                            mock_ct.return_value = 10, {}, 'foo'
                            self.cls.console_entry_point()
        assert excinfo.value.code == 10
        assert mock_ct.mock_calls == [
            call(self.cls, mock_prov.return_value)
        ]
        assert mock_prov.mock_calls == [
            call('rname', foo='bar', baz='blam'),
            call().set_run_duration(6),
            call().flush()
        ]

    def test_list_metrics_providers(self, capsys):
        argv = ['awslimitchecker', '--list-metrics-providers']
        with patch.object(sys, 'argv', argv):
            with patch(
                '%s.MetricsProvider.providers_by_name' % pb,
            ) as mock_list:
                mock_list.return_value = {
                    'Prov2': None,
                    'Prov1': None
                }
                with pytest.raises(SystemExit) as excinfo:
                    self.cls.console_entry_point()
        assert excinfo.value.code == 0
        assert mock_list.mock_calls == [
            call()
        ]
        out, err = capsys.readouterr()
        assert out == 'Available metrics providers:\nProv1\nProv2\n'

    def test_list_alert_providers(self, capsys):
        argv = ['awslimitchecker', '--list-alert-providers']
        with patch.object(sys, 'argv', argv):
            with patch(
                '%s.AlertProvider.providers_by_name' % pb,
            ) as mock_list:
                mock_list.return_value = {
                    'Prov2': None,
                    'Prov1': None
                }
                with pytest.raises(SystemExit) as excinfo:
                    self.cls.console_entry_point()
        assert excinfo.value.code == 0
        assert mock_list.mock_calls == [
            call()
        ]
        out, err = capsys.readouterr()
        assert out == 'Available alert providers:\nProv1\nProv2\n'

    def test_no_color(self):
        assert self.cls.colorize is True
        argv = ['awslimitchecker', '--no-color']
        with patch.object(sys, 'argv', argv):
            with patch('%s.Runner.check_thresholds' % pb,
                       autospec=True) as mock_ct:
                mock_ct.return_value = 0, {}, 'foo'
                with patch(
                    'awslimitchecker.utils.color_output'
                ) as m_co:
                    m_co.return_value = 'COLORIZED'
                    with pytest.raises(SystemExit):
                        self.cls.console_entry_point()
        assert self.cls.colorize is False
