"""
awslimitchecker/services/ec2.py

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
import logging
from collections import defaultdict
from copy import deepcopy

from .base import _AwsService
from ..limit import AwsLimit

logger = logging.getLogger(__name__)


class _Ec2Service(_AwsService):

    service_name = 'EC2'
    api_name = 'ec2'

    def find_usage(self):
        """
        Determine the current usage for each limit of this service,
        and update corresponding Limit via
        :py:meth:`~.AwsLimit._add_current_usage`.
        """
        logger.debug("Checking usage for service %s", self.service_name)
        self.connect()
        self.connect_resource()
        for lim in self.limits.values():
            lim._reset_usage()
        self._find_usage_instances()
        self._find_usage_networking_sgs()
        self._find_usage_networking_eips()
        self._find_usage_networking_eni_sg()
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_instances(self):
        """calculate On-Demand instance usage for all types and update Limits"""
        # update our limits with usage
        inst_usage = self._instance_usage()
        res_usage = self._get_reserved_instance_count()
        # subtract reservations from instance usage
        ondemand_usage = defaultdict(int)
        for az in inst_usage:
            if az not in res_usage:
                for i_type, count in inst_usage[az].items():
                    ondemand_usage[i_type] += count
                continue
            # else we have reservations for this AZ
            for i_type, count in inst_usage[az].items():
                if i_type not in res_usage[az]:
                    # no reservations for this type
                    ondemand_usage[i_type] += count
                    continue
                od = count - res_usage[az][i_type]
                if od < 1:
                    # we have unused reservations
                    continue
                ondemand_usage[i_type] += od
        total_instances = 0
        for i_type, usage in ondemand_usage.items():
            key = 'Running On-Demand {t} instances'.format(
                t=i_type)
            self.limits[key]._add_current_usage(
                usage,
                aws_type='AWS::EC2::Instance',
            )
            total_instances += usage
        # limit for ALL On-Demand EC2 instances
        key = 'Running On-Demand EC2 instances'
        self.limits[key]._add_current_usage(
            total_instances,
            aws_type='AWS::EC2::Instance'
        )

    def _get_reserved_instance_count(self):
        """
        For each availability zone, get the count of current instance
        reservations of each instance type. Return as a nested
        dict of AZ name to dict of instance type to reservation count.

        :rtype: dict
        """
        reservations = defaultdict(int)
        az_to_res = {}
        logger.debug("Getting reserved instance information")
        res = self.conn.describe_reserved_instances()

        for x in res['ReservedInstances']:
            if x['State'] != 'active':
                logger.debug("Skipping ReservedInstance %s with state %s",
                             x['ReservedInstancesId'], x['State'])
                continue
            if x['AvailabilityZone'] not in az_to_res:
                az_to_res[x['AvailabilityZone']] = deepcopy(reservations)
            az_to_res[x['AvailabilityZone']][
                x['InstanceType']] += x['InstanceCount']
        # flatten and return
        for x in az_to_res:
            az_to_res[x] = dict(az_to_res[x])
        return az_to_res

    def _instance_usage(self):
        """
        Find counts of currently-running EC2 Instances
        (On-Demand or Reserved) by placement (Availability
        Zone) and instance type (size). Return as a nested dict
        of AZ name to dict of instance type to count.

        :rtype: dict
        """
        # On-Demand instances by type
        ondemand = {}
        for t in self._instance_types():
            ondemand[t] = 0
        az_to_inst = {}
        logger.debug("Getting usage for on-demand instances")
        for inst in self.resource_conn.instances.all():
            if inst.spot_instance_request_id:
                logger.warning("Spot instance found (%s); awslimitchecker "
                               "does not yet support spot "
                               "instances.", inst.id)
                continue
            if inst.state['Name'] in ['stopped', 'terminated']:
                logger.debug("Ignoring instance %s in state %s", inst.id,
                             inst.state['Name'])
                continue
            if inst.placement['AvailabilityZone'] not in az_to_inst:
                az_to_inst[
                    inst.placement['AvailabilityZone']] = deepcopy(ondemand)
            try:
                az_to_inst[
                    inst.placement['AvailabilityZone']][inst.instance_type] += 1
            except KeyError:
                logger.error("ERROR - unknown instance type '%s'; not "
                             "counting", inst.instance_type)
        return az_to_inst

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
        limits.update(self._get_limits_instances())
        limits.update(self._get_limits_networking())
        self.limits = limits
        return self.limits

    def _update_limits_from_api(self):
        """
        Query EC2's DescribeAccountAttributes API action, and update limits
        with the quotas returned. Updates ``self.limits``.
        """
        self.connect()
        self.connect_resource()
        logger.info("Querying EC2 DescribeAccountAttributes for limits")
        # no need to paginate
        attribs = self.conn.describe_account_attributes()
        for attrib in attribs['AccountAttributes']:
            aname = attrib['AttributeName']
            val = attrib['AttributeValues'][0]['AttributeValue']
            lname = None
            if aname == 'max-elastic-ips':
                lname = 'Elastic IP addresses (EIPs)'
            elif aname == 'max-instances':
                lname = 'Running On-Demand EC2 instances'
            elif aname == 'vpc-max-elastic-ips':
                lname = 'VPC Elastic IP addresses (EIPs)'
            elif aname == 'vpc-max-security-groups-per-interface':
                lname = 'VPC security groups per elastic network interface'
            if lname is not None:
                self.limits[lname]._set_api_limit(int(val))
        logger.debug("Done setting limits from API")

    def _get_limits_instances(self):
        """
        Return a dict of limits for EC2 instances only.
        This method should only be used internally by
        :py:meth:~.get_limits`.

        :rtype: dict
        """
        # from: http://aws.amazon.com/ec2/faqs/
        # (On-Demand, Reserved, Spot)
        default_limits = (20, 20, 5)
        special_limits = {
            'c4.4xlarge': (10, 20, 5),
            'c4.8xlarge': (5, 20, 5),
            'cg1.4xlarge': (2, 20, 5),
            'hi1.4xlarge': (2, 20, 5),
            'hs1.8xlarge': (2, 20, 0),
            'cr1.8xlarge': (2, 20, 5),
            'g2.2xlarge': (5, 20, 5),
            'g2.8xlarge': (2, 20, 5),
            'r3.4xlarge': (10, 20, 5),
            'r3.8xlarge': (5, 20, 5),
            'i2.xlarge': (8, 20, 0),
            'i2.2xlarge': (8, 20, 0),
            'i2.4xlarge': (4, 20, 0),
            'i2.8xlarge': (2, 20, 0),
            'd2.4xlarge': (10, 20, 5),
            'd2.8xlarge': (5, 20, 5),
            'm4.4xlarge': (10, 20, 5),
            'm4.10xlarge': (5, 20, 5)
        }
        limits = {}
        for i_type in self._instance_types():
            key = 'Running On-Demand {t} instances'.format(
                t=i_type)
            lim = default_limits[0]
            if i_type in special_limits:
                lim = special_limits[i_type][0]
            limits[key] = AwsLimit(
                key,
                self,
                lim,
                self.warning_threshold,
                self.critical_threshold,
                limit_type='On-Demand instances',
                limit_subtype=i_type,
                ta_limit_name='On-Demand instances - %s' % i_type
            )
        # limit for ALL running On-Demand instances
        key = 'Running On-Demand EC2 instances'
        limits[key] = AwsLimit(
            key,
            self,
            default_limits[0],
            self.warning_threshold,
            self.critical_threshold,
            limit_type='On-Demand instances',
        )
        return limits

    def _find_usage_networking_sgs(self):
        """calculate usage for VPC-related things"""
        logger.debug("Getting usage for EC2 VPC resources")
        sgs_per_vpc = defaultdict(int)
        rules_per_sg = defaultdict(int)
        for sg in self.resource_conn.security_groups.all():
            if sg.vpc_id is not None:
                sgs_per_vpc[sg.vpc_id] += 1
                rules_per_sg[sg.id] = len(sg.ip_permissions)
        # set usage
        for vpc_id, count in sgs_per_vpc.items():
            self.limits['Security groups per VPC']._add_current_usage(
                count,
                aws_type='AWS::EC2::VPC',
                resource_id=vpc_id,
            )
        for sg_id, count in rules_per_sg.items():
            self.limits['Rules per VPC security group']._add_current_usage(
                count,
                aws_type='AWS::EC2::SecurityGroupRule',
                resource_id=sg_id,
            )

    def _find_usage_networking_eips(self):
        logger.debug("Getting usage for EC2 EIPs")
        vpc_addrs = self.resource_conn.vpc_addresses.all()
        self.limits['VPC Elastic IP addresses (EIPs)']._add_current_usage(
            sum(1 for a in vpc_addrs if a.domain == 'vpc'),
            aws_type='AWS::EC2::EIP',
        )
        # the EC2 limits screen calls this 'EC2-Classic Elastic IPs'
        # but Trusted Advisor just calls it 'Elastic IP addresses (EIPs)'
        classic_addrs = self.resource_conn.classic_addresses.all()
        self.limits['Elastic IP addresses (EIPs)']._add_current_usage(
            sum(1 for a in classic_addrs if a.domain == 'standard'),
            aws_type='AWS::EC2::EIP',
        )

    def _find_usage_networking_eni_sg(self):
        logger.debug("Getting usage for EC2 Network Interfaces")
        ints = self.resource_conn.network_interfaces.all()
        for iface in ints:
            if iface.vpc is None:
                continue
            self.limits['VPC security groups per elastic network '
                        'interface']._add_current_usage(
                            len(iface.groups),
                            aws_type='AWS::EC2::NetworkInterface',
                            resource_id=iface.id,
                        )

    def _get_limits_networking(self):
        """
        Return a dict of VPC-related limits only.
        This method should only be used internally by
        :py:meth:~.get_limits`.

        :rtype: dict
        """
        limits = {}
        limits['Security groups per VPC'] = AwsLimit(
            'Security groups per VPC',
            self,
            500,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::SecurityGroup',
            limit_subtype='AWS::EC2::VPC',
        )
        limits['Rules per VPC security group'] = AwsLimit(
            'Rules per VPC security group',
            self,
            50,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::SecurityGroup',
            limit_subtype='AWS::EC2::VPC',
        )
        limits['VPC Elastic IP addresses (EIPs)'] = AwsLimit(
            'VPC Elastic IP addresses (EIPs)',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::EIP',
            limit_subtype='AWS::EC2::VPC',
            ta_service_name='VPC'  # TA shows this as VPC not EC2
        )
        # the EC2 limits screen calls this 'EC2-Classic Elastic IPs'
        # but Trusted Advisor just calls it 'Elastic IP addresses (EIPs)'
        limits['Elastic IP addresses (EIPs)'] = AwsLimit(
            'Elastic IP addresses (EIPs)',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::EIP',
        )
        limits['VPC security groups per elastic network interface'] = AwsLimit(
            'VPC security groups per elastic network interface',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::SecurityGroup',
            limit_subtype='AWS::EC2::NetworkInterface',
        )
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
            "ec2:DescribeAccountAttributes",
            "ec2:DescribeAddresses",
            "ec2:DescribeInstances",
            "ec2:DescribeInternetGateways",
            "ec2:DescribeNetworkAcls",
            "ec2:DescribeNetworkInterfaces",
            "ec2:DescribeReservedInstances",
            "ec2:DescribeRouteTables",
            "ec2:DescribeSecurityGroups",
            "ec2:DescribeSnapshots",
            "ec2:DescribeSubnets",
            "ec2:DescribeVolumes",
            "ec2:DescribeVpcs",
        ]

    def _instance_types(self):
        """
        Return a list of all known EC2 instance types

        :returns: list of all valid known EC2 instance types
        :rtype: list
        """
        GENERAL_TYPES = [
            't2.nano',
            't2.micro',
            't2.small',
            't2.medium',
            't2.large',
            'm3.medium',
            'm3.large',
            'm3.xlarge',
            'm3.2xlarge',
            'm4.large',
            'm4.xlarge',
            'm4.2xlarge',
            'm4.4xlarge',
            'm4.10xlarge'
        ]

        PREV_GENERAL_TYPES = [
            't1.micro',
            'm1.small',
            'm1.medium',
            'm1.large',
            'm1.xlarge',
        ]

        MEMORY_TYPES = [
            'r3.large',
            'r3.xlarge',
            'r3.2xlarge',
            'r3.4xlarge',
            'r3.8xlarge',
        ]

        PREV_MEMORY_TYPES = [
            'm2.xlarge',
            'm2.2xlarge',
            'm2.4xlarge',
            'cr1.8xlarge',
        ]

        COMPUTE_TYPES = [
            'c3.large',
            'c3.xlarge',
            'c3.2xlarge',
            'c3.4xlarge',
            'c3.8xlarge',
            'c4.large',
            'c4.xlarge',
            'c4.2xlarge',
            'c4.4xlarge',
            'c4.8xlarge',
        ]

        PREV_COMPUTE_TYPES = [
            'c1.medium',
            'c1.xlarge',
            'cc2.8xlarge',
        ]

        STORAGE_TYPES = [
            'i2.xlarge',
            'i2.2xlarge',
            'i2.4xlarge',
            'i2.8xlarge',
        ]

        PREV_STORAGE_TYPES = [
            'hi1.4xlarge',
            'hs1.8xlarge',
        ]

        DENSE_STORAGE_TYPES = [
            'd2.xlarge',
            'd2.2xlarge',
            'd2.4xlarge',
            'd2.8xlarge',
        ]

        GPU_TYPES = [
            'g2.2xlarge',
            'g2.8xlarge',
        ]

        PREV_GPU_TYPES = [
            'cg1.4xlarge',
        ]

        return (
            GENERAL_TYPES +
            PREV_GENERAL_TYPES +
            MEMORY_TYPES +
            PREV_MEMORY_TYPES +
            COMPUTE_TYPES +
            PREV_COMPUTE_TYPES +
            STORAGE_TYPES +
            PREV_STORAGE_TYPES +
            DENSE_STORAGE_TYPES +
            GPU_TYPES +
            PREV_GPU_TYPES
        )
