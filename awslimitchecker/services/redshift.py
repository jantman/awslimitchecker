"""
awslimitchecker/services/redshift.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2016 Jessie Nadler <nadler.jessie@gmail.com>

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
Jessie Nadler <nadler.jessie@gmail.com>
################################################################################
"""

import abc  # noqa
import logging

from .base import _AwsService
from ..limit import AwsLimit
from ..utils import paginate_dict

logger = logging.getLogger(__name__)


class _RedshiftService(_AwsService):

    service_name = 'Redshift'
    api_name = 'redshift'

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
        self._find_cluster_manual_snapshots()
        self._find_cluster_subnet_groups()
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_cluster_manual_snapshots(self):
        results = paginate_dict(
            self.conn.describe_cluster_snapshots,
            alc_marker_path=['Marker'],
            alc_data_path=['Snapshots'],
            alc_marker_param='Marker',
            SnapshotType='manual'
        )
        self.limits['Redshift manual snapshots']._add_current_usage(
            len(results['Snapshots']),
            resource_id=self._boto3_connection_kwargs['region_name'],
            aws_type='AWS::Redshift::Snapshot',
        )

    def _find_cluster_subnet_groups(self):
        results = paginate_dict(
            self.conn.describe_cluster_subnet_groups,
            alc_marker_path=['Marker'],
            alc_data_path=['ClusterSubnetGroups'],
            alc_marker_param='Marker'
        )
        self.limits['Redshift subnet groups']._add_current_usage(
            len(results['ClusterSubnetGroups']),
            resource_id=self._boto3_connection_kwargs['region_name'],
            aws_type='AWS::Redshift::SubnetGroup',
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
        limits['Redshift manual snapshots'] = AwsLimit(
            'Redshift manual snapshots',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::Redshift::Snapshot',
        )
        limits['Redshift subnet groups'] = AwsLimit(
            'Redshift subnet groups',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::Redshift::SubnetGroup',
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
            "redshift:DescribeClusterSnapshots",
            "redshift:DescribeClusterSubnetGroups",
        ]
