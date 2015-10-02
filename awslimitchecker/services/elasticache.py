"""
awslimitchecker/services/elasticache.py

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

import abc  # noqa
import boto.elasticache
from boto.elasticache.layer1 import ElastiCacheConnection
from boto.exception import BotoServerError
import logging

from .base import _AwsService
from ..limit import AwsLimit

logger = logging.getLogger(__name__)


class _ElastiCacheService(_AwsService):

    service_name = 'ElastiCache'

    def connect(self):
        """Connect to API if not already connected; set self.conn."""
        if self.conn is not None:
            return
        elif self.region:
            self.conn = self.connect_via(boto.elasticache.connect_to_region)
        else:
            self.conn = ElastiCacheConnection()

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
        clusters = self.conn.describe_cache_clusters(show_cache_node_info=True)[
            'DescribeCacheClustersResponse']['DescribeCacheClustersResult'][
                'CacheClusters']
        for cluster in clusters:
            try:
                num_nodes = len(cluster['CacheNodes'])
            except (IndexError, TypeError):
                # sometimes CacheNodes is None...
                logger.debug("Cache Cluster '%s' returned dict with CacheNodes "
                             "None", cluster['CacheClusterId'])
                num_nodes = cluster['NumCacheNodes']
            nodes += num_nodes
            self.limits['Nodes per Cluster']._add_current_usage(
                num_nodes,
                aws_type='AWS::ElastiCache::CacheCluster',
                resource_id=cluster['CacheClusterId'],
            )

        self.limits['Clusters']._add_current_usage(
            len(clusters),
            aws_type='AWS::ElastiCache::CacheCluster'
        )
        self.limits['Nodes']._add_current_usage(
            nodes,
            aws_type='AWS::ElastiCache::CacheNode'
        )

    def _find_usage_subnet_groups(self):
        """find usage for elasticache subnet groups"""
        groups = self.conn.describe_cache_subnet_groups()[
            'DescribeCacheSubnetGroupsResponse'][
            'DescribeCacheSubnetGroupsResult'][
            'CacheSubnetGroups']
        self.limits['Subnet Groups']._add_current_usage(
            len(groups),
            aws_type='AWS::ElastiCache::SubnetGroup'
        )

    def _find_usage_parameter_groups(self):
        """find usage for elasticache parameter groups"""
        groups = self.conn.describe_cache_parameter_groups()[
            'DescribeCacheParameterGroupsResponse'][
            'DescribeCacheParameterGroupsResult'][
            'CacheParameterGroups']
        self.limits['Parameter Groups']._add_current_usage(
            len(groups),
            aws_type='AWS::ElastiCache::ParameterGroup'
        )

    def _find_usage_security_groups(self):
        """find usage for elasticache security groups"""
        try:
            # If EC2-Classic isn't available (e.g., a new account)
            # this method will fail with:
            #   Code:    "InvalidParameterValue"
            #   Message: "Use of cache security groups is not permitted in
            #             this API version for your account."
            #   Type:    "Sender"
            groups = self.conn.describe_cache_security_groups()[
                'DescribeCacheSecurityGroupsResponse'][
                'DescribeCacheSecurityGroupsResult'][
                'CacheSecurityGroups']
        except BotoServerError:
            logger.debug("caught BotoServerError checking ElastiCache security "
                         "groups (account without EC2-Classic?)")
            groups = []

        self.limits['Security Groups']._add_current_usage(
            len(groups),
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
            50,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ElastiCache::CacheNode',
        )

        limits['Clusters'] = AwsLimit(
            'Clusters',
            self,
            50,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ElastiCache::CacheCluster',
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
