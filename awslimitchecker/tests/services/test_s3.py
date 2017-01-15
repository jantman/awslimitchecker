"""
awslimitchecker/tests/services/test_s3.py

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
from awslimitchecker.services.s3 import _S3Service
from awslimitchecker.limit import AwsLimit

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock


pbm = 'awslimitchecker.services.s3'  # module patch base
pb = '%s._S3Service' % pbm  # class patch pase


class Test_S3Service(object):

    def test_init(self):
        """test __init__()"""
        cls = _S3Service(21, 43)
        assert cls.service_name == 'S3'
        assert cls.api_name == 's3'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _S3Service(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Buckets',
        ])
        assert res['Buckets'].service == cls
        assert res['Buckets'].def_warning_threshold == 21
        assert res['Buckets'].def_critical_threshold == 43
        assert res['Buckets'].default_limit == 100

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock(spec_set=AwsLimit)
        cls = _S3Service(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        mock_buckets = Mock()
        mock_buckets.all.return_value = ['a', 'b', 'c']
        mock_conn = Mock(buckets=mock_buckets)
        with patch('%s.connect_resource' % pb) as mock_connect:
            cls = _S3Service(21, 43)
            cls.resource_conn = mock_conn
            assert cls._have_usage is False
            cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        assert mock_buckets.mock_calls == [call.all()]
        assert len(cls.limits['Buckets'].get_current_usage()) == 1
        assert cls.limits['Buckets'].get_current_usage()[0].get_value() == 3

    def test_required_iam_permissions(self):
        cls = _S3Service(21, 43)
        assert cls.required_iam_permissions() == [
            's3:ListAllMyBuckets'
        ]
