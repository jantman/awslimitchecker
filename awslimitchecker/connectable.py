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
import boto3

logger = logging.getLogger(__name__)


class ConnectableCredentials(object):
    """
    boto's (2.x) :py:meth:`boto.sts.STSConnection.assume_role` returns a
    :py:class:`boto.sts.credentials.Credentials` object, but boto3's
    `boto3.sts.STSConnection.assume_role <https://boto3.readthedocs.org/en/
    latest/reference/services/sts.html#STS.Client.assume_role>`_ just returns
    a dict. This class provides a compatible interface for boto3.

    We also maintain an ``account_id`` attribute that can be set to the
    account ID, to ensure that credentials are updated when switching accounts.
    """

    def __init__(self, creds_dict):
        self.access_key = creds_dict['Credentials']['AccessKeyId']
        self.secret_key = creds_dict['Credentials']['SecretAccessKey']
        self.session_token = creds_dict['Credentials']['SessionToken']
        self.expiration = creds_dict['Credentials']['Expiration']
        self.assumed_role_id = creds_dict['AssumedRoleUser']['AssumedRoleId']
        self.assumed_role_arn = creds_dict['AssumedRoleUser']['Arn']
        self.account_id = None


class Connectable(object):

    """
    Mix-in helper class for connecting to AWS APIs. Centralizes logic of
    connecting via regions and/or STS.
    """

    # Class attribute to reuse credentials between calls
    credentials = None

    @property
    def _boto3_connection_kwargs(self):
        """
        Generate keyword arguments for boto3 connection functions.
        If ``self.account_id`` is None, this will just include
        ``region_name=self.region``. Otherwise, call
        :py:meth:`~._get_sts_token` to get STS token credentials using
        `boto3.STS.Client.assume_role <https://boto3.readthedocs.org/en/
        latest/reference/services/sts.html#STS.Client.assume_role>`_ and include
        those credentials in the return value.

        :return: keyword arguments for boto3 connection functions
        :rtype: dict
        """
        kwargs = {'region_name': self.region}
        if self.profile_name is not None:
            # fetch credentials from cache.
            session = boto3.Session(profile_name=self.profile_name)
            credentials = session._session.get_credentials()
            kwargs['aws_access_key_id'] = credentials.access_key
            kwargs['aws_secret_access_key'] = credentials.secret_key
            kwargs['aws_session_token'] = credentials.token
        elif self.account_id is not None:
            if Connectable.credentials is None:
                logger.debug("Connecting for account %s role '%s' with STS "
                             "(region: %s)", self.account_id, self.account_role,
                             self.region)
                Connectable.credentials = self._get_sts_token()
            else:
                if self.account_id == Connectable.credentials.account_id:
                    logger.debug("Reusing previous STS credentials for "
                                 "account %s", self.account_id)
                else:
                    logger.debug("Previous STS credentials are for account %s; "
                                 "getting new credentials for current account "
                                 "(%s)", Connectable.credentials.account_id,
                                 self.account_id)
                    Connectable.credentials = self._get_sts_token()
            kwargs['aws_access_key_id'] = Connectable.credentials.access_key
            kwargs['aws_secret_access_key'] = Connectable.credentials.secret_key
            kwargs['aws_session_token'] = Connectable.credentials.session_token
        else:
            logger.debug("Connecting to region %s", self.region)
        return kwargs

    def connect(self):
        """
        Connect to an AWS API via boto3 low-level client and set ``self.conn``
        to the `boto3.client <https://boto3.readthed
        ocs.org/en/latest/reference/core/boto3.html#boto3.client>`_ object
        (a ``botocore.client.*`` instance). If ``self.conn`` is not None,
        do nothing. This connects to the API name given by ``self.api_name``.

        :returns: None
        """
        if self.conn is not None:
            return
        kwargs = self._boto3_connection_kwargs
        self.conn = boto3.client(self.api_name, **kwargs)
        logger.info("Connected to %s in region %s", self.api_name,
                    self.conn._client_config.region_name)

    def connect_resource(self):
        """
        Connect to an AWS API via boto3 high-level resource connection and set
        ``self.resource_conn`` to the `boto3.resource <https://boto3.readthed
        ocs.org/en/latest/reference/core/boto3.html#boto3.resource>`_ object
        (a ``boto3.resources.factory.*.ServiceResource`` instance).
        If ``self.resource_conn`` is not None,
        do nothing. This connects to the API name given by ``self.api_name``.

        :returns: None
        """
        if self.resource_conn is not None:
            return
        kwargs = self._boto3_connection_kwargs
        self.resource_conn = boto3.resource(self.api_name, **kwargs)
        logger.info("Connected to %s (resource) in region %s", self.api_name,
                    self.resource_conn.meta.client._client_config.region_name)

    def _get_sts_token(self):
        """
        Assume a role via STS and return the credentials.

        First connect to STS via :py:func:`boto3.client`, then
        assume a role using `boto3.STS.Client.assume_role <https://boto3.readthe
        docs.org/en/latest/reference/services/sts.html#STS.Client.assume_role>`_
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
        assume_kwargs = {
            'RoleArn': arn,
            'RoleSessionName': 'awslimitchecker'
        }
        if self.external_id is not None:
            assume_kwargs['ExternalId'] = self.external_id
        if self.mfa_serial_number is not None:
            assume_kwargs['SerialNumber'] = self.mfa_serial_number
        if self.mfa_token is not None:
            assume_kwargs['TokenCode'] = self.mfa_token
        role = sts.assume_role(**assume_kwargs)

        creds = ConnectableCredentials(role)
        creds.account_id = self.account_id

        logger.debug("Got STS credentials for role; access_key_id=%s "
                     "(account_id=%s)", creds.access_key, creds.account_id)
        return creds
