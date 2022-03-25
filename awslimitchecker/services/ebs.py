"""
awslimitchecker/services/ebs.py

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

from .base import _AwsService
from ..limit import AwsLimit
from ..utils import paginate_dict

logger = logging.getLogger(__name__)


def convert_TiB_to_GiB(value, in_unit, out_unit):
    if in_unit != 'None' or out_unit != 'GiB':
        logger.error(
            'ERROR: cannot convert Service Quotas EBS limit value from '
            'units of "%s" to units of "%s"', in_unit, out_unit
        )
        return None
    return value * 1024.0


class _EbsService(_AwsService):

    service_name = 'EBS'
    api_name = 'ec2'
    quotas_service_code = 'ebs'

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
        piops_io1 = 0
        piops_io1_gb = 0
        piops_io2 = 0
        piops_io2_gb = 0
        gp2_gb = 0
        gp3_gb = 0
        mag_gb = 0
        st_gb = 0
        sc_gb = 0
        logger.debug("Getting usage for EBS volumes")
        results = paginate_dict(
            self.conn.describe_volumes,
            alc_marker_path=['NextToken'],
            alc_data_path=['Volumes'],
            alc_marker_param='NextToken'
        )
        for vol in results['Volumes']:
            vols += 1
            if vol['VolumeType'] == 'io1':
                piops_io1_gb += vol['Size']
                piops_io1 += vol['Iops']
            elif vol['VolumeType'] == 'io2':
                piops_io2_gb += vol['Size']
                piops_io2 += vol['Iops']
            elif vol['VolumeType'] == 'gp2':
                gp2_gb += vol['Size']
            elif vol['VolumeType'] == 'gp3':
                gp3_gb += vol['Size']
            elif vol['VolumeType'] == 'standard':
                mag_gb += vol['Size']
            elif vol['VolumeType'] == 'st1':
                st_gb += vol['Size']
            elif vol['VolumeType'] == 'sc1':
                sc_gb += vol['Size']
            else:
                logger.error(
                    "ERROR - unknown volume type '%s' for volume %s;"
                    " not counting",
                    vol['VolumeType'],
                    vol['VolumeId'])
        self.limits['Provisioned IOPS (io1)']._add_current_usage(
            piops_io1,
            aws_type='AWS::EC2::Volume'
        )
        self.limits[
            'Provisioned IOPS SSD (io1) storage (GiB)'
        ]._add_current_usage(
            piops_io1_gb,
            aws_type='AWS::EC2::Volume'
        )
        self.limits['Provisioned IOPS (io2)']._add_current_usage(
            piops_io2,
            aws_type='AWS::EC2::Volume'
        )
        self.limits[
            'Provisioned IOPS SSD (io2) storage (GiB)'
        ]._add_current_usage(
            piops_io2_gb,
            aws_type='AWS::EC2::Volume'
        )
        self.limits[
            'General Purpose (SSD gp2) volume storage (GiB)'
        ]._add_current_usage(
            gp2_gb,
            aws_type='AWS::EC2::Volume'
        )
        self.limits[
            'General Purpose (SSD gp3) volume storage (GiB)'
        ]._add_current_usage(
            gp3_gb,
            aws_type='AWS::EC2::Volume'
        )
        self.limits[
            'Magnetic volume storage (GiB)'
        ]._add_current_usage(
            mag_gb,
            aws_type='AWS::EC2::Volume'
        )
        self.limits[
            'Throughput Optimized (HDD) volume storage (GiB)'
        ]._add_current_usage(
            st_gb,
            aws_type='AWS::EC2::Volume'
        )
        self.limits[
            'Cold (HDD) volume storage (GiB)'
        ]._add_current_usage(
            sc_gb,
            aws_type='AWS::EC2::Volume'
        )
        self.limits['Active volumes']._add_current_usage(
            vols,
            aws_type='AWS::EC2::Volume'
        )

    def _find_usage_snapshots(self):
        """find snapshot usage"""
        logger.debug("Getting usage for EBS snapshots")
        snaps = paginate_dict(
            self.conn.describe_snapshots,
            OwnerIds=['self'],
            alc_marker_path=['NextToken'],
            alc_data_path=['Snapshots'],
            alc_marker_param='NextToken'
        )
        self.limits['Active snapshots']._add_current_usage(
            len(snaps['Snapshots']),
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
        limits['Provisioned IOPS (io1)'] = AwsLimit(
            'Provisioned IOPS (io1)',
            self,
            300000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Volume',
            limit_subtype='io1',
            quotas_name='IOPS for Provisioned IOPS SSD (io1) volumes'
        )
        limits['Provisioned IOPS SSD (io1) storage (GiB)'] = AwsLimit(
            'Provisioned IOPS SSD (io1) storage (GiB)',
            self,
            307200,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Volume',
            limit_subtype='io1',
            quotas_name='Storage for Provisioned IOPS SSD (io1) volumes',
            quotas_unit='GiB',
            quotas_unit_converter=convert_TiB_to_GiB
        )
        limits['Provisioned IOPS (io2)'] = AwsLimit(
            'Provisioned IOPS (io2)',
            self,
            100000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Volume',
            limit_subtype='io2',
            quotas_name='IOPS for Provisioned IOPS SSD (io2) volumes'
        )
        limits['Provisioned IOPS SSD (io2) storage (GiB)'] = AwsLimit(
            'Provisioned IOPS SSD (io2) storage (GiB)',
            self,
            20480,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Volume',
            limit_subtype='io2',
            quotas_name='Storage for Provisioned IOPS SSD (io2) volumes',
            quotas_unit='GiB',
            quotas_unit_converter=convert_TiB_to_GiB
        )
        limits['General Purpose (SSD gp2) volume storage (GiB)'] = AwsLimit(
            'General Purpose (SSD gp2) volume storage (GiB)',
            self,
            307200,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Volume',
            limit_subtype='gp2',
            ta_limit_name='General Purpose SSD (gp2) volume storage (GiB)',
            quotas_name='Storage for General Purpose SSD (gp2) volumes',
            quotas_unit='GiB',
            quotas_unit_converter=convert_TiB_to_GiB
        )
        limits['General Purpose (SSD gp3) volume storage (GiB)'] = AwsLimit(
            'General Purpose (SSD gp3) volume storage (GiB)',
            self,
            307200,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Volume',
            limit_subtype='gp3',
            ta_limit_name='General Purpose SSD (gp3) volume storage (GiB)',
            quotas_name='Storage for General Purpose SSD (gp3) volumes',
            quotas_unit='GiB',
            quotas_unit_converter=convert_TiB_to_GiB
        )
        limits['Magnetic volume storage (GiB)'] = AwsLimit(
            'Magnetic volume storage (GiB)',
            self,
            307200,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Volume',
            limit_subtype='standard',
            ta_limit_name='Magnetic (standard) volume storage (GiB)',
            quotas_name='Storage for Magnetic (standard) volumes',
            quotas_unit='GiB',
            quotas_unit_converter=convert_TiB_to_GiB
        )
        limits['Throughput Optimized (HDD) volume storage (GiB)'] = AwsLimit(
            'Throughput Optimized (HDD) volume storage (GiB)',
            self,
            307200,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Volume',
            limit_subtype='st1',
            quotas_name='Storage for Throughput Optimized HDD (st1) volumes',
            quotas_unit='GiB',
            quotas_unit_converter=convert_TiB_to_GiB
        )
        limits['Cold (HDD) volume storage (GiB)'] = AwsLimit(
            'Cold (HDD) volume storage (GiB)',
            self,
            307200,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::Volume',
            limit_subtype='sc1',
            quotas_name='Storage for Cold HDD (sc1) volumes',
            quotas_unit='GiB',
            quotas_unit_converter=convert_TiB_to_GiB
        )
        limits['Active snapshots'] = AwsLimit(
            'Active snapshots',
            self,
            100000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EC2::VolumeSnapshot',
            quotas_name='Snapshots Per Region'
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
