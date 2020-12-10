"""
awslimitchecker/alerts/alertmanager.py

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
from base64 import b64encode
from datetime import datetime, timedelta

from .base import AlertProvider
from awslimitchecker.utils import issue_string_tuple

logger = logging.getLogger(__name__)


class AlertManager(AlertProvider):
    """
    Alert provider to send notifications to AlertManager.
    """

    def __init__(
        self, region_name: str, endpoints: str, alert_duration='1800',
        basic_auth_username: str = None, basic_auth_password: str = None
    ):
        """
        Initialize AlertManager alert provider.

        :param region_name: the name of the region we're connected to
        :type region_name: str
        :param endpoints: **Required**; the AlertManager endpoints
          (ex. endpoints=http://alertmanager1:9093,http://alertmanager2:9093)
          env: ``ALERTMANAGER_ENDPOINTS``
        :type endpoints: str
        :param alert_duration: **Optional**; seconds before AlertManager
          considers alerts are resolved. Set it more then period between the
          program runs. env: ALERTMANAGER_ALERT_DURATION
        :type alert_duration: int
        :param basic_auth_username: **Optional**; Can also be specified via the
          ``ALERTMANAGER_BASIC_AUTH_USERNAME`` environment variable.
        :type basic_auth_username: str
        :param basic_auth_password: **Optional**; Can also be specified via the
          ``ALERTMANAGER_BASIC_AUTH_PASSWORD`` environment variable.
        :type basic_auth_password: str
        """
        super().__init__(region_name)

        self._endpoints = os.environ.get('ALERTMANAGER_ENDPOINTS') or endpoints
        if self._endpoints is None:
            raise RuntimeError(
                'ERROR: AlertManager alert provider requires '
                'endpoints parameter or ALERTMANAGER_ENDPOINTS '
                'environment variable.'
            )
        self._alert_duration = os.environ.get(
            'ALERTMANAGER_ALERT_DURATION'
        ) or alert_duration
        self._basic_auth_username = os.environ.get(
            'ALERTMANAGER_BASIC_AUTH_USERNAME'
        ) or basic_auth_username
        self._basic_auth_password = os.environ.get(
            'ALERTMANAGER_BASIC_AUTH_PASSWORD'
        ) or basic_auth_password

    def _send_event(self, severity: str, description: str):
        """
        Send an event to AlertManager.

        :param severity: event severity
        :type severity: str
        :param description: event description
        :type description: str
        """
        # region in the label 'instance' due to currently awslimitchecker
        # supports only check per region and grouping by instance is default
        # behavior in alertmanager.
        # datetime in UTC format to simplify the code
        event = '''[{
                    "labels": {
                       "alertname": "AWSServiceLimitExceeded",
                       "instance": "%s",
                       "severity": "%s"
                    },
                    "annotations": {
                       "description": "%s"
                    },
                    "endsAt": "%s"
                }]''' % (
            self._region_name,
            severity,
            description,
            (
                datetime.utcnow() + timedelta(seconds=float(self._alert_duration))
            ).isoformat() + 'Z'
        )

        http = urllib3.PoolManager()
        success = 0
        for endpoint in self._endpoints.split(","):
            url = endpoint + '/api/v1/alerts'
            logger.info(
                'POSTing to AlertManager API (%s): %s', url, event
            )
            try:
                auth = '%s:%s' % (
                    self._basic_auth_username, self._basic_auth_password
                )
                resp = http.request(
                    'POST', url,
                    headers={
                        'Content-type': 'application/json',
                        'Authorization': 'Basic %s' % b64encode(
                            auth.encode()
                        ).decode()
                    },
                    body=event
                )
                if resp.status == 200:
                    logger.debug(
                        'Successfully POSTed to %s: %s %s',
                        url, resp.status, resp.data
                    )
                    success += 1
                else:
                    logger.error(
                        'Unsuccessfully POSTed to %s: %s %s',
                        url, resp.status, resp.data
                    )
            except urllib3.exceptions.MaxRetryError as e:
                logger.error(e)

        if success == 0:
            raise RuntimeError(
                'Alert was not able to be sent to %s' % self._endpoints
            )

    def _generate_description(self, problems) -> str:
        """
        Generate description from dict of problems for an event

        :param problems: dict of service name to nested dict of limit name to
          limit, same format as the return value of
          :py:meth:`~.AwsLimitChecker.check_thresholds`. ``None`` if ``exc`` is
          specified.
        :type problems: dict
        :return: description string for Event
        :rtype: str
        """
        desc = ''
        for svc in sorted(problems.keys()):
            for limit_name in sorted(problems[svc].keys()):
                limit = problems[svc][limit_name]
                warns = limit.get_warnings()
                crits = limit.get_criticals()
                _, v = issue_string_tuple(
                    svc, limit, crits, warns, colorize=False
                )
                desc += f'{svc}/{limit_name} {v}. '
        return desc

    def on_success(self, duration=None):
        # AlertManager does not require an event with success
        pass

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
        if exc:
            # crash if exception arrives. The script health should be monitored from outside
            raise exc
        else:
            description = self._generate_description(problems)
        self._send_event("critical", description)

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
        self._send_event("warning", self._generate_description(problems))
