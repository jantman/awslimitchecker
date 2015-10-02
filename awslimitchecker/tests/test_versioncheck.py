"""
awslimitchecker/tests/test_versioncheck.py

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

import pytest
import sys
import os
import subprocess
import shutil
from textwrap import dedent
from pip._vendor.packaging.version import Version

from awslimitchecker.version import _VERSION
import awslimitchecker.versioncheck
from awslimitchecker.versioncheck import (
    _get_git_commit, _get_git_url, _get_git_tag, _check_output, DEVNULL,
    AGPLVersionChecker
)

import logging
logger = logging.getLogger(__name__)

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, DEFAULT, Mock
else:
    from unittest.mock import patch, call, DEFAULT, Mock


class Test_AGPLVersionChecker(object):
    """
    Mocked unit tests for AGPLVersionChecker
    """

    mpb = 'awslimitchecker.versioncheck'
    pb = 'awslimitchecker.versioncheck.AGPLVersionChecker'

    def test_is_git_dirty_false(self):
        cls = AGPLVersionChecker()
        with patch('%s._check_output' % self.mpb) as mock_check_out:
            mock_check_out.return_value = dedent("""
            On branch current_module
            Your branch is up-to-date with 'origin/current_module'.
            nothing to commit, working directory clean
            """)
            res = cls._is_git_dirty()
        assert res is False
        assert mock_check_out.mock_calls == [
            call(['git', 'status', '-u'], stderr=DEVNULL)
        ]

    def test_is_git_dirty_false_detatched(self):
        cls = AGPLVersionChecker()
        with patch('%s._check_output' % self.mpb) as mock_check_out:
            mock_check_out.return_value = dedent("""
            HEAD detached at 9247d43
            nothing to commit, working directory clean
            """)
            res = cls._is_git_dirty()
        assert res is False
        assert mock_check_out.mock_calls == [
            call(['git', 'status', '-u'], stderr=DEVNULL)
        ]

    def test_is_git_dirty_true_ahead(self):
        cls = AGPLVersionChecker()
        with patch('%s._check_output' % self.mpb) as mock_check_out:
            mock_check_out.return_value = dedent("""
            On branch issues/8
            Your branch is ahead of 'origin/issues/8' by 1 commit.
              (use "git push" to publish your local commits)
            Changes not staged for commit:
              (use "git add <file>..." to update what will be committed)
              (use "git checkout -- <file>..." to discard changes in )

                    modified:   awslimitchecker/tests/test_versioncheck.py
                    modified:   awslimitchecker/versioncheck.py

            no changes added to commit (use "git add" and/or "git commit -a")
            """)
            res = cls._is_git_dirty()
        assert res is True
        assert mock_check_out.mock_calls == [
            call(['git', 'status', '-u'], stderr=DEVNULL)
        ]

    def test_is_git_dirty_true_detatched(self):
        cls = AGPLVersionChecker()
        with patch('%s._check_output' % self.mpb) as mock_check_out:
            mock_check_out.return_value = dedent("""
            HEAD detached at 9247d43
            Untracked files:
              (use "git add <file>..." to include in what will be committed)

                    foo

            nothing added to commit but untracked files present
            """)
            res = cls._is_git_dirty()
        assert res is True
        assert mock_check_out.mock_calls == [
            call(['git', 'status', '-u'], stderr=DEVNULL)
        ]

    def test_is_git_dirty_true_changes(self):
        cls = AGPLVersionChecker()
        with patch('%s._check_output' % self.mpb) as mock_check_out:
            mock_check_out.return_value = dedent("""
            On branch issues/8
            Your branch is up-to-date with 'origin/issues/8'.
            Changes not staged for commit:
              (use "git add <file>..." to update what will be committed)
              (use "git checkout -- <file>..." to discard changes in working

                    modified:   awslimitchecker/tests/test_versioncheck.py
                    modified:   awslimitchecker/versioncheck.py

            no changes added to commit (use "git add" and/or "git commit -a")
            """)
            res = cls._is_git_dirty()
        assert res is True
        assert mock_check_out.mock_calls == [
            call(['git', 'status', '-u'], stderr=DEVNULL)
        ]

    def test_find_git_info(self):
        cls = AGPLVersionChecker()
        # this is a horribly ugly way to get this to work on py26-py34
        mocks = {}
        with patch.multiple(
            self.mpb,
            _get_git_commit=DEFAULT,
            _get_git_tag=DEFAULT,
            _get_git_url=DEFAULT,
        ) as mocks1:
            mocks.update(mocks1)
            with patch.multiple(
                self.pb,
                _is_git_dirty=DEFAULT,
            ) as mocks2:
                mocks.update(mocks2)
                with patch.multiple(
                    '%s.os' % self.mpb,
                    getcwd=DEFAULT,
                    chdir=DEFAULT,
                ) as mocks3:
                    mocks.update(mocks3)
                    mocks['getcwd'].return_value = '/my/cwd'
                    mocks['_get_git_commit'].return_value = '12345678'
                    mocks['_get_git_tag'].return_value = 'mytag'
                    mocks['_get_git_url'].return_value = 'http://my.git/url'
                    mocks['_is_git_dirty'].return_value = False
                    res = cls._find_git_info()
        assert mocks['_get_git_commit'].mock_calls == [call()]
        assert mocks['_get_git_tag'].mock_calls == [call('12345678')]
        assert mocks['_get_git_url'].mock_calls == [call()]
        assert mocks['_is_git_dirty'].mock_calls == [call()]
        assert mocks['getcwd'].mock_calls == [call()]
        assert mocks['chdir'].mock_calls == [
            call(os.path.dirname(os.path.abspath(
                awslimitchecker.versioncheck.__file__))),
            call('/my/cwd')
        ]
        assert res == {
            'commit': '12345678',
            'dirty': False,
            'tag': 'mytag',
            'url': 'http://my.git/url'
        }

    def test_find_git_info_no_git(self):
        cls = AGPLVersionChecker()

        def se_exc():
            raise Exception("foo")

        # this is a horribly ugly way to get this to work on py26-py34
        mocks = {}
        with patch.multiple(
            self.mpb,
            _get_git_commit=DEFAULT,
            _get_git_tag=DEFAULT,
            _get_git_url=DEFAULT,
        ) as mocks1:
            mocks.update(mocks1)
            with patch.multiple(
                self.pb,
                _is_git_dirty=DEFAULT,
            ) as mocks2:
                mocks.update(mocks2)
                with patch.multiple(
                    '%s.os' % self.mpb,
                    getcwd=DEFAULT,
                    chdir=DEFAULT,
                ) as mocks3:
                    mocks.update(mocks3)
                    mocks['getcwd'].return_value = '/my/cwd'
                    mocks['_get_git_commit'].return_value = None
                    mocks['_get_git_tag'].return_value = 'mytag'
                    mocks['_get_git_url'].return_value = 'http://my.git/url'
                    mocks['_is_git_dirty'].side_effect = se_exc
                    res = cls._find_git_info()
        assert mocks['_get_git_commit'].mock_calls == [call()]
        assert mocks['_get_git_tag'].mock_calls == []
        assert mocks['_get_git_url'].mock_calls == []
        assert mocks['_is_git_dirty'].mock_calls == [call()]
        assert mocks['getcwd'].mock_calls == [call()]
        assert mocks['chdir'].mock_calls == [
            call(os.path.dirname(os.path.abspath(
                awslimitchecker.versioncheck.__file__))),
            call('/my/cwd')
        ]
        assert res == {
            'commit': None,
            'tag': None,
            'url': None,
            'dirty': None,
        }

    def test_get_dist_version_url(self):
        """pip 6.0+ - see issue #55"""
        dist = Mock(
            parsed_version=Version('1.2.3'),
            version='2.4.2',
            PKG_INFO='PKG-INFO',
        )
        metadata = [
            'Metadata-Version: 1.1',
            'Name: awslimitchecker',
            'Version: 0.1.0',
            'Summary: A script and python module to check your AWS service ',
            'Home-page: https://github.com/jantman/awslimitchecker',
            'Author: Jason Antman',
            'Author-email: jason@jasonantman.com',
            'License: UNKNOWN',
            'Description: awslimitchecker',
            '========================',
            '.. image:: https://pypip.in/v/awslimitchecker/badge.png',
            ':target: https://crate.io/packages/awslimitchecker',
            ':alt: PyPi package version',
            'Status',
            '------',
            'Keywords: AWS EC2 Amazon boto limits cloud',
            'Platform: UNKNOWN',
            'Classifier: Environment :: Console',
        ]

        def se_metadata(foo):
            for line in metadata:
                yield line

        dist.get_metadata_lines.side_effect = se_metadata
        cls = AGPLVersionChecker()
        res = cls._dist_version_url(dist)
        assert res == ('2.4.2',
                       'https://github.com/jantman/awslimitchecker')

    def test_get_dist_version_url_pip1(self):
        """pip 1.x - see issue #54"""
        dist = Mock(
            parsed_version=('00000002', '00000004', '00000002', '*final'),
            version='2.4.2',
            PKG_INFO='PKG-INFO',
        )
        metadata = [
            'Metadata-Version: 1.1',
            'Name: awslimitchecker',
            'Version: 0.1.0',
            'Summary: A script and python module to check your AWS service ',
            'Home-page: https://github.com/jantman/awslimitchecker',
            'Author: Jason Antman',
            'Author-email: jason@jasonantman.com',
            'License: UNKNOWN',
            'Description: awslimitchecker',
            '========================',
            '.. image:: https://pypip.in/v/awslimitchecker/badge.png',
            ':target: https://crate.io/packages/awslimitchecker',
            ':alt: PyPi package version',
            'Status',
            '------',
            'Keywords: AWS EC2 Amazon boto limits cloud',
            'Platform: UNKNOWN',
            'Classifier: Environment :: Console',
        ]

        def se_metadata(foo):
            for line in metadata:
                yield line

        dist.get_metadata_lines.side_effect = se_metadata
        cls = AGPLVersionChecker()
        res = cls._dist_version_url(dist)
        assert res == ('2.4.2',
                       'https://github.com/jantman/awslimitchecker')

    def test_get_dist_version_url_no_homepage(self):
        dist = Mock(
            version='1.2.3',
            PKG_INFO='PKG-INFO',
        )
        metadata = [
            'Metadata-Version: 1.1',
            'Name: awslimitchecker',
            'Version: 0.1.0',
            'Summary: A script and python module to check your AWS service ',
            'Author: Jason Antman',
            'Author-email: jason@jasonantman.com',
            'License: UNKNOWN',
            'Description: awslimitchecker',
            '========================',
            '.. image:: https://pypip.in/v/awslimitchecker/badge.png',
            ':target: https://crate.io/packages/awslimitchecker',
            ':alt: PyPi package version',
            'Status',
            '------',
            'Keywords: AWS EC2 Amazon boto limits cloud',
            'Platform: UNKNOWN',
            'Classifier: Environment :: Console',
        ]

        def se_metadata(foo):
            for line in metadata:
                yield line

        dist.get_metadata_lines.side_effect = se_metadata
        cls = AGPLVersionChecker()
        res = cls._dist_version_url(dist)
        assert res == ('1.2.3', None)

    def test_find_pip_info(self):
        cls = AGPLVersionChecker()
        mock_distA = Mock(autospec=True, project_name='awslimitchecker')
        mock_distB = Mock(autospec=True, project_name='other')
        mock_distC = Mock(autospec=True, project_name='another')
        installed_dists = [mock_distA, mock_distB, mock_distC]
        mock_frozen = Mock(
            autospec=True,
            req='awslimitchecker==0.1.0'
        )

        with patch('%s.pip.get_installed_distributions' % self.mpb
                   ) as mock_pgid:
            with patch('%s.pip.FrozenRequirement.from_dist' % self.mpb
                       ) as mock_from_dist:
                with patch('%s._dist_version_url' % self.pb) as mock_dist_vu:
                    mock_pgid.return_value = installed_dists
                    mock_from_dist.return_value = mock_frozen
                    mock_dist_vu.return_value = ('4.5.6', 'http://foo')
                    res = cls._find_pip_info()
        assert res == {'version': '4.5.6', 'url': 'http://foo'}
        assert mock_pgid.mock_calls == [call()]
        assert mock_from_dist.mock_calls == [call(mock_distA, [])]
        assert mock_dist_vu.mock_calls == [call(mock_distA)]

    def test_find_pip_info_no_dist(self):
        cls = AGPLVersionChecker()
        mock_distB = Mock(autospec=True, project_name='other')
        mock_distC = Mock(autospec=True, project_name='another')
        installed_dists = [mock_distB, mock_distC]
        mock_frozen = Mock(
            autospec=True,
            req='awslimitchecker==0.1.0'
        )

        with patch('%s.pip.get_installed_distributions' % self.mpb
                   ) as mock_pgid:
            with patch('%s.pip.FrozenRequirement.from_dist' % self.mpb
                       ) as mock_from_dist:
                with patch('%s._dist_version_url' % self.pb) as mock_dist_vu:
                    mock_pgid.return_value = installed_dists
                    mock_from_dist.return_value = mock_frozen
                    mock_dist_vu.return_value = ('4.5.6', 'http://foo')
                    res = cls._find_pip_info()
        assert res == {}
        assert mock_pgid.mock_calls == [call()]
        assert mock_from_dist.mock_calls == []
        assert mock_dist_vu.mock_calls == []

    def test_find_pip_info_req_https(self):
        req_str = 'git+https://github.com/jantman/awslimitchecker.git@76c7e51' \
                  'f6e83350c72a1d3e8122ee03e589bbfde#egg=awslimitchecker-master'
        cls = AGPLVersionChecker()
        mock_distA = Mock(autospec=True, project_name='awslimitchecker')
        mock_distB = Mock(autospec=True, project_name='other')
        mock_distC = Mock(autospec=True, project_name='another')
        installed_dists = [mock_distA, mock_distB, mock_distC]
        mock_frozen = Mock(
            autospec=True,
            req=req_str
        )

        with patch('%s.pip.get_installed_distributions' % self.mpb
                   ) as mock_pgid:
            with patch('%s.pip.FrozenRequirement.from_dist' % self.mpb
                       ) as mock_from_dist:
                with patch('%s._dist_version_url' % self.pb) as mock_dist_vu:
                    mock_pgid.return_value = installed_dists
                    mock_from_dist.return_value = mock_frozen
                    mock_dist_vu.return_value = ('4.5.6', 'http://foo')
                    res = cls._find_pip_info()
        assert res == {'version': '4.5.6', 'url': req_str}
        assert mock_pgid.mock_calls == [call()]
        assert mock_from_dist.mock_calls == [call(mock_distA, [])]
        assert mock_dist_vu.mock_calls == [call(mock_distA)]

    def test_find_pip_info_req_git(self):
        req_str = 'git+git@github.com:jantman/awslimitchecker.git@76c7e51f6e8' \
                  '3350c72a1d3e8122ee03e589bbfde#egg=awslimitchecker-master'
        cls = AGPLVersionChecker()
        mock_distA = Mock(autospec=True, project_name='awslimitchecker')
        mock_distB = Mock(autospec=True, project_name='other')
        mock_distC = Mock(autospec=True, project_name='another')
        installed_dists = [mock_distA, mock_distB, mock_distC]
        mock_frozen = Mock(
            autospec=True,
            req=req_str
        )

        with patch('%s.pip.get_installed_distributions' % self.mpb
                   ) as mock_pgid:
            with patch('%s.pip.FrozenRequirement.from_dist' % self.mpb
                       ) as mock_from_dist:
                with patch('%s._dist_version_url' % self.pb) as mock_dist_vu:
                    mock_pgid.return_value = installed_dists
                    mock_from_dist.return_value = mock_frozen
                    mock_dist_vu.return_value = ('4.5.6', 'http://foo')
                    res = cls._find_pip_info()
        assert res == {'version': '4.5.6', 'url': req_str}
        assert mock_pgid.mock_calls == [call()]
        assert mock_from_dist.mock_calls == [call(mock_distA, [])]
        assert mock_dist_vu.mock_calls == [call(mock_distA)]

    def test_find_pkg_info(self):
        cls = AGPLVersionChecker()
        mock_distA = Mock(autospec=True, project_name='awslimitchecker')
        with patch('%s.pkg_resources.require' % self.mpb) as mock_require:
            with patch('%s._dist_version_url' % self.pb) as mock_dvu:
                mock_require.return_value = [mock_distA]
                mock_dvu.return_value = ('7.8.9', 'http://foobar')
                res = cls._find_pkg_info()
        assert res == {'version': '7.8.9', 'url': 'http://foobar'}

    def test_find_package_version_git_notag(self):
        cls = AGPLVersionChecker()
        with patch.multiple(
            self.pb,
            autospec=True,
            _find_git_info=DEFAULT,
            _find_pip_info=DEFAULT,
            _find_pkg_info=DEFAULT,
        ) as mocks:
            mocks['_find_git_info'].return_value = {
                'url': 'git+https://foo',
                'tag': None,
                'commit': '12345678',
                'dirty': False
            }
            mocks['_find_pip_info'].return_value = {
                'version': '1.2.3',
                'url': 'http://my.package.url/pip'
            }
            mocks['_find_pkg_info'].return_value = {
                'version': '1.2.3',
                'url': 'http://my.package.url/pkg_resources'
            }
            res = cls.find_package_version()
        assert res == {
            'version': '1.2.3',
            'url': 'git+https://foo',
            'tag': None,
            'commit': '12345678',
            'dirty': False,
        }
        assert mocks['_find_git_info'].mock_calls == [call(cls)]
        assert mocks['_find_pip_info'].mock_calls == [call(cls)]
        assert mocks['_find_pkg_info'].mock_calls == [call(cls)]

    def test_find_package_version_git_notag_dirty(self):
        cls = AGPLVersionChecker()
        with patch.multiple(
            self.pb,
            autospec=True,
            _find_git_info=DEFAULT,
            _find_pip_info=DEFAULT,
            _find_pkg_info=DEFAULT,
        ) as mocks:
            mocks['_find_git_info'].return_value = {
                'url': 'git+https://foo',
                'tag': None,
                'commit': '12345678',
                'dirty': True
            }
            mocks['_find_pip_info'].return_value = {
                'version': '1.2.3',
                'url': 'http://my.package.url/pip'
            }
            mocks['_find_pkg_info'].return_value = {
                'version': '1.2.3',
                'url': 'http://my.package.url/pkg_resources'
            }
            res = cls.find_package_version()
        assert res == {
            'version': '1.2.3',
            'url': 'git+https://foo',
            'tag': None,
            'commit': '12345678*',
            'dirty': True,
        }
        assert mocks['_find_git_info'].mock_calls == [call(cls)]
        assert mocks['_find_pip_info'].mock_calls == [call(cls)]
        assert mocks['_find_pkg_info'].mock_calls == [call(cls)]

    def test_find_package_version_git_tag(self):
        cls = AGPLVersionChecker()
        with patch.multiple(
            self.pb,
            autospec=True,
            _find_git_info=DEFAULT,
            _find_pip_info=DEFAULT,
            _find_pkg_info=DEFAULT,
        ) as mocks:
            mocks['_find_git_info'].return_value = {
                'url': 'git+https://foo',
                'tag': 'mytag',
                'commit': '12345678',
                'dirty': False
            }
            mocks['_find_pip_info'].return_value = {
                'version': '1.2.3',
                'url': 'http://my.package.url/pip'
            }
            mocks['_find_pkg_info'].return_value = {
                'version': '1.2.3',
                'url': 'http://my.package.url/pkg_resources'
            }
            res = cls.find_package_version()
        assert res == {
            'version': '1.2.3',
            'url': 'git+https://foo',
            'tag': 'mytag',
            'commit': '12345678',
            'dirty': False,
        }
        assert mocks['_find_git_info'].mock_calls == [call(cls)]
        assert mocks['_find_pip_info'].mock_calls == [call(cls)]
        assert mocks['_find_pkg_info'].mock_calls == [call(cls)]

    def test_find_package_version_git_tag_dirty(self):
        cls = AGPLVersionChecker()
        with patch.multiple(
            self.pb,
            autospec=True,
            _find_git_info=DEFAULT,
            _find_pip_info=DEFAULT,
            _find_pkg_info=DEFAULT,
        ) as mocks:
            mocks['_find_git_info'].return_value = {
                'url': 'git+https://foo',
                'tag': 'mytag',
                'commit': '12345678',
                'dirty': True
            }
            mocks['_find_pip_info'].return_value = {
                'version': '1.2.3',
                'url': 'http://my.package.url/pip'
            }
            mocks['_find_pkg_info'].return_value = {
                'version': '1.2.3',
                'url': 'http://my.package.url/pkg_resources'
            }
            res = cls.find_package_version()
        assert res == {
            'version': '1.2.3',
            'url': 'git+https://foo',
            'tag': 'mytag*',
            'commit': '12345678*',
            'dirty': True,
        }
        assert mocks['_find_git_info'].mock_calls == [call(cls)]
        assert mocks['_find_pip_info'].mock_calls == [call(cls)]
        assert mocks['_find_pkg_info'].mock_calls == [call(cls)]

    def test_find_package_version_pkg_res_exception(self):
        cls = AGPLVersionChecker()

        def se_exception():
            raise Exception("some exception")

        with patch.multiple(
            self.pb,
            autospec=True,
            _find_git_info=DEFAULT,
            _find_pip_info=DEFAULT,
            _find_pkg_info=DEFAULT,
        ) as mocks:
            mocks['_find_git_info'].return_value = {
                'url': 'git+https://foo',
                'tag': None,
                'commit': '12345678',
                'dirty': False
            }
            mocks['_find_pip_info'].return_value = {
                'version': '1.2.3',
                'url': 'http://my.package.url/pip'
            }
            mocks['_find_pkg_info'].side_effect = se_exception
            res = cls.find_package_version()
        assert res == {
            'version': '1.2.3',
            'url': 'git+https://foo',
            'tag': None,
            'commit': '12345678',
            'dirty': False,
        }
        assert mocks['_find_git_info'].mock_calls == [call(cls)]
        assert mocks['_find_pip_info'].mock_calls == [call(cls)]
        assert mocks['_find_pkg_info'].mock_calls == [call(cls)]

    def test_find_package_version_pip_exception(self):
        cls = AGPLVersionChecker()

        def se_exception():
            raise Exception("some exception")

        with patch.multiple(
            self.pb,
            autospec=True,
            _find_git_info=DEFAULT,
            _find_pip_info=DEFAULT,
            _find_pkg_info=DEFAULT,
        ) as mocks:
            mocks['_find_git_info'].return_value = {
                'url': 'git+https://foo',
                'tag': None,
                'commit': '12345678',
                'dirty': False
            }
            mocks['_find_pip_info'].side_effect = se_exception
            mocks['_find_pkg_info'].return_value = {
                'version': '1.2.3',
                'url': 'http://my.package.url/pkg_resources'
            }
            res = cls.find_package_version()
        assert res == {
            'version': '1.2.3',
            'url': 'git+https://foo',
            'tag': None,
            'commit': '12345678',
            'dirty': False,
        }
        assert mocks['_find_git_info'].mock_calls == [call(cls)]
        assert mocks['_find_pip_info'].mock_calls == [call(cls)]
        assert mocks['_find_pkg_info'].mock_calls == [call(cls)]

    def test_find_package_version_no_git(self):
        cls = AGPLVersionChecker()

        with patch.multiple(
            self.pb,
            autospec=True,
            _find_git_info=DEFAULT,
            _find_pip_info=DEFAULT,
            _find_pkg_info=DEFAULT,
        ) as mocks:
            mocks['_find_git_info'].return_value = {
                'url': None,
                'tag': None,
                'commit': None,
                'dirty': None,
            }
            mocks['_find_pip_info'].return_value = {
                'version': '1.2.3',
                'url': 'http://my.package.url/pip'
            }
            mocks['_find_pkg_info'].return_value = {
                'version': '1.2.3',
                'url': 'http://my.package.url/pkg_resources'
            }
            res = cls.find_package_version()
        assert res == {
            'version': '1.2.3',
            'url': 'http://my.package.url/pip',
            'tag': None,
            'commit': None,
        }
        assert mocks['_find_git_info'].mock_calls == [call(cls)]
        assert mocks['_find_pip_info'].mock_calls == [call(cls)]
        assert mocks['_find_pkg_info'].mock_calls == [call(cls)]

    def test_find_package_version_no_git_no_pip(self):
        cls = AGPLVersionChecker()

        def se_exception():
            raise Exception("some exception")

        with patch.multiple(
            self.pb,
            autospec=True,
            _find_git_info=DEFAULT,
            _find_pip_info=DEFAULT,
            _find_pkg_info=DEFAULT,
        ) as mocks:
            mocks['_find_git_info'].return_value = {
                'url': None,
                'tag': None,
                'commit': None,
                'dirty': None,
            }
            mocks['_find_pip_info'].side_effect = se_exception
            mocks['_find_pkg_info'].return_value = {
                'version': '1.2.3',
                'url': 'http://my.package.url/pkg_resources'
            }
            res = cls.find_package_version()
        assert res == {
            'version': '1.2.3',
            'url': 'http://my.package.url/pkg_resources',
            'tag': None,
            'commit': None,
        }
        assert mocks['_find_git_info'].mock_calls == [call(cls)]
        assert mocks['_find_pip_info'].mock_calls == [call(cls)]
        assert mocks['_find_pkg_info'].mock_calls == [call(cls)]

    def test_find_package_version_debug(self):
        mock_pip_logger = Mock(spec_set=logging.Logger)

        with patch.dict('%s.os.environ' % self.mpb,
                        {'VERSIONCHECK_DEBUG': 'true'}):
            with patch('%s.logging' % self.mpb) as mock_logging:
                cls = AGPLVersionChecker()
                with patch.multiple(
                        self.pb,
                        autospec=True,
                        _find_git_info=DEFAULT,
                        _find_pip_info=DEFAULT,
                        _find_pkg_info=DEFAULT,
                ) as mocks:
                    mocks['_find_git_info'].return_value = {
                        'url': None,
                        'tag': None,
                        'commit': None,
                        'dirty': None,
                    }
                    mocks['_find_pip_info'].return_value = {
                        'version': '1.2.3',
                        'url': 'http://my.package.url/pip'
                    }
                    mocks['_find_pkg_info'].return_value = {
                        'version': '1.2.3',
                        'url': 'http://my.package.url/pkg_resources'
                    }
                    with patch('%s.logger' % self.mpb,
                               spec_set=logging.Logger) as mock_mod_logger:
                        mock_logging.getLogger.return_value = mock_pip_logger
                        cls.find_package_version()
        assert mock_logging.mock_calls == []
        assert mock_pip_logger.mock_calls == []
        assert mock_mod_logger.mock_calls == [
            call.debug('Git info: %s',
                       {'url': None, 'commit': None, 'tag': None,
                        'dirty': None}),
            call.debug('pip info: %s', {'url': 'http://my.package.url/pip',
                                        'version': '1.2.3'}),
            call.debug('pkg_resources info: %s',
                       {'url': 'http://my.package.url/pkg_resources',
                        'version': '1.2.3'}),
            call.debug('Final package info: %s',
                       {'url': 'http://my.package.url/pip', 'commit': None,
                        'version': '1.2.3', 'tag': None})
        ]

    def test_find_package_version_no_debug(self):
        mock_pip_logger = Mock()
        type(mock_pip_logger).propagate = False

        with patch.dict('%s.os.environ' % self.mpb,
                        {'VERSIONCHECK_DEBUG': 'false'}):
            with patch('%s.logging' % self.mpb) as mock_logging:
                mock_logging.getLogger.return_value = mock_pip_logger
                cls = AGPLVersionChecker()
                with patch.multiple(
                        self.pb,
                        autospec=True,
                        _find_git_info=DEFAULT,
                        _find_pip_info=DEFAULT,
                        _find_pkg_info=DEFAULT,
                ) as mocks:
                    mocks['_find_git_info'].return_value = {
                        'url': None,
                        'tag': None,
                        'commit': None,
                        'dirty': None,
                    }
                    mocks['_find_pip_info'].return_value = {
                        'version': '1.2.3',
                        'url': 'http://my.package.url/pip'
                    }
                    mocks['_find_pkg_info'].return_value = {
                        'version': '1.2.3',
                        'url': 'http://my.package.url/pkg_resources'
                    }
                    with patch('%s.logger' % self.mpb,
                               spec_set=logging.Logger) as mock_mod_logger:
                        cls.find_package_version()
        assert mock_logging.mock_calls == [
            call.getLogger("pip"),
            call.getLogger().setLevel(mock_logging.WARNING)
        ]
        assert mock_pip_logger.mock_calls == [
            call.setLevel(mock_logging.WARNING),
        ]
        assert mock_mod_logger.mock_calls == [
            call.setLevel(mock_logging.WARNING),
            call.debug('Git info: %s',
                       {'url': None, 'commit': None, 'tag': None,
                        'dirty': None}),
            call.debug('pip info: %s', {'url': 'http://my.package.url/pip',
                                        'version': '1.2.3'}),
            call.debug('pkg_resources info: %s',
                       {'url': 'http://my.package.url/pkg_resources',
                        'version': '1.2.3'}),
            call.debug('Final package info: %s',
                       {'url': 'http://my.package.url/pip', 'commit': None,
                        'version': '1.2.3', 'tag': None})
        ]


class Test_VersionCheck_Funcs(object):
    """
    Mocked unit tests for versioncheck functions
    """

    pb = 'awslimitchecker.versioncheck'

    def test_get_git_url_simple(self):
        cmd_out = '' \
                "origin  git@github.com:jantman/awslimitchecker.git (fetch)\n" \
                "origin  git@github.com:jantman/awslimitchecker.git (push)\n"
        with patch('%s._check_output' % self.pb) as mock_check_out:
            mock_check_out.return_value = cmd_out
            res = _get_git_url()
        assert res == 'git@github.com:jantman/awslimitchecker.git'
        assert mock_check_out.mock_calls == [
            call(['git', 'remote', '-v'], stderr=DEVNULL)
        ]

    def test_get_git_url_fork(self):
        cmd_out = "origin  git@github.com:someone/awslimitchecker.git (fetch" \
                  ")\n" \
                  "origin  git@github.com:someone/awslimitchecker.git (push)" \
                  "\n" \
                  "upstream        https://github.com/jantman/awslimitchecke" \
                  "r.git (fetch)\n" \
                  "upstream        https://github.com/jantman/awslimitchecker" \
                  ".git (push)\n"
        with patch('%s._check_output' % self.pb) as mock_check_out:
            mock_check_out.return_value = cmd_out
            res = _get_git_url()
        assert res == 'git@github.com:someone/awslimitchecker.git'
        assert mock_check_out.mock_calls == [
            call(['git', 'remote', '-v'], stderr=DEVNULL)
        ]

    def test_get_git_url_no_origin(self):
        cmd_out = "mine  git@github.com:someone/awslimitchecker.git (fetch" \
                  ")\n" \
                  "mine  git@github.com:someone/awslimitchecker.git (push)" \
                  "\n" \
                  "upstream        https://github.com/jantman/awslimitchecke" \
                  "r.git (fetch)\n" \
                  "upstream        https://github.com/jantman/awslimitchecker" \
                  ".git (push)\n" \
                  "another        https://github.com/foo/awslimitchecke" \
                  "r.git (fetch)\n" \
                  "another        https://github.com/foo/awslimitchecker" \
                  ".git (push)\n"
        with patch('%s._check_output' % self.pb) as mock_check_out:
            mock_check_out.return_value = cmd_out
            res = _get_git_url()
        assert res == 'https://github.com/foo/awslimitchecker.git'
        assert mock_check_out.mock_calls == [
            call(['git', 'remote', '-v'], stderr=DEVNULL)
        ]

    def test_get_git_url_exception(self):

        def se(foo, stderr=None):
            raise subprocess.CalledProcessError(3, 'mycommand')

        with patch('%s._check_output' % self.pb) as mock_check_out:
            mock_check_out.side_effect = se
            res = _get_git_url()
        assert res is None
        assert mock_check_out.mock_calls == [
            call(['git', 'remote', '-v'], stderr=DEVNULL)
        ]

    def test_get_git_url_none(self):
        cmd_out = ''
        with patch('%s._check_output' % self.pb) as mock_check_out:
            mock_check_out.return_value = cmd_out
            res = _get_git_url()
        assert res is None
        assert mock_check_out.mock_calls == [
            call(['git', 'remote', '-v'], stderr=DEVNULL)
        ]

    def test_get_git_url_no_fetch(self):
        cmd_out = "mine  git@github.com:someone/awslimitchecker.git (push)" \
                  "\n" \
                  "upstream        https://github.com/jantman/awslimitchecker" \
                  ".git (push)\n" \
                  "another        https://github.com/jantman/awslimitchecker" \
                  ".git (push)\n"
        with patch('%s._check_output' % self.pb) as mock_check_out:
            mock_check_out.return_value = cmd_out
            res = _get_git_url()
        assert res is None
        assert mock_check_out.mock_calls == [
            call(['git', 'remote', '-v'], stderr=DEVNULL)
        ]

    def test_get_git_tag(self):
        with patch('%s._check_output' % self.pb) as mock_check_out:
            mock_check_out.return_value = 'mytag'
            res = _get_git_tag('abcd')
        assert res == 'mytag'
        assert mock_check_out.mock_calls == [
            call(['git', 'describe', '--exact-match', '--tags', 'abcd'],
                 stderr=DEVNULL)
        ]

    def test_get_git_tag_commit_none(self):
        with patch('%s._check_output' % self.pb) as mock_check_out:
            mock_check_out.return_value = 'mytag'
            res = _get_git_tag(None)
        assert res is None
        assert mock_check_out.mock_calls == []

    def test_get_git_tag_no_tags(self):
        with patch('%s._check_output' % self.pb) as mock_check_out:
            mock_check_out.return_value = ''
            res = _get_git_tag('abcd')
        assert res is None
        assert mock_check_out.mock_calls == [
            call(['git', 'describe', '--exact-match', '--tags', 'abcd'],
                 stderr=DEVNULL)
        ]

    def test_get_git_tag_exception(self):

        def se(foo, stderr=None):
            raise subprocess.CalledProcessError(3, 'mycommand')

        with patch('%s._check_output' % self.pb) as mock_check_out:
            mock_check_out.side_effect = se
            res = _get_git_tag('abcd')
        assert res is None
        assert mock_check_out.mock_calls == [
            call(['git', 'describe', '--exact-match', '--tags', 'abcd'],
                 stderr=DEVNULL)
        ]

    def test_get_git_commit(self):
        with patch('%s._check_output' % self.pb) as mock_check_out:
            mock_check_out.return_value = '1234abcd'
            res = _get_git_commit()
        assert res == '1234abcd'
        assert mock_check_out.mock_calls == [
            call(['git', 'rev-parse', '--short', 'HEAD'],
                 stderr=DEVNULL)
        ]

    def test_get_git_commit_exception(self):

        def se(foo):
            raise subprocess.CalledProcessError(3, 'mycommand')

        with patch('%s._check_output' % self.pb) as mock_check_out:
            mock_check_out.side_effect = se
            res = _get_git_commit()
        assert res is None
        assert mock_check_out.mock_calls == [
            call(['git', 'rev-parse', '--short', 'HEAD'],
                 stderr=DEVNULL)
        ]

    @pytest.mark.skipif(
        (
                sys.version_info[0] != 2 or
                (sys.version_info[0] == 2 and sys.version_info[1] != 6)
        ),
        reason='not running py26 test on %d.%d.%d' % (
                sys.version_info[0],
                sys.version_info[1],
                sys.version_info[2]
        ))
    def test_check_output_py26(self):
        mock_p = Mock(returncode=0)
        mock_p.communicate.return_value = ('foo', 'bar')
        with patch('%s.subprocess.Popen' % self.pb) as mock_popen:
            mock_popen.return_value = mock_p
            res = _check_output(['mycmd'], stderr='something')
        assert res == 'foo'
        assert mock_popen.mock_calls == [
            call(
                ['mycmd'],
                stderr='something',
                stdout=subprocess.PIPE
            ),
            call().communicate()
        ]

    @pytest.mark.skipif(
        (
                sys.version_info[0] != 2 or
                (sys.version_info[0] == 2 and sys.version_info[1] != 6)
        ),
        reason='not running py26 test on %d.%d.%d' % (
                sys.version_info[0],
                sys.version_info[1],
                sys.version_info[2]
        ))
    def test_check_output_py26_exception(self):
        mock_p = Mock(returncode=2)
        mock_p.communicate.return_value = ('foo', 'bar')
        with patch('%s.subprocess.Popen' % self.pb) as mock_popen:
            mock_popen.return_value = mock_p
            with pytest.raises(subprocess.CalledProcessError) as exc:
                _check_output(['mycmd'], stderr='something')
        assert mock_popen.mock_calls == [
            call(
                ['mycmd'],
                stderr='something',
                stdout=subprocess.PIPE
            ),
            call().communicate()
        ]
        assert exc.value.cmd == ['mycmd']
        assert exc.value.returncode == 2

    @pytest.mark.skipif(
        (
                sys.version_info[0] != 2 or
                (sys.version_info[0] == 2 and sys.version_info[1] != 7)
        ),
        reason='not running py27 test on %d.%d.%d' % (
                sys.version_info[0],
                sys.version_info[1],
                sys.version_info[2]
        ))
    def test_check_output_py27(self):
        with patch('%s.subprocess.check_output' % self.pb) as mock_check_out:
            mock_check_out.return_value = 'foobar'
            res = _check_output(['foo', 'bar'], stderr='something')
        assert res == 'foobar'
        assert mock_check_out.mock_calls == [
            call(['foo', 'bar'], stderr='something')
        ]

    @pytest.mark.skipif(sys.version_info[0] < 3,
                        reason='not running py3 test on %d.%d.%d' % (
                            sys.version_info[0],
                            sys.version_info[1],
                            sys.version_info[2]
                        ))
    def test_check_output_py3(self):
        with patch('%s.subprocess.check_output' % self.pb) as mock_check_out:
            mock_check_out.return_value = 'foobar'.encode('utf-8')
            res = _check_output(['foo', 'bar'], stderr='something')
        assert res == 'foobar'
        assert mock_check_out.mock_calls == [
            call(['foo', 'bar'], stderr='something')
        ]


@pytest.mark.versioncheck
class Test_AGPLVersionChecker_Acceptance(object):
    """
    Long-running acceptance tests for AGPLVersionChecker, which create venvs,
    install the code in them, and test the output
    """

    git_commit = None
    git_tag = None

    def setup_method(self, method):
        os.environ['VERSIONCHECK_DEBUG'] = 'true'
        print("\n")
        self._set_git_config()
        self.current_venv_path = sys.prefix
        self.source_dir = self._get_source_dir()
        self.git_commit = _get_git_commit()
        self.git_tag = _get_git_tag(self.git_commit)
        self.git_url = _get_git_url()
        print({
            'self.source_dir': self.source_dir,
            'self.git_commit': self.git_commit,
            'self.git_tag': self.git_tag,
            'self.git_url': self.git_url,
        })
        print(_check_output([
                'git',
                'show-ref',
                '--tags'
        ]).strip())

    def teardown_method(self, method):
        tag = _get_git_tag(self.git_commit)
        print("\n")
        if tag is not None:
            subprocess.call([
                'git',
                'tag',
                '--delete',
                tag
            ])
        try:
            if 'testremote' in _check_output([
                'git',
                'remote',
                '-v'
            ]):
                print("Removing 'testremote' git remote")
                subprocess.call([
                    'git',
                    'remote',
                    'remove',
                    'testremote'
                ])
        except subprocess.CalledProcessError:
            pass

    def _set_git_config(self):
        if os.environ.get('TRAVIS', '') != 'true':
            print("not running in Travis; not setting git config")
            return
        try:
            res = _check_output([
                'git',
                'config',
                'user.email'
            ]).strip()
        except subprocess.CalledProcessError as ex:
            res = None
        if res != '' and res is not None:
            print("Got git config user.email as %s" % res)
        else:
            subprocess.call([
                'git',
                'config',
                'user.email',
                'travisci@jasonantman.com'
            ])
            print("Set git config user.email")
        # name
        try:
            res = _check_output([
                'git',
                'config',
                'user.name'
            ]).strip()
        except subprocess.CalledProcessError as ex:
            print(ex)
            res = None
        if res != '' and res is not None:
            print("Got git config user.name as %s" % res)
        else:
            subprocess.call([
                'git',
                'config',
                'user.name',
                'travisci'
            ])
            print("Set git config user.name")

    def _set_git_tag(self, tagname):
        """set a git tag for the current commit"""
        tag = _get_git_tag(self.git_commit)
        if tag != tagname:
            print("Creating git tag 'versiontest' of %s" % self.git_commit)
            subprocess.call([
                'git',
                'tag',
                '-a',
                '-m',
                tagname,
                tagname
            ])
            tag = _get_git_tag(self.git_commit)
        print("Source git tag: %s" % tag)
        self.git_tag = tag
        return tag

    def _make_venv(self, path):
        """
        Create a venv in ``path``. Make sure it exists.

        :param path: filesystem path to directory to make the venv base
        """
        virtualenv = os.path.join(self.current_venv_path, 'bin', 'virtualenv')
        assert os.path.exists(virtualenv) is True, 'virtualenv not found'
        args = [virtualenv, path]
        print("\n" + "#" * 20 + " running: " + ' '.join(args) + "#" * 20)
        res = subprocess.call(args)
        if res == 0:
            print("\n" + "#" * 20 + " DONE: " + ' '.join(args) + "#" * 20)
        else:
            print("\n" + "#" * 20 + " FAILED: " + ' '.join(args) + "#" * 20)
        pypath = os.path.join(path, 'bin', 'python')
        assert os.path.exists(pypath) is True, "does not exist: %s" % pypath

    def _get_source_dir(self):
        """
        Determine the directory containing the project source. This is assumed
        to be either the TOXINIDIR environment variable, or determined relative
        to this file.

        :returns: path to the awslimitchecker source
        :rtype: str
        """
        s = os.environ.get('TOXINIDIR', None)
        if s is None:
            s = os.path.abspath(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    '..',
                    '..'
                )
            )
        assert os.path.exists(s)
        return s

    def _pip_install(self, path, args):
        """
        In the virtualenv at ``path``, run ``pip install [args]``.

        :param path: venv base/root path
        :param args: ``pip install`` arguments
        """
        pip = os.path.join(path, 'bin', 'pip')
        # get pip version
        res = subprocess.call([pip, '--version'])
        assert res == 0
        # install ALC in it
        final_args = [pip, 'install']
        final_args.extend(args)
        print("\n" + "#" * 20 + " running: " + ' '.join(final_args) + "#" * 20)
        res = subprocess.call(final_args)
        print("\n" + "#" * 20 + " DONE: " + ' '.join(final_args) + "#" * 20)
        assert res == 0

    def _get_alc_version(self, path):
        """
        In the virtualenv at ``path``, run ``awslimitchecker --version`` and
        return the string output.

        :param path: venv base/root path
        :return: version command output
        :rtype: str
        """
        alc = os.path.join(path, 'bin', 'awslimitchecker')
        args = [alc, '--version', '-vv']
        print("\n" + "#" * 20 + " running: " + ' '.join(args) + "#" * 20)
        res = _check_output(args, stderr=subprocess.STDOUT)
        print(res)
        print("\n" + "#" * 20 + " DONE: " + ' '.join(args) + "#" * 20)
        # confirm the git status
        print(self._get_git_status(path))
        # print(self._get_git_status(os.path.dirname(__file__)))
        return res

    def _get_git_status(self, path):
        header = "#" * 20 + " running: git status in: %s " % path + "#" * 20
        oldcwd = os.getcwd()
        os.chdir(path)
        try:
            status = _check_output(['git', 'status'],
                                   stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            status = ''
        os.chdir(oldcwd)
        footer = "#" * 20 + " DONE: git status " + "#" * 20
        if status == '':
            return "\n# git status exited non-0\n"
        return "\n" + header + "\n" + status + "\n" + footer + "\n"

    def _make_package(self, pkg_type, test_tmp_dir):
        """
        Use setup.py in the current (tox) virtualenv to build a package
        of the current project, of the specified ``pkg_type`` (sdist|bdist|
        bdist_wheel). Return the absolute path to the created archive/
        package.

        :param pkg_type: str, type of package to create
        :param test_tmp_dir: str, temporary dir for this test
        :return: absolute path to the package file
        :rtype: str
        """
        pkgdir = os.path.join(test_tmp_dir, 'pkg')
        if os.path.exists(pkgdir):
            print("removing: %s" % pkgdir)
            shutil.rmtree(pkgdir)
        args = [
            sys.executable,
            os.path.join(self.source_dir, 'setup.py'),
            pkg_type,
            '--dist-dir',
            pkgdir
        ]
        assert os.path.exists(
            args[0]) is True, "path does not exist: %s" % args[0]
        assert os.path.exists(
            args[1]) is True, "path does not exist: %s" % args[1]
        print("\n" + "#" * 20 + " running: " + ' '.join(args) + "#" * 20)
        print("# cwd: %s\n" % os.getcwd())
        try:
            subprocess.call(args)
        except Exception as ex:
            print("\nFAILED:")
            print(ex)
            print("\n")
        print("\n" + "#" * 20 + " DONE: " + ' '.join(args) + "#" * 20)
        assert os.path.exists(
            args[4]) is True, "path does not exist: %s" % args[4]
        files = os.listdir(pkgdir)
        assert len(files) == 1
        fpath = os.path.join(pkgdir, files[0])
        assert os.path.exists(fpath) is True
        return fpath

    def _check_git_pushed(self):
        """
        returns a trinary:
        0 - up-to-date and clean
        1 - not equal to origin
        2 - dirty

        :return: int
        """
        status = _check_output([
            'git',
            'status',
            '-u'
        ]).strip()
        if ('Your branch is up-to-date with' not in status and
                'HEAD detached at' not in status):
            print("\ngit status -u:\n" + status + "\n")
            return 1
        if 'nothing to commit' not in status:
            print("\ngit status -u:\n" + status + "\n")
            return 2
        return 0

    ################
    # Actual Tests #
    ################

    def test_install_local(self, tmpdir):
        path = str(tmpdir)
        # make the venv
        self._make_venv(path)
        self._pip_install(path, [self.source_dir])
        version_output = self._get_alc_version(path)
        expected = 'awslimitchecker {v} (see <{u}> for source code)'.format(
            v=_VERSION,
            u='https://github.com/jantman/awslimitchecker'
        )
        assert expected in version_output

    def test_install_local_e(self, tmpdir):
        path = str(tmpdir)
        # make the venv
        self._make_venv(path)
        self._pip_install(path, ['-e', self.source_dir])
        version_output = self._get_alc_version(path)
        expected_commit = self.git_commit
        if self._check_git_pushed() != 0:
            expected_commit += '*'
        expected = 'awslimitchecker {v} (see <{u}> for source code)'.format(
            v='%s@%s' % (_VERSION, expected_commit),
            u=self.git_url
        )
        assert expected in version_output

    def test_install_local_e_dirty(self, tmpdir):
        path = str(tmpdir)
        # make the venv
        self._make_venv(path)
        self._pip_install(path, ['-e', self.source_dir])
        fpath = os.path.join(self.source_dir, 'awslimitchecker', 'testfile')
        print("Creating junk file at %s" % fpath)
        with open(fpath, 'w') as fh:
            fh.write("testing")
        version_output = self._get_alc_version(path)
        print("Removing junk file at %s" % fpath)
        os.unlink(fpath)
        expected_commit = self.git_commit + '*'
        expected = 'awslimitchecker {v} (see <{u}> for source code)'.format(
            v='%s@%s' % (_VERSION, expected_commit),
            u=self.git_url
        )
        assert expected in version_output

    def test_install_local_e_tag(self, tmpdir):
        path = str(tmpdir)
        # make the venv
        self._set_git_tag('versioncheck')
        self._make_venv(path)
        self._pip_install(path, ['-e', self.source_dir])
        version_output = self._get_alc_version(path)
        expected_tag = 'versioncheck'
        if self._check_git_pushed() != 0:
            expected_tag += '*'
        expected = 'awslimitchecker {v} (see <{u}> for source code)'.format(
            v='%s@%s' % (_VERSION, expected_tag),
            u=self.git_url
        )
        assert expected in version_output

    def test_install_local_e_multiple_remotes(self, tmpdir):
        path = str(tmpdir)
        url = self.git_url
        # make the venv
        subprocess.call([
                'git',
                'remote',
                'add',
                'testremote',
                'https://github.com/jantman/awslimitchecker.git'
            ])
        self._make_venv(path)
        self._pip_install(path, ['-e', self.source_dir])
        version_output = self._get_alc_version(path)
        expected_commit = self.git_commit
        if self._check_git_pushed() != 0:
            expected_commit += '*'
        expected = 'awslimitchecker {v} (see <{u}> for source code)'.format(
            v='%s@%s' % (_VERSION, expected_commit),
            u=url
        )
        assert expected in version_output

    def test_install_sdist(self, tmpdir):
        path = str(tmpdir)
        # make the venv
        self._make_venv(path)
        # build the sdist
        pkg_path = self._make_package('sdist', path)
        # install ALC in it
        self._pip_install(path, [pkg_path])
        version_output = self._get_alc_version(path)
        expected = 'awslimitchecker {v} (see <{u}> for source code)'.format(
            v=_VERSION,
            u='https://github.com/jantman/awslimitchecker'
        )
        assert expected in version_output

    def test_install_sdist_pip154(self, tmpdir):
        """regression test for issue #55"""
        path = str(tmpdir)
        # make the venv
        self._make_venv(path)
        # build the sdist
        pkg_path = self._make_package('sdist', path)
        # ensure pip at 1.5.4
        self._pip_install(path, ['--force-reinstall', 'pip==1.5.4'])
        # install ALC in it
        self._pip_install(path, [pkg_path])
        version_output = self._get_alc_version(path)
        expected = 'awslimitchecker {v} (see <{u}> for source code)'.format(
            v=_VERSION,
            u='https://github.com/jantman/awslimitchecker'
        )
        assert expected in version_output

    def test_install_bdist_wheel(self, tmpdir):
        path = str(tmpdir)
        # make the venv
        self._make_venv(path)
        # build the sdist
        pkg_path = self._make_package('bdist_wheel', path)
        # install ALC in it
        self._pip_install(path, [pkg_path])
        version_output = self._get_alc_version(path)
        expected = 'awslimitchecker {v} (see <{u}> for source code)'.format(
            v=_VERSION,
            u='https://github.com/jantman/awslimitchecker'
        )
        assert expected in version_output

    # this doesn't work on PRs, because we can't check out the hash
    @pytest.mark.skipif(os.environ.get('TRAVIS_PULL_REQUEST', 'false') !=
                        'false', reason='git tests dont work on PRs')
    def test_install_git(self, tmpdir):
        # https://pip.pypa.io/en/latest/reference/pip_install.html#git
        status = self._check_git_pushed()
        assert status != 1, "git clone not equal to origin"
        assert status != 2, 'git clone is dirty'
        commit = _get_git_commit()
        path = str(tmpdir)
        # make the venv
        self._make_venv(path)
        self._pip_install(path, [
            'git+https://github.com/jantman/awslimitchecker.git'
            '@{c}#egg=awslimitchecker'.format(c=commit)
        ])
        version_output = self._get_alc_version(path)
        expected = 'awslimitchecker {v} (see <{u}> for source code)'.format(
            v=_VERSION,
            u='https://github.com/jantman/awslimitchecker'
        )
        assert expected in version_output

    # this doesn't work on PRs, because we can't check out the hash
    @pytest.mark.skipif(os.environ.get('TRAVIS_PULL_REQUEST', 'false') !=
                        'false', reason='git tests dont work on PRs')
    def test_install_git_e(self, tmpdir):
        # https://pip.pypa.io/en/latest/reference/pip_install.html#git
        status = self._check_git_pushed()
        assert status != 1, "git clone not equal to origin"
        assert status != 2, 'git clone is dirty'
        commit = _get_git_commit()
        path = str(tmpdir)
        print(_check_output([
            'git',
            'show-ref',
            '--tags'
        ]).strip())
        print("# commit=%s path=%s" % (commit, path))
        # make the venv
        self._make_venv(path)
        self._pip_install(path, [
            '-e',
            'git+https://github.com/jantman/awslimitchecker.git'
            '@{c}#egg=awslimitchecker'.format(c=commit)
        ])
        version_output = self._get_alc_version(path)
        expected = 'awslimitchecker {v} (see <{u}> for source code)'.format(
            v='%s@%s' % (_VERSION, commit),
            u='https://github.com/jantman/awslimitchecker.git'
        )
        assert expected in version_output

    # this doesn't work on PRs, because we can't check out the hash
    @pytest.mark.skipif(os.environ.get('TRAVIS_PULL_REQUEST', 'false') !=
                        'false', reason='git tests dont work on PRs')
    def test_install_git_e_dirty(self, tmpdir):
        # https://pip.pypa.io/en/latest/reference/pip_install.html#git
        status = self._check_git_pushed()
        assert status != 1, "git clone not equal to origin"
        assert status != 2, 'git clone is dirty'
        commit = _get_git_commit()
        path = str(tmpdir)
        print(_check_output([
            'git',
            'show-ref',
            '--tags'
        ]).strip())
        print("# commit=%s path=%s" % (commit, path))
        # make the venv
        self._make_venv(path)
        self._pip_install(path, [
            '-e',
            'git+https://github.com/jantman/awslimitchecker.git'
            '@{c}#egg=awslimitchecker'.format(c=commit)
        ])
        fpath = os.path.join(path, 'src', 'awslimitchecker', 'testfile')
        print("Creating junk file at %s" % fpath)
        with open(fpath, 'w') as fh:
            fh.write("testing")
        version_output = self._get_alc_version(path)
        expected = 'awslimitchecker {v} (see <{u}> for source code)'.format(
            v='%s@%s*' % (_VERSION, commit),
            u='https://github.com/jantman/awslimitchecker.git'
        )
        assert expected in version_output
