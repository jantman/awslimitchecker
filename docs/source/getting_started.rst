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
- Supports using `STS <http://docs.aws.amazon.com/STS/latest/APIReference/Welcome.html>`_ to assume roles in other accounts, including using ``external_id``.

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
   global percentage thresholds, as well as specify per-limit thresholds as a percentage, a fixed usage value, or both.

.. _getting_started.requirements:

Requirements
------------

* Python 2.6 or 2.7 (`boto <http://docs.pythonboto.org/en/latest/>`_ currently has incomplete python3 support)
* Python `VirtualEnv <http://www.virtualenv.org/>`_ and ``pip`` (recommended installation method; your OS/distribution should have packages for these)
* `boto <http://docs.pythonboto.org/en/latest/>`_


.. _getting_started.installing:

Installing
----------

It's recommended that you install into a virtual environment (virtualenv /
venv). See the `virtualenv usage documentation <http://www.virtualenv.org/en/latest/>`_
for more details, but the gist is as follows (the virtualenv name, "limitchecker" here,
can be whatever you want):

.. code-block:: bash

    virtualenv limitchecker
    source limitchecker/bin/activate
    pip install awslimitchecker

.. _getting_started.credentials:

Credentials
-----------

Aside from STS, awslimitchecker does nothing with AWS credentials, it leaves that to boto itself.
You must either have your credentials configured in one of boto's supported config
files, or set as environment variables. See
`boto config <http://docs.pythonboto.org/en/latest/boto_config_tut.html>`_
and
`this project's documentation <http://awslimitchecker.readthedocs.org/en/latest/getting_started.html#credentials>`_
for further information.

When using STS, you will need to specify the ``-r`` / ``--region`` option as well as the ``-A`` / ``--sts-account-id``
and ``-R`` / ``--sts-account-role`` options to specify the Account ID that you want to assume a role in, and the
name of the role you want to assume. If an external ID is required, you can specify it with ``-E`` / ``--external-id``.

.. _getting_started.regions:

Regions
-------

To specify the region that ``awslimitchecker`` connects to, use the ``-r`` / ``--region``
command line option. At this time awslimitchecker can only connect to one region at a time;
to check limits in multiple regions, simply run the script multiple times, once per region.

.. _getting_started.permissions:

Required Permissions
--------------------

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
