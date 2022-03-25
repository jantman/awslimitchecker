"""
awslimitchecker/services/vpc.py

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
from collections import defaultdict

from .base import _AwsService
from ..limit import AwsLimit
from ..utils import paginate_dict
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class _VpcService(_AwsService):

    service_name = 'VPC'
    api_name = 'ec2'
    quotas_service_code = 'vpc'

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
        subnet_to_az = self._find_usage_subnets()
        self._find_usage_ACLs()
        self._find_usage_route_tables()
        self._find_usage_gateways()
        self._find_usage_nat_gateways(subnet_to_az)
        self._find_usages_vpn_gateways()
        self._find_usage_network_interfaces()
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_vpcs(self):
        """find usage for VPCs"""
        # overall number of VPCs
        vpcs = self.conn.describe_vpcs(
            Filters=[{'Name': 'owner-id', 'Values': [self.current_account_id]}]
        )
        self.limits['VPCs']._add_current_usage(
            len(vpcs['Vpcs']),
            aws_type='AWS::EC2::VPC'
        )

    def _find_usage_subnets(self):
        """find usage for Subnets; return dict of SubnetId to AZ"""
        # subnets per VPC
        subnet_to_az = {}
        subnets = defaultdict(int)
        for subnet in self.conn.describe_subnets(
            Filters=[{'Name': 'owner-id', 'Values': [self.current_account_id]}]
        )['Subnets']:
            subnets[subnet['VpcId']] += 1
            subnet_to_az[subnet['SubnetId']] = subnet['AvailabilityZone']
        for vpc_id in subnets:
            self.limits['Subnets per VPC']._add_current_usage(
                subnets[vpc_id],
                aws_type='AWS::EC2::VPC',
                resource_id=vpc_id
            )
        return subnet_to_az

    def _find_usage_ACLs(self):
        """find usage for ACLs"""
        # Network ACLs per VPC
        acls = defaultdict(int)
        for acl in self.conn.describe_network_acls(
            Filters=[{'Name': 'owner-id', 'Values': [self.current_account_id]}]
        )['NetworkAcls']:
            acls[acl['VpcId']] += 1
            # Rules per network ACL
            egress_ipv4 = sum(map(
                lambda x: x["Egress"] and "CidrBlock" in x, acl['Entries']
            ))
            ingress_ipv4 = sum(map(
                lambda x: not x["Egress"] and "CidrBlock" in x, acl['Entries']
            ))
            egress_ipv6 = sum(map(
                lambda x: x["Egress"] and "Ipv6CidrBlock" in x, acl['Entries']
            ))
            ingress_ipv6 = sum(map(
                lambda x: not x["Egress"] and "Ipv6CidrBlock" in x,
                acl['Entries']
            ))
            self.limits['Rules per network ACL']._add_current_usage(
                max(egress_ipv4, ingress_ipv4, egress_ipv6, ingress_ipv6),
                aws_type='AWS::EC2::NetworkAcl',
                resource_id=acl['NetworkAclId']
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
        for table in self.conn.describe_route_tables(
            Filters=[{'Name': 'owner-id', 'Values': [self.current_account_id]}]
        )['RouteTables']:
            tables[table['VpcId']] += 1
            # Entries per route table
            routes = [
                r for r in table['Routes']
                if r['Origin'] != 'EnableVgwRoutePropagation'
            ]
            self.limits['Entries per route table']._add_current_usage(
                len(routes),
                aws_type='AWS::EC2::RouteTable',
                resource_id=table['RouteTableId']
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
        gws = self.conn.describe_internet_gateways(
            Filters=[{'Name': 'owner-id', 'Values': [self.current_account_id]}]
        )
        self.limits['Internet gateways']._add_current_usage(
            len(gws['InternetGateways']),
            aws_type='AWS::EC2::InternetGateway',
        )

    def _find_usage_nat_gateways(self, subnet_to_az):
        """
        find usage for NAT Gateways

        :param subnet_to_az: dict mapping subnet ID to AZ
        :type subnet_to_az: dict
        """
        # currently, some regions (sa-east-1 as one example) don't have NAT
        # Gateway service; they return an AuthError,
        # "This request has been administratively disabled."
        try:
            gws_per_az = defaultdict(int)
            for gw in paginate_dict(
                self.conn.describe_nat_gateways,
                alc_marker_path=['NextToken'], alc_data_path=['NatGateways'],
                alc_marker_param='NextToken'
            )['NatGateways']:
                if gw['State'] not in ['pending', 'available']:
                    logger.debug(
                        'Skipping NAT Gateway %s in state: %s',
                        gw['NatGatewayId'], gw['State']
                    )
                    continue
                if gw['SubnetId'] not in subnet_to_az:
                    logger.error('ERROR: NAT Gateway %s in SubnetId %s, but '
                                 'SubnetId not found in subnet_to_az; Gateway '
                                 'cannot be counted!', gw['NatGatewayId'],
                                 gw['SubnetId'])
                    continue
                gws_per_az[subnet_to_az[gw['SubnetId']]] += 1
            for az in sorted(gws_per_az.keys()):
                self.limits['NAT Gateways per AZ']._add_current_usage(
                    gws_per_az[az],
                    resource_id=az,
                    aws_type='AWS::EC2::NatGateway'
                )
        except ClientError:
            logger.error('Caught exception when trying to list NAT Gateways; '
                         'perhaps NAT service does not exist in this region?',
                         exc_info=1)

    def _find_usages_vpn_gateways(self):
        """find usage of vpn gateways"""

        # do not include deleting and deleted in the results
        vpngws = self.conn.describe_vpn_gateways(Filters=[
            {
                'Name': 'state',
                'Values': [
                    'available',
                    'pending'
                ]
            }
        ])['VpnGateways']

        self.limits['Virtual private gateways']._add_current_usage(
            len(vpngws),
            aws_type='AWS::EC2::VPNGateway'
        )

    def _find_usage_network_interfaces(self):
        """find usage of network interfaces"""
        enis = paginate_dict(
            self.conn.describe_network_interfaces,
            alc_marker_path=['NextToken'],
            alc_data_path=['NetworkInterfaces'],
            alc_marker_param='NextToken',
            Filters=[{'Name': 'owner-id', 'Values': [self.current_account_id]}]
        )

        self.limits['Network interfaces per Region']._add_current_usage(
            len(enis['NetworkInterfaces']),
            aws_type='AWS::EC2::NetworkInterface'
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
            quotas_name='VPCs per Region'
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
            quotas_name='Routes per route table'
        )

        limits['Internet gateways'] = AwsLimit(
            'Internet gateways',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::InternetGateway',
            quotas_name='Internet gateways per Region'
        )

        limits['NAT Gateways per AZ'] = AwsLimit(
            'NAT Gateways per AZ',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::NatGateway',
            quotas_name='NAT gateways per Availability Zone'
        )

        limits['Virtual private gateways'] = AwsLimit(
            'Virtual private gateways',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::VPNGateway'
        )

        limits['Network interfaces per Region'] = AwsLimit(
            'Network interfaces per Region',
            self,
            5000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::NetworkInterface'
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
            'ec2:DescribeNatGateways',
            'ec2:DescribeNetworkAcls',
            'ec2:DescribeRouteTables',
            'ec2:DescribeSubnets',
            'ec2:DescribeVpcs',
            'ec2:DescribeVpnGateways',
            'ec2:DescribeNetworkInterfaces',
        ]
