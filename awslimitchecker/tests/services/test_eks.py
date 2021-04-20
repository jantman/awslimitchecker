"""
awslimitchecker/tests/services/test_eks.py

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
from awslimitchecker.services.eks import _EksService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT, ANY
else:
    from unittest.mock import patch, call, Mock, DEFAULT, ANY


pbm = 'awslimitchecker.services.eks'  # module patch base
pb = '%s._EksService' % pbm  # class patch pase


class Test_EksService(object):

    def test_init(self):
        """test __init__()"""
        cls = _EksService(21, 43, {}, None)
        assert cls.service_name == 'EKS'
        assert cls.api_name == 'eks'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _EksService(21, 43, {}, None)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Clusters',
            'Control plane security groups per cluster',
            'Managed node groups per cluster',
            'Nodes per managed node group',
            'Public endpoint access CIDR ranges per cluster',
            'Fargate profiles per cluster',
            'Selectors per Fargate profile',
            'Label pairs per Fargate profile selector',
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _EksService(21, 43, {}, None)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        """test find usage method calls other methods"""
        mock_conn = Mock()
        with patch('%s.connect' % pb) as mock_connect:
            with patch.multiple(
                pb,
                _find_clusters_usage=DEFAULT,
            ) as mocks:
                cls = _EksService(21, 43, {}, None)
                cls.conn = mock_conn
                assert cls._have_usage is False
                cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        assert mock_conn.mock_calls == []
        for x in [
            '_find_clusters_usage',
        ]:
            assert mocks[x].mock_calls == [call()]

    def test_find_clusters_usage(self):
        list_clusters = result_fixtures.EKS.test_find_clusters_usage_list
        describe_cluster = result_fixtures.EKS.test_find_clusters_usage_describe
        list_nodegroups = result_fixtures.EKS.test_find_clusters_usage_nodegrps
        list_fargates = result_fixtures.EKS.test_find_clusters_usage_fargates
        dsc_fargate = result_fixtures.EKS.test_find_clusters_usage_fargate_prof

        clusters_limit_key = 'Clusters'
        security_group_limit_key = 'Control plane security groups per cluster'
        nodegroup_limit_key = 'Managed node groups per cluster'
        public_cidr_limit_key = 'Public endpoint access CIDR ranges per cluster'
        fargate_profiles_limit_key = 'Fargate profiles per cluster'
        selectors_limit_key = 'Selectors per Fargate profile'
        label_pairs_limit_key = 'Label pairs per Fargate profile selector'

        mock_conn = Mock()
        mock_conn.list_clusters.return_value = list_clusters
        mock_conn.describe_cluster.side_effect = describe_cluster
        mock_conn.list_nodegroups.side_effect = list_nodegroups
        mock_conn.list_fargate_profiles.side_effect = list_fargates
        mock_conn.describe_fargate_profile.side_effect = dsc_fargate

        cls = _EksService(21, 43, {'region_name': 'us-west-2'}, None)
        cls.conn = mock_conn
        cls._find_clusters_usage()

        assert mock_conn.mock_calls == [
            call.list_clusters(),
            call.describe_cluster(name=ANY),
            call.list_nodegroups(clusterName=ANY),
            call.list_fargate_profiles(clusterName=ANY),
            call.describe_fargate_profile(
                clusterName=ANY,
                fargateProfileName=ANY
            ),
            call.describe_cluster(name=ANY),
            call.list_nodegroups(clusterName=ANY),
            call.list_fargate_profiles(clusterName=ANY),
            call.describe_fargate_profile(
                clusterName=ANY,
                fargateProfileName=ANY
            ),
            call.describe_fargate_profile(
                clusterName=ANY,
                fargateProfileName=ANY
            ),
            call.describe_fargate_profile(
                clusterName=ANY,
                fargateProfileName=ANY
            ),
        ]
        assert len(cls.limits[clusters_limit_key].get_current_usage()) == 1
        assert cls.limits[clusters_limit_key].get_current_usage()[
            0].get_value() == 2

        assert len(cls.limits[
            security_group_limit_key].get_current_usage()) == 2
        assert cls.limits[security_group_limit_key].get_current_usage()[
            0].get_value() == 1
        assert cls.limits[security_group_limit_key].get_current_usage()[
            1].get_value() == 2

        assert len(cls.limits[
            nodegroup_limit_key].get_current_usage()) == 2
        assert cls.limits[nodegroup_limit_key].get_current_usage()[
            0].get_value() == 2
        assert cls.limits[nodegroup_limit_key].get_current_usage()[
            1].get_value() == 1

        assert len(cls.limits[
            public_cidr_limit_key].get_current_usage()) == 2
        assert cls.limits[public_cidr_limit_key].get_current_usage()[
            0].get_value() == 3
        assert cls.limits[public_cidr_limit_key].get_current_usage()[
            1].get_value() == 1

        assert len(cls.limits[
            fargate_profiles_limit_key].get_current_usage()) == 2
        assert cls.limits[fargate_profiles_limit_key].get_current_usage()[
            0].get_value() == 1
        assert cls.limits[fargate_profiles_limit_key].get_current_usage()[
            1].get_value() == 3

        assert len(cls.limits[
            selectors_limit_key].get_current_usage()) == 4
        assert cls.limits[selectors_limit_key].get_current_usage()[
            0].get_value() == 1
        assert cls.limits[selectors_limit_key].get_current_usage()[
            1].get_value() == 2
        assert cls.limits[selectors_limit_key].get_current_usage()[
            2].get_value() == 3

        assert len(cls.limits[
            label_pairs_limit_key].get_current_usage()) == 6
        assert cls.limits[label_pairs_limit_key].get_current_usage()[
            0].get_value() == 1
        assert cls.limits[label_pairs_limit_key].get_current_usage()[
            1].get_value() == 1
        assert cls.limits[label_pairs_limit_key].get_current_usage()[
            2].get_value() == 2
        assert cls.limits[label_pairs_limit_key].get_current_usage()[
            3].get_value() == 1
        assert cls.limits[label_pairs_limit_key].get_current_usage()[
            4].get_value() == 2
        assert cls.limits[label_pairs_limit_key].get_current_usage()[
            5].get_value() == 3

    def test_required_iam_permissions(self):
        cls = _EksService(21, 43, {}, None)
        assert cls.required_iam_permissions() == [
            "eks:ListClusters",
            "eks:DescribeCluster",
            "eks:ListNodegroups",
            "eks:ListFargateProfiles",
            "eks:DescribeFargateProfile"
        ]
