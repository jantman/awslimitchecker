"""
awslimitchecker/services/firehose.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2016 Hugo Lopes Tavares <hltbra@gmail.com>

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
Hugo Lopes Tavares <hltbra@gmail.com>
################################################################################
"""

import abc  # noqa
import logging

from .base import _AwsService
from ..limit import AwsLimit
from botocore.exceptions import EndpointConnectionError

logger = logging.getLogger(__name__)


class _FirehoseService(_AwsService):

    service_name = 'Firehose'
    api_name = 'firehose'

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
            self._find_delivery_streams()
        except EndpointConnectionError as ex:
            logger.warning(
                'Caught exception when trying to use Firehose ('
                'perhaps the Firehose service is not available in this '
                'region?): %s', ex
            )

        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_delivery_streams(self):
        streams = self.conn.list_delivery_streams()
        usage = len(streams['DeliveryStreamNames'])
        while streams.get('HasMoreDeliveryStreams'):
            last_stream_name = streams['DeliveryStreamNames'][-1]
            streams = self.conn.list_delivery_streams(
                ExclusiveStartDeliveryStreamName=last_stream_name)
            usage += len(streams['DeliveryStreamNames'])
        self.limits['Delivery streams per region']._add_current_usage(
            usage,
            resource_id=self._boto3_connection_kwargs['region_name'],
            aws_type='AWS::KinesisFirehose::DeliveryStream',
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
        limits['Delivery streams per region'] = AwsLimit(
            'Delivery streams per region',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::KinesisFirehose::DeliveryStream',
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
            "firehose:ListDeliveryStreams",
        ]
