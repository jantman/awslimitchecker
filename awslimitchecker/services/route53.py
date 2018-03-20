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
        "name": "Hosted Zone RecordSets"
    }
    MAX_VPCS_ASSOCIATED_BY_ZONE = {
        "type": "MAX_VPCS_ASSOCIATED_BY_ZONE",
        "name": "Hosted Zone VPC Associations"
    }

    _hosted_zone_cache = dict()
    _hosted_zone_type_cache = dict()

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

        self._find_usage_recordsets()
        self._find_usage_vpc_associations()

        self._have_usage = True
        logger.debug("Done checking usage.")

    def get_limits(self):
        """
        Return all known limits for this service, as a dict of their names
        to :py:class:`~.AwsLimit` objects.

        Limits from:
        docs.aws.amazon.com/Route53/latest/DeveloperGuide/DNSLimitations.html

        :returns: dict of limit names to :py:class:`~.AwsLimit` objects
        :rtype: dict
        """
        if self.limits != {}:
            return self.limits
        limits = {}
        limits['Hosted Zone RecordSets'] = AwsLimit(
            'Hosted Zone RecordSets',
            self,
            10000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::Route53::HostedZone',
        )

        limits['Hosted Zone VPC Associations'] = AwsLimit(
            'Hosted Zone VPC Associations',
            self,
            100,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::Route53::HostedZone',
        )

        return limits

    def _get_hosted_zones(self):
        """
        Return all available hosted zones

        :returns: dict of hosted zones
        :rtype: dict
        """
        if self._hosted_zone_cache:
            return self._hosted_zone_cache

        self.connect()
        results = paginate_dict(
            self.conn.list_hosted_zones,
            alc_marker_path=['NextMarker'],
            alc_data_path=['HostedZones'],
            alc_marker_param='Marker'
        )

        self._hosted_zone_cache = results["HostedZones"]

        print("HostedZones")
        print(results["HostedZones"])
        return self._hosted_zone_cache

    def _get_hosted_zone_limit(self, limit_type, hosted_zone_id):
        """
        Return a hosted zone limit [recordsets|vpc_associations]
        This method should only be used internally by
        :py:meth:~._get_limits_hosted_zones`.

        :rtype: dict
        """

        if not self._hosted_zone_type_cache.get(limit_type):
            self._hosted_zone_type_cache[limit_type] = dict()

        if self._hosted_zone_type_cache[limit_type].get(hosted_zone_id, None):
            return self._hosted_zone_type_cache[limit_type][hosted_zone_id]

        result = self.conn.get_hosted_zone_limit(
            Type=limit_type,
            HostedZoneId=hosted_zone_id
        )

        print("results")
        print(result)
        self._hosted_zone_type_cache[limit_type][hosted_zone_id] = result
        return result

    def _get_limits_hosted_zones(self, limit_type):
        """
        Return a dict of [recordsets|vpc_associations] limits
        for all hosted zones.
        This method should only be used internally by
        :py:meth:~.get_limits`.

        :rtype: dict
        """

        limits = {}
        for hosted_zone in self._get_hosted_zones():
            if limit_type == self.MAX_VPCS_ASSOCIATED_BY_ZONE \
                    and not hosted_zone["Config"]["PrivateZone"]:
                continue

            key = limit_type["name"]

            limit = self._get_hosted_zone_limit(limit_type["type"],
                                                hosted_zone['Id'])
            limits[key] = AwsLimit(
                key,
                self,
                int(limit["Limit"]["Value"]),
                self.warning_threshold,
                self.critical_threshold,
                limit_type=key
            )
        return limits

    def _get_limits_recordsets(self):
        """
        Return a dict of recordset limits for all hosted zones.
        This method should only be used internally by
        :py:meth:~.get_limits`.

        :rtype: dict
        """

        return self._get_limits_hosted_zones(self.MAX_RRSETS_BY_ZONE)

    def _get_limits_vpc_associations(self):
        """
        Return a dict of recordset limits for all hosted zones.
        This method should only be used internally by
        :py:meth:~.get_limits`.

        :rtype: dict
        """

        return self._get_limits_hosted_zones(self.MAX_VPCS_ASSOCIATED_BY_ZONE)

    def _find_usage_hosted_zone(self, limit_type):
        """
        Calculate the max [recordsets|vpc associations] per hosted zone
        """
        for hosted_zone in self._get_hosted_zones():
            if limit_type == self.MAX_VPCS_ASSOCIATED_BY_ZONE \
                    and not hosted_zone["Config"]["PrivateZone"]:
                continue

            key = limit_type["name"]
            count = self._get_hosted_zone_limit(limit_type["type"],
                                                hosted_zone['Id'])

            print("The Count")
            print(count)
            self.limits[key]._add_current_usage(
                int(count["Count"]),
                aws_type='AWS::Route53::HostedZone',
                resource_id="{} ({})".format(hosted_zone["Id"],
                                             hosted_zone["Name"])
            )

    def _find_usage_recordsets(self):
        """
        Calculate the max recordsets per hosted zone
        """
        self._find_usage_hosted_zone(self.MAX_RRSETS_BY_ZONE)

    def _find_usage_vpc_associations(self):
        """
        Calculate the max vpc associations per hosted zone
        """
        self._find_usage_hosted_zone(self.MAX_VPCS_ASSOCIATED_BY_ZONE)

    def _update_limits_from_api(self):
        """
        Call the service's API action to retrieve limit/quota information, and
        update AwsLimit objects in ``self.limits`` with this information.
        """
        self.limits.update(self._get_limits_recordsets())
        self.limits.update(self._get_limits_vpc_associations())

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
            "route53:ListHostedZones",
        ]
