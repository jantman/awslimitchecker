"""
awslimitchecker/services/iam.py

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

logger = logging.getLogger(__name__)


class _IamService(_AwsService):

    service_name = 'IAM'
    api_name = 'iam'

    # mapping of iam.AccountSummary() key to limit name
    API_TO_LIMIT_NAME = {
        'Groups': 'Groups',
        'Users': 'Users',
        'Roles': 'Roles',
        'InstanceProfiles': 'Instance profiles',
        'ServerCertificates': 'Server certificates',
        'Policies': 'Policies',
        'PolicyVersionsInUse': 'Policy Versions In Use',
    }

    def find_usage(self):
        """
        Determine the current usage for each limit of this service,
        and update corresponding Limit via
        :py:meth:`~.AwsLimit._add_current_usage`.
        """
        logger.debug("Checking usage for service %s", self.service_name)
        for lim in self.limits.values():
            lim._reset_usage()
        self._update_limits_from_api()
        self._have_usage = True
        logger.debug("Done checking usage.")

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
        limits['Groups'] = AwsLimit(
            'Groups',
            self,
            300,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::IAM::Group',
        )
        limits['Users'] = AwsLimit(
            'Users',
            self,
            5000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::IAM::User',
        )
        limits['Roles'] = AwsLimit(
            'Roles',
            self,
            1000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::IAM::Role',
        )
        limits['Instance profiles'] = AwsLimit(
            'Instance profiles',
            self,
            1000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::IAM::InstanceProfile',
        )
        limits['Server certificates'] = AwsLimit(
            'Server certificates',
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::IAM::ServerCertificate',
        )
        limits['Policies'] = AwsLimit(
            'Policies',
            self,
            1500,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::IAM::Policy',
        )
        limits['Policy Versions In Use'] = AwsLimit(
            'Policy Versions In Use',
            self,
            10000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::IAM::ServerCertificate',
        )
        self.limits = limits
        return limits

    def _update_limits_from_api(self):
        """
        Call the service's API action to retrieve limit/quota information, and
        update AwsLimit objects in ``self.limits`` with this information.
        """
        self.connect_resource()
        summary = self.resource_conn.AccountSummary()
        for k, v in sorted(summary.summary_map.items()):
            if k in self.API_TO_LIMIT_NAME:
                # this is a usage for one of our limits
                lname = self.API_TO_LIMIT_NAME[k]
                # if len(self.limits[lname].get_current_usage()) < 1:
                self.limits[lname]._add_current_usage(v)
            elif k.endswith('Quota') and k[:-5] in self.API_TO_LIMIT_NAME:
                # quota for one of our limits
                lname = self.API_TO_LIMIT_NAME[k[:-5]]
                self.limits[lname]._set_api_limit(v)
            else:
                logger.debug("Ignoring IAM AccountSummary attribute: %s", k)

    def required_iam_permissions(self):
        """
        Return a list of IAM Actions required for this Service to function
        properly. All Actions will be shown with an Effect of "Allow"
        and a Resource of "*".

        :returns: list of IAM Action strings
        :rtype: list
        """
        return [
            "iam:GetAccountSummary",
        ]
