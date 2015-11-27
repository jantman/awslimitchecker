"""
awslimitchecker/tests/test_utils.py

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

import argparse
import pytest
import sys

from boto.exception import BotoServerError
from boto.resultset import ResultSet

from awslimitchecker.utils import (
    StoreKeyValuePair, dict2cols, invoke_with_throttling_retries,
    boto_query_wrapper, paginate_query
)

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock
else:
    from unittest.mock import patch, call, Mock

pbm = 'awslimitchecker.utils'


class TestStoreKeyValuePair(object):

    def test_argparse_works(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--foo', action='store', type=str)
        res = parser.parse_args(['--foo=bar'])
        assert res.foo == 'bar'

    def test_long(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--one', action=StoreKeyValuePair)
        res = parser.parse_args(['--one=foo=bar'])
        assert res.one == {'foo': 'bar'}

    def test_short(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-o', '--one', action=StoreKeyValuePair)
        res = parser.parse_args(['-o', 'foo=bar'])
        assert res.one == {'foo': 'bar'}

    def test_multi_long(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-o', '--one', action=StoreKeyValuePair)
        res = parser.parse_args(['--one=foo=bar', '--one=baz=blam'])
        assert res.one == {'foo': 'bar', 'baz': 'blam'}

    def test_multi_short(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-o', '--one', action=StoreKeyValuePair)
        res = parser.parse_args(['-o', 'foo=bar', '-o', 'baz=blam'])
        assert res.one == {'foo': 'bar', 'baz': 'blam'}

    def test_no_equals(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-o', '--one', action=StoreKeyValuePair)
        with pytest.raises(SystemExit) as excinfo:
            parser.parse_args(['-o', 'foobar'])
        if sys.version_info[0] > 2:
            msg = excinfo.value.args[0]
        else:
            msg = excinfo.value.message
        assert msg == 2

    def test_quoted(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-o', '--one', action=StoreKeyValuePair)
        res = parser.parse_args([
            '-o',
            '"foo some"=bar',
            '--one="baz other"=blam'
        ])
        assert res.one == {'foo some': 'bar', 'baz other': 'blam'}


class Test_dict2cols(object):

    def test_simple(self):
        d = {'foo': 'bar', 'baz': 'blam'}
        res = dict2cols(d)
        assert res == 'baz  blam\nfoo  bar\n'

    def test_spaces(self):
        d = {'foo': 'bar', 'baz': 'blam'}
        res = dict2cols(d, spaces=4)
        assert res == 'baz    blam\nfoo    bar\n'

    def test_less_simple(self):
        d = {
            'zzz': 'bar',
            'aaa': 'blam',
            'abcdefghijklmnopqrstuv': 'someothervalue',
        }
        res = dict2cols(d)
        assert res == '' + \
            'aaa                     blam\n' + \
            'abcdefghijklmnopqrstuv  someothervalue\n' + \
            'zzz                     bar\n'

    def test_separator(self):
        d = {'foo': 'bar', 'baz': 'blam'}
        res = dict2cols(d, spaces=4, separator='.')
        assert res == 'baz....blam\nfoo....bar\n'

    def test_empty(self):
        d = {}
        res = dict2cols(d)
        assert res == ''


class TestInvokeWithThrottlingRetries(object):

    def setup(self):
        self.retry_count = 0
        self.num_errors = 0

    def retry_func(self, *args, **kwargs):
        self.retry_count += 1
        if self.num_errors != 0 and self.retry_count <= self.num_errors:
            body = "<ErrorResponse xmlns=\"http://cloudformation.amazonaws.co" \
                   "m/doc/2010-05-15/\">\n  <Error>\n    <Type>Sender</Type>" \
                   "\n    <Code>Throttling</Code>\n    <Message>Rate exceeded" \
                   "</Message>\n  </Error>\n  <RequestId>2ab5db0d-5bca-11e4-9" \
                   "592-272cff50ba2d</RequestId>\n</ErrorResponse>"
            raise BotoServerError(400, 'Bad Request', body)
        return True

    def other_error(self, *args, **kwargs):
        body = "<ErrorResponse xmlns=\"http://cloudformation.amazonaws.co" \
               "m/doc/2010-05-15/\">\n  <Error>\n    <Type>Sender</Type>" \
               "\n    <Code>UnauthorizedOperation</Code>\n    " \
               "<Message>foobar</Message>\n  " \
               "</Error>\n  <RequestId>2ab5db0d-5bca-11e4-9" \
               "592-272cff50ba2d</RequestId>\n</ErrorResponse>"
        raise BotoServerError(400, 'Bad Request', body)

    def test_invoke_ok(self):
        cls = Mock()
        cls.func.side_effect = self.retry_func
        with patch('awslimitchecker.utils.time.sleep') as mock_sleep:
            res = invoke_with_throttling_retries(cls.func)
        assert res is True
        assert cls.func.mock_calls == [call()]
        assert mock_sleep.mock_calls == []

    def test_invoke_ok_args(self):
        cls = Mock()
        cls.func.side_effect = self.retry_func
        with patch('awslimitchecker.utils.time.sleep') as mock_sleep:
            res = invoke_with_throttling_retries(
                cls.func, 'zzz', 'aaa', foo='bar'
            )
        assert res is True
        assert cls.func.mock_calls == [call('zzz', 'aaa', foo='bar')]
        assert mock_sleep.mock_calls == []

    def test_invoke_ok_alc_args(self):
        cls = Mock()
        cls.func.side_effect = self.retry_func
        with patch('awslimitchecker.utils.time.sleep') as mock_sleep:
            res = invoke_with_throttling_retries(
                cls.func, 'zzz', 'aaa', foo='bar', alc_paginate=True,
                alc_foo='bar'
            )
        assert res is True
        assert cls.func.mock_calls == [call('zzz', 'aaa', foo='bar')]
        assert mock_sleep.mock_calls == []

    def test_invoke_other_error(self):
        cls = Mock()
        cls.func.side_effect = self.other_error
        with patch('awslimitchecker.utils.time.sleep') as mock_sleep:
            with pytest.raises(BotoServerError) as ex:
                invoke_with_throttling_retries(cls.func)
        assert cls.func.mock_calls == [call()]
        assert mock_sleep.mock_calls == []
        assert ex.value.code == 'UnauthorizedOperation'

    def test_invoke_one_fail(self):
        self.num_errors = 1
        cls = Mock()
        cls.func.side_effect = self.retry_func
        with patch('awslimitchecker.utils.time.sleep') as mock_sleep:
            res = invoke_with_throttling_retries(cls.func)
        assert res is True
        assert cls.func.mock_calls == [call(), call()]
        assert mock_sleep.mock_calls == [call(2)]

    def test_invoke_max_fail(self):
        self.num_errors = 6
        cls = Mock()
        cls.func.side_effect = self.retry_func
        with patch('awslimitchecker.utils.time.sleep') as mock_sleep:
            with pytest.raises(BotoServerError) as ex:
                invoke_with_throttling_retries(cls.func)
        assert ex.value.code == 'Throttling'
        assert cls.func.mock_calls == [
            call(), call(), call(), call(), call(), call()
        ]
        assert mock_sleep.mock_calls == [
            call(2), call(4), call(8), call(16), call(32)
        ]


class TestBotoQueryWrapper(object):

    def test_invoke_noargs(self):
        func = Mock()
        retval = Mock()

        with patch('%s.invoke_with_throttling_retries' % pbm) as mock_invoke:
            with patch('%s.paginate_query' % pbm) as mock_paginate:
                mock_invoke.return_value = retval
                res = boto_query_wrapper(func)
        assert res == retval
        assert mock_invoke.mock_calls == [call(func)]
        assert mock_paginate.mock_calls == []

    def test_invoke_args(self):
        func = Mock()
        retval = Mock()

        with patch('%s.invoke_with_throttling_retries' % pbm) as mock_invoke:
            with patch('%s.paginate_query' % pbm) as mock_paginate:
                mock_invoke.return_value = retval
                res = boto_query_wrapper(func, 'foo', 'bar')
        assert res == retval
        assert mock_invoke.mock_calls == [call(func, 'foo', 'bar')]
        assert mock_paginate.mock_calls == []

    def test_invoke_kwargs(self):
        func = Mock()
        retval = Mock()

        with patch('%s.invoke_with_throttling_retries' % pbm) as mock_invoke:
            with patch('%s.paginate_query' % pbm) as mock_paginate:
                mock_invoke.return_value = retval
                res = boto_query_wrapper(
                    func, 'foo', bar='barval', baz='bazval'
                )
        assert res == retval
        assert mock_invoke.mock_calls == [
            call(func, 'foo', bar='barval', baz='bazval')
        ]
        assert mock_paginate.mock_calls == []

    def test_invoke_kwargs_alc(self):
        func = Mock()
        retval = Mock()

        with patch('%s.invoke_with_throttling_retries' % pbm) as mock_invoke:
            with patch('%s.paginate_query' % pbm) as mock_paginate:
                mock_invoke.return_value = retval
                res = boto_query_wrapper(func, 'foo', bar='barval',
                                         baz='bazval', alc_foo='alcfoo',
                                         alc_bar='alcbar')
        assert res == retval
        assert mock_invoke.mock_calls == [
            call(func, 'foo', bar='barval', baz='bazval', alc_foo='alcfoo',
                 alc_bar='alcbar')
        ]
        assert mock_paginate.mock_calls == []

    def test_invoke_paginate(self):
        func = Mock()
        retval = Mock()

        with patch('%s.invoke_with_throttling_retries' % pbm) as mock_invoke:
            with patch('%s.paginate_query' % pbm) as mock_paginate:
                mock_paginate.return_value = retval
                res = boto_query_wrapper(
                    func, 'foo', bar='barval', baz='bazval', alc_paginate=True
                )
        assert res == retval
        assert mock_invoke.mock_calls == []
        assert mock_paginate.mock_calls == [
            call(func, 'foo', bar='barval', baz='bazval', alc_paginate=True)
        ]


class TestPaginateQuery(object):

    def test_not_resultset(self):
        result = {'foo': 'bar'}
        func = Mock()

        with patch('%s.invoke_with_throttling_retries' % pbm) as mock_invoke:
            mock_invoke.return_value = result
            res = paginate_query(func, 'foo', bar='barval')
        assert res == result
        assert mock_invoke.mock_calls == [
            call(func, 'foo', bar='barval')
        ]

    def test_resultset_no_next(self):
        e1 = Mock()
        e2 = Mock()
        rs = ResultSet()
        rs.append(e1)
        rs.append(e2)

        func = Mock()

        with patch('%s.invoke_with_throttling_retries' % pbm) as mock_invoke:
            mock_invoke.return_value = rs
            res = paginate_query(func, 'foo', bar='barval')
        assert res == rs
        assert mock_invoke.mock_calls == [
            call(func, 'foo', bar='barval')
        ]

    def test_resultset_two_next(self):
        e1 = Mock()
        e2 = Mock()
        rs1 = ResultSet()
        rs1.append(e1)
        rs1.append(e2)
        rs1.next_token = 't1'

        e3 = Mock()
        e4 = Mock()
        rs2 = ResultSet()
        rs2.append(e3)
        rs2.append(e4)
        rs2.next_token = 't2'

        e5 = Mock()
        e6 = Mock()
        rs3 = ResultSet()
        rs3.append(e5)
        rs3.append(e6)

        func = Mock()

        results = [rs1, rs2, rs3]

        def se_invoke(f, *args, **argv):
            return results.pop(0)

        with patch('%s.invoke_with_throttling_retries' % pbm) as mock_invoke:
            mock_invoke.side_effect = se_invoke
            res = paginate_query(func, 'foo', bar='barval')
        assert isinstance(res, ResultSet)
        assert len(res) == 6
        assert res[0] == e1
        assert res[1] == e2
        assert res[2] == e3
        assert res[3] == e4
        assert res[4] == e5
        assert res[5] == e6
        assert mock_invoke.mock_calls == [
            call(func, 'foo', bar='barval'),
            call(func, 'foo', bar='barval', next_token='t1'),
            call(func, 'foo', bar='barval', next_token='t2')
        ]
