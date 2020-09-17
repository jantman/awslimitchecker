"""
awslimitchecker/services/lambdafunc.py

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
from botocore.exceptions import EndpointConnectionError

logger = logging.getLogger(__name__)


class _LambdaService(_AwsService):

    service_name = 'Lambda'
    api_name = 'lambda'

    def find_usage(self):
        """
        Determine the current usage for each limit of this service,
        and update corresponding Limit via
        :py:meth:`~.AwsLimit._add_current_usage`.
        """
        logger.debug("Getting usage for Lambda metrics")
        try:
            self.connect()
            resp = self.conn.get_account_settings()
        except EndpointConnectionError as ex:
            logger.warn('Skipping Lambda: %s', str(ex))
            return
        self.limits['Function Count']._add_current_usage(
            resp['AccountUsage']['FunctionCount']
        )
        self.limits['Total Code Size (MiB)']._add_current_usage(
            int((resp['AccountUsage']['TotalCodeSize']) / 1048576)
        )
        self._have_usage = True

    def get_limits(self):
        """
        Return all known limits for this service, as a dict of their names
        to :py:class:`~.AwsLimit` objects.

        :returns: dict of limit names to :py:class:`~.AwsLimit` objects
        :rtype: dict
        """
        logger.debug("Getting limits for Lambda")
        if self.limits != {}:
            return self.limits

        self._construct_limits()

        return self.limits

    def _update_limits_from_api(self):
        """
        Query Lambda's DescribeLimits API action, and update limits
        with the quotas returned. Updates ``self.limits``.
        """
        logger.debug("Updating limits for Lambda from the AWS API")
        if len(self.limits) == 2:
            return
        self.connect()
        lims = self.conn.get_account_settings()['AccountLimit']
        self.limits['Total Code Size (MiB)']._set_api_limit(
            (lims['TotalCodeSize'] / 1048576)
        )
        self.limits['Code Size Unzipped (MiB) per Function']._set_api_limit(
            (lims['CodeSizeUnzipped'] / 1048576)
        )
        self.limits['Unreserved Concurrent Executions']._set_api_limit(
            lims['UnreservedConcurrentExecutions']
        )
        self.limits['Concurrent Executions']._set_api_limit(
            lims['ConcurrentExecutions']
        )
        self.limits['Code Size Zipped (MiB) per Function']._set_api_limit(
            (lims['CodeSizeZipped'] / 1048576)
        )

    def _construct_limits(self):
        self.limits = {}
        self.limits['Total Code Size (MiB)'] = AwsLimit(
            'Total Code Size (MiB)',
            self,
            76800,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::Lambda::Function'
        )

        self.limits['Code Size Unzipped (MiB) per Function'] = AwsLimit(
            'Code Size Unzipped (MiB) per Function',
            self,
            250,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::Lambda::Function'
        )

        self.limits['Unreserved Concurrent Executions'] = AwsLimit(
            'Unreserved Concurrent Executions',
            self,
            1000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::Lambda::Function'
        )

        self.limits['Concurrent Executions'] = AwsLimit(
            'Concurrent Executions',
            self,
            1000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::Lambda::Function'
        )

        self.limits['Code Size Zipped (MiB) per Function'] = AwsLimit(
            'Code Size Zipped (MiB) per Function',
            self,
            50,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::Lambda::Function'
        )

        self.limits['Function Count'] = AwsLimit(
            'Function Count',
            self,
            None,  # unlimited
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::Lambda::Function'
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
            "lambda:GetAccountSettings"
        ]
