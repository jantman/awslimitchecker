"""
awslimitchecker/services/ecs.py

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
Di Zou <zou@pythian.com>
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

import abc  # noqa
import logging

from .base import _AwsService
from ..limit import AwsLimit

logger = logging.getLogger(__name__)


class _EcsService(_AwsService):

    service_name = 'ECS'
    api_name = 'ecs'  # AWS API name to connect to (boto3.client)

    def find_usage(self):
        """
        Determine the current usage for each limit of this service,
        and update corresponding Limit via
        :py:meth:`~.AwsLimit._add_current_usage`.

        __NOTE__ that the "EC2 Tasks per Service (desired count)" limit uses
        non-standard resource IDs, as service names and ARNs aren't unique
        by account or region, but only by cluster. i.e. the only way to uniquely
        identify an ECS Service is by the combination of service and cluster.
        As such, the ``resource_id`` field for usage values of the
        "EC2 Tasks per Service (desired count)" limit is a string of the form
        ``cluster=CLUSTER-NAME; service=SERVICE-NAME``.
        """
        logger.debug("Checking usage for service %s", self.service_name)
        self.connect()
        for lim in self.limits.values():
            lim._reset_usage()
        self._find_usage_clusters()
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_clusters(self):
        """
        Find the ECS service usage for clusters. Calls
        :py:meth:`~._find_usage_one_cluster` for each cluster.
        """
        count = 0
        fargate_task_count = 0
        paginator = self.conn.get_paginator('list_clusters')
        for page in paginator.paginate():
            for cluster_arn in page['clusterArns']:
                count += 1
                resp = self.conn.describe_clusters(
                    clusters=[cluster_arn], include=['STATISTICS']
                )
                cluster = resp['clusters'][0]
                self.limits[
                    'Container Instances per Cluster'
                ]._add_current_usage(
                    cluster['registeredContainerInstancesCount'],
                    aws_type='AWS::ECS::ContainerInstance',
                    resource_id=cluster['clusterName']
                )
                self.limits['Services per Cluster']._add_current_usage(
                    cluster['activeServicesCount'],
                    aws_type='AWS::ECS::Service',
                    resource_id=cluster['clusterName']
                )
                # Note: 'statistics' is not always present in API responses,
                # even if requested. As far as I can tell, it's omitted if
                # a cluster has no Fargate tasks.
                for stat in cluster.get('statistics', []):
                    if stat['name'] != 'runningFargateTasksCount':
                        continue
                    logger.debug(
                        'Found %s Fargate tasks in cluster %s',
                        stat['value'], cluster_arn
                    )
                    fargate_task_count += int(stat['value'])
                self._find_usage_one_cluster(cluster['clusterName'])
        self.limits['Fargate Tasks']._add_current_usage(
            fargate_task_count, aws_type='AWS::ECS::Task'
        )
        self.limits['Clusters']._add_current_usage(
            count, aws_type='AWS::ECS::Cluster'
        )

    def _find_usage_one_cluster(self, cluster_name):
        """
        Find usage for services in each cluster.

        :param cluster_name: name of the cluster to find usage for
        :type cluster_name: str
        """
        tps_lim = self.limits['EC2 Tasks per Service (desired count)']
        paginator = self.conn.get_paginator('list_services')
        for page in paginator.paginate(
            cluster=cluster_name, launchType='EC2'
        ):
            for svc_arn in page['serviceArns']:
                svc = self.conn.describe_services(
                    cluster=cluster_name, services=[svc_arn]
                )['services'][0]
                if svc['launchType'] != 'EC2':
                    continue
                tps_lim._add_current_usage(
                    svc['desiredCount'],
                    aws_type='AWS::ECS::Service',
                    resource_id='cluster=%s; service=%s' % (
                        cluster_name, svc['serviceName']
                    )
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
        limits['Clusters'] = AwsLimit(
            'Clusters',
            self,
            1000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ECS::Cluster',
        )
        limits['Container Instances per Cluster'] = AwsLimit(
            'Container Instances per Cluster',
            self,
            1000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ECS::ContainerInstance'
        )
        limits['Services per Cluster'] = AwsLimit(
            'Services per Cluster',
            self,
            500,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ECS::Service'
        )
        limits['EC2 Tasks per Service (desired count)'] = AwsLimit(
            'EC2 Tasks per Service (desired count)',
            self,
            1000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ECS::TaskDefinition',
            limit_subtype='EC2'
        )
        limits['Fargate Tasks'] = AwsLimit(
            'Fargate Tasks',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ECS::TaskDefinition',
            limit_subtype='Fargate'
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
            'ecs:DescribeClusters',
            'ecs:DescribeServices',
            'ecs:ListClusters',
            'ecs:ListServices'
        ]
