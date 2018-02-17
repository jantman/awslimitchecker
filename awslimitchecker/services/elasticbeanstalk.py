"""
awslimitchecker/services/elasticbeanstalk.py

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
Brian Flad <bflad417@gmail.com> <http://www.fladpad.com>
################################################################################
"""

import abc  # noqa
import logging

from .base import _AwsService
from ..limit import AwsLimit

logger = logging.getLogger(__name__)


class _ElasticBeanstalkService(_AwsService):

    service_name = 'ElasticBeanstalk'
    api_name = 'elasticbeanstalk'  # AWS API name to connect to (boto3.client)

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
        self._find_usage_applications()
        self._find_usage_application_versions()
        self._find_usage_environments()
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_applications(self):
        """find usage for ElasticBeanstalk applications"""
        applications = self.conn.describe_applications()
        self.limits['Applications']._add_current_usage(
            len(applications['Applications']),
            aws_type='AWS::ElasticBeanstalk::Application',
        )

    def _find_usage_application_versions(self):
        """find usage for ElasticBeanstalk application verions"""
        versions = self.conn.describe_application_versions()
        self.limits['Application versions']._add_current_usage(
            len(versions['ApplicationVersions']),
            aws_type='AWS::ElasticBeanstalk::ApplicationVersion',
        )

    def _find_usage_environments(self):
        """find usage for ElasticBeanstalk environments"""
        environments = self.conn.describe_environments()
        self.limits['Environments']._add_current_usage(
            len(environments['Environments']),
            aws_type='AWS::ElasticBeanstalk::Environment',
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
        limits['Applications'] = AwsLimit(
            'Applications',
            self,
            75,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ElasticBeanstalk::Application',
        )
        limits['Application versions'] = AwsLimit(
            'Application versions',
            self,
            1000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ElasticBeanstalk::ApplicationVersion',
        )
        limits['Environments'] = AwsLimit(
            'Environments',
            self,
            200,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ElasticBeanstalk::Environment',
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
            "elasticbeanstalk:DescribeApplications",
            "elasticbeanstalk:DescribeApplicationVersions",
            "elasticbeanstalk:DescribeEnvironments",
        ]
