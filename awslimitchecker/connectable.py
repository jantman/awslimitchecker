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
import boto  # @TODO boto3 migration - remove this when done
import boto.sts  # @TODO boto3 migration - remove this when done
import boto3

logger = logging.getLogger(__name__)


class ConnectableCredentials(object):
    """
    boto's (2.x) :py:meth:`boto.sts.STSConnection.assume_role` returns a
    :py:class:`boto.sts.credentials.Credentials` object, but boto3's
    :py:meth:`boto3.STS.Client.assume_role` just returns a dict. This class
    provides a compatible interface for boto3.
    """

    def __init__(self, creds_dict):
        self.access_key = creds_dict['Credentials']['AccessKeyId']
        self.secret_key = creds_dict['Credentials']['SecretAccessKey']
        self.session_token = creds_dict['Credentials']['SessionToken']
        self.expiration = creds_dict['Credentials']['Expiration']
        self.assumed_role_id = creds_dict['AssumedRoleUser']['AssumedRoleId']
        self.assumed_role_arn = creds_dict['AssumedRoleUser']['Arn']


class Connectable(object):

    """
    Mix-in helper class for connecting to AWS APIs. Centralizes logic of
    connecting via regions and/or STS.
    """

    # Class attribute to reuse credentials between calls
    credentials = None

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
        # @TODO boto3 migration - remove this when done
        if self.account_id is not None:
            if Connectable.credentials is None:
                logger.debug("Connecting to %s for account %s (STS; %s)",
                             self.service_name, self.account_id, self.region)
                Connectable.credentials = self._get_sts_token()
            else:
                logger.debug("Reusing previous STS credentials for account %s",
                             self.account_id)

            conn = driver(
                self.region,
                aws_access_key_id=Connectable.credentials.access_key,
                aws_secret_access_key=Connectable.credentials.secret_key,
                security_token=Connectable.credentials.session_token)
        else:
            logger.debug("Connecting to %s (%s)",
                         self.service_name, self.region)
            conn = driver(self.region)
        logger.info("Connected to %s", self.service_name)
        return conn

    def connect_client(self, service_name):
        """
        Connect to an AWS API and return the connected boto3 client object. If
        ``self.account_id`` is None, call :py:meth:`boto3.client` with
        ``region_name=self.region``. Otherwise, call :py:meth:`~._get_sts_token`
        to get STS token credentials using
        :py:meth:`boto.sts.STSConnection.assume_role` and call
        :py:meth:`boto3.client` with those credentials to use an assumed role.

        This method returns a low-level boto3 client object.

        :param service_name: name of the AWS service API to connect to (passed
          to :py:meth:`boto3.client` as the ``service_name`` parameter.)
        :type driver: str
        :returns: connected :py:meth:`boto3.client` class instance
        """
        if self.account_id is not None:
            if Connectable.credentials is None:
                logger.debug("Connecting to %s for account %s (STS; %s)",
                             service_name, self.account_id, self.region)
                Connectable.credentials = self._get_sts_token_boto3()
            else:
                logger.debug("Reusing previous STS credentials for account %s",
                             self.account_id)
            conn = boto3.client(
                service_name,
                region_name=self.region,
                aws_access_key_id=Connectable.credentials.access_key,
                aws_secret_access_key=Connectable.credentials.secret_key,
                aws_session_token=Connectable.credentials.session_token)
        else:
            logger.debug("Connecting to %s (%s)",
                         service_name, self.region)
            conn = boto3.client(service_name, region_name=self.region)
        logger.info("Connected to %s", service_name)
        return conn

    def _get_sts_token(self):
        """
        Assume a role via STS and return the credentials.

        First connect to STS via :py:func:`boto.sts.connect_to_region`, then
        assume a role using :py:meth:`boto.sts.STSConnection.assume_role`
        using ``self.account_id`` and ``self.account_role`` (and optionally
        ``self.external_id``, ``self.mfa_serial_number``, ``self.mfa_token``).
        Return the resulting :py:class:`boto.sts.credentials.Credentials`
        object.

        :returns: STS assumed role credentials
        :rtype: :py:class:`boto.sts.credentials.Credentials`
        """
        # @TODO boto3 migration - remove this when done
        logger.debug("Connecting to STS in region %s", self.region)
        sts = boto.sts.connect_to_region(self.region)
        arn = "arn:aws:iam::%s:role/%s" % (self.account_id, self.account_role)
        logger.debug("STS assume role for %s", arn)
        role = sts.assume_role(arn, "awslimitchecker",
                               external_id=self.external_id,
                               mfa_serial_number=self.mfa_serial_number,
                               mfa_token=self.mfa_token)
        logger.debug("Got STS credentials for role; access_key_id=%s",
                     role.credentials.access_key)
        return role.credentials

    def _get_sts_token_boto3(self):
        """
        Assume a role via STS and return the credentials.

        First connect to STS via :py:func:`boto3.client`, then
        assume a role using :py:meth:`boto3.STS.Client.assume_role`
        using ``self.account_id`` and ``self.account_role`` (and optionally
        ``self.external_id``, ``self.mfa_serial_number``, ``self.mfa_token``).
        Return the resulting :py:class:`~.ConnectableCredentials`
        object.

        :returns: STS assumed role credentials
        :rtype: :py:class:`~.ConnectableCredentials`
        """
        logger.debug("Connecting to STS in region %s", self.region)
        sts = boto3.client('sts', region_name=self.region)
        arn = "arn:aws:iam::%s:role/%s" % (self.account_id, self.account_role)
        logger.debug("STS assume role for %s", arn)
        role = sts.assume_role(RoleArn=arn,
                               RoleSessionName="awslimitchecker",
                               ExternalId=self.external_id,
                               SerialNumber=self.mfa_serial_number,
                               TokenCode=self.mfa_token)
        creds = ConnectableCredentials(role)
        logger.debug("Got STS credentials for role; access_key_id=%s",
                     creds.access_key)
        return creds
