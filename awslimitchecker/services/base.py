"""
awslimitchecker/services/base.py

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

import abc
import logging
from awslimitchecker.connectable import Connectable

logger = logging.getLogger(__name__)


class _AwsService(Connectable):
    __metaclass__ = abc.ABCMeta

    service_name = 'baseclass'
    api_name = 'baseclass'

    def __init__(self, warning_threshold, critical_threshold,
                 boto_connection_kwargs={}):
        """
        Describes an AWS service and its limits, and provides methods to
        query current utilization.

        Constructors of _AwsService subclasses *must not* make any external
        connections; these must be made lazily as needed in other methods.
        _AwsService subclasses should be usable without any external network
        connections.

        :param warning_threshold: the default warning threshold, as an
          integer percentage, for any limits without a specifically-set
          threshold.
        :type warning_threshold: int
        :param critical_threshold: the default critical threshold, as an
          integer percentage, for any limits without a specifically-set
          threshold.
        :type critical_threshold: int
        :param profile_name: The name of a profile in the cross-SDK
          `shared credentials file <https://boto3.readthedocs.io/en/latest/
          guide/configuration.html#shared-credentials-file>`_ for boto3 to
          retrieve AWS credentials from.
        :type profile_name: str
        :param account_id: `AWS Account ID <http://docs.aws.amazon.com/general/
          latest/gr/acct-identifiers.html>`_
          (12-digit string, currently numeric) for the account to connect to
          (destination) via STS
        :type account_id: str
        :param account_role: the name of an
          `IAM Role <http://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.
          html>`_
          (in the destination account) to assume
        :param region: AWS region name to connect to
        :type region: str
        :type account_role: str
        :param external_id: (optional) the `External ID <http://docs.aws.amazon.
          com/IAM/latest/UserGuide/id_roles_create_for-user_externalid.html>`_
          string to use when assuming a role via STS.
        :type external_id: str
        :param mfa_serial_number: (optional) the `MFA Serial Number` string to
          use when assuming a role via STS.
        :type mfa_serial_number: str
        :param mfa_token: (optional) the `MFA Token` string to use when
          assuming a role via STS.
        :type mfa_token: str
        """
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self._boto3_connection_kwargs = boto_connection_kwargs
        self.conn = None
        self.resource_conn = None
        self.limits = {}
        self.limits = self.get_limits()
        self._have_usage = False

    @abc.abstractmethod
    def find_usage(self):
        """
        Determine the current usage for each limit of this service,
        and update the ``current_usage`` property of each corresponding
        :py:class:`~.AwsLimit` instance.

        This method MUST set ``self._have_usage = True``.

        If the boto3 method being called returns a dict response that can
        include 'NextToken' or another pagination marker, it should be called
        through
        :py:func:`~awslimitchecker.utils.paginate_dict` with the appropriate
        parameters.
        """
        """
        logger.debug("Checking usage for service {n}".format(
            n=self.service_name))
        self.connect()
        usage = self.conn.method_to_get_usage()
        # or, if it needs to be paginated, something like:
        usage = paginate_dict(
            self.conn.method_to_get_usage,
            alc_marker_path=['NextToken'],
            alc_data_path=['ResourceListName'],
            alc_marker_param='NextToken'
        )
        logger.debug("Done checking usage.")
        self._have_usage = True
        """
        raise NotImplementedError('abstract base class')

    @abc.abstractmethod
    def get_limits(self):
        """
        Return all known limits for this service, as a dict of their names
        to :py:class:`~.AwsLimit` objects.

        All limits must have ``self.warning_threshold`` and
        ``self.critical_threshold`` passed into them.

        :returns: dict of limit names to :py:class:`~.AwsLimit` objects
        :rtype: dict
        """
        """
        if self.limits != []:
            return self.limits
        # else define the limits
        """
        raise NotImplementedError('abstract base class')

    @abc.abstractmethod
    def required_iam_permissions(self):
        """
        Return a list of IAM Actions required for this Service to function
        properly. All Actions will be shown with an Effect of "Allow"
        and a Resource of "*".

        :returns: list of IAM Action strings
        :rtype: list
        """
        raise NotImplementedError('abstract base class')

    def set_limit_override(self, limit_name, value, override_ta=True):
        """
        Set a new limit ``value`` for the specified limit, overriding
        the default. If ``override_ta`` is True, also use this value
        instead of any found by Trusted Advisor. This method simply
        passes the data through to the
        :py:meth:`~awslimitchecker.limit.AwsLimit.set_limit_override`
        method of the underlying :py:class:`~.AwsLimit` instance.

        :param limit_name: the name of the limit to override the value for
        :type limit_name: str
        :param value: the new value to set for the limit
        :type value: int
        :param override_ta: whether or not to also override Trusted
          Advisor information
        :type override_ta: bool
        :raises: ValueError if limit_name is not known to this service
        """
        try:
            self.limits[limit_name].set_limit_override(
                value,
                override_ta=override_ta
            )
            logger.debug(
                "Overriding %s limit %s; default=%d override=%d",
                self.service_name,
                limit_name,
                value,
                self.limits[limit_name].default_limit,
            )
        except KeyError:
            raise ValueError("{s} service has no '{l}' limit".format(
                s=self.service_name,
                l=limit_name))

    def _set_ta_limit(self, limit_name, value):
        """
        Set the value for the limit as reported by Trusted Advisor,
        for the specified limit.

        This method should only be called by :py:class:`~.TrustedAdvisor`.

        :param limit_name: the name of the limit to override the value for
        :type limit_name: str
        :param value: the Trusted Advisor limit value
        :type value: int
        :raises: ValueError if limit_name is not known to this service
        """
        try:
            self.limits[limit_name]._set_ta_limit(value)
            logger.debug(
                "Setting %s limit %s TA limit to %d",
                self.service_name,
                limit_name,
                value,
            )
        except KeyError:
            raise ValueError("{s} service has no '{l}' limit".format(
                s=self.service_name,
                l=limit_name))

    def set_threshold_override(self, limit_name, warn_percent=None,
                               warn_count=None, crit_percent=None,
                               crit_count=None):
        """
        Override the default warning and critical thresholds used to evaluate
        the specified limit's usage. Theresholds can be specified as a
        percentage of the limit, or as a usage count, or both.

        :param warn_percent: new warning threshold, percentage used
        :type warn_percent: int
        :param warn_count: new warning threshold, actual count/number
        :type warn_count: int
        :param crit_percent: new critical threshold, percentage used
        :type crit_percent: int
        :param crit_count: new critical threshold, actual count/number
        :type crit_count: int
        """
        try:
            self.limits[limit_name].set_threshold_override(
                warn_percent=warn_percent,
                warn_count=warn_count,
                crit_percent=crit_percent,
                crit_count=crit_count
            )
        except KeyError:
            raise ValueError("{s} service has no '{l}' limit".format(
                s=self.service_name,
                l=limit_name))

    def check_thresholds(self):
        """
        Checks current usage against configured thresholds for all limits
        for this service.

        :returns: a dict of limit name to :py:class:`~.AwsLimit` instance
          for all limits that crossed one or more of their thresholds.
        :rtype: :py:obj:`dict` of :py:class:`~.AwsLimit`
        """
        if not self._have_usage:
            self.find_usage()
        ret = {}
        for name, limit in self.limits.items():
            if limit.check_thresholds() is False:
                ret[name] = limit
        return ret
