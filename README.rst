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
Advisor where available), notifying you when you are approaching or at your limits. It also provides useful helper
methods to check capacity for a given number of a type of resource, usable as a sanity check in your deployment pipeline.

Requirements
------------

* Python 2.6 or 2.7 (`boto <http://docs.pythonboto.org/en/latest/>`_ currently has incomplete python3 support)
* Python `VirtualEnv <http://www.virtualenv.org/>`_ and ``pip`` (recommended installation method; your OS/distribution should have packages for these)

Installation
------------

It's recommended that you install into a virtual environment (virtualenv /
venv). See the `virtualenv usage documentation <http://www.virtualenv.org/en/latest/>`_
for information on how to create a venv. If you really want to install
system-wide, you can (using sudo).

.. code-block:: bash

    pip install botolimitchecker

Configuration
-------------

Something here.

Usage
-----

Something else here.

Bugs and Feature Requests
-------------------------

Bug reports and feature requests are happily accepted via the `GitHub Issue Tracker <https://github.com/jantman/botolimitchecker/issues>`_. Pull requests are
welcome. Issues that don't have an accompanying pull request will be worked on
as my time and priority allows.

Development
===========

To install for development:

1. Fork the `botolimitchecker <https://github.com/jantman/botolimitchecker>`_ repository on GitHub
2. Create a new branch off of master in your fork.

.. code-block:: bash

    $ virtualenv botolimitchecker
    $ cd botolimitchecker && source bin/activate
    $ pip install -e git+git@github.com:YOURNAME/botolimitchecker.git@BRANCHNAME#egg=botolimitchecker
    $ cd src/botolimitchecker

The git clone you're now in will probably be checked out to a specific commit,
so you may want to ``git checkout BRANCHNAME``.

Guidelines
----------

* pep8 compliant with some exceptions (see pytest.ini)
* 100% test coverage with pytest (with valid tests)

Unit Testing
-------------

Testing is done via `pytest <http://pytest.org/latest/>`_, driven by `tox <http://tox.testrun.org/>`_.

* testing is as simple as:

  * ``pip install tox``
  * ``tox``

* If you want to see code coverage: ``tox -e cov``

  * this produces two coverage reports - a summary on STDOUT and a full report in the ``htmlcov/`` directory

* If you want to pass additional arguments to pytest, add them to the tox command line after "--". i.e., for verbose pytext output on py27 tests: ``tox -e py27 -- -v``

Note that while boto currently doesn't have python3 support, we still run tests against py3 to ensure that this package
is ready for it when boto is.

Integration Testing
--------------------

TBD.
  
Release Checklist
-----------------

1. Open an issue for the release; cut a branch off master for that issue.
2. Confirm that there are CHANGES.rst entries for all major changes.
3. Ensure that Travis tests passing in all environments.
4. Ensure that test coverage is no less than the last release (ideally, 100%).
5. Increment the version number in botolimitchecker/version.py and add version and release date to CHANGES.rst, then push to GitHub.
6. Confirm that README.rst renders correctly on GitHub.
7. Upload package to testpypi, confirm that README.rst renders correctly.

   * Make sure your ~/.pypirc file is correct
   * ``python setup.py register -r https://testpypi.python.org/pypi``
   * ``python setup.py sdist upload -r https://testpypi.python.org/pypi``
   * Check that the README renders at https://testpypi.python.org/pypi/botolimitchecker

8. Create a pull request for the release to be merge into master. Upon successful Travis build, merge it.
9. Tag the release in Git, push tag to GitHub:

   * tag the release. for now the message is quite simple: ``git tag -a vX.Y.Z -m 'X.Y.Z released YYYY-MM-DD'``
   * push the tag to GitHub: ``git push origin vX.Y.Z``

11. Upload package to live pypi:

    * ``python setup.py sdist upload``

10. make sure any GH issues fixed in the release were closed.

License
--------

botolimitchecker is licensed under the `GNU Affero General Public License, version 3 or later <http://www.gnu.org/licenses/agpl.html>`_.
This shouldn't be much of a concern to most people.

If you're simply *running* botolimitchecker, all you must do is provide a notice on where to get the source code
in your output; this is already handled via a warning-level log message in the package. If you modify botolimitchecker's
code, you must update this URL to reflect your modifications.

If you're distributing botolimitchecker with modifications or as part of your own software (as opposed to simply a
requirement that gets installed with pip), please read the license and ensure that you comply with its terms.

If you are running botolimitchecker as part of a hosted service that users somehow interact with, please
ensure that the source code URL is visible in the output given to users.
