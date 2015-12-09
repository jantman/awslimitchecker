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
from boto.ec2.autoscale.limits import AccountLimits

from awslimitchecker.utils import (
    StoreKeyValuePair, dict2cols, invoke_with_throttling_retries,
    boto_query_wrapper, paginate_query, _paginate_resultset, _paginate_dict,
    _get_dict_value_by_path, _set_dict_value_by_path
)

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT

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
                cls.func, 'zzz', 'aaa', foo='bar', alc_foo='bar')
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

        with patch('%s.paginate_query' % pbm) as mock_paginate:
            mock_paginate.return_value = retval
            res = boto_query_wrapper(func)
        assert res == retval
        assert mock_paginate.mock_calls == [call(func)]

    def test_invoke_args(self):
        func = Mock()
        retval = Mock()

        with patch('%s.paginate_query' % pbm) as mock_paginate:
            mock_paginate.return_value = retval
            res = boto_query_wrapper(func, 'foo', 'bar')
        assert res == retval
        assert mock_paginate.mock_calls == [call(func, 'foo', 'bar')]

    def test_invoke_kwargs(self):
        func = Mock()
        retval = Mock()

        with patch('%s.paginate_query' % pbm) as mock_paginate:
            mock_paginate.return_value = retval
            res = boto_query_wrapper(
                func, 'foo', bar='barval', baz='bazval'
            )
        assert res == retval
        assert mock_paginate.mock_calls == [
            call(func, 'foo', bar='barval', baz='bazval')
        ]

    def test_invoke_kwargs_alc(self):
        func = Mock()
        retval = Mock()

        with patch('%s.paginate_query' % pbm) as mock_paginate:
            mock_paginate.return_value = retval
            res = boto_query_wrapper(func, 'foo', bar='barval',
                                     baz='bazval', alc_foo='alcfoo',
                                     alc_bar='alcbar')
        assert res == retval
        assert mock_paginate.mock_calls == [
            call(func, 'foo', bar='barval', baz='bazval', alc_foo='alcfoo',
                 alc_bar='alcbar')
        ]

    def test_invoke_paginate(self):
        func = Mock()
        retval = Mock()

        with patch('%s.paginate_query' % pbm) as mock_paginate:
            mock_paginate.return_value = retval
            res = boto_query_wrapper(
                func, 'foo', bar='barval', baz='bazval'
            )
        assert res == retval
        assert mock_paginate.mock_calls == [
            call(func, 'foo', bar='barval', baz='bazval')
        ]


