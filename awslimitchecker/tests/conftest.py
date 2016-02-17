"""
awslimitchecker/tests/conftest.py

This alters the pytest output to suppress some strings that come in as
environment variables.

This code is inspired by / based on the
`pytest-wholenodeid <https://github.com/willkg/pytest-wholenodeid>`_ plugin by
`Will Kahn-Greene <https://github.com/willkg>`_, distributed under a
Simplified BSD License.

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

import sys
import os
import re

from _pytest.terminal import TerminalReporter
import pytest


class OutputSanitizer(object):

    def __init__(self, tw):
        self.mfa_re = re.compile(r"'mfa_token':\s*b?'\d+'")
        self.tc_re = re.compile(r"'TokenCode':\s*b?'\d+'")
        self._tw = tw
        self.replace = []
        for keyname in [
            'AWS_MAIN_ACCESS_KEY_ID',
            'AWS_MAIN_SECRET_ACCESS_KEY',
            'AWS_MASTER_ACCOUNT_ID',
            'AWS_EXTERNAL_ID',
            'AWS_INTEGRATION_ACCESS_KEY_ID',
            'AWS_INTEGRATION_SECRET_KEY',
            'AWS_MFA_INTEGRATION_ACCESS_KEY_ID',
            'AWS_MFA_INTEGRATION_SECRET_KEY',
            'AWS_MFA_SERIAL',
            'AWS_MFA_SECRET',
            'AWS_MFA_EXTERNAL_ID',
            'AWS_MFA3_INTEGRATION_ACCESS_KEY_ID',
            'AWS_MFA3_INTEGRATION_SECRET_KEY',
            'AWS_MFA3_SERIAL',
            'AWS_MFA3_SECRET'
        ]:
            if keyname in os.environ:
                self.replace.append((
                    os.environ[keyname],
                    "<<os.environ[%s]>>" % keyname
                ))

    def line(self, s='', **kw):
        line = self.sanitize_line(s)
        self._tw.line(line, **kw)

    def sanitize_line(self, line):
        for repl_set in self.replace:
            line = line.replace(repl_set[0], repl_set[1])
        line = self.mfa_re.sub("'mfa_token': 'XXXXXX", line)
        line = self.tc_re.sub("'TokenCode': 'XXXXXX", line)
        return line

    def sep(self, *args, **kwargs):
        self._tw.sep(*args, **kwargs)

    @property
    def fullwidth(self):
        return self._tw.fullwidth


class WholeNodeIDTerminalReporter(TerminalReporter):

    def _outrep_summary(self, rep):
        sanitizer = OutputSanitizer(self._tw)
        rep.toterminal(sanitizer)
        for secname, content in rep.sections:
            self._tw.sep("-", secname)
            if content[-1:] == "\n":
                content = content[:-1]
            sanitizer.line(content)


@pytest.mark.trylast
def pytest_configure(config):
    # Get the standard terminal reporter plugin and replace it with our
    standard_reporter = config.pluginmanager.getplugin('terminalreporter')
    wholenodeid_reporter = WholeNodeIDTerminalReporter(config, sys.stdout)
    config.pluginmanager.unregister(standard_reporter)
    config.pluginmanager.register(wholenodeid_reporter, 'terminalreporter')
