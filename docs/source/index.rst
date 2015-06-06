.. botolimitchecker documentation master file, created by
   sphinx-quickstart on Sat Jun  6 16:12:56 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

botolimitchecker
================

.. image:: https://pypip.in/v/botolimitchecker/badge.png
   :target: https://crate.io/packages/botolimitchecker

.. image:: https://pypip.in/d/botolimitchecker/badge.png
   :target: https://crate.io/packages/botolimitchecker

.. image:: https://landscape.io/github/jantman/botolimitchecker/master/landscape.svg
   :target: https://landscape.io/github/jantman/botolimitchecker/master
   :alt: Code Health

.. image:: https://secure.travis-ci.org/jantman/botolimitchecker.png?branch=master
   :target: http://travis-ci.org/jantman/botolimitchecker
   :alt: travis-ci for master branch

.. image:: https://codecov.io/github/jantman/botolimitchecker/coverage.svg?branch=master
   :target: https://codecov.io/github/jantman/botolimitchecker?branch=master
   :alt: coverage report for master branch

.. image:: http://www.repostatus.org/badges/0.1.0/active.svg
   :alt: Project Status: Active - The project has reached a stable, usable state and is being actively developed.
   :target: http://www.repostatus.org/#active

A script and python module to check your AWS service limits and usage using `boto <http://docs.pythonboto.org/en/latest/>`_.

Users building out scalable services in Amazon AWS often run into AWS' `service limits <http://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html>`_ -
often at the least convenient time (i.e. mid-deploy or when autoscaling fails). Amazon's `Trusted Advisor <https://aws.amazon.com/premiumsupport/trustedadvisor/>`_
can help this, but even the version that comes with Business and Enterprise support only monitors a small subset of AWS limits
and only alerts *weekly*. Botolimitchecker provides a command line script and reusable package that queries your current
usage of AWS resources and compares it to limits (hard-coded AWS defaults that you can override, or data from Trusted
Advisor where available), notifying you when you are approaching or at your limits.

Requirements
------------

* Python 2.6 or 2.7 (`boto <http://docs.pythonboto.org/en/latest/>`_ currently has incomplete python3 support)
* Python `VirtualEnv <http://www.virtualenv.org/>`_ and ``pip`` (recommended installation method; your OS/distribution should have packages for these)
* `boto <http://docs.pythonboto.org/en/latest/>`_

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

   Features <features>
   Getting Started <getting_started>
   Development <development>
   Getting Help <getting_help>
   API <modules>
   search


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

License
--------

botolimitchecker is licensed under the `GNU Affero General Public License, version 3 or later <http://www.gnu.org/licenses/agpl.html>`_.
This shouldn't be much of a concern to most people.

If you're simply *running* botolimitchecker, all you must do is provide a notice on where to get the source code
in your output; this is already handled via a warning-level log message in the package. If you modify botolimitchecker's
code, you must update this URL to reflect your modifications (see ``botolimitchecker/version.py``).

If you're distributing botolimitchecker with modifications or as part of your own software (as opposed to simply a
requirement that gets installed with pip), please read the license and ensure that you comply with its terms.

If you are running botolimitchecker as part of a hosted service that users somehow interact with, please
ensure that the source code URL is visible in the output given to users.