class TestPaginateQuery(object):

    def test_resultset_next_token(self):
        result = ResultSet()
        result.next_token = 'foo'
        func = Mock()
        final_result = Mock()

        with patch.multiple(
                pbm,
                invoke_with_throttling_retries=DEFAULT,
                _paginate_resultset=DEFAULT,
                _paginate_dict=DEFAULT,
        ) as mocks:
            mocks['invoke_with_throttling_retries'].return_value = result
            mocks['_paginate_resultset'].return_value = final_result
            res = paginate_query(func, 'foo', bar='barval')
        assert res == final_result
        assert mocks['invoke_with_throttling_retries'].mock_calls == [
            call(func, 'foo', bar='barval')
        ]
        assert mocks['_paginate_resultset'].mock_calls == [
            call(result, func, 'foo', bar='barval')
        ]
        assert mocks['_paginate_dict'].mock_calls == []

    def test_alc_no_paginate(self):
        result = ResultSet()
        result.next_token = 'foo'
        func = Mock()

        with patch.multiple(
                pbm,
                invoke_with_throttling_retries=DEFAULT,
                _paginate_resultset=DEFAULT,
                _paginate_dict=DEFAULT,
        ) as mocks:
            mocks['invoke_with_throttling_retries'].return_value = result
            res = paginate_query(func, 'foo', bar='barval',
                                 alc_no_paginate=True)
        assert res == result
        assert mocks['invoke_with_throttling_retries'].mock_calls == [
            call(func, 'foo', bar='barval', alc_no_paginate=True)
        ]
        assert mocks['_paginate_resultset'].mock_calls == []
        assert mocks['_paginate_dict'].mock_calls == []

    def test_resultset_no_next(self):
        result = ResultSet()
        func = Mock()

        with patch.multiple(
                pbm,
                invoke_with_throttling_retries=DEFAULT,
                _paginate_resultset=DEFAULT,
                _paginate_dict=DEFAULT,
        ) as mocks:
            mocks['invoke_with_throttling_retries'].return_value = result
            res = paginate_query(func, 'foo', bar='barval')
        assert res == result
        assert mocks['invoke_with_throttling_retries'].mock_calls == [
            call(func, 'foo', bar='barval')
        ]
        assert mocks['_paginate_resultset'].mock_calls == []
        assert mocks['_paginate_dict'].mock_calls == []

    def test_dict(self):
        result = {'foo': 'bar'}
        func = Mock()
        final_result = Mock()

        with patch.multiple(
                pbm,
                invoke_with_throttling_retries=DEFAULT,
                _paginate_resultset=DEFAULT,
                _paginate_dict=DEFAULT,
                logger=DEFAULT,
        ) as mocks:
            mocks['invoke_with_throttling_retries'].return_value = result
            mocks['_paginate_dict'].return_value = final_result
            res = paginate_query(
                func,
                'foo',
                bar='barval',
                alc_marker_path=[],
                alc_data_path=[],
                alc_marker_param='p'
            )
        assert res == final_result
        assert mocks['invoke_with_throttling_retries'].mock_calls == [
            call(func, 'foo', bar='barval', alc_marker_path=[],
                 alc_data_path=[], alc_marker_param='p')
        ]
        assert mocks['_paginate_resultset'].mock_calls == []
        assert mocks['_paginate_dict'].mock_calls == [
            call(result, func, 'foo', bar='barval', alc_marker_path=[],
                 alc_data_path=[], alc_marker_param='p')
        ]
        assert mocks['logger'].mock_calls == []

    def test_dict_missing_params(self):
        result = {'foo': 'bar'}
        func = Mock()
        final_result = Mock()

        with patch.multiple(
                pbm,
                invoke_with_throttling_retries=DEFAULT,
                _paginate_resultset=DEFAULT,
                _paginate_dict=DEFAULT,
                logger=DEFAULT,
        ) as mocks:
            mocks['invoke_with_throttling_retries'].return_value = result
            mocks['_paginate_dict'].return_value = final_result
            res = paginate_query(
                func,
                'foo',
                bar='barval'
            )
        assert res == result
        assert mocks['invoke_with_throttling_retries'].mock_calls == [
            call(func, 'foo', bar='barval')
        ]
        assert mocks['_paginate_resultset'].mock_calls == []
        assert mocks['_paginate_dict'].mock_calls == []
        assert len(mocks['logger'].mock_calls) == 1
        args = mocks['logger'].warning.mock_calls[0][1]
        assert len(args) == 1
        assert args[0].startswith(
            "Query returned a dict, but does not have _paginate_dict params "
            "set; cannot paginate (<Mock id='") is True

    def test_result_AccountLimits(self):
        func = Mock()
        result = AccountLimits()

        with patch.multiple(
                pbm,
                invoke_with_throttling_retries=DEFAULT,
                _paginate_resultset=DEFAULT,
                _paginate_dict=DEFAULT,
                logger=DEFAULT,
        ) as mocks:
            mocks['invoke_with_throttling_retries'].return_value = result
            res = paginate_query(func, 'foo', bar='barval')
        assert res == result
        assert mocks['invoke_with_throttling_retries'].mock_calls == [
            call(func, 'foo', bar='barval')
        ]
        assert mocks['_paginate_resultset'].mock_calls == []
        assert mocks['_paginate_dict'].mock_calls == []
        assert mocks['logger'].mock_calls == []

    def test_other_type(self):
        func = Mock()

        with patch.multiple(
                pbm,
                invoke_with_throttling_retries=DEFAULT,
                _paginate_resultset=DEFAULT,
                _paginate_dict=DEFAULT,
                logger=DEFAULT,
        ) as mocks:
            mocks['invoke_with_throttling_retries'].return_value = 'foobar'
            res = paginate_query(func, 'foo', bar='barval')
        assert res == 'foobar'
        assert mocks['invoke_with_throttling_retries'].mock_calls == [
            call(func, 'foo', bar='barval')
        ]
        assert mocks['_paginate_resultset'].mock_calls == []
        assert mocks['_paginate_dict'].mock_calls == []
        assert mocks['logger'].mock_calls == [
            call.warning("Query result of type %s cannot be paginated",
                         type('foo'))
        ]


