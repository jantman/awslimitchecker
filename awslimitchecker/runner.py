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

from .version import get_version, get_project_url
from .checker import AwsLimitChecker


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
    - get_project_url() MUST point to the source code of the ACTUALLY RUNNING
      version of this program. i.e. if you modify this program, you MUST have
      the actually-running source available somewhere for your users.
    ####### IMPORTANT license notice ##########
    """
    epilog = 'awslimitchecker is AGPLv3-licensed Free Software. Anyone using' \
             ' this program, even remotely over a network, is entitled to a ' \
             'copy of the source code. You can obtain the source code of ' \
             'awslimitchecker ' + get_version() + ' from: <' \
             + get_project_url() + '>'
    p = argparse.ArgumentParser(description=desc, epilog=epilog)
    p.add_argument('-s', '--list-services', action='store_true', default=False,
                   help='print a list of all AWS service types that '
                   'awslimitchecker knows how to check and exit')
    p.add_argument('-l', '--list-defaults', action='store_true', default=False,
                   help='print all AWS default limits in "service_name/'
                   'limit_name" format and exit')
    p.add_argument('-v', '--verbose', dest='verbose', action='count',
                   default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-V', '--version', dest='version', action='store_true',
                   default=False,
                   help='print version number and exit.')
    args = p.parse_args(argv)
    return args


def console_entry_point():
    args = parse_args(sys.argv[1:])
    if args.version:
        print('awslimitchecker {v} (see <{s}> for source code)'.format(
            s=get_project_url(),
            v=get_version()
        ))
        raise SystemExit(0)
    if args.list_services:
        for x in sorted(AwsLimitChecker.get_service_names()):
            print(x)
        raise SystemExit(0)
    if args.list_defaults:
        limits = AwsLimitChecker.get_default_limits()
        for svc in sorted(limits.keys()):
            for lim in sorted(limits[svc].keys()):
                print("{s}/{l}\t=> {n}".format(
                    s=svc,
                    l=lim,
                    n=limits[svc][lim]
                ))
        raise SystemExit(0)


if __name__ == "__main__":
    console_entry_point()
