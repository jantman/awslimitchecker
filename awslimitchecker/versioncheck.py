"""
awslimitchecker/versioncheck.py

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

import os
import subprocess
import logging
import re
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')
logger = logging.getLogger(__name__)


class AGPLVersionChecker(object):

    def find_package_version(self):
        """
        Find the installed version of the specified package, and as much
        information about it as possible (source URL, git ref or tag, etc.)

        This attempts, to the best of our ability, to find out if the package
        was installed from git, and if so, provide information on the origin
        of that git repository and status of the clone. Otherwise, it uses
        pip and pkg_resources to find the version and homepage of the installed
        distribution.

        This class is not a sure-fire method of identifying the source of
        the distribution or ensuring AGPL compliance; it simply helps with this
        process _iff_ a modified version is installed from an editable git URL
        _and_ all changes are pushed up to the publicly-visible origin.

        Returns a dict with keys 'version', 'tag', 'commit', and 'url'.
        Values are strings or None.

        :param package_name: name of the package to find information for
        :type package_name: str
        :returns: information about the installed version of the package
        :rtype: dict
        """
        res = {
            'version': None,
            'url': None,
            'tag': None,
            'commit': None
        }
        git_info = self._find_git_info()
        logger.debug("Git info: %s", git_info)
        for k, v in git_info.items():
            if v is not None:
                res[k] = v
        try:
            dirty = self._is_git_dirty()
        except Exception:
            dirty = False
        if dirty and res['tag'] is not None:
            res['tag'] += '*'
        if dirty and res['commit'] is not None:
            res['commit'] += '*'
        try:
            pip_info = self._find_pip_info()
        except Exception:
            # we NEVER want this to crash the program
            pip_info = {}
        logger.debug("pip info: %s", pip_info)
        if 'version' in pip_info:
            res['version'] = pip_info['version']
        if 'url' in pip_info and res['url'] is None:
            res['url'] = pip_info['url']
        try:
            pkg_info = self._find_pkg_info()
        except Exception:
            pkg_info = {}
        logger.debug("pkg_resources info: %s", pkg_info)
        if 'version' in pkg_info and res['version'] is None:
            res['version'] = pkg_info['version']
        if 'url' in pkg_info and res['url'] is None:
            res['url'] = pkg_info['url']
        logger.debug("Final package info: %s", res)
        return res

    def _find_pkg_info(self):
        """
        Find information about the installed awslimitchecker from pkg_resources.

        :return: dict of information from pkg_resources
        """
        import pkg_resources
        dist = pkg_resources.require('awslimitchecker')[0]
        ver, url = self._dist_version_url(dist)
        return {'version': ver, 'url': url}

    def _find_pip_info(self):
        """
        Try to find information about the installed awslimitchecker from pip.
        This should be wrapped in a try/except.

        :return: dict of information from pip
        """
        import pip
        res = {}
        dist = None
        for d in pip.get_installed_distributions():
            if d.project_name == 'awslimitchecker':
                dist = d
        if dist is None:
            return res
        ver, url = self._dist_version_url(dist)
        res['version'] = ver
        # this is a bit of an ugly, lazy hack...
        req = pip.FrozenRequirement.from_dist(dist, [])
        if ':' in req.req or '@' in req.req:
            res['url'] = req.req
        else:
            res['url'] = url
        return res

    def _dist_version_url(self, dist):
        """get version and homepage for a pkg_resources.Distribution"""
        ver = str(dist.parsed_version)
        url = None
        for line in dist.get_metadata_lines(dist.PKG_INFO):
            line = line.strip()
            if ':' not in line:
                continue
            (k, v) = line.split(':', 1)
            if k == 'Home-page':
                url = v.strip()
        return (ver, url)

    def _find_git_info(self):
        """
        Find information about the git repository, if this file is in a clone.

        :rtype: dict
        """
        res = {'url': None, 'tag': None, 'commit': None}
        oldcwd = os.getcwd()
        logger.debug("Current directory: %s", oldcwd)
        logger.debug("This file: %s (%s)", __file__, os.path.abspath(__file__))
        newdir = os.path.dirname(os.path.abspath(__file__))
        logger.debug("cd to %s", newdir)
        os.chdir(newdir)
        res['commit'] = self._get_git_commit()
        if res['commit'] is not None:
            res['tag'] = self._get_git_tag(res['commit'])
            res['url'] = self._get_git_url()
        logger.debug("cd back to %s", oldcwd)
        os.chdir(oldcwd)
        return res

    def _get_git_commit(self):
        """
        Get the current git commit of the source directory.

        :return: string short git hash
        """
        try:
            commit = subprocess.check_output([
                'git',
                'rev-parse',
                '--short',
                'HEAD'
            ], stderr=DEVNULL).strip()
            logger.debug("Found source git commit: %s", commit)
        except Exception:
            logger.debug("Unable to run git to get commit")
            commit = None
        return commit

    def _get_git_tag(self, commit):
        """get the git tag for the specified commit, or None"""
        try:
            tag = subprocess.check_output([
                'git',
                'describe',
                '--exact-match',
                '--tags',
                commit
            ]).strip()
        except subprocess.CalledProcessError:
            tag = None
        return tag

    def _get_git_url(self):
        try:
            url = None
            lines = subprocess.check_output([
                'git',
                'remote',
                '-v'
            ]).strip().split("\n")
            urls = {}
            for line in lines:
                parts = re.split(r'\s+', line)
                if parts[2] != '(fetch)':
                    continue
                urls[parts[0]] = parts[1]
            if 'origin' in urls:
                return urls['origin']
            for k, v in urls.items():
                return v
        except subprocess.CalledProcessError:
            url = None
        return url

    def _is_git_dirty(self):
        status = subprocess.check_output([
            'git',
            'status',
            '-uno'
        ]).strip()
        if ('Your branch is up-to-date with' not in status or
                'HEAD detached at' not in status or
                'nothing to commit' not in status):
            return True
        return False
