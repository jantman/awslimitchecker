"""
awslimitchecker/tests/services/test_cloudfront.py

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

import sys
from awslimitchecker.tests.services import result_fixtures
from awslimitchecker.services.cloudfront import _CloudfrontService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if sys.version_info[0] < 3 or sys.version_info[0] == 3 \
        and sys.version_info[1] < 4:
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT

pbm = "awslimitchecker.services.cloudfront"  # module patch base
pb = "%s._CloudfrontService" % pbm  # class patch pase


class Test_CloudfrontService(object):
    def test_init(self):
        """test __init__()"""
        cls = _CloudfrontService(21, 43, {}, None)
        assert cls.service_name == "CloudFront"
        assert cls.api_name == "cloudfront"
        assert cls.quotas_service_code == "cloudfront"
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _CloudfrontService(21, 43, {}, None)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted(
            [
                "Alternate domain names (CNAMEs) per distribution",
                "Cache behaviors per distribution",
                "Distributions per AWS account",
                "Origins per distribution",
                "Origin groups per distribution",
                "Key groups associated with a single distribution",
                "Key groups associated with a single cache behavior",
                "Key groups per AWS account",
                "Origin access identities per account",
                "Cache policies per AWS account",
                "Origin request policies per AWS account",
                "Whitelisted cookies per cache behavior",
                "Whitelisted headers per cache behavior",
                "Whitelisted query strings per cache behavior",
                "Cookies per cache policy",
                "Headers per cache policy",
                "Query strings per cache policy",
                "Cookies per origin request policy",
                "Headers per origin request policy",
                "Query strings per origin request policy",
                "Public keys in a single key group",
                "Distributions associated with a single key group",
                "Distributions associated with the same cache policy",
                "Distributions associated with the same origin request policy"
            ]
        )
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _CloudfrontService(21, 43, {}, None)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        """
        Check that find_usage() method calls other methods.
        """
        with patch.multiple(
            pb,
            connect=DEFAULT,
            _find_usage_distributions=DEFAULT,
            _find_usage_keygroups=DEFAULT,
            _find_usage_origin_access_identities=DEFAULT,
            _find_usage_cache_policies=DEFAULT,
            _find_usage_origin_request_policies=DEFAULT,
            autospec=True
        ) as mocks:
            cls = _CloudfrontService(21, 43, {}, None)
            assert cls._have_usage is False
            cls.find_usage()

        assert cls._have_usage is True
        assert len(mocks) == 6
        # other methods should have been called
        for x in [
            "_find_usage_distributions",
            "_find_usage_keygroups",
            "_find_usage_origin_access_identities",
            "_find_usage_cache_policies",
            "_find_usage_origin_request_policies"
        ]:
            assert mocks[x].mock_calls == [call(cls)]

    def test_find_usage_distributions_empty(self):
        """
        Verify the correctness of usage (when there are no distributions)
        This test mocks the AWS list_distributions response (after pagination).
        """
        # Setup the mock and call the tested function
        resp = result_fixtures.CloudFront.test_find_usage_distributions_empty
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = resp
            cls._find_usage_distributions()

        # Check that usage values are correctly set
        assert len(
            cls.limits["Distributions per AWS account"].get_current_usage()
        ) == 1
        assert (
            cls.limits["Distributions per AWS account"].get_current_usage()[0]
            .get_value() == 0
        )
        assert (
            cls.limits["Distributions per AWS account"].get_current_usage()[0]
            .resource_id is None
        )

    def test_find_usage_distributions(self):
        """
        Verify the correctness of usage (basic per-distribution limits)
        This test mocks the AWS list_distributions response (after pagination)
        """
        # Setup the mock and call the tested function
        response = result_fixtures.CloudFront.test_find_usage_distributions
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = response
            cls._find_usage_distributions()

        expected_nb_distributions = len(
            response['DistributionList']['Items'])

        # Check that usage values are correctly set
        limit = "Distributions per AWS account"
        assert len(cls.limits[limit].get_current_usage()) == 1
        assert cls.limits[limit].get_current_usage()[0].get_value() \
            == expected_nb_distributions
        assert cls.limits[limit].get_current_usage()[0].resource_id is None

        limit = "Alternate domain names (CNAMEs) per distribution"
        assert len(cls.limits[limit].get_current_usage()) \
            == expected_nb_distributions
        assert cls.limits[limit].get_current_usage()[0].resource_id \
            == "ID-DISTRIBUTION-000"
        assert cls.limits[limit].get_current_usage()[0].get_value() == 3

        limit = "Cache behaviors per distribution"
        assert len(cls.limits[limit].get_current_usage()) \
            == expected_nb_distributions
        assert cls.limits[limit].get_current_usage()[1].resource_id \
            == "ID-DISTRIBUTION-001"
        assert cls.limits[limit].get_current_usage()[1].get_value() == 5

        limit = "Origins per distribution"
        assert len(cls.limits[limit].get_current_usage()) \
            == expected_nb_distributions
        assert cls.limits[limit].get_current_usage()[2].resource_id \
            == "ID-DISTRIBUTION-002"
        assert cls.limits[limit].get_current_usage()[2].get_value() == 3

        limit = "Origin groups per distribution"
        assert len(cls.limits[limit].get_current_usage()) \
            == expected_nb_distributions
        assert cls.limits[limit].get_current_usage()[3].resource_id \
            == "ID-DISTRIBUTION-003"
        assert cls.limits[limit].get_current_usage()[3].get_value() == 1

        # Check which methods were called
        assert mock_conn.mock_calls == []
        assert mock_paginate.mock_calls == [
            call(
                mock_conn.list_distributions,
                alc_marker_path=["DistributionList", "NextMarker"],
                alc_data_path=["DistributionList", "Items"],
                alc_marker_param="Marker",
            )
        ]

    def test_find_usage_distributions_keygroups(self):
        """
        Verify the correctness of usage (keygroups within a distribution)
        This test mocks the AWS list_distributions response (after pagination).
        """
        # Setup the mock and call the tested function
        response = result_fixtures.CloudFront.\
            test_find_usage_distributions_keygroups
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = response
            cls._find_usage_distributions()

        # Check that usage values are correctly set
        limit = "Key groups associated with a single distribution"
        assert len(cls.limits[limit].get_current_usage()) == 1  # 1 distribution
        assert cls.limits[limit].get_current_usage()[0].resource_id \
            == "ID-DISTRIBUTION-001"
        assert cls.limits[limit].get_current_usage()[0].get_value() == 3

        limit = "Key groups associated with a single cache behavior"
        assert len(cls.limits[limit].get_current_usage()) == 3  # 3 cache behav.
        # convert to map to ignore how usage entries are ordered in the array
        usage_map = {u.resource_id: u
                     for u in cls.limits[limit].get_current_usage()}
        assert "ID-DISTRIBUTION-001-default-cache-behavior" in usage_map
        assert usage_map["ID-DISTRIBUTION-001-default-cache-behavior"
                         ].get_value() == 2
        assert "ID-DISTRIBUTION-001-cache-behavior-path01" in usage_map
        assert usage_map["ID-DISTRIBUTION-001-cache-behavior-path01"
                         ].get_value() == 0
        assert "ID-DISTRIBUTION-001-cache-behavior-path02" in usage_map
        assert usage_map["ID-DISTRIBUTION-001-cache-behavior-path02"
                         ].get_value() == 3

        # Check which methods were called
        assert mock_conn.mock_calls == []
        assert mock_paginate.mock_calls == [
            call(
                mock_conn.list_distributions,
                alc_marker_path=["DistributionList", "NextMarker"],
                alc_data_path=["DistributionList", "Items"],
                alc_marker_param="Marker",
            )
        ]

    def test_find_usage_distributions_per_keygroups(self):
        """
        Verify the correctness of usage (distributions associated to a keygroup)
        This test mocks the AWS list_distributions response (after pagination).
        """
        # Setup the mock and call the tested function
        response = result_fixtures.CloudFront.\
            test_find_usage_distributions_per_key_group
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = response
            cls._find_usage_distributions()

        # Check that usage values are correctly set
        limit = "Distributions associated with a single key group"
        assert len(cls.limits[limit].get_current_usage()) == 3  # 3 key groups
        # convert to map to ignore how usage entries are ordered in the array
        usage_map = {u.resource_id: u
                     for u in cls.limits[limit].get_current_usage()}
        assert "A" in usage_map
        assert usage_map["A"].get_value() == 2  # "A" referenced in 2 distrib
        assert "B" in usage_map
        assert usage_map["B"].get_value() == 1  # "B" referenced in 1 distrib
        assert "C" in usage_map
        assert usage_map["C"].get_value() == 1  # "C" referenced in 1 distrib

    def test_find_usage_distributions_per_cache_policy(self):
        """
        Verify the correctness of usage
        (distributions associated to a cache policy)
        This test mocks the AWS list_distributions response (after pagination).
        """
        # Setup the mock and call the tested function
        response = result_fixtures.CloudFront.\
            test_find_usage_distributions_per_cache_policy
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = response
            cls._find_usage_distributions()

        # Check that usage values are correctly set
        limit = "Distributions associated with the same cache policy"
        assert len(cls.limits[limit].get_current_usage()) == 4  # 4 cache pol.
        # convert to map to ignore how usage entries are ordered in the array
        usage_map = {u.resource_id: u
                     for u in cls.limits[limit].get_current_usage()}
        assert "A" in usage_map
        assert usage_map["A"].get_value() == 2  # "A" referenced in 2 distrib
        assert "B" in usage_map
        assert usage_map["B"].get_value() == 1  # "B" referenced in 1 distrib
        assert "C" in usage_map
        assert usage_map["C"].get_value() == 1  # "C" referenced in 1 distrib
        assert "D" in usage_map
        assert usage_map["D"].get_value() == 1  # "D" referenced in 1 distrib

    def test_find_usage_distributions_per_origin_req_policy(self):
        """
        Verify the correctness of usage
        (distributions associated to an origin request policy)
        This test mocks the AWS list_distributions response (after pagination).
        """
        # Setup the mock and call the tested function
        response = result_fixtures.CloudFront.\
            test_find_usage_distributions_per_origin_req_policy
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = response
            cls._find_usage_distributions()

        # Check that usage values are correctly set
        limit = "Distributions associated with the same origin request policy"
        assert len(cls.limits[limit].get_current_usage()) == 3
        # convert to map to ignore how usage entries are ordered in the array
        usage_map = {u.resource_id: u
                     for u in cls.limits[limit].get_current_usage()}
        assert "A" in usage_map
        assert usage_map["A"].get_value() == 2  # "A" referenced in 2 distrib
        assert "B" in usage_map
        assert usage_map["B"].get_value() == 1  # "B" referenced in 1 distrib
        assert "C" in usage_map
        assert usage_map["C"].get_value() == 1  # "C" referenced in 1 distrib

    def test_find_usage_per_cache_behavior(self):
        """
        Verify the correctness of cache behavior (limits per cache behavior)
        This test mocks the AWS list_distributions response (after pagination).
        """
        # Setup the mock and call the tested function
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = result_fixtures.CloudFront\
                .test_find_usage_per_cache_behavior
            cls._find_usage_distributions()

        # Check that usage values are correctly set
        limit = "Whitelisted cookies per cache behavior"
        assert len(cls.limits[limit].get_current_usage()) == 2
        # convert to map to ignore how usage entries are ordered in the array
        usage_map = {u.resource_id: u
                     for u in cls.limits[limit].get_current_usage()}
        assert "ID-DISTRIBUTION-100-default-cache-behavior" in usage_map
        assert usage_map["ID-DISTRIBUTION-100-default-cache-behavior"
                         ].get_value() == 3
        assert "ID-DISTRIBUTION-100-cache-behavior-path01" in usage_map
        assert usage_map["ID-DISTRIBUTION-100-cache-behavior-path01"
                         ].get_value() == 1

        limit = "Whitelisted headers per cache behavior"
        assert len(cls.limits[limit].get_current_usage()) == 2
        # convert to map to ignore how usage entries are ordered in the array
        usage_map = {u.resource_id: u
                     for u in cls.limits[limit].get_current_usage()}
        assert "ID-DISTRIBUTION-100-default-cache-behavior" in usage_map
        assert usage_map["ID-DISTRIBUTION-100-default-cache-behavior"
                         ].get_value() == 4
        assert "ID-DISTRIBUTION-100-cache-behavior-path01" in usage_map
        assert usage_map["ID-DISTRIBUTION-100-cache-behavior-path01"
                         ].get_value() == 2

        limit = "Whitelisted query strings per cache behavior"
        assert len(cls.limits[limit].get_current_usage()) == 2
        # convert to map to ignore how usage entries are ordered in the array
        usage_map = {u.resource_id: u
                     for u in cls.limits[limit].get_current_usage()}
        assert "ID-DISTRIBUTION-100-default-cache-behavior" in usage_map
        assert usage_map["ID-DISTRIBUTION-100-default-cache-behavior"
                         ].get_value() == 5
        assert "ID-DISTRIBUTION-100-cache-behavior-path01" in usage_map
        assert usage_map["ID-DISTRIBUTION-100-cache-behavior-path01"
                         ].get_value() == 3

    def test_find_usage_keygroups(self):
        """
        Verify the correctness of usage (key groups)
        This test mocks the AWS list_key_groups response (after pagination).
        """
        # Setup the mock and call the tested function
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = \
                result_fixtures.CloudFront.test_find_usage_keygroups
            cls._find_usage_keygroups()

        # Check that usage values are correctly set
        limit = "Key groups per AWS account"
        assert len(cls.limits[limit].get_current_usage()) == 1
        assert cls.limits[limit].get_current_usage()[0].get_value() == 2
        assert cls.limits[limit].get_current_usage()[0].resource_id is None

        limit = "Public keys in a single key group"
        assert len(cls.limits[limit].get_current_usage()) == 2
        assert cls.limits[limit].get_current_usage()[0].get_value() == 4
        assert cls.limits[limit].get_current_usage()[0].resource_id == "kg01"

        # Check which methods were called
        assert mock_conn.mock_calls == []
        assert mock_paginate.mock_calls == [
            call(
                mock_conn.list_key_groups,
                alc_marker_path=["KeyGroupList", "NextMarker"],
                alc_data_path=["KeyGroupList", "Items"],
                alc_marker_param="Marker",
            )
        ]

    def test_find_usage_keygroups_empty(self):
        """
        Verify the correctness of usage
        (when there are no key groups)
        This test mocks the AWS list_key_groups response (after pagination).
        """
        # Setup the mock and call the tested function
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = \
                result_fixtures.CloudFront.test_find_usage_keygroups_empty
            cls._find_usage_keygroups()

        # Check that usage values are correctly set
        limit = "Key groups per AWS account"
        assert len(cls.limits[limit].get_current_usage()) == 1
        assert cls.limits[limit].get_current_usage()[0].get_value() == 0
        assert cls.limits[limit].get_current_usage()[0].resource_id is None

        limit = "Public keys in a single key group"
        assert len(cls.limits[limit].get_current_usage()) == 0

    def test_find_usage_origin_access_identities(self):
        """
        Verify the correctness of usage (origin access identities)
        This test mocks the AWS list_cloud_front_origin_access_identities
        response (after pagination).
        """
        # Setup the mock and call the tested function
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = result_fixtures.CloudFront\
                .test_find_usage_origin_access_identities
            cls._find_usage_origin_access_identities()

        # Check that usage values are correctly set
        limit = "Origin access identities per account"
        assert len(cls.limits[limit].get_current_usage()) == 1
        assert cls.limits[limit].get_current_usage()[0].get_value() == 3
        assert cls.limits[limit].get_current_usage()[0].resource_id is None

        # Check which methods were called
        assert mock_conn.mock_calls == []
        assert mock_paginate.mock_calls == [
            call(
                mock_conn.list_cloud_front_origin_access_identities,
                alc_marker_path=["CloudFrontOriginAccessIdentityList",
                                 "NextMarker"],
                alc_data_path=["CloudFrontOriginAccessIdentityList", "Items"],
                alc_marker_param="Marker",
            )
        ]

    def test_find_usage_origin_access_identities_empty(self):
        """
        Verify the correctness of usage
        (when there are no origin access identities)
        This test mocks the AWS list_cloud_front_origin_access_identities
        response (after pagination).
        """
        # Setup the mock and call the tested function
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = result_fixtures.CloudFront\
                .test_find_usage_origin_access_identities_empty
            cls._find_usage_origin_access_identities()

        # Check that usage values are correctly set
        limit = "Origin access identities per account"
        assert len(cls.limits[limit].get_current_usage()) == 1
        assert cls.limits[limit].get_current_usage()[0].get_value() == 0
        assert cls.limits[limit].get_current_usage()[0].resource_id is None

    def test_find_usage_cache_policies(self):
        """
        Verify the correctness of usage (cache policies)
        This test mocks the AWS list_cache_policies response (after pagination).
        """
        # Setup the mock and call the tested function
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = result_fixtures.CloudFront\
                .test_find_usage_cache_policies
            cls._find_usage_cache_policies()

        # Check that usage values are correctly set
        limit = "Cache policies per AWS account"
        assert len(cls.limits[limit].get_current_usage()) == 1
        assert cls.limits[limit].get_current_usage()[0].get_value() == 4
        assert cls.limits[limit].get_current_usage()[0].resource_id is None

        # Check which methods were called
        assert mock_conn.mock_calls == []
        assert mock_paginate.mock_calls == [
            call(
                mock_conn.list_cache_policies,
                Type='custom',
                alc_marker_path=["CachePolicyList", "NextMarker"],
                alc_data_path=["CachePolicyList", "Items"],
                alc_marker_param="Marker",
            )
        ]

    def test_find_usage_cache_policies_empty(self):
        """
        Verify the correctness of usage
        (when there are no cache policies)
        This test mocks the AWS list_cache_policies response (after pagination).
        """
        # Setup the mock and call the tested function
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = result_fixtures.CloudFront\
                .test_find_usage_cache_policies_empty
            cls._find_usage_cache_policies()

        # Check that usage values are correctly set
        limit = "Cache policies per AWS account"
        assert len(cls.limits[limit].get_current_usage()) == 1
        assert cls.limits[limit].get_current_usage()[0].get_value() == 0
        assert cls.limits[limit].get_current_usage()[0].resource_id is None

    def test_find_usage_cache_policies_config(self):
        """
        Verify the correctness of usage (per-cache-policy limits)
        This test mocks the AWS list_cache_policies response (after pagination).
        """
        # Setup the mock and call the tested function
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = result_fixtures.CloudFront\
                .test_find_usage_cache_policies_config
            cls._find_usage_cache_policies()

        # Check that usage values are correctly set
        limit = "Cookies per cache policy"
        assert len(cls.limits[limit].get_current_usage()) == 1
        assert cls.limits[limit].get_current_usage()[0].get_value() == 2
        assert cls.limits[limit].get_current_usage()[0].resource_id == "CP01"

        limit = "Headers per cache policy"
        assert len(cls.limits[limit].get_current_usage()) == 1
        assert cls.limits[limit].get_current_usage()[0].get_value() == 3
        assert cls.limits[limit].get_current_usage()[0].resource_id == "CP01"

        limit = "Query strings per cache policy"
        assert len(cls.limits[limit].get_current_usage()) == 1
        assert cls.limits[limit].get_current_usage()[0].get_value() == 1
        assert cls.limits[limit].get_current_usage()[0].resource_id == "CP01"

    def test_find_usage_origin_request_policies(self):
        """
        Verify the correctness of usage (origin request policies)
        This test mocks the AWS list_origin_request_policies response (after
        pagination).
        """
        # Setup the mock and call the tested function
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = result_fixtures.CloudFront\
                .test_find_usage_origin_request_policies
            cls._find_usage_origin_request_policies()

        # Check that usage values are correctly set
        limit = "Origin request policies per AWS account"
        assert len(cls.limits[limit].get_current_usage()) == 1
        assert cls.limits[limit].get_current_usage()[0].get_value() == 2
        assert cls.limits[limit].get_current_usage()[0].resource_id is None

        # Check which methods were called
        assert mock_conn.mock_calls == []
        assert mock_paginate.mock_calls == [
            call(
                mock_conn.list_origin_request_policies,
                Type='custom',
                alc_marker_path=["OriginRequestPolicyList", "NextMarker"],
                alc_data_path=["OriginRequestPolicyList", "Items"],
                alc_marker_param="Marker",
            )
        ]

    def test_find_usage_origin_request_policies_empty(self):
        """
        Verify the correctness of usage
        This test mocks the AWS list_origin_request_policies response (after
        pagination).
        """
        # Setup the mock and call the tested function
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = result_fixtures.CloudFront\
                .test_find_usage_origin_request_policies_empty
            cls._find_usage_origin_request_policies()

        # Check that usage values are correctly set
        limit = "Origin request policies per AWS account"
        assert len(cls.limits[limit].get_current_usage()) == 1
        assert cls.limits[limit].get_current_usage()[0].get_value() == 0
        assert cls.limits[limit].get_current_usage()[0].resource_id is None

    def test_find_usage_origin_request_policies_config(self):
        """
        Verify the correctness of usage (per-origin-request-policy limits)
        This test mocks the AWS list_origin_request_policies response (after
        pagination).
        """
        # Setup the mock and call the tested function
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CloudfrontService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = result_fixtures.CloudFront\
                .test_find_usage_origin_request_policies_config
            cls._find_usage_origin_request_policies()

        # Check that usage values are correctly set
        limit = "Cookies per origin request policy"
        assert len(cls.limits[limit].get_current_usage()) == 1
        assert cls.limits[limit].get_current_usage()[0].get_value() == 2
        assert cls.limits[limit].get_current_usage()[0].resource_id == "ORP01"

        limit = "Headers per origin request policy"
        assert len(cls.limits[limit].get_current_usage()) == 1
        assert cls.limits[limit].get_current_usage()[0].get_value() == 3
        assert cls.limits[limit].get_current_usage()[0].resource_id == "ORP01"

        limit = "Query strings per origin request policy"
        assert len(cls.limits[limit].get_current_usage()) == 1
        assert cls.limits[limit].get_current_usage()[0].get_value() == 1
        assert cls.limits[limit].get_current_usage()[0].resource_id == "ORP01"

    def test_required_iam_permissions(self):
        cls = _CloudfrontService(21, 43, {}, None)
        assert cls.required_iam_permissions() == [
            "cloudfront:ListCloudFrontOriginAccessIdentities",
            "cloudfront:ListKeyGroups",
            "cloudfront:ListDistributions",
            "cloudfront:ListCachePolicies",
            "cloudfront:ListOriginRequestPolicies"
        ]
