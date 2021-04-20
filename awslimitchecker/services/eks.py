"""
awslimitchecker/services/eks.py

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
from ..utils import paginate_dict

logger = logging.getLogger(__name__)


class _EksService(_AwsService):

    service_name = 'EKS'
    api_name = 'eks'  # AWS API name to connect to (boto3.client)
    quotas_service_code = 'eks'

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
        self._find_clusters_usage()
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_clusters_usage(self):
        clusters_info = paginate_dict(
            self.conn.list_clusters,
            alc_marker_path=['nextToken'],
            alc_data_path=['clusters'],
            alc_marker_param='nextToken'
        )

        cluster_list = clusters_info['clusters']

        for cluster in cluster_list:
            describe_cluster_response = self.conn.describe_cluster(
                name=cluster
            )
            security_group_id_list = describe_cluster_response['cluster'][
                'resourcesVpcConfig']['securityGroupIds']
            self.limits[
                'Control plane security groups per cluster']._add_current_usage(
                len(security_group_id_list),
                resource_id=cluster,
                aws_type='AWS::EKS::Cluster'
            )
            public_access_cidrs_list = describe_cluster_response['cluster'][
                'resourcesVpcConfig']['publicAccessCidrs']
            self.limits[
                'Public endpoint access CIDR ranges per cluster'
            ]._add_current_usage(
                len(public_access_cidrs_list),
                resource_id=cluster,
                aws_type='AWS::EKS::Cluster'
            )

            list_nodegroup_response = paginate_dict(
                self.conn.list_nodegroups,
                clusterName=cluster,
                alc_marker_path=['nextToken'],
                alc_data_path=['nodegroups'],
                alc_marker_param='nextToken'
            )
            nodegroup_list = list_nodegroup_response['nodegroups']
            self.limits['Managed node groups per cluster']._add_current_usage(
                len(nodegroup_list),
                resource_id=cluster,
                aws_type='AWS::EKS::Cluster')

            list_fargate_profiles_response = paginate_dict(
                self.conn.list_fargate_profiles,
                clusterName=cluster,
                alc_marker_path=['nextToken'],
                alc_data_path=['fargateProfileNames'],
                alc_marker_param='nextToken'
            )
            fargate_profiles_list = list_fargate_profiles_response[
                'fargateProfileNames'
            ]
            self.limits['Fargate profiles per cluster']._add_current_usage(
                len(fargate_profiles_list),
                resource_id=cluster,
                aws_type='AWS::EKS::FargateProfile')

            for fargate_profile_name in fargate_profiles_list:
                fargate_info = self.conn.describe_fargate_profile(
                    clusterName=cluster,
                    fargateProfileName=fargate_profile_name
                )
                profile_selectors = fargate_info['fargateProfile']['selectors']
                self.limits['Selectors per Fargate profile']._add_current_usage(
                    len(profile_selectors),
                    resource_id="{}.{}".format(cluster, fargate_profile_name),
                    aws_type='AWS::EKS::FargateProfile')

                for selector in profile_selectors:
                    label_pairs = selector.get('labels')
                    if label_pairs is None:
                        continue
                    self.limits[
                        'Label pairs per Fargate profile selector'
                    ]._add_current_usage(
                        len(label_pairs),
                        resource_id=(
                            "{}.{}.{}".format(
                                cluster,
                                fargate_profile_name,
                                selector
                            )
                        ),
                        aws_type='AWS::EKS::FargateProfile')

        self.limits['Clusters']._add_current_usage(
            len(cluster_list),
            resource_id=self._boto3_connection_kwargs['region_name'],
            aws_type='AWS::EKS::Cluster')

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
            100,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EKS::Cluster',
        )
        limits['Control plane security groups per cluster'] = AwsLimit(
            'Control plane security groups per cluster',
            self,
            4,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EKS::Cluster',
        )
        limits['Managed node groups per cluster'] = AwsLimit(
            'Managed node groups per cluster',
            self,
            30,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EKS::Nodegroup',
        )
        limits['Nodes per managed node group'] = AwsLimit(
            'Nodes per managed node group',
            self,
            100,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EKS::Cluster',
        )
        limits['Public endpoint access CIDR ranges per cluster'] = AwsLimit(
            'Public endpoint access CIDR ranges per cluster',
            self,
            40,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EKS::Cluster',
        )
        limits['Fargate profiles per cluster'] = AwsLimit(
            'Fargate profiles per cluster',
            self,
            10,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EKS::FargateProfile',
        )
        limits['Selectors per Fargate profile'] = AwsLimit(
            'Selectors per Fargate profile',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EKS::FargateProfile',
        )
        limits['Label pairs per Fargate profile selector'] = AwsLimit(
            'Label pairs per Fargate profile selector',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EKS::FargateProfile',
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
            "eks:ListClusters",
            "eks:DescribeCluster",
            "eks:ListNodegroups",
            "eks:ListFargateProfiles",
            "eks:DescribeFargateProfile",
        ]
