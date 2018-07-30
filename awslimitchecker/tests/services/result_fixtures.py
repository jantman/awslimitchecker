"""
awslimitchecker/tests/services/result_fixtures.py

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
from datetime import datetime
import boto3
from boto3.utils import ServiceContext

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import Mock
else:
    from unittest.mock import Mock

# boto3 response fixtures


def get_boto3_resource_model(service_name, resource_name):
    """
    Return a boto3 resource model class for the given service_name and
    resource_name (type).

    NOTE that when the boto3.session.Session object is instantiated, the
     underlying botocore Session will attempt HTTP requests to 169.254.169.254
     to retrieve Instance Metadata and an IAM Role. In order to prevent this,
     you should simply export some bogus AWS credential environment variables.

    :param service_name: name of the service
    :type service_name: str
    :param resource_name: name of the resource type/model to get
    :type resource_name: str
    :return: boto3 resource model class
    """
    session = boto3.session.Session(region_name='us-east-1')
    loader = session._session.get_component('data_loader')
    json_resource_model = loader.load_service_model(service_name,
                                                    'resources-1')
    service_resource = session.resource(service_name)
    service_model = service_resource.meta.client.meta.service_model

    resource_model = json_resource_model['resources'][resource_name]
    resource_cls = session.resource_factory.load_from_definition(
        resource_name=resource_name,
        single_resource_json_definition=resource_model,
        service_context=ServiceContext(
            service_name=service_name,
            resource_json_definitions=json_resource_model['resources'],
            service_model=service_model,
            service_waiter_model=None
        )
    )
    return resource_cls

# get some resource models for specs...
Instance = get_boto3_resource_model('ec2', 'Instance')
SecurityGroup = get_boto3_resource_model('ec2', 'SecurityGroup')
ClassicAddress = get_boto3_resource_model('ec2', 'ClassicAddress')
VpcAddress = get_boto3_resource_model('ec2', 'VpcAddress')
NetworkInterface = get_boto3_resource_model('ec2', 'NetworkInterface')


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
            # 500G ST1
            {
                'VolumeId': 'vol-8',
                'Size': 500,
                'VolumeType': 'st1',
                'Iops': None,
            },
            # 1000G SC1
            {
                'VolumeId': 'vol-9',
                'Size': 1000,
                'VolumeType': 'sc1',
                'Iops': None,
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
            {
                'VpcId': 'vpc-1',
                'SubnetId': 'subnet2',
                'AvailabilityZone': 'az3',
            },
            {
                'VpcId': 'vpc-2',
                'SubnetId': 'subnet3',
                'AvailabilityZone': 'az2',
            },
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
                    {
                        'foo': 'bar',
                        'baz': 'blam',
                        'Origin': 'CreateRoute'
                    },
                    {
                        'foo': 'bar',
                        'baz': 'blam',
                        'Origin': 'EnableVgwRoutePropagation'
                    },
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
                    {
                        'foo': 'bar',
                        'baz': 'blam',
                        'Origin': 'CreateRouteTable'
                    },
                ],
            },
            {
                'RouteTableId': 'rt-3',
                'VpcId': 'vpc-2',
                'Routes': [
                    {
                        'foo': 'bar',
                        'baz': 'blam',
                        'Origin': 'EnableVgwRoutePropagation'
                    },
                    {
                        'foo': 'bar',
                        'baz': 'blam',
                        'Origin': 'CreateRoute'
                    },
                    {
                        'foo': 'bar',
                        'baz': 'blam',
                        'Origin': 'CreateRoute'
                    },
                    {
                        'foo': 'bar',
                        'baz': 'blam',
                        'Origin': 'EnableVgwRoutePropagation'
                    },
                    {
                        'foo': 'bar',
                        'baz': 'blam',
                        'Origin': 'CreateRouteTable'
                    },
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

    test_find_usage_nat_gateways = {
        'NatGateways': [
            {
                'VpcId': 'vpc-123',
                'SubnetId': 'subnet2',
                'NatGatewayId': 'nat-121',
                'CreateTime': datetime(1970, 1, 1),
                'State': 'available',
            },
            {
                'VpcId': 'vpc-123',
                'SubnetId': 'subnet3',
                'NatGatewayId': 'nat-122',
                'CreateTime': datetime(1970, 1, 1),
                'State': 'available',
            },
            {
                'VpcId': 'vpc-123',
                'SubnetId': 'subnet3',
                'NatGatewayId': 'nat-123',
                'CreateTime': datetime(1970, 1, 1),
                'State': 'available',
            },
            {
                'VpcId': 'vpc-123',
                'SubnetId': 'subnet4',
                'NatGatewayId': 'nat-124',
                'CreateTime': datetime(1970, 1, 1),
                'State': 'available',
            },
            {
                'VpcId': 'vpc-123',
                'SubnetId': 'subnet2',
                'NatGatewayId': 'nat-125',
                'CreateTime': datetime(1970, 1, 1),
                'State': 'deleted',
            },
            {
                'VpcId': 'vpc-123',
                'SubnetId': 'subnet3',
                'NatGatewayId': 'nat-126',
                'CreateTime': datetime(1970, 1, 1),
                'State': 'pending',
            },
            {
                'VpcId': 'vpc-123',
                'SubnetId': 'subnet3',
                'NatGatewayId': 'nat-127',
                'CreateTime': datetime(1970, 1, 1),
                'State': 'failed',
            }
        ],
        'NextToken': None,
    }

    test_find_usage_nat_gateways_subnets = {
        'string': 'az2',
        'subnet2': 'az3',
        'subnet3': 'az2'
    }

    test_find_usages_vpn_gateways = {
        'VpnGateways': [
            {
                'AvailabilityZone': 'string',
                'State': 'pending',
                'Type': 'ipsec.1',
                'VpcAttachments': [
                    {
                        'State': 'attaching',
                        'VpcId': 'string'
                    },
                ],
                'VpnGatewayId': 'string',
                'Tags': [
                    {
                        'Key': 'string',
                        'Value': 'string'
                    },
                ]
            },
            {'VpnGatewayId': 'string1'}
        ]
    }


class RDS(object):
    test_find_usage_instances = []
    # first result page
    test_find_usage_instances.append({
        'DBInstances': [
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
        ],
        'NextToken': 'string'
    })
    # second result page
    test_find_usage_instances.append({
        'DBInstances': [
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
    })

    test_find_usage_subnet_groups = []
    test_find_usage_subnet_groups.append({
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
        ],
        'NextToken': 'string'
    })
    test_find_usage_subnet_groups.append({
        'DBSubnetGroups': [
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
    })

    test_find_usage_security_groups = []
    test_find_usage_security_groups.append({
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
                "DBSecurityGroupDescription": "empty",
                "DBSecurityGroupName":
                    "MyEmptySecurityGroup",
                "EC2SecurityGroups": [],
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
        ],
        'NextToken': 'string'
    })
    test_find_usage_security_groups.append({
        'DBSecurityGroups': [
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
    })

    test_update_limits_from_api = {
        'AccountQuotas': [
            {
                'Max': 200,
                'AccountQuotaName': 'DBInstances',
                'Used': 124
            },
            {
                'Max': 201,
                'AccountQuotaName': 'ReservedDBInstances',
                'Used': 96},
            {
                'Max': 100000,
                'AccountQuotaName': 'AllocatedStorage',
                'Used': 8320
            },
            {
                'Max': 25,
                'AccountQuotaName': 'DBSecurityGroups',
                'Used': 15
            },
            {
                'Max': 20,
                'AccountQuotaName': 'AuthorizationsPerDBSecurityGroup',
                'Used': 5
            },
            {
                'Max': 50,
                'AccountQuotaName': 'DBParameterGroups',
                'Used': 39
            },
            {
                'Max': 150,
                'AccountQuotaName': 'ManualSnapshots',
                'Used': 76
            },
            {
                'Max': 21,
                'AccountQuotaName': 'EventSubscriptions',
                'Used': 1
            },
            {
                'Max': 202,
                'AccountQuotaName': 'DBSubnetGroups',
                'Used': 89
            },
            {
                'Max': 22,
                'AccountQuotaName': 'OptionGroups',
                'Used': 2
            },
            {
                'Max': 23,
                'AccountQuotaName': 'SubnetsPerDBSubnetGroup',
                'Used': 14
            },
            {
                'Max': 5,
                'AccountQuotaName': 'ReadReplicasPerMaster',
                'Used': 4
            },
            {
                'Max': 40,
                'AccountQuotaName': 'DBClusters',
                'Used': 3
            },
            {
                'Max': 51,
                'AccountQuotaName': 'DBClusterParameterGroups',
                'Used': 6
            },
            {
                'Max': 98,
                'AccountQuotaName': 'Foo',
                'Used': 99
            }
        ],
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': '95729212-e5ab-11e5-8250-91a417accabb'
        }
    }


class ElasticBeanstalk(object):

    test_find_usage_applications = {
        'Applications': [
            {
                'ApplicationName': 'application-1',
                'Description': 'description-1',
                'DateCreated': datetime(2015, 1, 1),
                'DateUpdated': datetime(2015, 1, 1),
                'Versions': [
                    'version-1',
                    'version-2'
                ],
                'ConfigurationTemplates': [
                     'config-1',
                     'config-2'
                ]
            },
            {
                'ApplicationName': 'application-2',
                'Description': 'description-2',
                'DateCreated': datetime(2015, 1, 2),
                'DateUpdated': datetime(2015, 1, 2),
                'Versions': [
                    'version-1',
                    'version-2'
                ],
                'ConfigurationTemplates': [
                     'config-1',
                     'config-2'
                ]
            }
        ]
    }

    test_find_usage_application_versions = {
        'ApplicationVersions': [
            {
                'ApplicationName': 'application-1',
                'Description': 'description-1',
                'DateCreated': datetime(2015, 1, 1),
                'DateUpdated': datetime(2015, 1, 1),
                'SourceBundle': {
                    'S3Bucket': 's3-bucket',
                    'S3Key': 's3-key'
                },
                'VersionLabel': 'version-2'
            },
            {
                'ApplicationName': 'application-1',
                'Description': 'description-1',
                'DateCreated': datetime(2015, 1, 1),
                'DateUpdated': datetime(2015, 1, 1),
                'SourceBundle': {
                    'S3Bucket': 's3-bucket',
                    'S3Key': 's3-key'
                },
                'VersionLabel': 'version-1'
            },
            {
                'ApplicationName': 'application-2',
                'Description': 'description-1',
                'DateCreated': datetime(2015, 1, 2),
                'DateUpdated': datetime(2015, 1, 2),
                'SourceBundle': {
                    'S3Bucket': 's3-bucket',
                    'S3Key': 's3-key'
                },
                'VersionLabel': 'version-2'
            },
            {
                'ApplicationName': 'application-2',
                'Description': 'description-1',
                'DateCreated': datetime(2015, 1, 2),
                'DateUpdated': datetime(2015, 1, 2),
                'SourceBundle': {
                    'S3Bucket': 's3-bucket',
                    'S3Key': 's3-key'
                },
                'VersionLabel': 'version-1'
            }
        ]
    }

    test_find_usage_environments = {
        'Environments': [
            {
                'EnvironmentName': 'application-environment-1',
                'EnvironmentId': 'environment-id-1',
                'ApplicationName': 'application-1',
                'VersionLabel': 'version-2',
                'SolutionStackName': 'solution-stack',
                'TemplateName': 'template-name',
                'Description': 'description-1',
                'EndpointURL': 'application-1.region.elasticbeanstalk.com',
                'CNAME': 'application-1.elasticbeanstalk.com',
                'DateCreated': datetime(2015, 1, 1),
                'DateUpdated': datetime(2015, 1, 1),
                'Status': 'Ready',
                'AbortableOperationInProgress': False,
                'Health': 'Green',
                'HealthStatus': 'Ok',
                'Resources': {
                    'LoadBalancer': {
                        'LoadBalancerName': 'load-balancer-1',
                        'Domain': 'domain',
                        'Listeners': [
                            {
                                'Protocol': 'http',
                                'Port': 80
                            }
                        ]
                    }
                },
                'Tier': {
                    'Name': 'tier-1',
                    'Type': 'tier-type',
                    'Version': 'tier-version'
                },
                'EnvironmentLinks': [
                    {
                        'LinkName': 'link-name',
                        'EnvironmentName': 'environment-name'
                    }
                ]
            },
            {
                'EnvironmentName': 'application-environment-2',
                'EnvironmentId': 'environment-id-2',
                'ApplicationName': 'application-2',
                'VersionLabel': 'version-2',
                'SolutionStackName': 'solution-stack',
                'TemplateName': 'template-name',
                'Description': 'description-2',
                'EndpointURL': 'application-2.region.elasticbeanstalk.com',
                'CNAME': 'application-2.elasticbeanstalk.com',
                'DateCreated': datetime(2015, 1, 2),
                'DateUpdated': datetime(2015, 1, 2),
                'Status': 'Ready',
                'AbortableOperationInProgress': False,
                'Health': 'Green',
                'HealthStatus': 'Ok',
                'Resources': {
                    'LoadBalancer': {
                        'LoadBalancerName': 'load-balancer-2',
                        'Domain': 'domain',
                        'Listeners': [
                            {
                                'Protocol': 'http',
                                'Port': 80
                            }
                        ]
                    }
                },
                'Tier': {
                    'Name': 'tier-2',
                    'Type': 'tier-type',
                    'Version': 'tier-version'
                },
                'EnvironmentLinks': [
                    {
                        'LinkName': 'link-name',
                        'EnvironmentName': 'environment-name'
                    }
                ]
            }
        ]
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

    test_update_limits_elb = {
        'ResponseMetadata': {
            'RetryAttempts': 0,
            'HTTPStatusCode': 200,
            'RequestId': 'aaaa',
            'HTTPHeaders': {
                'x-amzn-requestid': 'ccccccc',
                'date': 'Sun, 06 Aug 2017 12:00:40 GMT',
                'content-length': '520',
                'content-type': 'text/xml'
            }
        },
        'Limits': [
            {'Max': '3', 'Name': 'classic-load-balancers'},
            {'Max': '5', 'Name': 'classic-listeners'},
            {'Name': 'invalid', 'Max': '99'},  # test invalid name
            {'Name': 'classic-listeners'}  # test no Max
        ]
    }

    test_update_limits_alb = {
        'ResponseMetadata': {
            'RetryAttempts': 0,
            'HTTPStatusCode': 200,
            'RequestId': 'bbb',
            'HTTPHeaders': {
                'x-amzn-requestid': 'dddddd',
                'date': 'Sun, 06 Aug 2017 12:19:40 GMT',
                'content-length': '860',
                'content-type': 'text/xml'
            }
        },
        'Limits': [
            {'Max': '6', 'Name': 'application-load-balancers'},
            {'Max': '7', 'Name': 'target-groups'},
            {'Max': '8', 'Name': 'targets-per-application-load-balancer'},
            {'Max': '9', 'Name': 'listeners-per-application-load-balancer'},
            {'Max': '10', 'Name': 'rules-per-application-load-balancer'},
            {'Name': 'invalid', 'Max': '99'},  # test invalid name
            {'Name': 'target-groups'}  # test no Max
        ]
    }

    test_find_usage_elbv2_elbs = {
        'LoadBalancers': [
            {
                'LoadBalancerName': 'lb1',
                'LoadBalancerArn': 'lb-arn1'
            },
            {
                'LoadBalancerName': 'lb2',
                'LoadBalancerArn': 'lb-arn2'
            }
        ]
    }

    test_find_usage_elbv2_target_groups = {
        'TargetGroups': [
            {
                'TargetGroupArn': 'arn1',
                'TargetGroupName': 'name1'
            },
            {
                'TargetGroupArn': 'arn2',
                'TargetGroupName': 'name2'
            },
            {
                'TargetGroupArn': 'arn3',
                'TargetGroupName': 'name3'
            }
        ]
    }

    test_usage_elbv2_listeners = {
        'Listeners': [
            {'ListenerArn': 'listener1'},
            {'ListenerArn': 'listener2'},
            {'ListenerArn': 'listener3'},
        ]
    }

    test_usage_elbv2_rules = [
        {
            'Rules': [
                {'RuleArn': 'listener1rule1'},
                {'RuleArn': 'listener1rule2'}
            ]
        },
        {
            'Rules': [
                {'RuleArn': 'listener2rule1'}
            ]
        },
        {
            'Rules': [
                {'RuleArn': 'listener3rule1'},
                {'RuleArn': 'listener3rule2'},
                {'RuleArn': 'listener3rule3'},
                {'RuleArn': 'listener3rule4'}
            ]
        }
    ]


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
            {
                'Engine': 'redis',
                'CacheParameterGroup': {
                    'CacheNodeIdsToReboot': [],
                    'CacheParameterGroupName': 'default.redis2.8',
                    'ParameterApplyStatus': 'in-sync'
                },
                'CacheClusterId': 'redis3',
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
                'PreferredMaintenanceWindow': 'mon:05:30-mon:06:30'
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

    @property
    def test_instance_usage(self):
        mock_inst1A = Mock(spec_set=Instance)
        type(mock_inst1A).id = '1A'
        type(mock_inst1A).instance_type = 't2.micro'
        type(mock_inst1A).spot_instance_request_id = None
        type(mock_inst1A).placement = {'AvailabilityZone': 'az1a'}
        type(mock_inst1A).state = {'Code': 16, 'Name': 'running'}

        mock_inst1B = Mock(spec_set=Instance)
        type(mock_inst1B).id = '1B'
        type(mock_inst1B).instance_type = 'r3.2xlarge'
        type(mock_inst1B).spot_instance_request_id = None
        type(mock_inst1B).placement = {'AvailabilityZone': 'az1a'}
        type(mock_inst1B).state = {'Code': 0, 'Name': 'pending'}

        mock_inst2A = Mock(spec_set=Instance)
        type(mock_inst2A).id = '2A'
        type(mock_inst2A).instance_type = 'c4.4xlarge'
        type(mock_inst2A).spot_instance_request_id = None
        type(mock_inst2A).placement = {'AvailabilityZone': 'az1a'}
        type(mock_inst2A).state = {'Code': 32, 'Name': 'shutting-down'}

        mock_inst2B = Mock(spec_set=Instance)
        type(mock_inst2B).id = '2B'
        type(mock_inst2B).instance_type = 't2.micro'
        type(mock_inst2B).spot_instance_request_id = '1234'
        type(mock_inst2B).placement = {'AvailabilityZone': 'az1a'}
        type(mock_inst2B).state = {'Code': 64, 'Name': 'stopping'}

        mock_inst2C = Mock(spec_set=Instance)
        type(mock_inst2C).id = '2C'
        type(mock_inst2C).instance_type = 'm4.8xlarge'
        type(mock_inst2C).spot_instance_request_id = None
        type(mock_inst2C).placement = {'AvailabilityZone': 'az1a'}
        type(mock_inst2C).state = {'Code': 16, 'Name': 'running'}

        mock_instStopped = Mock(spec_set=Instance)
        type(mock_instStopped).id = '2C'
        type(mock_instStopped).instance_type = 'm4.8xlarge'
        type(mock_instStopped).spot_instance_request_id = None
        type(mock_instStopped).placement = {'AvailabilityZone': 'az1a'}
        type(mock_instStopped).state = {'Code': 80, 'Name': 'stopped'}

        mock_instTerm = Mock(spec_set=Instance)
        type(mock_instTerm).id = '2C'
        type(mock_instTerm).instance_type = 'm4.8xlarge'
        type(mock_instTerm).spot_instance_request_id = None
        type(mock_instTerm).placement = {'AvailabilityZone': 'az1a'}
        type(mock_instTerm).state = {'Code': 48, 'Name': 'terminated'}

        return_value = [
            mock_inst1A,
            mock_inst1B,
            mock_inst2A,
            mock_inst2B,
            mock_inst2C,
            mock_instStopped,
            mock_instTerm
        ]
        return return_value

    @property
    def test_instance_usage_key_error(self):
        mock_inst1A = Mock(spec_set=Instance)
        type(mock_inst1A).id = '1A'
        type(mock_inst1A).instance_type = 'foobar'
        type(mock_inst1A).spot_instance_request_id = None
        type(mock_inst1A).placement = {'AvailabilityZone': 'az1a'}
        type(mock_inst1A).state = {'Code': 16, 'Name': 'running'}
        return [mock_inst1A]

    @property
    def test_find_usage_networking_sgs(self):
        mock_sg1 = Mock(spec_set=SecurityGroup)
        type(mock_sg1).id = 'sg-1'
        type(mock_sg1).vpc_id = 'vpc-aaa'
        type(mock_sg1).ip_permissions = []
        type(mock_sg1).ip_permissions_egress = []
        mock_sg2 = Mock(spec_set=SecurityGroup)
        type(mock_sg2).id = 'sg-2'
        type(mock_sg2).vpc_id = None
        type(mock_sg2).ip_permissions = [1, 2, 3, 4, 5, 6]
        type(mock_sg2).ip_permissions_egress = [8, 9, 10]
        mock_sg3 = Mock(spec_set=SecurityGroup)
        type(mock_sg3).id = 'sg-3'
        type(mock_sg3).vpc_id = 'vpc-bbb'
        type(mock_sg3).ip_permissions = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        type(mock_sg3).ip_permissions_egress = [6, 7, 8, 9]
        mock_sg4 = Mock(spec_set=SecurityGroup)
        type(mock_sg4).id = 'sg-4'
        type(mock_sg4).vpc_id = 'vpc-aaa'
        type(mock_sg4).ip_permissions = [1, 2, 3]
        type(mock_sg4).ip_permissions_egress = [21, 22, 23, 24]

        return_value = [
            mock_sg1,
            mock_sg2,
            mock_sg3,
            mock_sg4,
        ]
        return return_value

    test_get_reserved_instance_count = {
        'ReservedInstances': [
            {
                'ReservedInstancesId': 'res1',
                'InstanceType': 'it1',
                'AvailabilityZone': 'az1',
                'Start': datetime(2015, 1, 1),
                'End': datetime(2015, 1, 1),
                'Duration': 123,
                'UsagePrice': 12,
                'FixedPrice': 14,
                'InstanceCount': 1,
                'ProductDescription': 'Linux/UNIX',
                'State': 'active',
                'Tags': [
                    {
                        'Key': 'tagKey',
                        'Value': 'tagVal'
                    },
                ],
                'InstanceTenancy': 'default',
                'CurrencyCode': 'USD',
                'OfferingType': 'Heavy Utilization',
                'RecurringCharges': [
                    {
                        'Frequency': 'Hourly',
                        'Amount': 123.0
                    },
                ]
            },
            {
                'ReservedInstancesId': 'res2',
                'InstanceType': 'it2',
                'AvailabilityZone': 'az1',
                'InstanceCount': 1,
                'State': 'retired',
            },
            {
                'ReservedInstancesId': 'res3',
                'InstanceType': 'it1',
                'AvailabilityZone': 'az1',
                'InstanceCount': 9,
                'State': 'active',
            },
            {
                'ReservedInstancesId': 'res4',
                'InstanceType': 'it2',
                'AvailabilityZone': 'az2',
                'InstanceCount': 98,
                'State': 'active',
            },
            {
                'ReservedInstancesId': 'res5',
                'InstanceType': 'it2',
                'InstanceCount': 9,
                'State': 'active',
            },
            {
                'ReservedInstancesId': 'res6',
                'InstanceType': 'it3',
                'InstanceCount': 6,
                'State': 'active',
            },
        ]
    }

    @property
    def test_find_usage_networking_eips(self):
        mock_addr1 = Mock(spec_set=VpcAddress)
        type(mock_addr1).domain = 'vpc'
        mock_addr2 = Mock(spec_set=VpcAddress)
        type(mock_addr2).domain = 'vpc'
        mock_addr3 = Mock(spec_set=ClassicAddress)
        type(mock_addr3).domain = 'standard'
        return {
            'Classic': [mock_addr3],
            'Vpc': [mock_addr1, mock_addr2]
        }

    @property
    def test_find_usage_networking_eni_sg(self):
        mock_if1 = Mock(spec_set=NetworkInterface)
        type(mock_if1).id = 'if-1'
        type(mock_if1).groups = []
        type(mock_if1).vpc = Mock()

        mock_if2 = Mock(spec_set=NetworkInterface)
        type(mock_if2).id = 'if-2'
        type(mock_if2).groups = [1, 2, 3]
        type(mock_if2).vpc = Mock()

        mock_if3 = Mock(spec_set=NetworkInterface)
        type(mock_if3).id = 'if-3'
        type(mock_if3).groups = [1, 2, 3, 4, 5, 6, 7, 8]
        type(mock_if3).vpc = Mock()

        mock_if4 = Mock(spec_set=NetworkInterface)
        type(mock_if4).id = 'if-4'
        type(mock_if4).groups = [1, 2, 3, 4, 5, 6, 7, 8]
        type(mock_if4).vpc = None
        return [mock_if1, mock_if2, mock_if3, mock_if4]

    test_update_limits_from_api = {
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': '16b85906-ab0d-4134-b8bb-df3e6120c6c7'
        },
        'AccountAttributes': [
            {
                'AttributeName': 'supported-platforms',
                'AttributeValues': [
                    {
                        'AttributeValue': 'EC2'
                    },
                    {
                        'AttributeValue': 'VPC'
                    }
                ]
            },
            {
                'AttributeName': 'vpc-max-security-groups-per-interface',
                'AttributeValues': [
                    {
                        'AttributeValue': '5'
                    }
                ]
            },
            {
                'AttributeName': 'max-elastic-ips',
                'AttributeValues': [
                    {
                        'AttributeValue': '40'
                    }
                ]
            },
            {
                'AttributeName': 'max-instances',
                'AttributeValues': [
                    {
                        'AttributeValue': '400'
                    }
                ]
            },
            {
                'AttributeName': 'vpc-max-elastic-ips',
                'AttributeValues': [
                    {
                        'AttributeValue': '200'
                    }
                ]
            },
            {
                'AttributeName': 'default-vpc',
                'AttributeValues': [
                    {
                        'AttributeValue': 'none'
                    }
                ]
            }
        ]
    }

    test_update_limits_from_api_unsupported = {
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': '16b85906-ab0d-4134-b8bb-df3e6120c6c7'
        },
        'AccountAttributes': [
            {
                'AttributeName': 'supported-platforms',
                'AttributeValues': [
                    {
                        'AttributeValue': 'EC2'
                    },
                    {
                        'AttributeValue': 'VPC'
                    }
                ]
            },
            {
                'AttributeName': 'max-elastic-ips',
                'AttributeValues': [
                    {
                        'AttributeValue': '0'
                    }
                ]
            },
        ]
    }

    test_find_usage_spot_instances = {
        'SpotInstanceRequests': [
            {
                'SpotInstanceRequestId': 'reqID1',
                'SpotPrice': 'string',
                'Type': 'one-time',
                'State': 'closed',
                'Fault': {
                    'Code': 'string',
                    'Message': 'string'
                },
                'Status': {
                    'Code': 'string',
                    'UpdateTime': datetime(2015, 1, 1),
                    'Message': 'string'
                },
                'ValidFrom': datetime(2015, 1, 1),
                'ValidUntil': datetime(2015, 1, 1),
                'LaunchGroup': 'string',
                'AvailabilityZoneGroup': 'string',
                'LaunchSpecification': {
                    'ImageId': 'string',
                    'KeyName': 'string',
                    'SecurityGroups': [
                        {
                            'GroupName': 'string',
                            'GroupId': 'string'
                        },
                    ],
                    'UserData': 'string',
                    'AddressingType': 'string',
                    'InstanceType': 't1.micro',
                    'Placement': {
                        'AvailabilityZone': 'string',
                        'GroupName': 'string'
                    },
                    'KernelId': 'string',
                    'RamdiskId': 'string',
                    'BlockDeviceMappings': [
                        {
                            'VirtualName': 'string',
                            'DeviceName': 'string',
                            'Ebs': {
                                'SnapshotId': 'string',
                                'VolumeSize': 123,
                                'DeleteOnTermination': True,
                                'VolumeType': 'standard',
                                'Iops': 123,
                                'Encrypted': True
                            },
                            'NoDevice': 'string'
                        },
                    ],
                    'SubnetId': 'string',
                    'NetworkInterfaces': [
                        {
                            'NetworkInterfaceId': 'string',
                            'DeviceIndex': 123,
                            'SubnetId': 'string',
                            'Description': 'string',
                            'PrivateIpAddress': 'string',
                            'Groups': [
                                'string',
                            ],
                            'DeleteOnTermination': True,
                            'PrivateIpAddresses': [
                                {
                                    'PrivateIpAddress': 'string',
                                    'Primary': True
                                },
                            ],
                            'SecondaryPrivateIpAddressCount': 123,
                            'AssociatePublicIpAddress': True
                        },
                    ],
                    'IamInstanceProfile': {
                        'Arn': 'string',
                        'Name': 'string'
                    },
                    'EbsOptimized': True,
                    'Monitoring': {
                        'Enabled': True
                    }
                },
                'InstanceId': 'string',
                'CreateTime': datetime(2015, 1, 1),
                'ProductDescription': 'Linux/UNIX (Amazon VPC)',
                'BlockDurationMinutes': 123,
                'ActualBlockHourlyPrice': 'string',
                'Tags': [
                    {
                        'Key': 'string',
                        'Value': 'string'
                    },
                ],
                'LaunchedAvailabilityZone': 'string'
            },
            {
                'SpotInstanceRequestId': 'reqID2',
                'Type': 'persistent',
                'State': 'active',
            },
            {
                'SpotInstanceRequestId': 'reqID3',
                'Type': 'persistent',
                'State': 'open',
            },
            {
                'SpotInstanceRequestId': 'reqID4',
                'Type': 'persistent',
                'State': 'failed',
            },
        ]
    }

    test_find_usage_spot_fleets = {
        'SpotFleetRequestConfigs': [
            {
                'SpotFleetRequestId': 'req1',
                'SpotFleetRequestState': 'failed',
                'SpotFleetRequestConfig': {
                    'ClientToken': 'string',
                    'SpotPrice': 'string',
                    'TargetCapacity': 456,
                    'ValidFrom': datetime(2015, 1, 1),
                    'ValidUntil': datetime(2015, 1, 1),
                    'TerminateInstancesWithExpiration': True,
                    'IamFleetRole': 'string',
                    'LaunchSpecifications': [
                        {
                            'ImageId': 'string',
                            'KeyName': 'string',
                            'SecurityGroups': [
                                {
                                    'GroupName': 'string',
                                    'GroupId': 'string'
                                },
                            ],
                            'UserData': 'string',
                            'AddressingType': 'string',
                            'InstanceType': 't1.micro',
                            'Placement': {
                                'AvailabilityZone': 'string',
                                'GroupName': 'string'
                            },
                            'KernelId': 'string',
                            'RamdiskId': 'string',
                            'BlockDeviceMappings': [
                                {
                                    'VirtualName': 'string',
                                    'DeviceName': 'string',
                                    'Ebs': {
                                        'SnapshotId': 'string',
                                        'VolumeSize': 123,
                                        'DeleteOnTermination': True,
                                        'VolumeType': 'standard',
                                        'Iops': 123,
                                        'Encrypted': True
                                    },
                                    'NoDevice': 'string'
                                },
                            ],
                            'Monitoring': {
                                'Enabled': True
                            },
                            'SubnetId': 'string',
                            'NetworkInterfaces': [
                                {
                                    'NetworkInterfaceId': 'string',
                                    'DeviceIndex': 123,
                                    'SubnetId': 'string',
                                    'Description': 'string',
                                    'PrivateIpAddress': 'string',
                                    'Groups': [
                                        'string',
                                    ],
                                    'DeleteOnTermination': True,
                                    'PrivateIpAddresses': [
                                        {
                                            'PrivateIpAddress': 'string',
                                            'Primary': True
                                        },
                                    ],
                                    'SecondaryPrivateIpAddressCount': 123,
                                    'AssociatePublicIpAddress': True
                                },
                            ],
                            'IamInstanceProfile': {
                                'Arn': 'string',
                                'Name': 'string'
                            },
                            'EbsOptimized': True,
                            'WeightedCapacity': 123.0,
                            'SpotPrice': 'string'
                        },
                    ],
                    'ExcessCapacityTerminationPolicy': 'default',
                    'AllocationStrategy': 'lowestPrice',
                    'FulfilledCapacity': 123.0,
                    'Type': 'request'
                },
                'CreateTime': datetime(2015, 1, 1)
            },
            {
                'SpotFleetRequestId': 'req2',
                'SpotFleetRequestState': 'active',
                'SpotFleetRequestConfig': {
                    'TargetCapacity': 11,
                    'LaunchSpecifications': [
                        {
                            'ImageId': 'string',
                        },
                        {
                            'ImageId': 'string',
                        },
                        {
                            'ImageId': 'string',
                        },
                    ],
                    'Type': 'request'
                },
            },
            {
                'SpotFleetRequestId': 'req3',
                'SpotFleetRequestState': 'modifying',
                'SpotFleetRequestConfig': {
                    'TargetCapacity': 22,
                    'LaunchSpecifications': [
                        {
                            'ImageId': 'string',
                        },
                        {
                            'ImageId': 'string',
                        },
                        {
                            'ImageId': 'string',
                        },
                        {
                            'ImageId': 'string',
                        },
                    ],
                    'Type': 'request'
                },
            },
            {
                'SpotFleetRequestId': 'req4',
                'SpotFleetRequestState': 'active',
                'SpotFleetRequestConfig': {
                    'TargetCapacity': 33,
                    'LaunchSpecifications': [
                        {
                            'ImageId': 'string',
                        },
                    ],
                    'Type': 'request'
                },
            },
        ]
    }


class IAM(object):

    test_update_limits_from_api = {
        'AccessKeysPerUserQuota': 2,
        'AccountAccessKeysPresent': 1,
        'AccountMFAEnabled': 0,
        'AccountSigningCertificatesPresent': 3,
        'AssumeRolePolicySizeQuota': 2048,
        'AttachedPoliciesPerGroupQuota': 11,
        'AttachedPoliciesPerRoleQuota': 12,
        'AttachedPoliciesPerUserQuota': 13,
        'GroupPolicySizeQuota': 5120,
        'Groups': 25,
        'GroupsPerUserQuota': 14,
        'GroupsQuota': 100,
        'InstanceProfiles': 394,
        'InstanceProfilesQuota': 500,
        'MFADevices': 4,
        'MFADevicesInUse': 5,
        'Policies': 17,
        'PoliciesQuota': 1000,
        'PolicySizeQuota': 5120,
        'PolicyVersionsInUse': 53,
        'PolicyVersionsInUseQuota': 10000,
        'Providers': 6,
        'RolePolicySizeQuota': 10240,
        'Roles': 375,
        'RolesQuota': 501,
        'ServerCertificates': 55,
        'ServerCertificatesQuota': 101,
        'SigningCertificatesPerUserQuota': 7,
        'UserPolicySizeQuota': 2048,
        'Users': 152,
        'UsersQuota': 5000,
        'VersionsPerPolicyQuota': 8
    }


class Firehose(object):

    test_list_delivery_streams = [
        {
            'DeliveryStreamNames': [
                'first-page-stream1',
                'first-page-stream2',
                'first-page-stream3',
                'first-page-stream4',
                'first-page-stream5',
                'first-page-stream6',
                'first-page-stream7',
                'first-page-stream8',
                'first-page-stream9',
                'first-page-stream10',
            ],
            'HasMoreDeliveryStreams': True,
            'ResponseMetadata': {
                'HTTPStatusCode': 200,
                'RequestId': '1aaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
            }
        },
        {
            'DeliveryStreamNames': [
                'second-page-stream11',
            ],
            'HasMoreDeliveryStreams': False,
            'ResponseMetadata': {
                'HTTPStatusCode': 200,
                'RequestId': '2aaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
            }
        }
    ]


class Redshift(object):

    test_describe_cluster_snapshots = {
        'Snapshots': [
            {
                "EstimatedSecondsToCompletion": 0,
                "OwnerAccount": "123456789",
                "CurrentBackupRateInMegaBytesPerSecond": 1.0,
                "ActualIncrementalBackupSizeInMegaBytes": 1.0,
                "NumberOfNodes": 1,
                "Status": "available",
                "VpcId": "vpc-123456",
                "ClusterVersion": "1.0",
                "Tags": [],
                "MasterUsername": "username",
                "TotalBackupSizeInMegaBytes": 10.0,
                "DBName": "test",
                "BackupProgressInMegaBytes": 4.0,
                "ClusterCreateTime": "2017-01-01T00:00:00.000Z",
                "RestorableNodeTypes": [
                    "dc1.large"
                ],
                "EncryptedWithHSM": False,
                "ClusterIdentifier": "test12346",
                "SnapshotCreateTime": "2017-01-04T00:00:00.000Z",
                "AvailabilityZone": "us-east-1e",
                "NodeType": "dc1.large",
                "Encrypted": False,
                "ElapsedTimeInSeconds": 0,
                "SnapshotType": "manual",
                "Port": 1234,
                "SnapshotIdentifier": "snapshot1"
            },
            {
                "EstimatedSecondsToCompletion": 0,
                "OwnerAccount": "123456789",
                "CurrentBackupRateInMegaBytesPerSecond": 1.0,
                "ActualIncrementalBackupSizeInMegaBytes": 1.0,
                "NumberOfNodes": 1,
                "Status": "available",
                "VpcId": "vpc-123456",
                "ClusterVersion": "1.0",
                "Tags": [],
                "MasterUsername": "username",
                "TotalBackupSizeInMegaBytes": 10.0,
                "DBName": "test",
                "BackupProgressInMegaBytes": 4.0,
                "ClusterCreateTime": "2017-01-01T00:00:00.000Z",
                "RestorableNodeTypes": [
                    "dc1.large"
                ],
                "EncryptedWithHSM": False,
                "ClusterIdentifier": "test12346",
                "SnapshotCreateTime": "2017-01-04T00:00:00.000Z",
                "AvailabilityZone": "us-east-1e",
                "NodeType": "dc1.large",
                "Encrypted": False,
                "ElapsedTimeInSeconds": 0,
                "SnapshotType": "manual",
                "Port": 1234,
                "SnapshotIdentifier": "snapshot2"
            }
        ]
    }

    test_describe_cluster_subnet_groups = {
        "ClusterSubnetGroups": [
            {
                "Subnets": [
                    {
                        "SubnetStatus": "Active",
                        "SubnetIdentifier": "subnet-1",
                        "SubnetAvailabilityZone": {
                            "Name": "region-name"
                        }
                    },
                    {
                        "SubnetStatus": "Active",
                        "SubnetIdentifier": "subnet-2",
                        "SubnetAvailabilityZone": {
                            "Name": "alt-region-name"
                        }
                    }
                ],
                "VpcId": "vpc-1",
                "Description": "Redshift Subnet Group for Test1",
                "Tags": [],
                "SubnetGroupStatus": "Complete",
                "ClusterSubnetGroupName": "groupname1"
            },
            {
                "Subnets": [
                    {
                        "SubnetStatus": "Active",
                        "SubnetIdentifier": "subnet-3",
                        "SubnetAvailabilityZone": {
                            "Name": "alt-region-name"
                        }
                    },
                    {
                        "SubnetStatus": "Active",
                        "SubnetIdentifier": "subnet-4",
                        "SubnetAvailabilityZone": {
                            "Name": "region-name"
                        }
                    }
                ],
                "VpcId": "vpc-2",
                "Description": "Redshift Subnet Group for Test2",
                "Tags": [],
                "SubnetGroupStatus": "Complete",
                "ClusterSubnetGroupName": "groupname2"
            },
            {
                "Subnets": [
                    {
                        "SubnetStatus": "Active",
                        "SubnetIdentifier": "subnet-5",
                        "SubnetAvailabilityZone": {
                            "Name": "alt-region-name"
                        }
                    },
                    {
                        "SubnetStatus": "Active",
                        "SubnetIdentifier": "subnet-6",
                        "SubnetAvailabilityZone": {
                            "Name": "region-name"
                        }
                    }
                ],
                "VpcId": "vpc-3",
                "Description": "Redshift Subnet Group for Test3",
                "Tags": [],
                "SubnetGroupStatus": "Complete",
                "ClusterSubnetGroupName": "groupname3"
            }
        ]
    }


class ApiGateway(object):

    get_rest_apis = [
        {
            'items': [
                {
                    'id': 'api3',
                    'name': 'api3name',
                    'description': 'api3desc',
                    'createdDate': datetime(2015, 1, 1),
                    'version': 'api3ver',
                    'warnings': [
                        'string',
                    ],
                    'binaryMediaTypes': [
                        'string',
                    ]
                },
                {
                    'id': 'api2',
                    'name': 'api2name',
                    'description': 'api2desc',
                    'createdDate': datetime(2016, 1, 1),
                    'version': 'api2ver',
                    'warnings': [],
                    'binaryMediaTypes': []
                }
            ],
            'NextToken': 'string'
        },
        {
            'items': [
                {
                    'id': 'api1',
                    'name': 'api1name',
                    'description': 'api1desc',
                    'createdDate': datetime(2017, 1, 1),
                    'version': 'api1ver',
                    'warnings': [
                        'string',
                    ],
                    'binaryMediaTypes': [
                        'string',
                    ]
                },
            ]
        }
    ]

    resources_api1 = [
        {
            'items': [
                {
                    'id': 'api1res1',
                    'parentId': 'string',
                    'pathPart': 'string',
                    'path': 'string',
                    'resourceMethods': {
                        'string': {
                            'httpMethod': 'string',
                            'authorizationType': 'string',
                            'authorizerId': 'string',
                            'apiKeyRequired': False,
                            'requestValidatorId': 'string',
                            'operationName': 'string',
                            'requestParameters': {
                                'string': False
                            },
                            'requestModels': {
                                'string': 'string'
                            },
                            'methodResponses': {
                                'string': {
                                    'statusCode': 'string',
                                    'responseParameters': {
                                        'string': True
                                    },
                                    'responseModels': {
                                        'string': 'string'
                                    }
                                }
                            },
                            'methodIntegration': {
                                'type': 'HTTP',
                                'httpMethod': 'string',
                                'uri': 'string',
                                'credentials': 'string',
                                'requestParameters': {
                                    'string': 'string'
                                },
                                'requestTemplates': {
                                    'string': 'string'
                                },
                                'passthroughBehavior': 'string',
                                'contentHandling': 'CONVERT_TO_BINARY',
                                'cacheNamespace': 'string',
                                'cacheKeyParameters': [
                                    'string',
                                ],
                                'integrationResponses': {
                                    'string': {
                                        'statusCode': 'string',
                                        'selectionPattern': 'string',
                                        'responseParameters': {
                                            'string': 'string'
                                        },
                                        'responseTemplates': {
                                            'string': 'string'
                                        },
                                        'contentHandling': 'CONVERT_TO_BINARY'
                                    }
                                }
                            }
                        }
                    }
                },
                {
                    'id': 'api1res2',
                    'parentId': 'string',
                    'pathPart': 'string',
                    'path': 'string',
                    'resourceMethods': {
                        'string': {
                            'httpMethod': 'string',
                            'authorizationType': 'string',
                            'authorizerId': 'string',
                            'apiKeyRequired': False,
                            'requestValidatorId': 'string',
                            'operationName': 'string',
                            'requestParameters': {
                                'string': False
                            },
                            'requestModels': {
                                'string': 'string'
                            },
                            'methodResponses': {
                                'string': {
                                    'statusCode': 'string',
                                    'responseParameters': {
                                        'string': True
                                    },
                                    'responseModels': {
                                        'string': 'string'
                                    }
                                }
                            },
                            'methodIntegration': {
                                'type': 'AWS_PROXY',
                                'httpMethod': 'string',
                                'uri': 'string',
                                'credentials': 'string',
                                'requestParameters': {
                                    'string': 'string'
                                },
                                'requestTemplates': {
                                    'string': 'string'
                                },
                                'passthroughBehavior': 'string',
                                'contentHandling': 'CONVERT_TO_TEXT',
                                'cacheNamespace': 'string',
                                'cacheKeyParameters': [
                                    'string',
                                ],
                                'integrationResponses': {
                                    'string': {
                                        'statusCode': 'string',
                                        'selectionPattern': 'string',
                                        'responseParameters': {
                                            'string': 'string'
                                        },
                                        'responseTemplates': {
                                            'string': 'string'
                                        },
                                        'contentHandling': 'CONVERT_TO_TEXT'
                                    }
                                }
                            }
                        }
                    }
                }
            ],
            'NextToken': 'string'
        },
        {
            'items': [
                {
                    'id': 'api1res3',
                    'parentId': 'string',
                    'pathPart': 'string',
                    'path': 'string',
                    'resourceMethods': {
                        'string': {
                            'httpMethod': 'string',
                            'authorizationType': 'string',
                            'authorizerId': 'string',
                            'apiKeyRequired': False,
                            'requestValidatorId': 'string',
                            'operationName': 'string',
                            'requestParameters': {
                                'string': False
                            },
                            'requestModels': {
                                'string': 'string'
                            },
                            'methodResponses': {
                                'string': {
                                    'statusCode': 'string',
                                    'responseParameters': {
                                        'string': True
                                    },
                                    'responseModels': {
                                        'string': 'string'
                                    }
                                }
                            },
                            'methodIntegration': {
                                'type': 'HTTP',
                                'httpMethod': 'string',
                                'uri': 'string',
                                'credentials': 'string',
                                'requestParameters': {
                                    'string': 'string'
                                },
                                'requestTemplates': {
                                    'string': 'string'
                                },
                                'passthroughBehavior': 'string',
                                'contentHandling': 'CONVERT_TO_TEXT',
                                'cacheNamespace': 'string',
                                'cacheKeyParameters': [
                                    'string',
                                ],
                                'integrationResponses': {
                                    'string': {
                                        'statusCode': 'string',
                                        'selectionPattern': 'string',
                                        'responseParameters': {
                                            'string': 'string'
                                        },
                                        'responseTemplates': {
                                            'string': 'string'
                                        },
                                        'contentHandling': 'CONVERT_TO_TEXT'
                                    }
                                }
                            }
                        }
                    }
                }
            ]
        }
    ]

    resources_api2 = [
        {
            'items': [
                {
                    'id': 'api2res1',
                    'parentId': 'string',
                    'pathPart': 'string',
                    'path': 'string',
                    'resourceMethods': {
                        'string': {
                            'httpMethod': 'string',
                            'authorizationType': 'string',
                            'authorizerId': 'string',
                            'apiKeyRequired': False,
                            'requestValidatorId': 'string',
                            'operationName': 'string',
                            'requestParameters': {
                                'string': False
                            },
                            'requestModels': {
                                'string': 'string'
                            },
                            'methodResponses': {
                                'string': {
                                    'statusCode': 'string',
                                    'responseParameters': {
                                        'string': True
                                    },
                                    'responseModels': {
                                        'string': 'string'
                                    }
                                }
                            },
                            'methodIntegration': {
                                'type': 'HTTP',
                                'httpMethod': 'string',
                                'uri': 'string',
                                'credentials': 'string',
                                'requestParameters': {
                                    'string': 'string'
                                },
                                'requestTemplates': {
                                    'string': 'string'
                                },
                                'passthroughBehavior': 'string',
                                'contentHandling': 'CONVERT_TO_BINARY',
                                'cacheNamespace': 'string',
                                'cacheKeyParameters': [
                                    'string',
                                ],
                                'integrationResponses': {
                                    'string': {
                                        'statusCode': 'string',
                                        'selectionPattern': 'string',
                                        'responseParameters': {
                                            'string': 'string'
                                        },
                                        'responseTemplates': {
                                            'string': 'string'
                                        },
                                        'contentHandling': 'CONVERT_TO_TEXT'
                                    }
                                }
                            }
                        }
                    }
                },
            ],
            'NextToken': 'string'
        },
        {
            'items': [
                {
                    'id': 'api2res2',
                    'parentId': 'string',
                    'pathPart': 'string',
                    'path': 'string',
                    'resourceMethods': {
                        'string': {
                            'httpMethod': 'string',
                            'authorizationType': 'string',
                            'authorizerId': 'string',
                            'apiKeyRequired': False,
                            'requestValidatorId': 'string',
                            'operationName': 'string',
                            'requestParameters': {
                                'string': False
                            },
                            'requestModels': {
                                'string': 'string'
                            },
                            'methodResponses': {
                                'string': {
                                    'statusCode': 'string',
                                    'responseParameters': {
                                        'string': True
                                    },
                                    'responseModels': {
                                        'string': 'string'
                                    }
                                }
                            },
                            'methodIntegration': {
                                'type': 'AWS_PROXY',
                                'httpMethod': 'string',
                                'uri': 'string',
                                'credentials': 'string',
                                'requestParameters': {
                                    'string': 'string'
                                },
                                'requestTemplates': {
                                    'string': 'string'
                                },
                                'passthroughBehavior': 'string',
                                'contentHandling': 'CONVERT_TO_TEXT',
                                'cacheNamespace': 'string',
                                'cacheKeyParameters': [
                                    'string',
                                ],
                                'integrationResponses': {
                                    'string': {
                                        'statusCode': 'string',
                                        'selectionPattern': 'string',
                                        'responseParameters': {
                                            'string': 'string'
                                        },
                                        'responseTemplates': {
                                            'string': 'string'
                                        },
                                        'contentHandling': 'CONVERT_TO_TEXT'
                                    }
                                }
                            }
                        }
                    }
                }
            ]
        }
    ]

    resources_api3 = [{'items': []}]

    get_resources = {
        'api1': resources_api1,
        'api2': resources_api2,
        'api3': resources_api3
    }

    doc_parts = {
        'api1': [
            {
                'id': 'string',
                'location': {
                    'type': 'API',
                    'path': 'string',
                    'method': 'string',
                    'statusCode': 'string',
                    'name': 'string'
                },
                'properties': 'string'
            },
            {
                'id': 'string',
                'location': {
                    'type': 'AUTHORIZER',
                    'path': 'string',
                    'method': 'string',
                    'statusCode': 'string',
                    'name': 'string'
                },
                'properties': 'string'
            },
            {
                'id': 'string',
                'location': {
                    'type': 'MODEL',
                    'path': 'string',
                    'method': 'string',
                    'statusCode': 'string',
                    'name': 'string'
                },
                'properties': 'string'
            },
            {
                'id': 'string',
                'location': {
                    'type': 'RESPONSE_BODY',
                    'path': 'string',
                    'method': 'string',
                    'statusCode': 'string',
                    'name': 'string'
                },
                'properties': 'string'
            },
        ],
        'api2': [
            {
                'id': 'string',
                'location': {
                    'type': 'API',
                    'path': 'string',
                    'method': 'string',
                    'statusCode': 'string',
                    'name': 'string'
                },
                'properties': 'string'
            }
        ],
        'api3': [
            {
                'id': 'string',
                'location': {
                    'type': 'API',
                    'path': 'string',
                    'method': 'string',
                    'statusCode': 'string',
                    'name': 'string'
                },
                'properties': 'string'
            },
            {
                'id': 'string',
                'location': {
                    'type': 'RESPONSE_BODY',
                    'path': 'string',
                    'method': 'string',
                    'statusCode': 'string',
                    'name': 'string'
                },
                'properties': 'string'
            }
        ]
    }

    stages = {
        'api1': {'item': [
            {
                'deploymentId': 'string',
                'clientCertificateId': 'string',
                'stageName': 'string',
                'description': 'string',
                'cacheClusterEnabled': True,
                'cacheClusterSize': '0.5',
                'cacheClusterStatus': 'AVAILABLE',
                'methodSettings': {
                    'string': {
                        'metricsEnabled': True,
                        'loggingLevel': 'string',
                        'dataTraceEnabled': True,
                        'throttlingBurstLimit': 123,
                        'throttlingRateLimit': 123.0,
                        'cachingEnabled': True,
                        'cacheTtlInSeconds': 123,
                        'cacheDataEncrypted': True,
                        'requireAuthorizationForCacheControl': True,
                        'unauthorizedCacheControlHeaderStrategy': 'FAIL_WITH_40'
                    }
                },
                'variables': {
                    'string': 'string'
                },
                'documentationVersion': 'string',
                'createdDate': datetime(2015, 1, 1),
                'lastUpdatedDate': datetime(2015, 1, 1)
            },
            {
                'deploymentId': 'foo'
            },
            {
                'deploymentId': 'bar'
            }
        ]},
        'api2': {
            'item': [
                {'deploymentId': 'baz'}
            ]
        },
        'api3': {
            'item': [
                {'deploymentId': 'blam'},
                {'deploymentId': 'blarg'}
            ]
        }
    }

    authorizers = {
        'api1': [
            {
                'id': 'string',
                'name': 'string',
                'type': 'TOKEN',
                'providerARNs': [
                    'string',
                ],
                'authType': 'string',
                'authorizerUri': 'string',
                'authorizerCredentials': 'string',
                'identitySource': 'string',
                'identityValidationExpression': 'string',
                'authorizerResultTtlInSeconds': 123
            }
        ],
        'api2': [
            {
                'id': 'string',
                'name': 'string',
                'type': 'REQUEST',
                'providerARNs': [
                    'string',
                ],
                'authType': 'string',
                'authorizerUri': 'string',
                'authorizerCredentials': 'string',
                'identitySource': 'string',
                'identityValidationExpression': 'string',
                'authorizerResultTtlInSeconds': 123
            },
            {
                'id': 'string',
                'name': 'string',
                'type': 'TOKEN',
                'providerARNs': [
                    'string',
                ],
                'authType': 'string',
                'authorizerUri': 'string',
                'authorizerCredentials': 'string',
                'identitySource': 'string',
                'identityValidationExpression': 'string',
                'authorizerResultTtlInSeconds': 123
            }
        ],
        'api3': []
    }

    plans = [
        {
            'items': [
                {
                    'id': 'string',
                    'name': 'string',
                    'description': 'string',
                    'apiStages': [
                        {
                            'apiId': 'string',
                            'stage': 'string'
                        },
                    ],
                    'throttle': {
                        'burstLimit': 123,
                        'rateLimit': 123.0
                    },
                    'quota': {
                        'limit': 123,
                        'offset': 123,
                        'period': 'DAY'
                    },
                    'productCode': 'string'
                },
                {
                    'id': 'string',
                    'name': 'string',
                    'description': 'string',
                    'apiStages': [
                        {
                            'apiId': 'string',
                            'stage': 'string'
                        },
                    ],
                    'throttle': {
                        'burstLimit': 123,
                        'rateLimit': 123.0
                    },
                    'quota': {
                        'limit': 123,
                        'offset': 123,
                        'period': 'WEEK'
                    },
                    'productCode': 'string'
                },
                {
                    'id': 'string',
                    'name': 'string',
                    'description': 'string',
                    'apiStages': [
                        {
                            'apiId': 'string',
                            'stage': 'string'
                        },
                    ],
                    'throttle': {
                        'burstLimit': 123,
                        'rateLimit': 123.0
                    },
                    'quota': {
                        'limit': 123,
                        'offset': 123,
                        'period': 'MONTH'
                    },
                    'productCode': 'string'
                }
            ],
            'NextToken': 'foo'
        },
        {
            'items': [
                {
                    'id': 'string',
                    'name': 'string',
                    'description': 'string',
                    'apiStages': [
                        {
                            'apiId': 'string',
                            'stage': 'string'
                        },
                    ],
                    'throttle': {
                        'burstLimit': 123,
                        'rateLimit': 123.0
                    },
                    'quota': {
                        'limit': 123,
                        'offset': 123,
                        'period': 'DAY'
                    },
                    'productCode': 'string'
                }
            ]
        }
    ]

    certs = [
        {
            'items': [
                {
                    'clientCertificateId': 'string',
                    'description': 'string',
                    'pemEncodedCertificate': 'string',
                    'createdDate': datetime(2015, 1, 1),
                    'expirationDate': datetime(2015, 1, 1)
                },
            ],
            'NextToken': 'string'
        },
        {
            'items': [
                {
                    'clientCertificateId': 'string',
                    'description': 'string',
                    'pemEncodedCertificate': 'string',
                    'createdDate': datetime(2015, 1, 1),
                    'expirationDate': datetime(2015, 1, 1)
                },
            ]
        }
    ]

    api_keys = [
        {
            'warnings': [
                'string',
            ],
            'items': [
                {
                    'id': 'string',
                    'value': 'string',
                    'name': 'string',
                    'customerId': 'string',
                    'description': 'string',
                    'enabled': True,
                    'createdDate': datetime(2015, 1, 1),
                    'lastUpdatedDate': datetime(2015, 1, 1),
                    'stageKeys': [
                        'string',
                    ]
                },
                {
                    'id': 'string',
                    'value': 'string',
                    'name': 'string',
                    'customerId': 'string',
                    'description': 'string',
                    'enabled': True,
                    'createdDate': datetime(2015, 1, 1),
                    'lastUpdatedDate': datetime(2015, 1, 1),
                    'stageKeys': [
                        'string',
                    ]
                }
            ],
            'NextToken': 'string'
        },
        {
            'warnings': [
                'string',
            ],
            'items': [
                {
                    'id': 'string',
                    'value': 'string',
                    'name': 'string',
                    'customerId': 'string',
                    'description': 'string',
                    'enabled': False,
                    'createdDate': datetime(2015, 1, 1),
                    'lastUpdatedDate': datetime(2015, 1, 1),
                    'stageKeys': [
                        'string',
                    ]
                },
            ],
            'NextToken': 'string'
        },
        {
            'warnings': [
                'string',
            ],
            'items': [
                {
                    'id': 'string',
                    'value': 'string',
                    'name': 'string',
                    'customerId': 'string',
                    'description': 'string',
                    'enabled': True,
                    'createdDate': datetime(2015, 1, 1),
                    'lastUpdatedDate': datetime(2015, 1, 1),
                    'stageKeys': [
                        'string',
                    ]
                },
            ]
        }
    ]


class DynamoDB(object):

    test_update_limits_from_api = {
        'AccountMaxReadCapacityUnits': 111,
        'AccountMaxWriteCapacityUnits': 222,
        'TableMaxReadCapacityUnits': 333,
        'TableMaxWriteCapacityUnits': 444
    }

    test_find_usage_dynamodb = [
        Mock(
            name='table1',
            global_secondary_indexes=[
                {
                    'IndexName': 't1gi1',
                    'KeySchema': [],
                    'Projection': {},
                    'IndexStatus': 'ACTIVE',
                    'Backfilling': False,
                    'ProvisionedThroughput': {
                        'LastIncreaseDateTime': datetime(2015, 1, 1),
                        'LastDecreaseDateTime': datetime(2016, 1, 1),
                        'NumberOfDecreasesToday': 0,
                        'ReadCapacityUnits': 10,
                        'WriteCapacityUnits': 20
                    },
                    'IndexSizeBytes': 100,
                    'ItemCount': 99,
                    'IndexArn': 't1gi1arn'
                },
                {
                    'IndexName': 't1gi2',
                    'KeySchema': [],
                    'Projection': {},
                    'IndexStatus': 'ACTIVE',
                    'Backfilling': False,
                    'ProvisionedThroughput': {
                        'LastIncreaseDateTime': datetime(2015, 1, 1),
                        'LastDecreaseDateTime': datetime(2016, 1, 1),
                        'NumberOfDecreasesToday': 0,
                        'ReadCapacityUnits': 44,
                        'WriteCapacityUnits': 66
                    },
                    'IndexSizeBytes': 100,
                    'ItemCount': 99,
                    'IndexArn': 't1gi2arn'
                }
            ],
            local_secondary_indexes=[
                {
                    'IndexName': 't1li1',
                    'KeySchema': [],
                    'Projection': {},
                    'IndexSizeBytes': 100,
                    'ItemCount': 99,
                    'IndexArn': 't1li1arn'
                },
                {
                    'IndexName': 't1li1',
                    'KeySchema': [],
                    'Projection': {},
                    'IndexSizeBytes': 100,
                    'ItemCount': 99,
                    'IndexArn': 't1li1arn'
                },
                {
                    'IndexName': 't1li1',
                    'KeySchema': [],
                    'Projection': {},
                    'IndexSizeBytes': 100,
                    'ItemCount': 99,
                    'IndexArn': 't1li1arn'
                }
            ],
            provisioned_throughput={
                'LastIncreaseDateTime': datetime(2015, 1, 1),
                'LastDecreaseDateTime': datetime(2016, 1, 1),
                'NumberOfDecreasesToday': 0,
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 20
            }
        ),
        Mock(
            name='table2',
            global_secondary_indexes=[
                {
                    'IndexName': 't2gi1',
                    'KeySchema': [],
                    'Projection': {},
                    'IndexStatus': 'ACTIVE',
                    'Backfilling': False,
                    'ProvisionedThroughput': {
                        'LastIncreaseDateTime': datetime(2015, 1, 1),
                        'LastDecreaseDateTime': datetime(2016, 1, 1),
                        'NumberOfDecreasesToday': 0,
                        'ReadCapacityUnits': 3,
                        'WriteCapacityUnits': 5
                    },
                    'IndexSizeBytes': 100,
                    'ItemCount': 99,
                    'IndexArn': 't1gi1arn'
                }
            ],
            local_secondary_indexes=[
                {
                    'IndexName': 't2li1',
                    'KeySchema': [],
                    'Projection': {},
                    'IndexSizeBytes': 100,
                    'ItemCount': 99,
                    'IndexArn': 't1li1arn'
                }
            ],
            provisioned_throughput={
                'LastIncreaseDateTime': datetime(2015, 1, 1),
                'LastDecreaseDateTime': datetime(2016, 1, 1),
                'NumberOfDecreasesToday': 0,
                'ReadCapacityUnits': 333,
                'WriteCapacityUnits': 444
            }
        ),
        Mock(
            name='table3',
            global_secondary_indexes=None,
            local_secondary_indexes=None,
            provisioned_throughput={
                'LastIncreaseDateTime': datetime(2015, 1, 1),
                'LastDecreaseDateTime': datetime(2016, 1, 1),
                'NumberOfDecreasesToday': 0,
                'ReadCapacityUnits': 600,
                'WriteCapacityUnits': 800
            }
        )
    ]
    type(test_find_usage_dynamodb[0]).name = 'table1'
    type(test_find_usage_dynamodb[1]).name = 'table2'
    type(test_find_usage_dynamodb[2]).name = 'table3'


class Route53(object):
    test_get_hosted_zones = {
        "HostedZones": [
            {
                'Config': {
                    'PrivateZone': True
                },
                'Id': '/hostedzone/ABC',
                'Name': 'abc.example.com.'
            },
            {
                'Config': {
                    'PrivateZone': True
                },
                'Id': '/hostedzone/DEF',
                'Name': 'def.example.com.'
            },
            {
                'Config': {
                    'PrivateZone': False
                },
                'Id': '/hostedzone/GHI',
                'Name': 'ghi.example.com.'
            }
        ]
    }

    test_get_hosted_zone_limit = {
        '/hostedzone/ABC': {
            'MAX_RRSETS_BY_ZONE': {
                'Count': 7500,
                'Limit': {
                    'Type': 'MAX_RRSETS_BY_ZONE',
                    'Value': 10000
                }
            },
            'MAX_VPCS_ASSOCIATED_BY_ZONE': {
                'Count': 10,
                'Limit': {
                    'Type': 'MAX_VPCS_ASSOCIATED_BY_ZONE',
                    'Value': 100
                }
            }
        },
        '/hostedzone/DEF': {
            'MAX_RRSETS_BY_ZONE': {
                'Count': 2500,
                'Limit': {
                    'Type': 'MAX_RRSETS_BY_ZONE',
                    'Value': 10001
                }
            },
            'MAX_VPCS_ASSOCIATED_BY_ZONE': {
                'Count': 2,
                'Limit': {
                    'Type': 'MAX_VPCS_ASSOCIATED_BY_ZONE',
                    'Value': 101
                }
            }
        },
        '/hostedzone/GHI': {
            'MAX_RRSETS_BY_ZONE': {
                'Count': 5678,
                'Limit': {
                    'Type': 'MAX_RRSETS_BY_ZONE',
                    'Value': 10002
                }
            }
        }
    }


class CloudTrail(object):

    mock_describe_trails = {
            'trailList': [
                {
                    'Name': 'trail1',
                    'S3BucketName': 'string',
                    'S3KeyPrefix': 'string',
                    'SnsTopicName': 'string',
                    'SnsTopicARN': 'string',
                    'IncludeGlobalServiceEvents': True,
                    'IsMultiRegionTrail': True,
                    'HomeRegion': 'thisregion',
                    'TrailARN': 'string',
                    'LogFileValidationEnabled': True,
                    'CloudWatchLogsLogGroupArn': 'string',
                    'CloudWatchLogsRoleArn': 'string',
                    'KmsKeyId': 'string',
                    'HasCustomEventSelectors': False
                },
                {
                    'Name': 'trail2',
                    'S3BucketName': 'string',
                    'S3KeyPrefix': 'string',
                    'SnsTopicName': 'string',
                    'SnsTopicARN': 'string',
                    'IncludeGlobalServiceEvents': True,
                    'IsMultiRegionTrail': True,
                    'HomeRegion': 'thisregion',
                    'TrailARN': 'string',
                    'LogFileValidationEnabled': True,
                    'CloudWatchLogsLogGroupArn': 'string',
                    'CloudWatchLogsRoleArn': 'string',
                    'KmsKeyId': 'string',
                    'HasCustomEventSelectors': True
                },
                {
                    'Name': 'trail3',
                    'S3BucketName': 'string',
                    'S3KeyPrefix': 'string',
                    'SnsTopicName': 'string',
                    'SnsTopicARN': 'string',
                    'IncludeGlobalServiceEvents': True,
                    'IsMultiRegionTrail': True,
                    'HomeRegion': 'otherRegion',
                    'TrailARN': 'string',
                    'LogFileValidationEnabled': True,
                    'CloudWatchLogsLogGroupArn': 'string',
                    'CloudWatchLogsRoleArn': 'string',
                    'KmsKeyId': 'string',
                    'HasCustomEventSelectors': True
                }
            ],
    }

    mock_get_event_selectors = {
            'TrailARN': 'string',
            'EventSelectors': [
                {
                    'ReadWriteType': 'ReadOnly',
                    'IncludeManagementEvents': True,
                    'DataResources': [
                        {
                            'Type': 'string',
                            'Values': [
                                'string',
                            ]
                        },
                        {
                            'Type': 'string',
                            'Values': [
                                'string',
                            ]
                        },
                        {
                            'Type': 'string',
                            'Values': [
                                'string',
                            ]
                        }
                    ]
                },
                {
                    'ReadWriteType': 'ReadOnly',
                    'IncludeManagementEvents': True,
                    'DataResources': []
                },
                {
                    'ReadWriteType': 'ReadOnly',
                    'IncludeManagementEvents': True
                }
            ]
    }
