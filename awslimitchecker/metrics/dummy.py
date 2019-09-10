"""
awslimitchecker/metrics/dummy.py

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

import logging
from awslimitchecker.metrics.base import MetricsProvider

logger = logging.getLogger(__name__)


class Dummy(MetricsProvider):
    """Just writes metrics to STDOUT; mainly used for testing."""

    def __init__(self, region_name, **_):
        super(Dummy, self).__init__(region_name)

    def flush(self):
        print('DummyMetrics Provider flush for region=%s' % self._region_name)
        print('Duration: %s' % self._duration)
        lines = []
        for lim in self._limits:
            u = lim.get_current_usage()
            if len(u) == 0:
                max_usage = 0
            else:
                max_usage = max(u).get_value()
            limit = lim.get_limit()
            if limit is None:
                limit = 'unknown'
            lines.append(
                '%s / %s: limit=%s max_usage=%s' % (
                    lim.service.service_name, lim.name, limit, max_usage
                )
            )
        for l in sorted(lines):
            print(l)
