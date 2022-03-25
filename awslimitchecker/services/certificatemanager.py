"""
awslimitchecker/services/certificatemanager.py

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

import abc  # noqa
import logging

from .base import _AwsService
from ..limit import AwsLimit
from ..utils import paginate_dict

logger = logging.getLogger(__name__)


class _CertificatemanagerService(_AwsService):

    service_name = 'CertificateManager'
    api_name = 'acm'  # AWS API name to connect to (boto3.client)
    quotas_service_code = 'acm'

    def find_usage(self):
        """
        List CloudFront distributions by calling AWS list_certificates, and
        update usage in self.limits for the limit 'ACM certificates'
        """
        logger.debug("Checking usage for service %s", self.service_name)
        self.connect()
        for lim in self.limits.values():
            lim._reset_usage()

        self._find_usage_certificates()

        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_certificates(self):
        """find usage for ACM certificates"""
        res = paginate_dict(
            self.conn.list_certificates,
            alc_marker_path=['NextToken'],
            alc_data_path=['CertificateSummaryList'],
            alc_marker_param='NextToken'
        )
        if 'CertificateSummaryList' not in res:
            nb_certificates = 0
        else:
            nb_certificates = len(res['CertificateSummaryList'])
        self.limits['ACM certificates']._add_current_usage(nb_certificates)

    def get_limits(self):
        """
        Return all known limits for this service, as a dict of their names
        to :py:class:`~.AwsLimit` objects.

        :returns: dict of limit names to :py:class:`~.AwsLimit` objects
        :rtype: dict
        """
        if self.limits != {}:
            return self.limits
        limits = {}
        limits['ACM certificates'] = AwsLimit(
            'ACM certificates',
            self,
            1000,
            self.warning_threshold,
            self.critical_threshold
        )
        self.limits = limits
        return limits

    def required_iam_permissions(self):
        """
        Return a list of IAM Actions required for this Service to function
        properly. All Actions will be shown with an Effect of "Allow"
        and a Resource of "*".

        :returns: list of IAM Action strings
        :rtype: list
        """
        return [
            "acm:ListCertificates",
        ]
