"""
awslimitchecker/tests/services/result_fixtures.py

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

from datetime import datetime

# boto3 response fixtures


class EBS(object):

    test_find_usage_ebs = {
        'Volumes': [
            # 500G magnetic
            {
                'VolumeId': 'vol-1',
                'Size': 500,
                'VolumeType': 'standard',
                'Iops': None,
                # boilerplate sample response
                'SnapshotId': 'string',
                'AvailabilityZone': 'string',
                'State': 'available',
                'CreateTime': datetime(2015, 1, 1),
                'Attachments': [
                    {
                        'VolumeId': 'string',
                        'InstanceId': 'string',
                        'Device': 'string',
                        'State': 'attached',
                        'AttachTime': datetime(2015, 1, 1),
                        'DeleteOnTermination': True
                    },
                ],
                'Tags': [
                    {
                        'Key': 'string',
                        'Value': 'string'
                    },
                ],
                'Encrypted': False,
                'KmsKeyId': 'string'
            },
            # 8G magnetic
            {
                'VolumeId': 'vol-2',
                'Size': 8,
                'VolumeType': 'standard',
                'Iops': None,
            },
            # 15G general purpose SSD, 45 IOPS
            {
                'VolumeId': 'vol-3',
                'Size': 15,
                'VolumeType': 'gp2',
                'Iops': 45,
            },
            # 30G general purpose SSD, 90 IOPS
            {
                'VolumeId': 'vol-4',
                'Size': 30,
                'VolumeType': 'gp2',
                'Iops': 90,
            },
            # 400G PIOPS, 700 IOPS
            {
                'VolumeId': 'vol-5',
                'Size': 400,
                'VolumeType': 'io1',
                'Iops': 700,
            },
            # 100G PIOPS, 300 IOPS
            {
                'VolumeId': 'vol-6',
                'Size': 100,
                'VolumeType': 'io1',
                'Iops': 300,
            },
            # othertype
            {
                'VolumeId': 'vol-7',
                'VolumeType': 'othertype',
            },
        ]
    }

    test_find_usage_snapshots = {
        'Snapshots': [
            {
                'SnapshotId': 'snap-1',
                'VolumeId': 'string',
                'State': 'completed',
                'StateMessage': 'string',
                'StartTime': datetime(2015, 1, 1),
                'Progress': 'string',
                'OwnerId': 'string',
                'Description': 'string',
                'VolumeSize': 123,
                'OwnerAlias': 'string',
                'Tags': [
                    {
                        'Key': 'string',
                        'Value': 'string'
                    },
                ],
                'Encrypted': False,
                'KmsKeyId': 'string',
                'DataEncryptionKeyId': 'string'
            },
            {'SnapshotId': 'snap-2'},
            {'SnapshotId': 'snap-3'},
        ]
    }


class VPC(object):
    test_find_usage_vpcs = {
        'Vpcs': [
            {
                'VpcId': 'vpc-1',
                'State': 'available',
                'CidrBlock': 'string',
                'DhcpOptionsId': 'string',
                'Tags': [
                    {
                        'Key': 'fooTag',
                        'Value': 'fooVal'
                    },
                ],
                'InstanceTenancy': 'default',
                'IsDefault': False
            },
            {'VpcId': 'vpc-2'},
        ]
    }

    test_find_usage_subnets = {
        'Subnets': [
            {
                'SubnetId': 'string',
                'State': 'available',
                'VpcId': 'vpc-1',
                'CidrBlock': 'string',
                'AvailableIpAddressCount': 123,
                'AvailabilityZone': 'string',
                'DefaultForAz': False,
                'MapPublicIpOnLaunch': True,
                'Tags': [
                    {
                        'Key': 'tagKey',
                        'Value': 'tagVal'
                    },
                ]
            },
            {'VpcId': 'vpc-1'},
            {'VpcId': 'vpc-2'},
        ]
    }

    test_find_usage_acls = {
        'NetworkAcls': [
            {
                'NetworkAclId': 'acl-1',
                'VpcId': 'vpc-1',
                'IsDefault': True,
                'Entries': [
                    {
                        'RuleNumber': 123,
                        'Protocol': 'string',
                        'RuleAction': 'allow',
                        'Egress': True,
                        'CidrBlock': 'string',
                        'IcmpTypeCode': {
                            'Type': 123,
                            'Code': 123
                        },
                        'PortRange': {
                            'From': 123,
                            'To': 123
                        }
                    },
                    {
                        'RuleNumber': 124,
                        'Protocol': 'string',
                        'RuleAction': 'allow',
                        'Egress': False,
                        'CidrBlock': 'string',
                        'IcmpTypeCode': {
                            'Type': 123,
                            'Code': 123
                        },
                        'PortRange': {
                            'From': 124,
                            'To': 124
                        }
                    },
                    {
                        'RuleNumber': 125,
                        'Protocol': 'string',
                        'RuleAction': 'deny',
                        'Egress': False,
                        'CidrBlock': 'string',
                        'IcmpTypeCode': {
                            'Type': 123,
                            'Code': 123
                        },
                        'PortRange': {
                            'From': 125,
                            'To': 125
                        }
                    },
                ],
                'Associations': [
                    {
                        'NetworkAclAssociationId': 'string',
                        'NetworkAclId': 'string',
                        'SubnetId': 'string'
                    },
                ],
                'Tags': [
                    {
                        'Key': 'tagKey',
                        'Value': 'tagVal'
                    },
                ]
            },
            {
                'NetworkAclId': 'acl-2',
                'VpcId': 'vpc-1',
                'Entries': [1],
            },
            {
                'NetworkAclId': 'acl-3',
                'VpcId': 'vpc-2',
                'Entries': [1, 2, 3, 4, 5],
            },
        ]
    }

    test_find_usage_route_tables = {
        'RouteTables': [
            {
                'RouteTableId': 'rt-1',
                'VpcId': 'vpc-1',
                'Routes': [
                    {
                        'DestinationCidrBlock': 'string',
                        'DestinationPrefixListId': 'string',
                        'GatewayId': 'string',
                        'InstanceId': 'string',
                        'InstanceOwnerId': 'string',
                        'NetworkInterfaceId': 'string',
                        'VpcPeeringConnectionId': 'string',
                        'NatGatewayId': 'string',
                        'State': 'active',
                        'Origin': 'CreateRouteTable'
                    },
                    {'foo': 'bar', 'baz': 'blam'},
                    {'foo': 'bar', 'baz': 'blam'},
                ],
                'Associations': [
                    {
                        'RouteTableAssociationId': 'string',
                        'RouteTableId': 'string',
                        'SubnetId': 'string',
                        'Main': True
                    },
                ],
                'Tags': [
                    {
                        'Key': 'tagKey',
                        'Value': 'tagVal'
                    },
                ],
                'PropagatingVgws': [
                    {
                        'GatewayId': 'string'
                    },
                ]
            },
            {
                'RouteTableId': 'rt-2',
                'VpcId': 'vpc-1',
                'Routes': [
                    {'foo': 'bar', 'baz': 'blam'},
                ],
            },
            {
                'RouteTableId': 'rt-3',
                'VpcId': 'vpc-2',
                'Routes': [
                    {'foo': 'bar', 'baz': 'blam'},
                    {'foo': 'bar', 'baz': 'blam'},
                    {'foo': 'bar', 'baz': 'blam'},
                    {'foo': 'bar', 'baz': 'blam'},
                    {'foo': 'bar', 'baz': 'blam'},
                ],
            }
        ]
    }

    test_find_usage_internet_gateways = {
        'InternetGateways': [
            {
                'InternetGatewayId': 'gw-1',
                'Attachments': [
                    {
                        'VpcId': 'string',
                        'State': 'attached'
                    },
                ],
                'Tags': [
                    {
                        'Key': 'tagKey',
                        'Value': 'tagVal'
                    },
                ]
            },
            {'InternetGatewayId': 'gw-2'}
        ]
    }


class RDS(object):
    test_find_usage_instances = [
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

    test_find_usage_snapshots = {
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

    test_find_usage_param_groups = {
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

    test_find_usage_subnet_groups = {
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

    test_find_usage_option_groups = {
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

    # @TODO update this with realistic test data
    test_find_usage_event_subscriptions = {
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

    test_find_usage_security_groups = {
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

    # @TODO update this with realistic test data
    test_find_usage_reserved_instances = {
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


class ELB(object):

    test_find_usage = {
            # this is a subset of response items
            'LoadBalancerDescriptions': [
                {
                    'LoadBalancerName': 'elb-1',
                    'ListenerDescriptions': [
                        {'foo': 'bar'},
                    ],
                },
                {
                    'LoadBalancerName': 'elb-2',
                    'ListenerDescriptions': [
                        {'foo': 'bar'},
                        {'foo': 'bar'},
                    ],
                },
                {
                    'LoadBalancerName': 'elb-3',
                    'ListenerDescriptions': [
                        {'foo': 'bar'},
                        {'foo': 'bar'},
                        {'foo': 'bar'},
                    ],
                },
                {
                    'LoadBalancerName': 'elb-4',
                    'ListenerDescriptions': [
                        {'foo': 'bar'},
                        {'foo': 'bar'},
                        {'foo': 'bar'},
                        {'foo': 'bar'},
                        {'foo': 'bar'},
                        {'foo': 'bar'},
                    ],
                },
            ],
        }


class ElastiCache(object):
    test_find_usage_nodes = []
    # first page of results
    test_find_usage_nodes.append({
        'CacheClusters': [
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
            }
        ],
        'NextToken': 'string',
    })
    # second page of results
    test_find_usage_nodes.append({
        'CacheClusters': [
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
        ],
    })

    test_find_usage_subnet_groups = []
    # first page of results
    test_find_usage_subnet_groups.append({
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
        ],
        'NextToken': 'str'
    })
    # second page of results
    test_find_usage_subnet_groups.append({
        'CacheSubnetGroups': [
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
    })

    test_find_usage_parameter_groups = []
    # first page of results
    test_find_usage_parameter_groups.append({
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
        ],
        'NextToken': 'foo'
    })
    # second page of results
    test_find_usage_parameter_groups.append({
        'CacheParameterGroups': [
            {
                'CacheParameterGroupName': 'default.redis2.8',
                'CacheParameterGroupFamily': 'redis2.8',
                'Description': 'Default for redis2.8'
            }
        ],
    })

    test_find_usage_security_groups = []
    # first page of results
    test_find_usage_security_groups.append({
        'CacheSecurityGroups': [
            {
                'OwnerId': '123456789012',
                'CacheSecurityGroupName': 'default',
                'Description': 'default',
                'EC2SecurityGroups': []
            },
        ],
        'NextToken': 'foo'
    })
    # second page of results
    test_find_usage_security_groups.append({
        'CacheSecurityGroups': [
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
    })


class EC2(object):

    pass
