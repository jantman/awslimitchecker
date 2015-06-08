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
        for i_type, usage in ondemand_usage.iteritems():
            key = 'Running On-Demand {t} Instances'.format(
                t=i_type)
            self.limits[key]._set_current_usage(usage)

    def _get_reserved_instance_count(self):
        """
        For each availability zone, get the count of current instance
        reservations of each instance type. Return as a nested
        dict of AZ name to dict of instance type to reservation count.

        :rtype: dict
        """
        reservations = defaultdict(int)
        az_to_res = {}
        res = self.conn.get_all_reserved_instances()
        for x in res:
            if x.state != 'active':
                logger.debug("Skipping ReservedInstance {i} with state "
                             "{s}".format(i=x.id, s=x.status))
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

    def get_limits(self):
        """
        Return all known limits for this service, as a dict of their names
        to :py:class:`~._AwsLimit` objects.

        :returns: dict of limit names to :py:class:`~._AwsLimit` objects
        :rtype: dict
        """
        if self.limits != []:
            return self.limits
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
            key = 'Running On-Demand {t} Instances'.format(
                t=i_type)
            lim = default_limits[0]
            if i_type in special_limits:
                lim = special_limits[i_type][0]
            limits[key] = _AwsLimit(
                key,
                self.service_name,
                lim,
                limit_type='On-Demand Instances',
                limit_subtype=i_type
            )
        return limits

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
