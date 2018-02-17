#!/usr/bin/env python
"""
dev/terraform.py

Wrapper script around Terraform, using the TerraformRunner class from
`webhook2lambda2sqs <https://github.com/jantman/webhook2lambda2sqs>`_
to update my integration test accounts with the current generated IAM policy.

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
import os
from ConfigParser import SafeConfigParser

from awslimitchecker.checker import AwsLimitChecker
from webhook2lambda2sqs.terraform_runner import TerraformRunner

FORMAT = "[%(levelname)s %(filename)s:%(lineno)s - %(name)s.%(funcName)s() ] " \
         "%(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
logger = logging.getLogger()


class TerraformIAM(object):

    def __init__(self):
        logger.debug('Getting credentials')
        scriptpath = os.path.dirname(os.path.realpath(__file__))
        logger.debug('cd to scriptpath: %s', scriptpath)
        os.chdir(scriptpath)

    def run(self):
        """Run the Terraform"""
        pol = self.get_iam_policy()
        logger.info("Got IAM policy:\n%s\n", pol)
        with open('iam_policy.json', 'w') as fh:
            fh.write(pol)
        logger.info('Wrote policy to: iam_policy.json')
        self.run_tf()

    def run_tf(self):
        """actually run the terraform"""
        conf = {
            'terraform_remote_state': {
                'backend': 's3',
                'config': {
                    'bucket': 'jantman-personal',
                    'key': 'terraform/awslimitchecker-integration-iam',
                    'region': 'us-east-1'
                }
            }
        }
        runner = TerraformRunner(conf, 'terraform')
        runner._setup_tf(stream=True)
        runner._run_tf('plan', cmd_args=['-input=false', '-refresh=true', '.'],
                       stream=True)
        res = raw_input('Does this look correct? [y|N]')
        if res.lower().strip() != 'y':
            logger.error('OK, aborting!')
            return
        runner._run_tf('apply', cmd_args=['-input=false', '-refresh=true', '.'],
                       stream=True)

    def get_iam_policy(self):
        """Return the current IAM policy as a json-serialized string"""
        checker = AwsLimitChecker()
        policy = checker.get_required_iam_policy()
        return json.dumps(policy, sort_keys=True, indent=2)


if __name__ == "__main__":
    t = TerraformIAM()
    t.run()
