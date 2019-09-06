"""
awslimitchecker/alerts/pagerdutyv1.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2015-2019 Jason Antman <jason@jasonantman.com>

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

import os
import logging
import urllib3
import json

from .base import AlertProvider
from awslimitchecker.utils import issue_string_tuple

logger = logging.getLogger(__name__)


class PagerDutyV1(AlertProvider):
    """
    Alert provider to send notifications to PagerDuty via the Events API V1.
    """

    pd_url = 'https://events.pagerduty.com/generic/2010-04-15/create_event.json'

    def __init__(
        self, region_name, account_alias=None, critical_service_key=None,
        warning_service_key=None, incident_key=None
    ):
        """
        Initialize PagerDutyV1 alert provider.

        :param region_name: the name of the region we're connected to
        :type region_name: str
        :param account_alias: Optional; an alias for the account that
          awslimitchecker is currently running against, to use in the default
          incident_key and description.
        :param critical_service_key: **Required**; the PagerDuty Integration
          Key for sending Critical events. Can also be specified via the
          ``PAGERDUTY_SERVICE_KEY_CRIT`` environment variable.
        :type critical_service_key: str
        :param warning_service_key: **Required**; the PagerDuty Integration
          Key for sending Warning events. Can also be specified via the
          ``PAGERDUTY_SERVICE_KEY_WARN`` environment variable. If omitted,
          alerts will not be sent for warnings.
        :type warning_service_key: str
        :param incident_key: Optional; the PagerDuty incident/routing key to
          use, for de-duplication and resolving alerts. This string will have
          any occurrences of ``{account_alias}`` replaced with the account
          alias (or an empty string, if not specified) and any occurrences of
          ``{region_name}`` replaced with the current region name. If not
          specified, this will default to
          ``awslimitchecker-{account_alias}-{region_name}``.
        :type incident_key: str
        """
        super(PagerDutyV1, self).__init__(region_name)
        self._service_key_crit = os.environ.get(
            'PAGERDUTY_SERVICE_KEY_CRIT', None
        )
        if critical_service_key is not None:
            self._service_key_crit = critical_service_key
        if self._service_key_crit is None:
            raise RuntimeError(
                'ERROR: PagerDutyV1 alert provider requires '
                'critical_service_key parameter or PAGERDUTY_SERVICE_KEY_CRIT '
                'environment variable.'
            )
        self._service_key_warn = os.environ.get(
            'PAGERDUTY_SERVICE_KEY_WARN', None
        )
        if warning_service_key is not None:
            self._service_key_warn = warning_service_key
        self._account_alias = account_alias
        if incident_key is None:
            incident_key = 'awslimitchecker-{account_alias}-{region_name}'
        self._incident_key = incident_key.format(
            account_alias='' if self._account_alias is None
            else self._account_alias,
            region_name=self._region_name
        )

    def _send_event(self, service_key, payload):
        """
        Send an event to PagerDuty.

        :param service_key: service key to send to
        :type service_key: str
        :param payload: data to send with event
        :type payload: dict
        """
        payload['service_key'] = service_key
        http = urllib3.PoolManager()
        logger.info(
            'POSTing to PagerDuty Events API (%s): %s', self.pd_url, payload
        )
        encoded = json.dumps(payload, sort_keys=True).encode('utf-8')
        resp = http.request(
            'POST', self.pd_url,
            headers={'Content-type': 'application/json'},
            body=encoded
        )
        if resp.status == 200:
            logger.debug(
                'Successfully POSTed to PagerDuty; HTTP %d: %s',
                resp.status, resp.data
            )
            return
        raise RuntimeError(
            'ERROR creating PagerDuty Event; API responded HTTP %d: %s' % (
                resp.status, resp.data
            )
        )

    def _event_dict(self):
        """
        Return a skeleton dictionary for the PagerDuty V1 Event.

        :return: skeleton of Event
        :rtype: dict
        """
        d = {
            'incident_key': self._incident_key,
            'details': {
                'region': self._region_name
            },
            'client': 'awslimitchecker'
        }
        if self._account_alias is not None:
            d['details']['account_alias'] = self._account_alias
        return d

    def on_success(self, duration=None):
        """
        Method called when no thresholds were breached, and run completed
        successfully. Should resolve any open incidents (if the service supports
        that functionality) or else simply return.

        :param duration: duration of the usage/threshold checking run
        :type duration: float
        """
        data = self._event_dict()
        data['event_type'] = 'resolve'
        data['description'] = 'awslimitchecker in '
        if self._account_alias is not None:
            data['description'] += self._account_alias + ' '
        data['description'] += self._region_name + ' found no problems'
        if duration:
            data['description'] += '; run completed in %.2f seconds' % duration
            data['details']['duration_seconds'] = duration
        self._send_event(self._service_key_crit, data)
        if self._service_key_warn is not None:
            self._send_event(self._service_key_warn, data)

    def _problems_dict(self, problems):
        """
        Make a dict of problems suitable for inclusion in Event details.

        :param problems: dict of service name to nested dict of limit name to
          limit, same format as the return value of
          :py:meth:`~.AwsLimitChecker.check_thresholds`. ``None`` if ``exc`` is
          specified.
        :type problems: dict
        :return: problems summary suitable for Event details
        :rtype: dict
        """
        res = {}
        w_count = 0
        c_count = 0
        for svc in sorted(problems.keys()):
            for lim_name in sorted(problems[svc].keys()):
                limit = problems[svc][lim_name]
                warns = limit.get_warnings()
                w_count += len(warns)
                crits = limit.get_criticals()
                c_count += len(crits)
                _, v = issue_string_tuple(
                    svc, limit, crits, warns, colorize=False
                )
                if svc not in res:
                    res[svc] = {}
                res[svc][lim_name] = v
        return w_count, c_count, res

    def on_critical(self, problems, problem_str, exc=None, duration=None):
        """
        Method called when the run encountered errors, or at least one critical
        threshold was met or crossed.

        :param problems: dict of service name to nested dict of limit name to
          limit, same format as the return value of
          :py:meth:`~.AwsLimitChecker.check_thresholds`. ``None`` if ``exc`` is
          specified.
        :type problems: dict or None
        :param problem_str: String representation of ``problems``, as displayed
          in ``awslimitchecker`` command line output. ``None`` if ``exc`` is
          specified.
        :type problem_str: str or None
        :param exc: Exception object that was raised during the run (optional)
        :type exc: Exception
        :param duration: duration of the run
        :type duration: float
        """
        data = self._event_dict()
        data['event_type'] = 'trigger'
        data['description'] = 'awslimitchecker in '
        if self._account_alias is not None:
            data['description'] += self._account_alias + ' '
        data['description'] += self._region_name
        if duration:
            data['description'] += ' ran in %.2f seconds and' % duration
            data['details']['duration_seconds'] = duration
        if exc is not None:
            data['description'] += ' failed with an exception:' \
                                   ' %s' % exc.__repr__()
            data['details']['exception'] = exc.__repr__()
        else:
            w_count, c_count, pdict = self._problems_dict(problems)
            data['description'] += ' crossed %d CRITICAL thresholds' % c_count
            if w_count > 0:
                data['description'] += ' and %d WARNING thresholds' % w_count
            data['details']['limits'] = pdict
        self._send_event(self._service_key_crit, data)

    def on_warning(self, problems, problem_str, duration=None):
        """
        Method called when one or more warning thresholds were crossed, but no
        criticals and the run did not encounter any errors.

        :param problems: dict of service name to nested dict of limit name to
          limit, same format as the return value of
          :py:meth:`~.AwsLimitChecker.check_thresholds`.
        :type problems: dict or None
        :param problem_str: String representation of ``problems``, as displayed
          in ``awslimitchecker`` command line output.
        :type problem_str: str or None
        :param duration: duration of the run
        :type duration: float
        """
        data = self._event_dict()
        data['event_type'] = 'trigger'
        data['description'] = 'awslimitchecker in '
        if self._account_alias is not None:
            data['description'] += self._account_alias + ' '
        data['description'] += self._region_name
        if duration:
            data['description'] += ' ran in %.2f seconds and' % duration
            data['details']['duration_seconds'] = duration
        w_count, _, pdict = self._problems_dict(problems)
        data['description'] += ' crossed %d WARNING thresholds' % w_count
        data['details']['limits'] = pdict
        self._send_event(self._service_key_warn, data)
