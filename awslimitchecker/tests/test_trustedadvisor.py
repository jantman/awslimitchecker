"""
awslimitchecker/tests/test_trustedadvisor.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

##############################################################################
Copyright 2015-2017 Jason Antman <jason@jasonantman.com>

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
from awslimitchecker.trustedadvisor import TrustedAdvisor, datetime_now
from awslimitchecker.services.base import _AwsService
from awslimitchecker.limit import AwsLimit
import pytest
from datetime import datetime
from freezegun import freeze_time
from pytz import utc

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


class TestInit(object):

    def setup(self):
        self.mock_conn = Mock()
        self.mock_client_config = Mock()
        type(self.mock_client_config).region_name = 'us-east-1'
        type(self.mock_conn)._client_config = self.mock_client_config
        self.cls = TrustedAdvisor({}, {})
        self.cls.conn = self.mock_conn

        self.mock_svc1 = Mock(spec_set=_AwsService)
        self.mock_svc2 = Mock(spec_set=_AwsService)
        self.services = {
            'SvcFoo': self.mock_svc1,
            'SvcBar': self.mock_svc2,
        }

    def test_simple(self):
        cls = TrustedAdvisor({}, {})
        assert cls.conn is None
        assert cls._boto3_connection_kwargs == {
            'region_name': 'us-east-1'
        }
        assert cls.all_services == {}
        assert cls.limits_updated is False
        assert cls.refresh_mode is None
        assert cls.refresh_timeout is None

    def test_boto_kwargs(self):
        mock_svc = Mock(spec_set=_AwsService)
        mock_svc.get_limits.return_value = {}
        boto_args = dict(region_name='myregion',
                         aws_access_key_id='myaccesskey',
                         aws_secret_access_key='mysecretkey',
                         aws_session_token='mytoken')

        cls = TrustedAdvisor(
            {'foo': mock_svc},
            boto_args,
            ta_refresh_mode=123,
            ta_refresh_timeout=456
        )
        assert cls.conn is None
        cls_boto_args = cls._boto3_connection_kwargs
        assert cls_boto_args.get('region_name') == 'us-east-1'
        assert cls_boto_args.get('aws_access_key_id') == 'myaccesskey'
        assert cls_boto_args.get('aws_secret_access_key') == 'mysecretkey'
        assert cls_boto_args.get('aws_session_token') == 'mytoken'
        assert cls.ta_region == 'myregion'
        assert cls.all_services == {'foo': mock_svc}
        assert cls.limits_updated is False
        assert cls.refresh_mode == 123
        assert cls.refresh_timeout == 456


class TestUpdateLimits(object):

    def setup(self):
        self.mock_conn = Mock()
        self.mock_client_config = Mock()
        type(self.mock_client_config).region_name = 'us-east-1'
        type(self.mock_conn)._client_config = self.mock_client_config
        self.cls = TrustedAdvisor({}, {})
        self.cls.conn = self.mock_conn

        self.mock_svc1 = Mock(spec_set=_AwsService)
        self.mock_svc2 = Mock(spec_set=_AwsService)
        self.services = {
            'SvcFoo': self.mock_svc1,
            'SvcBar': self.mock_svc2,
        }

    def test_simple(self):
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

    def test_again(self):
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


class TestGetLimitCheckId(object):

    def setup(self):
        self.mock_conn = Mock()
        self.mock_client_config = Mock()
        type(self.mock_client_config).region_name = 'us-east-1'
        type(self.mock_conn)._client_config = self.mock_client_config
        self.cls = TrustedAdvisor({}, {})
        self.cls.conn = self.mock_conn

        self.mock_svc1 = Mock(spec_set=_AwsService)
        self.mock_svc2 = Mock(spec_set=_AwsService)
        self.services = {
            'SvcFoo': self.mock_svc1,
            'SvcBar': self.mock_svc2,
        }

    def test_simple(self):
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

    def test_none(self):
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

    def test_subscription_required(self):

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

    def test_other_exception(self):

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


class TestPoll(object):

    def setup(self):
        self.mock_conn = Mock()
        self.mock_client_config = Mock()
        type(self.mock_client_config).region_name = 'us-east-1'
        type(self.mock_conn)._client_config = self.mock_client_config
        self.cls = TrustedAdvisor({}, {})
        self.cls.conn = self.mock_conn

        self.mock_svc1 = Mock(spec_set=_AwsService)
        self.mock_svc2 = Mock(spec_set=_AwsService)
        self.services = {
            'SvcFoo': self.mock_svc1,
            'SvcBar': self.mock_svc2,
        }

    def test_none(self):
        tmp = self.mock_conn.describe_trusted_advisor_check_result
        with patch('%s._get_limit_check_id' % pb, autospec=True) as mock_id:
            mock_id.return_value = None
            res = self.cls._poll()
        assert tmp.mock_calls == []
        assert res is None

    def test_basic(self):
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
                        'resourceId': 'resid1',
                        'isSuppressed': False,
                        'region': 'us-east-1',
                        'metadata': [
                            'us-east-1',
                            'EC2',
                            'On-Demand instances - t2.micro',
                            'Unlimited',
                            '2',
                            'Green'
                        ]
                    },
                    {
                        'status': 'ok',
                        'resourceId': 'resid1',
                        'isSuppressed': False,
                        'region': 'us-east-1',
                        'metadata': [
                            'us-east-1',
                            'EC2',
                            'On-Demand instances - t2.small',
                            'error',
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
        with patch('%s._get_limit_check_id' % pb, autospec=True) as mock_id:
            with patch('%s._get_refreshed_check_result' % pb,
                       autospec=True) as mock_hr:
                mock_hr.return_value = poll_return_val
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
        assert self.mock_conn.mock_calls == []
        assert mock_id.mock_calls == [call(self.cls)]
        assert mock_hr.mock_calls == [
            call(self.cls, 'foo')
        ]
        assert res == {
            'AutoScaling': {
                'Launch configurations': 20,
                'Auto Scaling groups': 40,
            },
            'EC2': {
                'On-Demand instances - t2.micro': 'Unlimited'
            },
            'IAM': {
                'Users': 5000
            }
        }

    def test_no_timestamp(self):
        poll_return_val = {
            'result': {
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
                        'resourceId': 'resid1',
                        'isSuppressed': False,
                        'region': 'us-east-1',
                        'metadata': [
                            'us-east-1',
                            'EC2',
                            'On-Demand instances - t2.micro',
                            'Unlimited',
                            '2',
                            'Green'
                        ]
                    },
                    {
                        'status': 'ok',
                        'resourceId': 'resid1',
                        'isSuppressed': False,
                        'region': 'us-east-1',
                        'metadata': [
                            'us-east-1',
                            'EC2',
                            'On-Demand instances - t2.small',
                            'error',
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
        with patch('%s._get_limit_check_id' % pb, autospec=True) as mock_id:
            with patch('%s._get_refreshed_check_result' % pb,
                       autospec=True) as mock_hr:
                mock_hr.return_value = poll_return_val
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
        assert self.mock_conn.mock_calls == []
        assert mock_id.mock_calls == [call(self.cls)]
        assert mock_hr.mock_calls == [
            call(self.cls, 'foo')
        ]
        assert res == {
            'AutoScaling': {
                'Launch configurations': 20,
                'Auto Scaling groups': 40,
            },
            'EC2': {
                'On-Demand instances - t2.micro': 'Unlimited'
            },
            'IAM': {
                'Users': 5000
            }
        }

    def test_region(self):
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
        with patch('%s._get_limit_check_id' % pb, autospec=True) as mock_id:
            with patch('%s._get_refreshed_check_result' % pb,
                       autospec=True) as mock_hr:
                mock_hr.return_value = poll_return_value
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
        assert self.mock_conn.mock_calls == []
        assert mock_id.mock_calls == [call(self.cls)]
        assert mock_hr.mock_calls == [
            call(self.cls, 'foo')
        ]
        assert res == {
            'AutoScaling': {
                'Auto Scaling groups': 20,
            },
            'IAM': {
                'Users': 5000
            }
        }

    def test_dont_have_ta(self):
        self.cls.have_ta = False
        with patch('%s._get_limit_check_id' % pb, autospec=True) as mock_id:
            with patch('%s._get_refreshed_check_result' % pb,
                       autospec=True) as mock_hr:
                with patch('awslimitchecker.trustedadvisor'
                           '.logger', autospec=True) as mock_logger:
                    res = self.cls._poll()
        assert self.mock_conn.mock_calls == []
        assert mock_id.mock_calls == [
            call(self.cls)
        ]
        assert mock_hr.mock_calls == []
        assert mock_logger.mock_calls == [
            call.info('Beginning TrustedAdvisor poll'),
            call.info('TrustedAdvisor.have_ta is False; not polling TA')
        ]
        assert res == {}


class TestGetRefreshedCheckResult(object):

    def setup(self):
        self.mock_conn = Mock()
        self.mock_client_config = Mock()
        type(self.mock_client_config).region_name = 'us-east-1'
        type(self.mock_conn)._client_config = self.mock_client_config
        self.cls = TrustedAdvisor({}, {})
        self.cls.conn = self.mock_conn

        self.mock_svc1 = Mock(spec_set=_AwsService)
        self.mock_svc2 = Mock(spec_set=_AwsService)
        self.services = {
            'SvcFoo': self.mock_svc1,
            'SvcBar': self.mock_svc2,
        }

    def test_mode_none(self):
        self.cls.refresh_mode = None
        with patch('%s._get_check_result' % pb, autospec=True) as mock_gcr:
            with patch('%s._can_refresh_check' % pb, autospec=True) as mock_crc:
                with patch('%s.logger' % pbm, autospec=True) as mock_logger:
                    with patch('%s._poll_for_refresh' % pb,
                               autospec=True) as mock_pfr:
                        mock_gcr.return_value = ({'mock': 'gcr'}, None)
                        res = self.cls._get_refreshed_check_result('abc123')
        assert res == {'mock': 'gcr'}
        assert mock_gcr.mock_calls == [call(self.cls, 'abc123')]
        assert mock_crc.mock_calls == []
        assert mock_pfr.mock_calls == []
        assert mock_logger.mock_calls == [
            call.info("Not refreshing Trusted Advisor check (refresh mode is "
                      "None)")
        ]

    @freeze_time("2016-12-16 10:40:42", tz_offset=0)
    def test_mode_int(self):
        self.cls.refresh_mode = 120  # 2 minutes
        check_dt = datetime(2016, 12, 16, hour=10, minute=30, second=12,
                            tzinfo=utc)
        with patch('%s._get_check_result' % pb, autospec=True) as mock_gcr:
            with patch('%s._can_refresh_check' % pb, autospec=True) as mock_crc:
                with patch('%s.logger' % pbm, autospec=True) as mock_logger:
                    with patch('%s._poll_for_refresh' % pb,
                               autospec=True) as mock_pfr:
                        mock_gcr.return_value = ({'mock': 'gcr'}, check_dt)
                        mock_pfr.return_value = {'mock': 'pfr'}
                        mock_crc.return_value = True
                        res = self.cls._get_refreshed_check_result('abc123')
        assert res == {'mock': 'pfr'}
        assert mock_gcr.mock_calls == [call(self.cls, 'abc123')]
        assert mock_crc.mock_calls == [call(self.cls, 'abc123')]
        assert mock_pfr.mock_calls == [call(self.cls, 'abc123')]
        assert mock_logger.mock_calls == [
            call.debug('Handling refresh of check: %s', 'abc123'),
            call.debug('ta_refresh_mode older; check last refresh: %s; '
                       'threshold=%d seconds', check_dt, 120),
            call.info('Refreshing Trusted Advisor check: %s', 'abc123')
        ]

    @freeze_time("2016-12-16 10:40:42", tz_offset=0)
    def test_mode_int_within_threshold(self):
        self.cls.refresh_mode = 120  # 2 minutes
        check_dt = datetime(2016, 12, 16, hour=10, minute=40, second=12,
                            tzinfo=utc)
        with patch('%s._get_check_result' % pb, autospec=True) as mock_gcr:
            with patch('%s._can_refresh_check' % pb, autospec=True) as mock_crc:
                with patch('%s.logger' % pbm, autospec=True) as mock_logger:
                    with patch('%s._poll_for_refresh' % pb,
                               autospec=True) as mock_pfr:
                        mock_gcr.return_value = ({'mock': 'gcr'}, check_dt)
                        mock_pfr.return_value = {'mock': 'pfr'}
                        mock_crc.return_value = True
                        res = self.cls._get_refreshed_check_result('abc123')
        assert res == {'mock': 'gcr'}
        assert mock_gcr.mock_calls == [
            call(self.cls, 'abc123'),
            call(self.cls, 'abc123')
        ]
        assert mock_crc.mock_calls == [call(self.cls, 'abc123')]
        assert mock_pfr.mock_calls == []
        assert mock_logger.mock_calls == [
            call.debug('Handling refresh of check: %s', 'abc123'),
            call.debug('ta_refresh_mode older; check last refresh: %s; '
                       'threshold=%d seconds', check_dt, 120),
            call.warning('Trusted Advisor check %s last refresh time of %s '
                         'is newer than refresh threshold of %d seconds.',
                         'abc123',
                         datetime(2016, 12, 16, 10, 40, 12, tzinfo=utc),
                         120)
        ]

    @freeze_time("2016-12-16 10:40:42", tz_offset=0)
    def test_mode_trigger(self):
        self.cls.refresh_mode = 'trigger'
        check_dt = datetime(2016, 12, 16, hour=10, minute=30, second=12,
                            tzinfo=utc)
        with patch('%s._get_check_result' % pb, autospec=True) as mock_gcr:
            with patch('%s._can_refresh_check' % pb, autospec=True) as mock_crc:
                with patch('%s.logger' % pbm, autospec=True) as mock_logger:
                    with patch('%s._poll_for_refresh' % pb,
                               autospec=True) as mock_pfr:
                        mock_gcr.return_value = ({'mock': 'gcr'}, check_dt)
                        mock_pfr.return_value = {'mock': 'pfr'}
                        mock_crc.return_value = True
                        res = self.cls._get_refreshed_check_result('abc123')
        assert res == {'mock': 'gcr'}
        assert mock_gcr.mock_calls == [call(self.cls, 'abc123')]
        assert mock_crc.mock_calls == [call(self.cls, 'abc123')]
        assert mock_pfr.mock_calls == []
        assert mock_logger.mock_calls == [
            call.debug('Handling refresh of check: %s', 'abc123'),
            call.info('Refreshing Trusted Advisor check: %s', 'abc123')
        ]

    @freeze_time("2016-12-16 10:40:42", tz_offset=0)
    def test_cant_refresh(self):
        self.cls.refresh_mode = 120  # 2 minutes
        check_dt = datetime(2016, 12, 16, hour=10, minute=30, second=12,
                            tzinfo=utc)
        with patch('%s._get_check_result' % pb, autospec=True) as mock_gcr:
            with patch('%s._can_refresh_check' % pb, autospec=True) as mock_crc:
                with patch('%s.logger' % pbm, autospec=True) as mock_logger:
                    with patch('%s._poll_for_refresh' % pb,
                               autospec=True) as mock_pfr:
                        mock_gcr.return_value = ({'mock': 'gcr'}, check_dt)
                        mock_pfr.return_value = {'mock': 'pfr'}
                        mock_crc.return_value = False
                        res = self.cls._get_refreshed_check_result('abc123')
        assert res == {'mock': 'gcr'}
        assert mock_gcr.mock_calls == [call(self.cls, 'abc123')]
        assert mock_crc.mock_calls == [call(self.cls, 'abc123')]
        assert mock_pfr.mock_calls == []
        assert mock_logger.mock_calls == [
            call.debug('Handling refresh of check: %s', 'abc123')
        ]


class TestGetCheckResult(object):

    def setup(self):
        self.mock_conn = Mock()
        self.mock_client_config = Mock()
        type(self.mock_client_config).region_name = 'us-east-1'
        type(self.mock_conn)._client_config = self.mock_client_config
        self.cls = TrustedAdvisor({}, {})
        self.cls.conn = self.mock_conn

        self.mock_svc1 = Mock(spec_set=_AwsService)
        self.mock_svc2 = Mock(spec_set=_AwsService)
        self.services = {
            'SvcFoo': self.mock_svc1,
            'SvcBar': self.mock_svc2,
        }

    def test_simple(self):
        tmp = self.mock_conn.describe_trusted_advisor_check_result
        check_result = {
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
                    }
                ]
            }
        }
        tmp.return_value = check_result
        res = self.cls._get_check_result('abc123')
        assert tmp.mock_calls == [
            call(checkId='abc123', language='en')
        ]
        assert res == (
            check_result,
            datetime(2015, 6, 15, 20, 27, 42, tzinfo=utc)
        )

    def test_no_timestamp(self):
        tmp = self.mock_conn.describe_trusted_advisor_check_result
        check_result = {
            'result': {
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
                    }
                ]
            }
        }
        tmp.return_value = check_result
        res = self.cls._get_check_result('abc123')
        assert tmp.mock_calls == [
            call(checkId='abc123', language='en')
        ]
        assert res == (check_result, None)


class TestCanRefreshCheck(object):

    def setup(self):
        self.mock_conn = Mock()
        self.mock_client_config = Mock()
        type(self.mock_client_config).region_name = 'us-east-1'
        type(self.mock_conn)._client_config = self.mock_client_config
        self.cls = TrustedAdvisor({}, {})
        self.cls.conn = self.mock_conn

    def test_true(self):
        tmp = self.mock_conn.describe_trusted_advisor_check_refresh_statuses
        chkstat = {
            'checkId': 'abc123',
            'status': 'none',
            'millisUntilNextRefreshable': 0
        }
        tmp.return_value = {
            'statuses': [chkstat]
        }
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            res = self.cls._can_refresh_check('abc123')
        assert res is True
        assert tmp.mock_calls == [
            call(checkIds=['abc123'])
        ]
        assert mock_logger.mock_calls == [
            call.debug('TA Check %s refresh status: %s',
                       'abc123', chkstat)
        ]

    def test_false(self):
        tmp = self.mock_conn.describe_trusted_advisor_check_refresh_statuses
        chkstat = {
            'checkId': 'abc123',
            'status': 'none',
            'millisUntilNextRefreshable': 123456
        }
        tmp.return_value = {
            'statuses': [chkstat]
        }
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            res = self.cls._can_refresh_check('abc123')
        assert res is False
        assert tmp.mock_calls == [
            call(checkIds=['abc123'])
        ]
        assert mock_logger.mock_calls == [
            call.debug('TA Check %s refresh status: %s',
                       'abc123', chkstat),
            call.warning("Trusted Advisor check cannot be refreshed for "
                         "another %d milliseconds; skipping refresh and "
                         "getting check results now", 123456)
        ]

    def test_exception(self):
        tmp = self.mock_conn.describe_trusted_advisor_check_refresh_statuses
        chkstat = {
            'checkId': 'abc123',
            'status': 'none'
        }
        tmp.return_value = {
            'statuses': [chkstat]
        }
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            res = self.cls._can_refresh_check('abc123')
        assert res is True
        assert tmp.mock_calls == [
            call(checkIds=['abc123'])
        ]
        assert mock_logger.mock_calls == [
            call.debug('TA Check %s refresh status: %s',
                       'abc123', chkstat),
            call.warning('Could not get refresh status for TA check %s',
                         'abc123', exc_info=True)
        ]


class TestPollForRefresh(object):

    def setup(self):
        self.mock_conn = Mock()
        self.mock_client_config = Mock()
        type(self.mock_client_config).region_name = 'us-east-1'
        type(self.mock_conn)._client_config = self.mock_client_config
        self.cls = TrustedAdvisor({}, {})
        self.cls.conn = self.mock_conn

    def test_no_timeout(self):
        self.cls.refresh_timeout = None
        check_dt = datetime(2016, 12, 16, hour=10, minute=30, second=12,
                            tzinfo=utc)
        now_dt = datetime(2016, 12, 16, hour=11, minute=30, second=12,
                          tzinfo=utc)
        statuses = [
            {'statuses': [{'status': 'none'}]},
            {'statuses': [{'status': 'enqueued'}]},
            {'statuses': [{'status': 'processing'}]},
            {'statuses': [{'status': 'success'}]}
        ]
        m_s = self.mock_conn.describe_trusted_advisor_check_refresh_statuses
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.sleep' % pbm, autospec=True) as mock_sleep:
                with patch('%s._get_check_result' % pb, autospec=True) as gcr:
                    with patch('%s.datetime_now' % pbm) as mock_dt_now:
                        mock_dt_now.return_value = now_dt
                        m_s.side_effect = statuses
                        gcr.return_value = ({'foo': 'bar'}, check_dt)
                        res = self.cls._poll_for_refresh('abc123')
        assert res == {'foo': 'bar'}
        assert self.mock_conn.mock_calls == [
            call.describe_trusted_advisor_check_refresh_statuses(
                checkIds=['abc123']),
            call.describe_trusted_advisor_check_refresh_statuses(
                checkIds=['abc123']),
            call.describe_trusted_advisor_check_refresh_statuses(
                checkIds=['abc123']),
            call.describe_trusted_advisor_check_refresh_statuses(
                checkIds=['abc123'])
        ]
        assert gcr.mock_calls == [call(self.cls, 'abc123')]
        assert mock_sleep.mock_calls == [
            call(30), call(30), call(30)
        ]
        assert mock_dt_now.mock_calls == [
            call(), call(), call(), call(), call()
        ]
        assert mock_logger.mock_calls == [
            call.warning('Polling for TA check %s refresh...', 'abc123'),
            call.debug('Checking refresh status'),
            call.info('Refresh status: %s; sleeping 30s', 'none'),
            call.debug('Checking refresh status'),
            call.info('Refresh status: %s; sleeping 30s', 'enqueued'),
            call.debug('Checking refresh status'),
            call.info('Refresh status: %s; sleeping 30s', 'processing'),
            call.debug('Checking refresh status'),
            call.info('Refresh status: %s; done polling', 'success'),
            call.info('Done polling for check refresh'),
            call.debug('Check shows last refresh time of: %s', check_dt)
        ]

    def test_timeout(self):
        self.cls.refresh_timeout = 45
        check_dt = datetime(2016, 12, 16, hour=10, minute=30, second=12,
                            tzinfo=utc)
        now_dts = [
            datetime(2016, 12, 16, hour=11, minute=30, second=0, tzinfo=utc),
            datetime(2016, 12, 16, hour=11, minute=30, second=0, tzinfo=utc),
            datetime(2016, 12, 16, hour=11, minute=30, second=30, tzinfo=utc),
            datetime(2016, 12, 16, hour=11, minute=31, second=0, tzinfo=utc),
        ]
        status = {'statuses': [{'status': 'processing'}]}
        m_s = self.mock_conn.describe_trusted_advisor_check_refresh_statuses
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.sleep' % pbm, autospec=True) as mock_sleep:
                with patch('%s._get_check_result' % pb, autospec=True) as gcr:
                    with patch('%s.datetime_now' % pbm) as mock_dt_now:
                        mock_dt_now.side_effect = now_dts
                        m_s.return_value = status
                        gcr.return_value = ({'foo': 'bar'}, check_dt)
                        res = self.cls._poll_for_refresh('abc123')
        assert res == {'foo': 'bar'}
        assert self.mock_conn.mock_calls == [
            call.describe_trusted_advisor_check_refresh_statuses(
                checkIds=['abc123']),
            call.describe_trusted_advisor_check_refresh_statuses(
                checkIds=['abc123'])
        ]
        assert gcr.mock_calls == [call(self.cls, 'abc123')]
        assert mock_sleep.mock_calls == [
            call(30), call(30)
        ]
        assert mock_dt_now.mock_calls == [
            call(), call(), call(), call()
        ]
        assert mock_logger.mock_calls == [
            call.warning('Polling for TA check %s refresh...', 'abc123'),
            call.debug('Checking refresh status'),
            call.info('Refresh status: %s; sleeping 30s', 'processing'),
            call.debug('Checking refresh status'),
            call.info('Refresh status: %s; sleeping 30s', 'processing'),
            call.error('Timed out waiting for TA Check refresh; status=%s',
                       'processing'),
            call.info('Done polling for check refresh'),
            call.debug('Check shows last refresh time of: %s', check_dt)
        ]

    def test_none(self):
        self.cls.refresh_timeout = None
        check_dt = datetime(2016, 12, 16, hour=10, minute=30, second=12,
                            tzinfo=utc)
        now_dt = datetime(2016, 12, 16, hour=11, minute=30, second=12,
                          tzinfo=utc)
        statuses = [
            {'statuses': [{'status': 'none'}]},
            {'statuses': [{'status': 'enqueued'}]},
            {'statuses': [{'status': 'processing'}]},
            {'statuses': [{'status': 'none'}]}
        ]
        m_s = self.mock_conn.describe_trusted_advisor_check_refresh_statuses
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.sleep' % pbm, autospec=True) as mock_sleep:
                with patch('%s._get_check_result' % pb, autospec=True) as gcr:
                    with patch('%s.datetime_now' % pbm) as mock_dt_now:
                        mock_dt_now.return_value = now_dt
                        m_s.side_effect = statuses
                        gcr.return_value = ({'foo': 'bar'}, check_dt)
                        res = self.cls._poll_for_refresh('abc123')
        assert res == {'foo': 'bar'}
        assert self.mock_conn.mock_calls == [
            call.describe_trusted_advisor_check_refresh_statuses(
                checkIds=['abc123']),
            call.describe_trusted_advisor_check_refresh_statuses(
                checkIds=['abc123']),
            call.describe_trusted_advisor_check_refresh_statuses(
                checkIds=['abc123']),
            call.describe_trusted_advisor_check_refresh_statuses(
                checkIds=['abc123'])
        ]
        assert gcr.mock_calls == [call(self.cls, 'abc123')]
        assert mock_sleep.mock_calls == [
            call(30), call(30), call(30)
        ]
        assert mock_dt_now.mock_calls == [
            call(), call(), call(), call(), call()
        ]
        assert mock_logger.mock_calls == [
            call.warning('Polling for TA check %s refresh...', 'abc123'),
            call.debug('Checking refresh status'),
            call.info('Refresh status: %s; sleeping 30s', 'none'),
            call.debug('Checking refresh status'),
            call.info('Refresh status: %s; sleeping 30s', 'enqueued'),
            call.debug('Checking refresh status'),
            call.info('Refresh status: %s; sleeping 30s', 'processing'),
            call.debug('Checking refresh status'),
            call.warning('Trusted Advisor check refresh status went '
                         'from "%s" to "%s"; refresh is either complete '
                         'or timed out on AWS side. Continuing',
                         'processing', 'none'),
            call.info('Done polling for check refresh'),
            call.debug('Check shows last refresh time of: %s', check_dt)
        ]


class TestUpdateServices(object):

    def setup(self):
        self.mock_conn = Mock()
        self.mock_client_config = Mock()
        type(self.mock_client_config).region_name = 'us-east-1'
        type(self.mock_conn)._client_config = self.mock_client_config
        self.cls = TrustedAdvisor({}, {})
        self.cls.conn = self.mock_conn

        self.mock_svc1 = Mock(spec_set=_AwsService)
        self.mock_svc2 = Mock(spec_set=_AwsService)
        self.services = {
            'SvcFoo': self.mock_svc1,
            'SvcBar': self.mock_svc2,
        }

    def test_simple(self):
        mock_as_foo = Mock(spec_set=AwsLimit)
        mock_as_bar = Mock(spec_set=AwsLimit)
        mock_ec2_baz = Mock(spec_set=AwsLimit)
        mock_ec2_blarg = Mock(spec_set=AwsLimit)
        mock_vpc = Mock(spec_set=AwsLimit)
        ta_services = {
            'AutoScaling': {
                'foo': mock_as_foo,
                'bar': mock_as_bar
            },
            'EC2': {
                'baz': mock_ec2_baz,
                'blarg': mock_ec2_blarg
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
                'blarg': 'Unlimited',
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
        assert mock_ec2_blarg.mock_calls == [
            call._set_ta_unlimited()
        ]
        assert mock_vpc.mock_calls == [
            call._set_ta_limit(11)
        ]


class TestMakeTAServiceDict(object):

    def setup(self):
        self.mock_conn = Mock()
        self.mock_client_config = Mock()
        type(self.mock_client_config).region_name = 'us-east-1'
        type(self.mock_conn)._client_config = self.mock_client_config
        self.cls = TrustedAdvisor({}, {})
        self.cls.conn = self.mock_conn

        self.mock_svc1 = Mock(spec_set=_AwsService)
        self.mock_svc2 = Mock(spec_set=_AwsService)
        self.services = {
            'SvcFoo': self.mock_svc1,
            'SvcBar': self.mock_svc2,
        }

    def test_simple(self):
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


class TestDatetimeNow(object):

    @freeze_time("2016-12-16 10:40:42")
    def test_it(self):
        dt = datetime(2016, 12, 16, hour=10, minute=40, second=42)
        assert datetime_now() == dt
