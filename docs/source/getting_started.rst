.. _getting_started:

Getting Started
===============

.. _getting_started.features:

What It Does
------------

- Check current AWS resource usage against AWS Service Limits
- Show and inspect current usage
- Override default Service Limits (for accounts with increased limits)
- Compare current usage to limits; return information about limits that
  exceed thresholds, and (CLI wrapper) exit non-0 if thresholds are exceeded
- Define custom thresholds per-limit
- Where possible, pull current limits from Trusted Advisor API
- Supports explicitly setting the AWS region
- Supports using `STS <http://docs.aws.amazon.com/STS/latest/APIReference/Welcome.html>`_
  to assume roles in other accounts, including using ``external_id``.
- Optionally refresh Trusted Advisor "Service Limits" check before polling
  Trusted Advisor data, and optionally wait for the refresh to complete (up to
  an optional maximum time limit). See
  :ref:`Getting Started - Trusted Advisor <getting_started.trusted_advisor>`
  for more information.
- Optionally send current usage and limit metrics to a :ref:`metrics store <cli_usage.metrics>` such as Datadog.
- Optionally send warning/critical alerts to an :ref:`alert provider <cli_usage.alerts>`, such as PagerDuty.

.. _getting_started.nomenclature:

Nomenclature
------------

Service
   An AWS Service or Product, such as EC2, VPC, RDS or ElastiCache. More specifically, Services in AwsLimitChecker correspond to
   distinct APIs for `AWS Services <http://aws.amazon.com/documentation/>`_.

Limit
   An AWS-imposed maximum usage for a certain resource type in AWS. See `AWS Service Limits <http://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html>`_.
   Limits are generally either account-wide or per-region. They have AWS global default values, but can be increased by AWS Support. "Limit" is also the term used
   within this documentation to describe :py:class:`~.AwsLimit` objects, which describe a specific AWS Limit within this program.

Usage
   "Usage" refers to your current usage of a specific resource that has a limit. Usage values/amounts (some integer or floating point number, such as number of VPCs
   or GB of IOPS-provisioned storage) are represented by instances of the :py:class:`~.AwsLimitUsage` class. Limits that are measured as a subset of some "parent"
   resource, such as "Subnets per VPC" or "Read Replicas per Master" have their usage tracked per parent resource, so you can easily determine which ones are problematic.

Threshold
   The point at which AwsLimitChecker will consider the current usage for a limit to be problematic. Global thresholds default to usage >= 80% of limit for "warning" severity,
   and usage >= 99% of limit for "critical" severity. Limits which have reached or exceeded their threshold will be reported separately for warning and critical (we generally
   consider "warning" to be something that will require human intervention in the near future, and "critical" something that is an immediate problem, i.e. should block
   automated processes). The ``awslimitchecker`` command line wrapper can override the default global thresholds. The :py:class:`~.AwsLimitChecker` class can both override
   global percentage thresholds, as well as specify per-limit thresholds as a percentage, a fixed usage value, or both. For more information on overriding thresholds, see
   :ref:`Python Usage / Setting a Threshold Override <python_usage.threshold_overrides>` as well as the documentation for :py:meth:`.AwsLimitChecker.check_thresholds`
   and :py:meth:`.AwsLimitChecker.set_threshold_override`.

.. _getting_started.requirements:

Requirements
------------

**Either Docker in order to run via the** :ref:`docker image <docker>`, **or:**

* Python 2.7 or 3.4+. Python 2.6 and 3.3 are no longer supported.
* Python `VirtualEnv <http://www.virtualenv.org/>`_ and ``pip`` (recommended installation method; your OS/distribution should have packages for these)
* `boto3 <http://boto3.readthedocs.org/>`_ >= 1.4.6 and its dependency `botocore <https://botocore.readthedocs.io/en/latest/>`_ >= 1.6.0.

.. _getting_started.installing:

Installing
----------

awslimitchecker now distributes an official Docker image, which removes the need
to install locally. If you wish to run via this method, please see :ref:`docker`.

