"""
awslimitchecker/limit.py

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
bugs please submit them at <https://github.com/jantman/pydnstest> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""


class _AwsLimit(object):

    def __init__(self, name, service_name, default_limit,
                 limit_type=None, limit_subtype=None):
        """
        Describes one specific AWS service limit, as well as its
        current utilization, default limit, thresholds, and any
        Trusted Advisor information about this limit.

        :param name: the name of this limit (may contain spaces);
        if possible, this should be the name used by AWS, i.e. TrustedAdvisor
        :type name: string
        :param service_name: the name of the service this limit is for;
        this should be the ``service_name`` attribute of an
        :py:class:`~._AwsService` class.
        :type service_name: string
        :param default_limit: the default value of this limit for new accounts
        :type default_limit: int
        :param limit_type: the type of resource this limit describes, such as
        "On-Demand Instance" or "VPC"
        :param limit_subtype: resource sub-type for this limit, if applicable,
        such as "t2.micro" or "SecurityGroup"
        """
        self.name = name
        self.service_name = service_name
        self.default_limit = default_limit
        self.limit_type = limit_type
        self.limit_subtype = limit_subtype
        self.limit_override = None
        self.override_ta = True
        self._current_usage = None

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

    def get_current_usage(self):
        """
        Get the current usage value for this limit, or
        None if not yet set.

        :returns: current usage value, or None
        :rtype: :py:obj:`int` or :py:obj:`None`
        """
        return self._current_usage

    def _set_current_usage(self, value):
        """
        Set this limit's current usage value.

        This method should only be called from the :py:class:`~._AwsService`
        instance that created and manages this Limit.

        :param value: current usage value for this limit
        :type value: int
        """
        self._current_usage = value

    def check_thresholds(self, default_warning=80, default_critical=100):
        """
        Check this limit's current usage against the specified default
        thresholds, and any custom theresholds that have been set on the
        instance. Return True if usage is within thresholds, or false if
        warning or critical thresholds have been surpassed.

        This method sets internal variables in this instance which can be
        queried via :py:meth:`~.get_warnings` and :py:meth:`~.get_criticals`
        to obtain further details about the thresholds that were crossed.

        This method handles limits that are evaluated both globally
        (region- and account-wide) as well as limits on specific
        AWS resources or types.

        :param default_warning: default warning threshold in percentage;
          usage higher than this percent of the limit will be considered
          a warning
        :type default_warning: :py:obj:`int` or :py:obj:`float` percentage
        :param default_critical: default critical threshold in percentage;
          usage higher than this percent of the limit will be considered
          a critical
        :type default_critical: :py:obj:`int` or :py:obj:`float` percentage
        """
        pass

    def get_warnings(self):
        """
        Return a dict describing any warning-level thresholds that were
        crossed for this limit. Keys are unique identifiers for the resource
        that crossed the limit, or the name of the limit itself
        """
        pass
