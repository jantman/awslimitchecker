"""
awslimitchecker/runner.py

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

import sys
import argparse
import logging
import json
import boto3
import time

from .checker import AwsLimitChecker
from .utils import StoreKeyValuePair, dict2cols, issue_string_tuple
from .limit import SOURCE_TA, SOURCE_API, SOURCE_QUOTAS
from .metrics import MetricsProvider
from .alerts import AlertProvider

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger()

# suppress boto3 internal logging below WARNING level
boto3_log = logging.getLogger("boto3")
boto3_log.setLevel(logging.WARNING)
boto3_log.propagate = True

# suppress botocore internal logging below WARNING level
botocore_log = logging.getLogger("botocore")
botocore_log.setLevel(logging.WARNING)
botocore_log.propagate = True


class Runner(object):

    def __init__(self):
        self.colorize = True
        self.checker = None
        self.skip_ta = False
        self.service_name = None
        self.skip_check = []

    def parse_args(self, argv):
        """
        parse arguments/options

        :param argv: argument list to parse, usually ``sys.argv[1:]``
        :type argv: list
        :returns: parsed arguments
        :rtype: :py:class:`argparse.Namespace`
        """
        desc = 'Report on AWS service limits and usage via boto3, optionally ' \
               'warn about any services with usage nearing or exceeding their' \
               ' limits. For further help, see ' \
               '<http://awslimitchecker.readthedocs.org/>'
        # ###### IMPORTANT license notice ##########
        # Pursuant to Sections 5(b) and 13 of the GNU Affero General Public
        # License, version 3, this notice MUST NOT be removed, and MUST be
        # displayed to ALL USERS of this software, even if they interact with
        # it remotely over a network.
        #
        # See the "Development" section of the awslimitchecker documentation
        # (docs/source/development.rst or
        # <http://awslimitchecker.readthedocs.org/en/latest/development.html> )
        # for further information.
        # ###### IMPORTANT license notice ##########
        epilog = 'awslimitchecker is AGPLv3-licensed Free Software. Anyone ' \
                 'using this program, even remotely over a network, is ' \
                 'entitled to a copy of the source code. Use `--version` for ' \
                 'information on the source code location.'
        p = argparse.ArgumentParser(description=desc, epilog=epilog)
        p.add_argument('-S', '--service', action='store', nargs='*',
                       help='perform action for only the specified service name'
                            '; see -s|--list-services for valid names')
        p.add_argument('--skip-service', action='append', default=[],
                       dest='skip_service',
                       help='avoid performing actions for the specified service'
                            ' name; see -s|--list-services for valid names')
        p.add_argument('--skip-check', action='append', default=[],
                       dest='skip_check',
                       help='avoid performing actions for the specified check'
                            ' name')
        p.add_argument('-s', '--list-services', action='store_true',
                       default=False,
                       help='print a list of all AWS service types that '
                            'awslimitchecker knows how to check')
        p.add_argument('-l', '--list-limits', action='store_true',
                       default=False,
                       help='print all AWS effective limits in "service_name/'
                       'limit_name" format')
        p.add_argument('--list-defaults', action='store_true', default=False,
                       help='print all AWS default limits in "service_name/'
                       'limit_name" format')
        p.add_argument('-L', '--limit', action=StoreKeyValuePair,
                       help='override a single AWS limit, specified in '
                       '"service_name/limit_name=value" format; can be '
                       'specified multiple times.')
        p.add_argument('--limit-override-json', action='store', type=str,
                       default=None,
                       help='Absolute or relative path, or s3:// URL, to a '
                            'JSON file specifying limit overrides. See docs '
                            'for expected format.')
        p.add_argument('--threshold-override-json', action='store', type=str,
                       default=None,
                       help='Absolute or relative path, or s3:// URL, to a '
                            'JSON file specifying threshold overrides. See '
                            'docs for expected format.')
        p.add_argument('-u', '--show-usage', action='store_true',
                       default=False,
                       help='find and print the current usage of all AWS '
                       'services with known limits')
        p.add_argument('--iam-policy', action='store_true',
                       default=False,
                       help='output a JSON serialized IAM Policy '
                       'listing the required permissions for '
                       'awslimitchecker to run correctly.')
        p.add_argument('-W', '--warning-threshold', action='store',
                       type=int, default=80,
                       help='default warning threshold (percentage of '
                       'limit); default: 80')
        p.add_argument('-C', '--critical-threshold', action='store',
                       type=int, default=99,
                       help='default critical threshold (percentage of '
                       'limit); default: 99')
        p.add_argument('-P', '--profile', action='store', dest='profile_name',
                       type=str, default=None,
                       help='Name of profile in the AWS cross-sdk credentials '
                            'file to use credentials from; similar to the '
                            'corresponding awscli option')
        p.add_argument('-A', '--sts-account-id', action='store',
                       type=str, default=None,
                       help='for use with STS, the Account ID of the '
                       'destination account (account to assume a role in)')
        p.add_argument('-R', '--sts-account-role', action='store',
                       type=str, default=None,
                       help='for use with STS, the name of the IAM role to '
                       'assume')
        p.add_argument('-E', '--external-id', action='store', type=str,
                       default=None, help='External ID to use when assuming '
                       'a role via STS')
        p.add_argument('-M', '--mfa-serial-number', action='store', type=str,
                       default=None, help='MFA Serial Number to use when '
                       'assuming a role via STS')
        p.add_argument('-T', '--mfa-token', action='store', type=str,
                       default=None, help='MFA Token to use when assuming '
                       'a role via STS')
        p.add_argument('-r', '--region', action='store',
                       type=str, default=None,
                       help='AWS region name to connect to; required for STS')
        p.add_argument('--role-partition', action='store', type=str,
                       default='aws',
                       help='AWS partition name to use for account_role when '
                            'connecting via STS; see documentation for more '
                            'information (default: "aws")')
        p.add_argument('--ta-api-region', action='store', type=str,
                       default='us-east-1',
                       help='Region to use for Trusted Advisor / Support API'
                            ' (default: us-east-1)')
        p.add_argument('--skip-ta', action='store_true', default=False,
                       help='do not attempt to pull *any* information on limits'
                       ' from Trusted Advisor')
        p.add_argument('--skip-quotas', action='store_true', default=False,
                       help='Do not attempt to connect to Service Quotas '
                            'service or use its data for current limits')
        g = p.add_mutually_exclusive_group()
        g.add_argument('--ta-refresh-wait', dest='ta_refresh_wait',
                       action='store_true', default=False,
                       help='If applicable, refresh all Trusted Advisor '
                            'limit-related checks, and wait for the refresh to'
                            ' complete before continuing.')
        g.add_argument('--ta-refresh-trigger', dest='ta_refresh_trigger',
                       action='store_true', default=False,
                       help='If applicable, trigger refreshes for all Trusted '
                            'Advisor limit-related checks, but do not wait for '
                            'them to finish refreshing; trigger the refresh '
                            'and continue on (useful to ensure checks are '
                            'refreshed before the next scheduled run).')
        g.add_argument('--ta-refresh-older', dest='ta_refresh_older',
                       action='store', type=int, default=None,
                       help='If applicable, trigger refreshes for all Trusted '
                            'Advisor limit-related checks with results more '
                            'than this number of seconds old. Wait for the '
                            'refresh to complete before continuing.')
        p.add_argument('--ta-refresh-timeout', dest='ta_refresh_timeout',
                       type=int, action='store', default=None,
                       help='If waiting for TA checks to refresh, wait up to '
                            'this number of seconds before continuing on '
                            'anyway.')
        p.add_argument('--no-color', action='store_true', default=False,
                       help='do not colorize output')
        p.add_argument('--no-check-version', action='store_false', default=True,
                       dest='check_version',
                       help='do not check latest version at startup')
        p.add_argument('-v', '--verbose', dest='verbose', action='count',
                       default=0,
                       help='verbose output. specify twice for debug-level '
                       'output.')
        p.add_argument('-V', '--version', dest='version', action='store_true',
                       default=False,
                       help='print version number and exit.')
        p.add_argument('--list-metrics-providers',
                       dest='list_metrics_providers',
                       action='store_true', default=False,
                       help='List available metrics providers and exit')
        p.add_argument('--metrics-provider', dest='metrics_provider', type=str,
                       action='store', default=None,
                       help='Metrics provider class name, to enable sending '
                            'metrics')
        p.add_argument('--metrics-config', action=StoreKeyValuePair,
                       dest='metrics_config',
                       help='Specify key/value parameters for the metrics '
                            'provider constructor. See documentation for '
                            'further information.')
        p.add_argument('--list-alert-providers',
                       dest='list_alert_providers',
                       action='store_true', default=False,
                       help='List available alert providers and exit')
        p.add_argument('--alert-provider', dest='alert_provider', type=str,
                       action='store', default=None,
                       help='Alert provider class name, to enable sending '
                            'notifications')
        p.add_argument('--alert-config', action=StoreKeyValuePair,
                       dest='alert_config',
                       help='Specify key/value parameters for the alert '
                            'provider constructor. See documentation for '
                            'further information.')
        args = p.parse_args(argv)
        args.ta_refresh_mode = None
        if args.ta_refresh_wait:
            args.ta_refresh_mode = 'wait'
        elif args.ta_refresh_trigger:
            args.ta_refresh_mode = 'trigger'
        elif args.ta_refresh_older is not None:
            args.ta_refresh_mode = args.ta_refresh_older
        return args

    def list_services(self):
        for x in sorted(self.checker.get_service_names()):
            print(x)

    def list_limits(self):
        limits = self.checker.get_limits(
            use_ta=(not self.skip_ta),
            service=self.service_name)
        data = {}
        for svc in sorted(limits.keys()):
            for lim in sorted(limits[svc].keys()):
                src_str = ''
                if limits[svc][lim].get_limit_source() == SOURCE_API:
                    src_str = ' (API)'
                if limits[svc][lim].get_limit_source() == SOURCE_TA:
                    src_str = ' (TA)'
                if limits[svc][lim].get_limit_source() == SOURCE_QUOTAS:
                    src_str = ' (Quotas)'
                if limits[svc][lim].has_resource_limits():
                    for usage in limits[svc][lim].get_current_usage():
                        id = "{s}/{l}/{r}".format(s=svc, l=lim,
                                                  r=usage.resource_id)
                        data[id] = '{v} (API)'.format(v=usage.get_maximum())
                else:
                    data["{s}/{l}".format(s=svc, l=lim)] = '{v}{t}'.format(
                        v=limits[svc][lim].get_limit(),
                        t=src_str)
        print(dict2cols(data))

    def list_defaults(self):
        limits = self.checker.get_limits(service=self.service_name)
        data = {}
        for svc in sorted(limits.keys()):
            for lim in sorted(limits[svc].keys()):
                data["{s}/{l}".format(s=svc, l=lim)] = '{v}'.format(
                    v=limits[svc][lim].default_limit)
        print(dict2cols(data))

    def iam_policy(self):
        policy = self.checker.get_required_iam_policy()
        print(json.dumps(policy, sort_keys=True, indent=2))

    def show_usage(self):
        self.checker.find_usage(
            service=self.service_name, use_ta=(not self.skip_ta))
        limits = self.checker.get_limits(
            service=self.service_name, use_ta=(not self.skip_ta))
        data = {}
        for svc in sorted(limits.keys()):
            for lim in sorted(limits[svc].keys()):
                data["{s}/{l}".format(s=svc, l=lim)] = '{v}'.format(
                    v=limits[svc][lim].get_current_usage_str())
        print(dict2cols(data))

    def check_thresholds(self, metrics=None):
        have_warn = False
        have_crit = False
        problems = self.checker.check_thresholds(
            use_ta=(not self.skip_ta),
            service=self.service_name
        )
        if metrics:
            for svc, svc_limits in sorted(self.checker.get_limits().items()):
                if self.service_name and svc not in self.service_name:
                    continue
                for _, limit in sorted(svc_limits.items()):
                    metrics.add_limit(limit)
        columns = {}
        for svc in sorted(problems.keys()):
            for lim_name in sorted(problems[svc].keys()):
                check_name = "{svc}/{limit}".format(
                    svc=svc,
                    limit=lim_name,
                )
                if check_name in self.skip_check:
                    continue
                limit = problems[svc][lim_name]
                warns = limit.get_warnings()
                crits = limit.get_criticals()
                if len(crits) > 0:
                    have_crit = True
                if len(warns) > 0:
                    have_warn = True
                k, v = issue_string_tuple(
                    svc, limit, crits, warns, colorize=self.colorize
                )
                columns[k] = v
        d2c = dict2cols(columns)
        print(d2c)
        # might as well use the Nagios exit codes,
        # even though our output doesn't work for that
        if have_crit:
            return 2, problems, d2c
        if have_warn:
            return 1, problems, d2c
        return 0, problems, d2c

    def set_limit_overrides(self, overrides):
        for key in sorted(overrides.keys()):
            if key.count('/') != 1:
                raise ValueError("Limit names must be in 'service/limit' "
                                 "format; {k} is invalid.".format(k=key))
            svc, limit = key.split('/')
            self.checker.set_limit_override(svc, limit, int(overrides[key]))

    def load_json(self, path):
        """Load JSON from either a local file or S3"""
        if path.startswith('s3://'):
            parsed = urlparse(path)
            s3key = parsed.path.lstrip('/')
            logger.debug(
                'Reading JSON from S3 bucket "%s" key "%s"',
                parsed.netloc, s3key
            )
            client = boto3.client('s3')
            resp = client.get_object(Bucket=parsed.netloc, Key=s3key)
            data = resp['Body'].read()
        else:
            logger.debug('Reading JSON from: %s', path)
            with open(path, 'r') as fh:
                data = fh.read()
        if isinstance(data, type(b'')):
            data = data.decode()
        return json.loads(data)

    def set_limit_overrides_from_json(self, path):
        j = self.load_json(path)
        logger.debug('Limit overrides: %s', j)
        self.checker.set_limit_overrides(j)
        logger.debug('Done setting limit overrides from JSON.')

    def set_threshold_overrides_from_json(self, path):
        j = self.load_json(path)
        logger.debug('Threshold overrides: %s', j)
        self.checker.set_threshold_overrides(j)
        logger.debug('Done setting threshold overrides from JSON.')

    def console_entry_point(self):
        args = self.parse_args(sys.argv[1:])
        self.service_name = args.service
        if args.verbose == 1:
            logger.setLevel(logging.INFO)
        elif args.verbose > 1:
            # debug-level logging hacks
            FORMAT = "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - " \
                     "%(name)s.%(funcName)s() ] %(message)s"
            debug_formatter = logging.Formatter(fmt=FORMAT)
            logger.handlers[0].setFormatter(debug_formatter)
            logger.setLevel(logging.DEBUG)

        if args.no_color:
            self.colorize = False

        if args.skip_ta:
            self.skip_ta = True

        # the rest of these actually use the checker
        self.checker = AwsLimitChecker(
            warning_threshold=args.warning_threshold,
            critical_threshold=args.critical_threshold,
            profile_name=args.profile_name,
            account_id=args.sts_account_id,
            account_role=args.sts_account_role,
            region=args.region,
            external_id=args.external_id,
            mfa_serial_number=args.mfa_serial_number,
            mfa_token=args.mfa_token,
            ta_refresh_mode=args.ta_refresh_mode,
            ta_refresh_timeout=args.ta_refresh_timeout,
            check_version=args.check_version,
            role_partition=args.role_partition,
            ta_api_region=args.ta_api_region,
            skip_quotas=args.skip_quotas
        )

        if args.version:
            print('awslimitchecker {v} (see <{s}> for source code)'.format(
                s=self.checker.get_project_url(),
                v=self.checker.get_version()
            ))
            raise SystemExit(0)

        if len(args.skip_service) > 0:
            self.checker.remove_services(args.skip_service)

        if len(args.skip_check) > 0:
            for check in args.skip_check:
                self.skip_check.append(check)

        if args.limit_override_json is not None:
            self.set_limit_overrides_from_json(args.limit_override_json)

        if args.threshold_override_json is not None:
            self.set_threshold_overrides_from_json(
                args.threshold_override_json
            )

        if len(args.limit) > 0:
            self.set_limit_overrides(args.limit)

        if args.list_services:
            self.list_services()
            raise SystemExit(0)

        if args.list_defaults:
            self.list_defaults()
            raise SystemExit(0)

        if args.list_limits:
            self.list_limits()
            raise SystemExit(0)

        if args.iam_policy:
            self.iam_policy()
            raise SystemExit(0)

        if args.show_usage:
            self.show_usage()
            raise SystemExit(0)

        if args.list_metrics_providers:
            print('Available metrics providers:')
            for p in sorted(MetricsProvider.providers_by_name().keys()):
                print(p)
            raise SystemExit(0)

        if args.list_alert_providers:
            print('Available alert providers:')
            for p in sorted(AlertProvider.providers_by_name().keys()):
                print(p)
            raise SystemExit(0)

        # else check
        alerter = None
        if args.alert_provider:
            alerter = AlertProvider.get_provider_by_name(
                args.alert_provider
            )(self.checker.region_name, **args.alert_config)
        start_time = time.time()
        try:
            metrics = None
            if args.metrics_provider:
                metrics = MetricsProvider.get_provider_by_name(
                    args.metrics_provider
                )(self.checker.region_name, **args.metrics_config)
            res, problems, problem_str = self.check_thresholds(metrics)
            duration = time.time() - start_time
            logger.info('Finished checking limits in %s seconds', duration)
            if metrics:
                metrics.set_run_duration(duration)
                metrics.flush()
        except Exception as ex:
            if alerter:
                alerter.on_critical(
                    None, None, exc=ex, duration=time.time() - start_time
                )
            raise
        if alerter:
            if res == 2:
                alerter.on_critical(
                    problems, problem_str, duration=time.time() - start_time
                )
            elif res == 1:
                alerter.on_warning(
                    problems, problem_str, duration=time.time() - start_time
                )
            else:
                alerter.on_success(duration=time.time() - start_time)
            # with alert provider, always exit zero
            raise SystemExit(0)
        raise SystemExit(res)


def console_entry_point():
    r = Runner()
    r.console_entry_point()


if __name__ == "__main__":
    console_entry_point()
