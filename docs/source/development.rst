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

* All pull requests should be made against the ``develop`` branch, NOT master.
* If you have not contributed to the project before, all pull requests must include
  a statement that your contribution is being made under the same license as the
  awslimitchecker project (or any subsequent version of that license if adopted by
  awslimitchecker), may perpetually be included in and distributed with awslimitchecker,
  and that you have the legal power to agree to these terms.
* Code should conform to the :ref:`Guidelines <development.guidelines>` below.
* If you have difficulty writing tests for the code, feel free to ask for help or
  submit the PR without tests. This will increase the amount of time it takes to
  get merged, but I'd rather write tests for your code than write all the code myself.
* You've rebuilt the documentation using ``tox -e docs``

.. _development.installing:

Installing for Development
--------------------------

To setup awslimitchecker for development:

1. Fork the `awslimitchecker <https://github.com/jantman/awslimitchecker>`_ repository on GitHub

2. Create a ``virtualenv`` (using Python 3.5 or later) to run the code in:

.. code-block:: bash

    $ virtualenv awslimitchecker
    $ cd awslimitchecker
    $ source bin/activate

3. Install your fork in the virtualenv as an editable git clone and install development dependencies:

.. code-block:: bash

    $ pip install -e git+git@github.com:YOUR_NAME/awslimitchecker.git#egg=awslimitchecker
    $ cd src/awslimitchecker
    $ pip install -r dev/requirements_dev.txt

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

.. _development.instance_types:

Adding New EC2 Instance Types
-----------------------------

1. Run ``dev/missing_instance_types.py`` to find all EC2 Instance types listed in
   the EC2 Pricing API that aren't present in awslimitchecker and output a list of them.
2. In ``services/ec2.py`` update the constants in :py:meth:`~._Ec2Service._instance_types` accordingly.
3. Check the `EC2 Instance Type limits page <https://aws.amazon.com/ec2/faqs/>`__
   for any new types that have non-default limits, and update :py:meth:`~._Ec2Service._get_limits_instances_nonvcpu` accordingly.
4. Update ``tests/services/test_ec2.py`` as needed.

.. _development.adding_checks:

Adding New Limits and Checks to Existing Services
-------------------------------------------------

First, note that all calls to boto3 client ("low-level") methods that return a dict response that can
include 'NextToken' or another pagination marker, should be called through
:py:func:`~awslimitchecker.utils.paginate_dict` with the appropriate parameters
if the boto3 client can't paginate the call itself.

1. Add a new :py:class:`~.AwsLimit` instance to the return value of the
   Service class's :py:meth:`~._AwsService.get_limits` method. If Trusted Advisor
   returns data for this limit, be sure the service and limit names match those
   returned by Trusted Advisor.
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
4. If Service Quotas returns data for this limit, be sure that the parent
   :py:class:`~._AwsService` class has its :py:attr:`~._AwsService.quotas_service_code`
   attribute set appropriately and specify the ``quotas_name`` argument to the
   :py:class:`~.AwsLimit` constructor if the quota name is different from the limit name.
5. Ensure complete test coverage for the above.

In cases where the AWS service API has a different name than what is reported
by Trusted Advisor, or legacy cases where Trusted Advisor support is retroactively
added to a limit already in awslimitchecker, you must pass the
``ta_service_name`` and ``ta_limit_name`` parameters to the :py:class:`~.AwsLimit`
constructor, specifying the string values that are returned by Trusted Advisor.

**Note on services with per-resource limits:** Some AWS services, such as Route53,
set limits on each individual resource (i.e. each Hosted Zone, for Route53) instead
of globally for all resources in a region or account. When this is done, the per-resource
limit should be provided as the ``maximum`` argument to the :py:class:`~.AwsLimitUsage`
class; :py:class:`~.AwsLimit` will then properly determine warnings/criticals for the
limit. For further information, see the `5.0.0 release notes <https://github.com/jantman/awslimitchecker/releases/tag/5.0.0>`_
and `PR #345 <https://github.com/jantman/awslimitchecker/pull/345>`_ where this was initially implemented.

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
8. If the Service Quotas service returns information on limits for your service, be sure you set the :py:attr:`~._AwsService.quotas_service_code`
   attribute appropriately, and also pass the ``quota_name`` keyword argument to the constructor of any :py:class:`~.AwsLimit` classes
   which have information available via Service Quotas.
9. Test your code; 100% test coverage is expected, and mocks should be using ``autospec`` or ``spec_set``.
10. Ensure the :py:meth:`~awslimitchecker.services.base._AwsService.required_iam_permissions` method of your new class
    returns a list of all IAM permissions required for it to work.
11. Run all tox jobs, or at least one python version, docs and coverage.
12. Commit the updated documentation to the repository.
13. As there is no programmatic way to validate IAM policies, once you are done writing your service, grab the
    output of ``awslimitchecker --iam-policy``, login to your AWS account, and navigate to the IAM page.
    Click through to create a new policy, paste the output of the ``--iam-policy`` command, and click the
    "Validate Policy" button. Correct any errors that occur; for more information, see the AWS IAM docs on
    `Using Policy Validator <http://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_policy-validator.html>`_.
    It would also be a good idea to run any policy changes through the
    `Policy Simulator <http://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_testing-policies.html>`_.
