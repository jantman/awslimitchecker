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
import logging
import subprocess
from copy import deepcopy
import requests

try:
    from travispy import TravisPy
    from travispy.travispy import PUBLIC
except ImportError:
    raise SystemExit(
        "ERROR: TravisPy not installed. Please run 'pip install TravisPy'"
    )

logger = logging.getLogger(__name__)


def prompt_user(s):
    res = None
    while res not in ['y', 'Y', 'n', 'N']:
        try:
            res = input(s + '[y|n] ')
        except EOFError:
            res = ''
    if res.strip() in ['y', 'Y']:
        return True
    return False


def fail(s):
    logger.critical(s)
    raise SystemExit(1)


def is_git_dirty(raise_on_dirty=False):
    dirty = False
    if subprocess.call(
            ['git', 'diff', '--no-ext-diff', '--quiet', '--exit-code']
    ) != 0:
        dirty = True
    if subprocess.call(
            ['git', 'diff-index', '--cached', '--quiet', 'HEAD', '--']
    ) != 0:
        dirty = True
    if dirty and raise_on_dirty:
        raise RuntimeError(
            'ERROR: Git clone is dirty. Commit before continuing.'
        )
    return dirty


class TravisChecker(object):

    def __init__(self):
        token = os.environ.get('GITHUB_TOKEN', None)
        if token is None:
            raise SystemExit(
                'Please export your GitHub PAT as the "GITHUB_TOKEN" env var'
            )
        logger.debug('Connecting to TravisCI API...')
        self._travis = TravisPy.github_auth(token)

    def commit_latest_build_status(self, commit):
        """
        Find the latest build for the given commit and return it,
        or None if no build for the commit yet.
        """
        build = self._latest_travis_build(commit)
        if build is None:
            return None
        logger.info(
            'Found latest build for commit %s: %s (%s)',
            commit, build.number, build.id
        )
        return build

    def _find_travis_job(self, build, toxenv):
        """Given a build object, find the acceptance36 job"""
        for jobid in build.job_ids:
            j = self._travis.job(jobid)
            if 'TOXENV=%s' % toxenv in j.config['env']:
                logger.debug('Found %s job: %s', toxenv, j.number)
                return j
        raise SystemExit(
            'ERROR: could not find %s job for build %s (%s)' % (
                toxenv, build.number, build.id
            )
        )

    def _latest_travis_build(self, commit):
        logger.debug('Finding latest finished build...')
        r = self._travis.repo('jantman/awslimitchecker')
        for bnum in range(int(r.last_build_number), 0, -1):
            b = self._travis.builds(
                slug='jantman/awslimitchecker', number=bnum
            )[0]
            if b.commit.sha == commit:
                return b
        return None


class StepRegistry(object):

    def __init__(self):
        self._steps = {}

    def register(self, step_num, klass=None):
        if klass:
            raise RuntimeError(
                'StepRegistry.register can only be used to decorate classes, '
                'not functions.'
            )

        def _register_class(klass):
            if not isinstance(step_num, type(1)):
                raise RuntimeError(
                    'ERROR on register decorator of class %s: step number '
                    '"%s" is not an integer.' % (klass.__name__, step_num)
                )
            if step_num in self._steps:
                raise RuntimeError(
                    'ERROR: Duplicate step number %d on classes %s and %s' % (
                        step_num, self._steps[step_num].__name__, klass.__name__
                    )
                )
            self._steps[step_num] = klass
            return klass

        return _register_class

    @property
    def step_numbers(self):
        return sorted(self._steps.keys())

    def step(self, stepnum):
        return self._steps[stepnum]


class BaseStep(object):

    always_run = False

    def __init__(self, github_releaser, travis_checker, issue_num):
        self._gh = github_releaser
        self._travis = travis_checker
        self._release_issue_num = issue_num

    def run(self):
        raise NotImplementedError('BaseStep run() not overridden')

    @property
    def _current_branch(self):
        res = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stdout=subprocess.PIPE
        )
        return res.stdout.decode().strip()

    @property
    def _current_commit(self):
        res = subprocess.run(
            ['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE
        )
        return res.stdout.decode().strip()

    def _ensure_committed(self):
        while is_git_dirty():
            input(
                'Git repository has uncommitted changes; please commit '
                'changes and press any key.'
            )

    def _ensure_pushed(self):
        pushed = None
        while pushed is not True:
            logger.debug('Running git fetch')
            subprocess.run(['git', 'fetch'], check=True)
            local_ref = self._current_commit
            rmt_ref = subprocess.run(
                ['git', 'rev-parse', 'origin/%s' % self._current_branch],
                stdout=subprocess.PIPE, check=True
            ).stdout.decode().strip()
            pushed = local_ref == rmt_ref
            if not pushed:
                input(
                    'This branch must be pushed to origin. Git push and then '
                    'press any key.'
                )

    @property
    def projdir(self):
        return os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..'
            )
        )

    def _run_tox_env(self, env_name, extra_env_vars={}):
        """
        Run the specified tox environment.

        :param env_name: name of the tox environment to run
        :type env_name: str
        :param extra_env_vars: additional variables to set in the environment
        :type extra_env_vars: dict
        :raises: RuntimeError
        :returns: combined STDOUT / STDERR
        :rtype: str
        """
        projdir = self.projdir
        env = deepcopy(os.environ)
        env['PATH'] = self._fixed_path(projdir)
        env.update(extra_env_vars)
        cmd = [os.path.join(projdir, 'bin', 'tox'), '-e', env_name]
        logger.info(
            'Running tox environment %s: args="%s" cwd=%s '
            'timeout=1800', env_name, ' '.join(cmd), projdir
        )
        res = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=projdir, timeout=1800, env=env
        )
        logger.info('tox process exited %d', res.returncode)
        if res.returncode != 0:
            logger.error(
                'ERROR: tox environment %s exitcode %d',
                env_name, res.returncode
            )
            logger.error(
                'tox output:\n%s', res.stdout.decode()
            )
            res.check_returncode()
        return res.stdout.decode()

    def _fixed_path(self, projdir):
        """
        Return the current PATH, fixed to remove the docker tox env.

        :return: sanitized path
        :rtype: str
        """
        res = []
        toxdir = os.path.join(projdir, '.tox')
        for p in os.environ['PATH'].split(':'):
            if not p.startswith(toxdir):
                res.append(p)
        return ':'.join(res)

    def pypi_has_version(self, ver, test=False):
        host = 'pypi'
        if test:
            host = 'testpypi'
        url = 'https://%s.python.org/pypi/awslimitchecker/json' % host
        try:
            r = requests.get(url)
            if r.json()['info']['version'] == ver:
                return True
            return False
        except Exception:
            logger.warning('Exception getting JSON from %s',
                           url, exc_info=True)
        return False
