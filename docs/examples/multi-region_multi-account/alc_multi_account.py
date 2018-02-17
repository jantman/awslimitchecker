#!/usr/bin/env python
"""
awslimitchecker/docs/examples/multi-region_multi-account/alc_multi_account.py

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
import os
import logging
import argparse
import json
import re

from awslimitchecker.checker import AwsLimitChecker
from termcolor import colored

#: This defines the default role name to assume in other accounts that don't
#: have a specific name (or ``null`` for no assumed role) specified in their
#: config.json files.
DEFAULT_ROLE_NAME = 'awslimitchecker'

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class Config(object):

    acct_id_re = re.compile(r'^[0-9]+$')

    def __init__(self, config_dir):
        self._conf_dir = config_dir
        self._config = {}
        self._acct_name_to_id = {}
        self._load_config()

    def _load_config(self):
        """load configuration from config/"""
        logger.debug(
            'Listing per-account config subdirectories in %s', self._conf_dir
        )
        for acct_id in os.listdir(self._conf_dir):
            path = os.path.join(self._conf_dir, acct_id)
            # skip if not a directory
            if not os.path.isdir(path):
                continue
            # skip if doesn't match ^[0-9]+$
            if not self.acct_id_re.match(acct_id):
                continue
            # call _load_account specifying the directory name (acct ID) & path
            self._load_account(acct_id, path)
        # Once all configuration is loaded, build a dict of Account Name to
        # Account ID (``self._acct_name_to_id``) for faster access to configs
        # by name.
        for acct_id, data in self._config.items():
            if data['name'] is None:
                continue
            self._acct_name_to_id[data['name']] = acct_id

    def _load_account(self, acct_id, acct_dir_path):
        """load configuration from one per-account subdirectory"""
        # setup a default config dict for the account
        self._config[acct_id] = {
            'name': None,
            'role_name': DEFAULT_ROLE_NAME,
            'regions': {}
        }
        # read the account config file
        # @TODO unhandled exception if file doesn't exist or isn't JSON
        with open(os.path.join(acct_dir_path, 'config.json'), 'r') as fh:
            acct_conf = json.loads(fh.read())
        # overwrite defaults with what we read from the account JSON
        self._config[acct_id].update(acct_conf)
        # iterate over contents of the per-account directory
        for region_name in os.listdir(acct_dir_path):
            path = os.path.join(acct_dir_path, region_name)
            # skip anything that isn't a directory
            if not os.path.isdir(path):
                continue
            # load the per-region configs for the account...
            # @TODO - should check that it's a valid region name
            self._load_region(acct_id, region_name, path)

    def _load_region(self, acct_id, region_name, path):
        """load config from a single per-region subdirectory of an account"""
        lim_path = os.path.join(path, 'limit_overrides.json')
        thresh_path = os.path.join(path, 'threshold_overrides.json')
        res = {'limit_overrides': {}, 'threshold_overrides': {}}
        if os.path.exists(lim_path):
            with open(lim_path, 'r') as fh:
                res['limit_overrides'] = json.loads(fh.read())
        if os.path.exists(thresh_path):
            with open(thresh_path, 'r') as fh:
                res['threshold_overrides'] = json.loads(fh.read())
        self._config[acct_id]['regions'][region_name] = res

    def get_account_config(self, id_or_name):
        """
        Return a dictionary of account configuration for the account with the
        specified ID or name.

        :param id_or_name: ID or name of account
        :type id_or_name: str
        :return: configuration for specified account
        :rtype: dict
        """
        if id_or_name in self._config:
            return self._config[id_or_name]
        if id_or_name in self._acct_name_to_id:
            return self._config[self._acct_name_to_id[id_or_name]]
        raise RuntimeError('ERROR: Unknown account ID or name')

    @property
    def list_account_ids(self):
        """
        Return a list of the configured account IDs

        :return: list of configured account IDs (strings)
        :rtype: list
        """
        return list(self._config.keys())


class MultiAccountChecker(object):
    """check AWS usage against service limits"""

    def __init__(self, config):
        self._conf = config

    def check_limits(self, acct_id, region_name, role_name=None,
                     limit_overrides={}, threshold_overrides={}):
        """
        Run the actual usage and limit check, with overrides, against a specific
        account in a specific region, optionally assuming a role in the account
        and optionally setting limit and/or threshold overrides.

        Return a 2-tuple of lists, warning strings and critical strings.

        see: http://awslimitchecker.readthedocs.org/en/latest/python_usage.html

        :returns: 2-tuple of lists of strings, warnings and criticals
        """
        # instantiate the class
        if role_name is not None:
            checker = AwsLimitChecker(
                account_id=acct_id, region=region_name, account_role=role_name
            )
        else:
            checker = AwsLimitChecker(region=region_name)
        # set your overrides
        if len(threshold_overrides) > 0:
            checker.set_threshold_overrides(threshold_overrides)
        if len(limit_overrides) > 0:
            checker.set_limit_overrides(limit_overrides)

        # check usage against thresholds
        checker.check_thresholds()

        # save state for exit code and summary
        warnings = []
        criticals = []

        # iterate the results
        for service, svc_limits in sorted(checker.get_limits().items()):
            for limit_name, limit in sorted(svc_limits.items()):
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
                for crit in limit.get_criticals():
                    criticals.append(colored("{service} '{limit_name}' usage "
                                             "({u}) exceeds critical threshold"
                                             " (limit={l})".format(
                                                 service=service,
                                                 limit_name=limit_name,
                                                 u=str(crit),
                                                 l=limit.get_limit(),
                                             ), 'red'))
        return warnings, criticals

    def run(self, error_on_warning=False, region=None, accounts=[]):
        """
        Main entry point.
        """
        all_warnings = []
        all_criticals = []
        if len(accounts) == 0:
            # if no accounts specified, run all of them
            accounts = self._conf.list_account_ids
        for acct_id in accounts:
            acct_conf = self._conf.get_account_config(acct_id)
            if region is None:
                regions = list(acct_conf['regions'].keys())
            elif region in acct_conf['regions']:
                regions = [region]
            else:
                print('\nAccount %s is not configured for region %s' % (
                    acct_id, region
                ))
                regions = []
            for rname in regions:
                print('\n%s (%s) %s' % (acct_id, acct_conf['name'], rname))
                warnings, criticals = self.check_limits(
                    acct_id, rname, role_name=acct_conf['role_name'],
                    limit_overrides=acct_conf[
                        'regions'][rname]['limit_overrides'],
                    threshold_overrides=acct_conf[
                        'regions'][rname]['threshold_overrides'],
                )
                # output
                for w in warnings:
                    print("\tWARNING: %s" % w)
                    all_warnings.append(w)
                for c in criticals:
                    print("\tCRITICAL: %s" % c)
                    all_criticals.append(c)
                if len(warnings) == 0 and len(criticals) == 0:
                    print("\tNo problems found.")

        # summary
        if len(all_warnings) > 0 or len(all_criticals) > 0:
            print(
                "\n{c} limit(s) above CRITICAL threshold; {w} limit(s) above "
                "WARNING threshold".format(
                    c=len(all_criticals), w=len(all_warnings)
                )
            )
        else:
            print("All limits are within thresholds.")
        if (
            (len(all_warnings) > 0 and error_on_warning) or
            len(all_criticals) > 0
        ):
            print('PROBLEMS FOUND. See above output for details.')
            raise SystemExit(1)


def parse_args(argv):
    p = argparse.ArgumentParser(
        description='check AWS usage against service limits'
    )
    p.add_argument(
        '-w', '--error-on-warning', action='store_true', default=False,
        dest='error_on_warning', help="Exit 1 on warning as well as critical"
    )
    p.add_argument(
        '-r', '--region', action='store', type=str, dest='region_name',
        default=None, help='run only for this region name'
    )
    p.add_argument(
        'ACCOUNT', nargs='*', help='run only for these account IDs/names'
    )
    args = p.parse_args(argv)
    return args

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    conf = Config(os.path.abspath(os.path.join('.', 'config')))
    checker = MultiAccountChecker(conf)
    checker.run(
        error_on_warning=args.error_on_warning,
        region=args.region_name,
        accounts=args.ACCOUNT
    )
