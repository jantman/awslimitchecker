awslimitchecker
===============

.. image:: https://img.shields.io/pypi/v/awslimitchecker.svg
   :target: https://pypi.python.org/pypi/awslimitchecker
   :alt: PyPi package version

.. image:: http://jantman-personal-public.s3-website-us-east-1.amazonaws.com/pypi-stats/awslimitchecker/per-month.svg
   :target: http://jantman-personal-public.s3-website-us-east-1.amazonaws.com/pypi-stats/awslimitchecker/index.html
   :alt: PyPi downloads

.. image:: https://img.shields.io/github/forks/jantman/awslimitchecker.svg
   :alt: GitHub Forks
   :target: https://github.com/jantman/awslimitchecker/network

.. image:: https://img.shields.io/github/issues/jantman/awslimitchecker.svg
   :alt: GitHub Open Issues
   :target: https://github.com/jantman/awslimitchecker/issues

.. image:: http://www.repostatus.org/badges/1.1.0/active.svg
   :alt: Project Status: Active - The project has reached a stable, usable state and is being actively developed.
   :target: http://www.repostatus.org/#active

.. image:: http://badges.gitter.im/jantman/awslimitchecker.png
   :alt: gitter.im chat
   :target: https://gitter.im/awslimitchecker/Lobby

Master:

.. image:: https://secure.travis-ci.org/jantman/awslimitchecker.png?branch=master
   :target: http://travis-ci.org/jantman/awslimitchecker
   :alt: travis-ci for master branch

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
and only alerts *weekly*. The new Service Quotas service can also help with this, but relies on CloudWatch alarms per-limit to notify
you when you approach your limits; this cannot easily scale to the hundreds of current service limits. awslimitchecker provides a command line
script and reusable Python package that queries your current usage of AWS resources and compares it to limits (hard-coded AWS defaults that you
can override, API-based limits where available, Service Quotas data where available, or data from Trusted Advisor where available), notifying
you when you are approaching or at your limits.

Full project documentation for the latest release is available at `http://awslimitchecker.readthedocs.io/en/latest/ <http://awslimitchecker.readthedocs.io/en/latest/>`_.

Status
------

awslimitchecker is mature software, with approximately 13,000 downloads per month and in daily use at numerous organizations.

Development status is being tracked on a board at waffle.io: https://waffle.io/jantman/awslimitchecker

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
- where possible, pull current limits from the Service Quotas service
- Supports explicitly setting the AWS region
- Supports using `STS <http://docs.aws.amazon.com/STS/latest/APIReference/Welcome.html>`_ to assume roles in other accounts, including using ``external_id``.
- Optionally refresh Trusted Advisor "Service Limits" check before polling
  Trusted Advisor data, and optionally wait for the refresh to complete (up to
  an optional maximum time limit). See
  `Getting Started - Trusted Advisor <http://awslimitchecker.readthedocs.io/en/latest/getting_started.html#trusted-advisor>`_
  for more information.
- Optionally send current usage and limit metrics to a metrics store, such as Datadog.
- Optionally send warning/critical alerts to notification providers, such as PagerDuty.

Requirements
------------

**Either Docker in order to run via the** `docker image <http://awslimitchecker.readthedocs.io/en/latest/docker.html>`__, **or:**

* Python 3.5 or newer. Python 2.7 will not be supported as of January 1, 2010.
* Python `VirtualEnv <http://www.virtualenv.org/>`_ and ``pip`` (recommended installation method; your OS/distribution should have packages for these)
* `boto3 <http://boto3.readthedocs.org/>`_ >= 1.4.6 and its dependency `botocore <https://botocore.readthedocs.io/en/latest/>`_ >= 1.6.0.

Installation and Usage
-----------------------

See `Getting Started <http://awslimitchecker.readthedocs.io/en/latest/getting_started.html>`_.

Credentials
-----------

See `Credentials <http://awslimitchecker.readthedocs.io/en/latest/getting_started.html#credentials>`_.

Getting Help and Asking Questions
----------------------------------

See `Getting Help <http://awslimitchecker.readthedocs.io/en/latest/getting_help.html>`_.

For paid support and development options, please see the
`Enterprise Support Agreements and Contract Development <http://awslimitchecker.readthedocs.io/en/latest/getting_help.html#enterprise-support-agreements-and-contract-development>`_
section of the documentation.

There is also a `gitter.im chat channel <https://gitter.im/awslimitchecker/Lobby>`_ for support and discussion.

Changelog
---------

See `Changelog <http://awslimitchecker.readthedocs.io/en/latest/changes.html>`_.

Contributions
-------------

Pull requests are most definitely welcome. Please cut them against the **develop** branch. For more information, see
the `development documentation <http://awslimitchecker.readthedocs.org/en/latest/development.html#pull-requests>`_. I'm
also happy to accept contributions in the form of bug reports, feature requests, testing, etc.

License
-------

awslimitchecker is licensed under the `GNU Affero General Public License, version 3 or later <http://www.gnu.org/licenses/agpl.html>`_.
This shouldn't be much of a concern to most people; see `Development / AGPL <http://awslimitchecker.readthedocs.io/en/latest/development.html#agpl-license>`_ for more information.
