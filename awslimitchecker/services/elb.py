"""
awslimitchecker/services/elb.py

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
from boto3 import client
from botocore.config import Config

from .base import _AwsService
from ..limit import AwsLimit
from ..utils import paginate_dict

logger = logging.getLogger(__name__)

#: Override the elbv2 API maximum retry attempts
ELBV2_MAX_RETRY_ATTEMPTS = 12


class _ElbService(_AwsService):
    """
    Note that ELB (ELBv1) and ALB (ELBv2) are combined in the same service.
    This is because, per AWS docs, the limit for number of load balancers
    per region is a combination of ELB and ALB.
    """

    service_name = 'ELB'
    api_name = 'elb'

    def find_usage(self):
        """
        Determine the current usage for each limit of this service,
        and update corresponding Limit via
        :py:meth:`~.AwsLimit._add_current_usage`.
        """
        logger.debug("Checking usage for service %s", self.service_name)
        for lim in self.limits.values():
            lim._reset_usage()
        elb_usage = self._find_usage_elbv1()
        alb_usage = self._find_usage_elbv2()
        logger.debug('ELBs in use: %d, ALBs in use: %d', elb_usage, alb_usage)
        self.limits['Active load balancers']._add_current_usage(
            (elb_usage + alb_usage),
            aws_type='AWS::ElasticLoadBalancing::LoadBalancer',
        )
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_elbv1(self):
        """
        Find usage for ELBv1 / Classic ELB and update the appropriate limits.

        :returns: number of Classic ELBs in use
        :rtype: int
        """
        logger.debug("Checking usage for ELBv1")
        self.connect()
        lbs = paginate_dict(
            self.conn.describe_load_balancers,
            alc_marker_path=['NextMarker'],
            alc_data_path=['LoadBalancerDescriptions'],
            alc_marker_param='Marker'
        )
        for lb in lbs['LoadBalancerDescriptions']:
            self.limits['Listeners per load balancer']._add_current_usage(
                len(lb['ListenerDescriptions']),
                aws_type='AWS::ElasticLoadBalancing::LoadBalancer',
                resource_id=lb['LoadBalancerName'],
            )
        logger.debug('Done with ELBv1 usage')
        return len(lbs['LoadBalancerDescriptions'])

    def _find_usage_elbv2(self):
        """
        Find usage for ELBv2 / Application LB and update the appropriate limits.

        :returns: number of Application LBs in use
        :rtype: int
        """
        logger.debug('Checking usage for ELBv2')
        conn2 = client(
            'elbv2',
            config=Config(retries={'max_attempts': ELBV2_MAX_RETRY_ATTEMPTS}),
            **self._boto3_connection_kwargs
        )
        logger.debug("Connected to %s in region %s (with max retry attempts "
                     "overridden to %d)", 'elbv2',
                     conn2._client_config.region_name, ELBV2_MAX_RETRY_ATTEMPTS)
        # Target groups
        tgroups = paginate_dict(
            conn2.describe_target_groups,
            alc_marker_path=['NextMarker'],
            alc_data_path=['TargetGroups'],
            alc_marker_param='Marker'
        )
        self.limits['Target groups']._add_current_usage(
            len(tgroups['TargetGroups']),
            aws_type='AWS::ElasticLoadBalancingV2::TargetGroup'
        )
        # ALBs
        lbs = paginate_dict(
            conn2.describe_load_balancers,
            alc_marker_path=['NextMarker'],
            alc_data_path=['LoadBalancers'],
            alc_marker_param='Marker'
        )
        logger.debug(
            'Checking usage for each of %d ALBs', len(lbs['LoadBalancers'])
        )
        for lb in lbs['LoadBalancers']:
            self._update_usage_for_elbv2(
                conn2,
                lb['LoadBalancerArn'],
                lb['LoadBalancerName']
            )
        logger.debug('Done with ELBv2 usage')
        return len(lbs['LoadBalancers'])

    def _update_usage_for_elbv2(self, conn, alb_arn, alb_name):
        """
        Update usage for a single ALB.

        :param conn: elbv2 API connection
        :type conn: :py:class:`ElasticLoadBalancing.Client`
        :param alb_arn: Load Balancer ARN
        :type alb_arn: str
        :param alb_name: Load Balancer Name
        :type alb_name: str
        """
        logger.debug('Updating usage for ALB %s', alb_arn)
        listeners = paginate_dict(
            conn.describe_listeners,
            LoadBalancerArn=alb_arn,
            alc_marker_path=['NextMarker'],
            alc_data_path=['Listeners'],
            alc_marker_param='Marker'
        )['Listeners']
        num_rules = 0
        for l in listeners:
            rules = paginate_dict(
                conn.describe_rules,
                ListenerArn=l['ListenerArn'],
                alc_marker_path=['NextMarker'],
                alc_data_path=['Rules'],
                alc_marker_param='Marker'
            )['Rules']
            num_rules += len(rules)
        self.limits[
            'Listeners per application load balancer']._add_current_usage(
            len(listeners),
            aws_type='AWS::ElasticLoadBalancingV2::LoadBalancer',
            resource_id=alb_name,
        )
        self.limits['Rules per application load balancer']._add_current_usage(
            num_rules,
            aws_type='AWS::ElasticLoadBalancingV2::LoadBalancer',
            resource_id=alb_name,
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
        # ELBv1 (Classic ELB) limits
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
        # ELBv2 (ALB) limits
        limits['Target groups'] = AwsLimit(
            'Target groups',
            self,
            3000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ElasticLoadBalancingV2::LoadBalancer',
            limit_subtype='LoadBalancerTargetGroup'
        )
        limits['Listeners per application load balancer'] = AwsLimit(
            'Listeners per application load balancer',
            self,
            50,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ElasticLoadBalancingV2::LoadBalancer',
            limit_subtype='LoadBalancerListener'
        )
        limits['Rules per application load balancer'] = AwsLimit(
            'Rules per application load balancer',
            self,
            100,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ElasticLoadBalancingV2::LoadBalancer',
            limit_subtype='LoadBalancerRule'
        )
        self.limits = limits
        return limits

    def _update_limits_from_api(self):
        """
        Query ELB's DescribeAccountLimits API action, and update limits
        with the quotas returned. Updates ``self.limits``.
        """
        self.connect()
        logger.debug("Querying ELB DescribeAccountLimits for limits")
        attribs = self.conn.describe_account_limits()
        name_to_limits = {
            'classic-load-balancers': 'Active load balancers',
            'classic-listeners': 'Listeners per load balancer'
        }
        for attrib in attribs['Limits']:
            if int(attrib.get('Max', 0)) == 0:
                continue
            name = attrib.get('Name', 'unknown')
            if name not in name_to_limits:
                continue
            self.limits[name_to_limits[name]]._set_api_limit(int(attrib['Max']))
        # connect to ELBv2 API as well
        self.conn2 = client('elbv2', **self._boto3_connection_kwargs)
        logger.debug("Connected to %s in region %s",
                     'elbv2', self.conn2._client_config.region_name)
        logger.debug("Querying ELBv2 (ALB) DescribeAccountLimits for limits")
        attribs = self.conn2.describe_account_limits()
        name_to_limits = {
            'target-groups': 'Target groups',
            'listeners-per-application-load-balancer':
                'Listeners per application load balancer',
            'rules-per-application-load-balancer':
                'Rules per application load balancer'
        }
        for attrib in attribs['Limits']:
            if int(attrib.get('Max', 0)) == 0:
                continue
            name = attrib.get('Name', 'unknown')
            if name not in name_to_limits:
                continue
            self.limits[name_to_limits[name]]._set_api_limit(int(attrib['Max']))
        logger.debug("Done setting limits from API")

    def required_iam_permissions(self):
        """
        Return a list of IAM Actions required for this Service to function
        properly. All Actions will be shown with an Effect of "Allow"
        and a Resource of "*".

        :returns: list of IAM Action strings
        :rtype: list
        """
        return [
            "elasticloadbalancing:DescribeLoadBalancers",
            "elasticloadbalancing:DescribeAccountLimits",
            "elasticloadbalancing:DescribeListeners",
            "elasticloadbalancing:DescribeTargetGroups",
            "elasticloadbalancing:DescribeRules"
        ]
