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
import logging
from collections import defaultdict
from copy import deepcopy
from .base import _AwsService
from ..limit import _AwsLimit
logger = logging.getLogger(__name__)


class _Ec2Service(_AwsService):

    service_name = 'EC2'

    def connect(self):
        if self.conn is None:
            logger.debug("Connecting to EC2")
            self.conn = boto.connect_ec2()
            logger.info("Connected to EC2")

    def find_usage(self):
        """
        Determine the current usage for each limit of this service,
        and update the ``current_usage`` property of each corresponding
        :py:class:`~._AwsLimit` instance.
        """
        logger.debug("Checking usage for service {n}".format(
            n=self.service_name))
        self.connect()
        self._find_usage_instances()
        self._find_usage_ebs()
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
                for i_type, count in inst_usage[az].iteritems():
                    ondemand_usage[i_type] += count
                continue
            # else we have reservations for this AZ
            for i_type, count in inst_usage[az].iteritems():
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
        for i_type, usage in ondemand_usage.iteritems():
            key = 'Running On-Demand {t} instances'.format(
                t=i_type)
            self.limits[key]._set_current_usage(usage)
            total_instances += usage
        # limit for ALL On-Demand EC2 instances
        key = 'Running On-Demand EC2 instances'
        self.limits[key]._set_current_usage(total_instances)

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
        res = self.conn.get_all_reserved_instances()
        for x in res:
            if x.state != 'active':
                logger.debug("Skipping ReservedInstance {i} with state "
                             "{s}".format(i=x.id, s=x.state))
                continue
            if x.availability_zone not in az_to_res:
                az_to_res[x.availability_zone] = deepcopy(reservations)
            az_to_res[x.availability_zone][x.instance_type] += x.instance_count
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
        ondemand = {k: 0 for k in self._instance_types()}
        az_to_inst = {}
        logger.debug("Getting usage for on-demand instances")
        for res in self.conn.get_all_reservations():
            for inst in res.instances:
                if inst.spot_instance_request_id:
                    logger.warning("Spot instance found ({i}); awslimitchecker "
                                   "does not yet support spot "
                                   "instances.".format(i=inst.id))
                    continue
                if inst.placement not in az_to_inst:
                    az_to_inst[inst.placement] = deepcopy(ondemand)
                try:
                    az_to_inst[inst.placement][inst.instance_type] += 1
                except KeyError:
                    logger.error("ERROR - unknown instance type '{t}'; not "
                                 "counting".format(t=inst.instance_type))
        return az_to_inst

    def _find_usage_ebs(self):
        """calculate usage for all EBS limits and update Limits"""
        piops = 0
        piops_gb = 0
        gp_gb = 0
        mag_gb = 0
        logger.debug("Getting usage for EBS volumes")
        for vol in self.conn.get_all_volumes():
            if vol.type == 'io1':
                piops_gb += vol.size
                piops += vol.iops
            elif vol.type == 'gp2':
                gp_gb += vol.size
            elif vol.type == 'standard':
                mag_gb += vol.size
            else:
                logger.error("ERROR - unknown volume type '{t}' for volume {i};"
                             " not counting".format(t=vol.type, i=vol.id))
        self.limits['Provisioned IOPS']._set_current_usage(piops)
        self.limits['Provisioned IOPS (SSD) volume storage '
                    '(TiB)']._set_current_usage(piops_gb / 1000.0)
        self.limits['General Purpose (SSD) volume storage '
                    '(TiB)']._set_current_usage(gp_gb / 1000.0)
        self.limits['Magnetic volume storage '
                    '(TiB)']._set_current_usage(mag_gb / 1000.0)

    def get_limits(self):
        """
        Return all known limits for this service, as a dict of their names
        to :py:class:`~._AwsLimit` objects.

        :returns: dict of limit names to :py:class:`~._AwsLimit` objects
        :rtype: dict
        """
        if self.limits != {}:
            return self.limits
        limits = {}
        limits.update(self._get_limits_instances())
        limits.update(self._get_limits_ebs())
        return limits

    def _get_limits_ebs(self):
        """
        Return a dict of EBS-related limits only.
        This method should only be used internally by
        :py:meth:~.get_limits`.

        :rtype: dict
        """
        limits = {}
        limits['Provisioned IOPS'] = _AwsLimit(
            'Provisioned IOPS',
            self.service_name,
            40000,
            limit_type='IOPS',
            limit_subtype='Provisioned IOPS',
        )
        limits['Provisioned IOPS (SSD) volume storage (TiB)'] = _AwsLimit(
            'Provisioned IOPS (SSD) volume storage (TiB)',
            self.service_name,
            20,
            limit_type='volume storage (TiB)',
            limit_subtype='Provisioned IOPS (SSD)',
        )
        limits['General Purpose (SSD) volume storage (TiB)'] = _AwsLimit(
            'General Purpose (SSD) volume storage (TiB)',
            self.service_name,
            20,
            limit_type='volume storage (TiB)',
            limit_subtype='General Purpose (SSD)',
        )
        limits['Magnetic volume storage (TiB)'] = _AwsLimit(
            'Magnetic volume storage (TiB)',
            self.service_name,
            20,
            limit_type='volume storage (TiB)',
            limit_subtype='Magnetic',
        )
        return limits

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
        }
        limits = {}
        for i_type in self._instance_types():
            key = 'Running On-Demand {t} instances'.format(
                t=i_type)
            lim = default_limits[0]
            if i_type in special_limits:
                lim = special_limits[i_type][0]
            limits[key] = _AwsLimit(
                key,
                self.service_name,
                lim,
                limit_type='On-Demand instances',
                limit_subtype=i_type
            )
        # limit for ALL running On-Demand instances
        key = 'Running On-Demand EC2 instances'
        limits[key] = _AwsLimit(
            key,
            self.service_name,
            default_limits[0],
            limit_type='On-Demand instances',
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
            "ec2:DescribeInstances",
            "ec2:DescribeReservedInstances",
        ]

    def _instance_types(self):
        """
        Return a list of all known EC2 instance types

        :returns: list of all valid known EC2 instance types
        :rtype: list
        """
        GENERAL_TYPES = [
            't2.micro',
            't2.small',
            't2.medium',
            'm3.medium',
            'm3.large',
            'm3.xlarge',
            'm3.2xlarge',
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
