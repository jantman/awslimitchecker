"""
awslimitchecker/trustedadvisor.py

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

import boto
import boto.support
from dateutil import parser
import logging
from .connectable import Connectable

logger = logging.getLogger(__name__)


class TrustedAdvisor(Connectable):

    """
    Class to handle interaction with TrustedAdvisor API, polling TA and updating
    limits from TA information.
    """

    service_name = 'TrustedAdvisor'

    def __init__(self, account_id=None, account_role=None, region=None,
                 external_id=None):
        """
        Class to contain all TrustedAdvisor-related logic.

        :param account_id: `AWS Account ID <http://docs.aws.amazon.com/general/
          latest/gr/acct-identifiers.html>`_
          (12-digit string, currently numeric) for the account to connect to
          (destination) via STS
        :type account_id: str
        :param account_role: the name of an
          `IAM Role <http://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.
          html>`_
          (in the destination account) to assume
        :param region: AWS region name to connect to
        :type region: str
        :type account_role: str
        :param external_id: (optional) the `External ID <http://docs.aws.amazon.
          com/IAM/latest/UserGuide/id_roles_create_for-user_externalid.html>`_
          string to use when assuming a role via STS.
        :type external_id: str
        """
        self.conn = None
        self.have_ta = True
        self.account_id = account_id
        self.account_role = account_role
        self.region = 'us-east-1'
        self.ta_region = region
        self.external_id = external_id

    def connect(self):
        """Connect to API if not already connected; set self.conn."""
        if self.conn is not None:
            return
        if self.ta_region:
            logger.debug("Connecting to Support API (TrustedAdvisor) in %s",
                         self.region)
            self.conn = self.connect_via(boto.support.connect_to_region)
        else:
            logger.debug("Connecting to Support API (TrustedAdvisor)")
            self.conn = boto.connect_support()
        logger.debug("Connected to Support API")

    def update_limits(self, services):
        """
        Poll 'Service Limits' check results from Trusted Advisor, if possible.
        Iterate over all :py:class:`~.AwsLimit` objects for the given services
        and update their limits from TA if present in TA checks.

        :param services: dict of service name (string) to
          :py:class:`~._AwsService` objects
        :type services: dict
        """
        self.connect()
        ta_results = self._poll()
        self._update_services(ta_results, services)

    def _poll(self):
        """
        Poll Trusted Advisor (Support) API for limit checks.

        Return a dict of service name (string) keys to nested dict vals, where
        each key is a limit name and each value the current numeric limit.

        e.g.:
        ::

            {
                'EC2': {
                    'SomeLimit': 10,
                }
            }

        """
        logger.info("Beginning TrustedAdvisor poll")
        tmp = self._get_limit_check_id()
        if not self.have_ta:
            logger.info('TrustedAdvisor.have_ta is False; not polling TA')
            return {}
        if tmp is None:
            logger.critical("Unable to find 'Service Limits' Trusted Advisor "
                            "check; not using Trusted Advisor data.")
            return
        check_id, metadata = tmp
        region = self.ta_region or self.conn.region.name
        checks = self.conn.describe_trusted_advisor_check_result(check_id)
        check_datetime = parser.parse(checks['result']['timestamp'])
        logger.debug("Got TrustedAdvisor data for check %s as of %s",
                     check_id, check_datetime)
        res = {}
        for check in checks['result']['flaggedResources']:
            if check['region'] != region:
                continue
            data = dict(zip(metadata, check['metadata']))
            if data['Service'] not in res:
                res[data['Service']] = {}
            res[data['Service']][data['Limit Name']] = int(data['Limit Amount'])
        logger.info("Finished TrustedAdvisor poll")
        return res

    def _get_limit_check_id(self):
        """
        Query currently-available TA checks, return the check ID and metadata
        of the 'performance/Service Limits' check.

        :returns: 2-tuple of Service Limits TA check ID (string),
          metadata (list), or (None, None).
        :rtype: tuple
        """
        logger.debug("Querying Trusted Advisor checks")
        try:
            checks = self.conn.describe_trusted_advisor_checks('en')['checks']
        except boto.exception.JSONResponseError as ex:
            if (
                    '__type' in ex.body and
                    ex.body['__type'] == 'SubscriptionRequiredException'
            ):
                logger.warning(
                    "Cannot check TrustedAdvisor: %s",
                    ex.message
                )
                self.have_ta = False
                return (None, None)
            else:
                raise ex
        for check in checks:
            if (
                    check['category'] == 'performance' and
                    check['name'] == 'Service Limits'
            ):
                logger.debug("Found TA check; id=%s", check['id'])
                return (
                    check['id'],
                    check['metadata']
                )
        logger.debug("Unable to find check with category 'performance' and "
                     "name 'Service Limits'.")
        return (None, None)

    def _update_services(self, ta_results, services):
        """
        Given a dict of TrustedAdvisor check results from :py:meth:`~._poll`
        and a dict of Service objects passed in to :py:meth:`~.update_limits`,
        updated the TrustedAdvisor limits for all services.

        :param ta_results: results returned by :py:meth:`~._poll`
        :type ta_results: dict
        :param services: dict of service names to _AwsService objects
        :type services: dict
        """
        logger.debug("Updating TA limits on all services")
        for svc_name in sorted(ta_results.keys()):
            limits = ta_results[svc_name]
            if svc_name not in services:
                logger.info("TrustedAdvisor returned check results for "
                            "unknown service '%s'", svc_name)
                continue
            service = services[svc_name]
            for lim_name in sorted(limits.keys()):
                try:
                    service._set_ta_limit(lim_name, limits[lim_name])
                except ValueError:
                    logger.info("TrustedAdvisor returned check results for "
                                "unknown limit '%s' (service %s)",
                                lim_name,
                                svc_name)
        logger.info("Done updating TA limits on all services")
