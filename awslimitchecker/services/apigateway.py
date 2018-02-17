"""
awslimitchecker/services/apigateway.py

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
from awslimitchecker.utils import paginate_dict

logger = logging.getLogger(__name__)


class _ApigatewayService(_AwsService):

    service_name = 'ApiGateway'
    api_name = 'apigateway'  # AWS API name to connect to (boto3.client)

    def find_usage(self):
        """
        Determine the current usage for each limit of this service,
        and update corresponding Limit via
        :py:meth:`~.AwsLimit._add_current_usage`.
        """
        logger.debug("Checking usage for service %s", self.service_name)
        self.connect()
        for lim in self.limits.values():
            lim._reset_usage()
        self._find_usage_apis()
        self._find_usage_api_keys()
        self._find_usage_certs()
        self._find_usage_plans()
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_apis(self):
        """
        Find usage on APIs / RestAPIs, and resources that are limited per-API.
        Update `self.limits`.
        """
        api_ids = []
        logger.debug('Finding usage for APIs')
        paginator = self.conn.get_paginator('get_rest_apis')
        for resp in paginator.paginate():
            for api in resp['items']:
                api_ids.append(api['id'])
        logger.debug('Found %d APIs', len(api_ids))
        self.limits['APIs per account']._add_current_usage(
            len(api_ids), aws_type='AWS::ApiGateway::RestApi'
        )
        # now the per-API limits...
        warn_stages_paginated = None
        logger.debug('Finding usage for per-API limits')
        for api_id in api_ids:
            res_count = 0
            paginator = self.conn.get_paginator('get_resources')
            for resp in paginator.paginate(restApiId=api_id):
                res_count += len(resp['items'])
            self.limits['Resources per API']._add_current_usage(
                res_count, resource_id=api_id,
                aws_type='AWS::ApiGateway::Resource'
            )
            doc_parts = paginate_dict(
                self.conn.get_documentation_parts,
                restApiId=api_id,
                alc_marker_path=['position'],
                alc_data_path=['items'],
                alc_marker_param='position'
            )
            self.limits['Documentation parts per API']._add_current_usage(
                len(doc_parts), resource_id=api_id,
                aws_type='AWS::ApiGateway::DocumentationPart'
            )
            # note that per the boto3 docs, there's no pagination of this...
            stages = self.conn.get_stages(restApiId=api_id)
            if len(set(stages.keys()) - set(['item', 'ResponseMetadata'])) > 0:
                warn_stages_paginated = stages.keys()
            self.limits['Stages per API']._add_current_usage(
                len(stages['item']), resource_id=api_id,
                aws_type='AWS::ApiGateway::Stage'
            )
            authorizers = paginate_dict(
                self.conn.get_authorizers,
                restApiId=api_id,
                alc_marker_path=['position'],
                alc_data_path=['items'],
                alc_marker_param='position'
            )
            self.limits['Custom authorizers per API']._add_current_usage(
                len(authorizers), resource_id=api_id,
                aws_type='AWS::ApiGateway::Authorizer'
            )
        if warn_stages_paginated is not None:
            logger.warning(
                'APIGateway get_stages returned more keys than present in '
                'boto3 docs: %s', sorted(warn_stages_paginated)
            )

    def _find_usage_api_keys(self):
        """
        Find usage on API Keys.
        Update `self.limits`.
        """
        logger.debug('Finding usage for API Keys')
        key_count = 0
        paginator = self.conn.get_paginator('get_api_keys')
        for resp in paginator.paginate():
            key_count += len(resp['items'])
        self.limits['API keys per account']._add_current_usage(
            key_count, aws_type='AWS::ApiGateway::ApiKey'
        )

    def _find_usage_certs(self):
        """
        Find usage on Client Certificates. Update `self.limits`.
        """
        logger.debug('Finding usage for Client Certificates')
        cert_count = 0
        paginator = self.conn.get_paginator('get_client_certificates')
        for resp in paginator.paginate():
            cert_count += len(resp['items'])
        self.limits['Client certificates per account']._add_current_usage(
            cert_count, aws_type='AWS::ApiGateway::ClientCertificate'
        )

    def _find_usage_plans(self):
        """
        Find usage on Usage Plans and plans per API Key. Update `self.limits`.
        """
        logger.debug('Finding usage for Usage Plans')
        plan_count = 0
        paginator = self.conn.get_paginator('get_usage_plans')
        for resp in paginator.paginate():
            plan_count += len(resp['items'])
        self.limits['Usage plans per account']._add_current_usage(
            plan_count, aws_type='AWS::ApiGateway::UsagePlan'
        )

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
        limits['APIs per account'] = AwsLimit(
            'APIs per account',
            self,
            60,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ApiGateway::RestApi'
        )
        limits['API keys per account'] = AwsLimit(
            'API keys per account',
            self,
            500,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ApiGateway::ApiKey'
        )
        limits['Custom authorizers per API'] = AwsLimit(
            'Custom authorizers per API',
            self,
            10,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ApiGateway::Authorizer'
        )
        limits['Client certificates per account'] = AwsLimit(
            'Client certificates per account',
            self,
            60,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ApiGateway::ClientCertificate'
        )
        limits['Documentation parts per API'] = AwsLimit(
            'Documentation parts per API',
            self,
            2000,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ApiGateway::DocumentationPart'
        )
        limits['Resources per API'] = AwsLimit(
            'Resources per API',
            self,
            300,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ApiGateway::Resource'
        )
        limits['Stages per API'] = AwsLimit(
            'Stages per API',
            self,
            10,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ApiGateway::Stage'
        )
        limits['Usage plans per account'] = AwsLimit(
            'Usage plans per account',
            self,
            300,
            self.warning_threshold,
            self.critical_threshold,
            limit_type='AWS::ApiGateway::UsagePlan'
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
            "apigateway:GET",
            "apigateway:HEAD",
            "apigateway:OPTIONS"
        ]
