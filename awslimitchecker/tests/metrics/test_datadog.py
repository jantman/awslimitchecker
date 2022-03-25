"""
awslimitchecker/tests/metrics/test_datadog.py

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
from awslimitchecker.metrics import Datadog
import pytest
from freezegun import freeze_time

if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import Mock, patch, call
else:
    from unittest.mock import Mock, patch, call


pbm = 'awslimitchecker.metrics.datadog'
pb = '%s.Datadog' % pbm


class TestInit(object):

    @patch.dict('os.environ', {}, clear=True)
    def test_happy_path(self):
        mock_http = Mock()
        with patch('%s.urllib3.PoolManager' % pbm, autospec=True) as m_pm:
            m_pm.return_value = mock_http
            with patch('%s._validate_auth' % pb, autospec=True) as m_va:
                cls = Datadog(
                    'foo', api_key='1234', extra_tags='foo,bar,baz:blam'
                )
        assert cls._region_name == 'foo'
        assert cls._duration == 0.0
        assert cls._limits == []
        assert cls._api_key == '1234'
        assert cls._prefix == 'awslimitchecker.'
        assert cls._tags == [
            'region:foo', 'foo', 'bar', 'baz:blam'
        ]
        assert cls._http == mock_http
        assert cls._host == 'https://api.datadoghq.com'
        assert m_pm.mock_calls == [call()]
        assert m_va.mock_calls == [call(cls, '1234')]

    @patch.dict('os.environ', {}, clear=True)
    def test_host_param(self):
        mock_http = Mock()
        with patch('%s.urllib3.PoolManager' % pbm, autospec=True) as m_pm:
            m_pm.return_value = mock_http
            with patch('%s._validate_auth' % pb, autospec=True) as m_va:
                cls = Datadog(
                    'foo', api_key='1234', extra_tags='foo,bar,baz:blam',
                    host='http://foo.bar'
                )
        assert cls._region_name == 'foo'
        assert cls._duration == 0.0
        assert cls._limits == []
        assert cls._api_key == '1234'
        assert cls._prefix == 'awslimitchecker.'
        assert cls._tags == [
            'region:foo', 'foo', 'bar', 'baz:blam'
        ]
        assert cls._http == mock_http
        assert cls._host == 'http://foo.bar'
        assert m_pm.mock_calls == [call()]
        assert m_va.mock_calls == [call(cls, '1234')]

    @patch.dict('os.environ', {'DATADOG_HOST': 'http://dd.host'}, clear=True)
    def test_host_env_var(self):
        mock_http = Mock()
        with patch('%s.urllib3.PoolManager' % pbm, autospec=True) as m_pm:
            m_pm.return_value = mock_http
            with patch('%s._validate_auth' % pb, autospec=True) as m_va:
                cls = Datadog(
                    'foo', api_key='1234', extra_tags='foo,bar,baz:blam',
                    host='http://foo.bar'
                )
        assert cls._region_name == 'foo'
        assert cls._duration == 0.0
        assert cls._limits == []
        assert cls._api_key == '1234'
        assert cls._prefix == 'awslimitchecker.'
        assert cls._tags == [
            'region:foo', 'foo', 'bar', 'baz:blam'
        ]
        assert cls._http == mock_http
        assert cls._host == 'http://dd.host'
        assert m_pm.mock_calls == [call()]
        assert m_va.mock_calls == [call(cls, '1234')]

    @patch.dict('os.environ', {'DATADOG_API_KEY': '5678'}, clear=True)
    def test_api_key_env_var(self):
        mock_http = Mock()
        with patch('%s.urllib3.PoolManager' % pbm, autospec=True) as m_pm:
            m_pm.return_value = mock_http
            with patch('%s._validate_auth' % pb, autospec=True) as m_va:
                cls = Datadog(
                    'foo', prefix='myprefix.'
                )
        assert cls._region_name == 'foo'
        assert cls._duration == 0.0
        assert cls._limits == []
        assert cls._api_key == '5678'
        assert cls._prefix == 'myprefix.'
        assert cls._tags == [
            'region:foo'
        ]
        assert cls._http == mock_http
        assert cls._host == 'https://api.datadoghq.com'
        assert m_pm.mock_calls == [call()]
        assert m_va.mock_calls == [call(cls, '5678')]

    @patch.dict('os.environ', {}, clear=True)
    def test_no_api_key(self):
        mock_http = Mock()
        with patch('%s.urllib3.PoolManager' % pbm, autospec=True) as m_pm:
            m_pm.return_value = mock_http
            with patch('%s._validate_auth' % pb, autospec=True) as m_va:
                with pytest.raises(RuntimeError) as exc:
                    Datadog(
                        'foo', extra_tags='foo,bar,baz:blam', prefix='myprefix.'
                    )
        assert str(exc.value) == 'ERROR: Datadog metrics provider ' \
                                 'requires datadog API key.'
        assert m_pm.mock_calls == []
        assert m_va.mock_calls == []


class DatadogTester(object):

    def setup(self):
        with patch('%s.__init__' % pb) as m_init:
            m_init.return_value = None
            self.cls = Datadog()
            self.cls._host = 'https://api.datadoghq.com'


class TestValidateAuth(DatadogTester):

    def test_happy_path(self):
        mock_http = Mock()
        mock_resp = Mock(status=200, data=b'{"success": "ok"}')
        mock_http.request.return_value = mock_resp
        self.cls._http = mock_http
        self.cls._validate_auth('1234')
        assert mock_http.mock_calls == [
            call.request(
                'GET',
                'https://api.datadoghq.com/api/v1/validate?api_key=1234'
            )
        ]

    def test_non_default_host(self):
        mock_http = Mock()
        mock_resp = Mock(status=200, data=b'{"success": "ok"}')
        mock_http.request.return_value = mock_resp
        self.cls._http = mock_http
        self.cls._host = 'http://my.host'
        self.cls._validate_auth('1234')
        assert mock_http.mock_calls == [
            call.request(
                'GET',
                'http://my.host/api/v1/validate?api_key=1234'
            )
        ]

    def test_failure(self):
        mock_http = Mock()
        mock_resp = Mock(status=401, data='{"success": "NO"}')
        mock_http.request.return_value = mock_resp
        self.cls._http = mock_http
        with pytest.raises(RuntimeError) as exc:
            self.cls._validate_auth('1234')
        assert str(exc.value) == 'ERROR: Datadog API key validation failed ' \
                                 'with HTTP 401: {"success": "NO"}'
        assert mock_http.mock_calls == [
            call.request(
                'GET',
                'https://api.datadoghq.com/api/v1/validate?api_key=1234'
            )
        ]


class TestNameForMetric(DatadogTester):

    def test_simple(self):
        self.cls._prefix = 'foobar.'
        assert self.cls._name_for_metric(
            'Service Name*', 'limit NAME .'
        ) == 'foobar.service_name_.limit_name_'


class TestFlush(DatadogTester):

    @freeze_time("2016-12-16 10:40:42", tz_offset=0, auto_tick_seconds=6)
    def test_happy_path(self):
        self.cls._prefix = 'prefix.'
        self.cls._tags = ['tag1', 'tag:2']
        self.cls._limits = []
        self.cls._api_key = 'myKey'
        self.cls.set_run_duration(123.45)
        limA = Mock(
            name='limitA', service=Mock(service_name='SVC1')
        )
        type(limA).name = 'limitA'
        limA.get_current_usage.return_value = []
        limA.get_limit.return_value = None
        self.cls.add_limit(limA)
        limB = Mock(
            name='limitB', service=Mock(service_name='SVC1')
        )
        type(limB).name = 'limitB'
        mocku = Mock()
        mocku.get_value.return_value = 6
        limB.get_current_usage.return_value = [mocku]
        limB.get_limit.return_value = 10
        self.cls.add_limit(limB)
        mock_http = Mock()
        mock_resp = Mock(status=200, data='{"status": "ok"}')
        mock_http.request.return_value = mock_resp
        self.cls._http = mock_http
        self.cls.flush()
        ts = 1481884842
        expected = {
            'series': [
                {
                    'metric': 'prefix.runtime',
                    'points': [[ts, 123.45]],
                    'type': 'gauge',
                    'tags': ['tag1', 'tag:2']
                },
                {
                    'metric': 'prefix.svc1.limita.max_usage',
                    'points': [[ts, 0]],
                    'type': 'gauge',
                    'tags': ['tag1', 'tag:2']
                },
                {
                    'metric': 'prefix.svc1.limitb.max_usage',
                    'points': [[ts, 6]],
                    'type': 'gauge',
                    'tags': ['tag1', 'tag:2']
                },
                {
                    'metric': 'prefix.svc1.limitb.limit',
                    'points': [[ts, 10]],
                    'type': 'gauge',
                    'tags': ['tag1', 'tag:2']
                }
            ]
        }
        assert len(mock_http.mock_calls) == 1
        c = mock_http.mock_calls[0]
        assert c[0] == 'request'
        assert c[1] == (
            'POST', 'https://api.datadoghq.com/api/v1/series?api_key=myKey'
        )
        assert len(c[2]) == 2
        assert c[2]['headers'] == {'Content-type': 'application/json'}
        assert json.loads(c[2]['body'].decode()) == expected

    @freeze_time("2016-12-16 10:40:42", tz_offset=0, auto_tick_seconds=6)
    def test_api_error_non_default_host(self):
        self.cls._prefix = 'prefix.'
        self.cls._tags = ['tag1', 'tag:2']
        self.cls._limits = []
        self.cls._api_key = 'myKey'
        self.cls._host = 'http://my.host'
        self.cls.set_run_duration(123.45)
        limA = Mock(
            name='limitA', service=Mock(service_name='SVC1')
        )
        type(limA).name = 'limitA'
        limA.get_current_usage.return_value = []
        limA.get_limit.return_value = None
        self.cls.add_limit(limA)
        limB = Mock(
            name='limitB', service=Mock(service_name='SVC1')
        )
        type(limB).name = 'limitB'
        mocku = Mock()
        mocku.get_value.return_value = 6
        limB.get_current_usage.return_value = [mocku]
        limB.get_limit.return_value = 10
        self.cls.add_limit(limB)
        mock_http = Mock()
        mock_resp = Mock(status=503, data='{"status": "NG"}')
        mock_http.request.return_value = mock_resp
        self.cls._http = mock_http
        with pytest.raises(RuntimeError) as exc:
            self.cls.flush()
        assert str(exc.value) == 'ERROR sending metrics to Datadog; API ' \
                                 'responded HTTP 503: {"status": "NG"}'
        ts = 1481884842
        expected = {
            'series': [
                {
                    'metric': 'prefix.runtime',
                    'points': [[ts, 123.45]],
                    'type': 'gauge',
                    'tags': ['tag1', 'tag:2']
                },
                {
                    'metric': 'prefix.svc1.limita.max_usage',
                    'points': [[ts, 0]],
                    'type': 'gauge',
                    'tags': ['tag1', 'tag:2']
                },
                {
                    'metric': 'prefix.svc1.limitb.max_usage',
                    'points': [[ts, 6]],
                    'type': 'gauge',
                    'tags': ['tag1', 'tag:2']
                },
                {
                    'metric': 'prefix.svc1.limitb.limit',
                    'points': [[ts, 10]],
                    'type': 'gauge',
                    'tags': ['tag1', 'tag:2']
                }
            ]
        }
        assert len(mock_http.mock_calls) == 1
        c = mock_http.mock_calls[0]
        assert c[0] == 'request'
        assert c[1] == (
            'POST', 'http://my.host/api/v1/series?api_key=myKey'
        )
        assert len(c[2]) == 2
        assert c[2]['headers'] == {'Content-type': 'application/json'}
        assert json.loads(c[2]['body'].decode()) == expected
