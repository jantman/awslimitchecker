"""
awslimitchecker/tests/test_version.py

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

import awslimitchecker.version as version
from awslimitchecker.version import AWSLimitCheckerVersion
from awslimitchecker.versioncheck import AGPLVersionChecker

import re
import sys
# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call
else:
    from unittest.mock import patch, call


class TestVersion(object):

    def test_project_url(self):
        expected = 'https://github.com/jantman/awslimitchecker'
        assert version._PROJECT_URL == expected

    def test__get_version_info(self):
        with patch('awslimitchecker.version.AGPLVersionChecker',
                   spec_set=AGPLVersionChecker) as mock_checker:
            mock_checker.return_value.find_package_version.return_value = {
                'version': version._VERSION,
                'url': version._PROJECT_URL,
                'tag': 'foobar',
                'commit': None,
            }
            v = version._get_version_info()
        assert v.release == version._VERSION
        assert v.url == version._PROJECT_URL
        assert v.tag == 'foobar'
        assert mock_checker.mock_calls == [
            call(),
            call().find_package_version(),
        ]

    def test__get_version_info_fallback(self):
        def se(foo):
            raise Exception("foo")

        with patch('awslimitchecker.version.AGPLVersionChecker',
                   spec_set=AGPLVersionChecker) as mock_checker:
            with patch('awslimitchecker.version.logger') as mock_logger:
                mock_checker.return_value.find_package_version.side_effect = se
                v = version._get_version_info()
        assert v.release == version._VERSION
        assert v.url == version._PROJECT_URL
        assert v.tag is None
        assert v.commit is None
        assert mock_checker.mock_calls == [
            call(),
            call().find_package_version(),
        ]
        assert mock_logger.mock_calls == [
            call.exception('Error checking installed version; this installation'
                           ' may not be in compliance with the AGPLv3 license:')
        ]

    def test_is_semver(self):
        # see:
        # https://github.com/mojombo/semver.org/issues/59#issuecomment-57884619
        semver_ptn = re.compile(
            r'^'
            r'(?P<MAJOR>(?:'
            r'0|(?:[1-9]\d*)'
            r'))'
            r'\.'
            r'(?P<MINOR>(?:'
            r'0|(?:[1-9]\d*)'
            r'))'
            r'\.'
            r'(?P<PATCH>(?:'
            r'0|(?:[1-9]\d*)'
            r'))'
            r'(?:-(?P<prerelease>'
            r'[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*'
            r'))?'
            r'(?:\+(?P<build>'
            r'[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*'
            r'))?'
            r'$'
        )
        assert semver_ptn.match(version._VERSION) is not None


class Test_AWSLimitCheckerVersionInfo(object):

    def test_simple(self):
        x = AWSLimitCheckerVersion('1.0', 'foo')
        assert x.release == '1.0'
        assert x.url == 'foo'
        assert x.commit is None
        assert x.tag is None
        assert str(x) == '1.0 <foo>'
        assert repr(x) == "AWSLimitCheckerVersion('1.0', 'foo', tag=None, " \
                          "commit=None)"
        assert x.version_str == '1.0'

    def test_tag(self):
        x = AWSLimitCheckerVersion('1.0', 'foo', tag='mytag')
        assert x.release == '1.0'
        assert x.url == 'foo'
        assert x.commit is None
        assert x.tag == 'mytag'
        assert str(x) == '1.0@mytag <foo>'
        assert repr(x) == "AWSLimitCheckerVersion('1.0', 'foo', tag='mytag'" \
                          ", commit=None)"
        assert x.version_str == '1.0@mytag'

    def test_commit(self):
        x = AWSLimitCheckerVersion('1.0', 'foo', commit='abcd')
        assert x.release == '1.0'
        assert x.url == 'foo'
        assert x.commit == 'abcd'
        assert x.tag is None
        assert str(x) == '1.0@abcd <foo>'
        assert repr(x) == "AWSLimitCheckerVersion('1.0', 'foo', tag=None, " \
                          "commit='abcd')"
        assert x.version_str == '1.0@abcd'

    def test_tag_commit(self):
        x = AWSLimitCheckerVersion('1.0', 'foo', tag='mytag', commit='abcd')
        assert x.release == '1.0'
        assert x.url == 'foo'
        assert x.commit == 'abcd'
        assert x.tag == 'mytag'
        assert str(x) == '1.0@mytag <foo>'
        assert repr(x) == "AWSLimitCheckerVersion('1.0', 'foo', tag='mytag'," \
                          " commit='abcd')"
        assert x.version_str == '1.0@mytag'
