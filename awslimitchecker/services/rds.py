"""
awslimitchecker/services/rds.py

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


class _RDSService(_AwsService):

    service_name = 'RDS'
    api_name = 'rds'

    # Mapping of RDS DescribeAccountAttributes action AccountQuotaName string
    # to our Limit name
    API_NAME_TO_LIMIT = {
        'DBInstances': 'DB instances',
        'ReservedDBInstances': 'Reserved Instances',
        'AllocatedStorage': 'Storage quota (GB)',
        'DBSecurityGroups': 'DB security groups',
        'AuthorizationsPerDBSecurityGroup': 'Max auths per security group',
        'DBParameterGroups': 'DB parameter groups',
        'ManualSnapshots': 'DB snapshots per user',
        'EventSubscriptions': 'Event Subscriptions',
        'DBSubnetGroups': 'Subnet Groups',
        'OptionGroups': 'Option Groups',
        'SubnetsPerDBSubnetGroup': 'Subnets per Subnet Group',
        'ReadReplicasPerMaster': 'Read replicas per master',
        'DBClusters': 'DB Clusters',
        'DBClusterParameterGroups': 'DB Cluster Parameter Groups',
    }

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
        self._find_usage_instances()
        self._find_usage_subnet_groups()
        self._find_usage_security_groups()
        # RDS API also provides usage information
        self._update_limits_from_api()
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_instances(self):
        """find usage for DB Instances and related limits"""
        paginator = self.conn.get_paginator('describe_db_instances')
        for page in paginator.paginate():
            for instance in page['DBInstances']:
                self.limits['Read replicas per master']._add_current_usage(
                    len(instance['ReadReplicaDBInstanceIdentifiers']),
                    aws_type='AWS::RDS::DBInstance',
                    resource_id=instance['DBInstanceIdentifier']
                )

    def _find_usage_subnet_groups(self):
        """find usage for subnet groups"""
        paginator = self.conn.get_paginator('describe_db_subnet_groups')
        for page in paginator.paginate():
            for group in page['DBSubnetGroups']:
                self.limits['Subnets per Subnet Group']._add_current_usage(
                    len(group['Subnets']),
                    aws_type='AWS::RDS::DBSubnetGroup',
                    resource_id=group["DBSubnetGroupName"],
                )

    def _find_usage_security_groups(self):
        """find usage for security groups"""
        vpc_count = 0

        paginator = self.conn.get_paginator('describe_db_security_groups')
        for page in paginator.paginate():
            for group in page['DBSecurityGroups']:
                if 'VpcId' in group and group['VpcId'] is not None:
                    vpc_count += 1
                self.limits['Max auths per security group']._add_current_usage(
                    len(group["EC2SecurityGroups"]) + len(group["IPRanges"]),
                    aws_type='AWS::RDS::DBSecurityGroup',
                    resource_id=group['DBSecurityGroupName']
                )

        self.limits['VPC Security Groups']._add_current_usage(
            vpc_count,
            aws_type='AWS::RDS::DBSecurityGroup',
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
        limits = {}
        limits['DB instances'] = AwsLimit(
            'DB instances',
            self,
            40,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::RDS::DBInstance'
        )
        limits['Reserved Instances'] = AwsLimit(
            'Reserved Instances',
            self,
            40,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::RDS::DBInstance',
        )
        limits['Storage quota (GB)'] = AwsLimit(
            'Storage quota (GB)',
            self,
            100000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::RDS::DBInstance',
        )
        limits['DB snapshots per user'] = AwsLimit(
            'DB snapshots per user',
            self,
            100,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::RDS::DBSnapshot',
        )
        limits['DB parameter groups'] = AwsLimit(
            'DB parameter groups',
            self,
            50,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::RDS::DBParameterGroup',
        )
        limits['DB security groups'] = AwsLimit(
            'DB security groups',
            self,
            25,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::RDS::DBSecurityGroup',
        )
        limits['VPC Security Groups'] = AwsLimit(
            'VPC Security Groups',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::RDS::DBSecurityGroup',
        )
        limits['Subnet Groups'] = AwsLimit(
            'Subnet Groups',
            self,
            50,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::RDS::DBSubnetGroup',
            ta_limit_name='Subnet groups'
        )
        limits['Subnets per Subnet Group'] = AwsLimit(
            'Subnets per Subnet Group',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::RDS::DBSubnetGroup',
            ta_limit_name='Subnets per subnet group'
        )
        limits['Option Groups'] = AwsLimit(
            'Option Groups',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::RDS::DBOptionGroup',
        )
        limits['Event Subscriptions'] = AwsLimit(
            'Event Subscriptions',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::RDS::DBEventSubscription',
            ta_limit_name='Event subscriptions'
        )
        limits['Read replicas per master'] = AwsLimit(
            'Read replicas per master',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::RDS::DBInstance',
        )
        # this is the number of rules per security group
        limits['Max auths per security group'] = AwsLimit(
            'Max auths per security group',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::RDS::DBSecurityGroup',
            limit_subtype='AWS::RDS::DBSecurityGroupIngress',
        )
        limits['DB Clusters'] = AwsLimit(
            'DB Clusters',
            self,
            40,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::RDS::DBCluster',
            ta_limit_name='Clusters'
        )
        limits['DB Cluster Parameter Groups'] = AwsLimit(
            'DB Cluster Parameter Groups',
            self,
            50,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::RDS::DBClusterParameterGroup',
            ta_limit_name='Cluster parameter groups'
        )
        self.limits = limits
        return limits

    def _update_limits_from_api(self):
        """
        Query RDS's DescribeAccountAttributes API action, and update limits
        with the quotas returned. Updates ``self.limits``.

        We ignore the usage information from the API,
        """
        self.connect()
        logger.info("Querying RDS DescribeAccountAttributes for limits")
        lims = self.conn.describe_account_attributes()['AccountQuotas']
        for lim in lims:
            if lim['AccountQuotaName'] not in self.API_NAME_TO_LIMIT:
                logger.info('RDS DescribeAccountAttributes returned unknown'
                            'limit: %s (max: %s; used: %s)',
                            lim['AccountQuotaName'], lim['Max'], lim['Used'])
                continue
            lname = self.API_NAME_TO_LIMIT[lim['AccountQuotaName']]
            self.limits[lname]._set_api_limit(lim['Max'])
            if len(self.limits[lname].get_current_usage()) < 1:
                self.limits[lname]._add_current_usage(lim['Used'])
        logger.debug('Done setting limits from API.')

    def required_iam_permissions(self):
        """
        Return a list of IAM Actions required for this Service to function
        properly. All Actions will be shown with an Effect of "Allow"
        and a Resource of "*".

        :returns: list of IAM Action strings
        :rtype: list
        """
        return [
            "rds:DescribeAccountAttributes",
            "rds:DescribeDBInstances",
            "rds:DescribeDBParameterGroups",
            "rds:DescribeDBSecurityGroups",
            "rds:DescribeDBSnapshots",
            "rds:DescribeDBSubnetGroups",
            "rds:DescribeEventSubscriptions",
            "rds:DescribeOptionGroups",
            "rds:DescribeReservedDBInstances",
        ]
