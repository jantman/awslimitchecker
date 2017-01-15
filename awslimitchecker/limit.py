"""
awslimitchecker/limit.py

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

#: indicates a limit value that came from hard-coded defaults in awslimitchecker
SOURCE_DEFAULT = 0

#: indicates a limit value that came from user-defined limit overrides
SOURCE_OVERRIDE = 1

#: indicates a limit value that came from Trusted Advisor
SOURCE_TA = 2

#: indicates a limit value that came from the service's API
SOURCE_API = 3


class AwsLimit(object):

    def __init__(self, name, service, default_limit,
                 def_warning_threshold, def_critical_threshold,
                 limit_type=None, limit_subtype=None,
                 ta_service_name=None, ta_limit_name=None):
        """
        Describes one specific AWS service limit, as well as its
        current utilization, default limit, thresholds, and any
        Trusted Advisor information about this limit.

        :param name: the name of this limit (may contain spaces);
          if possible, this should be the name used by AWS, i.e. TrustedAdvisor
        :type name: string
        :param service: the :py:class:`~._AwsService` class that
          this limit is for
        :type service: :py:class:`~._AwsService`
        :param default_limit: the default value of this limit for new accounts
        :type default_limit: int
        :param def_warning_threshold: the default warning threshold, as an
          integer percentage.
        :type def_warning_threshold: int
        :param def_critical_threshold: the default critical threshold, as an
          integer percentage.
        :type def_critical_threshold: int
        :param limit_type: the type of resource this limit describes, specified
          as one of the type names used in
          `CloudFormation <http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html>`_  # noqa
          such as "AWS::EC2::Instance" or "AWS::RDS::DBSubnetGroup".
        :param limit_subtype: resource sub-type for this limit, if applicable,
          such as "t2.micro" or "SecurityGroup"
        :type limit_subtype: str
        :param ta_service_name: The service name returned by Trusted Advisor
          for this limit, if different from the name of ``service``
        :type ta_service_name: str
        :param ta_limit_name: The limit name returned by Trusted Advisor for
          this limit, if different from ``name``.
        :type ta_limit_name: str
        :raises: ValueError
        """
        if def_warning_threshold >= def_critical_threshold:
            raise ValueError("critical threshold must be greater than warning "
                             "threshold")
        self.name = name
        self.service = service
        self.default_limit = default_limit
        self.limit_type = limit_type
        self.limit_subtype = limit_subtype
        self.limit_override = None
        self.override_ta = True
        self.ta_limit = None
        self.ta_unlimited = False
        self.api_limit = None
        self._current_usage = []
        self.def_warning_threshold = def_warning_threshold
        self.def_critical_threshold = def_critical_threshold
        self.warn_percent = None
        self.warn_count = None
        self.crit_percent = None
        self.crit_count = None
        self._warnings = []
        self._criticals = []
        self._ta_service_name = ta_service_name
        self._ta_limit_name = ta_limit_name

    def set_limit_override(self, limit_value, override_ta=True):
        """
        Set a new value for this limit, to override the default
        (such as when AWS Support has increased a limit of yours).
        If ``override_ta`` is True, this value will also supersede
        any found through Trusted Advisor.

        :param limit_value: the new limit value
        :type limit_value: int
        :param override_ta: whether or not to also override Trusted
          Advisor information
        :type override_ta: bool
        """
        self.limit_override = limit_value
        self.override_ta = override_ta

    def _set_ta_limit(self, limit_value):
        """
        Set the value for the limit as reported by Trusted Advisor.

        This method should only be called by :py:class:`~.TrustedAdvisor`.

        :param limit_value: the Trusted Advisor limit value
        :type limit_value: int
        """
        self.ta_limit = limit_value

    def _set_ta_unlimited(self):
        """
        Set state to indicate that TrustedAdvisor reports this limit as
        having no maximum (unlimited).

        This method should only be called by :py:class:`~.TrustedAdvisor`.
        """
        self.ta_unlimited = True

    def _set_api_limit(self, limit_value):
        """
        Set the value for the limit as reported by the service's API.

        This method should only be called from the Service class.

        :param limit_value: the API limit value
        :type limit_value: int
        """
        self.api_limit = limit_value

    def get_limit_source(self):
        """
        Return :py:const:`~awslimitchecker.limit.SOURCE_DEFAULT` if
        :py:meth:`~.get_limit` returns the default limit,
        :py:const:`~awslimitchecker.limit.SOURCE_OVERRIDE` if it returns a
        manually-overridden limit,
        :py:const:`~awslimitchecker.limit.SOURCE_TA` if it returns a limit from
        Trusted Advisor, or   :py:const:`~awslimitchecker.limit.SOURCE_API`
        if it returns a limit retrieved from the service's API.

        :returns: one of :py:const:`~awslimitchecker.limit.SOURCE_DEFAULT`,
          :py:const:`~awslimitchecker.limit.SOURCE_OVERRIDE`, or
          :py:const:`~awslimitchecker.limit.SOURCE_TA`, or
          :py:const:`~awslimitchecker.limit.SOURCE_API`
        :rtype: int
        """
        if self.limit_override is not None and (
                self.override_ta is True or
                (self.ta_limit is None and self.ta_unlimited is False)
        ):
            return SOURCE_OVERRIDE
        if self.api_limit is not None:
            return SOURCE_API
        if self.ta_limit is not None or self.ta_unlimited is True:
            return SOURCE_TA
        return SOURCE_DEFAULT

    def get_limit(self):
        """
        Returns the effective limit value for this Limit,
        taking into account limit overrides and Trusted
        Advisor data. None is returned for limits that are
        explicitly unlimited.

        :returns: effective limit value, ``int`` or ``None``
        """
        limit_type = self.get_limit_source()
        if limit_type == SOURCE_OVERRIDE:
            return self.limit_override
        elif limit_type == SOURCE_API:
            return self.api_limit
        elif limit_type == SOURCE_TA:
            if self.ta_unlimited is True:
                return None
            return self.ta_limit
        return self.default_limit

    def get_current_usage(self):
        """
        Get the current usage for this limit, as a list of
        :py:class:`~.AwsLimitUsage` instances.

        :returns: list of current usage values
        :rtype: :py:obj:`list` of :py:class:`~.AwsLimitUsage`
        """
        return self._current_usage

    def get_current_usage_str(self):
        """
        Get the a string describing the current usage for this limit.

        If no usage has been added for this limit, the result will be
        "<unknown>".

        If the limit has only one current usage instance, this will be
        that instance's :py:meth:`~.AwsLimitUsage.__str__` value.

        If the limit has more than one current usage instance, this
        will be the a string of the form ``max: X (Y)`` where ``X`` is
        the :py:meth:`~.AwsLimitUsage.__str__` value of the instance
        with the maximum value, and ``Y`` is a comma-separated list
        of the :py:meth:`~.AwsLimitUsage.__str__` values of all usage
        instances in ascending order.

        :returns: representation of current usage
        :rtype: string
        """
        if len(self._current_usage) == 0:
            return '<unknown>'
        if len(self._current_usage) == 1:
            return str(self._current_usage[0])
        lim_str = ', '.join([str(x) for x in sorted(self._current_usage)])
        s = 'max: {m} ({l})'.format(
            m=str(max(self._current_usage)),
            l=lim_str
        )
        return s

    def _add_current_usage(self, value, resource_id=None, aws_type=None):
        """
        Add a new current usage value for this limit.

        Creates a new :py:class:`~.AwsLimitUsage` instance and
        appends it to the internal list. If more than one usage value
        is given to this service, they should have ``id`` and
        ``aws_type`` set.

        This method should only be called from the :py:class:`~._AwsService`
        instance that created and manages this Limit.

        :param value: the numeric usage value
        :type value: :py:obj:`int` or :py:obj:`float`
        :param resource_id: If there can be multiple usage values for one limit,
          an AWS ID for the resource this instance describes
        :type resource_id: string
        :param aws_type: if ``id`` is not None, the AWS resource type
          that ID represents. As a convention, we use the AWS Resource
          Type names used by
          `CloudFormation <http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html>`_  # noqa
        :type aws_type: string
        """
        self._current_usage.append(
            AwsLimitUsage(
                self,
                value,
                resource_id=resource_id,
                aws_type=aws_type
            )
        )

    def _reset_usage(self):
        """Discard all current usage data."""
        self._current_usage = []

    def _get_thresholds(self):
        """
        Get the warning and critical thresholds for this Limit.

        Return type is a 4-tuple of:

        1. warning integer (usage) threshold, or None
        2. warning percent threshold
        3. critical integer (usage) threshold, or None
        4. critical percent threshold

        :rtype: tuple
        """
        t = (
            self.warn_count,
            self.warn_percent or self.def_warning_threshold,
            self.crit_count,
            self.crit_percent or self.def_critical_threshold,
        )
        return t

    def set_threshold_override(self, warn_percent=None, warn_count=None,
                               crit_percent=None, crit_count=None):
        """
        Override the default warning and critical thresholds used to evaluate
        this limit's usage. Theresholds can be specified as a percentage
        of the limit, or as a usage count, or both.

        **Note:** The percent thresholds (``warn_percent`` and ``crit_percent``)
        have default values that are set globally for awslimitchecker, unlike
        the count thresholds. When setting threshold overrides to quiet or
        suppress alerts for a limit, you **must** set the percent thresholds.
        If you only set overrides for the ``count`` thresholds, the percent
        thresholds will continue to be evaluated at their awslimitchecker-wide
        default, and likely prevent alerts from being suppressed.

        see :py:meth:`~.check_thresholds` for further information on threshold
        evaluation.

        :param warn_percent: new warning threshold, percentage used
        :type warn_percent: int
        :param warn_count: new warning threshold, actual count/number
        :type warn_count: int
        :param crit_percent: new critical threshold, percentage used
        :type crit_percent: int
        :param crit_count: new critical threshold, actual count/number
        :type crit_count: int
        """
        self.warn_percent = warn_percent
        self.warn_count = warn_count
        self.crit_percent = crit_percent
        self.crit_count = crit_count

    def check_thresholds(self):
        """
        Check this limit's current usage against the specified default
        thresholds, and any custom theresholds that have been set on the
        class instance. Return True if usage is within thresholds, or false if
        warning or critical thresholds have been surpassed.

        This method sets internal variables in this instance which can be
        queried via :py:meth:`~.get_warnings` and :py:meth:`~.get_criticals`
        to obtain further details about the thresholds that were crossed.

        **Note** This function returns False if *any* thresholds were crossed.
        Please be aware of this when setting threshold overrides to suppress
        alerts. Each threshold (``warn_percent``, ``warn_count``,
        ``crit_percent``, ``crit_count``) that has been set is evaluated
        individually and the result appended to a list of warnings or criticals,
        respectively. If *any* of these evaluations failed, the method returns
        False.

        :returns: False if any thresholds were crossed, True otherwise
        :rtype: bool
        """
        limit = self.get_limit()
        if limit is None:
            # our limit is explicitly unlimited
            return True
        (warn_int, warn_pct, crit_int, crit_pct) = self._get_thresholds()
        all_ok = True
        for u in self._current_usage:
            usage = u.get_value()
            pct = (usage / (limit * 1.0)) * 100
            if crit_int is not None and usage >= crit_int:
                self._criticals.append(u)
                all_ok = False
            elif pct >= crit_pct:
                self._criticals.append(u)
                all_ok = False
            elif warn_int is not None and usage >= warn_int:
                self._warnings.append(u)
                all_ok = False
            elif pct >= warn_pct:
                self._warnings.append(u)
                all_ok = False
        return all_ok

    def get_warnings(self):
        """
        Return a list of :py:class:`~.AwsLimitUsage` instances that
        crossed the warning threshold. These objects are comparable
        and can be sorted.

        :rtype: list
        """
        return self._warnings

    def get_criticals(self):
        """
        Return a list of :py:class:`~.AwsLimitUsage` instances that
        crossed the critical threshold. These objects are comparable
        and can be sorted.

        :rtype: list
        """
        return self._criticals

    @property
    def ta_service_name(self):
        """
        Return the effective Trusted Advisor service name that this limit's
        data will have. This should be ``self._ta_service_name`` if set,
        otherwise the name of ``self.service``.

        :return: Trusted Advisor service data name
        :rtype: str
        """
        if self._ta_service_name is not None:
            return self._ta_service_name
        return self.service.service_name

    @property
    def ta_limit_name(self):
        """
        Return the effective Trusted Advisor limit name that this limit's
        data will have. This should be ``self._ta_limit_name`` if set,
        otherwise ``self.name``.

        :return: Trusted Advisor limit data name
        :rtype: str
        """
        if self._ta_limit_name is not None:
            return self._ta_limit_name
        return self.name


class AwsLimitUsage(object):

    def __init__(self, limit, value, resource_id=None, aws_type=None):
        """
        This object describes the usage of an AWS resource, with the capability
        of containing information about the resource beyond an integer usage.

        The simplest case is an account- / region-wide count, such as the
        number of running EC2 Instances, in which case a simple integer value
        is sufficient. In this case, the :py:class:`~.AwsLimit` would have one
        instance of this class for the single value.

        In more complex cases, such as the "Subnets per VPC", the limit is
        applied by AWS on multiple resources (once per VPC). In this case,
        the :py:class:`~.AwsLimit` should have one instance of this class
        per VPC, so we can determine *which* VPCs have crossed thresholds.

        AwsLimitUsage objects are comparable based on their numeric ``value``.

        :param limit: the AwsLimit that this instance describes
        :type limit: :py:class:`~.AwsLimit`
        :param value: the numeric usage value
        :type value: :py:obj:`int` or :py:obj:`float`
        :param resource_id: If there can be multiple usage values for one limit,
          an AWS ID for the resource this instance describes
        :type resource_id: string
        :param aws_type: if ``id`` is not None, the AWS resource type
          that ID represents. As a convention, we use the AWS Resource
          Type names used by
          `CloudFormation <http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html>`_  # noqa
        :type aws_type: string
        """
        self.limit = limit
        self.value = value
        self.resource_id = resource_id
        self.aws_type = aws_type

    def get_value(self):
        """
        Get the current usage value

        :returns: current usage value
        :rtype: :py:obj:`int` or :py:obj:`float`
        """
        return self.value

    def __str__(self):
        """
        Return a string representation of this object.

        If ``id`` is not set, return ``value`` formatted as a string;
        otherwise, return a string of the format ``id=value``.

        :rtype: string
        """
        s = '{v}'.format(v=self.value)
        if self.resource_id is not None:
            s = self.resource_id + '=' + s
        return s

    def __eq__(self, other):
        return self.value == other.value

    def __ne__(self, other):
        return self.value != other.value

    def __gt__(self, other):
        return self.value > other.value

    def __lt__(self, other):
        return self.value < other.value

    def __ge__(self, other):
        return self.value >= other.value
