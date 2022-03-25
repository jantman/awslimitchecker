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
import boto3
from datetime import datetime, timedelta
from awslimitchecker.connectable import Connectable

logger = logging.getLogger(__name__)


class _AwsService(Connectable):
    __metaclass__ = abc.ABCMeta

    #: awslimitchecker's name for the service
    service_name = 'baseclass'

    #: the AWS API name for the service
    api_name = 'baseclass'

    #: the service code for Service Quotas, or None
    quotas_service_code = None

    def __init__(self, warning_threshold, critical_threshold,
                 boto_connection_kwargs, quotas_client):
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
        :param boto_connection_kwargs: Dictionary of keyword arguments to
          pass to boto connection methods.
        :type boto_connection_kwargs: dict
        :param quotas_client: Instance of ServiceQuotasClient
        :type quotas_client: ``ServiceQuotasClient`` or ``None``
        """
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self._boto3_connection_kwargs = boto_connection_kwargs
        self._quotas_client = quotas_client
        self.conn = None
        self.resource_conn = None
        self.limits = {}
        self.limits = self.get_limits()
        self._have_usage = False
        self._current_account_id = None
        self._cloudwatch_client = None

    @property
    def current_account_id(self):
        """
        Return the numeric Account ID for the account that we are currently
        running against.

        :return: current account ID
        :rtype: str
        """
        if self._current_account_id is not None:
            return self._current_account_id
        kwargs = dict(self._boto3_connection_kwargs)
        sts = boto3.client('sts', **kwargs)
        logger.info(
            "Connected to STS in region %s", sts._client_config.region_name
        )
        cid = sts.get_caller_identity()
        self._current_account_id = cid['Account']
        return cid['Account']

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

    def _update_service_quotas(self):
        """
        Update all limits for this service via the Service Quotas service.
        """
        if self.quotas_service_code is None:
            return
        if self._quotas_client is None:
            return
        logger.debug('Updating service quotas for %s', self.service_name)
        for lname in sorted(self.limits.keys()):
            lim = self.limits[lname]
            val = self._quotas_client.get_quota_value(
                lim.quotas_service_code, lim.quota_name,
                units=lim.quotas_unit, converter=lim.quotas_unit_converter
            )
            if val is not None:
                lim._set_quotas_limit(val)

    def _cloudwatch_connection(self):
        """
        Return a connected CloudWatch client instance. ONLY to be used by
        :py:meth:`_get_cloudwatch_usage_latest`.
        """
        if self._cloudwatch_client is not None:
            return self._cloudwatch_client
        kwargs = dict(self._boto3_connection_kwargs)
        if self._max_retries_config is not None:
            kwargs['config'] = self._max_retries_config
        self._cloudwatch_client = boto3.client('cloudwatch', **kwargs)
        logger.info(
            "Connected to cloudwatch in region %s",
            self._cloudwatch_client._client_config.region_name
        )
        return self._cloudwatch_client

    def _get_cloudwatch_usage_latest(
        self, dimensions, metric_name='ResourceCount', period=60
    ):
        """
        Given some metric dimensions, return the value of the latest data point
        for the ``AWS/Usage`` metric specified.

        :param dimensions: list of dicts; dimensions for the metric
        :type dimensions: list
        :param metric_name: AWS/Usage metric name to get
        :type metric_name: str
        :param period: metric period
        :type period: int
        :return: return the metric value (float or int), or None if it cannot
          be retrieved
        :rtype: ``float, int or None``
        """
        conn = self._cloudwatch_connection()
        kwargs = dict(
            MetricDataQueries=[
                {
                    'Id': 'id',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/Usage',
                            'MetricName': metric_name,
                            'Dimensions': dimensions
                        },
                        'Period': period,
                        'Stat': 'Average'
                    }
                }
            ],
            StartTime=datetime.utcnow() - timedelta(hours=1, minutes=1),
            EndTime=datetime.utcnow() - timedelta(minutes=1),
            ScanBy='TimestampDescending',
            MaxDatapoints=1
        )
        try:
            logger.debug('Querying CloudWatch GetMetricData: %s', kwargs)
            resp = conn.get_metric_data(**kwargs)
        except Exception as ex:
            logger.error(
                'Error querying CloudWatch GetMetricData for AWS/Usage %s: %s',
                metric_name, ex
            )
            return 0
        results = resp.get('MetricDataResults', [])
        if len(results) < 1 or len(results[0]['Values']) < 1:
            logger.warning(
                'No data points found for AWS/Usage metric %s with dimensions '
                '%s; using value of zero!', metric_name, dimensions
            )
            return 0
        logger.debug(
            'CloudWatch metric query returned value of %s with timestamp %s',
            results[0]['Values'][0], results[0]['Timestamps'][0]
        )
        return results[0]['Values'][0]
