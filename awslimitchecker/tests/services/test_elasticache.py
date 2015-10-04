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
from boto.elasticache.layer1 import ElastiCacheConnection
from boto.elasticache import connect_to_region
from boto.exception import BotoServerError
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

    def test_connect(self):
        """test connect()"""
        mock_conn = Mock(spec_set=ElastiCacheConnection)
        mock_conn_via = Mock(spec_set=ElastiCacheConnection)
        cls = _ElastiCacheService(21, 43)
        with patch('%s.ElastiCacheConnection' % self.pbm) as mock_elasticache:
            with patch('%s.connect_via' % self.pb) as mock_connect_via:
                mock_elasticache.return_value = mock_conn
                mock_connect_via.return_value = mock_conn_via
                cls.connect()
        assert mock_elasticache.mock_calls == [call()]
        assert mock_conn.mock_calls == []
        assert mock_connect_via.mock_calls == []
        assert cls.conn == mock_conn

    def test_connect_region(self):
        """test connect()"""
        mock_conn = Mock(spec_set=ElastiCacheConnection)
        mock_conn_via = Mock(spec_set=ElastiCacheConnection)
        cls = _ElastiCacheService(21, 43, region='foo')
        with patch('%s.ElastiCacheConnection' % self.pbm) as mock_elasticache:
            with patch('%s.connect_via' % self.pb) as mock_connect_via:
                mock_elasticache.return_value = mock_conn
                mock_connect_via.return_value = mock_conn_via
                cls.connect()
        assert mock_elasticache.mock_calls == []
        assert mock_conn.mock_calls == []
        assert mock_connect_via.mock_calls == [
            call(connect_to_region)
        ]
        assert cls.conn == mock_conn_via

    def test_connect_again(self):
        """make sure we re-use the connection"""
        mock_conn = Mock()
        cls = _ElastiCacheService(21, 43)
        cls.conn = mock_conn
        with patch('awslimitchecker.services.elasticache.ElastiCacheConnection'
                   '') as mock_elasticache:
            with patch('%s.connect_via' % self.pb) as mock_connect_via:
                mock_elasticache.return_value = mock_conn
                cls.connect()
        assert mock_elasticache.mock_calls == []
        assert mock_conn.mock_calls == []
        assert mock_connect_via.mock_calls == []

    def test_get_limits(self):
        cls = _ElastiCacheService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Nodes',
            'Clusters',
            'Nodes per Cluster',
            'Parameter Groups',
            'Subnet Groups',
            'Security Groups',
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
        mock_conn = Mock(spec_set=ElastiCacheConnection)

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
        clusters = [
            {
                'Engine': 'memcached',
                'CacheParameterGroup': {
                    'CacheNodeIdsToReboot': [],
                    'CacheParameterGroupName': 'default.memcached1.4',
                    'ParameterApplyStatus': 'in-sync'
                },
                'CacheClusterId': 'memcached1',
                'CacheSecurityGroups': [],
                'ConfigurationEndpoint': {
                    'Port': 11211,
                    'Address': 'memcached1.vfavzi.cfg.use1.'
                    'cache.amazonaws.com'
                },
                'CacheClusterCreateTime': 1431109646.755,
                'ReplicationGroupId': None,
                'AutoMinorVersionUpgrade': True,
                'CacheClusterStatus': 'available',
                'NumCacheNodes': 1,
                'PreferredAvailabilityZone': 'us-east-1d',
                'SecurityGroups': [
                    {
                        'Status': 'active',
                        'SecurityGroupId': 'sg-11111111'
                    }
                ],
                'CacheSubnetGroupName': 'csg-memcached1',
                'EngineVersion': '1.4.14',
                'PendingModifiedValues': {
                    'NumCacheNodes': None,
                    'EngineVersion': None,
                    'CacheNodeIdsToRemove': None
                },
                'CacheNodeType': 'cache.t2.small',
                'NotificationConfiguration': None,
                'PreferredMaintenanceWindow': 'mon:05:30-mon:06:30',
                'CacheNodes': [
                    {
                        'CacheNodeId': '0001',
                        'Endpoint': {
                            'Port': 11211,
                            'Address': 'memcached1.vfavzi.0001.'
                            'use1.cache.amazonaws.com'
                        },
                        'CacheNodeStatus': 'available',
                        'ParameterGroupStatus': 'in-sync',
                        'CacheNodeCreateTime': 1431109646.755,
                        'SourceCacheNodeId': None
                    }
                ]
            },
            {
                'Engine': 'redis',
                'CacheParameterGroup': {
                    'CacheNodeIdsToReboot': [],
                    'CacheParameterGroupName': 'default.redis2.8',
                    'ParameterApplyStatus': 'in-sync'
                },
                'CacheClusterId': 'redis1',
                'CacheSecurityGroups': [
                    {
                        'Status': 'active',
                        'CacheSecurityGroupName': 'csg-redis1'
                    }
                ],
                'ConfigurationEndpoint': None,
                'CacheClusterCreateTime': 1412253787.914,
                'ReplicationGroupId': None,
                'AutoMinorVersionUpgrade': True,
                'CacheClusterStatus': 'available',
                'NumCacheNodes': 2,
                'PreferredAvailabilityZone': 'us-east-1a',
                'SecurityGroups': None,
                'CacheSubnetGroupName': None,
                'EngineVersion': '2.8.6',
                'PendingModifiedValues': {
                    'NumCacheNodes': None,
                    'EngineVersion': None,
                    'CacheNodeIdsToRemove': None
                },
                'CacheNodeType': 'cache.m3.medium',
                'NotificationConfiguration': None,
                'PreferredMaintenanceWindow': 'mon:05:30-mon:06:30',
                'CacheNodes': [
                    {
                        'CacheNodeId': '0001',
                        'Endpoint': {
                            'Port': 6379,
                            'Address': 'redis1.vfavzi.0001.use1.cache.'
                            'amazonaws.com'
                        },
                        'CacheNodeStatus': 'available',
                        'ParameterGroupStatus': 'in-sync',
                        'CacheNodeCreateTime': 1412253787.914,
                        'SourceCacheNodeId': None
                    },
                    {
                        'CacheNodeId': '0002',
                        'Endpoint': {
                            'Port': 6379,
                            'Address': 'redis1.vfavzi.0002.use1.cache.'
                            'amazonaws.com'
                        },
                        'CacheNodeStatus': 'available',
                        'ParameterGroupStatus': 'in-sync',
                        'CacheNodeCreateTime': 1412253787.914,
                        'SourceCacheNodeId': None
                    }
                ]
            },
            {
                'Engine': 'redis',
                'CacheParameterGroup': {
                    'CacheNodeIdsToReboot': [],
                    'CacheParameterGroupName': 'default.redis2.8',
                    'ParameterApplyStatus': 'in-sync'
                },
                'CacheClusterId': 'redis2',
                'CacheSecurityGroups': [
                    {
                        'Status': 'active',
                        'CacheSecurityGroupName': 'csg-redis2'
                    }
                ],
                'ConfigurationEndpoint': None,
                'CacheClusterCreateTime': 1412253787.123,
                'ReplicationGroupId': None,
                'AutoMinorVersionUpgrade': True,
                'CacheClusterStatus': 'available',
                'NumCacheNodes': 4,
                'PreferredAvailabilityZone': 'us-east-1a',
                'SecurityGroups': None,
                'CacheSubnetGroupName': None,
                'EngineVersion': '2.8.6',
                'PendingModifiedValues': {
                    'NumCacheNodes': None,
                    'EngineVersion': None,
                    'CacheNodeIdsToRemove': None
                },
                'CacheNodeType': 'cache.m3.medium',
                'NotificationConfiguration': None,
                'PreferredMaintenanceWindow': 'mon:05:30-mon:06:30',
                'CacheNodes': None,
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
        assert usage[0].get_value() == 7

        usage = cls.limits['Clusters'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 3

        usage = sorted(cls.limits['Nodes per Cluster'].get_current_usage())
        assert len(usage) == 3
        assert usage[0].get_value() == 1
        assert usage[0].resource_id == 'memcached1'
        assert usage[1].get_value() == 2
        assert usage[1].resource_id == 'redis1'
        assert usage[2].get_value() == 4
        assert usage[2].resource_id == 'redis2'

        assert mock_conn.mock_calls == [
            call.describe_cache_clusters(show_cache_node_info=True),
        ]

    def test_find_usage_subnet_groups(self):
        """test find usage for subnet groups"""
        data = {
            'DescribeCacheSubnetGroupsResponse': {
                'DescribeCacheSubnetGroupsResult': {
                    'CacheSubnetGroups': [
                        {
                            'Subnets': [
                                {
                                    'SubnetIdentifier': 'subnet-62e8783b',
                                    'SubnetAvailabilityZone': {
                                        'Name': 'us-east-1d'}
                                },
                                {
                                    'SubnetIdentifier': 'subnet-0b037e7c',
                                    'SubnetAvailabilityZone': {
                                        'Name': 'us-east-1a'
                                    }
                                }
                            ],
                            'CacheSubnetGroupName': 'break-memca-135tjabqoyywd',
                            'VpcId': 'vpc-73ec9716',
                            'CacheSubnetGroupDescription': 'memcached'
                        },
                        {
                            'Subnets': [
                                {
                                    'SubnetIdentifier': 'subnet-38e87861',
                                    'SubnetAvailabilityZone': {
                                        'Name': 'us-east-1d'
                                    }
                                },
                                {
                                    'SubnetIdentifier': 'subnet-4f027f38',
                                    'SubnetAvailabilityZone': {
                                        'Name': 'us-east-1a'
                                    }
                                }
                            ],
                            'CacheSubnetGroupName': 'break-memca-6yi6axon9ol9',
                            'VpcId': 'vpc-1ee8937b',
                            'CacheSubnetGroupDescription': 'memcached'
                        },
                        {
                            'Subnets': [
                                {
                                    'SubnetIdentifier': 'subnet-49071f61',
                                    'SubnetAvailabilityZone': {
                                        'Name': 'us-east-1e'
                                    }
                                },
                                {
                                    'SubnetIdentifier': 'subnet-6fe23c18',
                                    'SubnetAvailabilityZone': {
                                        'Name': 'us-east-1a'
                                    }
                                },
                                {
                                    'SubnetIdentifier': 'subnet-a9b54df0',
                                    'SubnetAvailabilityZone': {
                                        'Name': 'us-east-1d'
                                    }
                                }
                            ],
                            'CacheSubnetGroupName': 'lsp-d-redis-14d9407dl05er',
                            'VpcId': 'vpc-c300b9a6',
                            'CacheSubnetGroupDescription': 'redis'
                        },
                    ],
                    'Marker': None
                },
                'ResponseMetadata': {
                    'RequestId': '79654b0b-26ac-11e5-aaab-63850f3e3bca'
                }
            }
        }

        mock_conn = Mock(spec_set=ElastiCacheConnection)
        mock_conn.describe_cache_subnet_groups.return_value = data
        cls = _ElastiCacheService(21, 43)
        cls.conn = mock_conn
        cls._find_usage_subnet_groups()

        assert mock_conn.mock_calls == [
            call.describe_cache_subnet_groups(),
        ]

        usage = cls.limits['Subnet Groups'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 3

    def test_find_usage_parameter_groups(self):
        """test find usage for parameter groups"""
        data = {
            'DescribeCacheParameterGroupsResponse': {
                'DescribeCacheParameterGroupsResult': {
                    'Marker': None,
                    'CacheParameterGroups': [
                        {
                            'CacheParameterGroupName': 'default.memcached1.4',
                            'CacheParameterGroupFamily': 'memcached1.4',
                            'Description': 'Default for memcached1.4'
                        },
                        {
                            'CacheParameterGroupName': 'default.redis2.6',
                            'CacheParameterGroupFamily': 'redis2.6',
                            'Description': 'Default for redis2.6'
                        },
                        {
                            'CacheParameterGroupName': 'default.redis2.8',
                            'CacheParameterGroupFamily': 'redis2.8',
                            'Description': 'Default for redis2.8'
                        }
                    ]
                },
                'ResponseMetadata': {
                    'RequestId': 'ab5d593f-26ac-11e5-a6dd-17ec0aded872'
                }
            }
        }

        mock_conn = Mock(spec_set=ElastiCacheConnection)
        mock_conn.describe_cache_parameter_groups.return_value = data
        cls = _ElastiCacheService(21, 43)
        cls.conn = mock_conn
        cls._find_usage_parameter_groups()

        assert mock_conn.mock_calls == [
            call.describe_cache_parameter_groups(),
        ]

        usage = cls.limits['Parameter Groups'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 3

    def test_find_usage_security_groups(self):
        """test find usage for security groups"""
        data = {
            'DescribeCacheSecurityGroupsResponse': {
                'DescribeCacheSecurityGroupsResult': {
                    'Marker': None,
                    'CacheSecurityGroups': [
                        {
                            'OwnerId': '123456789012',
                            'CacheSecurityGroupName': 'default',
                            'Description': 'default',
                            'EC2SecurityGroups': []
                        },
                        {
                            'OwnerId': '123456789012',
                            'CacheSecurityGroupName': 'csg1',
                            'Description': 'foo bar',
                            'EC2SecurityGroups': [
                                {
                                    'EC2SecurityGroupName': 'ec2-sg1',
                                    'Status': 'authorized',
                                    'EC2SecurityGroupOwnerId': '123456789012'
                                }
                            ]
                        }
                    ]
                },
                'ResponseMetadata': {
                    'RequestId': 'be15fa9c-26ac-11e5-a849-894e77ed58a8'
                }
            }
        }

        mock_conn = Mock(spec_set=ElastiCacheConnection)
        mock_conn.describe_cache_security_groups.return_value = data
        cls = _ElastiCacheService(21, 43)
        cls.conn = mock_conn
        cls._find_usage_security_groups()

        assert mock_conn.mock_calls == [
            call.describe_cache_security_groups(),
        ]

        usage = cls.limits['Security Groups'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 2

    def test_find_usage_security_groups_exception(self):
        """test find usage for security groups"""
        def se_exc():
            raise BotoServerError(None, None, None)

        mock_conn = Mock(spec_set=ElastiCacheConnection)
        mock_conn.describe_cache_security_groups.side_effect = se_exc
        cls = _ElastiCacheService(21, 43)
        cls.conn = mock_conn
        cls._find_usage_security_groups()

        assert mock_conn.mock_calls == [
            call.describe_cache_security_groups(),
        ]

        usage = cls.limits['Security Groups'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 0

    def test_required_iam_permissions(self):
        cls = _ElastiCacheService(21, 43)
        assert cls.required_iam_permissions() == [
            "elasticache:DescribeCacheClusters",
            "elasticache:DescribeCacheParameterGroups",
            "elasticache:DescribeCacheSecurityGroups",
            "elasticache:DescribeCacheSubnetGroups",
        ]
