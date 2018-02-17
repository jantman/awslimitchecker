"""
awslimitchecker/tests/services/test_elb.py

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
from awslimitchecker.services.elb import _ElbService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, PropertyMock
else:
    from unittest.mock import patch, call, Mock, PropertyMock


pbm = 'awslimitchecker.services.elb'  # patch base path - module
pb = '%s._ElbService' % pbm  # patch base path


class Test_ElbService(object):

    def test_init(self):
        """test __init__()"""
        cls = _ElbService(21, 43)
        assert cls.service_name == 'ELB'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _ElbService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Active load balancers',
            'Listeners per application load balancer',
            'Listeners per load balancer',
            'Rules per application load balancer',
            'Target groups'
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _ElbService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_update_limits_from_api(self):
        r1 = result_fixtures.ELB.test_update_limits_elb
        r2 = result_fixtures.ELB.test_update_limits_alb

        mock_conn = Mock()
        mock_conn.describe_account_limits.return_value = r1

        with patch('%s.connect' % pb) as mock_connect:
            with patch('%s.client' % pbm) as mock_client:
                m_cli = mock_client.return_value
                m_cli._client_config.region_name = PropertyMock(
                    return_value='rname'
                )
                m_cli.describe_account_limits.return_value = r2
                cls = _ElbService(21, 43)
                cls.conn = mock_conn
                cls._boto3_connection_kwargs = {'foo': 'bar', 'baz': 'blam'}
                cls.get_limits()
                cls._update_limits_from_api()
        assert mock_connect.mock_calls == [call()]
        assert mock_conn.mock_calls == [call.describe_account_limits()]
        assert mock_client.mock_calls == [
            call('elbv2', foo='bar', baz='blam'),
            call().describe_account_limits()
        ]
        assert cls.limits['Active load balancers'].api_limit == 3
        assert cls.limits['Listeners per load balancer'].api_limit == 5
        assert cls.limits['Target groups'].api_limit == 7
        assert cls.limits[
            'Listeners per application load balancer'].api_limit == 9
        assert cls.limits['Rules per application load balancer'].api_limit == 10

    def test_find_usage(self):
        with patch('%s._find_usage_elbv1' % pb, autospec=True) as mock_v1:
            with patch('%s._find_usage_elbv2' % pb, autospec=True) as mock_v2:
                mock_v1.return_value = 3
                mock_v2.return_value = 5
                cls = _ElbService(21, 43)
                assert cls._have_usage is False
                cls.find_usage()
        assert cls._have_usage is True
        assert mock_v1.mock_calls == [call(cls)]
        assert mock_v2.mock_calls == [call(cls)]
        assert len(cls.limits['Active load balancers'].get_current_usage()) == 1
        assert cls.limits['Active load balancers'
                          ''].get_current_usage()[0].get_value() == 8

    def test_find_usage_elbv1(self):
        mock_conn = Mock()

        return_value = result_fixtures.ELB.test_find_usage

        with patch('%s.connect' % pb) as mock_connect:
            with patch('%s.paginate_dict' % pbm) as mock_paginate:
                mock_paginate.return_value = return_value
                cls = _ElbService(21, 43)
                cls.conn = mock_conn
                res = cls._find_usage_elbv1()
        assert res == 4
        assert mock_connect.mock_calls == [call()]
        assert mock_conn.mock_calls == []
        assert mock_paginate.mock_calls == [
            call(
                mock_conn.describe_load_balancers,
                alc_marker_path=['NextMarker'],
                alc_data_path=['LoadBalancerDescriptions'],
                alc_marker_param='Marker'
            )
        ]
        entries = sorted(cls.limits['Listeners per load balancer'
                                    ''].get_current_usage())
        assert len(entries) == 4
        assert entries[0].resource_id == 'elb-1'
        assert entries[0].get_value() == 1
        assert entries[1].resource_id == 'elb-2'
        assert entries[1].get_value() == 2
        assert entries[2].resource_id == 'elb-3'
        assert entries[2].get_value() == 3
        assert entries[3].resource_id == 'elb-4'
        assert entries[3].get_value() == 6

    def test_find_usage_elbv2(self):
        lbs_res = result_fixtures.ELB.test_find_usage_elbv2_elbs
        tgs_res = result_fixtures.ELB.test_find_usage_elbv2_target_groups

        with patch('%s.connect' % pb) as mock_connect:
            with patch('%s.client' % pbm) as mock_client:
                mock_client.return_value._client_config.region_name = \
                    PropertyMock(return_value='rname')
                with patch('%s.paginate_dict' % pbm) as mock_paginate:
                    with patch(
                        '%s._update_usage_for_elbv2' % pb, autospec=True
                    ) as mock_u:
                        with patch(
                            '%s.Config' % pbm, autospec=True
                        ) as mock_conf:
                            mock_paginate.side_effect = [
                                tgs_res,
                                lbs_res
                            ]
                            cls = _ElbService(21, 43)
                            cls._boto3_connection_kwargs = {
                                'foo': 'bar',
                                'baz': 'blam'
                            }
                            res = cls._find_usage_elbv2()
        assert res == 2
        assert mock_conf.mock_calls == [
            call(retries={'max_attempts': 12})
        ]
        assert mock_connect.mock_calls == []
        assert mock_client.mock_calls == [
            call('elbv2', foo='bar', baz='blam', config=mock_conf.return_value),
        ]
        assert mock_paginate.mock_calls == [
            call(
                mock_client.return_value.describe_target_groups,
                alc_marker_path=['NextMarker'],
                alc_data_path=['TargetGroups'],
                alc_marker_param='Marker'
            ),
            call(
                mock_client.return_value.describe_load_balancers,
                alc_marker_path=['NextMarker'],
                alc_data_path=['LoadBalancers'],
                alc_marker_param='Marker'
            )
        ]
        assert mock_u.mock_calls == [
            call(cls, mock_client.return_value, 'lb-arn1', 'lb1'),
            call(cls, mock_client.return_value, 'lb-arn2', 'lb2')
        ]
        lim = cls.limits['Target groups'].get_current_usage()
        assert len(lim) == 1
        assert lim[0].get_value() == 3
        assert lim[0].aws_type == 'AWS::ElasticLoadBalancingV2::TargetGroup'

    def test_update_usage_for_elbv2(self):
        conn = Mock()
        with patch('%s.paginate_dict' % pbm) as mock_paginate:
            mock_paginate.side_effect = [
                result_fixtures.ELB.test_usage_elbv2_listeners,
                result_fixtures.ELB.test_usage_elbv2_rules[0],
                result_fixtures.ELB.test_usage_elbv2_rules[1],
                result_fixtures.ELB.test_usage_elbv2_rules[2]
            ]
            cls = _ElbService(21, 43)
            cls._update_usage_for_elbv2(conn, 'myarn', 'albname')
        assert mock_paginate.mock_calls == [
            call(
                conn.describe_listeners,
                LoadBalancerArn='myarn',
                alc_marker_path=['NextMarker'],
                alc_data_path=['Listeners'],
                alc_marker_param='Marker'
            ),
            call(
                conn.describe_rules,
                ListenerArn='listener1',
                alc_marker_path=['NextMarker'],
                alc_data_path=['Rules'],
                alc_marker_param='Marker'
            ),
            call(
                conn.describe_rules,
                ListenerArn='listener2',
                alc_marker_path=['NextMarker'],
                alc_data_path=['Rules'],
                alc_marker_param='Marker'
            ),
            call(
                conn.describe_rules,
                ListenerArn='listener3',
                alc_marker_path=['NextMarker'],
                alc_data_path=['Rules'],
                alc_marker_param='Marker'
            )
        ]
        l = cls.limits[
            'Listeners per application load balancer'].get_current_usage()
        assert len(l) == 1
        assert l[0].get_value() == 3
        assert l[0].aws_type == 'AWS::ElasticLoadBalancingV2::LoadBalancer'
        assert l[0].resource_id == 'albname'
        r = cls.limits[
            'Rules per application load balancer'].get_current_usage()
        assert len(r) == 1
        assert r[0].get_value() == 7
        assert r[0].aws_type == 'AWS::ElasticLoadBalancingV2::LoadBalancer'
        assert r[0].resource_id == 'albname'

    def test_required_iam_permissions(self):
        cls = _ElbService(21, 43)
        assert cls.required_iam_permissions() == [
            "elasticloadbalancing:DescribeLoadBalancers",
            "elasticloadbalancing:DescribeAccountLimits",
            "elasticloadbalancing:DescribeListeners",
            "elasticloadbalancing:DescribeTargetGroups",
            "elasticloadbalancing:DescribeRules"
        ]
