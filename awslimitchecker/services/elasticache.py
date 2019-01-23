"""
awslimitchecker/services/elasticache.py

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
from botocore.exceptions import ClientError
import logging

from .base import _AwsService
from ..limit import AwsLimit

logger = logging.getLogger(__name__)


class _ElastiCacheService(_AwsService):

    service_name = 'ElastiCache'
    api_name = 'elasticache'

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
        self._find_usage_nodes()
        self._find_usage_subnet_groups()
        self._find_usage_parameter_groups()
        self._find_usage_security_groups()
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_nodes(self):
        """find usage for cache nodes"""
        nodes = 0
        paginator = self.conn.get_paginator('describe_cache_clusters')
        for page in paginator.paginate(ShowCacheNodeInfo=True):
            for cluster in page['CacheClusters']:
                try:
                    num_nodes = len(cluster['CacheNodes'])
                except (IndexError, TypeError, KeyError):
                    # sometimes CacheNodes is None...
                    logger.debug(
                        "Cache Cluster '%s' returned dict with CacheNodes "
                        "None", cluster['CacheClusterId'])
                    num_nodes = cluster['NumCacheNodes']
                nodes += num_nodes
                if cluster['Engine'] == 'memcached':
                    self.limits['Nodes per Cluster']._add_current_usage(
                        num_nodes,
                        aws_type='AWS::ElastiCache::CacheCluster',
                        resource_id=cluster['CacheClusterId'],
                    )

        self.limits['Nodes']._add_current_usage(
            nodes,
            aws_type='AWS::ElastiCache::CacheNode'
        )

    def _find_usage_subnet_groups(self):
        """find usage for elasticache subnet groups"""
        num_groups = 0

        paginator = self.conn.get_paginator('describe_cache_subnet_groups')
        for page in paginator.paginate():
            for group in page['CacheSubnetGroups']:
                num_groups += 1
                self.limits['Subnets per subnet group']._add_current_usage(
                    len(group['Subnets']),
                    resource_id=group['CacheSubnetGroupName'],
                    aws_type='AWS::ElastiCache::SubnetGroup'
                )
        self.limits['Subnet Groups']._add_current_usage(
            num_groups,
            aws_type='AWS::ElastiCache::SubnetGroup'
        )

    def _find_usage_parameter_groups(self):
        """find usage for elasticache parameter groups"""
        num_groups = 0

        paginator = self.conn.get_paginator('describe_cache_parameter_groups')
        for page in paginator.paginate():
            for group in page['CacheParameterGroups']:
                num_groups += 1
        self.limits['Parameter Groups']._add_current_usage(
            num_groups,
            aws_type='AWS::ElastiCache::ParameterGroup'
        )

    def _find_usage_security_groups(self):
        """find usage for elasticache security groups"""
        num_groups = 0
        # If EC2-Classic isn't available (e.g., a new account)
        # this method will fail with:
        #   Code:    "InvalidParameterValue"
        #   Message: "Use of cache security groups is not permitted in
        #             this API version for your account."
        #   Type:    "Sender"
        try:
            paginator = self.conn.get_paginator(
                'describe_cache_security_groups')
            for page in paginator.paginate():
                for secgroup in page['CacheSecurityGroups']:
                    num_groups += 1
        except ClientError as ex:
            if ex.response['Error']['Code'] != 'InvalidParameterValue':
                raise ex
            logger.debug("caught ClientError checking ElastiCache security "
                         "groups (account without EC2-Classic?)")

        self.limits['Security Groups']._add_current_usage(
            num_groups,
            aws_type='WS::ElastiCache::SecurityGroup'
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

        limits['Nodes'] = AwsLimit(
            'Nodes',
            self,
            100,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ElastiCache::CacheNode',
        )

        limits['Nodes per Cluster'] = AwsLimit(
            'Nodes per Cluster',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ElastiCache::CacheNode',
        )

        limits['Subnet Groups'] = AwsLimit(
            'Subnet Groups',
            self,
            50,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ElastiCache::SubnetGroup',
        )

        limits['Subnets per subnet group'] = AwsLimit(
            'Subnets per subnet group',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ElastiCache::SubnetGroup',
        )

        limits['Parameter Groups'] = AwsLimit(
            'Parameter Groups',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ElastiCache::ParameterGroup',
        )

        limits['Security Groups'] = AwsLimit(
            'Security Groups',
            self,
            50,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='WS::ElastiCache::SecurityGroup',
        )
        self.limits = limits
        return limits

    def required_iam_permissions(self):
        """
        Return a list of IAM Actions required for this Service to function
        properly. All Actions will be shown with an Effect of "Allow"
        and a Resource of "*".

        :returns: list of IAM Action strings
        :rtype: list
        """
        return [
            "elasticache:DescribeCacheClusters",
            "elasticache:DescribeCacheParameterGroups",
            "elasticache:DescribeCacheSecurityGroups",
            "elasticache:DescribeCacheSubnetGroups",
        ]
