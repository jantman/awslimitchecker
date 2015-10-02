"""
awslimitchecker/tests/services/test_base.py

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
bugs please submit them at <https://github.com/jantman/awslimitchecker> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

from awslimitchecker.services.base import _AwsService
from awslimitchecker.services import _services
from awslimitchecker.limit import AwsLimit
import pytest
import sys

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock


class AwsServiceTester(_AwsService):
    """class to test non-abstract methods on base class"""

    service_name = 'AwsServiceTester'

    def connect(self):
        pass

    def find_usage(self):
        self._have_usage = True

    def get_limits(self):
        return {'foo': 'bar'}

    def required_iam_permissions(self):
        pass


class Test_AwsService(object):

    @pytest.mark.skipif(sys.version_info != (2, 6), reason='test for py26')
    def test_init_py26(self):
        with pytest.raises(TypeError) as excinfo:
            _AwsService(1, 2)
        assert excinfo.value == "Can't instantiate abstract class " \
            "_AwsService with abstract methods " \
            "connect" \
            ", find_usage" \
            ", get_limits" \
            ", required_iam_permissions"

    @pytest.mark.skipif(sys.version_info != (2, 7), reason='test for py27')
    def test_init_py27(self):
        with pytest.raises(TypeError) as excinfo:
            _AwsService(1, 2)
        assert excinfo.value.message == "Can't instantiate abstract class " \
            "_AwsService with abstract methods " \
            "connect" \
            ", find_usage" \
            ", get_limits" \
            ", required_iam_permissions"

    @pytest.mark.skipif(sys.version_info < (3, 0), reason='test for py3')
    def test_init_py3(self):
        with pytest.raises(NotImplementedError) as excinfo:
            _AwsService(1, 2)
        assert excinfo.value.args[0] == "abstract base class"

    def test_init_subclass(self):
        cls = AwsServiceTester(1, 2)
        assert cls.warning_threshold == 1
        assert cls.critical_threshold == 2
        assert cls.limits == {'foo': 'bar'}
        assert cls.conn is None
        assert cls._have_usage is False
        assert cls.account_id is None
        assert cls.account_role is None
        assert cls.region is None
        assert cls.external_id is None

    def test_init_subclass_sts(self):
        cls = AwsServiceTester(
            1,
            2,
            account_id='012345678912',
            account_role='myrole',
            region='myregion'
        )
        assert cls.warning_threshold == 1
        assert cls.critical_threshold == 2
        assert cls.limits == {'foo': 'bar'}
        assert cls.conn is None
        assert cls._have_usage is False
        assert cls.account_id == '012345678912'
        assert cls.account_role == 'myrole'
        assert cls.region == 'myregion'

    def test_set_limit_override(self):
        mock_limit = Mock(spec_set=AwsLimit)
        type(mock_limit).default_limit = 5
        cls = AwsServiceTester(1, 2)
        cls.limits['foo'] = mock_limit
        cls.set_limit_override('foo', 10)
        assert mock_limit.mock_calls == [
            call.set_limit_override(10, override_ta=True)
        ]

    def test_set_limit_override_keyerror(self):
        mock_limit = Mock(spec_set=AwsLimit)
        type(mock_limit).default_limit = 5
        cls = AwsServiceTester(1, 2)
        cls.limits['foo'] = mock_limit
        with pytest.raises(ValueError) as excinfo:
            cls.set_limit_override('bar', 10)

        if sys.version_info[0] > 2:
            msg = excinfo.value.args[0]
        else:
            msg = excinfo.value.message

        assert msg == "AwsServiceTester service has no " \
            "'bar' limit"
        assert mock_limit.mock_calls == []

    def test_set_ta_limit(self):
        mock_limit = Mock(spec_set=AwsLimit)
        type(mock_limit).default_limit = 5
        cls = AwsServiceTester(1, 2)
        cls.limits['foo'] = mock_limit
        cls._set_ta_limit('foo', 10)
        assert mock_limit.mock_calls == [
            call._set_ta_limit(10)
        ]

    def test_set_ta_limit_keyerror(self):
        mock_limit = Mock(spec_set=AwsLimit)
        type(mock_limit).default_limit = 5
        cls = AwsServiceTester(1, 2)
        cls.limits['foo'] = mock_limit
        with pytest.raises(ValueError) as excinfo:
            cls._set_ta_limit('bar', 10)

        if sys.version_info[0] > 2:
            msg = excinfo.value.args[0]
        else:
            msg = excinfo.value.message

        assert msg == "AwsServiceTester service has no " \
            "'bar' limit"
        assert mock_limit.mock_calls == []

    def test_set_threshold_override(self):
        mock_limit = Mock(spec_set=AwsLimit)
        type(mock_limit).default_limit = 5
        cls = AwsServiceTester(1, 2)
        cls.limits['foo'] = mock_limit
        cls.set_threshold_override(
            'foo',
            warn_percent=10,
            warn_count=12,
            crit_percent=14,
            crit_count=16
        )
        assert mock_limit.mock_calls == [
            call.set_threshold_override(
                warn_percent=10,
                warn_count=12,
                crit_percent=14,
                crit_count=16
            )
        ]

    def test_set_threshold_override_keyerror(self):
        mock_limit = Mock(spec_set=AwsLimit)
        type(mock_limit).default_limit = 5
        cls = AwsServiceTester(1, 2)
        cls.limits['foo'] = mock_limit
        with pytest.raises(ValueError) as excinfo:
            cls.set_threshold_override('bar', warn_percent=10)

        if sys.version_info[0] > 2:
            msg = excinfo.value.args[0]
        else:
            msg = excinfo.value.message

        assert msg == "AwsServiceTester service has no " \
            "'bar' limit"
        assert mock_limit.mock_calls == []

    def test_check_thresholds(self):
        cls = AwsServiceTester(1, 2)
        cls.find_usage()
        mock_limit1 = Mock(spec_set=AwsLimit)
        mock_limit1.check_thresholds.return_value = False
        cls.limits['foo'] = mock_limit1
        mock_limit2 = Mock(spec_set=AwsLimit)
        mock_limit2.check_thresholds.return_value = True
        cls.limits['foo2'] = mock_limit2
        mock_limit3 = Mock(spec_set=AwsLimit)
        mock_limit3.check_thresholds.return_value = True
        cls.limits['foo3'] = mock_limit3
        mock_limit4 = Mock(spec_set=AwsLimit)
        mock_limit4.check_thresholds.return_value = False
        cls.limits['foo4'] = mock_limit4
        mock_find_usage = Mock()
        with patch.object(AwsServiceTester, 'find_usage', mock_find_usage):
            res = cls.check_thresholds()
        assert mock_limit1.mock_calls == [call.check_thresholds()]
        assert mock_limit2.mock_calls == [call.check_thresholds()]
        assert mock_limit3.mock_calls == [call.check_thresholds()]
        assert mock_limit4.mock_calls == [call.check_thresholds()]
        assert res == {'foo': mock_limit1, 'foo4': mock_limit4}
        assert mock_find_usage.mock_calls == []

    def test_check_thresholds_find_usage(self):
        cls = AwsServiceTester(1, 2)
        mock_limit1 = Mock(spec_set=AwsLimit)
        mock_limit1.check_thresholds.return_value = False
        cls.limits['foo'] = mock_limit1
        mock_limit2 = Mock(spec_set=AwsLimit)
        mock_limit2.check_thresholds.return_value = True
        cls.limits['foo2'] = mock_limit2
        mock_limit3 = Mock(spec_set=AwsLimit)
        mock_limit3.check_thresholds.return_value = True
        cls.limits['foo3'] = mock_limit3
        mock_limit4 = Mock(spec_set=AwsLimit)
        mock_limit4.check_thresholds.return_value = False
        cls.limits['foo4'] = mock_limit4
        mock_find_usage = Mock()
        with patch.object(AwsServiceTester, 'find_usage', mock_find_usage):
            res = cls.check_thresholds()
        assert mock_limit1.mock_calls == [call.check_thresholds()]
        assert mock_limit2.mock_calls == [call.check_thresholds()]
        assert mock_limit3.mock_calls == [call.check_thresholds()]
        assert mock_limit4.mock_calls == [call.check_thresholds()]
        assert res == {'foo': mock_limit1, 'foo4': mock_limit4}
        assert mock_find_usage.mock_calls == [call()]


class Test_AwsServiceSubclasses(object):

    def verify_subclass(self, clsname, cls):
        # ensure we set limits in the constructor
        mock_limits = Mock()
        mock_get_limits = Mock()
        mock_get_limits.return_value = mock_limits
        with patch.object(cls, 'get_limits', mock_get_limits):
            inst = cls(3, 7)
        assert inst.limits == mock_limits
        assert mock_get_limits.mock_calls == [call()]
        # ensure service name is changed
        assert inst.service_name != 'baseclass'
        # ensure an IAM permissions list, even if empty
        assert isinstance(inst.required_iam_permissions(), list)
        # ensure warning and critical thresholds
        assert inst.warning_threshold == 3
        assert inst.critical_threshold == 7
        assert inst.account_id is None
        assert inst.account_role is None
        assert inst.region is None

        sts_inst = cls(3, 7, account_id='123', account_role='myrole',
                       region='myregion')
        assert sts_inst.account_id == '123'
        assert sts_inst.account_role == 'myrole'
        assert sts_inst.region == 'myregion'

    def test_subclass_init(self):
        for clsname, cls in _services.items():
            yield "verify_subclass %s" % clsname, \
                self.verify_subclass, clsname, cls
