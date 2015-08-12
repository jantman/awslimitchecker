.. _development:

Development
===========

.. _development.pull_requests:

Pull Requests
-------------

Please cut all pull requests against the "develop" branch. I'll do my best to merge them as
quickly as possible. If they pass all unit tests and have 100% coverage, it'll certainly be
easier. I work on this project only in my personal time, so I can't always get things merged
as quickly as I'd like. That being said, I'm committed to doing my best, and please call me
out on it if you feel like I'm not.

.. _development.installing:

Installing for Development
--------------------------

To setup awslimitchecker for development:

1. Fork the `awslimitchecker <https://github.com/jantman/awslimitchecker>`_ repository on GitHub

2. Create a `virtualenv` to run the code in:

.. code-block:: bash

    $ virtualenv awslimitchecker
    $ cd awslimitchecker
    $ source bin/activate

3. Install your fork in the virtualenv as an editable git clone

.. code-block:: bash

    $ pip install -e git+git@github.com:YOUR_NAME/awslimitchecker.git#egg=awslimitchecker
    $ cd src/awslimitchecker

4. Check out a new git branch. If you're working on a GitHub issue you opened, your
   branch should be called "issues/N" where N is the issue number.


.. _development.guidelines:

Guidelines
----------

* pep8 compliant with some exceptions (see pytest.ini)
* 100% test coverage with pytest (with valid tests)
* each :py:class:`~awslimitchecker.services.base._AwsService` subclass
  should only connect to boto once, and should save the connection as ``self.conn``.
  They *must not* connect in the class constructor.
* All modules should have (and use) module-level loggers.
* See the section on the AGPL license below.

.. _development.adding_checks:

Adding New Limits and Checks to Existing Services
-------------------------------------------------

1. Add a new :py:class:`~.AwsLimit` instance to the return value of the
   Service class's :py:meth:`~._AwsService.get_limits` method.
2. In the Service class's :py:meth:`~._AwsService.find_usage` method (or a method
   called by that, in the case of large or complex services), get the usage information
   via `boto` and pass it to the appropriate AwsLimit object via its
   :py:meth:`~.AwsLimit._add_current_usage` method. For anything more than trivial
   services (those with only 2-3 limits), ``find_usage()`` should be broken into
   multiple methods, generally one per AWS API call.
3. Ensure complete test coverage for the above.

.. _development.adding_services:

Adding New Services
-------------------

All Services are sublcasses of :py:class:`~awslimitchecker.services.base._AwsService`
using the :py:mod:`abc` module.

1. The new service name should be in CamelCase, preferably one word (if not one word, it should be underscore-separated).
   In ``awslimitchecker/services``, use the ``addservice`` script; this will create a templated service class in the
   current directory, and create a templated (but far from complete) unit test file in ``awslimitchecker/tests/services``:

.. code-block:: bash

   ./addservice ServiceName

2. Find all "TODO" comments in the newly-created files; these have instructions on things to change for new services.
   Add yourself to the Authors section in the header if desired.
