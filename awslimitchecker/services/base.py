"""
awslimitchecker/services/base.py

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

import abc
import logging
import boto.sts

logger = logging.getLogger(__name__)


class _AwsService(object):
    __metaclass__ = abc.ABCMeta

    service_name = 'baseclass'

    def __init__(self, warning_threshold, critical_threshold, account_id=None,
                 account_role=None, region=None):
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
        :param account_id: connect via STS to this AWS account
        :type account_id: str
        :param account_role: connect via STS as this IAM role
        :type account_role: str
        """
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.account_id = account_id
        self.account_role = account_role
        self.region = region

        self.limits = {}
        self.limits = self.get_limits()
        self.conn = None
        self._have_usage = False

    @abc.abstractmethod
    def connect(self):
        """
        If not already done, establish a connection to the relevant AWS service
        and save as ``self.conn``.
        """
        """
        if self.conn is None:
            logger.debug("Connecting to %s", self.service_name)
            # self.conn = boto.<connect to something>
            logger.info("Connected to %s", self.service_name)
        """
        raise NotImplementedError('abstract base class')

    @abc.abstractmethod
    def find_usage(self):
        """
        Determine the current usage for each limit of this service,
        and update the ``current_usage`` property of each corresponding
        :py:class:`~.AwsLimit` instance.

        This method must set ``self._have_usage = True``
        """
        """
        logger.debug("Checking usage for service {n}".format(
            n=self.service_name))
        self.connect()
        # find usage here
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

    def connect_via(self, driver):
        """
        Connect to API if not already connected; set self.conn
        Use STS to assume a role as another user if self.account_id has been set

        :param driver: the connect_to_region() function of the boto
          submodule to use to create this connection
        :type driver: :py:obj:`function`
        """
        # @TODO do we really want to pass the modules in here, and assume
        # they all have the same ``.connect_to_region()``, or should we
        # pass in a reference to the function?
        # https://github.com/jantman/awslimitchecker/pull/64#issuecomment-131546997
        if(self.account_id):
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
        """Attempt to get STS token, exit if fail."""
        logger.debug("Connecting to STS in region %s", self.region)
        sts = boto.sts.connect_to_region(self.region)
        arn = "arn:aws:iam::%s:role/%s" % (self.account_id, self.account_role)
        logger.debug("STS assume role for %s", arn)
        role = sts.assume_role(arn, "awslimitchecker")
        logger.debug("Got STS credentials for role; access_key_id=%s",
                     role.credentials.access_key)
        return role.credentials

    def set_limit_override(self, limit_name, value, override_ta=True):
        """
        Set a new limit ``value`` for the specified limit, overriding
        the default. If ``override_ta`` is True, also use this value
        instead of any found by Trusted Advisor. This method simply
        passes the data through to the
        :py:meth:`~awslimitchecker.limit.AwsLimit.set_limit_override`
        method of the underlying :py:class:`~.AwsLimit` instance.

        :param limit_name: the name of the limit to override the value for
        :type limit_name: string
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
        :type limit_name: string
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
