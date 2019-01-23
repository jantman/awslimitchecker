"""
awslimitchecker/services/cloudformation.py

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

import abc  # noqa
import logging

from .base import _AwsService
from ..limit import AwsLimit

logger = logging.getLogger(__name__)


class _CloudformationService(_AwsService):

    service_name = 'CloudFormation'
    api_name = 'cloudformation'  # AWS API name to connect to (boto3.client)

    def find_usage(self):
        """
        Determine the current usage for each limit of this service,
        and update corresponding Limit via
        :py:meth:`~.AwsLimit._add_current_usage`.
        """
        ignore_statuses = [
            'DELETE_COMPLETE'
        ]
        logger.debug("Checking usage for service %s", self.service_name)
        self.connect()
        for lim in self.limits.values():
            lim._reset_usage()
        count = 0
        paginator = self.conn.get_paginator('describe_stacks')
        iter = paginator.paginate()
        for page in iter:
            for stk in page['Stacks']:
                if stk['StackStatus'] not in ignore_statuses:
                    count += 1
        self.limits['Stacks']._add_current_usage(
            count, aws_type='AWS::CloudFormation::Stack'
        )
        self._have_usage = True
        logger.debug("Done checking usage.")

    def get_limits(self):
        """
        Return all known limits for this service, as a dict of their names
        to :py:class:`~.AwsLimit` objects.

        :returns: dict of limit names to :py:class:`~.AwsLimit` objects
        :rtype: dict
        """
        if self.limits != {}:
            return self.limits
        limits = {}
        limits['Stacks'] = AwsLimit(
            'Stacks',
            self,
            200,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::CloudFormation::Stack',
        )
        self.limits = limits
        return limits

    def _update_limits_from_api(self):
        """
        Call the service's API action to retrieve limit/quota information, and
        update AwsLimit objects in ``self.limits`` with this information.
        """
        logger.debug('Setting CloudFormation limits from API')
        self.connect()
        resp = self.conn.describe_account_limits()
        for lim in resp['AccountLimits']:
            if lim['Name'] == 'StackLimit':
                self.limits['Stacks']._set_api_limit(lim['Value'])
                continue
            logger.debug('API response contained unknown CloudFormation '
                         'limit: %s', lim['Name'])

    def required_iam_permissions(self):
        """
        Return a list of IAM Actions required for this Service to function
        properly. All Actions will be shown with an Effect of "Allow"
        and a Resource of "*".

        :returns: list of IAM Action strings
        :rtype: list
        """
        return [
            'cloudformation:DescribeAccountLimits',
            'cloudformation:DescribeStacks'
        ]
