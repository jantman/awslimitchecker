"""
awslimitchecker/services/efs.py

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
from botocore.exceptions import EndpointConnectionError, ClientError
from botocore.vendored.requests.exceptions import ConnectTimeout

from .base import _AwsService
from ..limit import AwsLimit
from ..utils import paginate_dict

logger = logging.getLogger(__name__)


class _EfsService(_AwsService):

    service_name = 'EFS'
    api_name = 'efs'  # AWS API name to connect to (boto3.client)

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
        try:
            self._find_usage_filesystems()
        except (EndpointConnectionError, ClientError, ConnectTimeout) as ex:
            logger.warning(
                'Caught exception when trying to use EFS ('
                'perhaps the EFS service is not available in this '
                'region?): %s', ex
            )
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_filesystems(self):
        filesystems = paginate_dict(
            self.conn.describe_file_systems,
            alc_marker_path=['NextMarker'],
            alc_data_path=['FileSystems'],
            alc_marker_param='Marker'
        )
        self.limits['File systems']._add_current_usage(
            len(filesystems['FileSystems']),
            aws_type='AWS::EFS::FileSystem',
        )

    def get_limits(self):
        """
        Return all known limits for this service, as a dict of their names
        to :py:class:`~.AwsLimit` objects.

        **Note:** we can't make connections to AWS in this method. So, the
        :py:meth:`~._update_limits_from_api` method fixes this limit if we're
        in us-east-1, which has a lower default limit.

        :returns: dict of limit names to :py:class:`~.AwsLimit` objects
        :rtype: dict
        """
        if self.limits != {}:
            return self.limits
        limits = {}
        limits['File systems'] = AwsLimit(
            'File systems',
            self,
            125,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::EFS::FileSystem',
        )
        self.limits = limits
        return limits

    def _update_limits_from_api(self):
        """
        Call :py:meth:`~.connect` and then check what region we're running in;
        adjust default limits as required for regions that differ (us-east-1).
        """
        region_limits = {
            'us-east-1': 70
        }
        self.connect()
        rname = self.conn._client_config.region_name
        if rname in region_limits:
            self.limits['File systems'].default_limit = region_limits[rname]
            logger.debug(
                'Running in region %s; setting EFS "File systems" default '
                'limit value to: %d', rname, region_limits[rname]
            )

    def required_iam_permissions(self):
        """
        Return a list of IAM Actions required for this Service to function
        properly. All Actions will be shown with an Effect of "Allow"
        and a Resource of "*".

        :returns: list of IAM Action strings
        :rtype: list
        """
        return [
            "elasticfilesystem:DescribeFileSystems",
        ]