class TestPaginateResultSet(object):

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

        results = [rs2, rs3]

        def se_invoke(f, *args, **argv):
            return results.pop(0)

        with patch('%s.invoke_with_throttling_retries' % pbm) as mock_invoke:
            mock_invoke.side_effect = se_invoke
            res = _paginate_resultset(rs1, func, 'foo', bar='barval')
        assert isinstance(res, ResultSet)
        assert len(res) == 6
        assert res[0] == e1
        assert res[1] == e2
        assert res[2] == e3
        assert res[3] == e4
        assert res[4] == e5
        assert res[5] == e6
        assert mock_invoke.mock_calls == [
            call(func, 'foo', bar='barval', next_token='t1'),
            call(func, 'foo', bar='barval', next_token='t2')
        ]


class TestPaginateDict(object):

    def test_no_marker_path(self):
        result = {}
        func = Mock()

        with pytest.raises(Exception) as excinfo:
            _paginate_dict(result, func)
        ex_str = "alc_marker_path must be specified for queries " \
                 "that return a dict."
        assert ex_str in str(excinfo)

    def test_no_data_path(self):
        result = {}
        func = Mock()

        with pytest.raises(Exception) as excinfo:
            _paginate_dict(result, func, alc_marker_path=[])
        ex_str = "alc_data_path must be specified for queries " \
                 "that return a dict."
        assert ex_str in str(excinfo)

    def test_no_marker_param(self):
        result = {}
        func = Mock()

        with pytest.raises(Exception) as excinfo:
            _paginate_dict(result, func, alc_marker_path=[],
                           alc_data_path=[])
        ex_str = "alc_marker_param must be specified for queries " \
                 "that return a dict."
        assert ex_str in str(excinfo)

    def test_bad_path(self):
        result = {
            'k1': {
                'badpath': {}
            }
        }
        func = Mock()

        with patch('%s.invoke_with_throttling_retries' % pbm) as mock_invoke:
            res = _paginate_dict(
                result,
                func,
                alc_marker_path=['k1', 'k2', 'Marker'],
                alc_data_path=['k1', 'k2', 'Data'],
                alc_marker_param='Marker'
            )
        assert res == result
        assert mock_invoke.mock_calls == []

    def test_no_marker(self):
        result = {
            'k1': {
                'k2': {
                    'Data': []
                }
            }
        }
        func = Mock()

        with patch('%s.invoke_with_throttling_retries' % pbm) as mock_invoke:
            res = _paginate_dict(
                result,
                func,
                alc_marker_path=['k1', 'k2', 'Marker'],
                alc_data_path=['k1', 'k2', 'Data'],
                alc_marker_param='Marker'
            )
        assert res == result
        assert mock_invoke.mock_calls == []

    def test_two_iterations(self):
        e1 = Mock()
        e2 = Mock()
        e3 = Mock()
        e4 = Mock()
        e5 = Mock()
        e6 = Mock()
        func = Mock()

        res1 = {
            'k1': {
                'k2': {
                    'Data': [e1, e2],
                    'Foo1': 'bar1',
                    'Marker': 'marker1'
                }
            }
        }
        res2 = {
            'k1': {
                'k2': {
                    'Data': [e3, e4],
                    'Foo2': 'bar2',
                    'Marker': 'marker2'
                }
            }
        }
        res3 = {
            'k1': {
                'k2': {
                    'Data': [e5, e6],
                    'Foo3': 'bar3'
                }
            }
        }

        expected = {
            'k1': {
                'k2': {
                    'Data': [e1, e2, e3, e4, e5, e6],
                    'Foo3': 'bar3'
                }
            }
        }

        def se_invoke(self, func, *args, **kwargs):
            if 'MarkerParam' not in kwargs:
                return -1
            if kwargs['MarkerParam'] == 'marker1':
                return res2
            if kwargs['MarkerParam'] == 'marker2':
                return res3
            return kwargs['MarkerParam']

        with patch('%s.invoke_with_throttling_retries' % pbm) as mock_invoke:
            mock_invoke.side_effect = se_invoke
            res = _paginate_dict(
                res1,
                func,
                'foo',
                alc_marker_path=['k1', 'k2', 'Marker'],
                alc_data_path=['k1', 'k2', 'Data'],
                alc_marker_param='MarkerParam'
            )
        assert res == expected
        assert mock_invoke.mock_calls == [
            call(
                func,
                'foo',
                alc_marker_path=['k1', 'k2', 'Marker'],
                alc_data_path=['k1', 'k2', 'Data'],
                alc_marker_param='MarkerParam',
                MarkerParam='marker1'
            ),
            call(
                func,
                'foo',
                alc_marker_path=['k1', 'k2', 'Marker'],
                alc_data_path=['k1', 'k2', 'Data'],
                alc_marker_param='MarkerParam',
                MarkerParam='marker2'
            )
        ]


