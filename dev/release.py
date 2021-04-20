#!/usr/bin/env python
"""
Development script to convert current version release notes to markdown and
either upload to Github as a gist, or create a Github release for the version.

The latest version of this package is available at:
<http://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2016 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

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
import sys
import logging
import json
import subprocess
import re
from shutil import rmtree
from time import sleep
from copy import deepcopy
from datetime import datetime
from github_releaser import GithubReleaser
from release_utils import (
    StepRegistry, prompt_user, BaseStep, fail, is_git_dirty, TravisChecker
)
from awslimitchecker.version import _VERSION as VERSION
from update_integration_iam_policy import IntegrationIamPolicyUpdater

if sys.version_info[0:2] < (3, 6):
    raise SystemExit('ERROR: release.py can only run under py 3.6+')

FORMAT = "[%(levelname)s %(filename)s:%(lineno)s - %(name)s.%(funcName)s() ] " \
         "%(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
logger = logging.getLogger()

for n in ['urllib3', 'urllib', 'requests', 'git', 'github3']:
    l = logging.getLogger(n)
    l.setLevel(logging.ERROR)
    l.propagate = True


steps = StepRegistry()


@steps.register(1)
class InitialChecks(BaseStep):

    def run(self):
        b = self._current_branch
        if b == 'master':
            fail('release.py cannot be run from master for a new release')
        rbranch = 'issues/%d' % self._release_issue_num
        if b != rbranch:
            fail(
                'You must run this script from a release branch called '
                '"%s"' % rbranch
            )
        if not prompt_user(
            'Have you confirmed that there are CHANGES.rst entries for all '
            'major changes?'
        ):
            fail('Please check CHANGES.rst before releasing code.')
        if not prompt_user(
            'Is the current version (%s) the version being released?' % VERSION
        ):
            fail(
                'Please increment the version in awslimitchecker/version.py '
                'before running the release script.'
            )
        # check for proper CHANGES.rst heading
        have_ver = False
        last_line = ''
        expected = '%s (%s)' % (VERSION, datetime.now().strftime('%Y-%m-%d'))
        with open(os.path.join(self.projdir, 'CHANGES.rst'), 'r') as fh:
            for line in fh.readlines():
                line = line.strip()
                if (
                    line == '-' * len(expected) and
                    last_line == expected
                ):
                    have_ver = True
                    break
                last_line = line
        if not have_ver:
            fail('Expected to find a "%s" heading in CHANGES.rst, but did not. '
                 'Please ensure there is a changelog heading for this release.'
                 '' % expected)
        if not prompt_user(
            'Is the test coverage at least as high as the last release, and '
            'are there acceptance tests for all non-trivial changes?'
        ):
            fail('Test coverage!!!')


@steps.register(2)
class RunToxLocaldocs(BaseStep):

    def run(self):
        self._run_tox_env('localdocs')
        self._ensure_committed()


@steps.register(3)
class RunDevUpdateIntegrationIamPolicy(BaseStep):

    def run(self):
        logger.info('Running dev/update_integration_iam_policy.py')
        IntegrationIamPolicyUpdater().run()
        self._ensure_committed()
        if not prompt_user(
                'Are any IAM permission changes clearly documented in the '
                'changelog?'
        ):
            fail('Please update CHANGES.rst with any new IAM permissions.')


@steps.register(4)
class ConfirmTravisAndCoverage(BaseStep):

    always_run = True

    def run(self):
        commit = self._current_commit
        logger.info('Polling for finished TravisCI build of %s', commit)
        build = self._travis.commit_latest_build_status(commit)
        while build is None or build.finished is False:
            sleep(10)
            build = self._travis.commit_latest_build_status(commit)
        logger.info('Travis build finished')
        if not build.passed:
            fail('Travis build %s (%s) did not pass. Please fix build failures '
                 'and then re-run.' % (build.number, build.id))
        logger.info('OK, Travis build passed.')
        logger.info(
            'Build URL: <https://travis-ci.com/jantman/awslimitchecker/'
            'builds/%s>', build.id
        )
        if not prompt_user(
            'Is the test coverage at least as high as the last release, and '
            'are there acceptance tests for all non-trivial changes?'
        ):
            fail('Test coverage!!!')


@steps.register(5)
class RegenerateDocs(BaseStep):

    def run(self):
        self._run_tox_env('docs')
        self._ensure_committed()


@steps.register(6)
class EnsurePushed(BaseStep):

    always_run = True

    def run(self):
        self._ensure_pushed()


@steps.register(7)
class GistReleaseNotes(BaseStep):

    def run(self):
        result = None
        while result is not True:
            md = self._gh._get_markdown()
            print("Changelog Markdown:\n%s\n" % md)
            result = prompt_user('Does this markdown look right?')
            if result is not True:
                input('Revise Changelog and then press any key.')
                continue
            url = self._gh._gist(md)
            logger.info('Gist URL: <%s>', url)
            result = prompt_user('Does the gist at <%s> look right?' % url)
        self._ensure_pushed()


@steps.register(8)
class ConfirmReadmeRenders(BaseStep):

    def run(self):
        logger.info(
            'Readme URL: <https://github.com/jantman/awslimitchecker/blob/%s/'
            'README.rst>', self._current_branch
        )
        if not prompt_user('Does the Readme at the above URL render properly?'):
            fail('Please fix the README and then re-run.')


@steps.register(9)
class TestPyPI(BaseStep):

    def run(self):
        projdir = self.projdir
        logger.info('Removing dist directory...')
        rmtree(os.path.join(projdir, 'dist'))
        env = deepcopy(os.environ)
        env['PATH'] = self._fixed_path(projdir)
        cmd = ['python', 'setup.py', 'sdist', 'bdist_wheel']
        logger.info(
            'Running: %s (cwd=%s)', ' '.join(cmd), projdir
        )
        res = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=projdir, timeout=1800, env=env
        )
        if res.returncode != 0:
            logger.error(
                'ERROR: command exited %d:\n%s',
                res.returncode, res.stdout.decode()
            )
            fail('%s failed.' % ' '.join(cmd))
        cmd = ' '.join(['twine', 'upload', '-r', 'test', 'dist/*'])
        logger.info(
            'Running: %s (cwd=%s)', cmd, projdir
        )
        res = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=projdir, timeout=1800, env=env, shell=True
        )
        if res.returncode != 0:
            logger.error(
                'ERROR: command exited %d:\n%s',
                res.returncode, res.stdout.decode()
            )
            fail('%s failed.' % ' '.join(cmd))
        logger.info('Package generated and uploaded to Test PyPI.')
        res = self.pypi_has_version(VERSION, test=True)
        while not res:
            logger.info('Waiting for new version to show up on TestPyPI...')
            sleep(10)
            res = self.pypi_has_version(VERSION, test=True)
        logger.info(
            'Package is live on Test PyPI. URL: <https://testpypi.python.org/'
            'pypi/awslimitchecker>'
        )
        if not prompt_user('Does the Readme at the above URL render properly?'):
            fail('Please fix the README and then re-run.')


@steps.register(10)
class PullRequest(BaseStep):

    def run(self):
        pr_num = self.has_pr()
        if pr_num is None:
            pr_num = self.create_pr()
        self.wait_for_travis(pr_num)
        self.wait_for_merge(pr_num)

    def has_pr(self):
        repo = self._gh._repo
        branch = self._current_branch
        logger.debug('Looking for existing PR for %s into master', branch)
        for pr in repo.pull_requests(
            state='open', head='jantman:%s' % branch, base='master'
        ):
            if str(pr.head.user) != 'jantman':
                continue
            if pr.head.ref == branch:
                logger.debug('Found PR for %s: PR #%s', branch, pr.number)
                return pr.number
        logger.debug('No existing PR for branch')
        return None

    def create_pr(self):
        branch = self._current_branch
        logger.debug('Creating PR for %s into master', branch)
        pull = self._gh._repo.create_pull(
            'fixes #%s - %s release' % (self._release_issue_num, VERSION),
            'master',
            'jantman:%s' % branch,
            body='%s release' % VERSION
        )
        if pull is None:
            fail('ERROR: Could not create PR for release')
        logger.info('Opened PR for %s into master; PR #%s', branch, pull.number)
        return pull.number

    def wait_for_travis(self, pr_num):
        logger.info('Waiting for Travis PR build to complete...')
        pr = self._gh._repo.pull_request(pr_num)
        headsha = pr.head.sha
        while True:
            for s in self._gh._repo.commit(headsha).check_runs():
                if s.name == 'Travis CI - Pull Request':
                    logger.info(
                        'Last TravisCI PR status: %s <%s> (at %s)',
                        s.conclusion, s.html_url, s.completed_at
                    )
                    if s.conclusion == 'success':
                        return True
            logger.debug('No successful TravisCI PR build; trying again in 15s')
            sleep(15)

    def wait_for_merge(self, pr_num):
        pull = self._gh._repo.pull_request(pr_num)
        logger.info('Polling state of PR #%s (<%s>)', pr_num, pull.html_url)
        while not pull.is_merged():
            logger.info(
                'PR state is: %s; checking for merge again in 15s', pull.state
            )
            sleep(15)
            pull = pull.refresh()
        logger.info('OK; PR %s is merged to master', pr_num)


@steps.register(11)
class WaitForTag(BaseStep):

    def run(self):
        input(
            "Please run: git tag -s -a %s -m '%s released %s' && git tag -v "
            "%s && git push origin %s\nand then press any key." % (
                VERSION, VERSION, datetime.now().strftime('%Y-%m-%d'),
                VERSION, VERSION
            )
        )
        self._wait_for_tag(VERSION)

    def _wait_for_tag(self, tagname):
        logger.info('Waiting for tag to show up on GitHub...')
        while True:
            for t in self._gh._repo.tags():
                if t.name == tagname:
                    logger.info('GitHub has %s tag.', tagname)
                    return


@steps.register(12)
class UploadToPyPI(BaseStep):

    def run(self):
        projdir = self.projdir
        if not prompt_user('Ready to upload to PyPI?'):
            fail('Not ready to upload to PyPI.')
        env = deepcopy(os.environ)
        env['PATH'] = self._fixed_path(projdir)
        cmd = ' '.join(['twine', 'upload', 'dist/*'])
        logger.info(
            'Running: %s (cwd=%s)', cmd, projdir
        )
        res = subprocess.run(
            cmd, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=projdir, timeout=1800, env=env, shell=True
        )
        if res.returncode != 0:
            logger.error(
                'ERROR: command exited %d:\n%s',
                res.returncode, res.stdout.decode()
            )
            fail('%s failed.' % cmd)
        logger.info(
            'Package generated and uploaded to live/production PyPI.')
        res = self.pypi_has_version(VERSION)
        while not res:
            logger.info(
                'Waiting for new version to show up on PyPI...')
            sleep(10)
            res = self.pypi_has_version(VERSION)
        logger.info('Package is live on PyPI.')


@steps.register(13)
class DoGitHubRelease(BaseStep):

    def run(self):
        md = self._gh._get_markdown()
        print("Markdown:\n%s\n" % md)
        if not prompt_user('Does this look right?'):
            fail('Changelog apparently does not look right.')
        self._gh._release(md)


@steps.register(14)
class FinalChecks(BaseStep):

    def run(self):
        prompt_user(
            'Please ensure that all GitHub issues included in this release '
            'have been closed.'
        )
        prompt_user(
            'Please log in to readthedocs.org and ensure the %s tag has '
            'been built.' % VERSION
        )
        prompt_user(
            'Please be sure to merge master back into develop and push.'
        )
        prompt_user(
            'Please archive all finished issues on '
            '<https://waffle.io/jantman/awslimitchecker>'
        )
        prompt_user('Remember to blog/tweet/etc. about the new version.')


class AlcReleaseAutomator(object):

    def __init__(self, savepath):
        self._savepath = savepath
        logger.info('Release step/position save path: %s', savepath)
        self.gh = GithubReleaser()
        self.travis = TravisChecker()
        self.release_issue_num = None

    def run(self):
        if self.gh.get_tag(VERSION) != (None, None):
            logger.error(
                'Version %s is already released on GitHub. Either you need to '
                'increment the version number in awslimitchecker/version.py or '
                'the release is complete.', VERSION
            )
            raise SystemExit(1)
        self.release_issue_num = self._release_issue_number
        if self.release_issue_num is None:
            self.release_issue_num = self._open_release_issue()
            self._record_successful_step(0)
        is_git_dirty(raise_on_dirty=True)
        last_step = self._last_step
        for stepnum in steps.step_numbers:
            cls = steps.step(stepnum)
            if stepnum <= last_step and not cls.always_run:
                logger.debug('Skipping step %d - already completed', stepnum)
                continue
            logger.info('Running step %d (%s)', stepnum, cls.__name__)
            cls(self.gh, self.travis, self.release_issue_num).run()
            if stepnum >= last_step:
                self._record_successful_step(stepnum)
        logger.info('DONE!')
        logger.debug('Removing: %s', self._savepath)
        os.unlink(self._savepath)

    @property
    def _last_step(self):
        """
        If ``self._savepath`` doesn't exist, can't be read as JSON, or doesn't
        match ``VERSION``, return 0. Otherwise, return the step which that file
        lists as the last-run step for this release.

        :return: last-run step from the release or 0
        :rtype: int
        """
        if not os.path.exists(self._savepath):
            return 0
        try:
            with open(self._savepath, 'r') as fh:
                j = json.loads(fh.read())
        except Exception:
            logger.warning(
                'Could not read or JSON-deserialize %s', self._savepath
            )
            return 0
        if j.get('version', '') != VERSION:
            return 0
        return j.get('last_successful_step', 0)

    @property
    def _release_issue_number(self):
        if not os.path.exists(self._savepath):
            return None
        try:
            with open(self._savepath, 'r') as fh:
                j = json.loads(fh.read())
        except Exception:
            logger.warning(
                'Could not read or JSON-deserialize %s', self._savepath
            )
            return None
        if j.get('version', '') != VERSION:
            return None
        return j.get('release_issue_num', None)

    def _record_successful_step(self, stepnum):
        with open(self._savepath, 'w') as fh:
            fh.write(json.dumps({
                'version': VERSION,
                'last_successful_step': stepnum,
                'release_issue_num': self.release_issue_num
            }))
        logger.debug('Updated last_successful_step to %d', stepnum)

    def _open_release_issue(self):
        logger.info('Opening new issue for %s release', VERSION)
        issue = self.gh._repo.create_issue(
            '%s release' % VERSION,
            body='Issue for %s release' % VERSION
        )
        logger.info('Opened issue %d (%s)', issue.number, issue.id)
        return issue.number


if __name__ == "__main__":
    AlcReleaseAutomator(
        os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..',
                '.release_position.json'
            )
        )
    ).run()
