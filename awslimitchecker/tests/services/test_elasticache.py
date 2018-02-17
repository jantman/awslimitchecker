"""
awslimitchecker/tests/services/test_elasticache.py

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
from botocore.exceptions import ClientError
from awslimitchecker.services.elasticache import _ElastiCacheService
import pytest

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT


class TestElastiCacheService(object):

    pb = 'awslimitchecker.services.elasticache._ElastiCacheService'  # patch
    pbm = 'awslimitchecker.services.elasticache'  # module patch

    def test_init(self):
        """test __init__()"""
        cls = _ElastiCacheService(21, 43)
        assert cls.service_name == 'ElastiCache'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _ElastiCacheService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Nodes',
            'Nodes per Cluster',
            'Parameter Groups',
            'Subnet Groups',
            'Security Groups',
            'Subnets per subnet group'
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _ElastiCacheService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        """overall find usage method"""
        mock_conn = Mock()

        with patch('%s.connect' % self.pb) as mock_connect:
            with patch.multiple(
                self.pb,
                _find_usage_nodes=DEFAULT,
                _find_usage_subnet_groups=DEFAULT,
                _find_usage_parameter_groups=DEFAULT,
                _find_usage_security_groups=DEFAULT,
            ) as mocks:
                cls = _ElastiCacheService(21, 43)
                cls.conn = mock_conn
                assert cls._have_usage is False
                cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        assert mock_conn.mock_calls == []
        for x in [
            '_find_usage_nodes',
            '_find_usage_subnet_groups',
            '_find_usage_parameter_groups',
            '_find_usage_security_groups',
        ]:
            assert mocks[x].mock_calls == [call()]

    def test_find_usage_nodes(self):
        """test find usage for nodes"""
        # this also tests pagination
        responses = result_fixtures.ElastiCache.test_find_usage_nodes

        mock_conn = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = responses
        mock_conn.get_paginator.return_value = mock_paginator
        cls = _ElastiCacheService(21, 43)
        cls.conn = mock_conn
        cls._find_usage_nodes()

        usage = cls.limits['Nodes'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 11

        usage = sorted(cls.limits['Nodes per Cluster'].get_current_usage())
        assert len(usage) == 1
        assert usage[0].get_value() == 1
        assert usage[0].resource_id == 'memcached1'

        assert mock_conn.mock_calls == [
            call.get_paginator('describe_cache_clusters'),
            call.get_paginator().paginate(ShowCacheNodeInfo=True)
        ]
        assert mock_paginator.mock_calls == [
            call.paginate(ShowCacheNodeInfo=True)
        ]

    def test_find_usage_subnet_groups(self):
        """test find usage for subnet groups"""
        # this also tests pagination
        responses = result_fixtures.ElastiCache.test_find_usage_subnet_groups

        mock_conn = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = responses
        mock_conn.get_paginator.return_value = mock_paginator
        cls = _ElastiCacheService(21, 43)
        cls.conn = mock_conn

        cls._find_usage_subnet_groups()

        assert mock_conn.mock_calls == [
            call.get_paginator('describe_cache_subnet_groups'),
            call.get_paginator().paginate()
        ]
        assert mock_paginator.mock_calls == [
            call.paginate()
        ]

        usage = cls.limits['Subnet Groups'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 3
        usage2 = cls.limits['Subnets per subnet group'].get_current_usage()
        assert len(usage2) == 3
        assert usage2[0].get_value() == 2
        assert usage2[1].get_value() == 1
        assert usage2[2].get_value() == 3

    def test_find_usage_parameter_groups(self):
        """test find usage for parameter groups"""
        # this also tests pagination
        responses = result_fixtures.ElastiCache.test_find_usage_parameter_groups

        mock_conn = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = responses
        mock_conn.get_paginator.return_value = mock_paginator
        cls = _ElastiCacheService(21, 43)
        cls.conn = mock_conn
        cls._find_usage_parameter_groups()

        assert mock_conn.mock_calls == [
            call.get_paginator('describe_cache_parameter_groups'),
            call.get_paginator().paginate()
        ]
        assert mock_paginator.mock_calls == [
            call.paginate()
        ]

        usage = cls.limits['Parameter Groups'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 3

    def test_find_usage_security_groups(self):
        """test find usage for security groups"""
        # this also tests pagination
        responses = result_fixtures.ElastiCache.test_find_usage_security_groups

        mock_conn = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = responses
        mock_conn.get_paginator.return_value = mock_paginator
        cls = _ElastiCacheService(21, 43)
        cls.conn = mock_conn

        cls._find_usage_security_groups()

        assert mock_conn.mock_calls == [
            call.get_paginator('describe_cache_security_groups'),
            call.get_paginator().paginate()
        ]
        assert mock_paginator.mock_calls == [
            call.paginate()
        ]

        usage = cls.limits['Security Groups'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 2

    def test_find_usage_security_groups_no_ec2_classic(self):
        """test find usage for security groups"""
        def se_exc(*args, **kwargs):
            resp = {
                'ResponseMetadata': {
                    'HTTPStatusCode': 400,
                    'RequestId': '7d74c6f0-c789-11e5-82fe-a96cdaa6d564'
                },
                'Error': {
                    'Message': 'Use of cache security groups is not permitted'
                               ' in this API version for your account.',
                    'Code': 'InvalidParameterValue',
                    'Type': 'Sender'
                }
            }
            raise ClientError(resp, 'operation')

        mock_conn = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.side_effect = se_exc
        mock_conn.get_paginator.return_value = mock_paginator

        cls = _ElastiCacheService(21, 43)
        cls.conn = mock_conn

        with patch('%s.logger' % self.pbm) as mock_logger:
            cls._find_usage_security_groups()

        assert mock_conn.mock_calls == [
            call.get_paginator('describe_cache_security_groups'),
            call.get_paginator().paginate()
        ]
        assert mock_paginator.mock_calls == [
            call.paginate()
        ]
        assert mock_logger.mock_calls == [
            call.debug("caught ClientError checking ElastiCache security "
                       "groups (account without EC2-Classic?)")
        ]

        usage = cls.limits['Security Groups'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 0

    def test_find_usage_security_groups_exception(self):
        """test find usage for security groups"""
        err_resp = {
            'ResponseMetadata': {
                'HTTPStatusCode': 400,
                'RequestId': '7d74c6f0-c789-11e5-82fe-a96cdaa6d564'
            },
            'Error': {
                'Message': 'other message',
                'Code': 'OtherCode',
                'Type': 'Sender'
            }
        }
        exc = ClientError(err_resp, 'operation')

        def se_exc(*args, **kwargs):
            raise exc

        mock_conn = Mock()
        mock_paginator = Mock()
        mock_paginator.paginate.side_effect = se_exc
        mock_conn.get_paginator.return_value = mock_paginator

        cls = _ElastiCacheService(21, 43)
        cls.conn = mock_conn

        with pytest.raises(Exception) as raised:
            cls._find_usage_security_groups()

        assert mock_conn.mock_calls == [
            call.get_paginator('describe_cache_security_groups'),
            call.get_paginator().paginate()
        ]
        assert mock_paginator.mock_calls == [
            call.paginate()
        ]
        assert raised.value == exc

    def test_required_iam_permissions(self):
        cls = _ElastiCacheService(21, 43)
        assert cls.required_iam_permissions() == [
            "elasticache:DescribeCacheClusters",
            "elasticache:DescribeCacheParameterGroups",
            "elasticache:DescribeCacheSecurityGroups",
            "elasticache:DescribeCacheSubnetGroups",
        ]
