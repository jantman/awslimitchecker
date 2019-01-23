"""
awslimitchecker/trustedadvisor.py

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

from botocore.exceptions import ClientError
from dateutil import parser
import logging
from .connectable import Connectable
from datetime import datetime, timedelta
from pytz import utc
from time import sleep
from copy import deepcopy

logger = logging.getLogger(__name__)


class TrustedAdvisor(Connectable):
    """
    Class to handle interaction with TrustedAdvisor API, polling TA and updating
    limits from TA information.
    """

    service_name = 'TrustedAdvisor'
    api_name = 'support'

    def __init__(self, all_services, boto_connection_kwargs,
                 ta_refresh_mode=None, ta_refresh_timeout=None):
        """
        Class to contain all TrustedAdvisor-related logic.

        :param all_services: :py:class:`~.checker.AwsLimitChecker` ``services``
          dictionary.
        :type all_services: dict
        :param profile_name: The name of a profile in the cross-SDK
          `shared credentials file <https://boto3.readthedocs.io/en/latest/
          guide/configuration.html#shared-credentials-file>`_ for boto3 to
          retrieve AWS credentials from.
        :type profile_name: str
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
        :param mfa_serial_number: (optional) the `MFA Serial Number` string to
          use when assuming a role via STS.
        :type mfa_serial_number: str
        :param mfa_token: (optional) the `MFA Token` string to use when
          assuming a role via STS.
        :type mfa_token: str
        :param ta_refresh_mode: How to handle refreshing Trusted Advisor checks;
          this is either None (do not refresh at all), the string "wait"
          (trigger refresh of all limit-related checks and wait for the refresh
          to complete), the string "trigger" (trigger refresh of all
          limit-related checks but do not wait for the refresh to complete), or
          an integer, which causes any limit-related checks more than this
          number of seconds old to be refreshed, waiting for the refresh to
          complete. Note that "trigger" will likely result in the current run
          getting stale data, but the check being refreshed in time for the
          next run.
        :type ta_refresh_mode: :py:class:`str` or :py:class:`int` or
          :py:data:`None`
        :param ta_refresh_timeout: If ``ta_refresh_mode`` is "wait" or an
          integer (any mode that will wait for the refresh to complete), if this
          parameter is not None, only wait up to this number of seconds for the
          refresh to finish before continuing on anyway.
        :type ta_refresh_timeout: :py:class:`int` or :py:data:`None`
        """
        self.conn = None
        self.have_ta = True
        self.ta_region = boto_connection_kwargs.get('region_name')
        # All Support/TA API connections are to us-east-1 only
        ta_kwargs = deepcopy(boto_connection_kwargs)
        ta_kwargs['region_name'] = 'us-east-1'
        self._boto3_connection_kwargs = ta_kwargs
        self.refresh_mode = ta_refresh_mode
        self.refresh_timeout = ta_refresh_timeout
        self.all_services = all_services
        self.ta_services = self._make_ta_service_dict()
        self.limits_updated = False

    def update_limits(self):
        """
        Poll 'Service Limits' check results from Trusted Advisor, if possible.
        Iterate over all :py:class:`~.AwsLimit` objects for the given services
        and update their limits from TA if present in TA checks.

        :param services: dict of service name (string) to
          :py:class:`~._AwsService` objects
        :type services: dict
        """
        if self.limits_updated:
            logger.debug('Already polled TA; skipping update')
            return
        self.connect()
        ta_results = self._poll()
        self._update_services(ta_results)
        self.limits_updated = True

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
        checks = self._get_refreshed_check_result(check_id)
        region = self.ta_region or self.conn._client_config.region_name
        res = {}
        if checks['result'].get('status', '') == 'not_available':
            logger.warning(
                'Trusted Advisor returned status "not_available" for '
                'service limit check; cannot retrieve limits from TA.'
            )
            return {}
        if 'flaggedResources' not in checks['result']:
            logger.warning(
                'Trusted Advisor returned no results for '
                'service limit check; cannot retrieve limits from TA.'
            )
            return {}
        for check in checks['result']['flaggedResources']:
            if 'region' in check and check['region'] != region:
                continue
            data = dict(zip(metadata, check['metadata']))
            if data['Service'] not in res:
                res[data['Service']] = {}
            try:
                val = int(data['Limit Amount'])
            except ValueError:
                val = data['Limit Amount']
                if val != 'Unlimited':
                    logger.error('TrustedAdvisor returned unknown Limit '
                                 'Amount %s for %s - %s', val, data['Service'],
                                 data['Limit Name'])
                    continue
                else:
                    logger.debug('TrustedAdvisor setting explicit "Unlimited" '
                                 'limit for %s - %s', data['Service'],
                                 data['Limit Name'])
            res[data['Service']][data['Limit Name']] = val
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
            checks = self.conn.describe_trusted_advisor_checks(
                language='en'
            )['checks']
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'SubscriptionRequiredException':
                logger.warning(
                    "Cannot check TrustedAdvisor: %s",
                    ex.response['Error']['Message']
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

    def _get_refreshed_check_result(self, check_id):
        """
        Given the ``check_id``, return the dict of Trusted Advisor check
        results. This handles refreshing the Trusted Advisor check, if desired,
        according to ``self.refresh_mode`` and ``self.refresh_timeout``.

        :param check_id: the Trusted Advisor check ID
        :type check_id: str
        :returns: dict check result. The return value of
          :py:meth:`Support.Client.describe_trusted_advisor_check_result`
        :rtype: dict
        """
        # handle a refresh_mode of None right off the bat
        if self.refresh_mode is None:
            logger.info("Not refreshing Trusted Advisor check (refresh mode "
                        "is None)")
            return self._get_check_result(check_id)[0]
        logger.debug("Handling refresh of check: %s", check_id)
        # if we want to refresh, step 1 is to see if we can yet...
        if not self._can_refresh_check(check_id):
            return self._get_check_result(check_id)[0]
        # either it's not too soon to refresh, or we have no idea...
        if isinstance(self.refresh_mode, type(1)):
            # mode is an int, check the last refresh time and compare
            checks, check_datetime = self._get_check_result(check_id)
            logger.debug('ta_refresh_mode older; check last refresh: %s; '
                         'threshold=%d seconds', check_datetime,
                         self.refresh_mode)
            if check_datetime >= datetime.now(utc) - timedelta(
                    seconds=self.refresh_mode):
                logger.warning('Trusted Advisor check %s last refresh time '
                               'of %s is newer than refresh threshold of %d '
                               'seconds.', check_id, check_datetime,
                               self.refresh_mode)
                return self._get_check_result(check_id)[0]
        # do the refresh
        logger.info("Refreshing Trusted Advisor check: %s", check_id)
        self.conn.refresh_trusted_advisor_check(checkId=check_id)
        # if mode isn't trigger, wait for refresh up to timeout
        if self.refresh_mode == 'trigger':
            result = self._get_check_result(check_id)[0]
        else:
            result = self._poll_for_refresh(check_id)
        return result

    def _poll_for_refresh(self, check_id):
        """
        Given a Trusted Advisor check_id that has just been refreshed, poll
        until the refresh is complete. Once complete, return the check result.

        :param check_id: the Trusted Advisor check ID
        :type check_id: str
        :returns: dict check result. The return value of
          :py:meth:`Support.Client.describe_trusted_advisor_check_result`
        :rtype: dict
        """
        logger.warning('Polling for TA check %s refresh...', check_id)
        if self.refresh_timeout is None:
            # no timeout...
            cutoff = datetime_now() + timedelta(days=365)
        else:
            cutoff = datetime_now() + timedelta(seconds=self.refresh_timeout)
        last_status = None
        while datetime_now() <= cutoff:
            logger.debug('Checking refresh status')
            status = self.conn.describe_trusted_advisor_check_refresh_statuses(
                checkIds=[check_id]
            )['statuses'][0]['status']
            if status in ['success', 'abandoned']:
                logger.info('Refresh status: %s; done polling', status)
                break
            if status == 'none' and last_status not in ['none', None]:
                logger.warning('Trusted Advisor check refresh status went '
                               'from "%s" to "%s"; refresh is either complete '
                               'or timed out on AWS side. Continuing',
                               last_status, status)
                break
            last_status = status
            logger.info('Refresh status: %s; sleeping 30s', status)
            sleep(30)
        else:
            logger.error('Timed out waiting for TA Check refresh; status=%s',
                         status)
        logger.info('Done polling for check refresh')
        result, last_dt = self._get_check_result(check_id)
        logger.debug('Check shows last refresh time of: %s', last_dt)
        return result

    def _can_refresh_check(self, check_id):
        """
        Determine if the given check_id can be refreshed yet.

        :param check_id: the Trusted Advisor check ID
        :type check_id: str
        :return: whether or not the check can be refreshed yet
        :rtype: bool
        """
        try:
            refresh_status = \
                self.conn.describe_trusted_advisor_check_refresh_statuses(
                    checkIds=[check_id]
                )
            logger.debug("TA Check %s refresh status: %s", check_id,
                         refresh_status['statuses'][0])
            ms = refresh_status['statuses'][0]['millisUntilNextRefreshable']
            if ms > 0:
                logger.warning("Trusted Advisor check cannot be refreshed for "
                               "another %d milliseconds; skipping refresh and "
                               "getting check results now", ms)
                return False
            return True
        except Exception:
            logger.warning("Could not get refresh status for TA check %s",
                           check_id, exc_info=True)
        # default to True if we don't know...
        return True

    def _get_check_result(self, check_id):
        """
        Directly wrap
        :py:meth:`Support.Client.describe_trusted_advisor_check_result`;
        return a 2-tuple of the result dict and the last refresh DateTime.

        :param check_id: the Trusted Advisor check ID
        :type check_id: str
        :return: 2-tuple of (result dict, last refresh DateTime). If the last
          refresh time can't be parsed from the response, the second element
          will be None.
        :rtype: tuple
        """
        checks = self.conn.describe_trusted_advisor_check_result(
            checkId=check_id, language='en'
        )
        try:
            check_datetime = parser.parse(checks['result']['timestamp'])
            logger.debug("Got TrustedAdvisor data for check %s as of %s",
                         check_id, check_datetime)
        except KeyError:
            check_datetime = None
            logger.debug("Got TrustedAdvisor data for check %s but unable to "
                         "parse timestamp", check_id)
        return checks, check_datetime

    def _update_services(self, ta_results):
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
            svc_results = ta_results[svc_name]
            if svc_name not in self.ta_services:
                logger.info("TrustedAdvisor returned check results for "
                            "unknown service '%s'", svc_name)
                continue
            svc_limits = self.ta_services[svc_name]
            for lim_name in sorted(svc_results):
                if lim_name not in svc_limits:
                    logger.info("TrustedAdvisor returned check results for "
                                "unknown limit '%s' (service %s)",
                                lim_name,
                                svc_name)
                    continue
                val = svc_results[lim_name]
                if val == 'Unlimited':
                    svc_limits[lim_name]._set_ta_unlimited()
                else:
                    svc_limits[lim_name]._set_ta_limit(val)
        logger.info("Done updating TA limits on all services")

    def _make_ta_service_dict(self):
        """
        Build our service and limits dict. This is laid out identical to
        ``self.all_services``, but keys limits by their ``ta_service_name``
        and ``ta_limit_name`` properties.

        :return: dict of TA service names to TA limit names to AwsLimit objects.
        """
        res = {}
        for svc_name in self.all_services:
            svc_obj = self.all_services[svc_name]
            for lim_name, lim in svc_obj.get_limits().items():
                if lim.ta_service_name not in res:
                    res[lim.ta_service_name] = {}
                res[lim.ta_service_name][lim.ta_limit_name] = lim
        return res


def datetime_now():
    """
    Helper function for testing; return :py:meth:`datetime.datetime.now`.

    :return: :py:meth:`datetime.datetime.now`
    :rtype: datetime.datetime
    """
    return datetime.now()
