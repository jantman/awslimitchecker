"""
awslimitchecker/services/dynamodb.py

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


class _DynamodbService(_AwsService):

    service_name = 'DynamoDB'
    api_name = 'dynamodb'

    def find_usage(self):
        """
        Determine the current usage for each limit of this service,
        and update corresponding Limit via
        :py:meth:`~.AwsLimit._add_current_usage`.
        """
        logger.debug("Checking usage for service %s", self.service_name)
        self.connect_resource()
        for lim in self.limits.values():
            lim._reset_usage()
        self._find_usage_dynamodb()
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_dynamodb(self):
        """calculates current usage for all DynamoDB limits"""
        table_count = 0
        region_read_capacity = 0
        region_write_capacity = 0

        logger.debug("Getting usage for DynamoDB tables")
        for table in self.resource_conn.tables.all():
            table_count += 1
            gsi_write = 0
            gsi_read = 0
            gsi_count = 0
            if table.global_secondary_indexes is not None:
                for gsi in table.global_secondary_indexes:
                    gsi_count += 1
                    gsi_read += gsi['ProvisionedThroughput'][
                        'ReadCapacityUnits']
                    gsi_write += gsi['ProvisionedThroughput'][
                        'WriteCapacityUnits']
            table_write_capacity = table.provisioned_throughput[
                                       'WriteCapacityUnits'] + gsi_write
            table_read_capacity = table.provisioned_throughput[
                                      'ReadCapacityUnits'] + gsi_read
            region_write_capacity += table_write_capacity
            region_read_capacity += table_read_capacity

            self.limits['Global Secondary Indexes']._add_current_usage(
                gsi_count,
                resource_id=table.name,
                aws_type='AWS::DynamoDB::Table'
            )

            self.limits['Local Secondary Indexes']._add_current_usage(
                len(table.local_secondary_indexes)
                if table.local_secondary_indexes is not None else 0,
                resource_id=table.name,
                aws_type='AWS::DynamoDB::Table'
            )

            self.limits['Table Max Write Capacity Units']._add_current_usage(
                table_write_capacity,
                resource_id=table.name,
                aws_type='AWS::DynamoDB::Table'
            )

            self.limits['Table Max Read Capacity Units']._add_current_usage(
                table_read_capacity,
                resource_id=table.name,
                aws_type='AWS::DynamoDB::Table'
            )

        self.limits['Tables Per Region']._add_current_usage(
            table_count,
            aws_type='AWS::DynamoDB::Table'
        )

        self.limits['Account Max Write Capacity Units']._add_current_usage(
            region_write_capacity,
            aws_type='AWS::DynamoDB::Table'
        )

        self.limits['Account Max Read Capacity Units']._add_current_usage(
            region_read_capacity,
            aws_type='AWS::DynamoDB::Table'
        )

    def get_limits(self):
        """
        Return all known limits for this service, as a dict of their names
        to :py:class:`~.AwsLimit` objects.

        :returns: dict of limit names to :py:class:`~.AwsLimit` objects
        :rtype: dict
        """
        self.connect()
        region_name = self.conn._client_config.region_name
        if self.limits != {}:
            return self.limits
        limits = {}

        limits['Tables Per Region'] = AwsLimit(
            'Tables Per Region',
            self,
            256,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::DynamoDB::Table',
        )

        limits['Account Max Write Capacity Units'] = AwsLimit(
            'Account Max Write Capacity Units',
            self,
            80000 if region_name == 'us-east-1' else 20000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::DynamoDB::Table', )

        limits['Table Max Write Capacity Units'] = AwsLimit(
            'Table Max Write Capacity Units',
            self,
            40000 if region_name == 'us-east-1' else 10000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::DynamoDB::Table',
        )

        limits['Account Max Read Capacity Units'] = AwsLimit(
            'Account Max Read Capacity Units',
            self,
            80000 if region_name == 'us-east-1' else 20000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::DynamoDB::Table',
        )

        limits['Table Max Read Capacity Units'] = AwsLimit(
            'Table Max Read Capacity Units',
            self,
            40000 if region_name == 'us-east-1' else 10000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::DynamoDB::Table',
        )

        limits['Global Secondary Indexes'] = AwsLimit(
            'Global Secondary Indexes',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::DynamoDB::Table',
        )

        limits['Local Secondary Indexes'] = AwsLimit(
            'Local Secondary Indexes',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::DynamoDB::Table',
        )

        self.limits = limits
        return limits

    def _update_limits_from_api(self):
        """
        Query DynamoDB's DescribeLimits API action, and update limits
        with the quotas returned. Updates ``self.limits``.
        """
        self.connect()
        logger.info("Querying DynamoDB DescribeLimits for limits")
        # no need to paginate
        lims = self.conn.describe_limits()
        self.limits['Account Max Read Capacity Units']._set_api_limit(
            lims['AccountMaxReadCapacityUnits']
        )
        self.limits['Account Max Write Capacity Units']._set_api_limit(
            lims['AccountMaxWriteCapacityUnits']
        )
        self.limits['Table Max Read Capacity Units']._set_api_limit(
            lims['TableMaxReadCapacityUnits']
        )
        self.limits['Table Max Write Capacity Units']._set_api_limit(
            lims['TableMaxWriteCapacityUnits']
        )
        logger.debug("Done setting limits from API")

    def required_iam_permissions(self):
        """
        Return a list of IAM Actions required for this Service to function
        properly. All Actions will be shown with an Effect of "Allow"
        and a Resource of "*".

        :returns: list of IAM Action strings
        :rtype: list
        """
        return [
            "dynamodb:DescribeLimits",
            "dynamodb:DescribeTable",
            "dynamodb:ListTables"
        ]
