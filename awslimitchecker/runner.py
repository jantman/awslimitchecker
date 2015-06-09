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
bugs please submit them at <https://github.com/jantman/pydnstest> or
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

from .version import _get_version, _get_project_url
from .checker import AwsLimitChecker

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger()


def parse_args(argv):
    """
    parse arguments/options

    :param argv: argument list to parse, usually ``sys.argv[1:]``
    :type argv: list
    :returns: parsed arguments
    :rtype: :py:class:`argparse.Namespace`
    """
    desc = 'Report on AWS service limits and usage via boto, optionally warn ' \
           'about any services with usage nearing or exceeding their limits.'

    """
    ####### IMPORTANT license notice ##########
    In order to remain in compliance with the AGPLv3 license:
    - this notice MUST NOT be removed, and MUST be displayed to all users
    - _get_project_url() MUST point to the source code of the ACTUALLY RUNNING
      version of this program. i.e. if you modify this program, you MUST have
      the actually-running source available somewhere for your users.
    ####### IMPORTANT license notice ##########
    """
    epilog = 'awslimitchecker is AGPLv3-licensed Free Software. Anyone using' \
             ' this program, even remotely over a network, is entitled to a ' \
             'copy of the source code. You can obtain the source code of ' \
             'awslimitchecker ' + _get_version() + ' from: <' \
             + _get_project_url() + '>'
    p = argparse.ArgumentParser(description=desc, epilog=epilog)
    p.add_argument('-s', '--list-services', action='store_true', default=False,
                   help='print a list of all AWS service types that '
                   'awslimitchecker knows how to check')
    p.add_argument('-l', '--list-defaults', action='store_true', default=False,
                   help='print all AWS default limits in "service_name/'
                   'limit_name" format')
    p.add_argument('-u', '--show-usage', action='store_true', default=False,
                   help='find and print the current usage of all AWS services'
                   ' with known limits')
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
    p.add_argument('-v', '--verbose', dest='verbose', action='count',
                   default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-V', '--version', dest='version', action='store_true',
                   default=False,
                   help='print version number and exit.')
    args = p.parse_args(argv)
    return args


def list_services(checker):
    for x in sorted(checker.get_service_names()):
        print(x)


def list_limits(checker):
    limits = checker.get_limits()
    for svc in sorted(limits.keys()):
        for lim in sorted(limits[svc].keys()):
            print("{s}/{l}\t{n}".format(
                s=svc,
                l=lim,
                n=limits[svc][lim].default_limit
            ))


def iam_policy(checker):
    policy = checker.get_required_iam_policy()
    print(json.dumps(policy, sort_keys=True, indent=2))


def show_usage(checker):
    checker.find_usage()
    limits = checker.get_limits()
    for svc in sorted(limits.keys()):
        for lim in sorted(limits[svc].keys()):
            print("{s}/{l}\t{n}".format(
                s=svc,
                l=lim,
                n=limits[svc][lim].get_current_usage_str()
            ))


def print_issue(service_name, limit, crits, warns):
    """
    :param service_name: the name of the service
    :type service_name: str
    :param limit: the Limit this relates to
    :type limit: :py:class:`~.AwsLimit`
    :param crits: the specific usage values that crossed the critical threshold
    :type usage: :py:obj:`list` of :py:class:`~.AwsLimitUsage`
    :param crits: the specific usage values that crossed the warning threshold
    :type usage: :py:obj:`list` of :py:class:`~.AwsLimitUsage`
    """
    usage_str = ''
    if len(crits) > 0:
        usage_str += 'CRITICAL: '
        usage_str += ', '.join([str(x) for x in sorted(crits)])
    if len(warns) > 0:
        usage_str += 'WARNING: '
        usage_str += ', '.join([str(x) for x in sorted(warns)])
    s = "{s}/{l} (limit {v}) {u}".format(
        s=service_name,
        l=limit.name,
        v=limit.get_limit(),
        u=usage_str,
    )
    return s


def check_thresholds(checker):
    have_warn = False
    have_crit = False
    problems = checker.check_thresholds()
    for svc in sorted(problems.keys()):
        for lim_name in sorted(problems[svc].keys()):
            limit = problems[svc][lim_name]
            warns = limit.get_warnings()
            crits = limit.get_criticals()
            if len(crits) > 0:
                have_crit = True
            if len(warns) > 0:
                have_warn = True
            print(print_issue(svc, limit, crits, warns))
    # might as well use the Nagios exit codes,
    # even though our output doesn't work for that
    if have_crit:
        return 2
    if have_warn:
        return 1
    return 0


def console_entry_point():
    args = parse_args(sys.argv[1:])
    if args.verbose == 1:
        logger.setLevel(logging.INFO)
    elif args.verbose > 1:
        logger.setLevel(logging.DEBUG)

    if args.version:
        print('awslimitchecker {v} (see <{s}> for source code)'.format(
            s=_get_project_url(),
            v=_get_version()
        ))
        raise SystemExit(0)

    # the rest of these actually use the checker
    checker = AwsLimitChecker(
        warning_threshold=args.warning_threshold,
        critical_threshold=args.critical_threshold
    )
    if args.list_services:
        list_services(checker)
        raise SystemExit(0)

    if args.list_defaults:
        list_limits(checker)
        raise SystemExit(0)

    if args.iam_policy:
        iam_policy(checker)
        raise SystemExit(0)

    if args.show_usage:
        show_usage(checker)
        raise SystemExit(0)

    # else check
    res = check_thresholds(checker)
    raise SystemExit(res)

if __name__ == "__main__":
    console_entry_point()
