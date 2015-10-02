"""
awslimitchecker/runner.py

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

import sys
import argparse
import logging
import json
import termcolor

from .checker import AwsLimitChecker
from .utils import StoreKeyValuePair, dict2cols
from .limit import SOURCE_TA

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger()

# suppress boto internal logging below WARNING level
boto_log = logging.getLogger("boto")
boto_log.setLevel(logging.WARNING)
boto_log.propagate = True


class Runner(object):

    def __init__(self):
        self.colorize = True
        self.checker = None
        self.skip_ta = False
        self.service_name = None

    def parse_args(self, argv):
        """
        parse arguments/options

        :param argv: argument list to parse, usually ``sys.argv[1:]``
        :type argv: list
        :returns: parsed arguments
        :rtype: :py:class:`argparse.Namespace`
        """
        desc = 'Report on AWS service limits and usage via boto, optionally ' \
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
        p.add_argument('-S', '--service', action='store', default=None,
                       help='perform action for only the specified service name'
                            '; see -s|--list-services for valid names')
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
        p.add_argument('-r', '--region', action='store',
                       type=str, default=None,
                       help='AWS region name to connect to; required for STS')
        p.add_argument('--skip-ta', action='store_true', default=False,
                       help='do not attempt to pull *any* information on limits'
                       ' from Trusted Advisor')
        p.add_argument('--no-color', action='store_true', default=False,
                       help='do not colorize output')
        p.add_argument('-v', '--verbose', dest='verbose', action='count',
                       default=0,
                       help='verbose output. specify twice for debug-level '
                       'output.')
        p.add_argument('-V', '--version', dest='version', action='store_true',
                       default=False,
                       help='print version number and exit.')
        args = p.parse_args(argv)
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
                ta_str = ''
                if limits[svc][lim].get_limit_source() == SOURCE_TA:
                    ta_str = ' (TA)'
                data["{s}/{l}".format(s=svc, l=lim)] = '{v}{t}'.format(
                    v=limits[svc][lim].get_limit(),
                    t=ta_str)
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
        self.checker.find_usage(service=self.service_name)
        limits = self.checker.get_limits(service=self.service_name)
        data = {}
        for svc in sorted(limits.keys()):
            for lim in sorted(limits[svc].keys()):
                data["{s}/{l}".format(s=svc, l=lim)] = '{v}'.format(
                    v=limits[svc][lim].get_current_usage_str())
        print(dict2cols(data))

    def color_output(self, s, color):
        if not self.colorize:
            return s
        return termcolor.colored(s, color)

    def print_issue(self, service_name, limit, crits, warns):
        """
        :param service_name: the name of the service
        :type service_name: str
        :param limit: the Limit this relates to
        :type limit: :py:class:`~.AwsLimit`
        :param crits: the specific usage values that crossed the critical
          threshold
        :type usage: :py:obj:`list` of :py:class:`~.AwsLimitUsage`
        :param crits: the specific usage values that crossed the warning
          threshold
        :type usage: :py:obj:`list` of :py:class:`~.AwsLimitUsage`
        """
        usage_str = ''
        if len(crits) > 0:
            tmp = 'CRITICAL: '
            tmp += ', '.join([str(x) for x in sorted(crits)])
            usage_str += self.color_output(tmp, 'red')
        if len(warns) > 0:
            if len(crits) > 0:
                usage_str += ' '
            tmp = 'WARNING: '
            tmp += ', '.join([str(x) for x in sorted(warns)])
            usage_str += self.color_output(tmp, 'yellow')
        k = "{s}/{l}".format(
            s=service_name,
            l=limit.name,
        )
        v = "(limit {v}) {u}".format(
            v=limit.get_limit(),
            u=usage_str,
        )
        return (k, v)

    def check_thresholds(self):
        have_warn = False
        have_crit = False
        problems = self.checker.check_thresholds(
            use_ta=(not self.skip_ta),
            service=self.service_name)
        columns = {}
        for svc in sorted(problems.keys()):
            for lim_name in sorted(problems[svc].keys()):
                limit = problems[svc][lim_name]
                warns = limit.get_warnings()
                crits = limit.get_criticals()
                if len(crits) > 0:
                    have_crit = True
                if len(warns) > 0:
                    have_warn = True
                k, v = self.print_issue(svc, limit, crits, warns)
                columns[k] = v
        print(dict2cols(columns))
        # might as well use the Nagios exit codes,
        # even though our output doesn't work for that
        if have_crit:
            return 2
        if have_warn:
            return 1
        return 0

    def set_limit_overrides(self, overrides):
        for key in sorted(overrides.keys()):
            if key.count('/') != 1:
                raise ValueError("Limit names must be in 'service/limit' "
                                 "format; {k} is invalid.".format(k=key))
            svc, limit = key.split('/')
            self.checker.set_limit_override(svc, limit, int(overrides[key]))

    def console_entry_point(self):
        args = self.parse_args(sys.argv[1:])
        self.service_name = args.service
        if args.verbose == 1:
            logger.setLevel(logging.INFO)
        elif args.verbose > 1:
            # debug-level logging hacks
            FORMAT = "[%(levelname)s %(filename)s:%(lineno)s - " \
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
            account_id=args.sts_account_id,
            account_role=args.sts_account_role,
            region=args.region,
            external_id=args.external_id
        )

        if args.version:
            print('awslimitchecker {v} (see <{s}> for source code)'.format(
                s=self.checker.get_project_url(),
                v=self.checker.get_version()
            ))
            raise SystemExit(0)

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

        # else check
        res = self.check_thresholds()
        raise SystemExit(res)


def console_entry_point():
    r = Runner()
    r.console_entry_point()


if __name__ == "__main__":
    console_entry_point()
