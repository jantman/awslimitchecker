#!/usr/bin/env python
"""
dev/update_integration_iam_policy.py

Script using boto3 to update my integration test accounts with the current
generated IAM policy.

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

import logging
import json
import boto3
import os

from awslimitchecker.checker import AwsLimitChecker

FORMAT = "[%(levelname)s %(filename)s:%(lineno)s - %(name)s.%(funcName)s() ] " \
         "%(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger()


class IntegrationIamPolicyUpdater(object):

    def run(self):
        os.environ['AWS_DEFAULT_REGION'] = 'us-west-2'
        acct_id = boto3.client('sts').get_caller_identity()['Account']
        logger.info('Found Account ID as: %s', acct_id)
        iam = boto3.client('iam')
        aliases = iam.list_account_aliases()
        logger.info('Found account aliases as: %s', aliases)
        # ensure it's my account, without hard-coding the ID
        assert aliases['AccountAliases'] == ['jantman']
        pol = self.get_iam_policy()
        logger.info("Got IAM policy:\n%s\n", pol)
        arn = 'arn:aws:iam::%s:policy/awslimitchecker' % acct_id
        logger.info('Getting versions for policy: %s', arn)
        curr_versions = iam.list_policy_versions(PolicyArn=arn)['Versions']
        if len(curr_versions) > 3:
            logger.info('Policy currently has %d versions; removing old ones')
            for ver in sorted(
                curr_versions, key=lambda x: x['CreateDate'], reverse=True
            )[3:]:
                if ver['IsDefaultVersion']:
                    continue
                logger.info('Removing policy version %s', ver['VersionId'])
                iam.delete_policy_version(
                    PolicyArn=arn, VersionId=ver['VersionId']
                )
        logger.info('Updating policy')
        res = iam.create_policy_version(
            PolicyArn=arn, PolicyDocument=pol, SetAsDefault=True
        )
        logger.info(
            'Create policy version %s as default',
            res['PolicyVersion']['VersionId']
        )

    def get_iam_policy(self):
        """Return the current IAM policy as a json-serialized string"""
        checker = AwsLimitChecker()
        policy = checker.get_required_iam_policy()
        return json.dumps(policy, sort_keys=True, indent=2)


if __name__ == "__main__":
    IntegrationIamPolicyUpdater().run()
