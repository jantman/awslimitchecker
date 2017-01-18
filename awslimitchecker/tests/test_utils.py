"""
awslimitchecker/tests/test_utils.py

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

import argparse
import pytest
import sys

from awslimitchecker.utils import (
    StoreKeyValuePair, dict2cols, paginate_dict, _get_dict_value_by_path,
    _set_dict_value_by_path
)

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import call, Mock
else:
    from unittest.mock import call, Mock

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


class TestPaginateDict(object):

    def test_no_marker_path(self):
        func = Mock()

        with pytest.raises(Exception) as excinfo:
            paginate_dict(func)
        ex_str = "alc_marker_path must be specified for queries " \
                 "that return a dict."
        assert ex_str in str(excinfo)

    def test_no_data_path(self):
        func = Mock()

        with pytest.raises(Exception) as excinfo:
            paginate_dict(func, alc_marker_path=[])
        ex_str = "alc_data_path must be specified for queries " \
                 "that return a dict."
        assert ex_str in str(excinfo)

    def test_no_marker_param(self):
        func = Mock()

        with pytest.raises(Exception) as excinfo:
            paginate_dict(
                func,
                alc_marker_path=[],
                alc_data_path=[]
            )
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
        func.return_value = result

        res = paginate_dict(
            func,
            alc_marker_path=['k1', 'k2', 'Marker'],
            alc_data_path=['k1', 'k2', 'Data'],
            alc_marker_param='Marker'
        )
        assert res == result
        assert func.mock_calls == [call()]

    def test_no_marker(self):
        result = {
            'k1': {
                'k2': {
                    'Data': []
                }
            }
        }
        func = Mock()
        func.return_value = result

        res = paginate_dict(
            func,
            alc_marker_path=['k1', 'k2', 'Marker'],
            alc_data_path=['k1', 'k2', 'Data'],
            alc_marker_param='Marker'
        )
        assert res == result
        assert func.mock_calls == [call()]

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

        func.side_effect = [res1, res2, res3]

        res = paginate_dict(
            func,
            'foo',
            bar='baz',
            alc_marker_path=['k1', 'k2', 'Marker'],
            alc_data_path=['k1', 'k2', 'Data'],
            alc_marker_param='MarkerParam'
        )
        assert res == expected
        assert func.mock_calls == [
            call('foo', bar='baz'),
            call(
                'foo',
                bar='baz',
                MarkerParam='marker1'
            ),
            call(
                'foo',
                bar='baz',
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
