"""
awslimitchecker/services/ebs.py

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
import boto.ec2
import logging
from .base import _AwsService
from ..limit import AwsLimit
logger = logging.getLogger(__name__)


class _EbsService(_AwsService):

    service_name = 'EBS'

    def connect(self):
        """
        Connect to API if not already connected; set self.conn.
        """
        if self.conn is not None:
            return
        elif self.region:
            self.conn = self.connect_via(boto.ec2)
        else:
            self.conn = boto.connect_ec2()

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
        self._find_usage_ebs()
        self._find_usage_snapshots()
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_ebs(self):
        """calculate usage for all EBS limits and update Limits"""
        vols = 0
        piops = 0
        piops_gb = 0
        gp_gb = 0
        mag_gb = 0
        logger.debug("Getting usage for EBS volumes")
        for vol in self.conn.get_all_volumes():
            vols += 1
            if vol.type == 'io1':
                piops_gb += vol.size
                piops += vol.iops
            elif vol.type == 'gp2':
                gp_gb += vol.size
            elif vol.type == 'standard':
                mag_gb += vol.size
            else:
                logger.error(
                    "ERROR - unknown volume type '%s' for volume %s;"
                    " not counting",
                    vol.type,
                    vol.id)
        self.limits['Provisioned IOPS']._add_current_usage(
            piops,
            aws_type='AWS::EC2::Volume'
        )
        self.limits['Provisioned IOPS (SSD) storage '
                    '(GiB)']._add_current_usage(
                        piops_gb,
                        aws_type='AWS::EC2::Volume'
                    )
        self.limits['General Purpose (SSD) volume storage '
                    '(GiB)']._add_current_usage(
                        gp_gb,
                        aws_type='AWS::EC2::Volume'
                    )
        self.limits['Magnetic volume storage '
                    '(GiB)']._add_current_usage(
                        mag_gb,
                        aws_type='AWS::EC2::Volume'
                    )
        self.limits['Active volumes']._add_current_usage(
            vols,
            aws_type='AWS::EC2::Volume'
        )

    def _find_usage_snapshots(self):
        """find snapshot usage"""
        logger.debug("Getting usage for EBS snapshots")
        snaps = self.conn.get_all_snapshots(owner='self')
        self.limits['Active snapshots']._add_current_usage(
            len(snaps),
            aws_type='AWS::EC2::VolumeSnapshot'
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
        limits.update(self._get_limits_ebs())
        self.limits = limits
        return limits

    def _get_limits_ebs(self):
        """
        Return a dict of EBS-related limits only.
        This method should only be used internally by
        :py:meth:~.get_limits`.

        :rtype: dict
        """
        limits = {}
        limits['Provisioned IOPS'] = AwsLimit(
            'Provisioned IOPS',
            self,
            40000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Volume',
            limit_subtype='io1',
        )
        limits['Provisioned IOPS (SSD) storage (GiB)'] = AwsLimit(
            'Provisioned IOPS (SSD) storage (GiB)',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Volume',
            limit_subtype='io1',
        )
        limits['General Purpose (SSD) volume storage (GiB)'] = AwsLimit(
            'General Purpose (SSD) volume storage (GiB)',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Volume',
            limit_subtype='gp2',
        )
        limits['Magnetic volume storage (GiB)'] = AwsLimit(
            'Magnetic volume storage (GiB)',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Volume',
            limit_subtype='standard',
        )
        limits['Active snapshots'] = AwsLimit(
            'Active snapshots',
            self,
            10000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::VolumeSnapshot',
        )
        limits['Active volumes'] = AwsLimit(
            'Active volumes',
            self,
            5000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Volume',
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
            "ec2:DescribeVolumes",
            "ec2:DescribeSnapshots"
        ]
