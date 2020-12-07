"""
awslimitchecker/tests/services/test_kinesis.py

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
from awslimitchecker.limit import AwsLimit
from awslimitchecker.services.kinesis import _KinesisService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT


pbm = 'awslimitchecker.services.kinesis'  # module patch base
pb = '%s._KinesisService' % pbm  # class patch pase


class Test_KinesisService(object):

    def test_init(self):
        """test __init__()"""
        with patch('%s.get_limits' % pb):
            cls = _KinesisService(21, 43, {}, None)
        assert cls.service_name == 'Kinesis'
        assert cls.api_name == 'kinesis'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        mock_conn = Mock()
        m_client = Mock()
        type(m_client).region_name = 'ap-southeast-2'
        type(mock_conn)._client_config = m_client

        def se_conn(cls):
            cls.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as mock_connect:
            mock_connect.side_effect = se_conn
            cls = _KinesisService(21, 43, {}, None)

        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Shards per Region',
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

        limits = cls.limits
        assert len(limits) == 1
        assert limits['Shards per Region'].default_limit == 200

    def test_get_limits_us_east_1(self):
        mock_conn = Mock()
        m_client = Mock()
        type(m_client).region_name = 'us-east-1'
        type(mock_conn)._client_config = m_client

        def se_conn(cls):
            cls.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as mock_connect:
            mock_connect.side_effect = se_conn
            cls = _KinesisService(21, 43, {}, None)

        limits = cls.limits
        for x in limits:
            assert isinstance(limits[x], AwsLimit)
            assert x == limits[x].name
            assert limits[x].service == cls

        assert len(limits) == 1
        assert limits['Shards per Region'].default_limit == 500

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _KinesisService(21, 43, {}, None)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        mock_conn = Mock()

        def se_conn(cls):
            cls.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as mock_connect:
            mock_connect.side_effect = se_conn
            with patch.multiple(
                pb,
                _find_shards=DEFAULT,
            ) as mocks:
                cls = _KinesisService(21, 43, {}, None)
                cls.conn = mock_conn
                assert cls._have_usage is False
                cls.find_usage()
        assert mock_connect.mock_calls == [call(cls), call(cls)]
        assert cls._have_usage is True
        assert mock_conn.mock_calls == []
        for x in [
            '_find_shards',
        ]:
            assert mocks[x].mock_calls == [call()]

    def test_find_shards(self):
        response = result_fixtures.Kinesis.mock_describe_limits
        limit_key = 'Shards per Region'

        mock_conn = Mock()
        mock_conn.describe_limits.return_value = response

        cls = _KinesisService(21, 43, {'region_name': 'us-west-2'}, None)
        cls.conn = mock_conn
        cls._find_shards()

        assert mock_conn.mock_calls == [
            call.describe_limits()
        ]
        assert len(cls.limits[limit_key].get_current_usage()) == 1
        assert cls.limits[limit_key].get_current_usage()[
            0].get_value() == 555

    def test_update_limits_from_api(self):
        response = result_fixtures.Kinesis.mock_describe_limits
        mock_conn = Mock()
        mock_conn.describe_limits.return_value = response

        def se_conn(cls):
            cls.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as mock_connect:
            mock_connect.side_effect = se_conn
            cls = _KinesisService(21, 43, {'region_name': 'us-west-2'}, None)
            assert len(cls.limits) == 1
            cls.conn = mock_conn
            cls._update_limits_from_api()

        assert mock_connect.mock_calls == [call(cls), call(cls)]
        assert mock_conn.mock_calls == [call.describe_limits()]
        assert len(cls.limits) == 1
        lim = cls.limits['Shards per Region'].get_limit()
        assert lim == 700

    def test_required_iam_permissions(self):
        cls = _KinesisService(21, 43, {}, None)
        assert cls.required_iam_permissions() == [
            'kinesis:DescribeLimits',
        ]
