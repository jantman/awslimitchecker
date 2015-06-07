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

from awslimitchecker.services import services
import logging
logger = logging.getLogger(__name__)


class AwsLimitChecker(object):

    def __init__(self):
        """
        Main AwsLimitChecker class - this should be the only externally-used
        portion of awslimitchecker.

        Constructor builds ``self.services`` as a dict of service_name (str)
        to AwsService instance.
        """
        self.services = {}
        for sname, cls in services.iteritems():
            self.services[sname] = cls()

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
            return self.services[service].get_limits()
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

    def check_services(self, services=None, region=None):
        """
        Check the specified services.

        :param services: a list of :py:class:`~.service.AwsService`
          names, or None to check all services
        :type services: None or list of strings
        """
        raise NotImplementedError()

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
        :py:meth:`~.AwsService.set_limit_override` on the corresponding
        AwsService instance.

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
        logger.debug("Applying limit overrides")
        for svc_name in override_dict:
            for lim_name in override_dict[svc_name]:
                self.services[svc_name].set_limit_override(
                    lim_name,
                    override_dict[svc_name][lim_name],
                    override_ta=override_ta
                )
        logger.info("Limit overrides applied.")
