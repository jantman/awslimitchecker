"""
awslimitchecker/tests/services/test_elasticbeanstalk.py

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
Brian Flad <bflad417@gmail.com> <http://www.fladpad.com>
################################################################################
"""

import sys
from awslimitchecker.tests.services import result_fixtures
from awslimitchecker.services.elasticbeanstalk import _ElasticBeanstalkService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT


pbm = 'awslimitchecker.services.elasticbeanstalk'  # module patch base
pb = '%s._ElasticBeanstalkService' % pbm  # class patch pase


class Test_ElasticBeanstalkService(object):

    def test_init(self):
        """test __init__()"""
        cls = _ElasticBeanstalkService(21, 43)
        assert cls.service_name == 'ElasticBeanstalk'
        assert cls.api_name == 'elasticbeanstalk'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        """test get limits returns all keys"""
        cls = _ElasticBeanstalkService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Applications',
            'Application versions',
            'Environments',
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _ElasticBeanstalkService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        """test find usage method calls other methods"""
        mock_conn = Mock()
        with patch('%s.connect' % pb) as mock_connect:
            with patch.multiple(
                pb,
                _find_usage_applications=DEFAULT,
                _find_usage_application_versions=DEFAULT,
                _find_usage_environments=DEFAULT,
            ) as mocks:
                cls = _ElasticBeanstalkService(21, 43)
                cls.conn = mock_conn
                assert cls._have_usage is False
                cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        assert mock_conn.mock_calls == []
        for x in [
            '_find_usage_applications',
            '_find_usage_application_versions',
            '_find_usage_environments',
        ]:
            assert mocks[x].mock_calls == [call()]

    def test_find_usage_applications(self):
        response = result_fixtures.ElasticBeanstalk.test_find_usage_applications

        mock_conn = Mock()
        mock_conn.describe_applications.return_value = response

        cls = _ElasticBeanstalkService(21, 43)
        cls.conn = mock_conn

        cls._find_usage_applications()

        assert len(cls.limits['Applications'].get_current_usage()) == 1
        assert cls.limits['Applications'].get_current_usage()[
            0].get_value() == 2
        assert mock_conn.mock_calls == [
            call.describe_applications()
        ]

    def test_find_usage_application_versions(self):
        beanstalk_fixtures = result_fixtures.ElasticBeanstalk
        response = beanstalk_fixtures.test_find_usage_application_versions

        mock_conn = Mock()
        mock_conn.describe_application_versions.return_value = response

        cls = _ElasticBeanstalkService(21, 43)
        cls.conn = mock_conn

        cls._find_usage_application_versions()

        assert len(cls.limits['Application versions'].get_current_usage()) == 1
        assert cls.limits['Application versions'].get_current_usage()[
            0].get_value() == 4
        assert mock_conn.mock_calls == [
            call.describe_application_versions()
        ]

    def test_find_usage_environments(self):
        response = result_fixtures.ElasticBeanstalk.test_find_usage_environments

        mock_conn = Mock()
        mock_conn.describe_environments.return_value = response

        cls = _ElasticBeanstalkService(21, 43)
        cls.conn = mock_conn

        cls._find_usage_environments()

        assert len(cls.limits['Environments'].get_current_usage()) == 1
        assert cls.limits['Environments'].get_current_usage()[
            0].get_value() == 2
        assert mock_conn.mock_calls == [
            call.describe_environments()
        ]

    def test_required_iam_permissions(self):
        """test expected permissions are returned"""
        cls = _ElasticBeanstalkService(21, 43)
        assert cls.required_iam_permissions() == [
            'elasticbeanstalk:DescribeApplications',
            'elasticbeanstalk:DescribeApplicationVersions',
            'elasticbeanstalk:DescribeEnvironments',
        ]