If not running via Docker, it's recommended that you install into a virtual environment
(virtualenv / venv). See the `virtualenv usage documentation <http://www.virtualenv.org/>`_
for more details, but the gist is as follows (the virtualenv name, "limitchecker" here,
can be whatever you want):

.. code-block:: bash

    virtualenv limitchecker
    source limitchecker/bin/activate
    pip install awslimitchecker

Version Specification
+++++++++++++++++++++

If you're using awslimitchecker in automated tooling that recreates the virtualenv
(such as Jenkins or cron jobs, etc) you'll probably want to install a specific version
so that the job doesn't unexpectedly break. It's recommended that you pin your installation
to a ``major`` version. According to awslimitchecker's :ref:`versioning policy <development.versioning_policy>`,
this should ensure that you get the latest awslimitchecker version that's compatible with
your IAM policy and dependencies and has no backwards-incompatible API changes.

.. _getting_started.credentials:

Credentials
-----------

Aside from STS, awslimitchecker does nothing with AWS credentials, it leaves that to boto itself.
You must either have your credentials configured in one of boto3's supported config
files or set as environment variables. If your credentials are in the cross-SDK
credentials file (``~/.aws/credentials``) under a named profile section, you can
use credentials from that profile by specifying the ``-P`` / ``--profile`` command
lint option. See
`boto3 config <http://boto3.readthedocs.org/en/latest/guide/configuration.html#guide-configuration>`_
and
`this project's documentation <http://awslimitchecker.readthedocs.org/en/latest/getting_started.html#credentials>`_
for further information.

**Please note** that version 0.3.0 of awslimitchecker moved from using ``boto`` as its AWS API client to using
``boto3``. This change is mostly transparent, but there is a minor change in how AWS credentials are handled. In
``boto``, if the ``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY`` environment variables were set, and the
region was not set explicitly via awslimitchecker, the AWS region would either be taken from the ``AWS_DEFAULT_REGION``
environment variable or would default to us-east-1, regardless of whether a configuration file (``~/.aws/credentials``
or ``~/.aws/config``) was present. With boto3, it appears that the default region from the configuration file will be
used if present, regardless of whether the credentials come from that file or from environment variables.

When using STS, you will need to specify the ``-r`` / ``--region`` option as well as the ``-A`` / ``--sts-account-id``
and ``-R`` / ``--sts-account-role`` options to specify the Account ID that you want to assume a role in, and the
name of the role you want to assume. If an external ID is required, you can specify it with ``-E`` / ``--external-id``.

In addition, when assuming a role STS, you can use a `MFA device <https://aws.amazon.com/iam/details/mfa/>`_. simply
specify the device's serial number with the ``-M`` / ``--mfa-serial-number`` option and a token generated by the device
with the ``-T`` / ``--mfa-token`` option. STS credentials will be cached for the lifetime of the program.

**Important Note on Session and Federation (Temporary) Credentials:** The temporary credentials granted by the AWS IAM
`GetFederationToken <http://docs.aws.amazon.com/STS/latest/APIReference/API_GetFederationToken.html>`_
and `GetSessionToken <http://docs.aws.amazon.com/STS/latest/APIReference/API_GetSessionToken.html>`_
API calls will throw errors when trying to access the IAM API (except for Session tokens, which will
work for IAM API calls only if an MFA token is used). Furthermore, Federation tokens cannot make use
of the STS AssumeRole functionality. If you attempt to use awslimitchecker with credentials generated
by these APIs (commonly used by organizations to hand out limited-lifetime credentials), you will likely
encounter errors when checking IAM limits. If this is acceptable, you can use these credentials by setting
the ``AWS_SESSION_TOKEN`` environment variable in addition to ``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY``,
or by otherwise configuring these credentials in a way that's supported by
`boto3 configuration <http://boto3.readthedocs.org/en/latest/guide/configuration.html#guide-configuration>`_.

.. _getting_started.regions:

Regions
-------

