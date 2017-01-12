"""
awslimitchecker/tests/test_integration.py

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

import pytest
import os
import logging
import boto3
import time
import sys
from platform import python_implementation
import onetimepass as otp
from awslimitchecker.utils import dict2cols
from awslimitchecker.limit import SOURCE_TA, SOURCE_API
from awslimitchecker.checker import AwsLimitChecker
from awslimitchecker.tests.support import LogRecordHelper

if python_implementation() == 'CPython':
    # this doesn't work under PyPy
    from testfixtures import LogCapture

REGION = 'us-west-2'
MFA_CODE = None

skip_if_pr = pytest.mark.skipif(
    os.environ.get('TRAVIS_PULL_REQUEST', None) != 'false',
    reason='Not running integration tests for pull request'
)


@pytest.mark.integration
@skip_if_pr
class TestIntegration(object):
    """
    !!!!!!IMPORTANT NOTE!!!!!!!

    Using pytest 2.8.7, it appears that module- or class-level markers don't
    get transferred to tests that are run via ``yield``. The only sufficient
    way I've found to get the desired behavior is to apply the
    ``@pytest.mark.integration`` marker to every test-related function directly.
    """

    def setup(self):
        # setup debug-level logging for awslimitchecker
        logger = logging.getLogger("awslimitchecker")
        FORMAT = "[%(levelname)s %(filename)s:%(lineno)s - " \
            "%(name)s.%(funcName)s() ] %(message)s"
        debug_formatter = logging.Formatter(fmt=FORMAT)
        for h in logger.handlers:
            h.setFormatter(debug_formatter)
        logger.setLevel(logging.DEBUG)
        # capture the AWS-related env vars

    @pytest.mark.integration
    @skip_if_pr
    def test_verify_limits(self, checker_args, creds_type, service_name, use_ta,
                           expect_api_source, allow_endpoint_error):
        """
        This essentially replicates what's done when awslimitchecker is called
        from the command line with ``-l``. This replicates some of the internal
        logic of :py:class:`~awslimitchecker.runner.Runner`.

        The main purpose is:

        1. to allow passing in an existing
           :py:class:`awslimitchecker.checker.Checker` instance for testing
           the various authentication options, and,
        2. to verify that at least some limits are found

        This method is largely a duplication of
        :py:meth:`~awslimitchecker.runner.Runner.list_limits`.

        :param checker_args: dict of kwargs to pass to
          :py:class:`awslimitchecker.checker.Checker` constructor
        :type checker_args: dict
        :param creds_type: Type of credentials to use; 'normal', 'sts', or
          'sts_mfa'
        :type creds_type: str
        :param service_name: the Service name to test limits for; if None,
            check for all.
        :type service_name: str
        :param use_ta: whether or not to use TrustedAdvisor
        :type use_ta: bool
        :param expect_api_source: whether or not to expect a limit with an
          API source
        :type expect_api_source: bool
        :param allow_endpoint_error: passed on to
          :py:meth:`~.support.LogRecordHelper.unexpected_logs`
        :type allow_endpoint_error: bool
        """
        # destroy boto3's session, so it creates a new one
        boto3.DEFAULT_SESSION = None
        # set the env vars to the creds we want
        if creds_type == 'normal':
            creds = self.normal_creds()
        elif creds_type == 'sts':
            creds = self.sts_creds()
        elif creds_type == 'sts_mfa':
            creds = self.sts_mfa_creds()
            checker_args['mfa_serial_number'] = creds[2]
        else:
            raise RuntimeError("unknown creds type: '%s'" % creds_type)
        os.environ['AWS_ACCESS_KEY_ID'] = creds[0]
        os.environ['AWS_SECRET_ACCESS_KEY'] = creds[1]

        # this has to be generated inside the method, not in the method that
        # yields it
        if 'mfa_token' in checker_args:
            checker_args['mfa_token'] = self.totp_code(creds[3])

        # pytest-capturelog looked good, but won't work with our yielded
        # test functions, per https://github.com/pytest-dev/pytest/issues/227
        with LogCapture() as l:
            checker = AwsLimitChecker(**checker_args)
            limits = checker.get_limits(use_ta=use_ta, service=service_name)
        logs = LogRecordHelper(l)

        have_api_source = False
        data = {}
        for svc in sorted(limits.keys()):
            for lim in sorted(limits[svc].keys()):
                src_str = ''
                if limits[svc][lim].get_limit_source() == SOURCE_API:
                    have_api_source = True
                    src_str = ' (API)'
                if limits[svc][lim].get_limit_source() == SOURCE_TA:
                    src_str = ' (TA)'
                data["{s}/{l}".format(s=svc, l=lim)] = '{v}{t}'.format(
                    v=limits[svc][lim].get_limit(),
                    t=src_str)
        # this is the normal Runner output
        print(dict2cols(data))
        if expect_api_source:
            assert have_api_source is True
        # ensure we didn't log anything at WARN or above, except possibly
        # a TrustedAdvisor subscription required message
        records = logs.unexpected_logs(
            allow_endpoint_error=allow_endpoint_error
        )
        assert len(records) == 0, "awslimitchecker emitted unexpected log " \
            "messages at WARN or higher: \n%s" % "\n".join(records)
        polls = logs.num_ta_polls
        assert polls == 1, "awslimitchecker should have polled Trusted " \
            "Advisor once, but polled %s times" % polls

    @pytest.mark.integration
    @skip_if_pr
    def test_verify_usage(self, checker_args, creds_type, service_name,
                          expect_usage, allow_endpoint_error):
        """
        This essentially replicates what's done when awslimitchecker is called
        from the command line with ``-u``. This replicates some of the internal
        logic of :py:class:`~awslimitchecker.runner.Runner`.

        The main purpose is:

        1. to allow passing in an existing
           :py:class:`awslimitchecker.checker.Checker` instance for testing
           the various authentication options, and,
        2. to verify that at least some usage is found

        This method is largely a duplication of
        :py:meth:`~awslimitchecker.runner.Runner.show_usage`.

        :param checker_args: dict of kwargs to pass to
          :py:class:`awslimitchecker.checker.Checker` constructor
        :type checker_args: dict
        :param creds_type: Type of credentials to use; 'normal', 'sts', or
          'sts_mfa'
        :type creds_type: str
        :param service_name: the Service name to test usage for; if None,
            check for all.
        :type service_name: str
        :param expect_usage: whether or not to expect non-zero usage
        :type expect_usage: bool
        :param allow_endpoint_error: passed on to
          :py:meth:`~.support.LogRecordHelper.unexpected_logs`
        :type allow_endpoint_error: bool
        """
        # destroy boto3's session, so it creates a new one
        boto3.DEFAULT_SESSION = None
        # set the env vars to the creds we want
        if creds_type == 'normal':
            creds = self.normal_creds()
        elif creds_type == 'sts':
            creds = self.sts_creds()
        elif creds_type == 'sts_mfa':
            creds = self.sts_mfa_creds()
            checker_args['mfa_serial_number'] = creds[2]
        else:
            raise RuntimeError("unknown creds type: '%s'" % creds_type)
        os.environ['AWS_ACCESS_KEY_ID'] = creds[0]
        os.environ['AWS_SECRET_ACCESS_KEY'] = creds[1]

        # this has to be generated inside the method, not in the method that
        # yields it
        if 'mfa_token' in checker_args:
            checker_args['mfa_token'] = self.totp_code(creds[3])

        # pytest-capturelog looked good, but won't work with our yielded
        # test functions, per https://github.com/pytest-dev/pytest/issues/227
        with LogCapture() as l:
            checker = AwsLimitChecker(**checker_args)
            checker.find_usage(service=service_name)
            limits = checker.get_limits(service=service_name)
        logs = LogRecordHelper(l)

        have_usage = False
        data = {}
        for svc in sorted(limits.keys()):
            for lim in sorted(limits[svc].keys()):
                limit = limits[svc][lim]
                data["{s}/{l}".format(s=svc, l=lim)] = '{v}'.format(
                    v=limit.get_current_usage_str())
                for usage in limit.get_current_usage():
                    if usage.get_value() != 0:
                        have_usage = True
        # this is the normal Runner command line output
        print(dict2cols(data))
        if expect_usage:
            assert have_usage is True
        # ensure we didn't log anything at WARN or above, except possibly
        # a TrustedAdvisor subscription required message
        records = logs.unexpected_logs(
            allow_endpoint_error=allow_endpoint_error
        )
        assert len(records) == 0, "awslimitchecker emitted unexpected log " \
            "messages at WARN or higher: \n%s" % "\n".join(records)

    def normal_creds(self):
        return (
            os.environ.get('AWS_MAIN_ACCESS_KEY_ID', None),
            os.environ.get('AWS_MAIN_SECRET_ACCESS_KEY', None)
        )

    def sts_creds(self):
        return (
            os.environ.get('AWS_INTEGRATION_ACCESS_KEY_ID', None),
            os.environ.get('AWS_INTEGRATION_SECRET_KEY', None)
        )

    def sts_mfa_creds(self):
        if sys.version_info[0] < 3:
            return (
                os.environ.get('AWS_MFA_INTEGRATION_ACCESS_KEY_ID', None),
                os.environ.get('AWS_MFA_INTEGRATION_SECRET_KEY', None),
                os.environ.get('AWS_MFA_SERIAL', None),
                os.environ.get('AWS_MFA_SECRET', None)
            )
        return (
            os.environ.get('AWS_MFA3_INTEGRATION_ACCESS_KEY_ID', None),
            os.environ.get('AWS_MFA3_INTEGRATION_SECRET_KEY', None),
            os.environ.get('AWS_MFA3_SERIAL', None),
            os.environ.get('AWS_MFA3_SECRET', None)
        )

    def totp_code(self, secret):
        """
        note - this must be called from the yielded method, not the yielding one
        if it's called from the yielding method, all the codes will be the same
        """
        global MFA_CODE
        # need to make sure we have a unique code
        new_code = otp.get_totp(secret)
        code_str = "%06d" % new_code  # need to make sure it's a 0-padded str
        num_tries = 0
        while code_str == MFA_CODE and num_tries < 12:
            time.sleep(10)
            num_tries += 1
            new_code = otp.get_totp(secret)
            code_str = "%06d" % new_code  # need to make sure it's 0-padded
        if num_tries >= 12:
            # if we timed out, return the old code but don't update the global
            return code_str
        MFA_CODE = code_str
        return code_str
