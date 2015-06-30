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

from awslimitchecker.utils import StoreKeyValuePair, dict2cols


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