14. Submit your pull request.

.. _development.adding_ta:

Trusted Advisor Checks
----------------------

.. attention::
   Trusted Advisor support in awslimitchecker is deprecated outside of the China and GovCloud regions, and now defaults to disabled/skipped in standard AWS, as the information available from TA can now be retrieved faster and more accurately via other means. See :ref:`changelog.10_0_0` for further information.

So long as the ``Service`` and ``Limit`` name strings returned by the Trusted Advisor (Support) API exactly match
how they are set on the corresponding :py:class:`~._AwsService` and :py:class:`~.AwsLimit` objects, no code changes
are needed to support new limit checks from TA.

For further information, see :ref:`Internals / Trusted Advisor <internals.trusted_advisor>`.

.. _development.metrics_providers:

Adding Metrics Providers
------------------------

Metrics providers are subclasses of :py:class:`~.MetricsProvider` that take key/value
configuration items via constructor keyword arguments and implement a
:py:meth:`~.MetricsProvider.flush` method to send all metrics to the configured provider.
It is probably easiest to look at the other existing providers for an example of how to
implement a new one, but there are a few important things to keep in mind:

* All configuration must be able to be passed as keyword arguments to the class
  constructor (which come from ``--metrics-config=key=value`` CLI arguments).
  It is recommended that any secrets/API keys also be able to be set via
  environment variables, but the CLI arguments should have precedence.
* All dependency imports must be made inside the constructor, not at the module
  level.
* If the provider requires additional dependencies, they should be added as
  extras but installed in the Docker image.
* The constructor should do as much validation (i.e. authentication test) as
  possible.
* Metrics provider classes should be in a module with the same name.

.. _development.alert_providers:

Adding Alert Providers
------------------------

Alert providers are subclasses of :py:class:`~.AlertProvider` that take key/value
configuration items via constructor keyword arguments and implement three methods
for sending alerts depending on the type of situation: :py:meth:`~.AlertProvider.on_warning`
for runs that resulted in warning thresholds crossed, :py:meth:`~.AlertProvider.on_critical`
for runs that resulted in critical thresholds crossed or raised an exception, or
:py:meth:`~.AlertProvider.on_success` for successful runs with no thresholds crossed
(mainly for automatically resolving incidents, when supported).
It is probably easiest to look at the other existing providers for an example of how to
implement a new one, but there are a few important things to keep in mind:

* All configuration must be able to be passed as keyword arguments to the class
  constructor (which come from ``--alert-config=key=value`` CLI arguments).
  It is recommended that any secrets/API keys also be able to be set via
  environment variables, but the CLI arguments should have precedence.
* All dependency imports must be made inside the constructor, not at the module
  level.
* If the provider requires additional dependencies, they should be added as
  extras but installed in the Docker image.
* The constructor should do as much validation (i.e. authentication test) as
  possible.
* Alert provider classes should be in a module with the same name.

.. _development.tests:

Unit Testing
------------

Testing is done via `pytest <http://pytest.org/en/latest/>`_, driven by `tox <https://tox.readthedocs.org/>`_.

* testing is as simple as:

  * ``pip install tox==2.7.0``
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

If integration tests fail, check the required IAM permissions. The IAM user for Travis integration tests is configured via Terraform, which must be re-run after policy changes.

.. _development.docs:

Building Docs
-------------
Much like the test suite, documentation is build using tox:

.. code-block:: bash

    $ tox -e docs

Output will be in the ``docs/build/html`` directory under the project root.

.. _development.docker:

Building the Docker Image
-------------------------

The Docker image is normally built by TravisCI (for testing) and Docker Hub
Automated Builds (for the release). To build locally, run ``tox -e docker``.

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
  always returns correct and accurate information (a publicly-accessible URL to the exact version of the running source code, and a version number).
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

.. _development.versioning_policy:

Versioning Policy
-----------------

As of version 1.0.0, awslimitchecker strives to follow `semver 2.0.0 <http://semver.org/>`_ for versioning, with some specific clarifications:

* Major version bumps (backwards-incompatible changes):

  * Any additional required IAM permissions, beyond the minimum policy from the last major version.
  * Renaming (any change to the case-sensitive strings) any existing services or limits.
  * Changing the signatures or argument types of any public methods.
  * Any changes to direct dependencies or direct dependency version requirements.
  * Any changes that would cause the documented usage examples (Python or CLI) to cease functioning.

* Minor version bumps (backwards-compatible feature additions and changes):

  * Adding new limits or services that don't require any IAM policy changes.
  * New functionality that doesn't change existing APIs or CLI arguments.

* Patch version bumps:

  * Bug fixes
  * Documentation, development/support tooling, or anything else that isn't user-executed code.

This means that after 1.0.0, major version numbers will likely increase rather quickly.

.. _development.release_checklist:

Release Checklist
-----------------

To perform a release, run ``dev/release.py``.
