#!/usr/bin/env python
"""
Development script to convert current version release notes to markdown and
either upload to Github as a gist, or create a Github release for the version.

awslimitchecker/dev/release.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
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
################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/pydnstest> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

import os
import sys
import logging
import subprocess
import re
from datetime import datetime
from awslimitchecker.version import _VERSION
from distutils.spawn import find_executable
from github3 import login

FORMAT = "[%(levelname)s %(filename)s:%(lineno)s - %(name)s.%(funcName)s() ] " \
         "%(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
logger = logging.getLogger()

for n in ['urllib3', 'urllib', 'requests', 'git', 'github3']:
    l = logging.getLogger(n)
    l.setLevel(logging.ERROR)
    l.propagate = True


class GithubReleaser(object):

    head_re = re.compile(r'^## (\d+\.\d+\.\d+).*')

    def __init__(self):
        self._pandoc = find_executable('pandoc')
        if self._pandoc is None:
            sys.stderr.write("ERROR: pandoc not found on PATH.\n")
            raise SystemExit(1)
        self._gh_token = os.environ.get('GITHUB_TOKEN', None)
        if self._gh_token is None:
            sys.stderr.write("ERROR: GITHUB_TOKEN env var must be set\n")
            raise SystemExit(1)
        self._gh = login(token=self._gh_token)
        self._repo = self._gh.repository('jantman', 'awslimitchecker')

    def run(self, action):
        logger.info('Github Releaser running action: %s', action)
        logger.info('Current awslimitchecker version: %s', _VERSION)
        md = self._get_markdown()
        print("Markdown:\n%s\n" % md)
        try:
            raw_input(
                'Does this look right? <Enter> to continue or Ctrl+C otherwise'
            )
        except Exception:
            input(
                'Does this look right? <Enter> to continue or Ctrl+C otherwise'
            )
        if action == 'release':
            self._release(md)
        else:
            self._gist(md)

    def _release(self, markdown):
        _VERSION = 'foobar'
        for rel in self._repo.releases():
            if rel.tag_name == _VERSION:
                logger.error('Error: Release already present for %s: "%s" (%s)',
                             _VERSION, rel.name, rel.html_url)
                raise SystemExit(1)
        name = '%s released %s' % (
            _VERSION, datetime.now().strftime('%Y-%m-%d')
        )
        logger.info('Creating release: %s', name)
        r = self._repo.create_release(
            _VERSION,
            name=name,
            body=markdown,
            draft=False,
            prerelease=False
        )
        logger.info('Created release: %s', r.html_url)

    def _gist(self, markdown):
        logger.info('Creating private gist...')
        g = self._gh.create_gist(
            'awslimitchecker %s release notes test' % _VERSION,
            {
                'release_notes.md': {'content': markdown}
            },
            public=False
        )
        logger.info('Created gist: %s', g.html_url)

    def _get_markdown(self):
        fpath = os.path.abspath(os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            '..',
            'CHANGES.rst'
        ))
        cmd = [
            self._pandoc,
            '-f', 'rst',
            '-t', 'markdown',
            '--normalize',
            '--wrap=none',
            '--atx-headers',
            fpath
        ]
        logger.debug('Running: %s', cmd)
        markdown = subprocess.check_output(cmd)
        buf = ''
        in_ver = False
        for line in markdown.split("\n"):
            if not in_ver and line.startswith('## %s ' % _VERSION):
                in_ver = True
            elif in_ver and line.startswith('## '):
                return buf
            elif in_ver:
                buf += line + "\n"
        return buf


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("USAGE: release.py <gist|release>\n")
        raise SystemExit(1)

    action = sys.argv[1]
    if action not in ['gist', 'release']:
        sys.stderr.write("USAGE: release.py <gist|release>\n")
        raise SystemExit(1)
    GithubReleaser().run(action)
