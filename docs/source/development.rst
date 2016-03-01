.. _development:

Development
===========

Any and all contributions to awslimitchecker are welcome. Guidelines for submitting
code contributions in the form of pull requests on `GitHub <https://github.com/jantman/awslimitchecker>`_
can be found below. For guidelines on submitting bug reports or feature requests,
please see the :ref:`Getting Help <getting_help>` documentation.
For any contributions that don't fall into the above categories, please open an issue
for further assistance.

.. _development.pull_requests:

Pull Requests
-------------

.. NOTE: be sure to update .github/PULL_REQUEST_TEMPLATE.md when changing this

Please cut all pull requests against the "develop" branch. I'll do my best to merge them as
quickly as possible. If they pass all unit tests and have 100% coverage, it'll certainly be
easier. I work on this project only in my personal time, so I can't always get things merged
as quickly as I'd like. That being said, I'm committed to doing my best, and please call me
out on it if you feel like I'm not.

.. _development.pull_request_guidelines:

Pull Request Guidelines
+++++++++++++++++++++++

* Code should conform to the :ref:`Guidelines <development.guidelines>` below.
* If you have difficulty writing tests for the code, feel free to ask for help or
  submit the PR without tests. This will increase the amount of time it takes to
  get merged, but I'd rather write tests for your code than write all the code myself.
* If you make changes to the ``versioncheck`` code, be sure to locally run the
  ``-versioncheck`` tox tests.
* You've rebuilt the documentation using ``tox -e docs``

.. _development.installing:

Installing for Development
--------------------------

To setup awslimitchecker for development:

1. Fork the `awslimitchecker <https://github.com/jantman/awslimitchecker>`_ repository on GitHub

2. Create a ``virtualenv`` to run the code in:

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

.. NOTE: be sure to update .github/PULL_REQUEST_TEMPLATE.md when changing this

* pep8 compliant with some exceptions (see pytest.ini)
* 100% test coverage with pytest (with valid tests)
* Complete, correctly-formatted documentation for all classes, functions and methods.
* Connections to the AWS services should only be made by the class's
  :py:meth:`~awslimitchecker.connectable.Connectable.connect` and
  :py:meth:`~awslimitchecker.connectable.Connectable.connect_resource` methods,
  inherited from the :py:class:`~awslimitchecker.connectable.Connectable`
  mixin.
* All modules should have (and use) module-level loggers.
* See the section on the AGPL license below.
* **Commit messages** should be meaningful, and reference the Issue number
  if you're working on a GitHub issue (i.e. "issue #x - <message>"). Please
  refrain from using the "fixes #x" notation unless you are *sure* that the
  the issue is fixed in that commit.
* Unlike many F/OSS projects on GitHub, there is **no reason to squash your commits**;
  this just loses valuable history and insight into the development process,
  which could prove valuable if a bug is introduced by your work. Until GitHub
  `fixes this <https://github.com/isaacs/github/issues/406>`_, we'll live with
  a potentially messy git log in order to keep the history.

.. _development.adding_checks:

Adding New Limits and Checks to Existing Services
-------------------------------------------------

First, note that all calls to boto3 client ("low-level") methods that return a dict response that can
include 'NextToken' or another pagination marker, should be called through
:py:func:`~awslimitchecker.utils.paginate_dict` with the appropriate parameters.

1. Add a new :py:class:`~.AwsLimit` instance to the return value of the
   Service class's :py:meth:`~._AwsService.get_limits` method.
2. In the Service class's :py:meth:`~._AwsService.find_usage` method (or a method
   called by that, in the case of large or complex services), get the usage information
   via ``self.conn`` and/or ``self.resource_conn`` and pass it to the appropriate AwsLimit object via its
   :py:meth:`~.AwsLimit._add_current_usage` method. For anything more than trivial
   services (those with only 2-3 limits), ``find_usage()`` should be broken into
   multiple methods, generally one per AWS API call.
3. If the service has an API call that retrieves current limit values, and its results
   include your new limit, ensure that this value is updated in the limit via its
   :py:meth:`~.AwsLimit._set_api_limit` method. This should be done in the Service
   class's ``_update_limits_from_api()`` method.
4. Ensure complete test coverage for the above.

.. _development.adding_services:

Adding New Services
-------------------

All Services are sublcasses of :py:class:`~awslimitchecker.services.base._AwsService`
using the :py:mod:`abc` module.

First, note that all calls to boto3 client ("low-level") methods that return a dict response that can
include 'NextToken' or another pagination marker, should be called through
:py:func:`~awslimitchecker.utils.paginate_dict` with the appropriate parameters.

1. The new service name should be in CamelCase, preferably one word (if not one word, it should be underscore-separated).
   In ``awslimitchecker/services``, use the ``addservice`` script; this will create a templated service class in the
   current directory, and create a templated (but far from complete) unit test file in ``awslimitchecker/tests/services``:

.. code-block:: bash

   ./addservice ServiceName

2. Find all "TODO" comments in the newly-created files; these have instructions on things to change for new services.
   Add yourself to the Authors section in the header if desired.
