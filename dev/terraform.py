#!/usr/bin/env python
"""
dev/terraform.py

Wrapper script around Terraform, using the TerraformRunner class from
`webhook2lambda2sqs <https://github.com/jantman/webhook2lambda2sqs>`_
to update my integration test accounts with the current generated IAM policy.

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

##############################################################################
Copyright 2015-2018 Jason Antman <jason@jasonantman.com>

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

import logging
import json
import os
import sys
import subprocess
import re
from configparser import SafeConfigParser

from awslimitchecker.checker import AwsLimitChecker

FORMAT = "[%(levelname)s %(filename)s:%(lineno)s - %(name)s.%(funcName)s() ] " \
         "%(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
logger = logging.getLogger()


def run_cmd(args, stream=False, shell=True):
    """
    Execute a command via :py:class:`subprocess.Popen`; return its output
    (string, combined STDOUT and STDERR) and exit code (int). If stream is True,
    also stream the output to STDOUT in realtime.

    :param args: the command to run and arguments, as a list or string
    :param stream: whether or not to stream combined OUT and ERR in realtime
    :type stream: bool
    :param shell: whether or not to execute the command through the shell
    :type shell: bool
    :return: 2-tuple of (combined output (str), return code (int))
    :rtype: tuple
    """
    s = ''
    if stream:
        s = ' and streaming output'
    logger.info('Running command%s: %s', s, args)
    outbuf = ''
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         shell=shell)
    logger.debug('Started process; pid=%s', p.pid)
    for c in iter(lambda: p.stdout.read(1), ''):
        if p.poll() is not None:
            break
        outbuf += c.decode()
        if stream:
            sys.stdout.write(c.decode())
    sys.stdout.write("\n")
    p.poll()  # set returncode
    logger.info('Command exited with code %d', p.returncode)
    logger.debug("Command output:\n%s\n", outbuf)
    return outbuf, p.returncode


class TerraformRunner(object):

    def __init__(self, config, tf_path):
        """
        Initialize the Terraform command runner.

        :param config: program configuration
        :type config: :py:class:`~.Config`
        :param tf_path: path to terraform binary
        :type tf_path: str
        """
        self.config = config
        self.tf_path = tf_path
        # if we fail getting the version, assume newest
        self.tf_version = (999, 999, 999)
        self._validate()

    def _validate(self):
        """
        Confirm that we can run terraform (by calling its version action)
        and then validate the configuration.
        """
        try:
            out = self._run_tf('version')
        except:
            raise Exception('ERROR: executing \'%s version\' failed; is '
                            'terraform installed and is the path to it (%s) '
                            'correct?' % (self.tf_path, self.tf_path))
        res = re.search(r'Terraform v(\d+)\.(\d+)\.(\d+)', out)
        if res is None:
            logger.error('Unable to determine terraform version; will not '
                         'validate config. Note that this may cause problems '
                         'when using older Terraform versions. This program '
                         'requires Terraform >= 0.6.16.')
            return
        self.tf_version = (
            int(res.group(1)), int(res.group(2)), int(res.group(3))
        )
        logger.debug('Terraform version: %s', self.tf_version)
        if self.tf_version < (0, 6, 16):
            raise Exception('This program requires Terraform >= 0.6.16, as '
                            'that version introduces a bug fix for working '
                            'with api_gateway_integration_response resources; '
                            'see: https://github.com/hashicorp/terraform/pull'
                            '/5893')
        try:
            self._run_tf('validate', ['.'])
        except Exception as ex:
            logger.critical("Terraform config validation failed. "
                            "This is almost certainly a bug in "
                            "webhook2lambda2sqs; please re-run with '-vv' and "
                            "open a bug at <https://github.com/jantman/"
                            "webhook2lambda2sqs/issues>. Exception: %s", ex)
            raise Exception(
                'ERROR: Terraform config validation failed: %s' % ex
            )

    def _args_for_remote(self):
        """
        Generate arguments for 'terraform remote config'. Return None if
        not present in configuration.

        :return: list of args for 'terraform remote config' or None
        :rtype: :std:term:`list`
        """
        conf = self.config.get('terraform_remote_state')
        if conf is None:
            return None
        args = ['-backend=%s' % conf['backend']]
        for k, v in sorted(conf['config'].items()):
            args.append('-backend-config="%s=%s"' % (k, v))
        return args

    def _set_remote(self, stream=False):
        """
        Call :py:meth:`~._args_for_remote`; if the return value is not None,
        execute 'terraform remote config' with those arguments and ensure it
        exits 0.

        :param stream: whether or not to stream TF output in realtime
        :type stream: bool
        """
        args = self._args_for_remote()
        if args is None:
            logger.debug('_args_for_remote() returned None; not configuring '
                         'terraform remote')
            return
        logger.warning('Setting terraform remote config: %s', ' '.join(args))
        args = ['config'] + args
        self._run_tf('remote', cmd_args=args, stream=stream)
        logger.info('Terraform remote configured.')

    def _run_tf(self, cmd, cmd_args=[], stream=False):
        """
        Run a single terraform command via :py:func:`~.utils.run_cmd`;
        raise exception on non-zero exit status.

        :param cmd: terraform command to run
        :type cmd: str
        :param cmd_args: arguments to command
        :type cmd_args: :std:term:`list`
        :return: command output
        :rtype: str
        :raises: Exception on non-zero exit
        """
        args = [self.tf_path, cmd] + cmd_args
        arg_str = ' '.join(args)
        logger.info('Running terraform command: %s', arg_str)
        out, retcode = run_cmd(arg_str, stream=stream)
        if retcode != 0:
            logger.critical('Terraform command (%s) failed with exit code '
                            '%d:\n%s', arg_str, retcode, out)
            raise Exception('terraform %s failed' % cmd)
        return out

    def plan(self, stream=False):
        """
        Run a 'terraform plan'

        :param stream: whether or not to stream TF output in realtime
        :type stream: bool
        """
        self._setup_tf(stream=stream)
        args = ['-input=false', '-refresh=true', '.']
        logger.warning('Running terraform plan: %s', ' '.join(args))
        out = self._run_tf('plan', cmd_args=args, stream=stream)
        if stream:
            logger.warning('Terraform plan finished successfully.')
        else:
            logger.warning("Terraform plan finished successfully:\n%s", out)

    def _taint_deployment(self, stream=False):
        """
        Run 'terraform taint aws_api_gateway_deployment.depl' to taint the
        deployment resource. This is a workaround for
        https://github.com/hashicorp/terraform/issues/6613

        :param stream: whether or not to stream TF output in realtime
        :type stream: bool
        """
        args = ['aws_api_gateway_deployment.depl']
        logger.warning('Running terraform taint: %s as workaround for '
                       '<https://github.com/hashicorp/terraform/issues/6613>',
                       ' '.join(args))
        out = self._run_tf('taint', cmd_args=args, stream=stream)
        if stream:
            logger.warning('Terraform taint finished successfully.')
        else:
            logger.warning("Terraform taint finished successfully:\n%s", out)

    def apply(self, stream=False):
        """
        Run a 'terraform apply'

        :param stream: whether or not to stream TF output in realtime
        :type stream: bool
        """
        self._setup_tf(stream=stream)
        try:
            self._taint_deployment(stream=stream)
        except Exception:
            pass
        args = ['-input=false', '-refresh=true', '.']
        logger.warning('Running terraform apply: %s', ' '.join(args))
        out = self._run_tf('apply', cmd_args=args, stream=stream)
        if stream:
            logger.warning('Terraform apply finished successfully.')
        else:
            logger.warning("Terraform apply finished successfully:\n%s", out)
        self._show_outputs()

    def _show_outputs(self):
        """
        Print the terraform outputs.
        """
        outs = self._get_outputs()
        print("\n\n" + '=> Terraform Outputs:')
        for k in sorted(outs):
            print('%s = %s' % (k, outs[k]))

    def _get_outputs(self):
        """
        Return a dict of the terraform outputs.

        :return: dict of terraform outputs
        :rtype: dict
        """
        if self.tf_version >= (0, 7, 0):
            logger.debug('Running: terraform output')
            res = self._run_tf('output', cmd_args=['-json'])
            outs = json.loads(res.strip())
            res = {}
            for k in outs.keys():
                if isinstance(outs[k], type({})):
                    res[k] = outs[k]['value']
                else:
                    res[k] = outs[k]
            logger.debug('Terraform outputs: %s', res)
            return res
        logger.debug('Running: terraform output')
        res = self._run_tf('output')
        outs = {}
        for line in res.split("\n"):
            line = line.strip()
            if line == '':
                continue
            parts = line.split(' = ', 1)
            outs[parts[0]] = parts[1]
        logger.debug('Terraform outputs: %s', outs)
        return outs

    def destroy(self, stream=False):
        """
        Run a 'terraform destroy'

        :param stream: whether or not to stream TF output in realtime
        :type stream: bool
        """
        self._setup_tf(stream=stream)
        args = ['-refresh=true', '-force', '.']
        logger.warning('Running terraform destroy: %s', ' '.join(args))
        out = self._run_tf('destroy', cmd_args=args, stream=stream)
        if stream:
            logger.warning('Terraform destroy finished successfully.')
        else:
            logger.warning("Terraform destroy finished successfully:\n%s", out)

    def _setup_tf(self, stream=False):
        """
        Setup terraform; either 'remote config' or 'init' depending on version.
        """
        if self.tf_version < (0, 9, 0):
            self._set_remote(stream=stream)
            return
        self._run_tf('init', stream=stream)
        logger.info('Terraform initialized')


class TerraformIAM(object):

    def __init__(self):
        logger.debug('Getting credentials')
        scriptpath = os.path.dirname(os.path.realpath(__file__))
        logger.debug('cd to scriptpath: %s', scriptpath)
        os.chdir(scriptpath)

    def run(self):
        """Run the Terraform"""
        pol = self.get_iam_policy()
        logger.info("Got IAM policy:\n%s\n", pol)
        with open('iam_policy.json', 'w') as fh:
            fh.write(pol)
        logger.info('Wrote policy to: iam_policy.json')
        self.run_tf()

    def run_tf(self):
        """actually run the terraform"""
        conf = {
            'terraform_remote_state': {
                'backend': 's3',
                'config': {
                    'bucket': 'jantman-personal',
                    'key': 'terraform/awslimitchecker-integration-iam',
                    'region': 'us-east-1'
                }
            }
        }
        runner = TerraformRunner(conf, 'terraform')
        runner._setup_tf(stream=True)
        runner._run_tf('plan', cmd_args=['-input=false', '-refresh=true', '.'],
                       stream=True)
        res = input('Does this look correct? [y|N] ')
        if res.lower().strip() != 'y':
            logger.error('OK, aborting!')
            return
        runner._run_tf(
            'apply',
            cmd_args=['-input=false', '-refresh=true', '-auto-approve', '.'],
            stream=True
        )

    def get_iam_policy(self):
        """Return the current IAM policy as a json-serialized string"""
        checker = AwsLimitChecker()
        policy = checker.get_required_iam_policy()
        return json.dumps(policy, sort_keys=True, indent=2)


if __name__ == "__main__":
    t = TerraformIAM()
    t.run()
