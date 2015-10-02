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
from boto.support.layer1 import SupportConnection
from boto.support import connect_to_region
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError, BotoServerError
from awslimitchecker.trustedadvisor import TrustedAdvisor
from awslimitchecker.services.base import _AwsService
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


pb = 'awslimitchecker.trustedadvisor.TrustedAdvisor'


class Test_TrustedAdvisor(object):

    def setup(self):
        self.mock_conn = Mock(spec_set=SupportConnection)
        type(self.mock_conn).region = RegionInfo(name='us-east-1')
        self.cls = TrustedAdvisor()
        self.cls.conn = self.mock_conn

        self.mock_svc1 = Mock(spec_set=_AwsService)
        self.mock_svc2 = Mock(spec_set=_AwsService)
        self.services = {
            'SvcFoo': self.mock_svc1,
            'SvcBar': self.mock_svc2,
        }

    def test_init(self):
        cls = TrustedAdvisor()
        assert cls.conn is None
        assert cls.account_id is None
        assert cls.account_role is None
        assert cls.region == 'us-east-1'
        assert cls.ta_region is None
        assert cls.external_id is None

    def test_init_sts(self):
        cls = TrustedAdvisor(account_id='aid', account_role='role', region='r')
        assert cls.conn is None
        assert cls.account_id == 'aid'
        assert cls.account_role == 'role'
        assert cls.region == 'us-east-1'
        assert cls.ta_region == 'r'
        assert cls.external_id is None

    def test_init_sts_external_id(self):
        cls = TrustedAdvisor(account_id='aid', account_role='role', region='r',
                             external_id='myeid')
        assert cls.conn is None
        assert cls.account_id == 'aid'
        assert cls.account_role == 'role'
        assert cls.region == 'us-east-1'
        assert cls.ta_region == 'r'
        assert cls.external_id == 'myeid'

    def test_connect(self):
        cls = TrustedAdvisor()
        mock_conn = Mock(spec_set=SupportConnection, name='mock_conn')
        with patch('awslimitchecker.trustedadvisor.boto.connect_support'
                   '', autospec=True) as mock_connect:
            mock_connect.return_value = mock_conn
            cls.connect()
        assert cls.conn == mock_conn
        assert mock_connect.mock_calls == [call()]

    def test_connect_region(self):
        cls = TrustedAdvisor(account_id='foo', account_role='bar', region='re')
        mock_conn = Mock(spec_set=SupportConnection, name='mock_conn')
        mock_conn_via = Mock(spec_set=SupportConnection, name='mock_conn')
        with patch('awslimitchecker.trustedadvisor.TrustedAdvisor.connect_via'
                   '') as mock_connect_via:
            mock_connect_via.return_value = mock_conn_via
            with patch('awslimitchecker.trustedadvisor.boto.connect_support'
                       '', autospec=True) as mock_connect:
                mock_connect.return_value = mock_conn
                cls.connect()
        assert cls.conn == mock_conn_via
        assert mock_connect.mock_calls == []
        assert mock_connect_via.mock_calls == [
            call(connect_to_region)
        ]

    def test_connect_again(self):
        cls = TrustedAdvisor()
        mock_original_conn = Mock(spec_set=SupportConnection)
        cls.conn = mock_original_conn
        mock_conn = Mock(spec_set=SupportConnection)
        with patch('awslimitchecker.trustedadvisor.boto.connect_support'
                   '') as mock_connect:
            mock_connect.return_value = mock_conn
            cls.connect()
        assert cls.conn == mock_original_conn
        assert mock_connect.mock_calls == []

    def test_update_limits(self):
        mock_results = Mock()
        with patch('%s.connect' % pb, autospec=True) as mock_connect:
            with patch('%s._poll' % pb, autospec=True) as mock_poll:
                with patch('%s._update_services' % pb,
                           autospec=True) as mock_update_services:
                    mock_poll.return_value = mock_results
                    self.cls.update_limits(self.services)
        assert mock_connect.mock_calls == [call(self.cls)]
        assert mock_poll.mock_calls == [call(self.cls)]
        assert mock_update_services.mock_calls == [
            call(self.cls, mock_results, self.services)
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
            call.describe_trusted_advisor_checks('en')
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
            call.describe_trusted_advisor_checks('en')
        ]

    def test_get_limit_check_id_subscription_required(self):

        def se_api(language):
            status = 400
            reason = 'Bad Request'
            body = {
                'message': 'AWS Premium Support Subscription is required to '
                'use this service.',
                '__type': 'SubscriptionRequiredException'
            }
            raise JSONResponseError(status, reason, body)

        self.mock_conn.describe_trusted_advisor_checks.side_effect = se_api
        assert self.cls.have_ta is True
        with patch('awslimitchecker.trustedadvisor'
                   '.logger', autospec=True) as mock_logger:
            res = self.cls._get_limit_check_id()
        assert self.cls.have_ta is False
        assert res == (None, None)
        assert self.mock_conn.mock_calls == [
            call.describe_trusted_advisor_checks('en')
        ]
        assert mock_logger.mock_calls == [
            call.debug("Querying Trusted Advisor checks"),
            call.warning("Cannot check TrustedAdvisor: %s",
                         "AWS Premium Support "
                         "Subscription is required to use this service.")
        ]

    def test_get_limit_check_id_other_exception(self):

        def se_api(language):
            status = 400
            reason = 'foobar'
            body = {
                'message': 'other message',
                '__type': 'OtherException'
            }
            raise JSONResponseError(status, reason, body)

        self.mock_conn.describe_trusted_advisor_checks.side_effect = se_api
        with pytest.raises(BotoServerError) as excinfo:
            self.cls._get_limit_check_id()
        assert self.mock_conn.mock_calls == [
            call.describe_trusted_advisor_checks('en')
        ]
        assert excinfo.value.status == 400
        assert excinfo.value.reason == 'foobar'
        assert excinfo.value.body['__type'] == 'OtherException'

    def test_poll_id_none(self):
        tmp = self.mock_conn.describe_trusted_advisor_check_result
        with patch('%s._get_limit_check_id' % pb, autospec=True) as mock_id:
            mock_id.return_value = None
            self.cls._poll()
        assert tmp.mock_calls == []

    def test_poll(self):
        tmp = self.mock_conn.describe_trusted_advisor_check_result
        tmp.return_value = {
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
                ]
            }
        }
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
        assert tmp.mock_calls == [call('foo')]
        assert mock_id.mock_calls == [call(self.cls)]
        assert res == {
            'AutoScaling': {
                'Launch configurations': 20,
                'Auto Scaling groups': 40,
            }
        }

    def test_poll_region(self):
        tmp = self.mock_conn.describe_trusted_advisor_check_result
        self.cls.ta_region = 'us-west-2'
        tmp.return_value = {
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
                ]
            }
        }
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
        assert tmp.mock_calls == [call('foo')]
        assert mock_id.mock_calls == [call(self.cls)]
        assert res == {
            'AutoScaling': {
                'Auto Scaling groups': 20,
            }
        }

    def test_poll_dont_have_ta(self):
        self.cls.have_ta = False
        tmp = self.mock_conn.describe_trusted_advisor_check_result
        with patch('%s._get_limit_check_id' % pb, autospec=True) as mock_id:
            with patch('awslimitchecker.trustedadvisor'
                       '.logger', autospec=True) as mock_logger:
                res = self.cls._poll()
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

        def se_set(lname, val):
            if lname == 'blam':
                raise ValueError("foo")

        mock_autoscale = Mock(spec_set=_AwsService)
        mock_ec2 = Mock(spec_set=_AwsService)
        mock_ec2._set_ta_limit.side_effect = se_set
        services = {
            'AutoScaling': mock_autoscale,
            'EC2': mock_ec2,
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
            }
        }
        with patch('awslimitchecker.trustedadvisor'
                   '.logger', autospec=True) as mock_logger:
            self.cls._update_services(ta_results, services)
        assert mock_logger.mock_calls == [
            call.debug("Updating TA limits on all services"),
            call.info("TrustedAdvisor returned check results for unknown "
                      "limit '%s' (service %s)", 'blam', 'EC2'),
            call.info("TrustedAdvisor returned check results for unknown "
                      "service '%s'", 'OtherService'),
            call.info("Done updating TA limits on all services"),
        ]
        assert mock_autoscale.mock_calls == [
            call._set_ta_limit('bar', 40),
            call._set_ta_limit('foo', 20),
        ]
        assert mock_ec2.mock_calls == [
            call._set_ta_limit('baz', 5),
            call._set_ta_limit('blam', 10),
        ]
