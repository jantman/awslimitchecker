#!/usr/bin/env python
"""
awslimitchecker/docs/examples/check_aws_limits.py

awslimitchecker example Python wrapper - see README.rst for information

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

import sys
import logging
import argparse

from awslimitchecker.checker import AwsLimitChecker
from termcolor import colored

# BEGIN configuration for thresholds and limit overrides
AWS_LIMIT_OVERRIDES = {
    'AutoScaling': {
        'Auto Scaling groups': 100,
        'Launch configurations': 200,
    },
    'EBS': {
        'General Purpose (SSD) volume storage (GiB)': 30720,
        'Magnetic volume storage (GiB)': 30720,
    },
    'EC2': {
        'Running On-Demand EC2 instances': 1000,
        'Running On-Demand c1.medium instances': 1000,
    },
    'ELB': {
        'Active load balancers': 100,
    },
}

AWS_THRESHOLD_OVERRIDES = {
    'VPC': {
        # i.e. if you're using 4 of 5 VPCs
        'VPCs': {'warning': {'percent': 90}},
        'Internet gateways': {'warning': {'percent': 90}},
    },
}
# END configuration for thresholds and limit overrides

logger = logging.getLogger(__name__)


class CheckAWSLimits(object):
    """check AWS usage against service limits"""

    def check_limits(self, verbose=False):
        """
        Run the actual usage and limit check, with overrides.

        see: http://awslimitchecker.readthedocs.org/en/latest/python_usage.html#ci-deployment-checks
        """
        # instantiate the class
        checker = AwsLimitChecker()
        # set your overrides
        checker.set_threshold_overrides(AWS_THRESHOLD_OVERRIDES)
        checker.set_limit_overrides(AWS_LIMIT_OVERRIDES)

        print("Checking AWS resource usage; WARNING threshold {w}% of "
              "limit, CRITICAL threshold {c}% of limit".format(
                  w=checker.warning_threshold,
                  c=checker.critical_threshold))

        # check usage against thresholds
        # if we didn't support verbose output, we could just iterate the return
        # value of this to be a bit more efficient.
        checker.check_thresholds()

        # save state for exit code and summary
        warnings = []
        criticals = []

        # iterate the results
        for service, svc_limits in sorted(checker.get_limits().items()):
            for limit_name, limit in sorted(svc_limits.items()):
                have_alarms = False
                # check warnings and criticals for each Limit
                for warn in limit.get_warnings():
                    warnings.append(colored("{service} '{limit_name}' usage "
                                            "({u}) exceeds warning threshold "
                                            "(limit={l})".format(
                                                service=service,
                                                limit_name=limit_name,
                                                u=str(warn),
                                                l=limit.get_limit(),
                                            ), 'yellow'))
                    have_alarms = True
                for crit in limit.get_criticals():
                    criticals.append(colored("{service} '{limit_name}' usage "
                                             "({u}) exceeds critical threshold"
                                             " (limit={l})".format(
                                                 service=service,
                                                 limit_name=limit_name,
                                                 u=str(crit),
                                                 l=limit.get_limit(),
                                             ), 'red'))
                    have_alarms = True
                if not have_alarms and verbose:
                    print("{service} '{limit_name}' OK: {u} (limit={l})".format(
                        service=service,
                        limit_name=limit_name,
                        u=limit.get_current_usage_str(),
                        l=limit.get_limit()
                    ))
        if verbose:
            print("\n\n")
        return (warnings, criticals)

    def run(self, error_on_warning=False, verbose=False):
        """
        Main entry point.
        """
        warnings, criticals = self.check_limits(verbose=verbose)
        # output
        if len(warnings) > 0:
            print("\nWARNING:\n")
            for w in warnings:
                print(w)
        if len(criticals) > 0:
            print("\nCRITICAL:\n")
            for c in criticals:
                print(c)

        # summary
        if len(warnings) > 0 or len(criticals) > 0:
            print("\n{c} limit(s) above CRITICAL threshold; {w} limit(s) above "
                  "WARNING threshold".format(c=len(criticals), w=len(warnings)))
        else:
            print("All limits are within thresholds.")
        if (len(warnings) > 0 and error_on_warning) or len(criticals) > 0:
            raise SystemExit(1)


def parse_args(argv):
    p = argparse.ArgumentParser(description="check AWS usage against service "
                                "limits")
    p.add_argument('-v', '--verbose', action='store_true',
                   default=False, dest='verbose',
                   help='verbose output - show all usage')
    p.add_argument("-w", "--error-on-warning", action="store_true",
                   default=False, dest='error_on_warning',
                   help="Exit 1 on warning as well as critical")
    args = p.parse_args(argv)
    return args

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    checker = CheckAWSLimits()
    checker.run(error_on_warning=args.error_on_warning, verbose=args.verbose)
