"""
awslimitchecker/services/ecs.py

The latest version of this package is available at:
<https://github.com/di1214/awslimitchecker>

################################################################################
Copyright 2015-2017 Di Zou <zou@pythian.com>

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
bugs please submit them at <https://github.com/di1214/pydnstest> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Di Zou <zou@pythian.com>
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
        """
        logger.debug("Checking usage for service %s", self.service_name)
        self.connect()
        for lim in self.limits.values():
            lim._reset_usage()
        self._find_usage_clusters()
        self._have_usage = True
        logger.debug("Done checking usage.")
    
    def _find_usage_clusters(self):
        count = 0
        paginator = self.conn.get_paginator('list_clusters')
        iter = paginator.paginate()
        for page in iter:
            for clusterArn in page['clusterArns']:
                count += 1
                resp = self.conn.describe_clusters(
                    clusters = [
                        clusterArn,
                    ]
                )
                cluster = resp['clusters'][0]
                self.limits['Container Instances per Cluster']._add_current_usage(
                    cluster['registeredContainerInstancesCount'],
                    aws_type='AWS::ECS',
                    resource_id=clusterArn
                )
                self.limits['Services per Cluster']._add_current_usage(
                    cluster['activeServicesCount'],
                    aws_type='AWS::ECS',
                    resource_id=clusterArn
                )
        self.limits['Clusters']._add_current_usage(
            count, aws_type='AWS::ECS'
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
            limit_type='AWS::ECS',
        )
        limits['Container Instances per Cluster'] = AwsLimit(
            'Container Instances per Cluster',
            self,
            1000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ECS',
            limit_subtype='ContainerInstance'
        )
        limits['Services per Cluster'] = AwsLimit(
            'Services per Cluster',
            self,
            500,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ECS',
            limit_subtype='ContainerService'
        )
        # TODO: need to implement this later
        # limits['EC2 Tasks per Service (desired count)'] = AwsLimit(
        #     'EC2 Tasks per Service (desired count)',
        #     self,
        #     1000,
        #     self.warning_threshold,
        #     self.critical_threshold,
        #     limit_type='AWS::ECS',
        #     limit_subtype='EcsTask'
        # )
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
        # TODO: update this to be all IAM permissions required for find_usage() to work
        return [
            "ecs:Describe*",
            "ecs:List*",
        ]