3. Add an import line for the new service in ``awslimitchecker/services/__init__.py``.
4. Be sure to set the class's ``api_name`` attribute to the correct name of the
   AWS service API (i.e. the parameter passed to `boto3.client <https://boto3.readthedocs.org/en/latest/reference/core/boto3.html#boto3.client>`_). This string can
   typically be found at the top of the Service page in the `boto3 docs <http://boto3.readthedocs.org/en/latest/reference/services/index.html>`_.
5. Write at least high-level tests; TDD is greatly preferred.
6. Implement all abstract methods from :py:class:`~awslimitchecker.services.base._AwsService` and any other methods you need;
   small, easily-testable methods are preferred. Ensure all methods have full documentation. For simple services, you need only
   to search for "TODO" in the new service class you created (#1). See :ref:`Adding New Limits <development.adding_checks>` for further information.
7. If your service has an API action to retrieve limit/quota information (i.e. ``DescribeAccountAttributes`` for EC2 and RDS), ensure
   that the service class has an ``_update_limits_from_api()`` method which makes this API call and updates each relevant AwsLimit
   via its :py:meth:`~.AwsLimit._set_api_limit` method.
8. Test your code; 100% test coverage is expected, and mocks should be using ``autospec`` or ``spec_set``.
9. Ensure the :py:meth:`~awslimitchecker.services.base._AwsService.required_iam_permissions` method of your new class
   returns a list of all IAM permissions required for it to work.
10. Run all tox jobs, or at least one python version, docs and coverage.
11. Commit the updated documentation to the repository.
12. As there is no programmatic way to validate IAM policies, once you are done writing your service, grab the
    output of ``awslimitchecker --iam-policy``, login to your AWS account, and navigate to the IAM page.
    Click through to create a new policy, paste the output of the ``--iam-policy`` command, and click the
    "Validate Policy" button. Correct any errors that occur; for more information, see the AWS IAM docs on
    `Using Policy Validator <http://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_policy-validator.html>`_.
    It would also be a good idea to run any policy changes through the
    `Policy Simulator <http://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_testing-policies.html>`_.
13. Submit your pull request.

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

Testing is done via `pytest <http://pytest.org/latest/>`_, driven by `tox <https://tox.readthedocs.org/>`_.

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

Integration tests are automatically run in TravisCI for all **non-pull request**
branches. You can run them manually from your local machine using:

.. code-block:: console

    tox -r -e integration,integration3

These tests simply run ``awslimitchecker``'s CLI script for both usage and limits, for all services and each service individually. Note that this covers a very small amount of the code, as the account that I use for integration tests has virtually no resources in it.

If integration tests fail, check the required IAM permissions. The IAM user that I use for Travis integration tests has a manually-maintained IAM policy.

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
  awslimitchecker via Python's packaging system (i.e. with ``pip``), its current version and source will be automatically detected. This
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

.. _development.issues_and_prs:

Handling Issues and PRs
-----------------------

.. NOTE: be sure to update .github/PULL_REQUEST_TEMPLATE.md when changing this

All PRs and new work should be based off of the ``develop`` branch.

PRs can be merged if they look good, and ``CHANGES.rst`` updated after the merge.

For issues:

1. Cut a ``issues/number`` branch off of ``develop``.
2. Work the issue, come up with a fix. Commit early and often, and mention "issue #x - <message>" in your commit messages.
3. When you believe you have a working fix, build docs (``tox -e docs``) and push to origin. Ensure all Travis tests pass.
4. Ensure that coverage has increased or stayed the same.
5. Update ``CHANGES.rst`` for the fix; commit this with a message like "fixes #x - <message>" and push to origin.
6. Open a new pull request **against the develop branch** for this change; once all tests pass, merge it to develop.
7. Assign the "unreleased fix" label to the issue. It should be closed automatically when develop is merged to master for
   a release, but this lets us track which issues have unreleased fixes.

.. _development.release_checklist:

Release Checklist
-----------------

1. Open an issue for the release; cut a branch off ``develop`` for that issue.
2. Build docs (``tox -e docs``) and ensure they're current; commit any changes.
3. Ensure that Travis tests are passing in all environments. If there were any changes to ``awslimitchecker.versioncheck``,
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

   * Make sure your ~/.pypirc file is correct (a repo called ``test`` for https://testpypi.python.org/pypi).
   * ``rm -Rf dist``
   * ``python setup.py register -r https://testpypi.python.org/pypi``
   * ``python setup.py sdist bdist_wheel``
   * ``twine upload -r test dist/*``
   * Check that the README renders at https://testpypi.python.org/pypi/awslimitchecker

10. Create a pull request for the release to be merge into master. Upon successful Travis build, merge it.
11. Tag the release in Git, push tag to GitHub:

   * tag the release. for now the message is quite simple: ``git tag -a X.Y.Z -m 'X.Y.Z released YYYY-MM-DD'``
   * push the tag to GitHub: ``git push origin X.Y.Z``

12. Upload package to live pypi:

    * ``twine upload dist/*``

13. make sure any GH issues fixed in the release were closed.
14. merge master back into develop
15. Log in to ReadTheDocs and enable build of the tag.
16. Blog, tweet, etc. about the new version.
