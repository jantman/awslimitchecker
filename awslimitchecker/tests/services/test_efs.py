"""
awslimitchecker/tests/services/test_efs.py

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
from awslimitchecker.services.efs import _EfsService
from awslimitchecker.limit import AwsLimit
from botocore.exceptions import EndpointConnectionError, ClientError
from botocore.vendored.requests.exceptions import ConnectTimeout

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock


pbm = 'awslimitchecker.services.efs'  # module patch base
pb = '%s._EfsService' % pbm  # class patch pase


class Test_EfsService(object):

    def test_init(self):
        """test __init__()"""
        cls = _EfsService(21, 43)
        assert cls.service_name == 'EFS'
        assert cls.api_name == 'efs'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _EfsService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'File systems',
        ])
        assert res['File systems'].service == cls
        assert res['File systems'].def_warning_threshold == 21
        assert res['File systems'].def_critical_threshold == 43
        assert res['File systems'].default_limit == 125

    def test_update_limits_from_api(self):
        mock_conn = Mock()
        mock_conf = Mock()
        type(mock_conf).region_name = 'us-west-2'
        mock_conn._client_config = mock_conf
        with patch('%s.connect' % pb, create=True) as mock_connect:
            cls = _EfsService(21, 43)
            cls.conn = mock_conn
            cls.limits = {
                'File systems': AwsLimit(
                    'File systems',
                    cls,
                    125,
                    cls.warning_threshold,
                    cls.critical_threshold,
                    limit_type='AWS::EFS::FileSystem',
                )
            }
            cls._update_limits_from_api()
        assert mock_connect.mock_calls == [call()]
        assert mock_conn.mock_calls == []
        assert cls.limits['File systems'].default_limit == 125

    def test_update_limits_from_api_us_east_1(self):
        mock_conn = Mock()
        mock_conf = Mock()
        type(mock_conf).region_name = 'us-east-1'
        mock_conn._client_config = mock_conf
        with patch('%s.connect' % pb, create=True) as mock_connect:
            cls = _EfsService(21, 43)
            cls.conn = mock_conn
            cls.limits = {
                'File systems': AwsLimit(
                    'File systems',
                    cls,
                    125,
                    cls.warning_threshold,
                    cls.critical_threshold,
                    limit_type='AWS::EFS::FileSystem',
                )
            }
            cls._update_limits_from_api()
        assert mock_connect.mock_calls == [call()]
        assert mock_conn.mock_calls == []
        assert cls.limits['File systems'].default_limit == 70

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock(spec_set=AwsLimit)
        cls = _EfsService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        mock_conn = Mock()
        with patch('%s.connect' % pb) as mock_connect:
            with patch('%s.paginate_dict' % pbm) as mock_paginate:
                mock_paginate.return_value = {
                    'FileSystems': [
                        {'FileSystemId': 'foo'},
                        {'FileSystemId': 'bar'},
                        {'FileSystemId': 'baz'}
                    ]
                }
                cls = _EfsService(21, 43)
                cls.conn = mock_conn
                assert cls._have_usage is False
                cls.find_usage()
        assert cls._have_usage is True
        assert mock_connect.mock_calls == [call()]
        assert mock_paginate.mock_calls == [
            call(
                mock_conn.describe_file_systems,
                alc_marker_path=['NextMarker'],
                alc_data_path=['FileSystems'],
                alc_marker_param='Marker'
            )
        ]
        assert len(cls.limits) == 1
        usage = cls.limits['File systems'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 3
        assert usage[0].aws_type == 'AWS::EFS::FileSystem'

    def test_find_usage_no_endpoint(self):
        exc = EndpointConnectionError(
            endpoint_url='https://efs.bad-region.amazonaws.com/'
        )
        mock_conn = Mock()
        with patch('%s.connect' % pb) as mock_connect:
            with patch('%s.paginate_dict' % pbm) as mock_paginate:
                mock_paginate.side_effect = exc
                cls = _EfsService(21, 43)
                cls.conn = mock_conn
                assert cls._have_usage is False
                cls.find_usage()
        assert cls._have_usage is True
        assert mock_connect.mock_calls == [call()]
        assert mock_paginate.mock_calls == [
            call(
                mock_conn.describe_file_systems,
                alc_marker_path=['NextMarker'],
                alc_data_path=['FileSystems'],
                alc_marker_param='Marker'
            )
        ]
        assert len(cls.limits) == 1
        usage = cls.limits['File systems'].get_current_usage()
        assert len(usage) == 0

    def test_find_usage_access_denied(self):
        exc = ClientError(
            {
                'Error': {
                    'Code': 'AccessDeniedException',
                    'Message': 'This account does not have permission '
                               'to access this service',
                }
            },
            'DescribeFileSystems'
        )
        mock_conn = Mock()
        with patch('%s.connect' % pb) as mock_connect:
            with patch('%s.paginate_dict' % pbm) as mock_paginate:
                mock_paginate.side_effect = exc
                cls = _EfsService(21, 43)
                cls.conn = mock_conn
                assert cls._have_usage is False
                cls.find_usage()
        assert cls._have_usage is True
        assert mock_connect.mock_calls == [call()]
        assert mock_paginate.mock_calls == [
            call(
                mock_conn.describe_file_systems,
                alc_marker_path=['NextMarker'],
                alc_data_path=['FileSystems'],
                alc_marker_param='Marker'
            )
        ]
        assert len(cls.limits) == 1
        usage = cls.limits['File systems'].get_current_usage()
        assert len(usage) == 0

    def test_find_usage_connect_timeout(self):
        exc = ConnectTimeout()
        mock_conn = Mock()
        with patch('%s.connect' % pb) as mock_connect:
            with patch('%s.paginate_dict' % pbm) as mock_paginate:
                mock_paginate.side_effect = exc
                cls = _EfsService(21, 43)
                cls.conn = mock_conn
                assert cls._have_usage is False
                cls.find_usage()
        assert cls._have_usage is True
        assert mock_connect.mock_calls == [call()]
        assert mock_paginate.mock_calls == [
            call(
                mock_conn.describe_file_systems,
                alc_marker_path=['NextMarker'],
                alc_data_path=['FileSystems'],
                alc_marker_param='Marker'
            )
        ]
        assert len(cls.limits) == 1
        usage = cls.limits['File systems'].get_current_usage()
        assert len(usage) == 0

    def test_required_iam_permissions(self):
        cls = _EfsService(21, 43)
        assert cls.required_iam_permissions() == [
            'elasticfilesystem:DescribeFileSystems'
        ]
