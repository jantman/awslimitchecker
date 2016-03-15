awslimitchecker
========================

.. image:: https://img.shields.io/pypi/v/awslimitchecker.svg
   :target: https://pypi.python.org/pypi/awslimitchecker
   :alt: PyPi package version

.. image:: https://img.shields.io/pypi/dm/awslimitchecker.svg
   :target: https://pypi.python.org/pypi/awslimitchecker
   :alt: PyPi downloads

.. image:: https://img.shields.io/github/forks/jantman/awslimitchecker.svg
   :alt: GitHub Forks
   :target: https://github.com/jantman/awslimitchecker/network

.. image:: https://img.shields.io/github/issues/jantman/awslimitchecker.svg
   :alt: GitHub Open Issues
   :target: https://github.com/jantman/awslimitchecker/issues

.. image:: http://www.repostatus.org/badges/0.1.0/active.svg
   :alt: Project Status: Active - The project has reached a stable, usable state and is being actively developed.
   :target: http://www.repostatus.org/#active

Master:

.. image:: https://secure.travis-ci.org/jantman/awslimitchecker.png?branch=master
   :target: http://travis-ci.org/jantman/awslimitchecker
   :alt: travis-ci for master branch

.. image:: https://landscape.io/github/jantman/awslimitchecker/master/landscape.svg
   :target: https://landscape.io/github/jantman/awslimitchecker/master
   :alt: Code Health

.. image:: https://codecov.io/github/jantman/awslimitchecker/coverage.svg?branch=master
   :target: https://codecov.io/github/jantman/awslimitchecker?branch=master
   :alt: coverage report for master branch

.. image:: https://readthedocs.org/projects/awslimitchecker/badge/?version=latest
   :target: https://readthedocs.org/projects/awslimitchecker/?badge=latest
   :alt: sphinx documentation for latest release

Develop:

.. image:: https://secure.travis-ci.org/jantman/awslimitchecker.png?branch=develop
   :target: http://travis-ci.org/jantman/awslimitchecker
   :alt: travis-ci for develop branch

.. image:: https://landscape.io/github/jantman/awslimitchecker/develop/landscape.svg
   :target: https://landscape.io/github/jantman/awslimitchecker/develop
   :alt: Code Health

.. image:: https://codecov.io/github/jantman/awslimitchecker/coverage.svg?branch=develop
   :target: https://codecov.io/github/jantman/awslimitchecker?branch=develop
   :alt: coverage report for develop branch

.. image:: https://readthedocs.org/projects/awslimitchecker/badge/?version=develop
   :target: https://readthedocs.org/projects/awslimitchecker/?badge=develop
   :alt: sphinx documentation for develop branch

A script and python module to check your AWS service limits and usage, and warn when usage approaches limits.

Users building out scalable services in Amazon AWS often run into AWS' `service limits <http://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html>`_ -
often at the least convenient time (i.e. mid-deploy or when autoscaling fails). Amazon's `Trusted Advisor <https://aws.amazon.com/premiumsupport/trustedadvisor/>`_
can help this, but even the version that comes with Business and Enterprise support only monitors a small subset of AWS limits
and only alerts *weekly*. awslimitchecker provides a command line script and reusable package that queries your current
usage of AWS resources and compares it to limits (hard-coded AWS defaults that you can override, API-based limits where available, or data from Trusted
Advisor where available), notifying you when you are approaching or at your limits.

Full project documentation is available at `http://awslimitchecker.readthedocs.org <http://awslimitchecker.readthedocs.org>`_.

Status
------

This project has just undergone a relatively major refactor to migrate from
`boto <http://docs.pythonboto.org/en/latest/>`_ to `boto3 <http://boto3.readthedocs.org/>`_,
along with a refactor of much of the connection and usage gathering code. Until
it's been running in production for a while, please consider this to be "beta"
and make every effort to manually confirm the results for your environment.

What It Does
------------

- Check current AWS resource usage against AWS Service Limits
- Show and inspect current usage
- Override default Service Limits (for accounts with increased limits)
- Compare current usage to limits; return information about limits that
  exceed thresholds, and (CLI wrapper) exit non-0 if thresholds are exceeded
