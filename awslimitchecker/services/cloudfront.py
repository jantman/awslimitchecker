"""
awslimitchecker/services/cloudfront.py

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
from collections import Counter

from .base import _AwsService
from ..limit import AwsLimit
from ..utils import paginate_dict

logger = logging.getLogger(__name__)


class _CloudfrontService(_AwsService):

    service_name = "CloudFront"
    api_name = "cloudfront"  # AWS API name to connect to (boto3.client)
    quotas_service_code = "cloudfront"

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

        self._find_usage_distributions()
        self._find_usage_keygroups()
        self._find_usage_origin_access_identities()
        self._find_usage_cache_policies()
        self._find_usage_origin_request_policies()

        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_distributions(self):
        """
        List CloudFront distributions by calling AWS list_distributions, and
        update usage in self.limits for the following limits:

        Per-distribution:
        - Alternate domain names (CNAMEs) per distribution
        - Cache behaviors per distribution
        - Origins per distribution
        - Origin groups per distribution
        - Key groups associated with a single distribution

        Per cache behavior:
        - Key groups associated with a single cache behavior
        - Whitelisted cookies per cache behavior
        - Whitelisted headers per cache behavior
        - Whitelisted query strings per cache behavior

        Global:
        - Distributions associated with a single key group
        - Distributions associated with a single cache policy
        - Distributions associated with a single origin request policy
        - Distributions per AWS account
        """

        # Read distribution list from AWS
        res = paginate_dict(
            self.conn.list_distributions,
            alc_marker_path=['DistributionList', 'NextMarker'],
            alc_data_path=['DistributionList', 'Items'],
            alc_marker_param='Marker'
        )
        if 'Items' not in res['DistributionList']:
            nb_distributions = 0
        else:
            distributions = res['DistributionList']['Items']
            nb_distributions = len(distributions)

            # number of times a keygroup is referenced, in all distributions
            keygroup_references = Counter()
            cache_policy_references = Counter()
            origin_request_policy_references = Counter()

            for d in distributions:
                # Count alternate domain names
                nb_aliases = 0
                if ('Aliases' in d) and ('Items' in d['Aliases']):
                    nb_aliases = len(d['Aliases']['Items'])
                self.limits[
                    'Alternate domain names (CNAMEs) per distribution'
                ]._add_current_usage(
                    nb_aliases,
                    resource_id=d['Id'],
                    aws_type='AWS::CloudFront::Distribution',
                )

                # Count cache behaviors
                # Note: the AWS documentation does not specify this, but
                # the quota includes the default cache behavior.
                nb_cache_behaviors = 1  # 1 for default cache behavior
                if ('CacheBehaviors' in d) and ('Items' in d['CacheBehaviors']):
                    nb_cache_behaviors += len(d['CacheBehaviors']['Items'])
                self.limits[
                    'Cache behaviors per distribution'
                ]._add_current_usage(
                    nb_cache_behaviors,
                    resource_id=d['Id'],
                    aws_type='AWS::CloudFront::Distribution',
                )

                # Count origins
                nb_origins = 0
                if ('Origins' in d) and ('Items' in d['Origins']):
                    nb_origins = len(d['Origins']['Items'])
                self.limits[
                    'Origins per distribution'
                ]._add_current_usage(
                    nb_origins,
                    resource_id=d['Id'],
                    aws_type='AWS::CloudFront::Distribution',
                )

                # Count origin groups
                nb_origin_groups = 0
                if ('OriginGroups' in d) and ('Items' in d['OriginGroups']):
                    nb_origin_groups = len(d['OriginGroups']['Items'])
                self.limits[
                    'Origin groups per distribution'
                ]._add_current_usage(
                    nb_origin_groups,
                    resource_id=d['Id'],
                    aws_type='AWS::CloudFront::Distribution',
                )

                # Count:
                # - keygroups in cache behaviors
                # - whitelisted cookies in cache behaviors
                # - whitelisted headers in cache behaviors
                # - whitelisted query strings in cache behaviors
                keygroups = set()
                cache_policies = set()
                origin_request_policies = set()

                # Iterate over additional cache behaviors
                if ('CacheBehaviors' in d) and ('Items' in d['CacheBehaviors']):
                    for cb in d['CacheBehaviors']['Items']:
                        res_id = "{}-cache-behavior-{}".format(
                            d['Id'], cb['PathPattern'])

                        # Count key groups
                        nb_keygroups = 0
                        if ('TrustedKeyGroups' in cb) and (
                                'Items' in cb['TrustedKeyGroups']):
                            # counting the KG even if not Enabled
                            keygroups.update(cb['TrustedKeyGroups']['Items'])
                            nb_keygroups = len(cb['TrustedKeyGroups']['Items'])
                        self.limits[
                            'Key groups associated with a single cache behavior'
                        ]._add_current_usage(nb_keygroups, resource_id=res_id)

                        # Count whitelisted cookies
                        nb_cookies = 0
                        try:
                            nb_cookies = len(cb['ForwardedValues']['Cookies'][
                                'WhitelistedNames']['Items'])
                        except KeyError:
                            pass
                        self.limits[
                            'Whitelisted cookies per cache behavior'
                        ]._add_current_usage(nb_cookies, resource_id=res_id)

                        # Count whitelisted headers
                        nb_headers = 0
                        try:
                            nb_headers = len(
                                cb['ForwardedValues']['Headers']['Items'])
                        except KeyError:
                            pass
                        self.limits[
                            'Whitelisted headers per cache behavior'
                        ]._add_current_usage(nb_headers, resource_id=res_id)

                        # Count whitelisted query strings
                        nb_querystring = 0
                        try:
                            nb_querystring = len(cb['ForwardedValues'][
                                'QueryStringCacheKeys']['Items'])
                        except KeyError:
                            pass
                        self.limits[
                            'Whitelisted query strings per cache behavior'
                        ]._add_current_usage(nb_querystring, resource_id=res_id)

                        if 'CachePolicyId' in cb:
                            cache_policies.add(cb['CachePolicyId'])
                        if 'OriginRequestPolicyId' in cb:
                            origin_request_policies.add(
                                cb['OriginRequestPolicyId'])

                # Default cache behavior
                if 'DefaultCacheBehavior' in d:
                    cb = d['DefaultCacheBehavior']
                    res_id = "{}-default-cache-behavior".format(d['Id'])

                    nb_keygroups = 0
                    if ('TrustedKeyGroups' in cb) and (
                            'Items' in cb['TrustedKeyGroups']):
                        # counting the KG even if not Enabled
                        keygroups.update(cb['TrustedKeyGroups']['Items'])
                        nb_keygroups = len(cb['TrustedKeyGroups']['Items'])

                    self.limits[
                        'Key groups associated with a single cache behavior'
                    ]._add_current_usage(nb_keygroups, resource_id=res_id)

                    # Count whitelisted cookies
                    nb_cookies = 0
                    try:
                        nb_cookies = len(cb['ForwardedValues']['Cookies'][
                            'WhitelistedNames']['Items'])
                    except KeyError:
                        pass
                    self.limits[
                        'Whitelisted cookies per cache behavior'
                    ]._add_current_usage(nb_cookies, resource_id=res_id)

                    # Count whitelisted headers
                    nb_headers = 0
                    try:
                        nb_headers = len(
                            cb['ForwardedValues']['Headers']['Items'])
                    except KeyError:
                        pass
                    self.limits[
                        'Whitelisted headers per cache behavior'
                    ]._add_current_usage(nb_headers, resource_id=res_id)

                    # Count whitelisted query strings
                    nb_querystring = 0
                    try:
                        nb_querystring = len(cb['ForwardedValues'][
                            'QueryStringCacheKeys']['Items'])
                    except KeyError:
                        pass
                    self.limits[
                        'Whitelisted query strings per cache behavior'
                    ]._add_current_usage(nb_querystring, resource_id=res_id)

                    if 'CachePolicyId' in cb:
                        cache_policies.add(cb['CachePolicyId'])
                    if 'OriginRequestPolicyId' in cb:
                        origin_request_policies.add(
                            cb['OriginRequestPolicyId'])

                self.limits[
                    'Key groups associated with a single distribution'
                ]._add_current_usage(
                    len(keygroups),
                    resource_id=d['Id'],
                    aws_type='AWS::CloudFront::Distribution',
                )

                keygroup_references.update(keygroups)
                cache_policy_references.update(cache_policies)
                origin_request_policy_references.update(origin_request_policies)

            for k, count in keygroup_references.items():
                self.limits[
                    'Distributions associated with a single key group'
                ]._add_current_usage(count, resource_id=k)

            for k, count in cache_policy_references.items():
                self.limits[
                    'Distributions associated with the same cache policy'
                ]._add_current_usage(count, resource_id=k)

            for k, count in origin_request_policy_references.items():
                self.limits[
                    'Distributions associated with the same origin request '
                    'policy'
                ]._add_current_usage(count, resource_id=k)

        self.limits['Distributions per AWS account']._add_current_usage(
            nb_distributions,
            aws_type='AWS::CloudFront::Distribution',
        )

    def _find_usage_keygroups(self):
        """
        List CloudFront key groups from AWS, and update usage in self.limits
        for the following limits:
        - Key groups per AWS account
        - Public keys in a single key group
        """

        # Read keygroup list from AWS
        res = paginate_dict(
            self.conn.list_key_groups,
            alc_marker_path=['KeyGroupList', 'NextMarker'],
            alc_data_path=['KeyGroupList', 'Items'],
            alc_marker_param='Marker'
        )
        nb_keygroups = 0
        try:
            keygroups = res['KeyGroupList']['Items']
            nb_keygroups = len(keygroups)
        except KeyError:
            pass

        self.limits['Key groups per AWS account']._add_current_usage(
            nb_keygroups,
            aws_type='AWS::CloudFront::KeyGroup',
        )

        if 'Items' in res['KeyGroupList']:
            for kg in res['KeyGroupList']['Items']:
                nb_keys = 0
                try:
                    nb_keys = len(kg['KeyGroup']['KeyGroupConfig']['Items'])
                except KeyError:
                    pass
                self.limits[
                    'Public keys in a single key group'
                ]._add_current_usage(nb_keys, resource_id=kg['KeyGroup']['Id'])

    def _find_usage_origin_access_identities(self):
        """
        List CloudFront origin access identities from AWS, and update usage in
        self.limits for the limit "Origin access identities per account".
        """

        # Read usage from AWS
        res = paginate_dict(
            self.conn.list_cloud_front_origin_access_identities,
            alc_marker_path=['CloudFrontOriginAccessIdentityList',
                             'NextMarker'],
            alc_data_path=['CloudFrontOriginAccessIdentityList', 'Items'],
            alc_marker_param='Marker'
        )
        if 'Items' not in res['CloudFrontOriginAccessIdentityList']:
            nb_origin_access_identities = 0
        else:
            origin_access_identities = res['CloudFrontOriginAccessIdentityList'
                                           ]['Items']
            nb_origin_access_identities = len(origin_access_identities)

        self.limits["Origin access identities per account"]._add_current_usage(
            nb_origin_access_identities,
            aws_type='AWS::CloudFront::KeyGroup',
        )

    def _find_usage_cache_policies(self):
        """
        List CloudFront cache policies from AWS, and update usage in
        self.limits for the following limits:

        - Cache policies per AWS account
        - Cookies per cache policy
        - Headers per cache policy
        - Query strings per cache policy
        """

        # Read usage from AWS
        res = paginate_dict(
            # count only the custom cache policies, not the managed ones
            self.conn.list_cache_policies,
            Type='custom',
            alc_marker_path=['CachePolicyList',
                             'NextMarker'],
            alc_data_path=['CachePolicyList', 'Items'],
            alc_marker_param='Marker'
        )
        if 'Items' not in res['CachePolicyList']:
            nb_resources = 0
        else:
            cache_policies = res['CachePolicyList'
                                 ]['Items']
            nb_resources = len(cache_policies)

        self.limits["Cache policies per AWS account"]._add_current_usage(
            nb_resources,
            aws_type='AWS::CloudFront::CachePolicy',
        )

        if 'Items' in res['CachePolicyList']:
            for cp in res['CachePolicyList']['Items']:
                # Count whitelisted cookies
                nb_cookies = 0
                try:
                    nb_cookies = len(cp['CachePolicy']['CachePolicyConfig'][
                        'ParametersInCacheKeyAndForwardedToOrigin'][
                        'CookiesConfig']['Cookies']['Items'])
                except KeyError:
                    pass
                self.limits[
                    'Cookies per cache policy'
                ]._add_current_usage(nb_cookies,
                                     resource_id=cp['CachePolicy']['Id'])

                # Count whitelisted headers
                nb_headers = 0
                try:
                    nb_headers = len(cp['CachePolicy']['CachePolicyConfig'][
                        'ParametersInCacheKeyAndForwardedToOrigin'][
                        'HeadersConfig']['Headers']['Items'])
                except KeyError:
                    pass
                self.limits[
                    'Headers per cache policy'
                ]._add_current_usage(nb_headers,
                                     resource_id=cp['CachePolicy']['Id'])

                # Count whitelisted query strings
                nb_querystring = 0
                try:
                    nb_querystring = len(cp['CachePolicy']['CachePolicyConfig'][
                        'ParametersInCacheKeyAndForwardedToOrigin'][
                        'QueryStringsConfig']['QueryStrings']['Items'])
                except KeyError:
                    pass
                self.limits[
                    'Query strings per cache policy'
                ]._add_current_usage(nb_querystring,
                                     resource_id=cp['CachePolicy']['Id'])

    def _find_usage_origin_request_policies(self):
        """
        List CloudFront origin request policies from AWS, and update usage in
        self.limits for the following limits:

        - Origin request policies per AWS account
        - Cookies per origin request policy
        - Headers per origin request policy
        - Query strings per origin request policy
        """

        # Read usage from AWS
        res = paginate_dict(
            # count only the custom origin request policies
            self.conn.list_origin_request_policies,
            Type='custom',
            alc_marker_path=['OriginRequestPolicyList',
                             'NextMarker'],
            alc_data_path=['OriginRequestPolicyList', 'Items'],
            alc_marker_param='Marker'
        )
        if 'Items' not in res['OriginRequestPolicyList']:
            nb_resources = 0
        else:
            origin_request_policies = res['OriginRequestPolicyList'
                                          ]['Items']
            nb_resources = len(origin_request_policies)

        self.limits["Origin request policies per AWS account"
                    ]._add_current_usage(
            nb_resources,
            aws_type='AWS::CloudFront::OriginRequestPolicy',
        )

        if 'Items' in res['OriginRequestPolicyList']:
            for cp in res['OriginRequestPolicyList']['Items']:
                # Count cookies
                nb_cookies = 0
                try:
                    nb_cookies = len(
                        cp['OriginRequestPolicy']['OriginRequestPolicyConfig'][
                            'CookiesConfig']['Cookies']['Items'])
                except KeyError:
                    pass
                self.limits[
                    'Cookies per origin request policy'
                ]._add_current_usage(
                    nb_cookies,
                    resource_id=cp['OriginRequestPolicy']['Id'])

                # Count headers
                nb_headers = 0
                try:
                    nb_headers = len(
                        cp['OriginRequestPolicy']['OriginRequestPolicyConfig'][
                            'HeadersConfig']['Headers']['Items'])
                except KeyError:
                    pass
                self.limits[
                    'Headers per origin request policy'
                ]._add_current_usage(
                    nb_headers,
                    resource_id=cp['OriginRequestPolicy']['Id'])

                # Count query strings
                nb_querystring = 0
                try:
                    nb_querystring = len(
                        cp['OriginRequestPolicy']['OriginRequestPolicyConfig'][
                            'QueryStringsConfig']['QueryStrings']['Items'])
                except KeyError:
                    pass
                self.limits[
                    'Query strings per origin request policy'
                ]._add_current_usage(
                    nb_querystring,
                    resource_id=cp['OriginRequestPolicy']['Id'])

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

        limits["Distributions per AWS account"] = AwsLimit(
            "Distributions per AWS account",
            self,
            200,
            self.warning_threshold,
            self.critical_threshold,
            limit_type="AWS::CloudFront::Distribution",
            quotas_name="Web distributions per AWS account",
        )

        limits["Alternate domain names (CNAMEs) per distribution"] = AwsLimit(
            "Alternate domain names (CNAMEs) per distribution",
            self,
            100,
            self.warning_threshold,
            self.critical_threshold,
            limit_type="AWS::CloudFront::Distribution",
            quotas_name="Alternate domain names (CNAMEs) per distribution",
        )

        limits["Cache behaviors per distribution"] = AwsLimit(
            "Cache behaviors per distribution",
            self,
            25,
            self.warning_threshold,
            self.critical_threshold,
            limit_type="AWS::CloudFront::Distribution",
            quotas_name="Cache behaviors per distribution",
        )

        limits["Origins per distribution"] = AwsLimit(
            "Origins per distribution",
            self,
            25,
            self.warning_threshold,
            self.critical_threshold,
            limit_type="AWS::CloudFront::Distribution",
            quotas_name="Origins per distribution",
        )

        limits["Origin groups per distribution"] = AwsLimit(
            "Origin groups per distribution",
            self,
            10,
            self.warning_threshold,
            self.critical_threshold,
            limit_type="AWS::CloudFront::Distribution",
            quotas_name="Origin groups per distribution",
        )

        # This limit is listed by the "Service Quotas" service, but not in the
        # CloudFront documentation.
        limits["Key groups associated with a single distribution"] = AwsLimit(
            "Key groups associated with a single distribution",
            self,
            4,
            self.warning_threshold,
            self.critical_threshold,
            limit_type="AWS::CloudFront::Distribution",
            quotas_name="Key groups associated with a single distribution",
        )

        # This limit is listed in the CloudFront documentation, but not in the
        # "Service Quotas" service.
        limits["Key groups associated with a single cache behavior"] = AwsLimit(
            "Key groups associated with a single cache behavior",
            self,
            4,
            self.warning_threshold,
            self.critical_threshold,
            limit_type="AWS::CloudFront::Distribution",
        )

        limits["Key groups per AWS account"] = AwsLimit(
            "Key groups per AWS account",
            self,
            10,
            self.warning_threshold,
            self.critical_threshold,
            limit_type="AWS::CloudFront::KeyGroup",
            quotas_name="Key groups per AWS account"
        )

        limits["Origin access identities per account"] = AwsLimit(
            "Origin access identities per account",
            self,
            100,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Origin access identities per account"
        )

        limits["Cache policies per AWS account"] = AwsLimit(
            "Cache policies per AWS account",
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Cache policies per AWS account"
        )

        limits["Origin request policies per AWS account"] = AwsLimit(
            "Origin request policies per AWS account",
            self,
            20,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Origin request policies per AWS account"
        )

        limits["Whitelisted cookies per cache behavior"] = AwsLimit(
            "Whitelisted cookies per cache behavior",
            self,
            10,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Whitelisted cookies per cache behavior"
        )

        limits["Whitelisted headers per cache behavior"] = AwsLimit(
            "Whitelisted headers per cache behavior",
            self,
            10,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Whitelisted headers per cache behavior"
        )

        limits["Whitelisted query strings per cache behavior"] = AwsLimit(
            "Whitelisted query strings per cache behavior",
            self,
            10,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Whitelisted query strings per cache behavior"
        )

        limits["Cookies per cache policy"] = AwsLimit(
            "Cookies per cache policy",
            self,
            10,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Cookies per cache policy"
        )

        limits["Headers per cache policy"] = AwsLimit(
            "Headers per cache policy",
            self,
            10,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Headers per cache policy"
        )

        limits["Query strings per cache policy"] = AwsLimit(
            "Query strings per cache policy",
            self,
            10,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Query strings per cache policy"
        )

        limits["Cookies per origin request policy"] = AwsLimit(
            "Cookies per origin request policy",
            self,
            10,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Cookies per origin request policy"
        )

        limits["Headers per origin request policy"] = AwsLimit(
            "Headers per origin request policy",
            self,
            10,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Headers per origin request policy"
        )

        limits["Query strings per origin request policy"] = AwsLimit(
            "Query strings per origin request policy",
            self,
            10,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Query strings per origin request policy"
        )

        limits["Public keys in a single key group"] = AwsLimit(
            "Public keys in a single key group",
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Public keys in a single key group"
        )

        limits["Distributions associated with a single key group"] = AwsLimit(
            "Distributions associated with a single key group",
            self,
            100,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Distributions associated with a single key group"
        )

        limits["Distributions associated with the same cache policy"] = \
            AwsLimit(
            "Distributions associated with the same cache policy",
            self,
            100,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Distributions associated with the same cache policy"
        )

        limits["Distributions associated with the same origin request policy"] \
            = AwsLimit(
            "Distributions associated with the same origin request policy",
            self,
            100,
            self.warning_threshold,
            self.critical_threshold,
            quotas_name="Distributions associated with the same origin request "
                "policy"
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
            "cloudfront:ListCloudFrontOriginAccessIdentities",
            "cloudfront:ListKeyGroups",
            "cloudfront:ListDistributions",
            "cloudfront:ListCachePolicies",
            "cloudfront:ListOriginRequestPolicies"
        ]
