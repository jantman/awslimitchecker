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
import logging
logger = logging.getLogger(__name__)


class TrustedAdvisor(object):

    def __init__(self):
        """
        Class to contain all TrustedAdvisor-related logic.
        """
        self.conn = None

    def connect(self):
        if self.conn is None:
            logger.debug("Connecting to Support API (TrustedAdvisor)")
            self.conn = boto.connect_support()
            logger.info("Connected to Support API")

    def update_limits(self, services):
        """
        Poll 'Service Limits' check results from Trusted Advisor, if possible.
        Iterate over all :py:class:`~.AwsLimit` objects for the given services
        and update their limits from TA if present in TA checks.

        :param services: dict of service name (string) to
          :py:class:`~._AwsService` objects
        :type services: dict
        """
        # @TODO call this in AwsLimitChecker.get_limits()
        # also, make sure it's been done in get_usage, or anything else
        #   that relies on limits
        pass
