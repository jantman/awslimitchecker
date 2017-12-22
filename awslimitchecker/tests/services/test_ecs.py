"""
awslimitchecker/services/ecs.py

The latest version of this package is available at:
<https://github.com/di1214/awslimitchecker>

################################################################################
Copyright 2015-2017 Di Zou <zou@pythian.com>

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
bugs please submit them at <https://github.com/di1214/pydnstest> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Di Zou <zou@pythian.com>
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
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock


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
            'Services per Cluster',
            # 'EC2 Tasks per Service (desired count)',
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
        mock_conn = Mock()
        mock_conn.describe_clusters.return_value = {
            'clusters': [
                {
                    'clusterArn': 'string',
                    'clusterName': 'string',
                    'status': 'string',
                    'registeredContainerInstancesCount': 123,
                    'runningTasksCount': 123,
                    'pendingTasksCount': 123,
                    'activeServicesCount': 123,
                    'statistics': [
                        {
                            'name': 'string',
                            'value': 'string'
                        },
                    ]
                },
            ],
            'failures': [
                {
                    'arn': 'string',
                    'reason': 'string'
                },
            ]
        }
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{
            'clusterArns': [
                'string',
            ],
            'nextToken': 'string'
        }]

        mock_conn.get_paginator.return_value = mock_paginator
        with patch('%s.connect' % pb) as mock_connect:
            cls = _EcsService(21, 43)
            cls.conn = mock_conn
            assert cls._have_usage is False
            cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        assert mock_conn.mock_calls == [
            call.get_paginator('list_clusters'),
            call.get_paginator().paginate(),
            call.describe_clusters(
                clusters=['string'],
                include=[
                    'registeredContainerInstancesCount',
                    'activeEC2ServiceCount'
                ]
            )
        ]

    def test_required_iam_permissions(self):
        cls = _EcsService(21, 43)
        assert cls.required_iam_permissions() == [
            "ecs:Describe*",
            "ecs:List*"
        ]
