"""
awslimitchecker/tests/test_quotas.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

##############################################################################
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
import pytest

from awslimitchecker.quotas import ServiceQuotasClient
from awslimitchecker.tests.support import quotas_response

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock

pbm = 'awslimitchecker.quotas'
pb = '%s.ServiceQuotasClient' % pbm


class TestConstructor(object):

    def test_init(self):
        cls = ServiceQuotasClient({'foo': 'bar'})
        assert cls._boto3_connection_kwargs == {'foo': 'bar'}
        assert cls._cache == {}
        assert cls.conn is None


class TestQuotasForService(object):

    def setup(self):
        self.cls = ServiceQuotasClient({'foo': 'bar'})

    def test_not_cached(self):
        resp, expected = quotas_response()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = resp
        mock_conn = Mock()
        mock_conn.get_paginator.return_value = mock_paginator

        def se_connect(cls):
            cls.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_connect
            res = self.cls.quotas_for_service('scode')
        assert res == expected
        assert self.cls._cache == {'scode': expected}
        assert m_connect.mock_calls == [call(self.cls)]
        assert mock_conn.mock_calls == [
            call.get_paginator('list_service_quotas'),
            call.get_paginator().paginate(ServiceCode='scode')
        ]

    def test_cached(self):
        resp, expected = quotas_response()
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = resp
        mock_conn = Mock()
        mock_conn.get_paginator.return_value = mock_paginator

        def se_connect(cls):
            cls.conn = mock_conn

        self.cls._cache = {'scode': expected}

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_connect
            res = self.cls.quotas_for_service('scode')
        assert res == expected
        assert self.cls._cache == {'scode': expected}
        assert m_connect.mock_calls == []
        assert mock_conn.mock_calls == []

    def test_no_such_resource(self):
        mock_paginator = Mock()
        mock_paginator.paginate.side_effect = ClientError(
            {
                'Error': {
                    'Code': 'NoSuchResourceException',
                    'Message': 'The request failed because the specified '
                               'service does not exist.'
                }
            },
            'ListServiceQuotas'
        )
        mock_conn = Mock()
        mock_conn.get_paginator.return_value = mock_paginator

        def se_connect(cls):
            cls.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_connect
            res = self.cls.quotas_for_service('scode')
        assert res == {}
        assert self.cls._cache == {'scode': {}}
        assert m_connect.mock_calls == [call(self.cls)]
        assert mock_conn.mock_calls == [
            call.get_paginator('list_service_quotas'),
            call.get_paginator().paginate(ServiceCode='scode')
        ]

    def test_other_exception(self):
        mock_paginator = Mock()
        mock_paginator.paginate.side_effect = ClientError(
            {
                'Error': {
                    'Code': 'SomeOtherError',
                    'Message': 'My message.'
                }
            },
            'ListServiceQuotas'
        )
        mock_conn = Mock()
        mock_conn.get_paginator.return_value = mock_paginator

        def se_connect(cls):
            cls.conn = mock_conn

        with patch('%s.connect' % pb, autospec=True) as m_connect:
            m_connect.side_effect = se_connect
            with pytest.raises(ClientError):
                self.cls.quotas_for_service('scode')
        assert self.cls._cache == {'scode': {}}
        assert m_connect.mock_calls == [call(self.cls)]
        assert mock_conn.mock_calls == [
            call.get_paginator('list_service_quotas'),
            call.get_paginator().paginate(ServiceCode='scode')
        ]


class TestGetQuotaValue(object):

    def setup(self):
        self.cls = ServiceQuotasClient({'foo': 'bar'})

    def test_happy_path(self):
        self.cls._cache = {
            'scode': {
                'qname': {
                    'QuotaName': 'qname',
                    'QuotaCode': 'qcode',
                    'Value': 12.3,
                    'Unit': 'None'
                }
            }
        }
        res = self.cls.get_quota_value('scode', 'QName')
        assert res == 12.3

    def test_no_quota(self):
        self.cls._cache = {
            'scode': {
                'qname': {
                    'QuotaName': 'qname',
                    'QuotaCode': 'qcode',
                    'Value': 12.3,
                    'Unit': 'None'
                }
            }
        }
        res = self.cls.get_quota_value('scode', 'OtherName')
        assert res is None

    def test_units(self):
        self.cls._cache = {
            'scode': {
                'qname': {
                    'QuotaName': 'qname',
                    'QuotaCode': 'qcode',
                    'Value': 12.3,
                    'Unit': 'Foo'
                }
            }
        }
        res = self.cls.get_quota_value('scode', 'QName')
        assert res is None

    def test_units_converter(self):
        m_conv = Mock()
        m_conv.return_value = 1230.0
        self.cls._cache = {
            'scode': {
                'qname': {
                    'QuotaName': 'qname',
                    'QuotaCode': 'qcode',
                    'Value': 12.3,
                    'Unit': 'Foo'
                }
            }
        }
        res = self.cls.get_quota_value(
            'scode', 'QName', converter=m_conv
        )
        assert res == 1230.0
        assert m_conv.mock_calls == [
            call(12.3, 'Foo', 'None')
        ]
