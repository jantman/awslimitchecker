"""
awslimitchecker/connectable.py

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

import logging
import boto.sts

logger = logging.getLogger(__name__)


class Connectable(object):

    """
    Mix-in helper class for connecting to AWS APIs. Centralizes logic of
    connecting via regions and/or STS.
    """

    def connect_via(self, driver):
        """
        Connect to an AWS API and return the connection object. If
        ``self.account_id`` is None, call ``driver(self.region)``. Otherwise,
        call :py:meth:`~._get_sts_token` to get STS token credentials using
        :py:meth:`boto.sts.STSConnection.assume_role` and call ``driver()`` with
        those credentials to use an assumed role.

        :param driver: the connect_to_region() function of the boto
          submodule to use to create this connection
        :type driver: :py:obj:`function`
        :returns: connected boto service class instance
        """
        if self.account_id is not None:
            logger.debug("Connecting to %s for account %s (STS; %s)",
                         self.service_name, self.account_id, self.region)
            self.credentials = self._get_sts_token()
            conn = driver(
                self.region,
                aws_access_key_id=self.credentials.access_key,
                aws_secret_access_key=self.credentials.secret_key,
                security_token=self.credentials.session_token)
        else:
            logger.debug("Connecting to %s (%s)",
                         self.service_name, self.region)
            conn = driver(self.region)
        logger.info("Connected to %s", self.service_name)
        return conn

    def _get_sts_token(self):
        """
        Assume a role via STS and return the credentials.

        First connect to STS via :py:func:`boto.sts.connect_to_region`, then
        assume a role using :py:meth:`boto.sts.STSConnection.assume_role`
        using ``self.account_id`` and ``self.account_role`` (and optionally
        ``self.external_id``). Return the resulting
        :py:class:`boto.sts.credentials.Credentials` object.

        :returns: STS assumed role credentials
        :rtype: :py:class:`boto.sts.credentials.Credentials`
        """
        logger.debug("Connecting to STS in region %s", self.region)
        sts = boto.sts.connect_to_region(self.region)
        arn = "arn:aws:iam::%s:role/%s" % (self.account_id, self.account_role)
        logger.debug("STS assume role for %s", arn)
        role = sts.assume_role(arn, "awslimitchecker",
                               external_id=self.external_id)
        logger.debug("Got STS credentials for role; access_key_id=%s",
                     role.credentials.access_key)
        return role.credentials
