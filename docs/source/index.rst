.. awslimitchecker documentation master file, created by
   sphinx-quickstart on Sat Jun  6 16:12:56 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

awslimitchecker
================

.. image:: https://pypip.in/v/awslimitchecker/badge.png
   :target: https://crate.io/packages/awslimitchecker

.. image:: https://pypip.in/d/awslimitchecker/badge.png
   :target: https://crate.io/packages/awslimitchecker

.. image:: https://landscape.io/github/jantman/awslimitchecker/master/landscape.svg
   :target: https://landscape.io/github/jantman/awslimitchecker/master
   :alt: Code Health

.. image:: https://secure.travis-ci.org/jantman/awslimitchecker.png?branch=master
   :target: http://travis-ci.org/jantman/awslimitchecker
   :alt: travis-ci for master branch

.. image:: https://codecov.io/github/jantman/awslimitchecker/coverage.svg?branch=master
   :target: https://codecov.io/github/jantman/awslimitchecker?branch=master
   :alt: coverage report for master branch

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

This project is currently in very early development.

To Do:
+++++++

- add documentation about region coming from boto config/defaults
- subtract reserved instances (per-AZ) from ec2 usage
- add documentation about AGPL?
- log WARNING at init - awslimitchecker {version} - AGPLv3 Free Software - {source_url}

  - version should attempt to tell if we're installed from package or git, and print the right thing
  - source_url should print the package source url, or the clone url if installed from git

- set warning and critical thresholds as percentage; override per limit as percentage or int
- runner --help should point to RTD
- if using TA, update limits from TA (where possible)
- should have library support (init?) and CLI args for TA:
  - don't use it at all
  - trigger updates now
  - update (and wait for) anything not updated in <time interval>
- should be able to do everything (library and CLI) for ALL services, or a list of services
- should be able to dump limits and current usage in machine-readable format
- should be able to either report, or warn (should the library throw exceptions??? or just return a dict?)
- helpers to check capacity for a given type of resource
- regions - should be able to run with a single region or a list of them??

  - future - support finding what regions our account has things in

- re-enable -n and -W in sphinx docs build, and linkcheck
- ec2 get_usage - how to make sure we're not counting reserved instances?

- AWSLimit objects will handle limit overrides, TA information and thresholds
- will also contain threshold checking logic and hold information on what breached the threshold
  (i.e. if it was SGs per VPC, hold the vpc_ids that crossed threshold
- for now, rip out the runner logic to show individual services; can add that back later
- tox should generate checks.rst from actual source

Requirements
------------

* Python 2.6 or 2.7 (`boto <http://docs.pythonboto.org/en/latest/>`_ currently has incomplete python3 support)
* Python `VirtualEnv <http://www.virtualenv.org/>`_ and ``pip`` (recommended installation method; your OS/distribution should have packages for these)
* `boto <http://docs.pythonboto.org/en/latest/>`_ >= 2.30.0

Installation and Usage
-----------------------

See :ref:`getting_started`.

Getting Help and Asking Questions
----------------------------------

See :ref:`getting_help`.

Contents
=========

.. toctree::
   :maxdepth: 4

   Getting Started <getting_started>
   Current Checks <checks>
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
This shouldn't be much of a concern to most people.

If you're simply *running* awslimitchecker, all you must do is provide a notice on where to get the source code
in your output; this is already handled via a warning-level log message in the package. If you modify awslimitchecker's
code, you must update this URL to reflect your modifications (see ``awslimitchecker/version.py``).

If you're distributing awslimitchecker with modifications or as part of your own software (as opposed to simply a
requirement that gets installed with pip), please read the license and ensure that you comply with its terms.

If you are running awslimitchecker as part of a hosted service that users somehow interact with, please
ensure that the source code URL is visible in the output given to users.
