"""
awslimitchecker/tests/services/test_autoscaling.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2015-2017 Jason Antman <jason@jasonantman.com>

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

import sys
from awslimitchecker.services.autoscaling import _AutoscalingService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock


class Test_AutoscalingService(object):

    # path base paths
    pb = 'awslimitchecker.services.autoscaling._AutoscalingService'
    pbm = 'awslimitchecker.services.autoscaling'

    def test_init(self):
        """test __init__()"""
        cls = _AutoscalingService(21, 43)
        assert cls.service_name == 'AutoScaling'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _AutoscalingService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Auto Scaling groups',
            'Launch configurations',
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _AutoscalingService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        mock_conn = Mock()

        def se_wrapper(func, *args, **kwargs):
            if func == mock_conn.describe_auto_scaling_groups:
                return {
                    'AutoScalingGroups': [
                        {'AutoScalingGroupName': 'foo'},
                        {'AutoScalingGroupName': 'bar'},
                        {'AutoScalingGroupName': 'baz'},
                    ],
                }
            elif func == mock_conn.describe_launch_configurations:
                return {
                    'LaunchConfigurations': [
                        {'LaunchConfigurationName': 'foo'},
                        {'LaunchConfigurationName': 'bar'},
                    ],
                }
            return None

        with patch('%s.connect' % self.pb) as mock_connect:
            with patch('%s.paginate_dict' % self.pbm) as mock_paginate:
                cls = _AutoscalingService(21, 43)
                cls.conn = mock_conn
                mock_paginate.side_effect = se_wrapper
                assert cls._have_usage is False
                cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert mock_conn.mock_calls == []
        assert mock_paginate.mock_calls == [
            call(
                mock_conn.describe_auto_scaling_groups,
                alc_marker_path=['NextToken'],
                alc_data_path=['AutoScalingGroups'],
                alc_marker_param='NextToken'
            ),
            call(
                mock_conn.describe_launch_configurations,
                alc_marker_path=['NextToken'],
                alc_data_path=['LaunchConfigurations'],
                alc_marker_param='NextToken'
            )
        ]
        assert cls._have_usage is True
        asgs = sorted(cls.limits['Auto Scaling groups'].get_current_usage())
        assert len(asgs) == 1
        assert asgs[0].get_value() == 3
        lcs = sorted(cls.limits['Launch configurations'].get_current_usage())
        assert len(lcs) == 1
        assert lcs[0].get_value() == 2

    def test_required_iam_permissions(self):
        cls = _AutoscalingService(21, 43)
        assert cls.required_iam_permissions() == [
            'autoscaling:DescribeAccountLimits',
            'autoscaling:DescribeAutoScalingGroups',
            'autoscaling:DescribeLaunchConfigurations',
        ]

    def test_update_limits_from_api(self):
        mock_conn = Mock()
        aslimits = {
            'MaxNumberOfAutoScalingGroups': 11,
            'MaxNumberOfLaunchConfigurations': 22,
            'NumberOfAutoScalingGroups': 5,
            'NumberOfLaunchConfigurations': 6
        }

        mock_conn.describe_account_limits.return_value = aslimits
        with patch('%s.connect' % self.pb) as mock_connect:
            cls = _AutoscalingService(21, 43)
            cls.conn = mock_conn
            cls._update_limits_from_api()
        assert mock_connect.mock_calls == [call()]
        assert mock_conn.mock_calls == [
            call.describe_account_limits()
        ]
        assert cls.limits['Auto Scaling groups'].api_limit == 11
        assert cls.limits['Launch configurations'].api_limit == 22
