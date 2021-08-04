"""
awslimitchecker/services/ec2.py

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
import os
import logging
from collections import defaultdict
from copy import deepcopy

import botocore

from .base import _AwsService
from ..limit import AwsLimit

logger = logging.getLogger(__name__)

RI_NO_AZ = 'xxREGIONAL_BENEFIT-NO_AZxx'


class _Ec2Service(_AwsService):

    service_name = 'EC2'
    api_name = 'ec2'
    quotas_service_code = 'ec2'

    #: Mapping of lower-case instance family character (instance type first
    #: character) to limit name for that family.
    instance_family_to_limit_name = {
        'f': 'Running On-Demand All F instances',
        'g': 'Running On-Demand All G instances',
        'p': 'Running On-Demand All P instances',
        'x': 'Running On-Demand All X instances'
    }

    #: Mapping of lower-case instance family character to Service Quotas
    #: quota name for that family.
    instance_family_to_quota_name = {
        'f': 'Running On-Demand F instances',
        'g': 'Running On-Demand G instances',
        'p': 'Running On-Demand P instances',
        'x': 'Running On-Demand X instances'
    }

    #: Name of default limit for all other (standard) instance families.
    default_limit_name = 'Running On-Demand All Standard ' \
                         '(A, C, D, H, I, M, R, T, Z) instances'

    #: Name of default Service Quota for all other (standard) families.
    default_quota_name = 'Running On-Demand Standard ' \
                         '(A, C, D, H, I, M, R, T, Z) instances'

    #: List of instance types that aren't exposed via Service Quotas
    no_quotas_types = [
        'c5d.12xlarge',
        'c5d.24xlarge',
        'c5d.metal',
        'cc1.4xlarge',
        'cg1.4xlarge',
        'cr1.8xlarge',
        'g4dn.metal',
        'hi1.4xlarge',
        'hs1.8xlarge',
        'm5dn.metal',
        'm5n.metal',
        'r5dn.metal',
        'r5n.metal',
        'u-18tb1.metal',
        'u-24tb1.metal'
    ]

    instance_family_to_spot_limit_name = {
        'F': 'All F Spot Instance Requests',
        'G': 'All G Spot Instance Requests',
        'Inf': 'All Inf Spot Instance Requests',
        'P': 'All P Spot Instance Requests',
        'X': 'All X Spot Instance Requests',
        'Standard': 'All Standard (A, C, D, H, I, M, R, T, Z)'
                    ' Spot Instance Requests'
    }

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
        if self._use_vcpu_limits:
            self._find_usage_instances_vcpu()
        else:
            self._find_usage_instances_nonvcpu()
        self._find_usage_networking_sgs()
        self._find_usage_networking_eips()
        self._find_usage_networking_eni_sg()
        self._find_usage_spot_instances()
        self._find_usage_spot_fleets()
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_instances_nonvcpu(self):
        """calculate On-Demand instance usage for all types and update Limits"""
        # update our limits with usage
        inst_usage = self._instance_usage()
        res_usage = self._get_reserved_instance_count()
        logger.debug('Reserved instance count: %s', res_usage)
        total_ris = 0
        running_ris = 0
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
                total_ris += res_usage[az][i_type]
                if count < res_usage[az][i_type]:
                    running_ris += count
                else:
                    running_ris += res_usage[az][i_type]
                if od < 0:
                    # we have unused reservations
                    continue
                ondemand_usage[i_type] += od
        logger.debug(
            'Found %d total RIs and %d running/used RIs',
            total_ris, running_ris
        )
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

    def _find_usage_instances_vcpu(self):
        res_usage = self._get_reserved_instance_count()
        logger.debug('Reserved instance count: %s', res_usage)
        usage = self._instance_usage_vcpu(res_usage)
        limit_values = defaultdict(int)
        for i_family, count in usage.items():
            limname = self.instance_family_to_limit_name.get(
                i_family, self.default_limit_name
            )
            limit_values[limname] += count
        for lname in list(
            self.instance_family_to_limit_name.values()
        ) + [self.default_limit_name]:
            if lname not in limit_values:
                limit_values[lname] = 0
        for limname, count in limit_values.items():
            self.limits[limname]._add_current_usage(
                count,
                aws_type='AWS::EC2::Instance',
            )

    def _find_usage_spot_instances(self):
        """calculate spot instance request usage and update Limits"""
        logger.debug('Getting spot instance request usage')
        for key in self.instance_family_to_spot_limit_name.keys():
            self.limits[
                self.instance_family_to_spot_limit_name[key]
            ]._add_current_usage(
                self._get_cloudwatch_usage_latest(
                    [
                        {'Name': 'Type', 'Value': 'Resource'},
                        {'Name': 'Resource', 'Value': 'vCPU'},
                        {'Name': 'Service', 'Value': 'EC2'},
                        {'Name': 'Class', 'Value': '{}/Spot'.format(key)},
                    ],
                    period=300
                )
            )

    def _find_usage_spot_fleets(self):
        """calculate spot fleet request usage and update Limits"""
        logger.debug('Getting spot fleet request usage')
        try:
            res = self.conn.describe_spot_fleet_requests()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'UnsupportedOperation':
                return
            raise
        if 'NextToken' in res:
            logger.error('Error: describe_spot_fleet_requests() response '
                         'includes pagination token, but pagination not '
                         'configured in awslimitchecker.')
        active_fleets = 0
        total_target_cap = 0
        lim_cap_per_fleet = self.limits['Max target capacity per spot fleet']
        lim_launch_specs = self.limits[
            'Max launch specifications per spot fleet']
        for fleet in res['SpotFleetRequestConfigs']:
            _id = fleet['SpotFleetRequestId']
            if fleet['SpotFleetRequestState'] != 'active':
                logger.debug('Skipping spot fleet request %s in state %s',
                             _id, fleet['SpotFleetRequestState'])
                continue
            active_fleets += 1
            cap = fleet['SpotFleetRequestConfig']['TargetCapacity']
            launch_specs = len(
                fleet['SpotFleetRequestConfig'].get('LaunchSpecifications', []))
            total_target_cap += cap
            lim_cap_per_fleet._add_current_usage(
                cap, resource_id=_id, aws_type='AWS::EC2::SpotFleetRequest')
            lim_launch_specs._add_current_usage(
                launch_specs, resource_id=_id,
                aws_type='AWS::EC2::SpotFleetRequest')
        self.limits['Max active spot fleets per region']._add_current_usage(
            active_fleets, aws_type='AWS::EC2::SpotFleetRequest'
        )
        self.limits['Max target capacity for all spot '
                    'fleets in region']._add_current_usage(
            total_target_cap, aws_type='AWS::EC2::SpotFleetRequest'
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
            if 'AvailabilityZone' not in x:
                # "Regional Benefit" AZ-less reservation
                x['AvailabilityZone'] = RI_NO_AZ
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
                logger.info("Spot instance found (%s); skipping from "
                            "Running On-Demand Instances count", inst.id)
                continue
            if inst.placement.get('Tenancy', 'default') != 'default':
                logger.info(
                    'Skipping instance %s with Tenancy %s',
                    inst.id, inst.placement['Tenancy']
                )
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

    def _instance_usage_vcpu(self, ris):
        """
        Find counts of currently-running EC2 Instance vCPUs
        (On-Demand or Reserved) by instance family. Return as a dict of
        instance family letter to count.

        :param ris: nested dict of reserved instances, as returned by
          :py:meth:`~._get_reserved_instance_count`
        :type ris: dict
        :rtype: dict
        """
        inst_counts = defaultdict(int)
        logger.debug("Getting usage for on-demand instances (vCPU limit)")
        for inst in self.resource_conn.instances.all():
            if inst.spot_instance_request_id:
                logger.info("Spot instance found (%s); skipping from "
                            "Running On-Demand Instances count", inst.id)
                continue
            if inst.placement.get('Tenancy', 'default') != 'default':
                logger.info(
                    'Skipping instance %s with Tenancy %s',
                    inst.id, inst.placement['Tenancy']
                )
                continue
            if inst.state['Name'] in ['stopped', 'terminated']:
                logger.debug("Ignoring instance %s in state %s", inst.id,
                             inst.state['Name'])
                continue
            az = inst.placement['AvailabilityZone']
            itype = inst.instance_type
            if ris.get(az, {}).get(itype, 0) > 0:
                logger.debug(
                    'Using RI for %s: %s in %s', inst.id, itype, az
                )
                ris[az][itype] -= 1
                continue
            inst_counts[inst.instance_type[0]] += (
                inst.cpu_options['CoreCount'] * inst.cpu_options[
                    'ThreadsPerCore'
                ]
            )
        return inst_counts

    @property
    def _use_vcpu_limits(self):
        """
        Return whether or not to use the new vCPU-based limits.

        :return: whether to use vCPU-based limits (True) or older
          per-instance-type limits (False)
        :rtype: bool
        """
        if 'USE_VCPU_LIMITS' in os.environ:
            if os.environ['USE_VCPU_LIMITS'] == 'true':
                logger.debug(
                    'Using vCPU-based EC2 limits due to USE_VCPU_LIMITS=true '
                    'in environment.'
                )
                return True
            logger.debug(
                'Using vCPU-based EC2 limits due to USE_VCPU_LIMITS in '
                'environment and set to something other than "true".'
            )
            return False
        oldconn = self.conn
        self.connect()
        region_name = self.conn._client_config.region_name
        self.conn = oldconn
        if region_name.startswith('cn-') or region_name.startswith('us-gov-'):
            logger.debug(
                'Using non-vCPU EC2 limits due to region name: %s', region_name
            )
            return False
        return True

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
        if self._use_vcpu_limits:
            limits.update(self._get_limits_instances_vcpu())
        else:
            limits.update(self._get_limits_instances_nonvcpu())
        limits.update(self._get_limits_networking())
        limits.update(self._get_limits_spot())
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
            if lname in self.limits:
                if int(val) == 0:
                    continue
                self.limits[lname]._set_api_limit(int(val))
        logger.debug("Done setting limits from API")

    def _get_limits_instances_nonvcpu(self):
        """
        Return a dict of limits for EC2 instances only, for regions using
        non-vCPU-based (old-style) On Demand Instances limits.
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
            'c5.4xlarge': (10, 20, 5),
            'c5.9xlarge': (5, 20, 5),
            'c5.18xlarge': (5, 20, 5),
            'cg1.4xlarge': (2, 20, 5),
            'cr1.8xlarge': (2, 20, 5),
            'd2.4xlarge': (10, 20, 5),
            'd2.8xlarge': (5, 20, 5),
            'g2.2xlarge': (5, 20, 5),
            'g2.8xlarge': (2, 20, 5),
            'g3.4xlarge': (1, 20, 5),
            'g3.8xlarge': (1, 20, 5),
            'g3.16xlarge': (1, 20, 5),
            'h1.8xlarge': (10, 20, 5),
            'h1.16xlarge': (5, 20, 5),
            'hi1.4xlarge': (2, 20, 5),
            'hs1.8xlarge': (2, 20, 0),
            'i2.2xlarge': (8, 20, 0),
            'i2.4xlarge': (4, 20, 0),
            'i2.8xlarge': (2, 20, 0),
            'i2.xlarge': (8, 20, 0),
            'i3.2xlarge': (2, 20, 0),
            'i3.4xlarge': (2, 20, 0),
            'i3.8xlarge': (2, 20, 0),
            'i3.16xlarge': (2, 20, 0),
            'i3.large': (2, 20, 0),
            'i3.xlarge': (2, 20, 0),
            'm4.4xlarge': (10, 20, 5),
            'm4.10xlarge': (5, 20, 5),
            'm4.16xlarge': (5, 20, 5),
            'm5.4xlarge': (10, 20, 5),
            'm5.12xlarge': (5, 20, 5),
            'm5.24xlarge': (5, 20, 5),
            'p2.8xlarge': (1, 20, 5),
            'p2.16xlarge': (1, 20, 5),
            'p2.xlarge': (1, 20, 5),
            'p3.2xlarge': (1, 20, 5),
            'p3.8xlarge': (1, 20, 5),
            'p3.16xlarge': (1, 20, 5),
            'p3dn.24xlarge': (1, 20, 5),
            'r3.4xlarge': (10, 20, 5),
            'r3.8xlarge': (5, 20, 5),
            'r4.4xlarge': (10, 20, 5),
            'r4.8xlarge': (5, 20, 5),
            'r4.16xlarge': (1, 20, 5),
        }
        limits = {}
        for i_type in self._instance_types():
            key = 'Running On-Demand {t} instances'.format(
                t=i_type)
            lim = default_limits[0]
            if i_type in special_limits:
                lim = special_limits[i_type][0]
            quotas_name = 'Running On-Demand %s instances' % i_type
            if i_type in self.no_quotas_types:
                quotas_name = None
            limits[key] = AwsLimit(
                key,
                self,
                lim,
                self.warning_threshold,
                self.critical_threshold,
                limit_type='On-Demand instances',
                limit_subtype=i_type,
                ta_limit_name='On-Demand instances - %s' % i_type,
                quotas_name=quotas_name
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
            quotas_name='Total running On-Demand instances'
        )
        return limits

    def _get_limits_instances_vcpu(self):
        """
        Return a dict of limits for EC2 instances only, for regions using
        vCPU-based (new-style) On Demand Instances limits.
        This method should only be used internally by
        :py:meth:~.get_limits`.

        :rtype: dict
        """
        limits = {}
        iftln = self.instance_family_to_limit_name
        for key in iftln.keys():
            limits[iftln[key]] = AwsLimit(
                iftln[key],
                self,
                128,
                self.warning_threshold,
                self.critical_threshold,
                limit_type='On-Demand instances',
                limit_subtype=key.upper(),
                quotas_name=self.instance_family_to_quota_name[key]
            )
        limits[self.default_limit_name] = AwsLimit(
            self.default_limit_name,
            self,
            1152,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='On-Demand instances',
            limit_subtype='Standard',
            quotas_name=self.default_quota_name
        )
        return limits

    def _get_limits_spot(self):
        """
        Return a dict of limits for spot requests only.
        This method should only be used internally by
        :py:meth:~.get_limits`.

        :rtype: dict
        """
        limits = {}

        limits['All F Spot Instance Requests'] = AwsLimit(
            'All F Spot Instance Requests',
            self,
            11,
            self.warning_threshold,
            self.critical_threshold,
            limit_subtype='F'
        )
        limits['All G Spot Instance Requests'] = AwsLimit(
            'All G Spot Instance Requests',
            self,
            11,
            self.warning_threshold,
            self.critical_threshold,
            limit_subtype='G'
        )
        limits['All Inf Spot Instance Requests'] = AwsLimit(
            'All Inf Spot Instance Requests',
            self,
            64,
            self.warning_threshold,
            self.critical_threshold,
            limit_subtype='Inf'
        )
        limits['All P Spot Instance Requests'] = AwsLimit(
            'All P Spot Instance Requests',
            self,
            16,
            self.warning_threshold,
            self.critical_threshold,
            limit_subtype='P'
        )
        limits['All X Spot Instance Requests'] = AwsLimit(
            'All X Spot Instance Requests',
            self,
            21,
            self.warning_threshold,
            self.critical_threshold,
            limit_subtype='X'
        )
        limits[
            'All Standard (A, C, D, H, I, M, R, T, Z) Spot Instance Requests'
        ] = AwsLimit(
            'All Standard (A, C, D, H, I, M, R, T, Z) Spot Instance Requests',
            self,
            1440,
            self.warning_threshold,
            self.critical_threshold,
            limit_subtype='Standard'
        )

        limits['Max active spot fleets per region'] = AwsLimit(
            'Max active spot fleets per region',
            self,
            1000,
            self.warning_threshold,
            self.critical_threshold,
        )

        limits['Max launch specifications per spot fleet'] = AwsLimit(
            'Max launch specifications per spot fleet',
            self,
            50,
            self.warning_threshold,
            self.critical_threshold,
        )

        limits['Max target capacity per spot fleet'] = AwsLimit(
            'Max target capacity per spot fleet',
            self,
            3000,
            self.warning_threshold,
            self.critical_threshold
        )

        limits['Max target capacity for all spot fleets in region'] = AwsLimit(
            'Max target capacity for all spot fleets in region',
            self,
            5000,
            self.warning_threshold,
            self.critical_threshold
        )
        return limits

    def _find_usage_networking_sgs(self):
        """calculate usage for VPC-related things"""
        logger.debug("Getting usage for EC2 VPC resources")
        sg_count = 0
        rules_per_sg = defaultdict(int)
        for sg in self.resource_conn.security_groups.filter(
            Filters=[{'Name': 'owner-id', 'Values': [self.current_account_id]}]
        ):
            if sg.vpc_id is None:
                continue
            sg_count += 1
            """
            see: https://github.com/jantman/awslimitchecker/issues/431

            The value for each of ingress and egress is the count of all
            PrefixListIds in all rules, plus the count of all
            UserIdGroupPairs in all rules, plus the maximum of:
              the count of all IpRanges in all rules
                 -or-
              the count of all Ipv6Ranges in all rules

            The limit that we alert on is the maximum of those values for
            ingress and egress.

            In short, behind the scenes, there are four firewall rulesets
            per SG: (IPv4|IPv6) (ingress|egress)
            Each can have a maximum of <limit> entries. PrefixListIds and
            UserIdGroupPairs count towards both IPv4 and IPv6.
            """
            counts = []
            for perm in [sg.ip_permissions, sg.ip_permissions_egress]:
                counts.append(
                    max(
                        sum([len(x.get('IpRanges', [])) for x in perm]),
                        sum([len(x.get('Ipv6Ranges', [])) for x in perm])
                    ) +
                    sum([len(x.get('PrefixListIds', [])) for x in perm]) +
                    sum([len(x.get('UserIdGroupPairs', [])) for x in perm])
                )
            rules_per_sg[sg.id] = max(counts)
        # set usage
        self.limits['VPC security groups per Region']._add_current_usage(
            sg_count,
            aws_type='AWS::EC2::SecurityGroup',
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
            self.limits[
                'VPC security groups per elastic network interface'
            ]._add_current_usage(
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
        limits['VPC security groups per Region'] = AwsLimit(
            'VPC security groups per Region',
            self,
            2500,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::SecurityGroup',
            limit_subtype='AWS::EC2::VPC',
            quotas_name='VPC security groups per Region',
            quotas_service_code='vpc'
        )
        limits['Rules per VPC security group'] = AwsLimit(
            'Rules per VPC security group',
            self,
            60,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::SecurityGroup',
            limit_subtype='AWS::EC2::VPC',
            quotas_name='Inbound or outbound rules per security group',
            quotas_service_code='vpc'
        )
        limits['VPC Elastic IP addresses (EIPs)'] = AwsLimit(
            'VPC Elastic IP addresses (EIPs)',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::EIP',
            limit_subtype='AWS::EC2::VPC',
            ta_service_name='VPC',  # TA shows this as VPC not EC2
            quotas_name='EC2-VPC Elastic IPs'
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
            quotas_name='EC2-Classic Elastic IPs'
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
            "ec2:DescribeSpotDatafeedSubscription",
            "ec2:DescribeSpotFleetInstances",
            "ec2:DescribeSpotFleetRequestHistory",
            "ec2:DescribeSpotFleetRequests",
            "ec2:DescribeSpotPriceHistory",
            "ec2:DescribeSubnets",
            "ec2:DescribeVolumes",
            "ec2:DescribeVpcs",
            "cloudwatch:GetMetricData"
        ]

    def _instance_types(self):
        """
        Return a list of all known EC2 instance types

        :returns: list of all valid known EC2 instance types
        :rtype: list
        """
        GENERAL_TYPES = [
            'a1.2xlarge',
            'a1.4xlarge',
            'a1.large',
            'a1.medium',
            'a1.metal',
            'a1.xlarge',
            'm3.2xlarge',
            'm3.large',
            'm3.medium',
            'm3.xlarge',
            'm4.2xlarge',
            'm4.4xlarge',
            'm4.10xlarge',
            'm4.16xlarge',
            'm4.large',
            'm4.xlarge',
            'm5.2xlarge',
            'm5.4xlarge',
            'm5.8xlarge',
            'm5.12xlarge',
            'm5.16xlarge',
            'm5.24xlarge',
            'm5.large',
            'm5.metal',
            'm5.xlarge',
            'm5a.2xlarge',
            'm5a.4xlarge',
            'm5a.8xlarge',
            'm5a.12xlarge',
            'm5a.16xlarge',
            'm5a.24xlarge',
            'm5a.large',
            'm5a.xlarge',
            'm5ad.2xlarge',
            'm5ad.4xlarge',
            'm5ad.8xlarge',
            'm5ad.12xlarge',
            'm5ad.16xlarge',
            'm5ad.24xlarge',
            'm5ad.large',
            'm5ad.xlarge',
            'm5d.2xlarge',
            'm5d.4xlarge',
            'm5d.8xlarge',
            'm5d.12xlarge',
            'm5d.16xlarge',
            'm5d.24xlarge',
            'm5d.large',
            'm5d.metal',
            'm5d.xlarge',
            'm5dn.2xlarge',
            'm5dn.4xlarge',
            'm5dn.8xlarge',
            'm5dn.12xlarge',
            'm5dn.16xlarge',
            'm5dn.24xlarge',
            'm5dn.large',
            'm5dn.metal',
            'm5dn.xlarge',
            'm5n.2xlarge',
            'm5n.4xlarge',
            'm5n.8xlarge',
            'm5n.12xlarge',
            'm5n.16xlarge',
            'm5n.24xlarge',
            'm5n.large',
            'm5n.metal',
            'm5n.xlarge',
            't2.2xlarge',
            't2.large',
            't2.medium',
            't2.micro',
            't2.nano',
            't2.small',
            't2.xlarge',
            't3.2xlarge',
            't3.large',
            't3.medium',
            't3.micro',
            't3.nano',
            't3.small',
            't3.xlarge',
            't3a.2xlarge',
            't3a.large',
            't3a.medium',
            't3a.micro',
            't3a.nano',
            't3a.small',
            't3a.xlarge',
        ]

        PREV_GENERAL_TYPES = [
            't1.micro',
            'm1.small',
            'm1.medium',
            'm1.large',
            'm1.xlarge',
        ]

        MEMORY_TYPES = [
            'r3.2xlarge',
            'r3.4xlarge',
            'r3.8xlarge',
            'r3.large',
            'r3.xlarge',
            'r4.2xlarge',
            'r4.4xlarge',
            'r4.8xlarge',
            'r4.16xlarge',
            'r4.large',
            'r4.xlarge',
            'r5.2xlarge',
            'r5.4xlarge',
            'r5.8xlarge',
            'r5.12xlarge',
            'r5.16xlarge',
            'r5.24xlarge',
            'r5.large',
            'r5.metal',
            'r5.xlarge',
            'r5a.2xlarge',
            'r5a.4xlarge',
            'r5a.8xlarge',
            'r5a.12xlarge',
            'r5a.16xlarge',
            'r5a.24xlarge',
            'r5a.large',
            'r5a.xlarge',
            'r5ad.2xlarge',
            'r5ad.4xlarge',
            'r5ad.8xlarge',
            'r5ad.12xlarge',
            'r5ad.16xlarge',
            'r5ad.24xlarge',
            'r5ad.large',
            'r5ad.xlarge',
            'r5d.2xlarge',
            'r5d.4xlarge',
            'r5d.8xlarge',
            'r5d.12xlarge',
            'r5d.16xlarge',
            'r5d.24xlarge',
            'r5d.large',
            'r5d.metal',
            'r5d.xlarge',
            'r5dn.2xlarge',
            'r5dn.4xlarge',
            'r5dn.8xlarge',
            'r5dn.12xlarge',
            'r5dn.16xlarge',
            'r5dn.24xlarge',
            'r5dn.large',
            'r5dn.metal',
            'r5dn.xlarge',
            'r5n.2xlarge',
            'r5n.4xlarge',
            'r5n.8xlarge',
            'r5n.12xlarge',
            'r5n.16xlarge',
            'r5n.24xlarge',
            'r5n.large',
            'r5n.metal',
            'r5n.xlarge',
            'u-18tb1.metal',
            'u-24tb1.metal',
            'x1.16xlarge',
            'x1.32xlarge',
            'x1e.2xlarge',
            'x1e.4xlarge',
            'x1e.8xlarge',
            'x1e.16xlarge',
            'x1e.32xlarge',
            'x1e.xlarge',
            'z1d.2xlarge',
            'z1d.3xlarge',
            'z1d.6xlarge',
            'z1d.12xlarge',
            'z1d.large',
            'z1d.xlarge',
        ]

        PREV_MEMORY_TYPES = [
            'm2.xlarge',
            'm2.2xlarge',
            'm2.4xlarge',
            'cr1.8xlarge',
        ]

        COMPUTE_TYPES = [
            'c3.2xlarge',
            'c3.4xlarge',
            'c3.8xlarge',
            'c3.large',
            'c3.xlarge',
            'c4.2xlarge',
            'c4.4xlarge',
            'c4.8xlarge',
            'c4.large',
            'c4.xlarge',
            'c5.2xlarge',
            'c5.4xlarge',
            'c5.9xlarge',
            'c5.12xlarge',
            'c5.18xlarge',
            'c5.24xlarge',
            'c5.large',
            'c5.metal',
            'c5.xlarge',
            'c5d.2xlarge',
            'c5d.4xlarge',
            'c5d.9xlarge',
            'c5d.12xlarge',
            'c5d.18xlarge',
            'c5d.24xlarge',
            'c5d.large',
            'c5d.metal',
            'c5d.xlarge',
            'c5n.2xlarge',
            'c5n.4xlarge',
            'c5n.9xlarge',
            'c5n.18xlarge',
            'c5n.large',
            'c5n.metal',
            'c5n.xlarge',
        ]

        PREV_COMPUTE_TYPES = [
            'c1.medium',
            'c1.xlarge',
            'cc2.8xlarge',
            'cc1.4xlarge',
        ]

        ACCELERATED_COMPUTE_TYPES = [
            'f1.4xlarge',
            'p2.xlarge',
            'p2.8xlarge',
            'p2.16xlarge',
            'p3.16xlarge',
            'p3.2xlarge',
            'p3.8xlarge',
            'p3dn.24xlarge',
        ]

        STORAGE_TYPES = [
            'h1.2xlarge',
            'h1.4xlarge',
            'h1.8xlarge',
            'h1.16xlarge',
            'i2.2xlarge',
            'i2.4xlarge',
            'i2.8xlarge',
            'i2.xlarge',
            'i3.2xlarge',
            'i3.4xlarge',
            'i3.8xlarge',
            'i3.16xlarge',
            'i3.large',
            'i3.metal',
            'i3.xlarge',
            'i3en.2xlarge',
            'i3en.3xlarge',
            'i3en.6xlarge',
            'i3en.12xlarge',
            'i3en.24xlarge',
            'i3en.large',
            'i3en.xlarge',
        ]

        PREV_STORAGE_TYPES = [
            # NOTE hi1.4xlarge is no longer in the instance type listings,
            # but some accounts might still have a limit for it
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
            'g3.4xlarge',
            'g3.8xlarge',
            'g3.16xlarge',
            'g3s.xlarge',
            'g4dn.2xlarge',
            'g4dn.4xlarge',
            'g4dn.8xlarge',
            'g4dn.12xlarge',
            'g4dn.16xlarge',
            'g4dn.metal',
            'g4dn.xlarge',
        ]

        PREV_GPU_TYPES = [
            'cg1.4xlarge',
        ]

        FPGA_TYPES = [
            # note, as of 2016-12-17, these are still in Developer Preview;
            # there isn't a published instance limit yet, so we'll assume
            # it's the default...
            'f1.2xlarge',
            'f1.16xlarge',
        ]

        return (
            GENERAL_TYPES +
            PREV_GENERAL_TYPES +
            MEMORY_TYPES +
            PREV_MEMORY_TYPES +
            COMPUTE_TYPES +
            PREV_COMPUTE_TYPES +
            ACCELERATED_COMPUTE_TYPES +
            STORAGE_TYPES +
            PREV_STORAGE_TYPES +
            DENSE_STORAGE_TYPES +
            GPU_TYPES +
            PREV_GPU_TYPES +
            FPGA_TYPES
        )
