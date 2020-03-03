"""
awslimitchecker/tests/test_limit.py

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

import pytest
import sys
from awslimitchecker.limit import (
    AwsLimit, AwsLimitUsage, SOURCE_DEFAULT, SOURCE_OVERRIDE,
    SOURCE_TA, SOURCE_API, SOURCE_QUOTAS
)
from awslimitchecker.services.base import _AwsService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock


class AwsLimitTester(object):

    def setup(self):
        self.mock_svc = Mock(spec_set=_AwsService)
        type(self.mock_svc).service_name = 'mysname'
        type(self.mock_svc).quotas_service_code = 'qscode'


class TestInit(AwsLimitTester):

    def test_simple(self):
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            3,
            7,
            11
        )
        assert limit.name == 'limitname'
        assert limit.service == self.mock_svc
        assert limit.default_limit == 3
        assert limit.limit_type is None
        assert limit.limit_subtype is None
        assert limit.limit_override is None
        assert limit.override_ta is True
        assert limit.ta_limit is None
        assert limit.ta_unlimited is False
        assert limit.api_limit is None
        assert limit.def_warning_threshold == 7
        assert limit.def_critical_threshold == 11
        assert limit._ta_service_name is None
        assert limit._ta_limit_name is None
        assert limit._quotas_service_code is None
        assert limit._quotas_name is None
        assert limit._quotas_unit == 'None'
        assert limit.quotas_limit is None
        assert limit.quotas_unit_converter is None

    def test_ta_names(self):
        m_foo = Mock()
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            3,
            7,
            11,
            ta_service_name='foo',
            ta_limit_name='bar',
            quotas_service_code='baz',
            quotas_name='blam',
            quotas_unit='blarg',
            quotas_unit_converter=m_foo
        )
        assert limit.name == 'limitname'
        assert limit.service == self.mock_svc
        assert limit.default_limit == 3
        assert limit.limit_type is None
        assert limit.limit_subtype is None
        assert limit.limit_override is None
        assert limit.override_ta is True
        assert limit.ta_limit is None
        assert limit.api_limit is None
        assert limit.def_warning_threshold == 7
        assert limit.def_critical_threshold == 11
        assert limit._ta_service_name == 'foo'
        assert limit._ta_limit_name == 'bar'
        assert limit._quotas_service_code == 'baz'
        assert limit._quotas_name == 'blam'
        assert limit._quotas_unit == 'blarg'
        assert limit.quotas_limit is None
        assert limit.quotas_unit_converter == m_foo

    def test_valueerror(self):
        with pytest.raises(ValueError) as excinfo:
            AwsLimit(
                'limitname',
                self.mock_svc,
                3,
                11,
                7
            )
        if sys.version_info[0] > 2:
            msg = excinfo.value.args[0]
        else:
            msg = excinfo.value.message
        assert msg == "critical threshold must be greater " \
            "than warning threshold"

    def test_type(self):
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            1,
            6,
            12,
            limit_type='foo',
            limit_subtype='bar',
        )
        assert limit.name == 'limitname'
        assert limit.service == self.mock_svc
        assert limit.default_limit == 1
        assert limit.limit_type == 'foo'
        assert limit.limit_subtype == 'bar'
        assert limit.limit_override is None
        assert limit.override_ta is True
        assert limit.def_warning_threshold == 6
        assert limit.def_critical_threshold == 12


class TestSetLimitOverride(AwsLimitTester):

    def test_simple(self):
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            3,
            1,
            2
        )
        limit.set_limit_override(10)
        assert limit.limit_override == 10
        assert limit.default_limit == 3
        assert limit.override_ta is True

    def test_ta_False(self):
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            3,
            1,
            2
        )
        limit.set_limit_override(1, override_ta=False)
        assert limit.limit_override == 1
        assert limit.default_limit == 3
        assert limit.override_ta is False


class TestSetTaLimit(AwsLimitTester):

    def test_simple(self):
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            3,
            1,
            2
        )
        assert limit.ta_limit is None
        limit._set_ta_limit(10)
        assert limit.ta_limit == 10

    def test_set_ta_unlimited(self):
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            3,
            1,
            2
        )
        assert limit.ta_limit is None
        assert limit.ta_unlimited is False
        limit._set_ta_unlimited()
        assert limit.ta_limit is None
        assert limit.ta_unlimited is True


class TestSetApiLimit(AwsLimitTester):

    def test_simple(self):
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            3,
            1,
            2
        )
        assert limit.api_limit is None
        limit._set_api_limit(10)
        assert limit.api_limit == 10


class TestSetQuotasLimit(AwsLimitTester):

    def test_simple(self):
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            3,
            1,
            2
        )
        assert limit.quotas_limit is None
        limit._set_quotas_limit(10.1)
        assert limit.quotas_limit == 10.1


class TestAddCurrentUsage(AwsLimitTester):

    def test_simple(self):
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            3,
            1,
            2
        )
        assert limit._current_usage == []
        limit._add_current_usage(2)
        assert len(limit.get_current_usage()) == 1
        assert limit._current_usage[0].get_value() == 2
        limit._add_current_usage(4)
        assert len(limit.get_current_usage()) == 2
        assert limit._current_usage[1].get_value() == 4


class TestGetCurrentUsage(AwsLimitTester):

    def test_simple(self):
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            3,
            1,
            2
        )
        limit._current_usage = 2
        assert limit.get_current_usage() == 2

    def test_str_none(self):
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            3,
            1,
            2
        )
        assert limit.get_current_usage_str() == '<unknown>'

    def test_str(self):
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            3,
            1,
            2
        )
        limit._add_current_usage(4)
        assert limit.get_current_usage_str() == '4'

    def test_str_id(self):
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            3,
            1,
            2
        )
        limit._add_current_usage(4, resource_id='foobar')
        assert limit.get_current_usage_str() == 'foobar=4'

    def test_str_multi(self):
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            3,
            1,
            2
        )
        limit._add_current_usage(4)
        limit._add_current_usage(3)
        limit._add_current_usage(2)
        assert limit.get_current_usage_str() == 'max: 4 (2, 3, 4)'

    def test_str_multi_id(self):
        limit = AwsLimit(
            'limitname',
            self.mock_svc,
            3,
            1,
            2
        )
        limit._add_current_usage(4, resource_id='foo4bar')
        limit._add_current_usage(3, resource_id='foo3bar')
        limit._add_current_usage(2, resource_id='foo2bar')
        assert limit.get_current_usage_str() == 'max: foo4bar=4 (foo2bar=2, ' \
            'foo3bar=3, foo4bar=4)'


class TestGetLimit(AwsLimitTester):

    def test_default(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        assert limit.get_limit() == 3

    def test_override(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit.set_limit_override(55)
        assert limit.get_limit() == 55

    def test_ta(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit.set_limit_override(55, override_ta=False)
        limit._set_ta_limit(40)
        assert limit.get_limit() == 40

    def test_ta_unlimited(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit.set_limit_override(55, override_ta=False)
        limit._set_ta_unlimited()
        assert limit.get_limit() is None

    def test_api(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit._set_api_limit(40)
        assert limit.get_limit() == 40

    def test_api_ta(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit._set_ta_limit(40)
        limit._set_api_limit(11)
        assert limit.get_limit() == 11

    def test_api_override(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit.set_limit_override(55)
        limit._set_api_limit(40)
        assert limit.get_limit() == 55

    def test_api_override_ta(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit.set_limit_override(55)
        limit._set_ta_limit(40)
        limit._set_api_limit(11)
        assert limit.get_limit() == 55

    def test_quotas(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit._set_quotas_limit(12)
        assert limit.get_limit() == 12

    def test_quotas_api_ta_override(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit.set_limit_override(55)
        limit._set_ta_limit(40)
        limit._set_api_limit(11)
        limit._set_quotas_limit(12)
        assert limit.get_limit() == 55


class TestGetLimitSource(AwsLimitTester):

    def test_default(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        assert limit.get_limit_source() == SOURCE_DEFAULT

    def test_override(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit.set_limit_override(55)
        assert limit.get_limit_source() == SOURCE_OVERRIDE

    def test_override_no_override_ta(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit.set_limit_override(55, override_ta=False)
        limit._set_ta_limit(40)
        assert limit.get_limit_source() == SOURCE_TA

    def test_override_with_ta(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit.set_limit_override(55)
        limit._set_ta_limit(40)
        assert limit.get_limit_source() == SOURCE_OVERRIDE

    def test_ta(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit._set_ta_limit(40)
        assert limit.get_limit_source() == SOURCE_TA

    def test_ta_unlimited(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit._set_ta_unlimited()
        assert limit.get_limit_source() == SOURCE_TA

    def test_api(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit._set_api_limit(40)
        assert limit.get_limit_source() == SOURCE_API

    def test_api_override(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit._set_api_limit(40)
        limit.set_limit_override(55)
        assert limit.get_limit_source() == SOURCE_OVERRIDE

    def test_api_ta(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit._set_api_limit(40)
        limit._set_ta_limit(41)
        assert limit.get_limit_source() == SOURCE_API

    def test_api_override_ta(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit._set_api_limit(40)
        limit._set_ta_limit(41)
        limit.set_limit_override(55)
        assert limit.get_limit_source() == SOURCE_OVERRIDE

    def test_quotas(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit._set_quotas_limit(40)
        assert limit.get_limit_source() == SOURCE_QUOTAS

    def test_quotas_api(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit._set_api_limit(40)
        limit._set_quotas_limit(50)
        assert limit.get_limit_source() == SOURCE_API

    def test_quotas_override(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit._set_quotas_limit(40)
        limit.set_limit_override(55)
        assert limit.get_limit_source() == SOURCE_OVERRIDE

    def test_quotas_ta(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit._set_quotas_limit(40)
        limit._set_ta_limit(41)
        assert limit.get_limit_source() == SOURCE_QUOTAS

    def test_quotas_override_ta(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit._set_quotas_limit(40)
        limit._set_ta_limit(41)
        limit.set_limit_override(55)
        assert limit.get_limit_source() == SOURCE_OVERRIDE

    def test_quotas_api_override_ta(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        limit._set_quotas_limit(10.2)
        limit._set_api_limit(40)
        limit._set_ta_limit(41)
        limit.set_limit_override(55)
        assert limit.get_limit_source() == SOURCE_OVERRIDE


class TestCheckThresholds(AwsLimitTester):

    def test_pct(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        u1 = AwsLimitUsage(limit, 4, resource_id='foo4bar')
        u2 = AwsLimitUsage(limit, 3, resource_id='foo3bar')
        u3 = AwsLimitUsage(limit, 2, resource_id='foo2bar')
        limit._current_usage = [u1, u2, u3]
        with patch('awslimitchecker.limit.AwsLimit.'
                   '_get_thresholds') as mock_get_thresh:
            with patch('awslimitchecker.limit.AwsLimit.get_'
                       'limit') as mock_get_limit:
                mock_get_thresh.return_value = (None, 40, None, 80)
                mock_get_limit.return_value = 100
                res = limit.check_thresholds()
        assert res is True
        assert limit._warnings == []
        assert limit._criticals == []
        assert mock_get_thresh.mock_calls == [call()]
        assert mock_get_limit.mock_calls == [call(), call(), call()]

    def test_ta_unlimited(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        u1 = AwsLimitUsage(limit, 4, resource_id='foo4bar')
        u2 = AwsLimitUsage(limit, 3, resource_id='foo3bar')
        u3 = AwsLimitUsage(limit, 2, resource_id='foo2bar')
        limit._current_usage = [u1, u2, u3]
        limit._set_ta_unlimited()
        with patch('awslimitchecker.limit.AwsLimit.'
                   '_get_thresholds') as mock_get_thresh:
            with patch('awslimitchecker.limit.AwsLimit.get_'
                       'limit') as mock_get_limit:
                mock_get_thresh.return_value = (None, 40, None, 80)
                mock_get_limit.return_value = None
                res = limit.check_thresholds()
        assert res is True
        assert limit._warnings == []
        assert limit._criticals == []
        assert mock_get_thresh.mock_calls == [call()]
        assert mock_get_limit.mock_calls == [call(), call(), call()]

    def test_ta_zero(self):
        limit = AwsLimit('limitname', self.mock_svc, 3, 1, 2)
        u1 = AwsLimitUsage(limit, 4, resource_id='foo4bar')
        u2 = AwsLimitUsage(limit, 3, resource_id='foo3bar')
        u3 = AwsLimitUsage(limit, 2, resource_id='foo2bar')
        limit._current_usage = [u1, u2, u3]
        limit._set_ta_unlimited()
        with patch('awslimitchecker.limit.AwsLimit.'
                   '_get_thresholds') as mock_get_thresh:
            with patch('awslimitchecker.limit.AwsLimit.get_'
                       'limit') as mock_get_limit:
                mock_get_thresh.return_value = (None, 40, None, 80)
                mock_get_limit.return_value = 0
                res = limit.check_thresholds()
        assert res is True
        assert limit._warnings == []
        assert limit._criticals == []
        assert mock_get_thresh.mock_calls == [call()]
        assert mock_get_limit.mock_calls == [call(), call(), call()]

    def test_pct_warn(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 1, 2)
        u1 = AwsLimitUsage(limit, 4, resource_id='foo4bar')
        u2 = AwsLimitUsage(limit, 50, resource_id='foo3bar')
        u3 = AwsLimitUsage(limit, 2, resource_id='foo2bar')
        limit._current_usage = [u1, u2, u3]
        with patch('awslimitchecker.limit.AwsLimit.'
                   '_get_thresholds') as mock_get_thresh:
            with patch('awslimitchecker.limit.AwsLimit.get_'
                       'limit') as mock_get_limit:
                mock_get_thresh.return_value = (None, 40, None, 80)
                mock_get_limit.return_value = 100
                res = limit.check_thresholds()
        assert res is False
        assert limit._warnings == [u2]
        assert limit._criticals == []
        assert mock_get_thresh.mock_calls == [call()]
        assert mock_get_limit.mock_calls == [call(), call(), call()]

    def test_int_warn(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 1, 2)
        u1 = AwsLimitUsage(limit, 4, resource_id='foo4bar')
        u2 = AwsLimitUsage(limit, 1, resource_id='foo3bar')
        u3 = AwsLimitUsage(limit, 2, resource_id='foo2bar')
        limit._current_usage = [u1, u2, u3]
        with patch('awslimitchecker.limit.AwsLimit.'
                   '_get_thresholds') as mock_get_thresh:
            with patch('awslimitchecker.limit.AwsLimit.get_'
                       'limit') as mock_get_limit:
                mock_get_thresh.return_value = (4, 40, 6, 80)
                mock_get_limit.return_value = 100
                res = limit.check_thresholds()
        assert res is False
        assert limit._warnings == [u1]
        assert limit._criticals == []
        assert mock_get_thresh.mock_calls == [call()]
        assert mock_get_limit.mock_calls == [call(), call(), call()]

    def test_int_warn_crit(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 1, 2)
        u1 = AwsLimitUsage(limit, 4, resource_id='foo4bar')
        u2 = AwsLimitUsage(limit, 1, resource_id='foo3bar')
        u3 = AwsLimitUsage(limit, 7, resource_id='foo2bar')
        limit._current_usage = [u1, u2, u3]
        with patch('awslimitchecker.limit.AwsLimit.'
                   '_get_thresholds') as mock_get_thresh:
            with patch('awslimitchecker.limit.AwsLimit.get_'
                       'limit') as mock_get_limit:
                mock_get_thresh.return_value = (4, 40, 6, 80)
                mock_get_limit.return_value = 100
                res = limit.check_thresholds()
        assert res is False
        assert limit._warnings == [u1]
        assert limit._criticals == [u3]
        assert mock_get_thresh.mock_calls == [call()]
        assert mock_get_limit.mock_calls == [call(), call(), call()]

    def test_pct_crit(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 1, 2)
        u1 = AwsLimitUsage(limit, 4, resource_id='foo4bar')
        u2 = AwsLimitUsage(limit, 3, resource_id='foo3bar')
        u3 = AwsLimitUsage(limit, 95, resource_id='foo2bar')
        limit._current_usage = [u1, u2, u3]
        with patch('awslimitchecker.limit.AwsLimit.'
                   '_get_thresholds') as mock_get_thresh:
            with patch('awslimitchecker.limit.AwsLimit.get_'
                       'limit') as mock_get_limit:
                mock_get_thresh.return_value = (None, 40, None, 80)
                mock_get_limit.return_value = 100
                res = limit.check_thresholds()
        assert res is False
        assert limit._warnings == []
        assert limit._criticals == [u3]
        assert mock_get_thresh.mock_calls == [call()]
        assert mock_get_limit.mock_calls == [call(), call(), call()]

    def test_int_crit(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 1, 2)
        u1 = AwsLimitUsage(limit, 9, resource_id='foo4bar')
        u2 = AwsLimitUsage(limit, 3, resource_id='foo3bar')
        u3 = AwsLimitUsage(limit, 95, resource_id='foo2bar')
        limit._current_usage = [u1, u2, u3]
        with patch('awslimitchecker.limit.AwsLimit.'
                   '_get_thresholds') as mock_get_thresh:
            with patch('awslimitchecker.limit.AwsLimit.get_'
                       'limit') as mock_get_limit:
                mock_get_thresh.return_value = (6, 40, 8, 80)
                mock_get_limit.return_value = 100
                res = limit.check_thresholds()
        assert res is False
        assert limit._warnings == []
        assert limit._criticals == [u1, u3]
        assert mock_get_thresh.mock_calls == [call()]
        assert mock_get_limit.mock_calls == [call(), call(), call()]

    def test_pct_warn_crit(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 1, 2)
        u1 = AwsLimitUsage(limit, 50, resource_id='foo4bar')
        u2 = AwsLimitUsage(limit, 3, resource_id='foo3bar')
        u3 = AwsLimitUsage(limit, 95, resource_id='foo2bar')
        limit._current_usage = [u1, u2, u3]
        with patch('awslimitchecker.limit.AwsLimit.'
                   '_get_thresholds') as mock_get_thresh:
            with patch('awslimitchecker.limit.AwsLimit.get_'
                       'limit') as mock_get_limit:
                mock_get_thresh.return_value = (None, 40, None, 80)
                mock_get_limit.return_value = 100
                res = limit.check_thresholds()
        assert res is False
        assert limit._warnings == [u1]
        assert limit._criticals == [u3]
        assert mock_get_thresh.mock_calls == [call()]
        assert mock_get_limit.mock_calls == [call(), call(), call()]


class TestGetWarnings(AwsLimitTester):

    def test_simple(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 1, 2)
        m = Mock()
        limit._warnings = m
        assert limit.get_warnings() == m


class TestGetCriticals(AwsLimitTester):

    def test_simple(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 1, 2)
        m = Mock()
        limit._criticals = m
        assert limit.get_criticals() == m


class TestGetThresholds(AwsLimitTester):

    def test_simple(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 1, 2)
        assert limit._get_thresholds() == (
            None,
            1,
            None,
            2
        )

    def test_overridden(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 88, 99)
        limit.warn_percent = 1
        limit.warn_count = 2
        limit.crit_percent = 3
        limit.crit_count = 4
        assert limit._get_thresholds() == (
            2,
            1,
            4,
            3
        )


class TestSetThresholdOverride(AwsLimitTester):

    def test_set_threshold_override(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 1, 2)
        limit.set_threshold_override(
            warn_percent=1,
            warn_count=2,
            crit_percent=3,
            crit_count=4
        )
        assert limit.warn_percent == 1
        assert limit.warn_count == 2
        assert limit.crit_percent == 3
        assert limit.crit_count == 4


class TestTaServiceName(AwsLimitTester):

    def test_default(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 1, 2)
        assert limit.ta_service_name == 'mysname'

    def test_overridden(self):
        limit = AwsLimit(
            'limitname', self.mock_svc, 100, 1, 2, ta_service_name='foo'
        )
        assert limit.ta_service_name == 'foo'


class TestTaLimitName(AwsLimitTester):

    def test_default(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 1, 2)
        assert limit.ta_limit_name == 'limitname'

    def test_overridden(self):
        limit = AwsLimit(
            'limitname', self.mock_svc, 100, 1, 2, ta_limit_name='foo'
        )
        assert limit.ta_limit_name == 'foo'


class TestQuotasServiceCode(AwsLimitTester):

    def test_default(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 1, 2)
        assert limit.quotas_service_code == 'qscode'

    def test_overridden(self):
        limit = AwsLimit(
            'limitname', self.mock_svc, 100, 1, 2, quotas_service_code='qsc'
        )
        assert limit.quotas_service_code == 'qsc'


class TestQuotaName(AwsLimitTester):

    def test_default(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 1, 2)
        assert limit.quota_name == 'limitname'

    def test_overridden(self):
        limit = AwsLimit(
            'limitname', self.mock_svc, 100, 1, 2, quotas_name='qn'
        )
        assert limit.quota_name == 'qn'


class TestQuotasUnit(AwsLimitTester):

    def test_default(self):
        limit = AwsLimit('limitname', self.mock_svc, 100, 1, 2)
        assert limit.quotas_unit == 'None'


class TestAwsLimitUsage(object):

    def test_init(self):
        mock_limit = Mock(spec_set=AwsLimit)
        u = AwsLimitUsage(
            mock_limit,
            1.23,
        )
        assert u.limit == mock_limit
        assert u.value == 1.23
        assert u.resource_id is None
        assert u.aws_type is None

        u2 = AwsLimitUsage(
            mock_limit,
            3,
            resource_id='foobar',
            aws_type='mytype',
        )
        assert u2.limit == mock_limit
        assert u2.value == 3
        assert u2.resource_id == 'foobar'
        assert u2.aws_type == 'mytype'

    def test_get_value(self):
        mock_limit = Mock(spec_set=AwsLimit)
        u = AwsLimitUsage(
            mock_limit,
            3.456
        )
        assert u.get_value() == 3.456

    def test_repr(self):
        mock_limit = Mock(spec_set=AwsLimit)
        u = AwsLimitUsage(
            mock_limit,
            3.456
        )
        assert str(u) == '3.456'

        u2 = AwsLimitUsage(
            mock_limit,
            3.456,
            resource_id='foobar'
        )
        assert str(u2) == 'foobar=3.456'

    def test_comparable(self):
        mock_limit = Mock(spec_set=AwsLimit)
        u1 = AwsLimitUsage(
            mock_limit,
            3.456
        )
        u2 = AwsLimitUsage(
            mock_limit,
            3
        )
        u3 = AwsLimitUsage(
            mock_limit,
            4
        )
        u1b = AwsLimitUsage(
            mock_limit,
            3.456
        )
        assert u1 == u1b
        assert u1 != u2
        assert u1 < u3
        assert u1 > u2
        assert u1 >= u2
