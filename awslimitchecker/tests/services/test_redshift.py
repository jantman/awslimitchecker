"""
awslimitchecker/tests/services/test_redshift.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2015 Jessie Nadler <nadler.jessie@gmail.com>

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
Jessie Nadler <nadler.jessie@gmail.com>
################################################################################
"""

import sys
from awslimitchecker.tests.services import result_fixtures
from awslimitchecker.services.redshift import _RedshiftService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT


pbm = 'awslimitchecker.services.redshift'  # module patch base
pb = '%s._RedshiftService' % pbm  # class patch pase


class Test_RedshiftService(object):

    def test_init(self):
        """test __init__()"""
        cls = _RedshiftService(21, 43)
        assert cls.service_name == 'Redshift'
        assert cls.api_name == 'redshift'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _RedshiftService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Redshift manual snapshots',
            'Redshift subnet groups',
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _RedshiftService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        """test find usage method calls other methods"""
        mock_conn = Mock()
        with patch('%s.connect' % pb) as mock_connect:
            with patch.multiple(
                pb,
                _find_cluster_manual_snapshots=DEFAULT,
                _find_cluster_subnet_groups=DEFAULT,
            ) as mocks:
                cls = _RedshiftService(21, 43)
                cls.conn = mock_conn
                assert cls._have_usage is False
                cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        assert mock_conn.mock_calls == []
        for x in [
            '_find_cluster_manual_snapshots',
            '_find_cluster_subnet_groups',
        ]:
            assert mocks[x].mock_calls == [call()]

    def test_find_usage_manual_snapshots(self):
        response = result_fixtures.Redshift.test_describe_cluster_snapshots
        limit_key = 'Redshift manual snapshots'

        mock_conn = Mock()
        mock_conn.describe_cluster_snapshots.return_value = response

        cls = _RedshiftService(21, 43, {'region_name': 'us-west-2'})
        cls.conn = mock_conn
        cls._find_cluster_manual_snapshots()

        assert mock_conn.mock_calls == [
            call.describe_cluster_snapshots(SnapshotType='manual')
        ]
        assert len(cls.limits[limit_key].get_current_usage()) == 1
        assert cls.limits[limit_key].get_current_usage()[
            0].get_value() == 2

    def test_find_usage_subnet_groups(self):
        response = result_fixtures.Redshift.test_describe_cluster_subnet_groups
        limit_key = 'Redshift subnet groups'

        mock_conn = Mock()
        mock_conn.describe_cluster_subnet_groups.return_value = response

        cls = _RedshiftService(21, 43, {'region_name': 'us-west-2'})
        cls.conn = mock_conn
        cls._find_cluster_subnet_groups()

        assert mock_conn.mock_calls == [call.describe_cluster_subnet_groups()]
        assert len(cls.limits[limit_key].get_current_usage()) == 1
        assert cls.limits[limit_key].get_current_usage()[
            0].get_value() == 3

    def test_required_iam_permissions(self):
        cls = _RedshiftService(21, 43)
        assert cls.required_iam_permissions() == [
            "redshift:DescribeClusterSnapshots",
            "redshift:DescribeClusterSubnetGroups",
        ]
