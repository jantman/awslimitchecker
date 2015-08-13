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
import sys
import locale

if sys.version_info >= (3, 3):
    from subprocess import DEVNULL
else:
    DEVNULL = open(os.devnull, 'wb')

try:
    import pip
except ImportError:
    # this is used within try blocks; NBD if they fail
    pass

try:
    import pkg_resources
except ImportError:
    # this is used within try blocks; NBD if they fail
    pass

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
        if os.environ.get('VERSIONCHECK_DEBUG', '') != 'true':
            # silence logging
            logger.setLevel(logging.WARNING)
            # silence pip logging
            pip_log = logging.getLogger("pip")
            pip_log.setLevel(logging.WARNING)
            pip_log.propagate = True

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
        if git_info['dirty'] and res['tag'] is not None:
            res['tag'] += '*'
        if git_info['dirty'] and res['commit'] is not None:
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

        :returns: information from pkg_resources about 'awslimitchecker'
        :rtype: dict
        """
        dist = pkg_resources.require('awslimitchecker')[0]
        ver, url = self._dist_version_url(dist)
        return {'version': ver, 'url': url}

    def _find_pip_info(self):
        """
        Try to find information about the installed awslimitchecker from pip.
        This should be wrapped in a try/except.

        :returns: information from pip about 'awslimitchecker'
        :rtype: dict
        """
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
        """
        Get version and homepage for a pkg_resources.Distribution

        :param dist: the pkg_resources.Distribution to get information for
        :returns: 2-tuple of (version, homepage URL)
        :rtype: tuple
        """
        ver = str(dist.version)
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

        :returns: information about the git clone
        :rtype: dict
        """
        res = {'url': None, 'tag': None, 'commit': None, 'dirty': None}
        oldcwd = os.getcwd()
        logger.debug("Current directory: %s", oldcwd)
        logger.debug("This file: %s (%s)", __file__, os.path.abspath(__file__))
        newdir = os.path.dirname(os.path.abspath(__file__))
        logger.debug("cd to %s", newdir)
        os.chdir(newdir)
        res['commit'] = _get_git_commit()
        if res['commit'] is not None:
            res['tag'] = _get_git_tag(res['commit'])
            res['url'] = _get_git_url()
        try:
            res['dirty'] = self._is_git_dirty()
        except Exception:
            pass
        logger.debug("cd back to %s", oldcwd)
        os.chdir(oldcwd)
        return res

    def _is_git_dirty(self):
        """
        Determine if the git clone has uncommitted changes or is behind origin

        :returns: True if clone is dirty, False otherwise
        :rtype: bool
        """
        status = _check_output([
            'git',
            'status',
            '-u'
        ], stderr=DEVNULL).strip()
        if (('Your branch is up-to-date with' not in status and
                'HEAD detached at' not in status) or
                'nothing to commit' not in status):
            logger.debug("Git repository dirty based on status: %s", status)
            return True
        return False


def _check_output(args, stderr=None):
    """
    Python version compatibility wrapper for subprocess.check_output

    :param stderr: what to do with STDERR - None or an appropriate argument
     to subprocess.check_output / subprocess.Popen
    :raises: subprocess.CalledProcessError
    :returns: command output
    :rtype: string
    """
    if sys.version_info < (2, 7):
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=stderr)
        (res, err) = p.communicate()
        if p.returncode != 0:
            raise subprocess.CalledProcessError(p.returncode, args)
    else:
        res = subprocess.check_output(args, stderr=stderr)
        if sys.version_info >= (3, 0):
            res = res.decode(locale.getdefaultlocale()[1])
    return res


def _get_git_commit():
    """
    Get the current (short) git commit hash of the current directory.

    :returns: short git hash
    :rtype: string
    """
    try:
        commit = _check_output([
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


def _get_git_tag(commit):
    """
    Get the git tag for the specified commit, or None

    :param commit: git commit hash to get the tag for
    :type commit: string
    :returns: tag name pointing to commit
    :rtype: string
    """
    if commit is None:
        return None
    try:
        tag = _check_output([
            'git',
            'describe',
            '--exact-match',
            '--tags',
            commit
        ], stderr=DEVNULL).strip()
    except subprocess.CalledProcessError:
        tag = None
    if tag == '':
        return None
    return tag


def _get_git_url():
    """
    Get the origin URL for the git repository.

    :returns: repository origin URL
    :rtype: string
    """
    try:
        url = None
        lines = _check_output([
            'git',
            'remote',
            '-v'
        ], stderr=DEVNULL).strip().split("\n")
        urls = {}
        for line in lines:
            parts = re.split(r'\s+', line)
            if parts[2] != '(fetch)':
                continue
            urls[parts[0]] = parts[1]
        if 'origin' in urls:
            return urls['origin']
        for k, v in sorted(urls.items()):
            return v
    except subprocess.CalledProcessError:
        url = None
    except IndexError:
        url = None
    return url
