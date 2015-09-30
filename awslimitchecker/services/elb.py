"""
awslimitchecker/services/elb.py

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
import boto
import boto.ec2.elb
import logging

from .base import _AwsService
from ..limit import AwsLimit

logger = logging.getLogger(__name__)


class _ElbService(_AwsService):

    service_name = 'ELB'

    def connect(self):
        """Connect to API if not already connected; set self.conn."""
        if self.conn is not None:
            return
        elif self.region:
            self.conn = self.connect_via(boto.ec2.elb.connect_to_region)
        else:
            self.conn = boto.connect_elb()

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
        lbs = self.conn.get_all_load_balancers()
        self.limits['Active load balancers']._add_current_usage(
            len(lbs),
            aws_type='AWS::ElasticLoadBalancing::LoadBalancer',
        )
        for lb in lbs:
            self.limits['Listeners per load balancer']._add_current_usage(
                len(lb.listeners),
                aws_type='AWS::ElasticLoadBalancing::LoadBalancer',
                resource_id=lb.name,
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
        limits['Active load balancers'] = AwsLimit(
            'Active load balancers',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ElasticLoadBalancing::LoadBalancer',
        )
        limits['Listeners per load balancer'] = AwsLimit(
            'Listeners per load balancer',
            self,
            100,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ElasticLoadBalancing::LoadBalancer',
            limit_subtype='LoadBalancerListener'
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
            "elasticloadbalancing:DescribeLoadBalancers"
        ]
