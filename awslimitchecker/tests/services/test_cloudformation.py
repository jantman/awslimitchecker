"""
awslimitchecker/tests/services/test_cloudformation.py

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
from awslimitchecker.services.cloudformation import _CloudformationService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock


pbm = 'awslimitchecker.services.cloudformation'  # module patch base
pb = '%s._CloudformationService' % pbm  # class patch pase


class Test_CloudformationService(object):

    def test_init(self):
        """test __init__()"""
        cls = _CloudformationService(21, 43)
        assert cls.service_name == 'CloudFormation'
        assert cls.api_name == 'cloudformation'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _CloudformationService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Stacks',
        ])
        limit = cls.limits['Stacks']
        assert limit.service == cls
        assert limit.def_warning_threshold == 21
        assert limit.def_critical_threshold == 43
        assert limit.default_limit == 200

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _CloudformationService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [
            {
                'Stacks': [
                    {'StackStatus': 'CREATE_IN_PROGRESS'},
                    {'StackStatus': 'DELETE_COMPLETE'},
                    {'StackStatus': 'DELETE_IN_PROGRESS'},
                    {'StackStatus': 'CREATE_FAILED'},
                ]
            },
            {
                'Stacks': [
                    {'StackStatus': 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS'},
                    {'StackStatus': 'ROLLBACK_COMPLETE'},
                    {'StackStatus': 'DELETE_FAILED'},
                ]
            },
        ]
        mock_conn = Mock()
        mock_conn.get_paginator.return_value = mock_paginator
        with patch('%s.connect' % pb) as mock_connect:
            cls = _CloudformationService(21, 43)
            cls.conn = mock_conn
            assert cls._have_usage is False
            cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        assert mock_conn.mock_calls == [
            call.get_paginator('describe_stacks'),
            call.get_paginator().paginate()
        ]
        assert mock_paginator.mock_calls == [call.paginate()]
        assert len(cls.limits['Stacks'].get_current_usage()) == 1
        assert cls.limits['Stacks'].get_current_usage()[0].get_value() == 6

    def test_update_limits_from_api(self):
        mock_conn = Mock()
        mock_conn.describe_account_limits.return_value = {
            'AccountLimits': [
                {
                    'Name': 'StackLimit',
                    'Value': 400
                },
                {
                    'Name': 'Foo',
                    'Value': 1
                }
            ],
            'ResponseMetadata': {
                'HTTPStatusCode': 200,
                'RequestId': 'cf0140c4'
            }
        }

        with patch('%s.connect' % pb) as mock_connect:
            cls = _CloudformationService(21, 43)
            cls.conn = mock_conn
            cls._update_limits_from_api()
        assert mock_connect.mock_calls == [call()]
        assert mock_conn.mock_calls == [call.describe_account_limits()]
        assert cls.limits['Stacks'].api_limit == 400

    def test_required_iam_permissions(self):
        cls = _CloudformationService(21, 43)
        assert cls.required_iam_permissions() == [
            'cloudformation:DescribeAccountLimits',
            'cloudformation:DescribeStacks'
        ]
