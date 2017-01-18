"""
awslimitchecker/connectable.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2015-2017 Jason Antman <jason@jasonantman.com>

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
        logger.info("Connected to %s in region %s",
                    self.api_name, self.conn._client_config.region_name)

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
