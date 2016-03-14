.. meta::
   :description: A script and python module to check your AWS service limits and usage, and warn when usage approaches limits.

awslimitchecker
================

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

Status
-------

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

* Python 2.6 through 3.5  (it should work, but is no longer tested, with PyPy and PyPy3).
* Python `VirtualEnv <http://www.virtualenv.org/>`_ and ``pip`` (recommended installation method; your OS/distribution should have packages for these)
* `boto3 <http://boto3.readthedocs.org/>`_ >= 1.2.3

Installation and Usage
-----------------------

See :ref:`getting_started`.

Getting Help and Asking Questions
----------------------------------

See :ref:`getting_help`.

For paid support and development options, please see the
:ref:`Enterprise Support Agreements and Contract Development <getting_help.paid_support>`
section of the documentation.

Contents
=========

.. toctree::
   :maxdepth: 4

   Getting Started <getting_started>
   Command Line Usage <cli_usage>
   Python Usage <python_usage>
   Required IAM Permissions <iam_policy>
   Supported Limits <limits>
   Getting Help <getting_help>
   Development <development>
   Internals <internals>
   API <modules>
   Changelog <changes>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

License
--------

awslimitchecker is licensed under the `GNU Affero General Public License, version 3 or later <http://www.gnu.org/licenses/agpl.html>`_.
This shouldn't be much of a concern to most people; see :ref:`Development / AGPL <development.agpl>` for more information.
