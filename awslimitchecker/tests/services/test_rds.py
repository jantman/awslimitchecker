"""
awslimitchecker/tests/services/test_rds.py

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
from boto.rds2.layer1 import RDSConnection
from boto.rds2 import connect_to_region
from awslimitchecker.services.rds import _RDSService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT


class Test_RDSService(object):

    pb = 'awslimitchecker.services.rds._RDSService'  # patch base path
    pbm = 'awslimitchecker.services.rds'  # patch base path - module

    def test_init(self):
        """test __init__()"""
        cls = _RDSService(21, 43)
        assert cls.service_name == 'RDS'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_connect(self):
        """test connect()"""
        mock_conn = Mock()
        mock_conn_via = Mock()
        cls = _RDSService(21, 43)
        with patch('%s.boto.connect_rds2' % self.pbm) as mock_rds:
            with patch('%s.connect_via' % self.pb) as mock_connect_via:
                mock_rds.return_value = mock_conn
                mock_connect_via.return_value = mock_conn_via
                cls.connect()
        assert mock_rds.mock_calls == [call()]
        assert mock_conn.mock_calls == []
        assert mock_connect_via.mock_calls == []
        assert cls.conn == mock_conn

    def test_connect_region(self):
        """test connect()"""
        mock_conn = Mock()
        mock_conn_via = Mock()
        cls = _RDSService(21, 43, region='foo')
        with patch('%s.boto.connect_rds2' % self.pbm) as mock_rds:
            with patch('%s.connect_via' % self.pb) as mock_connect_via:
                mock_rds.return_value = mock_conn
                mock_connect_via.return_value = mock_conn_via
                cls.connect()
        assert mock_rds.mock_calls == []
        assert mock_conn.mock_calls == []
        assert mock_connect_via.mock_calls == [
            call(connect_to_region)
        ]
        assert cls.conn == mock_conn_via

    def test_connect_again(self):
        """make sure we re-use the connection"""
        mock_conn = Mock()
        cls = _RDSService(21, 43)
        cls.conn = mock_conn
        with patch('awslimitchecker.services.rds.boto.connect_rds2'
                   '') as mock_rds:
            with patch('%s.connect_via' % self.pb) as mock_connect_via:
                mock_rds.return_value = mock_conn
                cls.connect()
        assert mock_rds.mock_calls == []
        assert mock_conn.mock_calls == []
        assert mock_connect_via.mock_calls == []

    def test_get_limits(self):
        cls = _RDSService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            # TA  # non-TA / service doc name
            'DB instances',  # 'Instances'
            'Max auths per security group',
            'Storage quota (GB)',  # 'Total storage for all DB instances'
            'DB snapshots per user',  # 'Manual Snapshots'
            'DB security groups',  # 'Security Groups'
            # non-TA
            'Reserved Instances',
            'Parameter Groups',
            'VPC Security Groups',
            'Subnet Groups',
            'Subnets per Subnet Group',
            'Option Groups',
            'Event Subscriptions',
            'Read Replicas per Master',
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _RDSService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        mock_conn = Mock(spec_set=RDSConnection)

        with patch('%s.connect' % self.pb) as mock_connect:
            with patch.multiple(
                    self.pb,
                    _find_usage_instances=DEFAULT,
                    _find_usage_snapshots=DEFAULT,
                    _find_usage_param_groups=DEFAULT,
                    _find_usage_subnet_groups=DEFAULT,
                    _find_usage_option_groups=DEFAULT,
                    _find_usage_event_subscriptions=DEFAULT,
                    _find_usage_security_groups=DEFAULT,
                    _find_usage_reserved_instances=DEFAULT,
            ) as mocks:
                cls = _RDSService(21, 43)
                cls.conn = mock_conn
                assert cls._have_usage is False
                cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        for x in [
                '_find_usage_instances',
                '_find_usage_snapshots',
        ]:
            assert mocks[x].mock_calls == [call()]

    def test_required_iam_permissions(self):
        cls = _RDSService(21, 43)
        assert cls.required_iam_permissions() == [
            "rds:DescribeDBInstances",
            "rds:DescribeDBParameterGroups",
            "rds:DescribeDBSecurityGroups",
            "rds:DescribeDBSnapshots",
            "rds:DescribeDBSubnetGroups",
            "rds:DescribeEventSubscriptions",
            "rds:DescribeOptionGroups",
            "rds:DescribeReservedDBInstances",
        ]

    def test_find_usage_instances(self):
        mock_conn = Mock(spec_set=RDSConnection)
        cls = _RDSService(21, 43)
        cls.conn = mock_conn
        instances = [
            {
                'PubliclyAccessible': False,
                'MasterUsername': 'myuser',
                'LicenseModel': 'general-public-license',
                'VpcSecurityGroups': [
                    {
                        'Status': 'active',
                        'VpcSecurityGroupId': 'sg-aaaaaaaa'
                    }
                ],
                'InstanceCreateTime': 1429910904.366,
                'OptionGroupMemberships': [
                    {
                        'Status': 'in-sync',
                        'OptionGroupName': 'default:mysql-5-6'
                    }
                ],
                'PendingModifiedValues': {
                    'MultiAZ': None,
                    'MasterUserPassword': None,
                    'Port': None,
                    'Iops': None,
                    'AllocatedStorage': None,
                    'EngineVersion': None,
                    'BackupRetentionPeriod': None,
                    'DBInstanceClass': None,
                    'DBInstanceIdentifier': None
                },
                'Engine': 'mysql',
                'MultiAZ': True,
                'LatestRestorableTime': 1435966800.0,
                'DBSecurityGroups': [
                    {
                        'Status': 'active',
                        'DBSecurityGroupName': 'mydb-dbsecuritygroup-aaaa'
                    }
                ],
                'DBParameterGroups': [
                    {
                        'DBParameterGroupName': 'default.mysql5.6',
                        'ParameterApplyStatus': 'in-sync'
                    }
                ],
                'ReadReplicaSourceDBInstanceIdentifier': None,
                'AutoMinorVersionUpgrade': True,
                'PreferredBackupWindow': '07:00-08:00',
                'DBSubnetGroup': {
                    'VpcId': 'vpc-abcdef01',
                    'Subnets': [
                        {
                            'SubnetStatus': 'Active',
                            'SubnetIdentifier': 'subnet-aaaaaaaa',
                            'SubnetAvailabilityZone': {
                                'Name': 'us-east-1d',
                                'ProvisionedIopsCapable': False
                            }
                        },
                        {
                            'SubnetStatus': 'Active',
                            'SubnetIdentifier': 'subnet-22222222',
                            'SubnetAvailabilityZone': {
                                'Name': 'us-east-1a',
                                'ProvisionedIopsCapable': False
                            }
                        }
                    ],
                    'DBSubnetGroupName': 'mydb-dbsubnetgroup-abcd',
                    'SubnetGroupStatus': 'Complete',
                    'DBSubnetGroupDescription': 'Subnet group for RDS instance'
                },
                'SecondaryAvailabilityZone': 'us-east-1a',
                'ReadReplicaDBInstanceIdentifiers': [],
                'AllocatedStorage': 200,
                'BackupRetentionPeriod': 7,
                'DBName': 'wordpress',
                'PreferredMaintenanceWindow': 'tue:08:00-tue:09:00',
                'Endpoint': {
                    'Port': 3306,
                    'Address': 'foo.bar.us-east-1.rds.amazonaws.com'
                },
                'DBInstanceStatus': 'available',
                'StatusInfos': None,
                'EngineVersion': '5.6.22',
                'CharacterSetName': None,
                'AvailabilityZone': 'us-east-1d',
                'Iops': None,
                'DBInstanceClass': 'db.t2.small',
                'DBInstanceIdentifier': 'foo'
            },
            {
                'PubliclyAccessible': False,
                'MasterUsername': 'myuser2',
                'LicenseModel': 'postgresql-license',
                'VpcSecurityGroups': [
                    {
                        'Status': 'active',
                        'VpcSecurityGroupId': 'sg-12345678'
                    }
                ],
                'InstanceCreateTime': 1432238504.239,
                'OptionGroupMemberships': [
                    {
                        'Status': 'in-sync',
                        'OptionGroupName': 'default:postgres-9-3'
                    }
                ],
                'PendingModifiedValues': {
                    'MultiAZ': None,
                    'MasterUserPassword': None,
                    'Port': None,
                    'Iops': None,
                    'AllocatedStorage': None,
                    'EngineVersion': None,
                    'BackupRetentionPeriod': None,
                    'DBInstanceClass': None,
                    'DBInstanceIdentifier': None
                },
                'Engine': 'postgres',
                'MultiAZ': False,
                'LatestRestorableTime': 1435966550.0,
                'DBSecurityGroups': [
                    {
                        'Status': 'active',
                        'DBSecurityGroupName': 'sg1234-dbsecuritygroup-abcd'
                    }
                ],
                'DBParameterGroups': [
                    {
                        'DBParameterGroupName': 'default.postgres9.3',
                        'ParameterApplyStatus': 'in-sync'
                    }
                ],
                'ReadReplicaSourceDBInstanceIdentifier': None,
                'AutoMinorVersionUpgrade': True,
                'PreferredBackupWindow': '03:09-03:39',
                'DBSubnetGroup': {
                    'VpcId': 'vpc-87654321',
                    'Subnets': [
                        {
                            'SubnetStatus': 'Active',
                            'SubnetIdentifier': 'subnet-a1234567',
                            'SubnetAvailabilityZone': {
                                'Name': 'us-east-1e',
                                'ProvisionedIopsCapable': False
                            }
                        },
                        {
                            'SubnetStatus': 'Active',
                            'SubnetIdentifier': 'subnet-b1234567',
                            'SubnetAvailabilityZone': {
                                'Name': 'us-east-1a',
                                'ProvisionedIopsCapable': False
                            }
                        },
                        {
                            'SubnetStatus': 'Active',
                            'SubnetIdentifier': 'subnet-c1234567',
                            'SubnetAvailabilityZone': {
                                'Name': 'us-east-1d',
                                'ProvisionedIopsCapable': False
                            }
                        }
                    ],
                    'DBSubnetGroupName': 'mydb-dbsubnetgroup-abcdef',
                    'SubnetGroupStatus': 'Complete',
                    'DBSubnetGroupDescription': 'Subnet group for RDS instance'
                },
                'SecondaryAvailabilityZone': None,
                'ReadReplicaDBInstanceIdentifiers': ['db-123', 'db-456'],
                'AllocatedStorage': 50,
                'BackupRetentionPeriod': 1,
                'DBName': 'mydbname',
                'PreferredMaintenanceWindow': 'mon:05:11-mon:05:41',
                'Endpoint': {
                    'Port': 5432,
                    'Address': 'baz.blam.us-east-1.rds.amazonaws.com'
                },
                'DBInstanceStatus': 'available',
                'StatusInfos': None,
                'EngineVersion': '9.3.6',
                'CharacterSetName': None,
                'AvailabilityZone': 'us-east-1a',
                'Iops': None,
                'DBInstanceClass': 'db.t2.small',
                'DBInstanceIdentifier': 'baz'
            }
        ]
        mock_conn.describe_db_instances.return_value = {
            'DescribeDBInstancesResponse': {
                'DescribeDBInstancesResult': {
                    'DBInstances': instances
                }
            }
        }

        cls._find_usage_instances()

        assert mock_conn.mock_calls == [
            call.describe_db_instances()
        ]

        usage = sorted(cls.limits['DB instances'].get_current_usage())
        assert len(usage) == 1
        assert usage[0].get_value() == 2
        assert usage[0].aws_type == 'AWS::RDS::DBInstance'

        usage = sorted(cls.limits['Storage quota (GB)'].get_current_usage())
        assert len(usage) == 1
        assert usage[0].get_value() == 250
        assert usage[0].aws_type == 'AWS::RDS::DBInstance'

        usage = sorted(
            cls.limits['Read Replicas per Master'].get_current_usage()
        )
        assert len(usage) == 2
        assert usage[0].get_value() == 0
        assert usage[0].resource_id == 'foo'
        assert usage[1].get_value() == 2
        assert usage[1].resource_id == 'baz'

    def test_find_usage_snapshots(self):
        data = {
            "DescribeDBSnapshotsResponse": {
                "DescribeDBSnapshotsResult": {
                    "DBSnapshots": [
                        {
                            "AllocatedStorage": 100,
                            "AvailabilityZone": "us-east-1a",
                            "DBInstanceIdentifier": "foo-db",
                            "DBSnapshotIdentifier": "foo-db-final-snapshot",
                            "Engine": "postgres",
                            "EngineVersion": "9.3.3",
                            "InstanceCreateTime": 1408035263.101,
                            "Iops": 1000,
                            "LicenseModel": "postgresql-license",
                            "MasterUsername": "dbfoouser",
                            "OptionGroupName": "default:postgres-9-3",
                            "PercentProgress": 100,
                            "Port": 5432,
                            "SnapshotCreateTime": 1408454469.536,
                            "SnapshotType": "manual",
                            "SourceRegion": None,
                            "Status": "available",
                            "VpcId": None
                        },
                        {
                            "AllocatedStorage": 50,
                            "AvailabilityZone": "us-east-1d",
                            "DBInstanceIdentifier": "bd1t3lf90p3lqdx",
                            "DBSnapshotIdentifier":
                                "rds:bd1t3lf90p3lqdx-2015-06-29-07-02",
                            "Engine": "mysql",
                            "EngineVersion": "5.6.22",
                            "InstanceCreateTime": 1429910904.366,
                            "Iops": None,
                            "LicenseModel": "general-public-license",
                            "MasterUsername": "dbuser3",
                            "OptionGroupName": "default:mysql-5-6",
                            "PercentProgress": 100,
                            "Port": 3306,
                            "SnapshotCreateTime": 1435561349.441,
                            "SnapshotType": "automated",
                            "SourceRegion": None,
                            "Status": "available",
                            "VpcId": "vpc-1ee8937b"
                        },
                        {
                            "AllocatedStorage": 25,
                            "AvailabilityZone": "us-east-1d",
                            "DBInstanceIdentifier": "md1e8qwtegkjdgy",
                            "DBSnapshotIdentifier":
                                "rds:md1e8qwtegkjdgy-2015-06-29-07-06",
                            "Engine": "postgres",
                            "EngineVersion": "9.3.6",
                            "InstanceCreateTime": 1433883813.314,
                            "Iops": None,
                            "LicenseModel": "postgresql-license",
                            "MasterUsername": "dbuser4",
                            "OptionGroupName": "default:postgres-9-3",
                            "PercentProgress": 100,
                            "Port": 5432,
                            "SnapshotCreateTime": 1435561593.669,
                            "SnapshotType": "automated",
                            "SourceRegion": None,
                            "Status": "available",
                            "VpcId": "vpc-1ee8937b"
                        },
                    ],
                    "Marker":
                        "YXJuOmF3czpyZHM6dXMtZWFzdC0xOjkzNDQ0NjIwOTU0MTpzbm"
                        "Fwc2hvdDpyZHM6bWQxZThxd3RlZ2tqZGd5LTIwMTUtMDctMDEt"
                        "MDctMDc="
                },
                "ResponseMetadata": {
                    "RequestId": "5fe976b3-2499-11e5-ad5a-1fed04d9fd3d"
                }
            }
        }

        mock_conn = Mock(spec_set=RDSConnection)
        mock_conn.describe_db_snapshots.return_value = data
        cls = _RDSService(21, 43)
        cls.conn = mock_conn

        cls._find_usage_snapshots()

        assert mock_conn.mock_calls == [
            call.describe_db_snapshots()
        ]

        usage = sorted(cls.limits['DB snapshots per user'].get_current_usage())
        assert len(usage) == 1
        assert usage[0].get_value() == 1
        assert usage[0].aws_type == 'AWS::RDS::DBSnapshot'

    def test_find_usage_param_groups(self):
        data = {
            "DescribeDBParameterGroupsResponse": {
                "DescribeDBParameterGroupsResult": {
                    "DBParameterGroups": [
                        {
                            "DBParameterGroupFamily": "mysql5.6",
                            "DBParameterGroupName": "default.mysql5.6",
                            "Description":
                                "Default parameter group for mysql5.6"
                        },
                        {
                            "DBParameterGroupFamily": "postgres9.3",
                            "DBParameterGroupName": "default.postgres9.3",
                            "Description":
                                "Default parameter group for postgres9.3"
                        }
                    ],
                    "Marker": None
                },
                "ResponseMetadata": {
                    "RequestId": "xxxxxxxxxxxxxxx"
                }
            }
        }

        mock_conn = Mock(spec_set=RDSConnection)
        mock_conn.describe_db_parameter_groups.return_value = data
        cls = _RDSService(21, 43)
        cls.conn = mock_conn

        cls._find_usage_param_groups()

        assert mock_conn.mock_calls == [
            call.describe_db_parameter_groups()
        ]

        usage = sorted(cls.limits['Parameter Groups'].get_current_usage())
        assert len(usage) == 1
        assert usage[0].get_value() == 2
        assert usage[0].aws_type == 'AWS::RDS::DBParameterGroup'

    def test_find_usage_subnet_groups(self):
        data = {
            "DescribeDBSubnetGroupsResponse": {
                "DescribeDBSubnetGroupsResult": {
                    "DBSubnetGroups": [
                        {
                            "DBSubnetGroupDescription":
                                "Subnet group for CloudFormation RDS instance",
                            "DBSubnetGroupName":
                                "SubnetGroup1",
                            "SubnetGroupStatus": "Complete",
                            "Subnets": [
                                {
                                    "SubnetAvailabilityZone": {
                                        "Name": "us-east-1d",
                                        "ProvisionedIopsCapable": False
                                    },
                                    "SubnetIdentifier": "subnet-38e87861",
                                    "SubnetStatus": "Active"
                                },
                                {
                                    "SubnetAvailabilityZone": {
                                        "Name": "us-east-1a",
                                        "ProvisionedIopsCapable": False
                                    },
                                    "SubnetIdentifier": "subnet-4f027f38",
                                    "SubnetStatus": "Active"
                                }
                            ],
                            "VpcId": "vpc-1ee8937b"
                        },
                        {
                            "DBSubnetGroupDescription":
                                "Created from the RDS Management Console",
                            "DBSubnetGroupName": "default",
                            "SubnetGroupStatus": "Complete",
                            "Subnets": [
                                {
                                    "SubnetAvailabilityZone": {
                                        "Name": "us-east-1e",
                                        "ProvisionedIopsCapable": False
                                    },
                                    "SubnetIdentifier": "subnet-49071f61",
                                    "SubnetStatus": "Active"
                                },
                                {
                                    "SubnetAvailabilityZone": {
                                        "Name": "us-east-1a",
                                        "ProvisionedIopsCapable": False
                                    },
                                    "SubnetIdentifier": "subnet-6fe23c18",
                                    "SubnetStatus": "Active"
                                },
                                {
                                    "SubnetAvailabilityZone": {
                                        "Name": "us-east-1d",
                                        "ProvisionedIopsCapable": False
                                    },
                                    "SubnetIdentifier": "subnet-a9b54df0",
                                    "SubnetStatus": "Active"
                                }
                            ],
                            "VpcId": "vpc-c300b9a6"
                        },
                        {
                            "DBSubnetGroupDescription":
                                "Subnet group for CloudFormation RDS instance",
                            "DBSubnetGroupName":
                                "SubnetGroup2",
                            "SubnetGroupStatus": "Complete",
                            "Subnets": [
                                {
                                    "SubnetAvailabilityZone": {
                                        "Name": "us-east-1a",
                                        "ProvisionedIopsCapable": False
                                    },
                                    "SubnetIdentifier": "subnet-0b037e7c",
                                    "SubnetStatus": "Active"
                                }
                            ],
                            "VpcId": "vpc-73ec9716"
                        },
                    ],
                    "Marker": None
                },
                "ResponseMetadata": {
                    "RequestId": "7cd7ed68-2499-11e5-ad44-cdf98c606d42"
                }
            }
        }

        mock_conn = Mock(spec_set=RDSConnection)
        mock_conn.describe_db_subnet_groups.return_value = data
        cls = _RDSService(21, 43)
        cls.conn = mock_conn

        cls._find_usage_subnet_groups()

        assert mock_conn.mock_calls == [
            call.describe_db_subnet_groups()
        ]

        usage = sorted(cls.limits['Subnet Groups'].get_current_usage())
        assert len(usage) == 1
        assert usage[0].get_value() == 3
        assert usage[0].aws_type == 'AWS::RDS::DBSubnetGroup'
        usage = sorted(
            cls.limits['Subnets per Subnet Group'].get_current_usage()
        )
        assert len(usage) == 3
        assert usage[0].get_value() == 1
        assert usage[0].aws_type == 'AWS::RDS::DBSubnetGroup'
        assert usage[0].resource_id == "SubnetGroup2"
        assert usage[1].get_value() == 2
        assert usage[1].aws_type == 'AWS::RDS::DBSubnetGroup'
        assert usage[1].resource_id == "SubnetGroup1"
        assert usage[2].get_value() == 3
        assert usage[2].aws_type == 'AWS::RDS::DBSubnetGroup'
        assert usage[2].resource_id == "default"

    def test_find_usage_option_groups(self):
        data = {
            "DescribeOptionGroupsResponse": {
                "DescribeOptionGroupsResult": {
                    "Marker": None,
                    "OptionGroupsList": [
                        {
                            "AllowsVpcAndNonVpcInstanceMemberships": True,
                            "EngineName": "mysql",
                            "MajorEngineVersion": "5.6",
                            "OptionGroupDescription":
                                "Default option group for mysql 5.6",
                            "OptionGroupName": "default:mysql-5-6",
                            "Options": [],
                            "VpcId": None
                        },
                        {
                            "AllowsVpcAndNonVpcInstanceMemberships": True,
                            "EngineName": "postgres",
                            "MajorEngineVersion": "9.3",
                            "OptionGroupDescription":
                                "Default option group for postgres 9.3",
                            "OptionGroupName": "default:postgres-9-3",
                            "Options": [],
                            "VpcId": None
                        }
                    ]
                },
                "ResponseMetadata": {
                    "RequestId": "8725ddc9-2499-11e5-9ed1-d5a3270e57f9"
                }
            }
        }

        mock_conn = Mock(spec_set=RDSConnection)
        mock_conn.describe_option_groups.return_value = data
        cls = _RDSService(21, 43)
        cls.conn = mock_conn

        cls._find_usage_option_groups()

        assert mock_conn.mock_calls == [
            call.describe_option_groups()
        ]

        usage = sorted(cls.limits['Option Groups'].get_current_usage())
        assert len(usage) == 1
        assert usage[0].get_value() == 2
        assert usage[0].aws_type == 'AWS::RDS::DBOptionGroup'

    def test_find_usage_event_subscriptions(self):
        # @TODO update this with realistic test data
        data = {
            "DescribeEventSubscriptionsResponse": {
                "DescribeEventSubscriptionsResult": {
                    "EventSubscriptionsList": ['a'],
                    "Marker": None
                },
                "ResponseMetadata": {
                    "RequestId": "91c0b568-2499-11e5-8440-1fb643a72e45"
                }
            }
        }

        mock_conn = Mock(spec_set=RDSConnection)
        mock_conn.describe_event_subscriptions.return_value = data
        cls = _RDSService(21, 43)
        cls.conn = mock_conn

        cls._find_usage_event_subscriptions()

        assert mock_conn.mock_calls == [
            call.describe_event_subscriptions()
        ]

        usage = sorted(cls.limits['Event Subscriptions'].get_current_usage())
        assert len(usage) == 1
        assert usage[0].get_value() == 1
        assert usage[0].aws_type == 'AWS::RDS::EventSubscription'

    def test_find_usage_security_groups(self):
        data = {
            "DescribeDBSecurityGroupsResponse": {
                "DescribeDBSecurityGroupsResult": {
                    "DBSecurityGroups": [
                        {
                            "DBSecurityGroupDescription": "Frontend Access",
                            "DBSecurityGroupName":
                                "SecurityGroup1",
                            "EC2SecurityGroups": [
                                {
                                    "EC2SecurityGroupId": "sg-c6dd95a2",
                                    "EC2SecurityGroupName":
                                        "EC2SG1",
                                    "EC2SecurityGroupOwnerId": None,
                                    "Status": "authorized"
                                }
                            ],
                            "IPRanges": [],
                            "OwnerId": "123456789012",
                            "VpcId": None
                        },
                        {
                            "DBSecurityGroupDescription":
                                "default:vpc-a926c2cc",
                            "DBSecurityGroupName": "default:vpc-a926c2cc",
                            "EC2SecurityGroups": [],
                            "IPRanges": [],
                            "OwnerId": "123456789012",
                            "VpcId": "vpc-a926c2cc"
                        },
                        {
                            "DBSecurityGroupDescription": "Frontend Access",
                            "DBSecurityGroupName": "SecurityGroup2",
                            "EC2SecurityGroups": [
                                {
                                    "EC2SecurityGroupId": "sg-aaaaaaaa",
                                    "EC2SecurityGroupName": "SGName-aaaaaaaa",
                                    "EC2SecurityGroupOwnerId": None,
                                    "Status": "authorized"
                                },
                                {
                                    "EC2SecurityGroupId": "sg-bbbbbbbb",
                                    "EC2SecurityGroupName": "SGName-bbbbbbbb",
                                    "EC2SecurityGroupOwnerId": None,
                                    "Status": "authorized"
                                },
                                {
                                    "EC2SecurityGroupId": "sg-cccccccc",
                                    "EC2SecurityGroupName": "SGName-cccccccc",
                                    "EC2SecurityGroupOwnerId": None,
                                    "Status": "authorized"
                                },
                            ],
                            "IPRanges": [],
                            "OwnerId": "123456789012",
                            "VpcId": "vpc-73ec9716"
                        },
                        {
                            'VpcId': None,
                            'DBSecurityGroupDescription':
                                'awslimitchecker test',
                            'IPRanges': [
                                {
                                    'Status': 'authorized',
                                    'CIDRIP': '76.122.124.15/32'
                                },
                                {
                                    'Status': 'authorized',
                                    'CIDRIP': '66.6.152.59/32'
                                }
                            ],
                            'OwnerId': '123456789012',
                            'EC2SecurityGroups': [],
                            'DBSecurityGroupName': 'alctest'
                        }
                    ],
                    "Marker": None
                },
                "ResponseMetadata": {
                    "RequestId": "9c78d95d-2499-11e5-9456-735a7f5001de"
                }
            }
        }

        mock_conn = Mock(spec_set=RDSConnection)
        mock_conn.describe_db_security_groups.return_value = data
        cls = _RDSService(21, 43)
        cls.conn = mock_conn

        cls._find_usage_security_groups()

        assert mock_conn.mock_calls == [
            call.describe_db_security_groups()
        ]

        usage = sorted(cls.limits['DB security groups'].get_current_usage())
        assert len(usage) == 1
        assert usage[0].get_value() == 2
        assert usage[0].aws_type == 'AWS::RDS::DBSecurityGroup'

        usage = sorted(cls.limits['VPC Security Groups'].get_current_usage())
        assert len(usage) == 1
        assert usage[0].get_value() == 2
        assert usage[0].aws_type == 'AWS::RDS::DBSecurityGroup'

        usage = sorted(cls.limits[
                           'Max auths per security group'].get_current_usage())
        assert len(usage) == 4
        assert usage[0].get_value() == 0
        assert usage[0].resource_id == 'default:vpc-a926c2cc'
        assert usage[0].aws_type == 'AWS::RDS::DBSecurityGroup'
        assert usage[1].get_value() == 1
        assert usage[1].resource_id == 'SecurityGroup1'
        assert usage[1].aws_type == 'AWS::RDS::DBSecurityGroup'
        assert usage[2].get_value() == 2
        assert usage[2].resource_id == 'alctest'
        assert usage[2].aws_type == 'AWS::RDS::DBSecurityGroup'
        assert usage[3].get_value() == 3
        assert usage[3].resource_id == 'SecurityGroup2'
        assert usage[3].aws_type == 'AWS::RDS::DBSecurityGroup'

    def test_find_usage_reserved_instances(self):
        # @TODO update this with realistic test data
        data = {
            'DescribeReservedDBInstancesResponse': {
                'DescribeReservedDBInstancesResult': {
                    'Marker': None,
                    'ReservedDBInstances': [1, 2]
                },
                'ResponseMetadata': {
                    'RequestId': '75366d86-25a9-11e5-b6fa-c9da955772c6'
                }
            }
        }

        mock_conn = Mock(spec_set=RDSConnection)
        mock_conn.describe_reserved_db_instances.return_value = data
        cls = _RDSService(21, 43)
        cls.conn = mock_conn

        cls._find_usage_reserved_instances()

        assert mock_conn.mock_calls == [
            call.describe_reserved_db_instances()
        ]

        usage = sorted(cls.limits['Reserved Instances'].get_current_usage())
        assert len(usage) == 1
        assert usage[0].get_value() == 2
        assert usage[0].aws_type == 'AWS::RDS::DBInstance'
