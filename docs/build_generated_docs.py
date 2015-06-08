"""
awslimitchecker docs/build_generated_docs.py

Builds documentation that is generated dynamically from awslimitchecker.

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
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
################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/pydnstest> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

import json
import logging
import os
import sys
from textwrap import dedent

my_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(my_dir, '..'))

from awslimitchecker.checker import AwsLimitChecker

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

def build_iam_policy(checker):
    logger.info("Beginning build of iam_policy.rst")
    # get the policy dict
    logger.info("Getting IAM Policy")
    policy = checker.get_required_iam_policy()
    # serialize as pretty-printed JSON
    policy_json = json.dumps(policy, sort_keys=True, indent=2)
    # indent each line by 4 spaces
    policy_str = ''
    for line in policy_json.split("\n"):
        policy_str += (' ' * 4) + line + "\n"
    doc = """
    .. _iam_policy:

    Required IAM Permissions
    ========================

    Below is the sample IAM policy from this version of awslimitchecker, listing the IAM
    permissions required for it to function correctly:

    .. code-block:: json

    {policy_str}
    """
    doc = dedent(doc)
    doc = doc.format(policy_str=policy_str)
    fname = os.path.join(my_dir, 'source', 'iam_policy.rst')
    logger.info("Writing {f}".format(f=fname))
    with open(fname, 'w') as fh:
        fh.write(doc)

def build_limits(checker):
    logger.info("Beginning build of limits.rst")
    # get the policy dict
    logger.info("Getting Limits")
    ta_info = 'TODO'  # @TODO trusted advisor data
    limit_info = ''
    limits = checker.get_limits()
    # this is a bit of a pain, because we need to know string lengths to build the table
    for svc_name in sorted(limits):
        limit_info += svc_name + "\n"
        limit_info += ('+' * (len(svc_name)+1)) + "\n"
        limit_info += "\n"
        # build a dict of the limits
        slimits = {}
        # track the maximum string lengths
        max_name = 0
        max_default_limit = 0
        for limit in limits[svc_name].values():
            # update max string length for table formatting
            if len(limit.name) > max_name:
                max_name = len(limit.name)
            if len(str(limit.default_limit)) > max_default_limit:
                max_default_limit = len(str(limit.default_limit))
            # @TODO trusted advisor, use :sup:`[TA]`
            slimits[limit.name] = str(limit.default_limit)
        # create the format string
        sformat = '{name: <' + str(max_name) + '} ' \
                  '{limit: <' + str(max_default_limit) + '}\n'
        # separator lines
        sep = ('=' * max_name) + ' ' + ('=' * max_default_limit) + "\n"
        # header
        limit_info += sep
        limit_info += sformat.format(name='Limit', limit='Default')
        limit_info += sep
        # limit lines
        for lname, limit in sorted(slimits.iteritems()):
            limit_info += sformat.format(name=lname, limit=limit)
        # footer
        limit_info += sep

    doc = """
    .. _limits:

    Supported Limits
    ================

    .. _limits.trusted_advisor:

    Trusted Advisor Data
    ---------------------

    {ta_info}

    .. _limits.checks:

    Current Checks
    ---------------

    The section below lists every limit that this version of awslimitchecker knows
    how to check, and its hard-coded default value (per AWS documentation).

    {limit_info}

    """
    doc = dedent(doc)
    doc = doc.format(ta_info=ta_info, limit_info=limit_info)
    fname = os.path.join(my_dir, 'source', 'limits.rst')
    logger.info("Writing {f}".format(f=fname))
    with open(fname, 'w') as fh:
        fh.write(doc)

def build_docs():
    """
    Trigger rebuild of all documentation that is dynamically generated
    from awslimitchecker.
    """
    logger.info("Beginning build of dynamically-generated docs")
    logger.info("Instantiating AwsLimitChecker")
    c = AwsLimitChecker()
    build_iam_policy(c)
    build_limits(c)

if __name__ == "__main__":
    build_docs()
