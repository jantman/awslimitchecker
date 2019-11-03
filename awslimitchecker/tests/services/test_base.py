"""
awslimitchecker/tests/services/test_base.py

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

from awslimitchecker.services.base import _AwsService
from awslimitchecker.limit import AwsLimit
from awslimitchecker.quotas import ServiceQuotasClient
import pytest
import sys

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, PropertyMock
else:
    from unittest.mock import patch, call, Mock, PropertyMock


class AwsServiceTester(_AwsService):
    """class to test non-abstract methods on base class"""

    service_name = 'AwsServiceTester'
    api_name = 'awsservicetester'

    def connect(self):
        pass

    def find_usage(self):
        self._have_usage = True

    def get_limits(self):
        return {'foo': 'bar'}

    def required_iam_permissions(self):
        pass


class Test_AwsService(object):

    @pytest.mark.skipif(sys.version_info != (2, 7), reason='test for py27')
    def test_init_py27(self):
        with pytest.raises(TypeError) as excinfo:
            _AwsService(1, 2, {}, None)
        assert excinfo.value.message == "Can't instantiate abstract class " \
            "_AwsService with abstract methods " \
            "connect" \
            ", find_usage" \
            ", get_limits" \
            ", required_iam_permissions"

    @pytest.mark.skipif(sys.version_info < (3, 0), reason='test for py3')
    def test_init_py3(self):
        with pytest.raises(NotImplementedError) as excinfo:
            _AwsService(1, 2, {}, None)
        assert excinfo.value.args[0] == "abstract base class"

    def test_init_subclass(self):
        m_quota = Mock()
        cls = AwsServiceTester(1, 2, {}, m_quota)
        assert cls.warning_threshold == 1
        assert cls.critical_threshold == 2
        assert cls.limits == {'foo': 'bar'}
        assert cls.conn is None
        assert cls._have_usage is False
        assert cls._boto3_connection_kwargs == {}
        assert cls._quotas_client == m_quota

    def test_init_subclass_boto_xargs(self):
        boto_args = {'region_name': 'myregion',
                     'aws_access_key_id': 'myaccesskey',
                     'aws_secret_access_key': 'mysecretkey',
                     'aws_session_token': 'mytoken'}

        cls = AwsServiceTester(1, 2, boto_args, None)
        assert cls.warning_threshold == 1
        assert cls.critical_threshold == 2
        assert cls.limits == {'foo': 'bar'}
        assert cls.conn is None
        assert cls._have_usage is False
        assert cls._boto3_connection_kwargs == boto_args
        assert cls._quotas_client is None

    def test_set_limit_override(self):
        mock_limit = Mock(spec_set=AwsLimit)
        type(mock_limit).default_limit = 5
        cls = AwsServiceTester(1, 2, {}, None)
        cls.limits['foo'] = mock_limit
        cls.set_limit_override('foo', 10)
        assert mock_limit.mock_calls == [
            call.set_limit_override(10, override_ta=True)
        ]

    def test_set_limit_override_keyerror(self):
        mock_limit = Mock(spec_set=AwsLimit)
        type(mock_limit).default_limit = 5
        cls = AwsServiceTester(1, 2, {}, None)
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
        cls = AwsServiceTester(1, 2, {}, None)
        cls.limits['foo'] = mock_limit
        cls._set_ta_limit('foo', 10)
        assert mock_limit.mock_calls == [
            call._set_ta_limit(10)
        ]

    def test_set_ta_limit_keyerror(self):
        mock_limit = Mock(spec_set=AwsLimit)
        type(mock_limit).default_limit = 5
        cls = AwsServiceTester(1, 2, {}, None)
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
        cls = AwsServiceTester(1, 2, {}, None)
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
        cls = AwsServiceTester(1, 2, {}, None)
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
        cls = AwsServiceTester(1, 2, {}, None)
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
        cls = AwsServiceTester(1, 2, {}, None)
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

    def test_update_service_quotas(self):

        def se_get_quota_value(_, quota_name, **kwargs):
            if quota_name == 'qn1':
                return 12.4
            return None

        mock_client = Mock(spec_set=ServiceQuotasClient)
        mock_client.get_quota_value.side_effect = se_get_quota_value
        mock_limit1 = Mock(spec_set=AwsLimit)
        type(mock_limit1).quotas_service_code = PropertyMock(
            return_value='qsc'
        )
        type(mock_limit1).quota_name = PropertyMock(return_value='qn1')
        type(mock_limit1).quotas_unit = PropertyMock(return_value='None')
        type(mock_limit1).quotas_unit_converter = PropertyMock(
            return_value=None
        )
        mock_limit2 = Mock(spec_set=AwsLimit)
        type(mock_limit2).quotas_service_code = PropertyMock(
            return_value='qsc'
        )
        type(mock_limit2).quota_name = PropertyMock(return_value='qn2')
        type(mock_limit2).quotas_unit = PropertyMock(return_value='None')
        type(mock_limit2).quotas_unit_converter = PropertyMock(
            return_value=None
        )
        mock_limit3 = Mock(spec_set=AwsLimit)
        type(mock_limit3).quotas_service_code = PropertyMock(
            return_value='qsc'
        )
        type(mock_limit3).quota_name = PropertyMock(return_value='qn3')
        type(mock_limit3).quotas_unit = PropertyMock(return_value='Foo')
        mock_conv = Mock()
        type(mock_limit3).quotas_unit_converter = PropertyMock(
            return_value=mock_conv
        )
        cls = AwsServiceTester(1, 2, {}, mock_client)
        cls.quotas_service_code = 'qsc'
        cls.limits = {
            'limit1': mock_limit1,
            'limit2': mock_limit2,
            'limit3': mock_limit3
        }
        cls._update_service_quotas()
        assert mock_client.mock_calls == [
            call.get_quota_value('qsc', 'qn1', units='None', converter=None),
            call.get_quota_value('qsc', 'qn2', units='None', converter=None),
            call.get_quota_value(
                'qsc', 'qn3', units='Foo', converter=mock_conv
            )
        ]
        assert mock_limit1.mock_calls == [
            call._set_quotas_limit(12.4)
        ]
        assert mock_limit2.mock_calls == []

    def test_update_service_quotas_no_code(self):

        def se_get_quota_value(_, quota_name, **kwargs):
            if quota_name == 'qn1':
                return 12.4
            return None

        mock_client = Mock(spec_set=ServiceQuotasClient)
        mock_client.get_quota_value.side_effect = se_get_quota_value
        mock_limit1 = Mock(spec_set=AwsLimit)
        type(mock_limit1).quotas_service_code = PropertyMock(
            return_value='qsc'
        )
        type(mock_limit1).quota_name = PropertyMock(return_value='qn1')
        type(mock_limit1).quotas_unit = PropertyMock(return_value='None')
        mock_limit2 = Mock(spec_set=AwsLimit)
        type(mock_limit2).quotas_service_code = PropertyMock(
            return_value='qsc'
        )
        type(mock_limit2).quota_name = PropertyMock(return_value='qn2')
        type(mock_limit2).quotas_unit = PropertyMock(return_value='None')
        cls = AwsServiceTester(1, 2, {}, mock_client)
        cls.quotas_service_code = None
        cls.limits = {'limit1': mock_limit1, 'limit2': mock_limit2}
        cls._update_service_quotas()
        assert mock_client.mock_calls == []
        assert mock_limit1.mock_calls == []
        assert mock_limit2.mock_calls == []

    def test_update_service_quotas_no_client(self):

        def se_get_quota_value(_, quota_name, **kwargs):
            if quota_name == 'qn1':
                return 12.4
            return None

        mock_client = Mock(spec_set=ServiceQuotasClient)
        mock_client.get_quota_value.side_effect = se_get_quota_value
        mock_limit1 = Mock(spec_set=AwsLimit)
        type(mock_limit1).quotas_service_code = PropertyMock(
            return_value='qsc'
        )
        type(mock_limit1).quota_name = PropertyMock(return_value='qn1')
        type(mock_limit1).quotas_unit = PropertyMock(return_value='None')
        mock_limit2 = Mock(spec_set=AwsLimit)
        type(mock_limit2).quotas_service_code = PropertyMock(
            return_value='qsc'
        )
        type(mock_limit2).quota_name = PropertyMock(return_value='qn2')
        type(mock_limit2).quotas_unit = PropertyMock(return_value='None')
        cls = AwsServiceTester(1, 2, {}, None)
        cls.quotas_service_code = 'qsc'
        cls.limits = {'limit1': mock_limit1, 'limit2': mock_limit2}
        cls._update_service_quotas()
        assert mock_client.mock_calls == []
        assert mock_limit1.mock_calls == []
        assert mock_limit2.mock_calls == []


class Test_AwsServiceSubclasses(object):

    def test_subclass_init(self, cls):
        # ensure we set limits in the constructor
        mock_limits = Mock()
        mock_get_limits = Mock()
        mock_get_limits.return_value = mock_limits
        mock_quotas = Mock()
        with patch.object(cls, 'get_limits', mock_get_limits):
            inst = cls(3, 7, {}, mock_quotas)
        assert inst.limits == mock_limits
        assert inst._quotas_client == mock_quotas
        assert mock_get_limits.mock_calls == [call()]
        # ensure service name is changed
        assert inst.service_name != 'baseclass'
        assert inst.api_name != 'baseclass'
        # ensure an IAM permissions list, even if empty
        assert isinstance(inst.required_iam_permissions(), list)
        # ensure warning and critical thresholds
        assert inst.warning_threshold == 3
        assert inst.critical_threshold == 7
        assert not inst._boto3_connection_kwargs

        boto_args = dict(region_name='myregion',
                         aws_access_key_id='myaccesskey',
                         aws_secret_access_key='mysecretkey',
                         aws_session_token='mytoken')

        sts_inst = cls(3, 7, boto_args, mock_quotas)
        assert sts_inst._boto3_connection_kwargs == boto_args
        assert sts_inst._quotas_client == mock_quotas