3. Add an import line for the new service in ``awslimitchecker/services/__init__.py``.
4. Write at least high-level tests; TDD is greatly preferred.
5. Implement all abstract methods from :py:class:`~awslimitchecker.services.base._AwsService` and any other methods you need;
   small, easily-testable methods are preferred. Ensure all methods have full documentation. For simple services, you need only
   to search for "TODO" in the new service class you created (#1). See :ref:`Adding New Limits <development.adding_checks>` for further information.
6. Test your code; 100% test coverage is expected, and mocks should be using ``autospec`` or ``spec_set``.
7. Ensure the :py:meth:`~awslimitchecker.services.base._AwsService.required_iam_permissions` method of your new class
   returns a list of all IAM permissions required for it to work.
8. Write integration tests. (currently not implemented; see `issue #21 <https://github.com/jantman/awslimitchecker/issues/21>`_)
9. Run all tox jobs, or at least one python version, docs and coverage.
10. Commit the updated documentation to the repository.
11. As there is no programmatic way to validate IAM policies, once you are done writing your service, grab the
    output of ``awslimitchecker --iam-policy``, login to your AWS account, and navigate to the IAM page.
    Click through to create a new policy, paste the output of the ``--iam-policy`` command, and click the
    "Validate Policy" button. Correct any errors that occur; for more information, see the AWS IAM docs on
    `Using Policy Validator <http://docs.aws.amazon.com/IAM/latest/UserGuide/policies_policy-validator.html>`_.
    It would also be a good idea to run any policy changes through the
    `Policy Simulator <https://policysim.aws.amazon.com/>`_.
12. Submit your pull request.

.. _development.adding_ta:

Trusted Advisor Checks
----------------------

So long as the ``Service`` and ``Limit`` name strings returned by the Trusted Advisor (Support) API exactly match
how they are set on the corresponding :py:class:`~._AwsService` and :py:class:`~.AwsLimit` objects, no code changes
are needed to support new limit checks from TA.

For further information, see :ref:`Internals / Trusted Advisor <internals.trusted_advisor>`.

.. _development.tests:

Unit Testing
------------

Testing is done via `pytest <http://pytest.org/latest/>`_, driven by `tox <http://tox.testrun.org/>`_.

* testing is as simple as:

  * ``pip install tox``
  * ``tox``

* If you want to see code coverage: ``tox -e cov``

  * this produces two coverage reports - a summary on STDOUT and a full report in the ``htmlcov/`` directory

* If you want to pass additional arguments to pytest, add them to the tox command line after "--". i.e., for verbose pytext output on py27 tests: ``tox -e py27 -- -v``

Note that while boto currently doesn't have python3 support, we still run tests against py3 to ensure that this package
is ready for it when boto is.


.. _development.integration_tests:

Integration Testing
-------------------

currently not implemented; see `issue #21 <https://github.com/jantman/awslimitchecker/issues/21>`_

.. _development.docs:

Building Docs
-------------
Much like the test suite, documentation is build using tox:

.. code-block:: bash

    $ tox -e docs

Output will be in the ``docs/build/html`` directory under the project root.

.. _development.agpl:

AGPL License
------------

awslimitchecker is licensed under the `GNU Affero General Public License, version 3 or later <http://www.gnu.org/licenses/agpl.html>`_.

Pursuant to Sections `5(b) <http://www.gnu.org/licenses/agpl-3.0.en.html#section5>`_
and `13 <http://www.gnu.org/licenses/agpl-3.0.en.html#section13>`_ of the license,
all users of awslimitchecker - including those interacting with it remotely over
a network - have a right to obtain the exact, unmodified running source code. We
have done as much as possible to make this transparent to developers, with no additional
work needed. See the guidelines below for information.

* If you're simply *running* awslimitchecker via the command line, there's nothing to worry about;
  just use it like any other software.
* If you're using awslimitchecker in your own software in a way that allows users to interact with it over the network (i.e. in your
  deployment or monitoring systems), but not modifying it, you also don't need to do anything special; awslimitchecker will log a
  WARNING-level message indicating where the source code of the currently-running version can be obtained. So long as you've installed
  awslimitchecker via Python's packaging system (i.e. with `pip`), its current version and source will be automatically detected. This
  suffices for the AGPL source code offer provision, so long as it's displayed to users and the currently-running source is unmodified.
* If you wish to modify the source code of awslimitchecker, you need to do is ensure that :py:meth:`~awslimitchecker.version._get_version_info`
  always returns correct and accutate information (a publicly-accessible URL to the exact version of the running source code, and a version number).
  If you install your modified version directly from an editable (i.e. ``pip install -e``), publicly-accessible Git repository, and ensure
  that changes are available in the repository before they are present in the code running for your users, this should be automatically
  detected by awslimitchecker and the correct URL provided. It is strongly recommended that any such repository is a fork of the
  project's original GitHub repository. It is solely your responsibility to ensure that the URL and version information presented
  to users is accurate and reflects source code identical to what is running.
* If you're distributing awslimitchecker with modifications or as part of your own software (as opposed to simply an
  editable requirement that gets installed with pip), please read the license and ensure that you comply with its terms.
* If you are running awslimitchecker as part of a hosted service that users somehow interact with, please
  ensure that the source code URL and version is correct and visible in the output given to users.

.. _development.release_checklist:

Release Checklist
-----------------

1. Open an issue for the release; cut a branch off ``develop`` for that issue.
2. Build docs (``tox -e docs``) and ensure they're current; commit any changes.
3. Ensure that Travis tests passing in all environments. If there were any changes to ``awslimitchecker.versioncheck``,
   manually run the ``-versioncheck`` tox environments (these are problematic in Travis and with PRs).
4. Ensure that test coverage is no less than the last release (ideally, 100%).
5. Create or update an actual IAM user with the policy from ``awslimitchecker --iam-policy``;
   run the command line wrapper and ensure that the policy works and contains all needed permissions.
6. Build docs for the branch (locally) and ensure they look correct.
7. Increment the version number in awslimitchecker/version.py and add version and release date to CHANGES.rst.
   Ensure that there are CHANGES.rst entries for all major changes since the last release. Mention the issue
   in the commit for this, and push to GitHub.
8. Confirm that README.rst renders correctly on GitHub.
9. Upload package to testpypi, confirm that README.rst renders correctly.

   * Make sure your ~/.pypirc file is correct
   * ``python setup.py register -r https://testpypi.python.org/pypi``
   * ``python setup.py sdist upload -r https://testpypi.python.org/pypi``
   * Check that the README renders at https://testpypi.python.org/pypi/awslimitchecker

10. Create a pull request for the release to be merge into master. Upon successful Travis build, merge it.
11. Tag the release in Git, push tag to GitHub:

   * tag the release. for now the message is quite simple: ``git tag -a vX.Y.Z -m 'X.Y.Z released YYYY-MM-DD'``
   * push the tag to GitHub: ``git push origin vX.Y.Z``

12. Upload package to live pypi:

    * ``python setup.py sdist upload``

13. make sure any GH issues fixed in the release were closed.
14. merge master back into develop
15. Blog, tweet, etc. about the new version.
