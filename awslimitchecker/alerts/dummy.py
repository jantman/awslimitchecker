"""
awslimitchecker/alerts/dummy.py

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
from .base import AlertProvider

logger = logging.getLogger(__name__)


class Dummy(AlertProvider):
    """
    Dummy alert provider that just outputs alerts to STDOUT (this will
    effectively duplicate awslimitchecker's CLI output).
    """

    def __init__(self, region_name, **_):
        """
        Initialize an AlertProvider class. This MUST be overridden by
        subclasses. All configuration must be passed as keyword arguments
        to the class constructor (these come from ``--alert-config`` CLI
        arguments). Any dependency imports must be made in the constructor.
        The constructor should do as much as possible to validate configuration.

        :param region_name: the name of the region we're connected to
        :type region_name: str
        """
        super(Dummy, self).__init__(region_name)

    def on_success(self, duration=None):
        """
        Method called when no thresholds were breached, and run completed
        successfully. Should resolve any open incidents (if the service supports
        that functionality) or else simply return.

        :param duration: duration of the usage/threshold checking run
        :type duration: float
        """
        print('awslimitchecker in %s found no problems' % self._region_name)
        if duration:
            print('awslimitchecker run duration: %s' % duration)

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
        if exc is not None:
            print('awslimitchecker in %s failed with exception: %s' % (
                self._region_name, exc.__repr__()
            ))
        else:
            print('awslimitchecker in %s found CRITICALS:' % self._region_name)
            print(problem_str)
        if duration:
            print('awslimitchecker run duration: %s' % duration)

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
        print('awslimitchecker in %s found WARNINGS:' % self._region_name)
        print(problem_str)
        if duration:
            print('awslimitchecker run duration: %s' % duration)
