"""
awslimitchecker/tests/services/test_ecs.py

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
Di Zou <zou@pythian.com>
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

import sys
from awslimitchecker.services.ecs import _EcsService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT


pbm = 'awslimitchecker.services.ecs'  # module patch base
pb = '%s._EcsService' % pbm  # class patch pase


class Test_EcsService(object):

    def test_init(self):
        """test __init__()"""
        cls = _EcsService(21, 43)
        assert cls.service_name == 'ECS'
        assert cls.api_name == 'ecs'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _EcsService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Clusters',
            'Container Instances per Cluster',
            'EC2 Tasks per Service (desired count)',
            'Fargate Tasks',
            'Services per Cluster',
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _EcsService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        with patch.multiple(
            pb,
            autospec=True,
            connect=DEFAULT,
            _find_usage_clusters=DEFAULT
        ) as mocks:
            cls = _EcsService(21, 43)
            assert cls._have_usage is False
            cls.find_usage()
        assert mocks['connect'].mock_calls == [call(cls)]
        assert cls._have_usage is True
        assert mocks['connect'].return_value.mock_calls == []

    def test_find_usage_clusters(self):
        def se_clusters(*_, **kwargs):
            if kwargs['clusters'] == ['c1arn']:
                return {
                    'clusters': [
                        {
                            'clusterArn': 'c1arn',
                            'clusterName': 'c1name',
                            'status': 'string',
                            'registeredContainerInstancesCount': 11,
                            'runningTasksCount': 6,
                            'pendingTasksCount': 45,
                            'activeServicesCount': 23,
                            'statistics': [
                                {'name': 'runningEC2TasksCount', 'value': '0'},
                                {
                                    'name': 'runningFargateTasksCount',
                                    'value': '4'
                                },
                                {'name': 'pendingEC2TasksCount', 'value': '0'},
                                {
                                    'name': 'pendingFargateTasksCount',
                                    'value': '2'
                                }
                            ]
                        }
                    ]
                }
            elif kwargs['clusters'] == ['c2arn']:
                return {
                    'clusters': [
                        {
                            'clusterArn': 'c2arn',
                            'clusterName': 'c2name',
                            'status': 'string',
                            'registeredContainerInstancesCount': 3,
                            'runningTasksCount': 8,
                            'pendingTasksCount': 22,
                            'activeServicesCount': 2
                        }
                    ]
                }
            return {}

        mock_conn = Mock()
        mock_conn.describe_clusters.side_effect = se_clusters
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{
            'clusterArns': [
                'c1arn',
                'c2arn'
            ],
            'nextToken': 'string'
        }]

        mock_conn.get_paginator.return_value = mock_paginator
        cls = _EcsService(21, 43)
        cls.conn = mock_conn
        with patch('%s._find_usage_one_cluster' % pb, autospec=True) as m_fuoc:
            cls._find_usage_clusters()
        assert mock_conn.mock_calls == [
            call.get_paginator('list_clusters'),
            call.get_paginator().paginate(),
            call.describe_clusters(
                clusters=['c1arn'], include=['STATISTICS']
            ),
            call.describe_clusters(
                clusters=['c2arn'], include=['STATISTICS']
            )
        ]
        c = cls.limits['Container Instances per Cluster'].get_current_usage()
        assert len(c) == 2
        assert c[0].get_value() == 11
        assert c[0].resource_id == 'c1name'
        assert c[1].get_value() == 3
        assert c[1].resource_id == 'c2name'
        s = cls.limits['Services per Cluster'].get_current_usage()
        assert len(s) == 2
        assert s[0].get_value() == 23
        assert s[0].resource_id == 'c1name'
        assert s[1].get_value() == 2
        assert s[1].resource_id == 'c2name'
        u = cls.limits['Clusters'].get_current_usage()
        assert len(u) == 1
        assert u[0].get_value() == 2
        assert u[0].resource_id is None
        f = cls.limits['Fargate Tasks'].get_current_usage()
        assert len(f) == 1
        assert f[0].get_value() == 4
        assert f[0].resource_id is None
        assert m_fuoc.mock_calls == [
            call(cls, 'c1name'),
            call(cls, 'c2name')
        ]

    def test_find_usage_one_cluster(self):

        def se_cluster(*_, **kwargs):
            if kwargs['services'] == ['s1arn']:
                return {
                    'services': [
                        {
                            'launchType': 'EC2',
                            'serviceName': 's1',
                            'desiredCount': 4
                        }
                    ]
                }
            elif kwargs['services'] == ['s2arn']:
                return {
                    'services': [
                        {
                            'launchType': 'Fargate',
                            'serviceName': 's2',
                            'desiredCount': 26
                        }
                    ]
                }
            elif kwargs['services'] == ['s3arn']:
                return {
                    'services': [
                        {
                            'launchType': 'EC2',
                            'serviceName': 's3',
                            'desiredCount': 8
                        }
                    ]
                }
            else:
                return {}

        mock_conn = Mock()
        mock_conn.describe_services.side_effect = se_cluster
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{
            'serviceArns': [
                's1arn',
                's2arn',
                's3arn'
            ],
            'nextToken': 'string'
        }]
        mock_conn.get_paginator.return_value = mock_paginator

        cls = _EcsService(21, 43)
        cls.conn = mock_conn
        cls._find_usage_one_cluster('cName')

        assert mock_conn.mock_calls == [
            call.get_paginator('list_services'),
            call.get_paginator().paginate(
                cluster='cName', launchType='EC2'
            ),
            call.describe_services(cluster='cName', services=['s1arn']),
            call.describe_services(cluster='cName', services=['s2arn']),
            call.describe_services(cluster='cName', services=['s3arn'])
        ]
        u = cls.limits[
            'EC2 Tasks per Service (desired count)'
        ].get_current_usage()
        assert len(u) == 2
        assert u[0].get_value() == 4
        assert u[0].resource_id == 'cluster=cName; service=s1'
        assert u[0].aws_type == 'AWS::ECS::Service'
        assert u[1].get_value() == 8
        assert u[1].resource_id == 'cluster=cName; service=s3'
        assert u[1].aws_type == 'AWS::ECS::Service'

    def test_required_iam_permissions(self):
        cls = _EcsService(21, 43)
        assert sorted(cls.required_iam_permissions()) == [
            'ecs:DescribeClusters',
            'ecs:DescribeServices',
            'ecs:ListClusters',
            'ecs:ListServices'
        ]
