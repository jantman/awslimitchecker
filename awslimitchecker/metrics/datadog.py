"""
awslimitchecker/metrics/datadog.py

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

import os
import logging
import urllib3
import time
import re
import json
from awslimitchecker.metrics.base import MetricsProvider

logger = logging.getLogger(__name__)


class Datadog(MetricsProvider):
    """Send metrics to Datadog."""

    def __init__(
        self, region_name, prefix='awslimitchecker.', api_key=None,
        extra_tags=None, host='https://api.datadoghq.com'
    ):
        """
        Initialize the Datadog metrics provider. This class does not have any
        additional requirements. You must specify at least the ``api_key``
        configuration option.

        :param region_name: the name of the region we're connected to. This
          parameter is automatically passed in by the Runner class.
        :type region_name: str
        :param prefix: Datadog metric prefix
        :type prefix: str
        :param api_key: Datadog API key. May alternatively be specified by the
          ``DATADOG_API_KEY`` environment variable.
        :type api_key: str
        :param host: The datadog host URL to use; defaults to
          ``https://api.datadoghq.com``. This parameter is overridden by the
          ``DATADOG_HOST`` environment variable, if set. This must NOT end with
          a trailing slash.
        :type host: str
        :param extra_tags: CSV list of additional tags to send with metrics.
          All metrics will automatically be tagged with ``region:<region name>``
        :type extra_tags: str
        """
        super(Datadog, self).__init__(region_name)
        self._prefix = prefix
        self._tags = ['region:%s' % region_name]
        if extra_tags is not None:
            self._tags.extend(extra_tags.split(','))
        self._api_key = os.environ.get('DATADOG_API_KEY')
        self._host = os.environ.get('DATADOG_HOST', host)
        if api_key is not None:
            self._api_key = api_key
        if self._api_key is None:
            raise RuntimeError(
                'ERROR: Datadog metrics provider requires datadog API key.'
            )
        self._http = urllib3.PoolManager()
        self._validate_auth(self._api_key)

    def _validate_auth(self, api_key):
        url = self._host + '/api/v1/validate?api_key=%s'
        logger.debug('Validating Datadog API key: GET %s', url)
        url = url % api_key
        r = self._http.request('GET', url)
        if r.status != 200:
            raise RuntimeError(
                'ERROR: Datadog API key validation failed with HTTP %s: %s' % (
                    r.status, r.data
                )
            )

    def _name_for_metric(self, service, limit):
        """
        Return a metric name that's safe for datadog

        :param service: service name
        :type service: str
        :param limit: limit name
        :type limit: str
        :return: datadog metric name
        :rtype: str
        """
        return ('%s%s.%s' % (
            self._prefix,
            re.sub(r'[^0-9a-zA-Z]+', '_', service),
            re.sub(r'[^0-9a-zA-Z]+', '_', limit)
        )).lower()

    def flush(self):
        ts = int(time.time())
        logger.debug('Flushing metrics to Datadog.')
        series = [{
            'metric': '%sruntime' % self._prefix,
            'points': [[ts, self._duration]],
            'type': 'gauge',
            'tags': self._tags
        }]
        for lim in self._limits:
            u = lim.get_current_usage()
            if len(u) == 0:
                max_usage = 0
            else:
                max_usage = max(u).get_value()
            mname = self._name_for_metric(lim.service.service_name, lim.name)
            series.append({
                'metric': '%s.max_usage' % mname,
                'points': [[ts, max_usage]],
                'type': 'gauge',
                'tags': self._tags
            })
            limit = lim.get_limit()
            if limit is not None:
                series.append({
                    'metric': '%s.limit' % mname,
                    'points': [[ts, limit]],
                    'type': 'gauge',
                    'tags': self._tags
                })
        logger.info('POSTing %d metrics to datadog', len(series))
        data = {'series': series}
        encoded = json.dumps(data).encode('utf-8')
        url = self._host + '/api/v1/series?api_key=%s' % self._api_key
        resp = self._http.request(
            'POST', url,
            headers={'Content-type': 'application/json'},
            body=encoded
        )
        if resp.status < 300:
            logger.debug(
                'Successfully POSTed to Datadog; HTTP %d: %s',
                resp.status, resp.data
            )
            return
        raise RuntimeError(
            'ERROR sending metrics to Datadog; API responded HTTP %d: %s' % (
                resp.status, resp.data
            )
        )
