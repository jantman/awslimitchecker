"""
awslimitchecker/tests/services/test_iam.py

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
from awslimitchecker.services.iam import _IamService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock


pbm = 'awslimitchecker.services.iam'  # module patch base
pb = '%s._IamService' % pbm  # class patch pase


class Test_IamService(object):

    def test_init(self):
        """test __init__()"""
        cls = _IamService(21, 43)
        assert cls.service_name == 'IAM'
        assert cls.api_name == 'iam'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _IamService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Groups',
            'Users',
            'Roles',
            'Instance profiles',
            'Server certificates',
            'Policies',
            'Policy Versions In Use',
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _IamService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        with patch('%s._update_limits_from_api' % pb) as mock_update:
            cls = _IamService(21, 43)
            assert cls._have_usage is False
            cls.find_usage()
        assert mock_update.mock_calls == [call()]
        assert cls._have_usage is True

    def test_required_iam_permissions(self):
        cls = _IamService(21, 43)
        assert cls.required_iam_permissions() == [
            'iam:GetAccountSummary'
        ]

    def test_update_limits_from_api(self):
        mock_summary = Mock(
            summary_map=result_fixtures.IAM.test_update_limits_from_api
        )
        mock_conn = Mock()
        mock_conn.AccountSummary.return_value = mock_summary
        with patch('%s.logger' % pbm) as mock_logger:
            with patch('%s.connect_resource' % pb) as mock_connect:
                cls = _IamService(21, 43)
                cls.resource_conn = mock_conn
                cls._update_limits_from_api()
        assert mock_connect.mock_calls == [call()]
        assert mock_conn.mock_calls == [call.AccountSummary()]

        assert call.debug('Ignoring IAM AccountSummary attribute: %s',
                          'GroupsPerUserQuota') in mock_logger.mock_calls

        lim = cls.limits['Groups']
        assert lim.api_limit == 100
        assert lim.get_current_usage()[0].get_value() == 25

        lim = cls.limits['Users']
        assert lim.api_limit == 5000
        assert lim.get_current_usage()[0].get_value() == 152

        lim = cls.limits['Roles']
        assert lim.api_limit == 501
        assert lim.get_current_usage()[0].get_value() == 375

        lim = cls.limits['Instance profiles']
        assert lim.api_limit == 500
        assert lim.get_current_usage()[0].get_value() == 394

        lim = cls.limits['Server certificates']
        assert lim.api_limit == 101
        assert lim.get_current_usage()[0].get_value() == 55

        lim = cls.limits['Policies']
        assert lim.api_limit == 1000
        assert lim.get_current_usage()[0].get_value() == 17

        lim = cls.limits['Policy Versions In Use']
        assert lim.api_limit == 10000
        assert lim.get_current_usage()[0].get_value() == 53
