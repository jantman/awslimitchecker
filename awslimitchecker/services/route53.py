"""
awslimitchecker/services/route53.py

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


class _Route53Service(_AwsService):
    service_name = 'Route53'
    api_name = 'route53'  # AWS API name to connect to (boto3.client)

    # Route53 limit types
    MAX_RRSETS_BY_ZONE = {
        "type": "MAX_RRSETS_BY_ZONE",
        "name": "Record sets per hosted zone",
        "default_limit": 10000
    }
    MAX_VPCS_ASSOCIATED_BY_ZONE = {
        "type": "MAX_VPCS_ASSOCIATED_BY_ZONE",
        "name": "VPC associations per hosted zone",
        "default_limit": 100
    }

    def find_usage(self):
        """
        Determine the current usage for each limit of this service,
        and update corresponding Limit via
        :py:meth:`~.AwsLimit._add_current_usage`.
        """
        self._have_usage = True

    def _update_limits_from_api(self):
        """
        Query Route53's GetHostedZoneLimit API action, and update limits
        with the quotas returned. Updates ``self.limits``.
        """
        logger.info("Querying Route53 GetHostedZoneLimits for limits")
        self.connect()
        self._find_limit_hosted_zone()
        logger.debug('Done setting limits from API.')

    def get_limits(self):
        """
        Return all known limits for this service, as a dict of their names
        to :py:class:`~.AwsLimit` objects.

        Limits from:
        docs.aws.amazon.com/Route53/latest/DeveloperGuide/DNSLimitations.html

        :returns: dict of limit names to :py:class:`~.AwsLimit` objects
        :rtype: dict
        """
        if not self.limits:
            self.limits = {}
            for item in [self.MAX_RRSETS_BY_ZONE,
                         self.MAX_VPCS_ASSOCIATED_BY_ZONE]:
                self.limits[item["name"]] = AwsLimit(
                    item["name"],
                    self,
                    item["default_limit"],
                    self.warning_threshold,
                    self.critical_threshold,
                    limit_type='AWS::Route53::HostedZone',
                    limit_subtype=item["name"]
                )

        return self.limits

    def _get_hosted_zones(self):
        """
        Return all available hosted zones

        :returns: dict of hosted zones
        :rtype: dict
        """
        results = paginate_dict(
            self.conn.list_hosted_zones,
            alc_marker_path=['NextMarker'],
            alc_data_path=['HostedZones'],
            alc_marker_param='Marker'
        )

        return results["HostedZones"]

    def _get_hosted_zone_limit(self, limit_type, hosted_zone_id):
        """
        Return a hosted zone limit [recordsets|vpc_associations]

        :rtype: dict
        """

        result = self.conn.get_hosted_zone_limit(
            Type=limit_type,
            HostedZoneId=hosted_zone_id
        )

        return result

    def _find_limit_hosted_zone(self):
        """
        Calculate the max recordsets and vpc associations and the current values
        per hosted zone
        """
        for limit_type in [self.MAX_RRSETS_BY_ZONE,
                           self.MAX_VPCS_ASSOCIATED_BY_ZONE]:
            self.limits[limit_type["name"]]._reset_usage()

        for hosted_zone in self._get_hosted_zones():
            for limit_type in [self.MAX_RRSETS_BY_ZONE,
                               self.MAX_VPCS_ASSOCIATED_BY_ZONE]:

                if limit_type == self.MAX_VPCS_ASSOCIATED_BY_ZONE and \
                        not hosted_zone["Config"]["PrivateZone"]:
                    continue

                limit = self._get_hosted_zone_limit(limit_type["type"],
                                                    hosted_zone['Id'])

                self.limits[limit_type["name"]]._add_current_usage(
                    int(limit["Count"]),
                    maximum=int(limit["Limit"]["Value"]),
                    aws_type='AWS::Route53::HostedZone',
                    resource_id=hosted_zone["Name"]
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
            "route53:GetHostedZone",
            "route53:GetHostedZoneLimit",
            "route53:ListHostedZones"
        ]
