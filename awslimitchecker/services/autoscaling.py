"""
awslimitchecker/services/autoscaling.py

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
from ..utils import paginate_dict

logger = logging.getLogger(__name__)


class _AutoscalingService(_AwsService):

    service_name = 'AutoScaling'
    api_name = 'autoscaling'

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

        self.limits['Auto Scaling groups']._add_current_usage(
            len(
                paginate_dict(
                    self.conn.describe_auto_scaling_groups,
                    alc_marker_path=['NextToken'],
                    alc_data_path=['AutoScalingGroups'],
                    alc_marker_param='NextToken'
                )['AutoScalingGroups']
            ),
            aws_type='AWS::AutoScaling::AutoScalingGroup',
        )

        self.limits['Launch configurations']._add_current_usage(
            len(
                paginate_dict(
                    self.conn.describe_launch_configurations,
                    alc_marker_path=['NextToken'],
                    alc_data_path=['LaunchConfigurations'],
                    alc_marker_param='NextToken'
                )['LaunchConfigurations']
            ),
            aws_type='AWS::AutoScaling::LaunchConfiguration',
        )
        self._have_usage = True
        logger.debug("Done checking usage.")

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
        # autoscaleconnection.get_all_groups()
        limits['Auto Scaling groups'] = AwsLimit(
            'Auto Scaling groups',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::AutoScaling::AutoScalingGroup',
        )
        # autoscaleconnection.get_all_launch_configurations()
        limits['Launch configurations'] = AwsLimit(
            'Launch configurations',
            self,
            100,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::AutoScaling::LaunchConfiguration',
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
            'autoscaling:DescribeAccountLimits',
            'autoscaling:DescribeAutoScalingGroups',
            'autoscaling:DescribeLaunchConfigurations',
        ]

    def _update_limits_from_api(self):
        """
        Query EC2's DescribeAccountAttributes API action, and update limits
        with the quotas returned. Updates ``self.limits``.
        """
        self.connect()
        logger.info("Querying EC2 DescribeAccountAttributes for limits")
        lims = self.conn.describe_account_limits()
        self.limits['Auto Scaling groups']._set_api_limit(
            lims['MaxNumberOfAutoScalingGroups'])
        self.limits['Launch configurations']._set_api_limit(
            lims['MaxNumberOfLaunchConfigurations'])