To specify the region that ``awslimitchecker`` connects to, use the ``-r`` / ``--region``
command line option. At this time awslimitchecker can only connect to one region at a time;
to check limits in multiple regions, simply run the script multiple times, once per region.

.. _getting_started.trusted_advisor:

Trusted Advisor
---------------

awslimitchecker supports retrieving your current service limits via the
`Trusted Advisor <https://aws.amazon.com/premiumsupport/trustedadvisor/>`_
`"Service Limits" performance check <https://aws.amazon.com/premiumsupport/trustedadvisor/best-practices/#Performance>`_
, for limits which Trusted Advisor tracks (currently a subset of what awslimitchecker
knows about). The results of this check may not be available via the API for all
accounts; as of December 2016, the Trusted Advisor documentation states that while
this check is available for all accounts, API access is only available to accounts
with Business- or Enterprise-level support plans. If your account does not have
Trusted Advisor access, the API call will result in a ``SubscriptionRequiredException``
and awslimitchecker will log a ``Cannot check TrustedAdvisor`` message at
warning level.

Trusted Advisor information is important to awslimitchecker, however, as it provides
the current service limit values for a number of limits that cannot be obtained
any other way. While you can completely disable Trusted Advisor polling via the
``--skip-ta`` command-line option, you will then be left with default service
limit values for many limits.

As of 0.7.0, awslimitchecker also supports programmatically refreshing the
"Service Limits" Trusted Advisor check, in order to get updated limit values. If
this is not done, the data provided by Trusted Advisor may not be updated unless
a human does so via the AWS Console. The refresh logic operates in one of three
modes, controlled by command-line options (these are also exposed in the Python
API; see the "Internals" link below):

* ``--ta-refresh-wait`` - The check will be refreshed and awslimitchecker will
  poll every 30 seconds waiting for the refresh to complete (or until
  ``ta_refresh_timeout`` seconds have elapsed).
* ``--ta-refresh-older INTEGER`` - This operates like the ``--ta-refresh-wait``
  option, but will only refresh the check if its current result data is at least
  ``INTEGER`` seconds old.
* ``--ta-refresh-trigger`` - The check will be refreshed and the program will
  continue on immediately, without waiting for the refresh to
  complete; this will almost certainly result in stale check results in the current
  run. However, this may be useful if you desire to keep ``awslimitchecker`` runs
  short, and run it on a regular schedule (i.e. if you run ``awslimitchecker``
  every 6 hours, and are OK with Trusted Advisor check data being 6 hours old).

Additionally, there is a ``--ta-refresh-timeout`` option. If this is set (to an integer),
refreshes of the check will time out after that number of seconds. If a timeout
occurs, a message will be logged at error level, but the program will continue
running (most likely using the old result data).

**Important:** It may take 30 to 60 *minutes* for the Service Limits check to
refresh on large accounts. Please be aware of this when enabling the refresh
options.

Using the check refresh options will require the ``trustedadvisor:RefreshCheck``
IAM permission.

See :ref:`Internals - Trusted Advisor <internals.trusted_advisor>` for technical
information on the implementation of Trusted Advisor polling.

.. _getting_started.permissions:

Required Permissions
--------------------

.. important::
   The required IAM policy output by awslimitchecker includes only the permissions required to check limits and usage. If you are loading :ref:`limit overrides <cli_usage.limit_overrides>` and/or :ref:`threshold overrides <cli_usage.threshold_overrides>` from S3, you will need to run awslimitchecker with additional permissions to access those objects.

You can view a sample IAM policy listing the permissions required for awslimitchecker to function properly
either via the CLI client:

.. code-block:: bash

    awslimitchecker --iam-policy

Or as a python dict:

.. code-block:: python

    from awslimitchecker.checker import AwsLimitChecker
    c = AwsLimitChecker()
    iam_policy = c.get_required_iam_policy()

You can also view the required permissions for the current version of awslimitchecker at :ref:`Required IAM Permissions <iam_policy>`.
