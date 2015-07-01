"""
awslimitchecker/tests/services/test_elasticache.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2015 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

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
# TODO confirm this is the correct import
from boto.elasticache.layer1 import ElastiCacheConnection
from awslimitchecker.services.elasticache import _ElastiCacheService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT


class Test_ElastiCacheService(object):

    pb = 'awslimitchecker.services.elasticache._ElastiCacheService'  # patch

    def test_init(self):
        """test __init__()"""
        cls = _ElastiCacheService(21, 43)
        assert cls.service_name == 'ElastiCache'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_connect(self):
        """test connect()"""
        mock_conn = Mock(spec_set=ElastiCacheConnection)
        cls = _ElastiCacheService(21, 43)
        with patch('awslimitchecker.services.elasticache.ElastiCacheConnection'
                   '') as mock_elasticache:
            mock_elasticache.return_value = mock_conn
            cls.connect()
        assert mock_elasticache.mock_calls == [call()]
        assert mock_conn.mock_calls == []

    def test_connect_again(self):
        """make sure we re-use the connection"""
        mock_conn = Mock()
        cls = _ElastiCacheService(21, 43)
        cls.conn = mock_conn
        with patch('awslimitchecker.services.elasticache.ElastiCacheConnection'
                   '') as mock_elasticache:
            mock_elasticache.return_value = mock_conn
            cls.connect()
        assert mock_elasticache.mock_calls == []
        assert mock_conn.mock_calls == []

    def test_get_limits(self):
        cls = _ElastiCacheService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Nodes',
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
        mock_conn = Mock(spec_set=ElastiCacheConnection)

        with patch('%s.connect' % self.pb) as mock_connect:
            with patch.multiple(
                    self.pb,
                    _find_usage_nodes=DEFAULT,
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
        ]:
            assert mocks[x].mock_calls == [call()]

    def test_find_usage_nodes(self):
        clusters = [
            {
                'Engine': 'memcached',
                'CacheParameterGroup': {
                    u'CacheNodeIdsToReboot': [],
                    u'CacheParameterGroupName': u'default.memcached1.4',
                    u'ParameterApplyStatus': u'in-sync'
                },
                u'CacheClusterId': u'memcached1',
                u'CacheSecurityGroups': [],
                u'ConfigurationEndpoint': {
                    u'Port': 11211,
                    u'Address': u'memcached1.vfavzi.cfg.use1.'
                    'cache.amazonaws.com'
                },
                u'CacheClusterCreateTime': 1431109646.755,
                u'ReplicationGroupId': None,
                u'AutoMinorVersionUpgrade': True,
                u'CacheClusterStatus': u'available',
                u'NumCacheNodes': 1,
                u'PreferredAvailabilityZone': u'us-east-1d',
                u'SecurityGroups': [
                    {
                        u'Status': u'active',
                        u'SecurityGroupId': u'sg-11111111'
                    }
                ],
                u'CacheSubnetGroupName': u'csg-memcached1',
                u'EngineVersion': u'1.4.14',
                u'PendingModifiedValues': {
                    u'NumCacheNodes': None,
                    u'EngineVersion': None,
                    u'CacheNodeIdsToRemove': None
                },
                u'CacheNodeType': u'cache.t2.small',
                u'NotificationConfiguration': None,
                u'PreferredMaintenanceWindow': u'mon:05:30-mon:06:30',
                u'CacheNodes': [
                    {
                        u'CacheNodeId': u'0001',
                        u'Endpoint': {
                            u'Port': 11211,
                            u'Address': u'memcached1.vfavzi.0001.'
                            'use1.cache.amazonaws.com'
                        },
                        u'CacheNodeStatus': u'available',
                        u'ParameterGroupStatus': u'in-sync',
                        u'CacheNodeCreateTime': 1431109646.755,
                        u'SourceCacheNodeId': None
                    }
                ]
            },
            {
                u'Engine': u'redis',
                u'CacheParameterGroup': {
                    u'CacheNodeIdsToReboot': [],
                    u'CacheParameterGroupName': u'default.redis2.8',
                    u'ParameterApplyStatus': u'in-sync'
                },
                u'CacheClusterId': u'redis1',
                u'CacheSecurityGroups': [
                    {
                        u'Status': u'active',
                        u'CacheSecurityGroupName': u'csg-redis1'
                    }
                ],
                u'ConfigurationEndpoint': None,
                u'CacheClusterCreateTime': 1412253787.914,
                u'ReplicationGroupId': None,
                u'AutoMinorVersionUpgrade': True,
                u'CacheClusterStatus': u'available',
                u'NumCacheNodes': 1,
                u'PreferredAvailabilityZone': u'us-east-1a',
                u'SecurityGroups': None,
                u'CacheSubnetGroupName': None,
                u'EngineVersion': u'2.8.6',
                u'PendingModifiedValues': {
                    u'NumCacheNodes': None,
                    u'EngineVersion': None,
                    u'CacheNodeIdsToRemove': None
                },
                u'CacheNodeType': u'cache.m3.medium',
                u'NotificationConfiguration': None,
                u'PreferredMaintenanceWindow': u'mon:05:30-mon:06:30',
                u'CacheNodes': [
                    {
                        u'CacheNodeId': u'0001',
                        u'Endpoint': {
                            u'Port': 6379,
                            u'Address': u'redis1.vfavzi.0001.use1.cache.'
                            'amazonaws.com'
                        },
                        u'CacheNodeStatus': u'available',
                        u'ParameterGroupStatus': u'in-sync',
                        u'CacheNodeCreateTime': 1412253787.914,
                        u'SourceCacheNodeId': None
                    }
                ]
            },
        ]
        resp = {
            'DescribeCacheClustersResponse': {
                'DescribeCacheClustersResult': {
                    'CacheClusters': clusters
                }
            }
        }

        mock_conn = Mock(spec_set=ElastiCacheConnection)
        mock_conn.describe_cache_clusters.return_value = resp
        cls = _ElastiCacheService(21, 43)
        cls.conn = mock_conn
        cls._find_usage_nodes()
        usage = cls.limits['Nodes'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 2
        assert mock_conn.mock_calls == [
            call.describe_cache_clusters(show_cache_node_info=True),
        ]

    def test_required_iam_permissions(self):
        cls = _ElastiCacheService(21, 43)
        assert cls.required_iam_permissions() == [
            "elasticache:DescribeCacheClusters"
        ]
