.. awslimitchecker documentation master file, created by
   sphinx-quickstart on Sat Jun  6 16:12:56 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

awslimitchecker
================

.. image:: https://pypip.in/v/awslimitchecker/badge.png
   :target: https://crate.io/packages/awslimitchecker
   :alt: PyPi package version

.. image:: https://pypip.in/d/awslimitchecker/badge.png
   :target: https://crate.io/packages/awslimitchecker
   :alt: PyPi downloads

.. image:: https://landscape.io/github/jantman/awslimitchecker/master/landscape.svg
   :target: https://landscape.io/github/jantman/awslimitchecker/master
   :alt: Code Health

.. image:: https://secure.travis-ci.org/jantman/awslimitchecker.png?branch=master
   :target: http://travis-ci.org/jantman/awslimitchecker
   :alt: travis-ci for master branch

.. image:: https://codecov.io/github/jantman/awslimitchecker/coverage.svg?branch=master
   :target: https://codecov.io/github/jantman/awslimitchecker?branch=master
   :alt: coverage report for master branch

.. image:: https://readthedocs.org/projects/awslimitchecker/badge/?version=latest
   :target: https://readthedocs.org/projects/awslimitchecker/?badge=latest
   :alt: sphinx documentation for latest release

.. image:: https://readthedocs.org/projects/awslimitchecker/badge/?version=develop
   :target: https://readthedocs.org/projects/awslimitchecker/?badge=develop
   :alt: sphinx documentation for develop branch

.. image:: https://img.shields.io/github/release/jantman/awslimitchecker.svg
   :alt: GitHub latest release version
   :target: https://github.com/jantman/awslimitchecker/releases

.. image:: https://img.shields.io/github/forks/jantman/awslimitchecker.svg
   :alt: GitHub Forks
   :target: https://github.com/jantman/awslimitchecker/network

.. image:: https://img.shields.io/github/stars/jantman/awslimitchecker.svg
   :alt: GitHub Stars
   :target: https://github.com/jantman/awslimitchecker

.. image:: https://img.shields.io/github/issues/jantman/awslimitchecker.svg
   :alt: GitHub Open Issues
   :target: https://github.com/jantman/awslimitchecker/issues

.. image:: http://www.repostatus.org/badges/0.1.0/active.svg
   :alt: Project Status: Active - The project has reached a stable, usable state and is being actively developed.
   :target: http://www.repostatus.org/#active

A script and python module to check your AWS service limits and usage using `boto <http://docs.pythonboto.org/en/latest/>`_.

Users building out scalable services in Amazon AWS often run into AWS' `service limits <http://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html>`_ -
often at the least convenient time (i.e. mid-deploy or when autoscaling fails). Amazon's `Trusted Advisor <https://aws.amazon.com/premiumsupport/trustedadvisor/>`_
can help this, but even the version that comes with Business and Enterprise support only monitors a small subset of AWS limits
and only alerts *weekly*. awslimitchecker provides a command line script and reusable package that queries your current
usage of AWS resources and compares it to limits (hard-coded AWS defaults that you can override, or data from Trusted
Advisor where available), notifying you when you are approaching or at your limits.

Status
-------

This project is currently in very early development. At this time please consider it beta code and not fully tested in all situations;
furthermore its API may be changing rapidly. I hope to have this stabilized soon.

What It Does
------------

- Check current AWS resource usage against AWS Service Limits
- Show and inspect current usage
- Override default Service Limits (for accounts with increased limits)
- Compare current usage to limits; return information about limits that
  exceed thresholds, and (CLI wrapper) exit non-0 if thresholds are exceeded
- Define custom thresholds per-limit
- where possible, pull current limits from Trusted Advisor API
- Supports explicitly setting the AWS region
- Supports using `STS <http://docs.aws.amazon.com/STS/latest/APIReference/Welcome.html>`_ to assume roles in other accounts, including using ``external_id``.

Requirements
------------

* Python 2.6 through 3.4. Python 2.x is recommended, as `boto <http://docs.pythonboto.org/en/latest/>`_ (the AWS client library) currently has
  incomplete Python3 support. See the `boto documentation <http://boto.readthedocs.org/en/latest/>`_ for a list of AWS services that are Python3-compatible.
* Python `VirtualEnv <http://www.virtualenv.org/>`_ and ``pip`` (recommended installation method; your OS/distribution should have packages for these)
* `boto <http://docs.pythonboto.org/en/latest/>`_ >= 2.32.0

Installation and Usage
-----------------------

See :ref:`getting_started`.

Getting Help and Asking Questions
----------------------------------

See :ref:`getting_help`.

Changelog
---------

See `https://github.com/jantman/awslimitchecker/blob/develop/CHANGES.rst <https://github.com/jantman/awslimitchecker/blob/develop/CHANGES.rst>`_

Contents
=========

.. toctree::
   :maxdepth: 4

   Getting Started <getting_started>
   Command Line Usage <cli_usage>
   Python Usage <python_usage>
   Required IAM Permissions <iam_policy>
   Supported Limits <limits>
   Development <development>
   Internals <internals>
   API <modules>
   Getting Help <getting_help>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

License
--------

awslimitchecker is licensed under the `GNU Affero General Public License, version 3 or later <http://www.gnu.org/licenses/agpl.html>`_.
This shouldn't be much of a concern to most people; see :ref:`Development / AGPL <development.agpl>` for more information.