- Define custom thresholds per-limit
- where possible, pull current limits from Trusted Advisor API
- where possible, pull current limits from each service's API (for services that provide this information)
- Supports explicitly setting the AWS region
- Supports using `STS <http://docs.aws.amazon.com/STS/latest/APIReference/Welcome.html>`_ to assume roles in other accounts, including using ``external_id``.

Requirements
------------

* Python 2.6 through 3.5 (it should work, but is no longer tested, with PyPy and PyPy3).
* Python `VirtualEnv <http://www.virtualenv.org/>`_ and ``pip`` (recommended installation method; your OS/distribution should have packages for these)
* `boto3 <http://boto3.readthedocs.org/>`_ >= 1.2.3

Installation
------------

It's recommended that you install into a virtual environment (virtualenv /
venv). See the `virtualenv usage documentation <http://www.virtualenv.org/en/latest/>`_
for information on how to create a venv. If you really want to install
system-wide, you can (using sudo).

.. code-block:: bash

    pip install awslimitchecker

Credentials
-----------

Aside from STS, awslimitchecker does nothing with AWS credentials, it leaves that to boto itself.
You must either have your credentials configured in one of boto's supported config
files, or set as environment variables. See
`boto3 config <http://boto3.readthedocs.org/en/latest/guide/configuration.html#guide-configuration>`_
and
`this project's documentation <http://awslimitchecker.readthedocs.org/en/latest/getting_started.html#credentials>`_
for further information.

**Please note** that version 0.3.0 of awslimitchecker moved from using ``boto`` as its AWS API client to using
``boto3``. This change is mostly transparent, but there is a minor change in how AWS credentials are handled. In
``boto``, if the ``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY`` environment variables were set, and the
region was not set explicitly via awslimitchecker, the AWS region would either be taken from the ``AWS_DEFAULT_REGION``
environment variable or would default to us-east-1, regardless of whether a configuration file (``~/.aws/credentials``
or ``~/.aws/config``) was present. With boto3, it appears that the default region from the configuration file will be
used if present, regardless of whether the credentials come from that file or from environment variables.

When using STS, you will need to specify the ``-r`` / ``--region`` option as well as the ``-A`` / ``--sts-account-id``
and ``-R`` / ``--sts-account-role`` options to specify the Account ID that you want to assume a role in, and the
name of the role you want to assume. If an external ID is required, you can specify it with ``-E`` / ``--external-id``.

Usage
-----

For basic usage, see:

.. code-block:: bash

    awslimitchecker --help

See the `project documentation <http://awslimitchecker.readthedocs.org>`_
for further information.

Bugs, Feature Requests, Support
-------------------------------

Questions, comments, Bug reports and feature requests are happily accepted via
the `GitHub Issue Tracker <https://github.com/jantman/awslimitchecker/issues>`_.
Pull requests are always welcome.

Please see the `Development <http://awslimitchecker.readthedocs.org/en/latest/development.html>`_
and `Getting Help <http://awslimitchecker.readthedocs.org/en/latest/getting_help.html>`_ documentation for more information.

For paid support and development options, please see the
`Enterprise Support Agreements and Contract Development <http://awslimitchecker.readthedocs.org/en/latest/getting_help.html#getting-help-paid-support>`_
section of the documentation.

Changelog
---------

See `https://github.com/jantman/awslimitchecker/blob/develop/CHANGES.rst <https://github.com/jantman/awslimitchecker/blob/develop/CHANGES.rst>`_.

Contributions
-------------

Pull requests are most definitely welcome. Please cut them against the **develop** branch. For more information, see
the `development documentation <http://awslimitchecker.readthedocs.org/en/latest/development.html#pull-requests>`_. I'm
also happy to accept contributions in the form of bug reports, feature requests, testing, etc.

License
-------

awslimitchecker is licensed under the `GNU Affero General Public License, version 3 or later <http://www.gnu.org/licenses/agpl.html>`_.
This shouldn't be much of a concern to most people.

If you're simply *running* awslimitchecker, all you must do is provide a notice on where to get the source code
in your output; this is already handled via a warning-level log message in the package. If you modify awslimitchecker's
code, you must update this URL to reflect your modifications (see ``awslimitchecker/version.py``).

If you're distributing awslimitchecker with modifications or as part of your own software (as opposed to simply a
requirement that gets installed with pip), please read the license and ensure that you comply with its terms.

If you are running awslimitchecker as part of a hosted service that users somehow interact with, please
ensure that the source code URL is visible in the output given to users.
