"""
awslimitchecker/checker.py

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

from .services import _services
from .version import _get_version_info
from .trustedadvisor import TrustedAdvisor
import sys
import logging

logger = logging.getLogger(__name__)


class AwsLimitChecker(object):

    def __init__(self, warning_threshold=80, critical_threshold=99,
                 account_id=None, account_role=None, region=None,
                 external_id=None):
        """
        Main AwsLimitChecker class - this should be the only externally-used
        portion of awslimitchecker.

        Constructor builds ``self.services`` as a dict of service_name (str)
        to :py:class:`~._AwsService` instance, and sets limit
        thresholds.

        :param warning_threshold: the default warning threshold, as an
          integer percentage, for any limits without a specifically-set
          threshold.
        :type warning_threshold: int
        :param critical_threshold: the default critical threshold, as an
          integer percentage, for any limits without a specifically-set
          threshold.
        :type critical_threshold: int
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
        """
        # ###### IMPORTANT license notice ##########
        # Pursuant to Sections 5(b) and 13 of the GNU Affero General Public
        # License, version 3, this notice MUST NOT be removed, and MUST be
        # displayed to ALL USERS of this software, even if they interact with
        # it remotely over a network.
        #
        # Furthermore, _get_version_info() MUST return a valid URL pointing
        # to the EXACT identical source code that is currently running.
        #
        # See the "Development" section of the awslimitchecker documentation
        # (docs/source/development.rst or
        # <http://awslimitchecker.readthedocs.org/en/latest/development.html> )
        # for further information.
        # ###### IMPORTANT license notice ##########
        self.vinfo = _get_version_info()
        sys.stderr.write(
            "awslimitchecker %s is AGPL-licensed free software; "
            "all users have a right to the full source code of "
            "this version. See <%s>\n" % (
                self.vinfo.version_str,
                self.vinfo.url
            )
        )
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.account_id = account_id
        self.account_role = account_role
        self.external_id = external_id
        self.region = region
        self.services = {}
        self.ta = TrustedAdvisor(
            account_id=account_id,
            account_role=account_role,
            region=region,
            external_id=external_id
        )
        for sname, cls in _services.items():
            self.services[sname] = cls(warning_threshold, critical_threshold,
                                       account_id, account_role, region,
                                       external_id)

    def get_version(self):
        """
        Return the version of awslimitchecker currently running.

        :returns: current awslimitchecker version
        :rtype: string
        """
        return self.vinfo.version_str

    def get_project_url(self):
        """
        Return the URL for the awslimitchecker project.

        :returns: URL of where to find awslimitchecker
        :rtype: string
        """
        return self.vinfo.url

    def get_limits(self, service=None, use_ta=True):
        """
        Return all :py:class:`~.AwsLimit` objects for the given
        service name, or for all services if ``service`` is None.

        If ``service`` is specified, the returned dict has one element,
        the service name, whose value is a nested dict as described below.

        :param service: the name of one service to return limits for
        :type service: string
        :param use_ta: check Trusted Advisor for information on limits
        :type use_ta: bool
        :returns: dict of service name (string) to nested dict
          of limit name (string) to limit (:py:class:`~.AwsLimit`)
        :rtype: dict
        """
        res = {}
        to_get = self.services
        if service is not None:
            to_get = {service: self.services[service]}
        if use_ta:
            self.ta.update_limits(to_get)
        for sname, cls in to_get.items():
            res[sname] = cls.get_limits()
        return res

    def get_service_names(self):
        """
        Return a list of all known service names

        :returns: list of service names
        :rtype: list
        """
        return sorted(self.services.keys())

    def find_usage(self, service=None, use_ta=True):
        """
        For each limit in the specified service (or all services if
        ``service`` is ``None``), query the AWS API via :py:mod:`boto`
        and find the current usage amounts for that limit.

        This method updates the ``current_usage`` attribute of the
        :py:class:`~.AwsLimit` objects for each service, which can
        then be queried using :py:meth:`~.get_limits`.

        :param service: :py:class:`~._AwsService` name, or ``None`` to
          check all services.
        :type service: :py:obj:`None`, or :py:obj:`string` service name to get
        :param use_ta: check Trusted Advisor for information on limits
        :type use_ta: bool
        """
        to_get = self.services
        if service is not None:
            to_get = {service: self.services[service]}
        if use_ta:
            self.ta.update_limits(to_get)
        for cls in to_get.values():
            logger.debug("Finding usage for service: %s", cls.service_name)
            cls.find_usage()

    def set_limit_overrides(self, override_dict, override_ta=True):
        """
        Set manual overrides on AWS service limits, i.e. if you
        had limits increased by AWS support. This takes a dict in
        the same form as that returned by :py:meth:`~.get_limits`,
        i.e. service_name (str) keys to nested dict of limit_name
        (str) to limit value (int) like:
        ::

            {
                'EC2': {
                  'Running On-Demand t2.micro Instances': 1000,
                  'Running On-Demand r3.4xlarge Instances': 1000,
                }
            }

        Internally, for each limit override for each service in
        ``override_dict``, this method calls
        :py:meth:`~._AwsService.set_limit_override` on the corresponding
        _AwsService instance.

        Explicitly set limit overrides using this method will take
        precedence over default limits. They will also take precedence over
        limit information obtained via Trusted Advisor, unless ``override_ta``
        is set to ``False``.

        :param override_dict: dict of overrides to default limits
        :type override_dict: dict
        :param override_ta: whether or not to use this value even if Trusted
          Advisor supplies limit information
        :type override_ta: bool
        :raises: :py:exc:`exceptions.ValueError` if limit_name is not known to
          the service instance
        """
        for svc_name in override_dict:
            for lim_name in override_dict[svc_name]:
                self.services[svc_name].set_limit_override(
                    lim_name,
                    override_dict[svc_name][lim_name],
                    override_ta=override_ta
                )

    def set_limit_override(self, service_name, limit_name,
                           value, override_ta=True):
        """
        Set a manual override on an AWS service limits, i.e. if you
        had limits increased by AWS support.

        This method calls :py:meth:`~._AwsService.set_limit_override`
        on the corresponding _AwsService instance.

        Explicitly set limit overrides using this method will take
        precedence over default limits. They will also take precedence over
        limit information obtained via Trusted Advisor, unless ``override_ta``
        is set to ``False``.

        :param service_name: the name of the service to override limit for
        :type service_name: string
        :param limit_name: the name of the limit to override:
        :type limit_name: string
        :param value: the new (overridden) limit value)
        :type value: int
        :param override_ta: whether or not to use this value even if Trusted
          Advisor supplies limit information
        :type override_ta: bool
        :raises: ValueError if limit_name is not known to the service instance
        """
        self.services[service_name].set_limit_override(
            limit_name,
            value,
            override_ta=override_ta
        )

    def set_threshold_overrides(self, override_dict):
        """
        Set manual overrides on the threshold (used for determining
        warning/critical status) a dict of limits. See
        :py:class:`~.AwsLimitChecker` for information on Warning and
        Critical thresholds.

        Dict is composed of service name keys (string) to dict of
        limit names (string), to dict of threshold specifications.
        Each threhold specification dict can contain keys 'warning'
        or 'critical', each having a value of a dict containing
        keys 'percent' or 'count', to an integer value.

        Example:
        ::

            {
                'EC2': {
                    'SomeLimit': {
                        'warning': {
                            'percent': 80,
                            'count': 8,
                        },
                        'critical': {
                            'percent': 90,
                            'count': 9,
                        }
                    }
                }
            }

        See :py:meth:`~.AwsLimit.set_threshold_override`.

        :param override_dict: nested dict of threshold overrides
        :type override_dict: dict
        """
        for svc_name in sorted(override_dict):
            for lim_name in sorted(override_dict[svc_name]):
                d = override_dict[svc_name][lim_name]
                kwargs = {}
                if 'warning' in d:
                    if 'percent' in d['warning']:
                        kwargs['warn_percent'] = d['warning']['percent']
                    if 'count' in d['warning']:
                        kwargs['warn_count'] = d['warning']['count']
                if 'critical' in d:
                    if 'percent' in d['critical']:
                        kwargs['crit_percent'] = d['critical']['percent']
                    if 'count' in d['critical']:
                        kwargs['crit_count'] = d['critical']['count']
                self.services[svc_name].set_threshold_override(
                    lim_name,
                    **kwargs
                )

    def set_threshold_override(self, service_name, limit_name,
                               warn_percent=None, warn_count=None,
                               crit_percent=None, crit_count=None):
        """
        Set a manual override on the threshold (used for determining
        warning/critical status) for a specific limit. See
        :py:class:`~.AwsLimitChecker` for information on Warning and
        Critical thresholds.

        See :py:meth:`~.AwsLimit.set_threshold_override`.

        :param service_name: the name of the service to override limit for
        :type service_name: string
        :param limit_name: the name of the limit to override:
        :type limit_name: string
        :param warn_percent: new warning threshold, percentage used
        :type warn_percent: int
        :param warn_count: new warning threshold, actual count/number
        :type warn_count: int
        :param crit_percent: new critical threshold, percentage used
        :type crit_percent: int
        :param crit_count: new critical threshold, actual count/number
        :type crit_count: int
        """
        self.services[service_name].set_threshold_override(
            limit_name,
            warn_percent=warn_percent,
            warn_count=warn_count,
            crit_percent=crit_percent,
            crit_count=crit_count
        )

    def check_thresholds(self, service=None, use_ta=True):
        """
        Check all limits and current usage against their specified thresholds;
        return all :py:class:`~.AwsLimit` instances that have crossed
        one or more of their thresholds.

        If ``service`` is specified, the returned dict has one element,
        the service name, whose value is a nested dict as described below;
        otherwise it includes all known services.

        The returned :py:class:`~.AwsLimit` objects can be interrogated
        for their limits (:py:meth:`~.AwsLimit.get_limit`) as well as
        the details of usage that crossed the thresholds
        (:py:meth:`~.AwsLimit.get_warnings` and
        :py:meth:`~.AwsLimit.get_criticals`).

        :param service: the name of one service to return results for
        :type service: string
        :param use_ta: check Trusted Advisor for information on limits
        :type use_ta: bool
        :returns: dict of service name (string) to nested dict
          of limit name (string) to limit (:py:class:`~.AwsLimit`)
        :rtype: dict
        """
        res = {}
        to_get = self.services
        if service is not None:
            to_get = {service: self.services[service]}
        if use_ta:
            self.ta.update_limits(to_get)
        for sname, cls in to_get.items():
            tmp = cls.check_thresholds()
            if len(tmp) > 0:
                res[sname] = tmp
        return res

    def get_required_iam_policy(self):
        """
        Return an IAM policy granting all of the permissions needed for
        awslimitchecker to fully function. This returns a dict suitable
        for json serialization to a valid IAM policy.

        Internally, this calls :py:meth:`~._AwsService.required_iam_permissions`
        on each :py:class:`~._AwsService` instance.

        :returns: dict representation of IAM Policy
        :rtype: dict
        """
        required_actions = [
            'support:*',
            'trustedadvisor:Describe*',
        ]
        for cls in self.services.values():
            required_actions.extend(cls.required_iam_permissions())
        policy = {
            'Version': '2012-10-17',
            'Statement': [{
                'Effect': 'Allow',
                'Resource': '*',
                'Action': sorted(required_actions),
            }],
        }
        return policy
