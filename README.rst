botolimitchecker
========================

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

Full project documentation is available at [http://botolimitchecker.readthedocs.org](http://botolimitchecker.readthedocs.org).

Requirements
------------

* Python 2.6 or 2.7 (`boto <http://docs.pythonboto.org/en/latest/>`_ currently has incomplete python3 support)
* Python `VirtualEnv <http://www.virtualenv.org/>`_ and ``pip`` (recommended installation method; your OS/distribution should have packages for these)
* `boto <http://docs.pythonboto.org/en/latest/>`_

Installation
------------

It's recommended that you install into a virtual environment (virtualenv /
venv). See the `virtualenv usage documentation <http://www.virtualenv.org/en/latest/>`_
for information on how to create a venv. If you really want to install
system-wide, you can (using sudo).

.. code-block:: bash

    pip install botolimitchecker

Credentials
------------

botolimitchecker does nothing with AWS credentials, it leaves that to boto itself.
You must either have your credentials configured in one of boto's supported config
files, or set as environment variables. See `boto config <http://docs.pythonboto.org/en/latest/boto_config_tut.html>`_
for further information.

Usage
-----

For basic usage, see:

.. code-block:: bash

    botolimitchecker --help

See the [project documentation](http://botolimitchecker.readthedocs.org) for further information.

Bugs and Feature Requests
-------------------------

Questions, comments, Bug reports and feature requests are happily accepted via
the `GitHub Issue Tracker <https://github.com/jantman/botolimitchecker/issues>`_.
Pull requests are always welcome.

Please see the [Development]() and [Getting Help]() documentation for more information.

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
