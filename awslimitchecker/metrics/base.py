"""
awslimitchecker/metrics/base.py

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

import logging
from abc import ABCMeta, abstractmethod

logger = logging.getLogger(__name__)


class MetricsProvider(object):

    __metaclass__ = ABCMeta

    def __init__(self, region_name):
        """
        Initialize a MetricsProvider class. This MUST be overridden by
        subclasses. All configuration must be passed as keyword arguments
        to the class constructor (these come from ``--metrics-config`` CLI
        arguments). Any dependency imports must be made in the constructor.
        The constructor should do as much as possible to validate configuration.

        :param region_name: the name of the region we're connected to
        :type region_name: str
        """
        self._region_name = region_name
        self._duration = 0.0
        self._limits = []

    def set_run_duration(self, duration):
        """
        Set the duration for the awslimitchecker run (the time taken to check
        usage against limits).

        :param duration: time taken to check limits
        :type duration: float
        """
        self._duration = duration

    def add_limit(self, limit):
        """
        Cache a given limit for later sending to the metrics store.

        :param limit: a limit to cache
        :type limit: AwsLimit
        """
        self._limits.append(limit)

    @abstractmethod
    def flush(self):
        """
        Flush all metrics to the provider. This is the method that actually
        sends data to your metrics provider/store. It should iterate over
        ``self._limits`` and send metrics for them, as well as for
        ``self._duration``.
        """
        raise NotImplementedError()

    @staticmethod
    def providers_by_name():
        """
        Return a dict of available MetricsProvider subclass names to the class
        objects.

        :return: MetricsProvider class names to classes
        :rtype: dict
        """
        return {x.__name__: x for x in MetricsProvider.__subclasses__()}

    @staticmethod
    def get_provider_by_name(name):
        """
        Get a reference to the provider class with the specified name.

        :param name: name of the MetricsProvider subclass
        :type name: str
        :return: MetricsProvider subclass
        :rtype: ``class``
        :raises: RuntimeError
        """
        try:
            return MetricsProvider.providers_by_name()[name]
        except KeyError:
            raise RuntimeError(
                'ERROR: "%s" is not a valid MetricsProvider class name' % name
            )
