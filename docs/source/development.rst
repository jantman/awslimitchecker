.. _development:

Development
============


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
-----------

* pep8 compliant with some exceptions (see pytest.ini)
* 100% test coverage with pytest (with valid tests)
* each :py:class:`~awslimitchecker.services.base._AwsService` subclass
  should only connect to boto once, and should save the connection as ``self.conn``.
  They *must not* connect in the class constructor.
* All modules should have (and use) module-level loggers.
* See the section on the AGPL license below.

.. _development.adding_checks:

Adding New Limits and Checks to Existing Services
--------------------------------------------------

1. Add a new :py:class:`~.AwsLimit` instance to the return value of the
   Service class's :py:meth:`~._AwsService.get_limits` method.
2. In the Service class's :py:meth:`~._AwsService.find_usage` method (or a method
   called by that, in the case of large or complex services), get the usage information
   via `boto` and pass it to the appropriate AwsLimit object via its
   :py:meth:`~.AwsLimit._add_current_usage` method.
3. Ensure complete test coverage for the above.

.. _development.adding_services:

Adding New Services
--------------------

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
   to search for "TODO" in the new service class you created (#1).
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

Adding Trusted Advisor Checks
------------------------------

Currently not implemented; see `issue #14 <https://github.com/jantman/awslimitchecker/issues/14>`_

.. _development.tests:

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


.. _development.integration_tests:

Integration Testing
--------------------

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
-------------

awslimitchecker is licensed under the `GNU Affero General Public License, version 3 or later <http://www.gnu.org/licenses/agpl.html>`_.

* If you're simply *running* awslimitchecker via the command line, there's nothing to worry about; just use it like any other software.
* If you're using awslimitchecker in your own software in a way that allows users to interact with it over the network (i.e. in your
  deployment or monitoring systems), but not modifying it, you also don't need to do anything special; awslimitchecker will log a
  WARNING-level message indicating where the source code of the currently-running version can be obtained from. This suffices for the
  AGPL source code offer provision, so long as it's displayed to users and the currently-running source is unmodified.
* If you wish to modify the source code of awslimitchecker, all you need to do is ensure that :py:meth:`~awslimitchecker.version._get_project_url`
  returns a publicly-accessible URL to the exact version of the running source code. A `future version <https://github.com/jantman/awslimitchecker/issues/28>`_
  of awslimitchecker will automatically provide the correct URL if you install it as an editable (``pip install -e``)
  fork of the original GitHub repository.
* If you're distributing awslimitchecker with modifications or as part of your own software (as opposed to simply a
  requirement that gets installed with pip), please read the license and ensure that you comply with its terms.
* If you are running awslimitchecker as part of a hosted service that users somehow interact with, please
  ensure that the source code URL is visible in the output given to users.

.. _development.release_checklist:

Release Checklist
-----------------

1. Open an issue for the release; cut a branch off ``develop`` for that issue.
2. Build docs (``tox -e docs``) and ensure they're current; commit any changes.
3. Confirm that there are CHANGES.rst entries for all major changes.
4. Ensure that Travis tests passing in all environments.
5. Ensure that test coverage is no less than the last release (ideally, 100%).
6. Build docs for the branch (locally) and ensure they look correct.
7. Increment the version number in awslimitchecker/version.py and add version and release date to CHANGES.rst, then push to GitHub.
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
