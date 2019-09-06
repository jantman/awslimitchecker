"""
awslimitchecker/tests/alerts/test_pagerdutyv1.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2015-2019 Jason Antman <jason@jasonantman.com>

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
import json
from awslimitchecker.alerts.pagerdutyv1 import PagerDutyV1
import pytest

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT

pbm = 'awslimitchecker.alerts.pagerdutyv1'
pb = '%s.PagerDutyV1' % pbm


class TestInit(object):

    @patch.dict(
        'os.environ',
        {'PAGERDUTY_SERVICE_KEY_CRIT': 'cKey'},
        clear=True
    )
    def test_no_options(self):
        cls = PagerDutyV1('foo')
        assert cls._region_name == 'foo'
        assert cls._service_key_crit == 'cKey'
        assert cls._service_key_warn is None
        assert cls._account_alias is None
        assert cls._incident_key == 'awslimitchecker--foo'

    @patch.dict(
        'os.environ',
        {
            'PAGERDUTY_SERVICE_KEY_CRIT': 'cKey',
            'PAGERDUTY_SERVICE_KEY_WARN': 'wKey'
        },
        clear=True
    )
    def test_warn_env_var(self):
        cls = PagerDutyV1('foo')
        assert cls._region_name == 'foo'
        assert cls._service_key_crit == 'cKey'
        assert cls._service_key_warn == 'wKey'
        assert cls._account_alias is None
        assert cls._incident_key == 'awslimitchecker--foo'

    @patch.dict('os.environ', {}, clear=True)
    def test_all_options(self):
        cls = PagerDutyV1(
            'foo', account_alias='myacct', critical_service_key='cKey',
            warning_service_key='wKey',
            incident_key='foo{account_alias}bar{region_name}baz'
        )
        assert cls._region_name == 'foo'
        assert cls._service_key_crit == 'cKey'
        assert cls._service_key_warn == 'wKey'
        assert cls._account_alias == 'myacct'
        assert cls._incident_key == 'foomyacctbarfoobaz'

    @patch.dict('os.environ', {}, clear=True)
    def test_no_crit_key(self):
        with pytest.raises(RuntimeError) as exc:
            PagerDutyV1('foo')
        assert str(exc.value) == 'ERROR: PagerDutyV1 alert ' \
                                 'provider requires ' \
                                 'critical_service_key parameter or' \
                                 ' PAGERDUTY_SERVICE_KEY_CRIT ' \
                                 'environment variable.'


class PagerDutyV1Tester(object):

    def setup(self):
        with patch('%s.__init__' % pb) as m_init:
            m_init.return_value = None
            self.cls = PagerDutyV1('rname')
            self.cls._incident_key = 'iKey'
            self.cls._region_name = 'rname'
            self.cls._service_key_warn = None
            self.cls._service_key_crit = None
            self.cls._account_alias = None


class TestSendEvent(PagerDutyV1Tester):

    def test_success(self):
        mock_http = Mock()
        mock_resp = Mock(
            status=200, data='{"status": "success", "message": '
                             '"Event processed", "incident_key":'
                             ' "iKey"}'
        )
        mock_http.request.return_value = mock_resp
        expected = json.dumps(
            {'foo': 'bar', 'service_key': 'sKey'}, sort_keys=True
        ).encode('utf-8')
        with patch('%s.urllib3.PoolManager' % pbm) as mock_pm:
            mock_pm.return_value = mock_http
            self.cls._send_event('sKey', {'foo': 'bar'})
        assert mock_http.mock_calls == [
            call.request(
                'POST', self.cls.pd_url,
                headers={'Content-type': 'application/json'},
                body=expected
            )
        ]

    def test_invalid_event(self):
        mock_http = Mock()
        mock_resp = Mock(
            status=400, data='{"status": "invalid event",'
                             '"message": "Event object is invalid", '
                             '"errors": ["foo"]}'
        )
        mock_http.request.return_value = mock_resp
        expected = json.dumps(
            {'foo': 'bar', 'service_key': 'sKey'}, sort_keys=True
        ).encode('utf-8')
        with patch('%s.urllib3.PoolManager' % pbm) as mock_pm:
            mock_pm.return_value = mock_http
            with pytest.raises(RuntimeError):
                self.cls._send_event('sKey', {'foo': 'bar'})
        assert mock_http.mock_calls == [
            call.request(
                'POST', self.cls.pd_url,
                headers={'Content-type': 'application/json'},
                body=expected
            )
        ]


class TestEventDict(PagerDutyV1Tester):

    def test_no_account_alias(self):
        assert self.cls._event_dict() == {
            'incident_key': 'iKey',
            'details': {
                'region': 'rname'
            },
            'client': 'awslimitchecker'
        }

    def test_with_account_alias(self):
        self.cls._account_alias = 'myAcct'
        assert self.cls._event_dict() == {
            'incident_key': 'iKey',
            'details': {
                'region': 'rname',
                'account_alias': 'myAcct'
            },
            'client': 'awslimitchecker'
        }


class TestOnSuccess(PagerDutyV1Tester):

    def test_happy_path(self):
        self.cls._service_key_crit = 'cKey'
        self.cls._service_key_warn = 'wKey'
        self.cls._account_alias = 'myAcct'
        with patch('%s._event_dict' % pb, autospec=True) as m_ed:
            m_ed.return_value = {'event': 'dict', 'details': {}}
            with patch('%s._send_event' % pb, autospec=True) as m_send:
                self.cls.on_success(duration=12.34567)
        assert m_ed.mock_calls == [call(self.cls)]
        assert m_send.mock_calls == [
            call(self.cls, 'cKey', {
                'event': 'dict',
                'details': {
                    'duration_seconds': 12.34567
                },
                'event_type': 'resolve',
                'description': 'awslimitchecker in myAcct rname found '
                               'no problems; run completed in 12.35 '
                               'seconds'
            }),
            call(self.cls, 'wKey', {
                'event': 'dict',
                'details': {
                    'duration_seconds': 12.34567
                },
                'event_type': 'resolve',
                'description': 'awslimitchecker in myAcct rname found '
                               'no problems; run completed in 12.35 '
                               'seconds'
            })
        ]

    def test_no_duration(self):
        self.cls._service_key_crit = 'cKey'
        self.cls._service_key_warn = 'wKey'
        self.cls._account_alias = 'myAcct'
        with patch('%s._event_dict' % pb, autospec=True) as m_ed:
            m_ed.return_value = {'event': 'dict', 'details': {}}
            with patch('%s._send_event' % pb, autospec=True) as m_send:
                self.cls.on_success()
        assert m_ed.mock_calls == [call(self.cls)]
        assert m_send.mock_calls == [
            call(self.cls, 'cKey', {
                'event': 'dict',
                'details': {},
                'event_type': 'resolve',
                'description': 'awslimitchecker in myAcct rname found '
                               'no problems'
            }),
            call(self.cls, 'wKey', {
                'event': 'dict',
                'details': {},
                'event_type': 'resolve',
                'description': 'awslimitchecker in myAcct rname found '
                               'no problems'
            })
        ]

    def test_no_account_alias(self):
        self.cls._service_key_crit = 'cKey'
        self.cls._service_key_warn = 'wKey'
        with patch('%s._event_dict' % pb, autospec=True) as m_ed:
            m_ed.return_value = {'event': 'dict', 'details': {}}
            with patch('%s._send_event' % pb, autospec=True) as m_send:
                self.cls.on_success(duration=12.3)
        assert m_ed.mock_calls == [call(self.cls)]
        assert m_send.mock_calls == [
            call(self.cls, 'cKey', {
                'event': 'dict',
                'details': {
                    'duration_seconds': 12.3
                },
                'event_type': 'resolve',
                'description': 'awslimitchecker in rname found '
                               'no problems; run completed in '
                               '12.30 seconds'
            }),
            call(self.cls, 'wKey', {
                'event': 'dict',
                'details': {
                    'duration_seconds': 12.3
                },
                'event_type': 'resolve',
                'description': 'awslimitchecker in rname found '
                               'no problems; run completed in '
                               '12.30 seconds'
            })
        ]

    def test_no_service_key_warn(self):
        self.cls._service_key_crit = 'cKey'
        self.cls._account_alias = 'myAcct'
        with patch('%s._event_dict' % pb, autospec=True) as m_ed:
            m_ed.return_value = {'event': 'dict', 'details': {}}
            with patch('%s._send_event' % pb, autospec=True) as m_send:
                self.cls.on_success(duration=12.3)
        assert m_ed.mock_calls == [call(self.cls)]
        assert m_send.mock_calls == [
            call(self.cls, 'cKey', {
                'event': 'dict',
                'details': {
                    'duration_seconds': 12.3
                },
                'event_type': 'resolve',
                'description': 'awslimitchecker in myAcct rname found '
                               'no problems; run completed in '
                               '12.30 seconds'
            })
        ]


class TestProblemsDict(PagerDutyV1Tester):

    def test_happy_path(self):
        mock_l1 = Mock()
        type(mock_l1).name = 'l1'
        mock_l1.get_warnings.return_value = ['w1']
        mock_l1.get_criticals.return_value = []
        mock_l2 = Mock()
        type(mock_l2).name = 'l2'
        mock_l2.get_warnings.return_value = []
        mock_l2.get_criticals.return_value = []
        mock_l3 = Mock()
        type(mock_l3).name = 'l3'
        mock_l3.get_warnings.return_value = ['w2', 'w3']
        mock_l3.get_criticals.return_value = ['c1', 'c2']
        problems = {
            'S1': {
                'l1': mock_l1,
                'l2': mock_l2
            },
            'S2': {
                'l3': mock_l3
            }
        }
        expected = {
            'S1': {
                'l1': 'S1/l1',
                'l2': 'S1/l2'
            },
            'S2': {
                'l3': 'S2/l3'
            }
        }

        def se_ist(svc, limit, crits, warns, colorize=False):
            return '', '%s/%s' % (svc, limit.name)

        with patch('%s.issue_string_tuple' % pbm) as m_ist:
            m_ist.side_effect = se_ist
            wc, cc, d = self.cls._problems_dict(problems)
        assert wc == 3
        assert cc == 2
        assert d == expected
        assert m_ist.mock_calls == [
            call('S1', mock_l1, [], ['w1'], colorize=False),
            call('S1', mock_l2, [], [], colorize=False),
            call(
                'S2', mock_l3, ['c1', 'c2'], ['w2', 'w3'],
                colorize=False
            )
        ]


class TestOnCritical(PagerDutyV1Tester):

    def test_criticals(self):
        self.cls._account_alias = 'aAlias'
        self.cls._service_key_crit = 'cKey'
        data = {'event': 'data', 'details': {}}
        expected = {
            'event': 'data',
            'event_type': 'trigger',
            'description': 'awslimitchecker in aAlias rname ran in '
                           '12.35 seconds and crossed 2 CRITICAL '
                           'thresholds and 1 WARNING thresholds',
            'details': {
                'duration_seconds': 12.34567,
                'limits': {'foo': 'bar'}
            }
        }
        with patch.multiple(
            pb,
            autospec=True,
            _event_dict=DEFAULT,
            _problems_dict=DEFAULT,
            _send_event=DEFAULT
        ) as mocks:
            mocks['_event_dict'].return_value = data
            mocks['_problems_dict'].return_value = (
                1, 2, {'foo': 'bar'}
            )
            self.cls.on_critical({'p': 'd'}, '', duration=12.34567)
        assert mocks['_event_dict'].mock_calls == [call(self.cls)]
        assert mocks['_problems_dict'].mock_calls == [
            call(self.cls, {'p': 'd'})
        ]
        assert mocks['_send_event'].mock_calls == [
            call(self.cls, 'cKey', expected)
        ]

    def test_no_warnings_no_duration(self):
        self.cls._account_alias = 'aAlias'
        self.cls._service_key_crit = 'cKey'
        data = {'event': 'data', 'details': {}}
        expected = {
            'event': 'data',
            'event_type': 'trigger',
            'description': 'awslimitchecker in aAlias rname crossed '
                           '2 CRITICAL thresholds',
            'details': {
                'limits': {'foo': 'bar'}
            }
        }
        with patch.multiple(
            pb,
            autospec=True,
            _event_dict=DEFAULT,
            _problems_dict=DEFAULT,
            _send_event=DEFAULT
        ) as mocks:
            mocks['_event_dict'].return_value = data
            mocks['_problems_dict'].return_value = (
                0, 2, {'foo': 'bar'}
            )
            self.cls.on_critical({'p': 'd'}, '')
        assert mocks['_event_dict'].mock_calls == [call(self.cls)]
        assert mocks['_problems_dict'].mock_calls == [
            call(self.cls, {'p': 'd'})
        ]
        assert mocks['_send_event'].mock_calls == [
            call(self.cls, 'cKey', expected)
        ]

    def test_exception_no_account_alias(self):
        self.cls._service_key_crit = 'cKey'
        data = {'event': 'data', 'details': {}}
        exc = RuntimeError('foo')
        expected = {
            'event': 'data',
            'event_type': 'trigger',
            'description': 'awslimitchecker in rname ran in '
                           '12.30 seconds and failed with an '
                           'exception: %s' % exc.__repr__(),
            'details': {
                'duration_seconds': 12.3,
                'exception': exc.__repr__()}
        }
        with patch.multiple(
            pb,
            autospec=True,
            _event_dict=DEFAULT,
            _problems_dict=DEFAULT,
            _send_event=DEFAULT
        ) as mocks:
            mocks['_event_dict'].return_value = data
            mocks['_problems_dict'].return_value = (
                1, 2, {'foo': 'bar'}
            )
            self.cls.on_critical(None, None, exc=exc, duration=12.3)
        assert mocks['_event_dict'].mock_calls == [call(self.cls)]
        assert mocks['_problems_dict'].mock_calls == []
        assert mocks['_send_event'].mock_calls == [
            call(self.cls, 'cKey', expected)
        ]


class TestOnWarning(PagerDutyV1Tester):

    def test_duration_alias(self):
        self.cls._account_alias = 'aAlias'
        self.cls._service_key_warn = 'wKey'
        data = {'event': 'data', 'details': {}}
        expected = {
            'event': 'data',
            'event_type': 'trigger',
            'description': 'awslimitchecker in aAlias rname ran in '
                           '12.35 seconds and crossed 1 WARNING '
                           'thresholds',
            'details': {
                'duration_seconds': 12.34567,
                'limits': {'foo': 'bar'}
            }
        }
        with patch.multiple(
            pb,
            autospec=True,
            _event_dict=DEFAULT,
            _problems_dict=DEFAULT,
            _send_event=DEFAULT
        ) as mocks:
            mocks['_event_dict'].return_value = data
            mocks['_problems_dict'].return_value = (
                1, 0, {'foo': 'bar'}
            )
            self.cls.on_warning({'p': 'd'}, '', duration=12.34567)
        assert mocks['_event_dict'].mock_calls == [call(self.cls)]
        assert mocks['_problems_dict'].mock_calls == [
            call(self.cls, {'p': 'd'})
        ]
        assert mocks['_send_event'].mock_calls == [
            call(self.cls, 'wKey', expected)
        ]

    def test_no_duration_no_alias(self):
        self.cls._service_key_warn = 'wKey'
        data = {'event': 'data', 'details': {}}
        expected = {
            'event': 'data',
            'event_type': 'trigger',
            'description': 'awslimitchecker in rname crossed '
                           '1 WARNING thresholds',
            'details': {
                'limits': {'foo': 'bar'}
            }
        }
        with patch.multiple(
            pb,
            autospec=True,
            _event_dict=DEFAULT,
            _problems_dict=DEFAULT,
            _send_event=DEFAULT
        ) as mocks:
            mocks['_event_dict'].return_value = data
            mocks['_problems_dict'].return_value = (
                1, 0, {'foo': 'bar'}
            )
            self.cls.on_warning({'p': 'd'}, '')
        assert mocks['_event_dict'].mock_calls == [call(self.cls)]
        assert mocks['_problems_dict'].mock_calls == [
            call(self.cls, {'p': 'd'})
        ]
        assert mocks['_send_event'].mock_calls == [
            call(self.cls, 'wKey', expected)
        ]
