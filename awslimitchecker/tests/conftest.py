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
from awslimitchecker.services import _services
from awslimitchecker.tests.test_integration import REGION


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

    def write(self, s, **kw):
        line = self.sanitize_line(s)
        self._tw.write(line, **kw)

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


def pytest_generate_tests(metafunc):
    if (
        metafunc.cls.__name__ == 'Test_AwsServiceSubclasses' and
        metafunc.function.__name__ == 'test_subclass_init'
    ):
        param_for_service_base_subclass_init(metafunc)
    if (
        metafunc.cls.__name__ == 'TestIntegration' and
        metafunc.function.__name__ == 'test_verify_limits'
    ):
        param_for_integration_test_verify_limits(metafunc)
    if (
        metafunc.cls.__name__ == 'TestIntegration' and
        metafunc.function.__name__ == 'test_verify_usage'
    ):
        param_for_integration_test_verify_usage(metafunc)


def param_for_service_base_subclass_init(metafunc):
    classnames = []
    classes = []
    for clsname in sorted(_services.keys()):
        classnames.append(clsname)
        classes.append([_services[clsname]])
    metafunc.parametrize(
        ['cls'],
        classes,
        ids=classnames
    )


def param_for_integration_test_verify_usage(metafunc):
    argnames = [
        'checker_args',
        'creds_type',
        'service_name',
        'expect_usage',
        'allow_endpoint_error'
    ]
    argvals = [
        [
            {'region': REGION},
            'normal',
            None,
            True,
            False
        ],
        [
            {'region': 'sa-east-1'},
            'normal',
            None,
            False,
            True
        ],
        [
            {
                'account_id': os.environ.get('AWS_MASTER_ACCOUNT_ID', None),
                'account_role': 'alc-integration-sts',
                'region': REGION,
            },
            'sts',
            ['VPC'],
            True,
            False
        ],
        [
            {
                'account_id': os.environ.get('AWS_MASTER_ACCOUNT_ID', None),
                'account_role': 'alc-integration-sts',
                'region': REGION,
                'external_id': os.environ.get('AWS_EXTERNAL_ID', None),
            },
            'sts',
            ['VPC'],
            True,
            False
        ],
        [
            {
                'account_id': os.environ.get('AWS_MASTER_ACCOUNT_ID', None),
                'account_role': 'alc-integration-sts-mfa',
                'region': REGION,
                'mfa_token': 'foo'  # will be replaced in the method
            },
            'sts_mfa',
            ['VPC'],
            True,
            False
        ],
        [
            {
                'account_id': os.environ.get('AWS_MASTER_ACCOUNT_ID', None),
                'account_role': 'alc-integration-sts-mfa-extid',
                'region': REGION,
                'external_id': os.environ.get('AWS_MFA_EXTERNAL_ID', None),
                'mfa_token': 'foo'  # will be replaced in the method
            },
            'sts_mfa',
            ['VPC'],
            True,
            False
        ]
    ]
    testnames = [
        'default_creds_all_services',
        'other_region_all_services',
        'sts',
        'sts_external_id',
        'sts_mfa',
        'sts_mfa_external_id'
    ]
    for sname in _services:
        eu = False
        if sname in ['VPC', 'EC2', 'ElastiCache', 'EBS', 'IAM']:
            eu = True
        argvals.append([
            {'region': REGION},
            'normal',
            [sname],
            eu,
            False
        ])
        testnames.append('default_creds_each_service-%s' % sname)
    metafunc.parametrize(
        argnames,
        argvals,
        ids=testnames
    )


def param_for_integration_test_verify_limits(metafunc):
    argnames = [
        'checker_args',
        'creds_type',
        'service_name',
        'use_ta',
        'expect_api_source',
        'allow_endpoint_error'
    ]
    argvals = [
        [
            {'region': REGION},
            'normal',
            None,
            True,
            True,
            False
        ],
        [
            {'region': 'sa-east-1'},
            'normal',
            None,
            True,
            True,
            True
        ],
        [
            {
                'account_id': os.environ.get('AWS_MASTER_ACCOUNT_ID', None),
                'account_role': 'alc-integration-sts',
                'region': REGION,
            },
            'sts',
            ['VPC'],
            True,
            False,
            False
        ],
        [
            {
                'account_id': os.environ.get('AWS_MASTER_ACCOUNT_ID', None),
                'account_role': 'alc-integration-sts',
                'region': REGION,
                'external_id': os.environ.get('AWS_EXTERNAL_ID', None),
            },
            'sts',
            ['VPC'],
            True,
            False,
            False
        ],
        [
            {
                'account_id': os.environ.get('AWS_MASTER_ACCOUNT_ID', None),
                'account_role': 'alc-integration-sts-mfa',
                'region': REGION,
                'mfa_token': 'foo'  # will be replaced in the method
            },
            'sts_mfa',
            ['VPC'],
            True,
            False,
            False
        ],
        [
            {
                'account_id': os.environ.get('AWS_MASTER_ACCOUNT_ID', None),
                'account_role': 'alc-integration-sts-mfa-extid',
                'region': REGION,
                'external_id': os.environ.get('AWS_MFA_EXTERNAL_ID', None),
                'mfa_token': 'foo'  # will be replaced in the method
            },
            'sts_mfa',
            ['VPC'],
            True,
            False,
            False
        ]
    ]
    testnames = [
        'default_creds_all_services',
        'other_region_all_services',
        'sts',
        'sts_external_id',
        'sts_mfa',
        'sts_mfa_external_id'
    ]
    for sname in _services:
        argvals.append([
            {'region': REGION},
            'normal',
            [sname],
            True,
            False,
            False
        ])
        testnames.append('default_creds_each_service-%s' % sname)
    metafunc.parametrize(
        argnames,
        argvals,
        ids=testnames
    )
