"""
awslimitchecker/tests/test_trustedadvisor.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

##############################################################################
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
##############################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/awslimitchecker> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
##############################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
##############################################################################
"""

import sys
from botocore.exceptions import ClientError
from awslimitchecker.trustedadvisor import TrustedAdvisor
from awslimitchecker.services.base import _AwsService
from awslimitchecker.limit import AwsLimit
import pytest

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock


pbm = 'awslimitchecker.trustedadvisor'
pb = '%s.TrustedAdvisor' % pbm


class Test_TrustedAdvisor(object):

    def setup(self):
        self.mock_conn = Mock()
        self.mock_client_config = Mock()
        type(self.mock_client_config).region_name = 'us-east-1'
        type(self.mock_conn)._client_config = self.mock_client_config
        self.cls = TrustedAdvisor({})
        self.cls.conn = self.mock_conn

        self.mock_svc1 = Mock(spec_set=_AwsService)
        self.mock_svc2 = Mock(spec_set=_AwsService)
        self.services = {
            'SvcFoo': self.mock_svc1,
            'SvcBar': self.mock_svc2,
        }

    def test_init(self):
        cls = TrustedAdvisor({})
        assert cls.conn is None
        assert cls.account_id is None
        assert cls.account_role is None
        assert cls.region == 'us-east-1'
        assert cls.ta_region is None
        assert cls.external_id is None
        assert cls.mfa_serial_number is None
        assert cls.mfa_token is None
        assert cls.all_services == {}
        assert cls.limits_updated is False

    def test_init_sts(self):
        mock_svc = Mock(spec_set=_AwsService)
        mock_svc.get_limits.return_value = {}
        cls = TrustedAdvisor(
            {'foo': mock_svc},
            account_id='aid', account_role='role', region='r'
        )
        assert cls.conn is None
        assert cls.account_id == 'aid'
        assert cls.account_role == 'role'
        assert cls.region == 'us-east-1'
        assert cls.ta_region == 'r'
        assert cls.external_id is None
        assert cls.mfa_serial_number is None
        assert cls.mfa_token is None
        assert cls.all_services == {'foo': mock_svc}
        assert cls.limits_updated is False

    def test_init_sts_external_id(self):
        cls = TrustedAdvisor(
            {}, account_id='aid', account_role='role', region='r',
            external_id='myeid'
        )
        assert cls.conn is None
        assert cls.account_id == 'aid'
        assert cls.account_role == 'role'
        assert cls.region == 'us-east-1'
        assert cls.ta_region == 'r'
        assert cls.external_id == 'myeid'
        assert cls.mfa_serial_number is None
        assert cls.mfa_token is None
        assert cls.limits_updated is False

    def test_update_limits(self):
        mock_results = Mock()
        with patch('%s.connect' % pb, autospec=True) as mock_connect:
            with patch('%s._poll' % pb, autospec=True) as mock_poll:
                with patch('%s._update_services' % pb,
                           autospec=True) as mock_update_services:
                    mock_poll.return_value = mock_results
                    self.cls.update_limits()
        assert mock_connect.mock_calls == [call(self.cls)]
        assert mock_poll.mock_calls == [call(self.cls)]
        assert mock_update_services.mock_calls == [
            call(self.cls, mock_results)
        ]

    def test_update_limits_again(self):
        mock_results = Mock()
        self.cls.limits_updated = True
        with patch('%s.connect' % pb, autospec=True) as mock_connect:
            with patch('%s._poll' % pb, autospec=True) as mock_poll:
                with patch('%s._update_services' % pb,
                           autospec=True) as mock_update_services:
                    with patch('%s.logger' % pbm) as mock_logger:
                        mock_poll.return_value = mock_results
                        self.cls.update_limits()
        assert mock_connect.mock_calls == []
        assert mock_poll.mock_calls == []
        assert mock_update_services.mock_calls == []
        assert mock_logger.mock_calls == [
            call.debug('Already polled TA; skipping update')
        ]

    def test_get_limit_check_id(self):
        api_resp = {
            'checks': [
                {
                    'category': 'performance',
                    'name': 'Service Limits',
                    'id': 'bar',
                    'metadata': [
                        'Region',
                        'Service',
                        'Limit Name',
                        'Limit Amount',
                        'Current Usage',
                        'Status'
                    ],
                },
                {
                    'category': 'fault_tolerance',
                    'name': 'ELB Cross-Zone Load Balancing',
                    'id': 'foo',
                },
            ]
        }
        self.mock_conn.describe_trusted_advisor_checks.return_value = api_resp
        res = self.cls._get_limit_check_id()
        assert res == (
            'bar',
            [
                'Region',
                'Service',
                'Limit Name',
                'Limit Amount',
                'Current Usage',
                'Status'
            ]
        )
        assert self.mock_conn.mock_calls == [
            call.describe_trusted_advisor_checks(language='en')
        ]

    def test_get_limit_check_id_none(self):
        api_resp = {
            'checks': [
                {
                    'category': 'performance',
                    'name': 'Something Else',
                    'id': 'bar',
                },
                {
                    'category': 'fault_tolerance',
                    'name': 'ELB Cross-Zone Load Balancing',
                    'id': 'foo',
                },
            ]
        }
        self.mock_conn.describe_trusted_advisor_checks.return_value = api_resp
        res = self.cls._get_limit_check_id()
        assert res == (None, None)
        assert self.mock_conn.mock_calls == [
            call.describe_trusted_advisor_checks(language='en')
        ]

    def test_get_limit_check_id_subscription_required(self):

        def se_api(language=None):
            response = {
                'ResponseMetadata': {
                    'HTTPStatusCode': 400,
                    'RequestId': '3cc9b2a8-c6e5-11e5-bc1d-b13dcea36176'
                },
                'Error': {
                    'Message': 'AWS Premium Support Subscription is required '
                               'to use this service.',
                    'Code': 'SubscriptionRequiredException'
                }
            }
            raise ClientError(response, 'operation')

        assert self.cls.have_ta is True
        self.mock_conn.describe_trusted_advisor_checks.side_effect = se_api
        with patch('awslimitchecker.trustedadvisor'
                   '.logger', autospec=True) as mock_logger:
            res = self.cls._get_limit_check_id()
        assert self.cls.have_ta is False
        assert res == (None, None)
        assert self.mock_conn.mock_calls == [
            call.describe_trusted_advisor_checks(language='en')
        ]
        assert mock_logger.mock_calls == [
            call.debug("Querying Trusted Advisor checks"),
            call.warning("Cannot check TrustedAdvisor: %s",
                         'AWS Premium Support Subscription is required to '
                         'use this service.')
        ]

    def test_get_limit_check_id_other_exception(self):

        def se_api(language=None):
            response = {
                'ResponseMetadata': {
                    'HTTPStatusCode': 400,
                    'RequestId': '3cc9b2a8-c6e5-11e5-bc1d-b13dcea36176'
                },
                'Error': {
                    'Message': 'foo',
                    'Code': 'SomeOtherException'
                }
            }
            raise ClientError(response, 'operation')

        self.mock_conn.describe_trusted_advisor_checks.side_effect = se_api
        with pytest.raises(ClientError) as excinfo:
            self.cls._get_limit_check_id()
        assert self.mock_conn.mock_calls == [
            call.describe_trusted_advisor_checks(language='en')
        ]
        assert excinfo.value.response['ResponseMetadata'][
                   'HTTPStatusCode'] == 400
        assert excinfo.value.response['Error']['Message'] == 'foo'
        assert excinfo.value.response['Error']['Code'] == 'SomeOtherException'

    def test_poll_id_none(self):
        tmp = self.mock_conn.describe_trusted_advisor_check_result
        with patch('%s._get_limit_check_id' % pb, autospec=True) as mock_id:
            mock_id.return_value = None
            res = self.cls._poll()
        assert tmp.mock_calls == []
        assert res is None

    def test_poll(self):
        tmp = self.mock_conn.describe_trusted_advisor_check_result
        poll_return_val = {
            'result': {
                'timestamp': '2015-06-15T20:27:42Z',
                'flaggedResources': [
                    {
                        'status': 'ok',
                        'resourceId': 'resid1',
                        'isSuppressed': False,
                        'region': 'us-west-2',
                        'metadata': [
                            'us-west-2',
                            'AutoScaling',
                            'Auto Scaling groups',
                            '20',
                            '2',
                            'Green'
                        ]
                    },
                    {
                        'status': 'ok',
                        'resourceId': 'resid2',
                        'isSuppressed': False,
                        'region': 'us-east-1',
                        'metadata': [
                            'us-east-1',
                            'AutoScaling',
                            'Launch configurations',
                            '20',
                            '18',
                            'Yellow'
                        ]
                    },
                    {
                        'status': 'ok',
                        'resourceId': 'resid3',
                        'isSuppressed': False,
                        'region': 'us-east-1',
                        'metadata': [
                            'us-west-2',
                            'AutoScaling',
                            'Auto Scaling groups',
                            '40',
                            '10',
                            'Green'
                        ]
                    },
                    {
                        'status': 'ok',
                        'resourceId': 'resid4',
                        'isSuppressed': False,
                        'metadata': [
                            '-',
                            'IAM',
                            'Users',
                            '5000',
                            '152',
                            'Green'
                        ]
                    },
                ]
            }
        }
        tmp.return_value = poll_return_val
        with patch('%s._get_limit_check_id' % pb, autospec=True) as mock_id:
            mock_id.return_value = (
                'foo',
                [
                    'Region',
                    'Service',
                    'Limit Name',
                    'Limit Amount',
                    'Current Usage',
                    'Status'
                ]
            )
            res = self.cls._poll()
        assert self.mock_conn.mock_calls == [
            call.describe_trusted_advisor_check_result(
                checkId='foo', language='en'
            )
        ]
        assert mock_id.mock_calls == [call(self.cls)]
        assert res == {
            'AutoScaling': {
                'Launch configurations': 20,
                'Auto Scaling groups': 40,
            },
            'IAM': {
                'Users': 5000
            }
        }

    def test_poll_region(self):
        tmp = self.mock_conn.describe_trusted_advisor_check_result
        self.cls.ta_region = 'us-west-2'
        poll_return_value = {
            'result': {
                'timestamp': '2015-06-15T20:27:42Z',
                'flaggedResources': [
                    {
                        'status': 'ok',
                        'resourceId': 'resid1',
                        'isSuppressed': False,
                        'region': 'us-west-2',
                        'metadata': [
                            'us-west-2',
                            'AutoScaling',
                            'Auto Scaling groups',
                            '20',
                            '2',
                            'Green'
                        ]
                    },
                    {
                        'status': 'ok',
                        'resourceId': 'resid2',
                        'isSuppressed': False,
                        'region': 'us-east-1',
                        'metadata': [
                            'us-east-1',
                            'AutoScaling',
                            'Launch configurations',
                            '20',
                            '18',
                            'Yellow'
                        ]
                    },
                    {
                        'status': 'ok',
                        'resourceId': 'resid3',
                        'isSuppressed': False,
                        'region': 'us-east-1',
                        'metadata': [
                            'us-west-2',
                            'AutoScaling',
                            'Auto Scaling groups',
                            '40',
                            '10',
                            'Green'
                        ]
                    },
                    {
                        'status': 'ok',
                        'resourceId': 'resid4',
                        'isSuppressed': False,
                        'metadata': [
                            '-',
                            'IAM',
                            'Users',
                            '5000',
                            '152',
                            'Green'
                        ]
                    },
                ]
            }
        }
        tmp.return_value = poll_return_value
        with patch('%s._get_limit_check_id' % pb, autospec=True) as mock_id:
            mock_id.return_value = (
                'foo',
                [
                    'Region',
                    'Service',
                    'Limit Name',
                    'Limit Amount',
                    'Current Usage',
                    'Status'
                ]
            )
            res = self.cls._poll()
        assert self.mock_conn.mock_calls == [
            call.describe_trusted_advisor_check_result(
                checkId='foo', language='en'
            )
        ]
        assert mock_id.mock_calls == [call(self.cls)]
        assert res == {
            'AutoScaling': {
                'Auto Scaling groups': 20,
            },
            'IAM': {
                'Users': 5000
            }
        }

    def test_poll_dont_have_ta(self):
        self.cls.have_ta = False
        tmp = self.mock_conn.describe_trusted_advisor_check_result
        with patch('%s._get_limit_check_id' % pb, autospec=True) as mock_id:
            with patch('awslimitchecker.trustedadvisor'
                       '.logger', autospec=True) as mock_logger:
                res = self.cls._poll()
        assert self.mock_conn.mock_calls == []
        assert tmp.mock_calls == []
        assert mock_id.mock_calls == [
            call(self.cls)
        ]
        assert mock_logger.mock_calls == [
            call.info('Beginning TrustedAdvisor poll'),
            call.info('TrustedAdvisor.have_ta is False; not polling TA')
        ]
        assert res == {}

    def test_update_services(self):
        mock_as_foo = Mock(spec_set=AwsLimit)
        mock_as_bar = Mock(spec_set=AwsLimit)
        mock_ec2_baz = Mock(spec_set=AwsLimit)
        mock_vpc = Mock(spec_set=AwsLimit)
        ta_services = {
            'AutoScaling': {
                'foo': mock_as_foo,
                'bar': mock_as_bar
            },
            'EC2': {
                'baz': mock_ec2_baz
            },
            'VPC': {
                'VPC Elastic IP addresses (EIPs)': mock_vpc
            },
        }
        ta_results = {
            'AutoScaling': {
                'foo': 20,
                'bar': 40,
            },
            'EC2': {
                'baz': 5,
                'blam': 10,
            },
            'OtherService': {
                'blarg': 1,
            },
            'VPC': {
                'VPC Elastic IP addresses (EIPs)': 11,
            }
        }
        with patch('awslimitchecker.trustedadvisor'
                   '.logger', autospec=True) as mock_logger:
            self.cls.ta_services = ta_services
            self.cls._update_services(ta_results)
        assert mock_logger.mock_calls == [
            call.debug("Updating TA limits on all services"),
            call.info("TrustedAdvisor returned check results for unknown "
                      "limit '%s' (service %s)", 'blam', 'EC2'),
            call.info("TrustedAdvisor returned check results for unknown "
                      "service '%s'", 'OtherService'),
            call.info("Done updating TA limits on all services"),
        ]
        assert mock_as_foo.mock_calls == [
            call._set_ta_limit(20)
        ]
        assert mock_as_bar.mock_calls == [
            call._set_ta_limit(40)
        ]
        assert mock_ec2_baz.mock_calls == [
            call._set_ta_limit(5)
        ]
        assert mock_vpc.mock_calls == [
            call._set_ta_limit(11)
        ]

    def test_make_ta_service_dict(self):
        mock_ec2 = Mock(spec_set=_AwsService)
        mock_el1 = Mock(spec_set=AwsLimit)
        type(mock_el1).name = 'el1'
        type(mock_el1).ta_service_name = 'EC2'
        type(mock_el1).ta_limit_name = 'el1'
        mock_el2 = Mock(spec_set=AwsLimit)
        type(mock_el2).name = 'el2'
        type(mock_el2).ta_service_name = 'Foo'
        type(mock_el2).ta_limit_name = 'el2'
        mock_ec2.get_limits.return_value = {
            'mock_el1': mock_el1,
            'mock_el2': mock_el2
        }

        mock_vpc = Mock(spec_set=_AwsService)
        mock_vl1 = Mock(spec_set=AwsLimit)
        type(mock_vl1).name = 'vl1'
        type(mock_vl1).ta_service_name = 'VPC'
        type(mock_vl1).ta_limit_name = 'other name'
        mock_vl2 = Mock(spec_set=AwsLimit)
        type(mock_vl2).name = 'vl2'
        type(mock_vl2).ta_service_name = 'Foo'
        type(mock_vl2).ta_limit_name = 'other limit'
        mock_vpc.get_limits.return_value = {
            'mock_vl1': mock_vl1,
            'mock_vl2': mock_vl2
        }

        svcs = {
            'EC2': mock_ec2,
            'VPC': mock_vpc
        }

        expected = {
            'EC2': {
                'el1': mock_el1
            },
            'VPC': {
                'other name': mock_vl1
            },
            'Foo': {
                'el2': mock_el2,
                'other limit': mock_vl2
            }
        }
        self.cls.all_services = svcs
        assert self.cls._make_ta_service_dict() == expected
