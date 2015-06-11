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
bugs please submit them at <https://github.com/jantman/pydnstest> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

from .services import _services
from .version import _get_version, _get_project_url
import logging
logger = logging.getLogger(__name__)

# suppress boto internal logging
boto_log = logging.getLogger("boto")
boto_log.setLevel(logging.WARNING)
boto_log.propagate = True


class AwsLimitChecker(object):

    def __init__(self, warning_threshold=80, critical_threshold=99):
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
        """
        logger.warning("awslimitchecker {v} is AGPL-licensed free software; "
                       "all users have a right to the full source code of "
                       "this version. See <{u}>".format(
                           v=_get_version(),
                           u=_get_project_url(),
                       ))
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.services = {}
        for sname, cls in _services.iteritems():
            self.services[sname] = cls(warning_threshold, critical_threshold)

    def get_version(self):
        """
        Return the version of awslimitchecker currently running.

        :returns: current awslimitchecker version
        :rtype: string
        """
        return _get_version()

    def get_project_url(self):
        """
        Return the URL for the awslimitchecker project.

        :returns: URL of where to find awslimitchecker
        :rtype: string
        """
        return _get_project_url()

    def get_limits(self, service=None):
        """
        Return all :py:class:`~.AwsLimit` objects for the given
        service name, or for all services if ``service`` is None.

        If ``service`` is specified, the returned dict has one element,
        the service name, whose value is a nested dict as described below.

        :param service: the name of one service to return limits for
        :type service: string
        :returns: dict of service name (string) to nested dict
          of limit name (string) to limit (:py:class:`~.AwsLimit`)
        :rtype: dict
        """
        res = {}
        if service is not None:
            return {service: self.services[service].get_limits()}
        for sname, cls in self.services.iteritems():
            res[sname] = cls.get_limits()
        return res

    def get_service_names(self):
        """
        Return a list of all known service names

        :returns: list of service names
        :rtype: list
        """
        return sorted(self.services.keys())

    def find_usage(self, service=None):
        """
        For each limit in the specified service (or all services if
        ``service`` is ``None``), query the AWS API via :py:pkg:`boto`
        and find the current usage amounts for that limit.

        This method updates the ``current_usage`` attribute of the
        :py:class:`~.AwsLimit` objects for each service, which can
        then be queried using :py:meth:`~.get_limits`.

        :param service: :py:class:`~._AwsService` name, or ``None`` to
          check all services.
        :type services: :py:obj:`None` or :py:obj:`string` service name
        """
        if service is not None:
            logger.debug("Finding usage for service: {s}".format(
                s=self.services[service].service_name))
            self.services[service].find_usage()
            return
        for sname, cls in self.services.iteritems():
            logger.debug("Finding usage for service: {s}".format(
                s=cls.service_name))
            cls.find_usage()

    def set_limit_overrides(self, override_dict, override_ta=True):
        """
        Set manual overrides on AWS service limits, i.e. if you
        had limits increased by AWS support. This takes a dict in
        the same form as that returned by :py:meth:`~.get_limits`,
        i.e. service_name (str) keys to nested dict of limit_name
        (str) to limit value (int) like:

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
        :raises: ValueError if limit_name is not known to the service instance
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

    def check_thresholds(self, service=None):
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
        :returns: dict of service name (string) to nested dict
          of limit name (string) to limit (:py:class:`~.AwsLimit`)
        :rtype: dict
        """
        res = {}
        if service is not None:
            return {service: self.services[service].check_thresholds()}
        for sname, cls in self.services.iteritems():
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
        required_actions = []
        for sname, cls in self.services.iteritems():
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