class TestDictFuncs(object):

    def test_get_dict_value_by_path(self):
        d = {
            'foo': {
                'bar': {
                    'baz': 'bazval'
                }
            }
        }

        path = ['foo', 'bar', 'baz']
        res = _get_dict_value_by_path(d, path)
        assert res == 'bazval'
        # make sure we don't modify inputs
        assert path == ['foo', 'bar', 'baz']
        assert d == {
            'foo': {
                'bar': {
                    'baz': 'bazval'
                }
            }
        }

    def test_get_dict_value_by_path_obj(self):
        e1 = Mock()
        e2 = Mock()
        d = {
            'k1': {
                'k2': {
                    'Marker': 'marker2',
                    'Data': [e1, e2],
                    'Foo2': 'bar2'
                }
            }
        }
        res = _get_dict_value_by_path(d, ['k1', 'k2', 'Data'])
        assert res == [e1, e2]

    def test_get_dict_value_by_path_none(self):
        d = {
            'foo': {
                'bar': {
                    'blam': 'blarg'
                }
            }
        }

        res = _get_dict_value_by_path(d, ['foo', 'bar', 'baz'])
        assert res is None

    def test_get_dict_value_by_path_deep_none(self):
        d = {'baz': 'blam'}

        res = _get_dict_value_by_path(d, ['foo', 'bar', 'baz'])
        assert res is None

    def test_set_dict_value_by_path(self):
        d = {
            'foo': {
                'bar': {
                    'baz': 'bazval'
                }
            }
        }
        path = ['foo', 'bar', 'baz']

        res = _set_dict_value_by_path(d, 'blam', path)
        assert res == {
            'foo': {
                'bar': {
                    'baz': 'blam'
                }
            }
        }
        # make sure we don't modify inputs
        assert path == ['foo', 'bar', 'baz']
        assert d == {
            'foo': {
                'bar': {
                    'baz': 'bazval'
                }
            }
        }

    def test_set_dict_value_by_path_none(self):
        d = {
            'foo': {
                'bar': {
                    'blam': 'blarg'
                }
            }
        }

        res = _set_dict_value_by_path(d, 'blam', ['foo', 'bar', 'baz'])
        assert res == {
            'foo': {
                'bar': {
                    'baz': 'blam',
                    'blam': 'blarg'
                }
            }
        }

    def test_set_dict_value_by_path_deep_none(self):
        d = {'foo': 'bar'}

        with pytest.raises(TypeError):
            _set_dict_value_by_path(d, 'blam', ['foo', 'bar', 'baz'])

    def test_set_dict_value_by_path_empty(self):
        d = {'foo': 'bar'}
        res = _set_dict_value_by_path(d, 'baz', [])
        assert res == d
