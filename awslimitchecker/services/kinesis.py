"""
awslimitchecker/services/kinesis.py

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


class _KinesisService(_AwsService):

    service_name = 'Kinesis'
    api_name = 'kinesis'
    quotas_service_code = 'kinesis'

    def find_usage(self):
        """
        Determine the current usage for each limit of this service,
        and update corresponding Limit via
        :py:meth:`~.AwsLimit._add_current_usage`.
        """
        logger.debug("Checking usage for service %s", self.service_name)
        self.connect()
        for lim in self.limits.values():
            lim._reset_usage()
        self._find_shards()
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_shards(self):
        describe_limits_response = self.conn.describe_limits()
        self.limits['Shards per Region']._add_current_usage(
            describe_limits_response['OpenShardCount'],
            resource_id=self._boto3_connection_kwargs['region_name'],
            aws_type='AWS::Kinesis::Stream'
        )

    def get_limits(self):
        """
        Return all known limits for this service, as a dict of their names
        to :py:class:`~.AwsLimit` objects.

        :returns: dict of limit names to :py:class:`~.AwsLimit` objects
        :rtype: dict
        """
        if self.limits != {}:
            return self.limits

        self.connect()
        region_name = self.conn._client_config.region_name
        regions_500_shards = ['us-east-1', 'us-west-2', 'eu-west-1']

        limits = {}

        limits['Shards per Region'] = AwsLimit(
            'Shards per Region',
            self,
            500 if region_name in regions_500_shards else 200,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::Kinesis::Stream',
        )
        self.limits = limits
        return limits

    def _update_limits_from_api(self):
        """
        Call the service's API action to retrieve limit/quota information, and
        update AwsLimit objects in ``self.limits`` with this information.
        """
        logger.debug("Updating limits for Kinesis from the AWS API")
        self.connect()
        describe_limits_response = self.conn.describe_limits()
        self.limits['Shards per Region']._set_api_limit(
            describe_limits_response['ShardLimit']
        )

    def required_iam_permissions(self):
        """
        Return a list of IAM Actions required for this Service to function
        properly. All Actions will be shown with an Effect of "Allow"
        and a Resource of "*".

        :returns: list of IAM Action strings
        :rtype: list
        """
        return [
            'kinesis:DescribeLimits',
        ]
