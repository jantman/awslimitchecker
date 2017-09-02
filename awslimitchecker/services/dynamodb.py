"""
awslimitchecker/services/dynamodb.py
The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>
################################################################################
Copyright 2015-2017 Jason Antman <jason@jasonantman.com>
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

import abc  # noqa
import logging

from .base import _AwsService
from ..limit import AwsLimit

logger = logging.getLogger(__name__)


class _DynamodbService(_AwsService):

    service_name = 'DynamoDB'
    api_name = 'dynamodb'  # AWS API name to connect to (boto3.client)

    def find_usage(self):
        """
        Determine the current usage for each limit of this service,
        and update corresponding Limit via
        :py:meth:`~.AwsLimit._add_current_usage`.
        """
        logger.debug("Checking usage for service %s", self.service_name)

        self.connect()
        self.connect_resource()

        for lim in self.limits.values():
            lim._reset_usage()

        self._find_usage_dynamodb()



    def _find_usage_dynamodb(self):
        ''' calculates current usage for all DynamoDB limits '''

        logger.debug("Getting usage for DynamoDB tables")
        table_count = 0
        region_read_capacity = 0
        region_write_capacity = 0

        for table in self.connect().list_tables()['TableNames']:

            table_count += 1
            gsi_write = 0
            gsi_read = 0
            table_Arn = self.connect().describe_table(TableName=table)['Table']['TableArn']
            UsagePerTable = self.connect().describe_table(TableName=table)['Table']

            logger.debug("Getting usage for DynamoDB tables")

            for gsi in UsagePerTable['GlobalSecondaryIndexes']:
                gsi_read += gsi['ProvisionedThroughput']['ReadCapacityUnits']
                gsi_write += gsi['ProvisionedThroughput']['WriteCapacityUnits']

            table_write_capacity = UsagePerTable['ProvisionedThroughput']['WriteCapacityUnits'] + gsi_write
            table_read_capacity = UsagePerTable['ProvisionedThroughput']['ReadCapacityUnits'] + gsi_read
            region_read_capacity += table_read_capacity
            region_write_capacity += table_write_capacity

            self.limits['Global Secondary Indexes (table)']._add_current_usage(len(UsagePerTable['GlobalSecondaryIndexes'] if 'GlobalSecondaryIndexes' in UsagePerTable else 0), resource_id=table_Arn, aws_type='AWS::DynamoDB::Table')
            self.limits['Local Secondary Indexes (table)']._add_current_usage(len(UsagePerTable['LocalSecondaryIndexes'] if 'LocalSecondaryIndexes' in UsagePerTable else 0), resource_id=table_Arn, aws_type='AWS::DynamoDB::Table')
            self.limits['Write Capacity (table)']._add_current_usage(table_write_capacity, resource_id=table_Arn)
            self.limits['Read Capacity (table)']._add_current_usage(table_read_capacity, resource_id=table_Arn)

        self.limits['Table Count (region)']._add_current_usage(table_count, aws_type='AWS::DynamoDB::Table')
        self.limits['Write Capacity (region)']._add_current_usage(region_write_capacity, aws_type='AWS::DynamoDB::Table')
        self.limits['Read Capacity (region)']._add_current_usage(region_read_capacity, aws_type='AWS::DynamoDB::Table')


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
        limits.update(self._get_limits_dynamodb())
        self.limits = limits
        return limits

    def _get_limits_dynamodb(self):
        """
        Return a dict of DynamoDB-related limits only.
        This method should only be used internally by
        :py:meth:~.get_limits`.
        :rtype: dict
        """
        limits = {}

        limits['Table_Count (region)'] = AwsLimit(
            'Table Count (region)',
            self,
            256,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::DynamoDB::Table',
        )


        limits['Write Capacity (region)'] = AwsLimit(
            'Write Capacity (region)',
            self,
            80000 if self.conn._client_config.region_name == 'us-east-1' else 20000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::DynamoDB::Table',)

        limits['Write Capacity (table)'] = AwsLimit(
            'Write Capacity (table)',
            self,
            40000 if self.conn._client_config.region_name == 'us-east-1' else 10000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::DynamoDB::Table',
        )

        limits['Read Capacity (region)'] = AwsLimit(
            'Read Capacity (region)',
            self,
            80000 if self.conn._client_config.region_name == 'us-east-1' else 20000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::DynamoDB::Table',
        )

        limits['Read Capacity (table)'] = AwsLimit(
            'Read Capacity (table)',
            self,
            40000 if self.conn._client_config.region_name == 'us-east-1' else 10000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::DynamoDB::Table',
        )

        limits['Global Secondary Indexes (table)'] = AwsLimit(
            'Read Capacity (table)',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::DynamoDB::Table',
        )

        limits['Local Secondary Indexes (table)'] = AwsLimit(
            'Read Capacity (table)',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::DynamoDB::Table',
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
            "dynamodb:DescribeTable"
        ]



