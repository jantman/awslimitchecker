"""
awslimitchecker/services/vpc.py

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
bugs please submit them at <https://github.com/jantman/awslimitchecker> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

import abc  # noqa
import boto
import boto.vpc
import logging
from collections import defaultdict

from .base import _AwsService
from ..limit import AwsLimit

logger = logging.getLogger(__name__)


class _VpcService(_AwsService):

    service_name = 'VPC'

    def connect(self):
        """Connect to API if not already connected; set self.conn."""
        if self.conn is not None:
            return
        elif self.region:
            self.conn = self.connect_via(boto.vpc.connect_to_region)
        else:
            self.conn = boto.connect_vpc()

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
        self._find_usage_vpcs()
        self._find_usage_subnets()
        self._find_usage_ACLs()
        self._find_usage_route_tables()
        self._find_usage_gateways()
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_vpcs(self):
        """find usage for VPCs"""
        # overall number of VPCs
        vpcs = self.conn.get_all_vpcs()
        self.limits['VPCs']._add_current_usage(
            len(vpcs),
            aws_type='AWS::EC2::VPC'
        )

    def _find_usage_subnets(self):
        """find usage for Subnets"""
        # subnets per VPC
        subnets = defaultdict(int)
        for subnet in self.conn.get_all_subnets():
            # boto.vpc.subnet.Subnet
            subnets[subnet.vpc_id] += 1
        for vpc_id in subnets:
            self.limits['Subnets per VPC']._add_current_usage(
                subnets[vpc_id],
                aws_type='AWS::EC2::VPC',
                resource_id=vpc_id
            )

    def _find_usage_ACLs(self):
        """find usage for ACLs"""
        # Network ACLs per VPC
        acls = defaultdict(int)
        for acl in self.conn.get_all_network_acls():
            # boto.vpc.networkacl.NetworkAcl
            acls[acl.vpc_id] += 1
            # Rules per network ACL
            self.limits['Rules per network ACL']._add_current_usage(
                len(acl.network_acl_entries),
                aws_type='AWS::EC2::NetworkAcl',
                resource_id=acl.id
            )
        for vpc_id in acls:
            self.limits['Network ACLs per VPC']._add_current_usage(
                acls[vpc_id],
                aws_type='AWS::EC2::VPC',
                resource_id=vpc_id,
            )

    def _find_usage_route_tables(self):
        """find usage for route tables"""
        # Route tables per VPC
        tables = defaultdict(int)
        for table in self.conn.get_all_route_tables():
            # boto.vpc.routetable.RouteTable
            tables[table.vpc_id] += 1
            # Entries per route table
            self.limits['Entries per route table']._add_current_usage(
                len(table.routes),
                aws_type='AWS::EC2::RouteTable',
                resource_id=table.id
            )
        for vpc_id in tables:
            self.limits['Route tables per VPC']._add_current_usage(
                tables[vpc_id],
                aws_type='AWS::EC2::VPC',
                resource_id=vpc_id,
            )

    def _find_usage_gateways(self):
        """find usage for Internet Gateways"""
        # Internet gateways
        gws = self.conn.get_all_internet_gateways()
        self.limits['Internet gateways']._add_current_usage(
            len(gws),
            aws_type='AWS::EC2::InternetGateway',
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

        limits['VPCs'] = AwsLimit(
            'VPCs',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::VPC',
        )

        limits['Subnets per VPC'] = AwsLimit(
            'Subnets per VPC',
            self,
            200,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Subnet',
            limit_subtype='AWS::EC2::VPC',
        )

        limits['Network ACLs per VPC'] = AwsLimit(
            'Network ACLs per VPC',
            self,
            200,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::NetworkAcl',
            limit_subtype='AWS::EC2::VPC',
        )

        limits['Rules per network ACL'] = AwsLimit(
            'Rules per network ACL',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::NetworkAclEntry',
            limit_subtype='AWS::EC2::NetworkAcl',
        )

        limits['Route tables per VPC'] = AwsLimit(
            'Route tables per VPC',
            self,
            200,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::RouteTable',
            limit_subtype='AWS::EC2::VPC',
        )

        limits['Entries per route table'] = AwsLimit(
            'Entries per route table',
            self,
            50,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Route',
            limit_subtype='AWS::EC2::RouteTable',
        )

        limits['Internet gateways'] = AwsLimit(
            'Internet gateways',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::InternetGateway',
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
            'ec2:DescribeNetworkAcls',
            'ec2:DescribeRouteTables',
            'ec2:DescribeSubnets',
            'ec2:DescribeVpcs',
        ]
