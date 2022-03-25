Changelog
=========

.. _changelog.12_0_0:

12.0.0 (2021-08-04)
-------------------

IMPORTANT - Breaking Changes
++++++++++++++++++++++++++++

* This release **removes** the ``EC2 / Max spot instance requests per region`` limit, which has been removed by AWS, in favor of six new vCPU-based limits: ``All F Spot Instance Requests``, ``All G Spot Instance Requests``, ``All Inf Spot Instance Requests``, ``All P Spot Instance Requests``,  ``All X Spot Instance Requests``, and ``All Standard (A, C, D, H, I, M, R, T, Z) Spot Instance Requests``.
* This release **adds two new services**: ``CertificateManager`` (ACM) and ``CloudFront``.
* This release **requires additional IAM permissions**: ``acm:ListCertificates``, ``cloudfront:ListCloudFrontOriginAccessIdentities``, ``cloudfront:ListKeyGroups``, ``cloudfront:ListDistributions``, ``cloudfront:ListCachePolicies``, and ``cloudfront:ListOriginRequestPolicies``.

IMPORTANT - Seeking New Maintainer
++++++++++++++++++++++++++++++++++

As I commented in `Issue #500 <https://github.com/jantman/awslimitchecker/issues/500>`__, I'm looking for someone to share (and perhaps take over) maintenance of this project. awslimitchecker is, and has always been, a personal-time-only project for me; the only time I've done work on it during my day job is when my employer was experiencing an issue or requested a specific feature. Because of a variety of issues, including changing personal interests and my employer relying on this project much less (following an AWS account restructuring that largely avoids service limits), I've been spending much less time on this project than it deserves. As a result, I'm looking for someone to help with maintenance... at the very least, helping review PRs and get them to a merge-able state. If you're interested, please comment on `Issue #500 <https://github.com/jantman/awslimitchecker/issues/500>`__ or contact me directly. While I am *incredibly* flattered by the offers I've received for sponsorship, paid support, or other financial incentive, I'd ask that anyone who's willing to make that commitment instead dedicate a few hours to working on issues or PRs. I, for my part, will make a concerted effort to quickly merge and release any PRs that meet all of the :ref:`development.pull_request_guidelines`.

All Changes
+++++++++++

* `PR #532 <https://github.com/jantman/awslimitchecker/pull/532>`__ - Add Quotas Service support for ECS Fargate quotas. Thanks to `robpickerill <https://github.com/robpickerill>`__ for this contribution.
* `PR #533 <https://github.com/jantman/awslimitchecker/pull/533>`__ / Fixes `Issue #527 <https://github.com/jantman/awslimitchecker/issues/527>`__ - Fix Quotas Service quota names for EIPs. Thanks to `robpickerill <https://github.com/robpickerill>`__ for this contribution.
* `PR #534 <https://github.com/jantman/awslimitchecker/pull/534>`__ / Fixes `Issue #521 <https://github.com/jantman/awslimitchecker/issues/521>`__ - Update Quotas Service quota names for EBS. Thanks to `robpickerill <https://github.com/robpickerill>`__ for this contribution.
* `PR #535 <https://github.com/jantman/awslimitchecker/pull/535>`__ / Fixes `Issue #518 <https://github.com/jantman/awslimitchecker/issues/518>`__ - Fix EC2 Security Group counts to only include groups owned by the current account. Thanks to `robpickerill <https://github.com/robpickerill>`__ for this contribution.
* `PR #536 <https://github.com/jantman/awslimitchecker/pull/536>`__ / Fixes `Issue #512 <https://github.com/jantman/awslimitchecker/issues/512>`__ - Fix CloudWatch metrics queries to get data from one minute ago, to fix bug where GetMetricData is not yet populated. Thanks to `robpickerill <https://github.com/robpickerill>`__ for this contribution.
* `PR #543 <https://github.com/jantman/awslimitchecker/pull/543>`__ / Fixes `Issue #538 <https://github.com/jantman/awslimitchecker/issues/538>`__ - Fix issue with calculation of usage for EC2 Rules Per Network ACL. Thanks to `jwu2 <https://github.com/jwu2>`__ for this contribution.
* `PR #537 <https://github.com/jantman/awslimitchecker/pull/537>`__ - Use boto3 adaptive retry mode. Thanks to `robpickerill <https://github.com/robpickerill>`__ for this contribution.
* `PR #547 <https://github.com/jantman/awslimitchecker/pull/547>`__ / Fixes `Issue #502 <https://github.com/jantman/awslimitchecker/issues/502>`__ - Replace ``EC2 / Max spot instance requests per region`` limit, which has been removed by AWS, with new vCPU-based spot instance requests limits. This also switches to using CloudWatch metric data to retrieve current usage. Thanks to `TagadaPoe <https://github.com/TagadaPoe>`__ for this contribution.
* `PR #546 <https://github.com/jantman/awslimitchecker/pull/546>`__ / Fixes `Issue #540 <https://github.com/jantman/awslimitchecker/issues/540>`__ - Add support for ACM (Certificate Manager) limits. Thanks to `TagadaPoe <https://github.com/TagadaPoe>`__ for this contribution.
* `PR #545 <https://github.com/jantman/awslimitchecker/pull/545>`__ / Fixes `Issue #539 <https://github.com/jantman/awslimitchecker/issues/539>`__ - Add support for CloudFront limits. Thanks to `TagadaPoe <https://github.com/TagadaPoe>`__ for this contribution.
* `Issue #551 <https://github.com/jantman/awslimitchecker/issues/551>`__ - Allow custom host for Datadog metric provider.

.. _changelog.11_0_0:

11.0.0 (2021-04-20)
-------------------

IMPORTANT - Breaking Changes
++++++++++++++++++++++++++++

* This release **removes** the EBS ``General Purpose (SSD) volume storage (GiB)`` limit in favor of ``General Purpose (SSD gp2) volume storage (GiB)`` and ``General Purpose (SSD gp3) volume storage (GiB)`` limits, to account for the new gp3 volume type and corresponding AWS service limits.
* This release **removes** the EBS ``Provisioned IOPS`` and ``Provisioned IOPS (SSD) storage (GiB)`` limits in favor of ``Provisioned IOPS (io1)`` and ``Provisioned IOPS (io2)``, and ``Provisioned IOPS SSD (io1) storage (GiB)`` and ``Provisioned IOPS SSD (io2) storage (GiB)``, respectively, to account for the new ``io2`` EBS volume type and corresponding AWS service limtits.

IMPORTANT - Seeking New Maintainer
++++++++++++++++++++++++++++++++++

As I commented in `Issue #500 <https://github.com/jantman/awslimitchecker/issues/500>`__, I'm looking for someone to share (and perhaps take over) maintenance of this project. awslimitchecker is, and has always been, a personal-time-only project for me; the only time I've done work on it during my day job is when my employer was experiencing an issue or requested a specific feature. Because of a variety of issues, including changing personal interests and my employer relying on this project much less (following an AWS account restructuring that largely avoids service limits), I've been spending much less time on this project than it deserves. As a result, I'm looking for someone to help with maintenance... at the very least, helping review PRs and get them to a merge-able state. If you're interested, please comment on `Issue #500 <https://github.com/jantman/awslimitchecker/issues/500>`__ or contact me directly. While I am *incredibly* flattered by the offers I've received for sponsorship, paid support, or other financial incentive, I'd ask that anyone who's willing to make that commitment instead dedicate a few hours to working on issues or PRs. I, for my part, will make a concerted effort to quickly merge and release any PRs that meet all of the :ref:`development.pull_request_guidelines`.

All Changes
+++++++++++

* `PR #519 <https://github.com/jantman/awslimitchecker/pull/519>`__ - Add support for ``gp3`` EBS volume type. Thanks to `spockNinja <https://github.com/spockNinja>`__ for this contribution!
* `Issue #514 <https://github.com/jantman/awslimitchecker/issues/514>`__ / `PR #517 <https://github.com/jantman/awslimitchecker/pull/517>`__ - Fix EKS Fargate profile usage check exception (``KeyError: 'labels'``). Thanks to `jwu2 <https://github.com/jwu2>`__ for first reporting this issue and `sebasrp <https://github.com/sebasrp>`__ for the fix!
* `Issue #520 <https://github.com/jantman/awslimitchecker/issues/520>`__ / `PR #522 <https://github.com/jantman/awslimitchecker/pull/522>`__ - Add awslimitchecker to `conda-forge <https://github.com/conda-forge/awslimitchecker-feedstock>`__ so it can be installed via `Conda <https://conda.io/>`__. Thanks to `BastianZim <https://github.com/BastianZim>`__ for this.
* `PR #525 <https://github.com/jantman/awslimitchecker/pull/525>`_ - Fix Prometheus example in docs, thanks to `felixkrohn <https://github.com/felixkrohn>`__.
* `PR #526 <https://github.com/jantman/awslimitchecker/pull/526>`__ - Fix possible ``KeyError: 'LaunchSpecifications'`` in EC2 service. Thanks to `nitrocode <https://github.com/nitrocode>`__ for this.
* `PR #528 <https://github.com/jantman/awslimitchecker/pull/528>`_ - Update ECS default limits. Thanks to `arturpriz <https://github.com/arturpriz>`__ for this contribution.
* `PR #523 <https://github.com/jantman/awslimitchecker/pull/523>`_ - Add support for io2 type EBS volumes. Thanks to `andyjp <https://github.com/andyjp>`__ for this contribution.
* Add tox and TravisCI support for testing against Python 3.9; bump the ``docker``, ``docs``, and ``integration3`` tox environments from 3.8 to 3.9.
* Bump the base Docker image from Python 3.8 to 3.9.

.. _changelog.10_0_0:

10.0.0 (2020-12-07)
-------------------

IMPORTANT - Breaking Changes
++++++++++++++++++++++++++++

* This release makes significant changes to how Trusted Advisor is used; see below.
* This release requires the following new IAM permissions: ``eks:ListClusters``, ``eks:DescribeCluster``, ``eks:ListNodegroups``, ``eks:ListFargateProfiles``, ``eks:DescribeFargateProfile``, ``kinesis:DescribeLimits``.
* This release introduces a number of new limits, as well as new services. Please see below for details.
* This release **removes** the ``EC2/Security groups per VPC`` limit, which no longer exists, and adds the new ``EC2/VPC security groups per Region`` limit.

All Changes
+++++++++++

* `Issue #466 <https://github.com/jantman/awslimitchecker/issues/466>`__ - **Significant** changes to Trusted Advisor support.

  * In June 2019, AWS `announced <https://aws.amazon.com/about-aws/whats-new/2019/06/introducing-service-quotas-view-and-manage-quotas-for-aws-services-from-one-location/>`__ the new Service Quotas service (great name) that allows us to retrieve limit/quota information from a unified API. In addition, many individual services now provide limit information via their own APIs. At this point (late 2020) all of the limit/quota information that was previously available via Trusted Advisor is now available via a combination of the individual service APIs and Service Quotas.
  * In February 2020, the layout of Trusted Advisor checks was changed, and the "Performance / Service Limits" check that we previously used to obtain limit information was moved to its own category in Trusted Advisor. While I can't confirm this, as far as I can tell, this change was only made in the standard AWS regions/partitions (i.e. not GovCloud or China).
  * awslimitchecker still has not been updated for this new Trusted Advisor layout.
  * This release **disables Trusted Advisor by default outside China and GovCloud**, as it provides no additional information outside of these regions/partitions.
  * If you are running in China or GovCloud and have issues with awslimitchecker retrieving information from Trusted Advisor, please `open an issue <https://github.com/jantman/awslimitchecker/issues>`__.
  * My current intent is to leave Trusted Advisor support in this state until Service Quotas is available in China and GovCloud, at which point I plan on completely removing all Trusted Advisor support.
* Migrate CI builds from travis-ci.org to travis-ci.com.
* `Issue #503 <https://github.com/jantman/awslimitchecker/issues/503>`__ - Fix ``Units set to "None"`` error when retrieving load balancer data from Service Quotas. We now allow the (A|E)LB per Region quota with a unit of either "Count" (prior to November 2020) or "None" (November 2020 on).
* `Issue #489 <https://github.com/jantman/awslimitchecker/issues/489>`__ / `PR #490 <https://github.com/jantman/awslimitchecker/pull/490>`__ - Add missing RDS limits: ``Manual Cluster Snapshots``, ``Custom Endpoints Per DB Cluster``, ``DB Instance Roles``, and ``DB Cluster Roles``. Thanks to `sebasrp <https://github.com/sebasrp>`__ for this contribution!
* `Issue #472 <https://github.com/jantman/awslimitchecker/issues/472>`__ / `PR #494 <https://github.com/jantman/awslimitchecker/pull/494>`__ - Add support for the ``EKS`` service, and 8 new limits for it. Thanks to `sebasrp <https://github.com/sebasrp>`__ for this contribution!
* `Issue #495 <https://github.com/jantman/awslimitchecker/issues/495>`__ / `PR #496 <https://github.com/jantman/awslimitchecker/pull/496>`__ - Add support for the ``Kinesis`` service, and one new limit for it. Thanks to `sebasrp <https://github.com/sebasrp>`__ for this contribution!
* `PR #499 <https://github.com/jantman/awslimitchecker/pull/499>`__ - Set quota_name for VPC "Entries per route table" limit, so that the current limit will be automatically retrieved from Service Quotas. Thanks to `patuck <https://github.com/patuck>`__ for this contribution!
* `Issue #498 <https://github.com/jantman/awslimitchecker/issues/498>`__ - Fix multiple issues relating to VPC limits:

  * Update the EC2 / ``Rules per VPC security group`` limit to support retrieving the current limit value from Service Quotas.
  * Remove the ``EC2/Security groups per VPC`` limit, which no longer exists.
  * Add the new ``EC2/VPC security groups per Region`` limit.

* `Issue #501 <https://github.com/jantman/awslimitchecker/issues/501>`__ - Update ``VPC/Network interfaces per Region`` limit for new calculation method.
* `Issue #488 <https://github.com/jantman/awslimitchecker/issues/488>`__ / `PR #491 <https://github.com/jantman/awslimitchecker/pull/491>`__ - Update new ElastiCache default limits. Thanks to `sebasrp <https://github.com/sebasrp>`__ for this contribution!

.. _changelog.9_0_0:

9.0.0 (2020-09-22)
------------------

**Important:** This release requires new IAM permissions: ``sts:GetCallerIdentity`` and ``cloudwatch:GetMetricData``

**Important:** This release includes updates for major changes to ECS limits, which includes the renaming of some existing limits.

* `Issue #477 <https://github.com/jantman/awslimitchecker/issues/477>`__ - EC2 instances running on Dedicated Hosts (tenancy "host") or single-tenant hardware (tenancy "dedicated") do not count towards On-Demand Instances limits. They were previously being counted towards these limits; they are now excluded from the count. Thanks to `pritam2277 <https://github.com/pritam2277>`__ for reporting this issue and providing details and test data.
* `Issue #477 <https://github.com/jantman/awslimitchecker/issues/477>`__ - For all VPC resources that support the ``owner-id`` filter, supply that filter when describing them, set to the current account ID. This will prevent shared resources from other accounts from being counted against the limits. Thanks to `pritam2277 <https://github.com/pritam2277>`__ for reporting this issue and providing details and test data.
* `Issue #475 <https://github.com/jantman/awslimitchecker/issues/475>`__ - When an Alert Provider is used, only exit non-zero if an exception is encountered. Exit zero even if there are warnings and/or criticals. Thanks to `varuzam <https://github.com/varuzam>`__ for this feature request.
* `Issue #467 <https://github.com/jantman/awslimitchecker/issues/467>`__ - Fix the Service Quotas quota name for VPC "NAT Gateways per AZ" limit. Thanks to `xRokco <https://github.com/xRokco>`__ for reporting this issue, as well as the required fix.
* `Issue #457 <https://github.com/jantman/awslimitchecker/issues/457>`__ - In the required IAM permissions, replace ``support:*`` with the specific permissions that we need.
* `Issue #463 <https://github.com/jantman/awslimitchecker/issues/463>`__ - Updates for the major changes to ECS limits `in August 2020 <https://github.com/awsdocs/amazon-ecs-developer-guide/commit/3ba9bc24b3f667557f43a49b9001fea3538311ad#diff-d98743b56c4036e0baeb5e15901d2a73>`__. Thanks to `vincentclee <https://github.com/vincentclee>`__ for reporting this issue.

  * The ``EC2 Tasks per Service (desired count)`` limit has been replaced with ``Tasks per service``, which measures the desired count of tasks of all launch types (EC2 or Fargate). The default value of this limit has increased from 1000 to 2000.
  * The default of ``Clusters`` has increased from 2,000 to 10,000.
  * The default of ``Services per Cluster`` has increased from 1,000 to 2,000.
  * The ``Fargate Tasks`` limit has been removed.
  * The ``Fargate On-Demand resource count`` limit has been added, with a default quota value of 500. This limit measures the number of ECS tasks and EKS pods running concurrently on Fargate. The current usage for this metric is obtained from CloudWatch.
  * The ``Fargate Spot resource count`` limit has been added, with a default quota value of 500. This limit measures the number of ECS tasks running concurrently on Fargate Spot. The current usage for this metric is obtained from CloudWatch.

* Add internal helper method to :py:class:`~._AwsService` to get Service Quotas usage information from CloudWatch.

.. _changelog.8_1_0:

8.1.0 (2020-09-18)
------------------

* `PR #468 <https://github.com/jantman/awslimitchecker/pull/468>`_ - Fix transposed headings in CLI Usage documentation. Thanks to `@owenmann <https://github.com/owenmann>`__.
* `PR #470 <https://github.com/jantman/awslimitchecker/pull/470>`_ - Fix new EBS "Active snapshots" limit (bumped from 10,000 to 100,000) and Quotas Service name. Thanks to `@rashidamiri <https://github.com/rashidamiri>`__.
* `Issue #464 <https://github.com/jantman/awslimitchecker/issues/464>`_ - Fix bug where SES was causing ``ConnectTimeoutError`` in some regions. This has been added to the list of SES exceptions that we catch and silently ignore. This is a new exception thrown by regions that do not have SES support.
* Add ``.dockerignore`` file to make local builds quite a bit smaller.
* `Issue #465 <https://github.com/jantman/awslimitchecker/issues/465>`_ - Fixed via `versionfinder 1.1.1 <https://github.com/jantman/versionfinder/pull/13>`_.
* Internal testing changes:

  * Stop testing under Python 2.7 and Python 3.4.
  * Switch from deprecated pep8 / pytest-pep8 to pycodestyle / pytest-pycodestyle.
  * Pin pytest to ``<6.0.0`` to avoid some breaking changes for now.
  * Switch integration test environment from Python 3.7 to Python 3.8.

.. _changelog.8_0_2:

8.0.2 (2020-03-03)
------------------

* `PR #458 <https://github.com/jantman/awslimitchecker/pull/458>`_ - Fix for ZeroDivisionError on some Service Quotas limits that report as having a limit of zero. Thanks to `@deimosfr <https://github.com/deimosfr>`__.

.. _changelog.8_0_1:

8.0.1 (2019-12-28)
------------------

* Fixes `issue #453 <https://github.com/jantman/awslimitchecker/issues/453>`__ - remove version constraint on ``dateutil`` dependency.
* Fixes `issue #454 <https://github.com/jantman/awslimitchecker/issues/454>`__ - remove version constraint on ``botocore`` dependency.
* Update tox ``docs``, ``localdocs``, and ``docker`` environments to use Python 3.8.
* Fixes `issue #451 <https://github.com/jantman/awslimitchecker/issues/451>`__ - Fix default Rules Per VPC Security Group limit.

.. _changelog.8_0_0:

8.0.0 (2019-11-03)
------------------

**Important:** This release includes **major** changes to the EC2 On-Demand Instances service limits! For most users, this means the 175 Instance-type-specific limits will be removed and replaced with five (5) limits. Please see the :ref:`changelog.8_0_0_vcpu_limits` section below for further details, as this will especially impact anyone using limit or threshold overrides, or post-processing awslimitchecker's output. This is also a time to remind all users that this project adheres to a strict :ref:`development.versioning_policy` and if occasional breakage due to limit or IAM policy changes is unacceptable, you should pin to a major version.

**Important:** Python versions prior to 3.5, including 2.7, are now pending deprecation. As of January 1, 2020, they will no longer be tested or supported, and awslimitchecker **will require Python 3.5 or newer**. Please see below for details. Also take note that running via the official Docker image is a way to ensure the best version of Python is always used.

**Important:** This release requires a new IAM permission, ``servicequotas:ListServiceQuotas``.

* `Issue #400 <https://github.com/jantman/awslimitchecker/issues/400>`__ / `PR #434 <https://github.com/jantman/awslimitchecker/pull/434>`__ - Support GovCloud region and alternate partitions in STS assumed roles and Trusted Advisor. Thanks to `@djkiourtsis <https://github.com/djkiourtsis>`__.
* `Issue #432 <https://github.com/jantman/awslimitchecker/issues/432>`__ - Update EC2 limit handling for new vCPU-based limits in regions other than ``cn-*`` and ``us-gov-*`` (which still use old per-instance-type limits). See :ref:`section below <changelog.8_0_0_vcpu_limits>` for further information. For regions other than ``cn-*`` and ``us-gov-*``, **this will remove** all 175 ``Running On-Demand <type> instances`` and the ``Running On-Demand EC2 instances`` limit, and replace them with:

  * ``Running On-Demand All F instances``
  * ``Running On-Demand All G instances``
  * ``Running On-Demand All P instances``
  * ``Running On-Demand All X instances``
  * ``Running On-Demand All Standard (A, C, D, H, I, M, R, T, Z) instances``

* `Issue #429 <https://github.com/jantman/awslimitchecker/issues/429>`_ - add 87 missing EC2 instance types. This will now only impact ``cn-*`` and ``us-gov-*`` regions.
* `Issue #433 <https://github.com/jantman/awslimitchecker/issues/433>`_ - Fix broken links in the docs; waffle.io and landscape.io are both gone, sadly.
* `Issue #441 <https://github.com/jantman/awslimitchecker/issues/441>`_ - Fix critical bug where awslimitchecker would die with an unhandled ``botocore.exceptions.ParamValidationError`` exception in accounts that have Trusted Advisor but do not have a "Service Limits" check in the "performance" category.
* `Issue #439 <https://github.com/jantman/awslimitchecker/issues/439>`_ - Fix unhandled exception in CloudTrail service when attempting to call ``GetEventSelectors`` on an Organization trail. When calling ``DescribeTrails``, we will now pass ``includeShadowTrails`` as False, to not include replications of trails in different regions or organization trails in member accounts (relevant `API documentation <https://docs.aws.amazon.com/awscloudtrail/latest/APIReference/API_DescribeTrails.html>`_).
* `Issue #438 <https://github.com/jantman/awslimitchecker/issues/438>`_ - Per `PEP 373 <https://www.python.org/dev/peps/pep-0373/>`__, Python 2.7 will officially end support on January 1, 2020. As such, and in keeping with reasoning explained at `python3statement.org <https://python3statement.org/>`__, awslimitchecker will **stop supporting and testing against Python 2.7** on January 1, 2020. At that point, all new versions will be free to use Python features introduced in 3.5. As of this version, a `PendingDeprecationWarning <https://docs.python.org/3/library/exceptions.html#PendingDeprecationWarning>`__ will be emitted when running awslimitchecker under Python 2.7.
* `Issue #437 <https://github.com/jantman/awslimitchecker/issues/437>`_ - Per `PEP 429 <https://www.python.org/dev/peps/pep-0429/>`_, Python 3.4 reached end-of-life on March 18, 2019 and is now officially retired. Add a ``PendingDeprecationWarning`` for users running under this version, announcing that support for Python 3.4 will be removed on January 1, 2020.
* In following with the above two issues, raise a ``DeprecationWarning`` when running on any Python2 version prior to 2.7 or any Python3 version prior to 3.4, in accorance with the `published end-of-life dates of those versions <https://devguide.python.org/devcycle/#end-of-life-branches>`_.
* `Issue #436 <https://github.com/jantman/awslimitchecker/issues/436>`_ - Begin testing under Python 3.8 and base our Docker image on ``python:3.8-alpine``.
* `Issue #435 <https://github.com/jantman/awslimitchecker/issues/435>`_ - Allow configuring the botocore maximum retries for Throttling / RateExceeded errors on a per-AWS-API basis via environment variables. See the relevant sections of the :ref:`CLI Usage <cli_usage.throttling>` or :ref:`Python Usage <python_usage.throttling>` documentation for further details.
* `Issue #431 <https://github.com/jantman/awslimitchecker/issues/431>`_ - Fix a **major under-calculation** of usage for the EC2 ``Rules per VPC security group`` limit. We were previously calculating the number of "Rules" (from port / to port / protocol combinations) in a Security Group, but the limit is actually based on the number of permissions granted. See `this comment <https://github.com/jantman/awslimitchecker/issues/431#issuecomment-548599785>`_ on the issue for further details.
* `Issue #413 <https://github.com/jantman/awslimitchecker/issues/431>`_ - Add support for retrieving limits from the new `Service Quotas service <https://docs.aws.amazon.com/servicequotas/latest/userguide/intro.html>`__ where available. See the :ref:`changelog.8_0_0_service_quotas` section below for more information.
* Bump boto3 minimum version requirement from 1.4.6 to 1.9.175 and botocore minimum version requirement from 1.6.0 to 1.12.175, in order to support Service Quotas.

.. _changelog.8_0_0_vcpu_limits:

New EC2 vCPU Limits
+++++++++++++++++++

AWS has `announced <https://aws.amazon.com/blogs/compute/preview-vcpu-based-instance-limits/>`__ new, completely different handling of EC2 On-Demand Instances service limits. Instead of having a limit per instance type (currently 261 limits), there will now be only *five* limits, based on the number of vCPUs for instance families: one each for "F", "G", "P", and "X" family instances (defaulting to a total of 128 vCPUs each) and one limit for all other "Standard" instance families (currently A, C, D, H, I, M, R, T, and Z) defaulting to a combined total of 1152 vCPUs. Please see the link, and the `EC2 On-Demand Instance Limits section of the AWS FAQ <https://aws.amazon.com/ec2/faqs/#EC2_On-Demand_Instance_limits>`__ for further information.

This greatly simplifies handling of the EC2 On-Demand limits, but does mean that any existing code that references EC2 Running On-Demand limit names, including any limit and/or threshold overrides, will need to be updated for this change.

This change is only going into effect in the "standard" AWS regions/partitions, i.e. not in the China partition (``cn-`` regions) or GovCloud (``us-gov-`` regions). It is a phased rollout from October 24 to November 7, 2019 based on the first character of your account ID (see the "How will the transition to vCPU limits happen?" entry in the FAQ linked above for exact dates). **Unfortunately, there is no clear way to determine via API if a given account is using the new vCPU limits or the old per-instance-type limits.** As a result, and given that this release is being made already part-way through the rollout window, the current behavior of awslimitchecker is as follows:

* When running against region names beginning with ``cn-`` or ``us-gov-``, use the old per-instance-type limits, unless the ``USE_VCPU_LIMITS`` environment variable is set to ``true``.
* Otherwise use the new vCPU-based limits, unless the ``USE_VCPU_LIMITS`` environment variable is set to something other than ``true``.

As such, if you install this release before November 7, 2019 and need to force your non-China, non-GovCloud accout to use the older per-instance-type limits, setting the ``USE_VCPU_LIMITS`` environment variable to ``false`` will accomplish this until your account switches over to the new vCPU limits. **Alternatively, you can leave awslimitchecker as-is and accept possibly-slightly-inaccurate limit calculations for a few days.**

Please also note that with the change to vCPU limits, there is no longer an overall ``Running On-Demand EC2 instances`` limit for accounts that use the new vCPU limits.

I have **not** yet implemented Trusted Advisor (TA) support for these new limits, as they're presented in a different category of Trusted Advisor checks from the previous EC2 limits. I'm not going to be implementing TA for these limits, in favor of spending the time instead on implementing Service Quotas support via `Issue #413 <https://github.com/jantman/awslimitchecker/issues/413>`__.

Calculation of current usage for the vCPU limits is based on the `EC2 Optimizing CPU Options documentation <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-optimize-cpu.html>`__ which specifies, "The number of vCPUs for the instance is the number of CPU cores multiplied by the threads per core." The ``CpuOptions`` field of the EC2 ``DescribeInstances`` API specifies the core and thread count for each running instance.

.. _changelog.8_0_0_service_quotas:

Service Quotas
++++++++++++++

AWS' new `Service Quotas service <https://docs.aws.amazon.com/servicequotas/latest/userguide/intro.html>`__ provides a unified interface to retrieve current limits from many AWS services. These limit values are second only to the services' own APIs (for the services that provide limit information via API), and are much more current and complete than the information provided by Trusted Advisor. The introduction of Service Quotas should greatly reduce the number of limits that need to be retrieved from Trusted Advisor or specified manually.

If you currently have any Limit Overrides set (via either the :ref:`CLI <cli_usage.limit_overrides>` or :ref:`Python API <python_usage.limit_overrides>`), please verify on the :ref:`limits` page whether Service Quotas data is now available for those limits. You should be able to remove manual overrides for the limits that now retrieve data from Service Quotas.

.. _changelog.7_1_0:

7.1.0 (2019-09-10)
------------------

* `Issue #301 <https://github.com/jantman/awslimitchecker/issues/301>`__ - Distribute an official Docker image for awslimitchecker.
* `Issue #421 <https://github.com/jantman/awslimitchecker/issues/421>`__

  * Stop referencing deprecated ``botocore.vendored.requests.exceptions.ConnectTimeout`` in favor of new, and higher-level, ``botocore.exceptions.ConnectionError``
  * In :py:meth:`awslimitchecker.utils._get_latest_version`, replace use of ``botocore.vendored.requests`` with ``urllib3``.

* `Issue #324 <https://github.com/jantman/awslimitchecker/issues/324>`__ - Support loading :ref:`limit overrides <cli_usage.limit_overrides>` and/or :ref:`threshold overrides <cli_usage.threshold_overrides>` from a JSON file either stored locally or in S3 via new ``--limit-override-json`` and ``--threshold-override-json`` CLI options.
* `Issue #418 <https://github.com/jantman/awslimitchecker/issues/418>`__ - Add support for sending runtime, limits, and usage to :ref:`<metric providers <cli_usage.metrics>` such as Datadog.
* `Issue #419 <https://github.com/jantman/awslimitchecker/issues/419>`__ - Add support for alerts/notifications of thresholds crossed or failed runs (exceptions) via :ref:`<alert providers <cli_usage.alerts>` such as PagerDuty.

.. _changelog.7_0_0:

7.0.0 (2019-08-13)
------------------

This release **removes one limit and adds two new limits**!

* `Issue #412 <https://github.com/jantman/awslimitchecker/issues/412>`__ / `PR #414 <https://github.com/jantman/awslimitchecker/pull/414>`__ - Since some time in June 2019, the former ``ELB`` Service ``Active load balancers`` limit is now two separate limits, ``Classic load balancers`` and ``Application load balancers``. **Anyone who was using the "Active load balancers" limit name (e.g. in overrides or custom code) must update their code accordingly.** This release removes the ``Active load balancers`` limit and adds two new limits, ``Classic load balancers`` and ``Application load balancers``, to match how AWS now calculates and exposes these limits.
* `Issue #410 <https://github.com/jantman/awslimitchecker/issues/410>`__ - Documentation fix for missing Trusted Advisor information on Limits page.
* Fix some test failures related to exception objects in pytest 5.0.0.

.. _changelog.6_1_7:

6.1.7 (2019-05-17)
------------------

* `Issue #406 <https://github.com/jantman/awslimitchecker/issues/406>`__ - Fix for unhandled exception when a Trusted Advisor check has a ``null`` timestamp.

.. _changelog.6_1_6:

6.1.6 (2019-04-19)
------------------

* `PR #402 <https://github.com/jantman/awslimitchecker/pull/402>`__ - Add ``--skip-check`` command line option for ignoring specific checks based on service and check name. Thanks to `@ddelnano <https://github.com/ddelnano>`__.

.. _changelog.6_1_5:

6.1.5 (2019-03-06)
------------------

* `Issue #397 <https://github.com/jantman/awslimitchecker/issues/397>`__ - Fix unhandled exception checking SES in some regions. `Issue #375 <https://github.com/jantman/awslimitchecker/issues/375>`__ in 6.0.1 handled an uncaught ``ClientError`` when checking SES in some regions, but some regions such as ap-southeast-2 are now returning a 503 Service Unavailable for SES instead. Handle this case as well. Thanks to `@TimGebert <https://github.com/TimGebert>`__ for reporting the issue and `bergkampsliew <https://github.com/bergkampsliew>`__ for verifying.

.. _changelog.6_1_4:

6.1.4 (2019-03-01)
------------------

* `PR #394 <https://github.com/jantman/awslimitchecker/pull/394>`_ - Fix bug in calculation of VPC "Network interfaces per Region" limit, added in 6.1.0 (`PR #379 <https://github.com/jantman/awslimitchecker/pull/379>`__), that resulted in reporting the limit 5x lower than it actually is in some cases. Thanks to `@TimGebert <https://github.com/TimGebert>`__.

.. _changelog.6_1_3:

6.1.3 (2019-02-26)
------------------

* `PR #391 <https://github.com/jantman/awslimitchecker/pull/391>`_ / `Issue #390 <https://github.com/jantman/awslimitchecker/issues/390>`_ - Update for some recently-increased DynamoDB and EFS default limits. Thanks to `bergkampsliew <https://github.com/bergkampsliew>`__.

.. _changelog.6_1_2:

6.1.2 (2019-02-19)
------------------

* `PR #387 <https://github.com/jantman/awslimitchecker/pull/387>`_ - Fix bug in calculation of VPC "Network interfaces per Region" limit, added in 6.1.0 (`PR #379 <https://github.com/jantman/awslimitchecker/pull/379>`__). Thanks to `@nadlerjessie <https://github.com/nadlerjessie>`__.

.. _changelog.6_1_1:

6.1.1 (2019-02-15)
------------------

* `PR #381 <https://github.com/jantman/awslimitchecker/pull/381>`_ / `Issue #382 <https://github.com/jantman/awslimitchecker/issues/382>`_ - Revised fix for `Issue #375 <https://github.com/jantman/awslimitchecker/issues/375>`__, uncaught ``ClientError`` exception when checking SES Send Quota in certain regions. Thanks to `bergkampsliew <https://github.com/bergkampsliew>`__.

.. _changelog.6_1_0:

6.1.0 (2019-01-30)
------------------

* `PR #379 <https://github.com/jantman/awslimitchecker/pull/379>`__ - Add support for EC2/VPC ``Network interfaces per Region`` limit. Thanks to `@nadlerjessie <https://github.com/nadlerjessie>`__.

.. _changelog.6_0_1:

6.0.1 (2019-01-27)
------------------

* `Issue #375 <https://github.com/jantman/awslimitchecker/issues/375>`__ - Fix uncaught ``ClientError`` exception when checking SES Send Quota in certain regions. Thanks to `bergkampsliew <https://github.com/bergkampsliew>`__ for `PR #376 <https://github.com/jantman/awslimitchecker/pull/376>`_.

.. _changelog.6_0_0:

6.0.0 (2019-01-01)
------------------

This release **requires new IAM permissions**:

* ``lambda:GetAccountSettings``

**Important:** This release removes the ApiGateway ``APIs per account`` limit in favor of more-specific limits; see below.

* `Issue #363 <https://github.com/jantman/awslimitchecker/issues/363>`_ - Add support for the Lambda limits and usages.
* Clarify support for "unlimited" limits (limits where :py:meth:`awslimitchecker.limit.AwsLimit.get_limit` returns ``None``).
* Add support for 26 new EC2 instance types.
* Update default limits for ECS service.
* ``ApiGateway`` service now has three ReST API limits (``Regional API keys per account``, ``Private API keys per account``, and ``Edge API keys per account``) in place of the previous single ``APIs per account`` to reflect the current documented service limits.
* API Gateway service - add support for ``VPC Links per account`` limit.
* Add support for Network Load Balancer limits ``Network load balancers`` and ``Listeners per network load balancer``.
* Add support for Application Load Balancer limits ``Certificates per application load balancer``.
* Add support for Classic ELB (ELBv1) ``Registered instances per load balancer`` limit.
* Rename ``dev/terraform.py`` to ``dev/update_integration_iam_policy.py`` and move from using terraform to manage integration test IAM policy to pure Python.

* Note that I've left out the ``Targets per application load balancer`` and ``Targets per network load balancer`` limits. Checking usage for these requires iterating over ``DescribeTargetHealth`` for each target group, so I've opted to leave it out at this time for performance reasons and because I'd guess that the number of people with 500 or 1000 targets per LB is rather small. Please open an issue if you'd like to see usage calculation for these limits.

Important Note on Limit Values
++++++++++++++++++++++++++++++

awslimitchecker has had documented support for Limits that are unlimited/"infinite" since 0.5.0 by returning ``None`` from :py:meth:`awslimitchecker.limit.AwsLimit.get_limit`. Until now, that edge case was only triggered when Trusted Advisor returned "Unlimited" for a limit. It will now also be returned for the Lambda service's ``Function Count`` Limit. Please be aware of this if you're using the Python API and assuming Limit values are all numeric.

If you are relying on the output format of the command line ``awslimitchecker`` script, please use the Python API instead.

.. _changelog.5_1_0:

5.1.0 (2018-09-23)
------------------

* `Issue #358 <https://github.com/jantman/awslimitchecker/issues/358>`_ - Update EFS with new default limit for number of File systems: 70 in us-east-1 and 125 in other regions.
* `PR #359 <https://github.com/jantman/awslimitchecker/pull/359>`_ - Add support for ``t3`` EC2 instance types (thanks to `chafouin <https://github.com/chafouin>`_).
* Switch ``py37`` TravisCI tests from py37-dev to py37 (release).

.. _changelog.5_0_0:

5.0.0 (2018-07-30)
------------------

This release **requires new IAM permissions**:

* ``cloudtrail:DescribeTrails``
* ``cloudtrail:GetEventSelectors``
* ``route53:GetHostedZone``
* ``route53:ListHostedZones``
* ``route53:GetHostedZoneLimit``

This release **officially drops support for Python 2.6 and 3.3.**

* `PR #345 <https://github.com/jantman/awslimitchecker/pull/345>`_ / `Issue #349 <https://github.com/jantman/awslimitchecker/issues/349>`_ - Add Route53 service and checks for "Record sets per hosted zone" and "VPC associations per hosted zone" limits (the latter only for private zones). (thanks to `julienduchesne <https://github.com/julienduchesne>`_).
* Support Per-Resource Limits (see below). **Note that this includes some changes to the ``awslimitchecker`` CLI output format and some minor API changes.**
* `Issue #317 <https://github.com/jantman/awslimitchecker/issues/317>`_ - Officially drop support for Python 2.6 and 3.3. Also, begin testing py37.
* `Issue #346 <https://github.com/jantman/awslimitchecker/issues/346>`_ - Update documentation for S3 API calls made by ElasticBeanstalk while retrieving EB limits (thanks to `fenichelar <https://github.com/fenichelar>`_ for finding this).
* `PR #350 <https://github.com/jantman/awslimitchecker/pull/350>`_ - Add support for CloudTrail limits (thanks to `fpiche <https://github.com/fpiche>`_).
* `Issue #352 <https://github.com/jantman/awslimitchecker/issues/352>`_ - Update version check PyPI URL and set User-Agent when performing version check.
* `Issue #351 <https://github.com/jantman/awslimitchecker/issues/351>`_ - Add support for **forty two (42)** missing EC2 instance types including the new c5d/m5d/r5d/z1d series instances.

Per-Resource Limits
+++++++++++++++++++

Some Limits (:py:class:`~.AwsLimit`) now have limits/maxima that are per-resource rather than shared across all resources of a given type. The first limit of this kind that awslimitchecker supports is Route53, where the "Record sets per hosted zone" and "VPC associations per hosted zone" limits are set on a per-resource (per-zone) basis rather than globally to all zones in the account. Limits of this kind are also different since, as they are per-resource, they can only be enumerated at runtime. Supporting limits of this kind required some changes to the internals of awslimitchecker (specifically the :py:class:`~.AwsLimit` and :py:class:`~.AwsLimitUsage` classes) as well as to the output of the command line script/entrypoint.

For limits which support different maxima/limit values per-resource, the command line ``awslimitchecker`` script ``-l`` / ``--list-limits`` functionality will now display them in Service/Limit/ResourceID format, i.e.:

.. code-block:: none

    Route53/Record sets per hosted zone/foo.com                  10000 (API)
    Route53/Record sets per hosted zone/bar.com                  10000 (API)
    Route53/Record sets per hosted zone/local.                   15000 (API)
    Route53/VPC associations per hosted zone/local.              100 (API)

As opposed to the Service/Limit format used for all existing limits, i.e.:

.. code-block:: none

    IAM/Groups             300 (API)
    IAM/Instance profiles  2000 (API)

If you are relying on the output format of the command line ``awslimitchecker`` script, please use the Python API instead.

For users of the Python API, please take note of the new :py:meth:`.AwsLimit.has_resource_limits` and :py:meth:`~.AwsLimitUsage.get_maximum` methods which assist in how to identify limits that have per-resource maxima. Existing code that only surfaces awslimitchecker's warnings/criticals (the result of :py:meth:`~.AwsLimitChecker.check_thresholds`) will work without modification, but any code that displays or uses the current limit values themselves may need to be updated.

.. _changelog.4_0_2:

4.0.2 (2018-03-22)
------------------

This is a minor bugfix release for one issue:

* `Issue #341 <https://github.com/jantman/awslimitchecker/issues/341>`_ - The Trusted Advisor EBS checks for ``General Purpose (SSD) volume storage (GiB)`` and ``Magnetic volume storage (GiB)`` have been renamed to to ``General Purpose SSD (gp2) volume storage (GiB)`` and ``Magnetic (standard) volume storage (GiB)``, respectively, to provide more unified naming. This change was made on March 19th or 20th without any public announcement, and resulted in awslimitchecker being unable to determine the current values for these limits from Trusted Advisor. Users relying on Trusted Advisor for these values saw the limit values incorrectly revert to the global default. This is an internal-only change to map the new Trusted Advisor check names to the awslimitchecker limit names.

.. _changelog.4_0_1:

4.0.1 (2018-03-09)
------------------

This is a minor bugfix release for a few issues that users have reported recently.

* Fix `Issue #337 <https://github.com/jantman/awslimitchecker/issues/337>`_ where sometimes an account even with Business-level support will not have a Trusted Advisor result for the Service Limits check, and will return a result with ``status: not_available`` or a missing ``flaggedResources`` key.
* Fix `Issue #335 <https://github.com/jantman/awslimitchecker/issues/335>`_ where runs against the EFS service in certain unsupported regions result in either a connection timeout or an AccessDeniedException.

.. _changelog.4_0_0:

4.0.0 (2018-02-17)
------------------

This release **requires new IAM permissions**:

* ``ds:GetDirectoryLimits``
* ``ecs:DescribeClusters``
* ``ecs:DescribeServices``
* ``ecs:ListClusters``
* ``ecs:ListServices``

* Fix various docstring problems causing documentation build to fail.
* `PR #328 <https://github.com/jantman/awslimitchecker/pull/328>`_ - Add support for Directory Service and ECS (thanks to `di1214 <https://github.com/di1214>`_).

  * *NOTE* the "EC2 Tasks per Service (desired count)" limit uses non-standard resource IDs, as service names and ARNs aren't unique by account or region, but only by cluster. i.e. the only way to uniquely identify an ECS Service is by the combination of service and cluster. As such, the ``resource_id`` field for usage values of the "EC2 Tasks per Service (desired count)" limit is a string of the form ``cluster=CLUSTER-NAME; service=SERVICE-NAME``.

* `PR #330 <https://github.com/jantman/awslimitchecker/pull/330>`_ - Update numerous no-longer-correct default limits (thanks to GitHub user KingRogue).

  * AutoScaling

    * Auto Scaling groups - 20 to 200
    * Launch configurations - 100 to 200

  * EBS

    * Provisioned IOPS - 40000 to 200000
    * Provisioned IOPS (SSD) storage (GiB) - 20480 to 102400 (100 TiB)
    * General Purpose (SSD) volume storage (GiB) - 20480 to 102400 (100 TiB)
    * Throughput Optimized (HDD) volume storage (GiB) - 20480 to 307200 (300 TiB)
    * Cold (HDD) volume storage (GiB) - 20480 to 307200 (300 TiB)

  * ElasticBeanstalk

    * Applications - 25 to 75
    * Application versions - 500 to 1000

  * IAM

    * Groups - 100 to 300
    * Roles - 250 to 1000
    * Instance profiles - 100 to 1000
    * Policies - 1000 to 1500

* Fix ``dev/terraform.py`` and ``dev/integration_test_iam.tf`` for integration tests.
* Fix date and incorrect project name in some file/copyright headers.
* `Issue #331 <https://github.com/jantman/awslimitchecker/issues/331>`_ - Change layout of the generated `Supported Limits <http://awslimitchecker.readthedocs.io/en/latest/limits.html>`_ documentation page to be more clear about which limits are supported, and include API and Trusted Advisor data in the same table as the limits and their defaults.

.. _changelog.3_0_0:

3.0.0 (2017-12-02)
------------------

**Important Notice for python 2.6 and 3.3 users**:

Python 2.6 reached its end of life in `October 2013 <https://mail.python.org/pipermail/python-dev/2013-September/128287.html>`_.
Python 3.3 officially reached its end of life in `September 2017 <https://www.python.org/dev/peps/pep-0398/#lifespan>`_, five years
after development was ceased. The test framework used by awslimitchecker, pytest, has `dropped support <https://github.com/pytest-dev/pytest/blob/master/CHANGELOG.rst#pytest-330-2017-11-23>`_ for Python 2.6 and 3.3 in its latest release. According to the `PyPI download statistics <http://jantman-personal-public.s3-website-us-east-1.amazonaws.com/pypi-stats/awslimitchecker/index.html#graph_by-implementation>`_ (which unfortunately don't take into account mirrors or caching proxies), awslimitchecker has only ever had one download reported as Python 3.3 and has a very, very small number reporting as Python 2.6 (likely only a handful of users). **The next release of awslimitchecker will officially drop support for Python 2.6 and 3.3**, changing the required Python version to 2.7 or >= 3.4. If you are one of the very few (perhaps only one) users running on Python 2.6, you can either run with a newer Python version or see `Issue 301 <https://github.com/jantman/awslimitchecker/issues/301>`_ for information on building a Docker container based on Python 3.5.

* Fix test failures caused by dependency updates.
* Pin ``pytest`` development to 3.2.5 to continue python 2.6 and 3.3 support.
* `Issue #314 <https://github.com/jantman/awslimitchecker/issues/314>`_ - Update RDS service default limits; ``DB snapshots per user`` default limit increased from 50 to 100 and ``Subnet Groups`` limit increased from 20 to 50. This should not have affected any users, as these limits are retrieved in realtime via the RDS API.
* `Issue #293 <https://github.com/jantman/awslimitchecker/issues/293>`_ - Increase maximum number of retries (boto3/botocore) for ``elbv2`` API calls, to attempt to deal with the large number of calls we have to make in order to count the ALB listeners and rules. This requires botocore >= 1.6.0, which requires boto3 >= 1.4.6.
* `Issue #315 <https://github.com/jantman/awslimitchecker/issues/315>`_ - Add new instance types: 'c5.18xlarge', 'c5.2xlarge', 'c5.4xlarge', 'c5.9xlarge', 'c5.large', 'c5.xlarge', 'g3.16xlarge', 'g3.4xlarge', 'g3.8xlarge', 'h1.16xlarge', 'h1.2xlarge', 'h1.4xlarge', 'h1.8xlarge', 'm5.12xlarge', 'm5.24xlarge', 'm5.2xlarge', 'm5.4xlarge', 'm5.large', 'm5.xlarge', 'p3.16xlarge', 'p3.2xlarge', 'p3.8xlarge', 'x1e.32xlarge', 'x1e.xlarge'
* `Issue #316 <https://github.com/jantman/awslimitchecker/issues/316>`_ - Automate release process.

.. _changelog.2_0_0:

2.0.0 (2017-10-12)
------------------

* Update README with correct boto version requirement. (Thanks to `nadlerjessie <https://github.com/nadlerjessie>`_ for the contribution.)
* Update minimum ``boto3`` version requirement from 1.2.3 to 1.4.4; the code for `Issue #268 <https://github.com/jantman/awslimitchecker/issues/268>`_ released in 0.11.0 requires boto3 >= 1.4.4 to make the ElasticLoadBalancing ``DescribeAccountLimits`` call.
* **Bug fix for "Running On-Demand EC2 instances" limit** - `Issue #308 <https://github.com/jantman/awslimitchecker/issues/308>`_ - The fix for `Issue #215 <https://github.com/jantman/awslimitchecker/issues/215>`_ / `PR #223 <https://github.com/jantman/awslimitchecker/pull/223>`_, released in 0.6.0 on November 11, 2016 was based on `incorrect information <https://github.com/jantman/awslimitchecker/issues/215#issuecomment-259144130>`_ about how Regional Benefit Reserved Instances (RIs) impact the service limit. The code implemented at that time subtracted Regional Benefit RIs from the count of running instances that we use to establish usage. Upon further review, as well as confirmation from AWS Support, some AWS TAMs, and the `relevant AWS documentation <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-reserved-instances.html#ri-limits>`_, only Zonal RIs (AZ-specific) are exempt from the Running On-Demand Instances limit. Regional Benefit RIs are counted the same as any other On-Demand Instances, as they don't have reserved capacity. This release stops subtracting Regional Benefit RIs from the count of Running Instances, which was causing awslimitchecker to report inaccurately low Running Instances usage.

.. _changelog.1_0_0:

1.0.0 (2017-09-21)
------------------

This release **requires new IAM permissions**:

* ``apigateway:GET``
* ``apigateway:HEAD``
* ``apigateway:OPTIONS``
* ``ec2:DescribeVpnGateways``
* ``dynamodb:DescribeLimits``
* ``dynamodb:DescribeTable``
* ``dynamodb:ListTables``

Changes in this release:

* `Issue #254 <https://github.com/jantman/awslimitchecker/issues/254>`_ - Officially adopt SemVer for this project, and document our :ref:`versioning policy <development.versioning_policy>`.
* `Issue #294 <https://github.com/jantman/awslimitchecker/issues/294>`_ - Ignore NAT Gateways that are not in "available" or "pending" state.
* `Issue #253 <https://github.com/jantman/awslimitchecker/issues/253>`_ - Check latest awslimitchecker version on PyPI at class instantiation; log warning if a newer version is available. Add Python API and CLI options to disable this.
* Pin `tox <https://tox.readthedocs.io/>`_ version to 2.7.0 as workaround for parsing change.
* `Issue #292 <https://github.com/jantman/awslimitchecker/issues/292>`_ - Add support for API Gateway limits.
* `PR #302 <https://github.com/jantman/awslimitchecker/pull/302>`_ - Add support for VPC VPN Gateways limit. (Thanks to `andrewmichael <https://github.com/andrewmichael>`_ for the contribution.)
* `Issue #280 <https://github.com/jantman/awslimitchecker/issues/280>`_ / `PR #297 <https://github.com/jantman/awslimitchecker/pull/297>`_ - Add support for DynamoDB limits. (Thanks to `saratlingamarla <https://github.com/saratlingamarla>`_ for the contribution.)

.. _changelog.0_11_0:

0.11.0 (2017-08-06)
-------------------

This release **requires new IAM permissions**:

* ``elasticfilesystem:DescribeFileSystems``
* ``elasticloadbalancing:DescribeAccountLimits``
* ``elasticloadbalancing:DescribeListeners``
* ``elasticloadbalancing:DescribeTargetGroups``
* ``elasticloadbalancing:DescribeRules``

Changes in this release:

* `Issue #287 <https://github.com/jantman/awslimitchecker/issues/287>`_ / `PR #288 <https://github.com/jantman/awslimitchecker/pull/288>`_ - Add support for Elastic Filesystem number of filesystems limit. (Thanks to `nicksantamaria <https://github.com/nicksantamaria>`_ for the contribution.)
* `Issue #268 <https://github.com/jantman/awslimitchecker/issues/268>`_ - Add support for ELBv2 (Application Load Balancer) limits; get ELBv1 (Classic) and ELBv2 (Application) limits from the DescribeAccountLimits API calls.

.. _changelog.0_10_0:

0.10.0 (2017-06-25)
-------------------

This release **removes the ElastiCache Clusters limit**, which no longer exists.

* `Issue #283 <https://github.com/jantman/awslimitchecker/issues/283>`_ - Add gitter.im chat link to README and docs.
* `Issue #282 <https://github.com/jantman/awslimitchecker/issues/282>`_ - versionfinder caused awslimitchecker to die unexpectedly on systems without a ``git`` binary on the PATH. Bump versionfinder requirement to ``>= 0.1.1``.
* `Issue #284 <https://github.com/jantman/awslimitchecker/issues/284>`_ - Fix ElastiCache limits to reflect what AWS Support and the `current documentation <https://docs.aws.amazon.com/general/latest/gr/elasticache-service.html#limits_elasticache>`_ say, instead of a `support ticket from July 2015 <https://github.com/jantman/awslimitchecker/issues/38#issuecomment-118806921>`_.

  * Remove the "Clusters" limit, which no longer exists.
  * "Nodes per Cluster" limit is Memcached only.
  * Add "Subnets per subnet group" limit.

* `Issue #279 <https://github.com/jantman/awslimitchecker/issues/279>`_ - Add Github release to release process.

.. _changelog.0_9_0:

0.9.0 (2017-06-11)
------------------

* `Issue #269 <https://github.com/jantman/awslimitchecker/issues/269>`_ - set Trusted
  Advisor limit name overrides for some RDS limits that were recently added to TA, but
  with different names than what awslimitchecker uses.
* Fix bug `Issue #270 <https://github.com/jantman/awslimitchecker/issues/270>`_ - do
  not count propagated routes towards the VPC "Entries per route table" limit,
  per clarification in `VPC service limits documentation <http://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html#limits_vpc>`_ ("This is the limit
  for the number of non-propagated entries per route table.")
* `PR #276 <https://github.com/jantman/awslimitchecker/pull/276>`_ /
  `Issue #275 <https://github.com/jantman/awslimitchecker/issues/275>`_ - Add new
  ``--skip-service`` CLI option and ``AwsLimitChecker.remove_services`` to allow
  skipping of one or more specific services during runs. (Thanks to `tamsky <https://github.com/tamsky>`_ for this contribution.)
* `PR #274 <https://github.com/jantman/awslimitchecker/pull/274>`_ /
  `Issue #273 <https://github.com/jantman/awslimitchecker/issues/273>`_ - Add support
  for new ``i3`` EC2 Instance types.  (Thanks to `tamsky <https://github.com/tamsky>`_)
  for this contribution.)
* Fix broken docs build due to changes Intersphinx reference to ValueError in python2 docs
* Add hack to ``docs/source/conf.py`` as workaround for https://github.com/sphinx-doc/sphinx/issues/3860
* `Issue #267 <https://github.com/jantman/awslimitchecker/issues/267>`_ - Firehose is only
  available in ``us-east-1``, ``us-west-2`` and ``eu-west-1``. Omit the traceback from the
  log message for Firehose ``EndpointConnectionError`` and log at warning instead of error.

.. _changelog.0_8_0:

0.8.0 (2017-03-11)
------------------

This release includes a **breaking API change**. Please see the first bullet point
below. Note that once 1.0.0 is released (which should be relatively soon), such
API changes will only come with a major version increment.

This release **requires new IAM permissions**: ``redshift:DescribeClusterSnapshots`` and ``redshift:DescribeClusterSubnetGroups``.

This release **removes Python 3.2 support**. This was deprecated in 0.7.0. As of this release,
awslimitchecker may still work on Python 3.2, but it is no longer tested and any support tickets
or bug reports specific to 3.2 will be closed.

* `PR #250 <https://github.com/jantman/awslimitchecker/pull/250>`_ - Allow the
  ``--service`` command line option to accept multiple values. This is a
  **breaking public API change**; the ``awslimitchecker.checker.AwsLimitChecker``
  `check_thresholds <http://awslimitchecker.readthedocs.io/en/latest/awslimitchecker.checker.html#awslimitchecker.checker.AwsLimitChecker.check_thresholds>`_,
  `find_usage <http://awslimitchecker.readthedocs.io/en/latest/awslimitchecker.checker.html#awslimitchecker.checker.AwsLimitChecker.find_usage>`_,
  and `get_limits <http://awslimitchecker.readthedocs.io/en/latest/awslimitchecker.checker.html#awslimitchecker.checker.AwsLimitChecker.get_limits>`_
  methods now take an optional ``service`` *list* keyword argument instead of a *string* for a
  single service name.
* `PR #251 <https://github.com/jantman/awslimitchecker/pull/251>`_ - Handle GovCloud-specific edge cases; specifically, UnsupportedOperation errors
  for EC2 Spot Instance-related API calls, and limits returned as 0 by the DescribeAccountAttributes EC2 API action.
* `PR #249 <https://github.com/jantman/awslimitchecker/pull/249>`_ - Add support for RedShift limits (Redshift subnet groups and Redshift manual snapshots).
  This requires the ``redshift:DescribeClusterSnapshots`` and ``redshift:DescribeClusterSubnetGroups`` IAM permissions.
* `Issue #259 <https://github.com/jantman/awslimitchecker/issues/259>`_ - remove duplicates from required IAM policy returned by ``awslimitchecker.checker.AwsLimitChecker.get_required_iam_policy`` and ``awslimitchecker --iam-policy``.
* Various TravisCI/tox build fixes:

  * Fix pip caching; use default pip cache directory
  * Add python 3.6 tox env and Travis env, now that it's released
  * Switch integration3 tox env from py3.4 to py3.6

* `PR #256 <https://github.com/jantman/awslimitchecker/pull/256>`_ - Add example of wrapping awslimitchecker in a script to send metrics to `Prometheus <https://prometheus.io/>`_.
* `Issue #236 <https://github.com/jantman/awslimitchecker/issues/236>`_ - Drop support for Python 3.2; stop testing under py32.
* `Issue #257 <https://github.com/jantman/awslimitchecker/issues/257>`_ - Handle ElastiCache DescribeCacheCluster responses that are missing ``CacheNodes`` key in a cluster description.
* `Issue #200 <https://github.com/jantman/awslimitchecker/issues/200>`_ - Remove EC2 Spot Instances/Fleets limits from experimental status.
* `Issue #123 <https://github.com/jantman/awslimitchecker/issues/123>`_ - Update documentation on using session tokens (Session or Federation temporary creds).

.. _changelog.0_7_0:

0.7.0 (2017-01-15)
------------------

This release deprecates support for Python 3.2. It will be removed in the
next release.

This release introduces support for automatically refreshing Trusted Advisor
checks on accounts that support this. If you use this new feature,
awslimitchecker will require a new permission, ``trustedadvisor:RefreshCheck``.
See `Getting Started - Trusted Advisor <http://awslimitchecker.readthedocs.io/en/latest/getting_started.html#trusted-advisor>`_ for further information.

* `#231 <https://github.com/jantman/awslimitchecker/issues/231>`_ - add support
  for new f1, r4 and t2.(xlarge|2xlarge) instance types, introduced in November
  2016.
* `#230 <https://github.com/jantman/awslimitchecker/issues/230>`_ - replace the
  built-in ``versioncheck.py`` with `versionfinder <http://versionfinder.readthedocs.io/en/latest/>`_. Remove all of the many versioncheck tests.
* `#233 <https://github.com/jantman/awslimitchecker/issues/233>`_ - refactor
  tests to replace yield-based tests with parametrize, as yield-based tests are
  deprecated and will be removed in pytest 4.
* `#235 <https://github.com/jantman/awslimitchecker/issues/235>`_ - Deprecate
  Python 3.2 support. There don't appear to have been any downloads on py32
  in the last 6 months, and the effort to support it is too high.
* A bunch of Sphinx work to use README.rst in the generated documentation.
* Changed DEBUG-level logging format to include timestamp.
* `#239 <https://github.com/jantman/awslimitchecker/issues/239>`_ - Support
  refreshing Trusted Advisor check results during the run, and optionally waiting
  for refresh to finish. See
  `Getting Started - Trusted Advisor <http://awslimitchecker.readthedocs.io/en/latest/getting_started.html#trusted-advisor>`_
  for further information.
* `#241 <https://github.com/jantman/awslimitchecker/issues/241>`_ / `PR #242 <https://github.com/jantman/awslimitchecker/pull/242>`_ -
  Fix default ElastiCache/Nodes limit from 50 to 100, as that's `now <http://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html#limits_elasticache>`_
  what the docs say.
* `#220 <https://github.com/jantman/awslimitchecker/issues/220>`_ / `PR #243 <https://github.com/jantman/awslimitchecker/pull/243>`_ /
  `PR #245 <https://github.com/jantman/awslimitchecker/pull/245>`_ - Fix for ExpiredTokenException Errors.
  **awslimitchecker.connectable.credentials has been removed.**
  In previous releases, awslimitchecker had been using a ``Connectable.credentials`` class attribute
  to store AWS API credentials and share them between ``Connectable`` subclass instances. The side-effect
  of this was that AWS credentials were set at the start of the Python process and never changed. For users
  taking advantage of the Python API and either using short-lived STS credentials or using long-running
  or threaded implementations, the same credentials persisted for the life of the process, and would often
  result in ExpiredTokenExceptions. The fix was to move
  `_boto_conn_kwargs <http://awslimitchecker.readthedocs.io/en/latest/awslimitchecker.checker.html#awslimitchecker.checker.AwsLimitChecker._boto_conn_kwargs>`_
  and `_get_sts_token <http://awslimitchecker.readthedocs.io/en/latest/awslimitchecker.checker.html#awslimitchecker.checker.AwsLimitChecker._get_sts_token>`_
  from `connectable <http://awslimitchecker.readthedocs.io/en/develop/awslimitchecker.connectable.html>`_ to the top-level
  `AwsLimitChecker <http://awslimitchecker.readthedocs.io/en/latest/awslimitchecker.checker.html#awslimitchecker.checker.AwsLimitChecker>`_
  class itself, get the value of the ``_boto_conn_kwargs`` property in the constructor, and pass that value in to all
  ``Connectable`` subclasses. This means that each instance of AwsLimitChecker has its own unique connection-related kwargs
  and credentials, and constructing a new instance will work intuitively - either use the newly-specified credentials,
  or regenerate STS credentials if configured to use them. I have to extend my deepest gratitude to the folks who
  identified and fixed this issue, specifically `cstewart87 <https://github.com/cstewart87>`_ for the initial
  bug report and description, `aebie <https://github.com/aebie>`_ for the tireless and relentlessly thorough
  investigation and brainstorming and for coordinating work for a fix, and `willusher <https://github.com/willusher>`_
  for the final implementation and dealing (wonderfully) with the dizzying complexity of many of the unit tests
  (and even matching the existing style).

.. _changelog.0_6_0:

0.6.0 (2016-11-12)
------------------

This release has a breaking change. The ``VPC`` ``NAT gateways`` has been renamed
to ``NAT Gateways per AZ`` and its ``get_current_usage()`` method will now return
a list with multiple items. See the changelog entry for #214 below.

This release requires the following new IAM permissions to function:

* ``firehose:ListDeliveryStreams``

* `#217 <https://github.com/jantman/awslimitchecker/issues/217>`_ - add support
  for new/missing EC2 instance types: ``m4.16xlarge``, ``x1.16xlarge``, ``x1.32xlarge``,
  ``p2.xlarge``, ``p2.8xlarge``, ``p2.16xlarge``.
* `#215 <https://github.com/jantman/awslimitchecker/issues/215>`_ - support
  "Regional Benefit" Reserved Instances that have no specific AZ set on them. Per
  AWS, these are exempt from On-Demand Running Instances limits like all other
  RIs.
* `#214 <https://github.com/jantman/awslimitchecker/issues/214>`_ - The VPC "NAT gateways"
  limit incorrectly calculated usage for the entire region, while the limit is
  actually per-AZ. It also had strange capitalization that confused users. The name
  has been changed to "NAT Gateways per AZ" and the usage is now correctly calculated
  per-AZ instead of region-wide.
* `#221 <https://github.com/jantman/awslimitchecker/issues/221>`_ /
  `PR #222 <https://github.com/jantman/awslimitchecker/pull/222>`_ - Fix bug
  in handling of STS Credentials where they are cached permanently in
  ``connectable.Connectable.credentials``, and new AwsLimitChecker instances
  in the same Python process reuse the first set of STS credentials. This is
  fixed by storing the Account ID as part of
  ``connectable.ConnectableCredentials`` and getting new STS creds if the cached
  account ID does not match the current ``account_id`` on the ``Connectable``
  object.
* `PR #216 <https://github.com/jantman/awslimitchecker/pull/216>`_ - add new
  "Firehose" service with support for "Delivery streams per region" limit.
* `#213 <https://github.com/jantman/awslimitchecker/issues/213>`_ /
  `PR #188 <https://github.com/jantman/awslimitchecker/pull/188>`_ - support
  AWS cross-sdk credential file profiles via ``-P`` / ``--profile``, like
  awscli.

.. _changelog.0_5_1:

0.5.1 (2016-09-25)
------------------

This release requires the following new IAM permissions to function:

* ``ec2:DescribeSpot*`` or more specifically:

  * ``ec2:DescribeSpotDatafeedSubscription``
  * ``ec2:DescribeSpotFleetInstances``
  * ``ec2:DescribeSpotFleetRequestHistory``
  * ``ec2:DescribeSpotFleetRequests``
  * ``ec2:DescribeSpotInstanceRequests``
  * ``ec2:DescribeSpotPriceHistory``

* ``ec2:DescribeNatGateways``

* `#51 <https://github.com/jantman/awslimitchecker/issues/51>`_ / PR `#201 <https://github.com/jantman/awslimitchecker/pull/201>`_ - Add experimental support for Spot Instance and Spot Fleet limits (only the ones explicitly documented by AWS). This is currently experimental, as the documentation is not terribly clear or detailed, and the author doesn't have access to any accounts that make use of spot instances. This will be kept experimental until multiple users validate it. For more information, see `the EC2 limit documentation <http://awslimitchecker.readthedocs.io/en/latest/limits.html#ec2>`_.
* `PR #204 <https://github.com/jantman/awslimitchecker/pull/204>`_ contributed by `hltbra <https://github.com/hltbra>`_ to add support for VPC NAT Gateways limit.
* Add README and Docs link to waffle.io board.
* Fix bug where ``--skip-ta`` command line flag was ignored in :py:meth:`~.Runner.show_usage` (when running with ``-u`` / ``--show-usage`` action).
* Add link to `waffle.io Kanban board <https://waffle.io/jantman/awslimitchecker>`_
* `#202 <https://github.com/jantman/awslimitchecker/issues/202>`_ - Adds management of integration test IAM policy via Terraform.
* `#211 <https://github.com/jantman/awslimitchecker/issues/211>`_ - Add working download stats to README and docs
* Fix broken landscape.io badges in README and docs
* `#194 <https://github.com/jantman/awslimitchecker/issues/194>`_ - On Limits page of docs, clarify that Running On-Demand Instances does not include Reserved Instances.
* Multiple ``tox.ini`` changes:

  * simplify integration and unit/versioncheck testenv blocks using factors and reuse
  * py26 testenv was completely unused, and py26-unit was running and working with mock==2.0.0
  * use pytest<3.0.0 in py32 envs

* `#208 <https://github.com/jantman/awslimitchecker/issues/208>`_ - fix KeyError when ``timestamp`` key is missing from TrustedAdvisor check result dict

.. _changelog.0_5_0:

0.5.0 (2016-07-06)
------------------

This release includes a change to ``awslimitchecker``'s Python API. `awslimitchecker.limit.AwsLimit.get_limit <https://awslimitchecker.readthedocs.io/en/latest/awslimitchecker.limit.html#awslimitchecker.limit.AwsLimit.get_limit>`_ can now return either an ``int`` or ``None``, as TrustedAdvisor now lists some service limits as being explicitly "unlimited".

* `#195 <https://github.com/jantman/awslimitchecker/issues/195>`_ - Handle TrustedAdvisor explicitly reporting some limits as "unlimited". This introduces the concept of unlimited limits, where the effective limit is ``None``.

.. _changelog.0_4_4:

0.4.4 (2016-06-27)
------------------

* `PR #190 <https://github.com/jantman/awslimitchecker/pull/19>`_ / `#189 <https://github.com/jantman/awslimitchecker/issues/189>`_ - Add support for EBS st1 and sc1 volume types (adds "EBS/Throughput Optimized (HDD) volume storage (GiB)" and "EBS/Cold (HDD) volume storage (GiB)" limits).

.. _changelog.0_4_3:

0.4.3 (2016-05-08)
------------------

* `PR #184 <https://github.com/jantman/awslimitchecker/pull/184>`_ Fix default VPC/Security groups per VPC limit from 100 to 500, per `VPC limits documentation <http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_Appendix_Limits.html#vpc-limits-security-groups>`_ (this limit was increased at some point recently). Thanks to `Travis Thieman <https://github.com/thieman>`_ for this contribution.

.. _changelog.0_4_2:

0.4.2 (2016-04-27)
------------------

This release requires the following new IAM permissions to function:

* ``elasticbeanstalk:DescribeApplications``
* ``elasticbeanstalk:DescribeApplicationVersions``
* ``elasticbeanstalk:DescribeEnvironments``

* `#70 <https://github.com/jantman/awslimitchecker/issues/70>`_ Add support for ElasicBeanstalk service.
* `#177 <https://github.com/jantman/awslimitchecker/issues/177>`_ Integration tests weren't being properly skipped for PRs.
* `#175 <https://github.com/jantman/awslimitchecker/issues/175>`_ the simplest and most clear contributor license agreement I could come up with.
* `#172 <https://github.com/jantman/awslimitchecker/issues/172>`_ add an integration test running against sa-east-1, which has fewer services than the popular US regions.

.. _changelog.0_4_1:

0.4.1 (2016-03-15)
------------------

* `#170 <https://github.com/jantman/awslimitchecker/issues/170>`_ Critical bug fix in implementation of `#71 <https://github.com/jantman/awslimitchecker/issues/71>`_ - SES only supports three regions (us-east-1, us-west-2, eu-west-1) and causes an unhandled connection error if used in another region.

.. _changelog.0_4_0:

0.4.0 (2016-03-14)
------------------

This release requires the following new IAM permissions to function:

* ``rds:DescribeAccountAttributes``
* ``iam:GetAccountSummary``
* ``s3:ListAllMyBuckets``
* ``ses:GetSendQuota``
* ``cloudformation:DescribeAccountLimits``
* ``cloudformation:DescribeStacks``

Issues addressed:

* `#150 <https://github.com/jantman/awslimitchecker/issues/150>`_ add CHANGES.rst to Sphinx docs
* `#85 <https://github.com/jantman/awslimitchecker/issues/85>`_ and `#154 <https://github.com/jantman/awslimitchecker/issues/154>`_

    * add support for RDS 'DB Clusters' and 'DB Cluster Parameter Groups' limits
    * use API to retrieve RDS limits
    * switch RDS from calculating usage to using the DescribeAccountAttributes usage information, for all limits other than those which are per-resource and need resource IDs (Max auths per security group, Read replicas per master, Subnets per Subnet Group)
    * awslimitchecker now **requires an additional IAM permission**, ``rds:DescribeAccountAttributes``
* `#157 <https://github.com/jantman/awslimitchecker/issues/157>`_ fix for TrustedAdvisor polling multiple times - have TA set an instance variable flag when it updates services after a poll, and skip further polls and updates if the flag is set. Also add an integration test to confirm this.
* `#50 <https://github.com/jantman/awslimitchecker/issues/50>`_ Add support for IAM service with a subset of its limits (Groups, Instance Profiles, Policies, Policy Versions In Use, Roles, Server Certificates, Users), using both limits and usage information from the `GetAccountSummary <http://docs.aws.amazon.com/IAM/latest/APIReference/API_GetAccountSummary.html>`_ API action. This **requires an additional IAM permission**, ``iam:GetAccountSummary``.
* `#48 <https://github.com/jantman/awslimitchecker/issues/48>`_ Add support for S3 Buckets limit. This **requires an additional IAM permission**, ``s3:ListAllMyBuckets``.
* `#71 <https://github.com/jantman/awslimitchecker/issues/71>`_ Add support for SES service (daily sending limit). This **requires an additional IAM permission**, ``ses:GetSendQuota``.
* `#69 <https://github.com/jantman/awslimitchecker/issues/69>`_ Add support for CloudFormation service Stacks limit. This **requires additional IAM permissions**, ``cloudformation:DescribeAccountLimits`` and ``cloudformation:DescribeStacks``.
* `#166 <https://github.com/jantman/awslimitchecker/issues/166>`_ Speed up TravisCI tests by dropping testing for PyPy and PyPy3, and only running the -versioncheck tests for two python interpreters instead of 8.

.. _changelog.0_3_2:

0.3.2 (2016-03-11)
------------------

* `#155 <https://github.com/jantman/awslimitchecker/issues/155>`_ Bug fix for uncaught KeyError on accounts with Trusted Advisor (business-level support and above). This was caused by an undocumented change released by AWS between Thu, 10 Mar 2016 07:00:00 GMT and Fri, 11 Mar 2016 07:00:00 GMT, where five new IAM-related checks were introduced that lack the ``region`` data field (which the `TrustedAdvisorResourceDetail API docs <https://docs.aws.amazon.com/awssupport/latest/APIReference/API_TrustedAdvisorResourceDetail.html>`_ still list as a required field).

.. _changelog.0_3_1:

0.3.1 (2016-03-04)
------------------

* `#117 <https://github.com/jantman/awslimitchecker/issues/117>`_ fix Python 3.5 TravisCI tests and re-enable automatic testing for 3.5.
* `#116 <https://github.com/jantman/awslimitchecker/issues/116>`_ add t2.nano EC2 instance type; fix typo - "m4.8xlarge" should have been "m4.10xlarge"; update default limits for m4.(4|10)xlarge
* `#134 <https://github.com/jantman/awslimitchecker/issues/134>`_ Minor update to project description in docs and setup.py; use only _VERSION (not git) when building in RTD; include short description in docs HTML title; set meta description on docs index.rst.
* `#128 <https://github.com/jantman/awslimitchecker/issues/128>`_ Update Development and Getting Help documentation; add GitHub CONTRIBUTING.md file with link back to docs, as well as Issue and PR templates.
* `#131 <https://github.com/jantman/awslimitchecker/issues/131>`_ Refactor TrustedAdvisor interaction with limits for special naming cases (limits where the TrustedAdvisor service or limit name doesn't match that of the awslimitchecker limit); enable newly-available TrustedAdvisor data for some EC2 on-demand instance usage.

.. _changelog.0_3_0:

0.3.0 (2016-02-18)
------------------

* Add coverage for one code branch introduced in `PR #100 <https://github.com/jantman/awslimitchecker/pull/100>`_ that wasn't covered by tests.
* `#112 <https://github.com/jantman/awslimitchecker/issues/112>`_ fix a bug in the versioncheck integration tests, and a bug uncovered in versioncheck itself, both dealing with checkouts that are on a un-cloned branch.
* `#105 <https://github.com/jantman/awslimitchecker/issues/105>`_ build and upload wheels in addition to sdist
* `#95 <https://github.com/jantman/awslimitchecker/issues/95>`_ **major** refactor to convert AWS client library from `boto <https://github.com/boto/boto>`_ to `boto3 <https://github.com/boto/boto3>`_. This also includes significant changes to the internal connection logic and some of the internal (private) API. Pagination has been moved to boto3 wherever possible, and handling of API request throttling has been removed from awslimitchecker, as boto3 handles this itself. This also introduces full, official support for python3.
* Add separate ``localdocs`` tox env for generating documentation and updating output examples.
* `#113 <https://github.com/jantman/awslimitchecker/issues/113>`_ update, expand and clarify documentation around threshold overrides; ignore some sites from docs linkcheck.
* `#114 <https://github.com/jantman/awslimitchecker/issues/114>`_ expanded automatic integration tests
* **Please note** that version 0.3.0 of awslimitchecker moved from using ``boto`` as its AWS API client to using ``boto3``. This change is mostly transparent, but there is a minor change in how AWS credentials are handled. In ``boto``, if the ``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY`` environment variables were set, and the region was not set explicitly via awslimitchecker, the AWS region would either be taken from the ``AWS_DEFAULT_REGION`` environment variable or would default to us-east-1, regardless of whether a configuration file (``~/.aws/credentials`` or ``~/.aws/config``) was present. With boto3, it appears that the default region from the configuration file will be used if present, regardless of whether the credentials come from that file or from environment variables.

.. _changelog.0_2_3:

0.2.3 (2015-12-16)
------------------

* `PR #100 <https://github.com/jantman/awslimitchecker/pull/100>`_ support MFA tokens when using STS assume role
* `#107 <https://github.com/jantman/awslimitchecker/issues/107>`_ add support to explicitly disable pagination, and use for TrustedAdvisor to prevent pagination warnings

.. _changelog.0_2_2:

0.2.2 (2015-12-02)
------------------

* `#83 <https://github.com/jantman/awslimitchecker/issues/83>`_ remove the "v" prefix from version tags so ReadTheDocs will build them automatically.
* `#21 <https://github.com/jantman/awslimitchecker/issues/21>`_ run simple integration tests of ``-l`` and ``-u`` for commits to main repo branches.

.. _changelog.0_2_1:

0.2.1 (2015-12-01)
------------------

* `#101 <https://github.com/jantman/awslimitchecker/issues/101>`_ Ignore stopped and terminated instances from EC2 Running On-Demand Instances usage count.
* `#47 <https://github.com/jantman/awslimitchecker/issues/47>`_ In VersionCheck git -e tests, explicitly fetch git tags at beginning of test.

.. _changelog.0_2_0:

0.2.0 (2015-11-29)
------------------

* `#86 <https://github.com/jantman/awslimitchecker/issues/86>`_ wrap all AWS API queries in ``awslimitchecker.utils.boto_query_wrapper`` to retry queries with an exponential backoff when API request throttling/rate limiting is encountered
* Attempt at fixing `#47 <https://github.com/jantman/awslimitchecker/issues/47>`_ where versioncheck acceptance tests fail under TravisCI, when testing master after a tagged release (when there's a tag for the current commit)
* Fix `#73 <https://github.com/jantman/awslimitchecker/issues/73>`_ versioncheck.py reports incorrect information when package is installed in a virtualenv inside a git repository
* Fix `#87 <https://github.com/jantman/awslimitchecker/issues/87>`_ run coverage in all unit test Tox environments, not a dedicated env
* Fix `#75 <https://github.com/jantman/awslimitchecker/issues/75>`_ re-enable py26 Travis builds now that `pytest-dev/pytest#1035 <https://github.com/pytest-dev/pytest/issues/1035>`_ is fixed (pytest >= 2.8.3)
* Fix `#13 <https://github.com/jantman/awslimitchecker/issues/13>`_ re-enable Sphinx documentation linkcheck
* Fix `#40 <https://github.com/jantman/awslimitchecker/issues/40>`_ add support for pagination of API responses (to get all results) and handle pagination for all current services
* Fix `#88 <https://github.com/jantman/awslimitchecker/issues/88>`_ add support for API-derived limits. This is a change to the public API for ``awslimitchecker.limit.AwsLimit`` and the CLI output.
* Fix `#72 <https://github.com/jantman/awslimitchecker/issues/72>`_ add support for some new limits returned by Trusted Advisor. This renames the following limits:
  * ``EC2/EC2-VPC Elastic IPs`` to ``EC2/VPC Elastic IP addresses (EIPs)``
  * ``RDS/Read Replicas per Master`` to ``RDS/Read replicas per master``
  * ``RDS/Parameter Groups`` to ``RDS/DB parameter groups``
* Fix `#84 <https://github.com/jantman/awslimitchecker/issues/84>`_ pull some EC2 limits from the API's DescribeAccountAttributes action
* Fix `#94 <https://github.com/jantman/awslimitchecker/issues/94>`_ pull AutoScaling limits from the API's DescribeAccountLimits action
* Add ``autoscaling:DescribeAccountLimits`` and ``ec2:DescribeAccountAttributes`` to required IAM permissions.
* Ignore ``AccountLimits`` objects from result pagination

.. _changelog.0_1_3:

0.1.3 (2015-10-04)
------------------

* Update trove classifier Development Status in setup.py to Beta
* Fix markup formatting issue in ``docs/source/getting_started.rst``
* temporarily disable py26 testenv in Travis; failing due to upstream bug https://github.com/pytest-dev/pytest/issues/1035
* `PR #64 <https://github.com/jantman/awslimitchecker/pull/64>`_ and `#68 <https://github.com/jantman/awslimitchecker/issues/68>`_ -
  support [STS](http://docs.aws.amazon.com/STS/latest/APIReference/Welcome.html) and regions
  * Add support for passing in a region to connect to via ``-r`` / ``--region``
  * Add support for using STS to check resources in another account, including support for ``external_id``
  * Major refactor of how service classes connect to AWS API
* `#74 <https://github.com/jantman/awslimitchecker/issues/74>`_ add support for EC2 t2.large instance type
* `#65 <https://github.com/jantman/awslimitchecker/issues/65>`_ handle case where ElastiCache API returns CacheCluster response with CacheNodes None
* `#63 <https://github.com/jantman/awslimitchecker/issues/63>`_ update Python usage documentation
* `#49 <https://github.com/jantman/awslimitchecker/issues/49>`_ clean up badges in README.rst and sphinx index.rst; PyPi downloads and version badges broken (switch to shields.io)
* `#67 <https://github.com/jantman/awslimitchecker/issues/67>`_ fix typo in required IAM policy; comma missing in list returned from `_Ec2Service.required_iam_permissions()`
* `#76 <https://github.com/jantman/awslimitchecker/issues/76>`_ default limits for EBS volume usage were in TiB not GiB, causing invalid default limits on accounts without Trusted Advisor
* Changes to some tests in ``test_versioncheck.py`` to aid in debugging `#47 <https://github.com/jantman/awslimitchecker/issues/47>`_ where Travis tests fail on master because of git tag from release (if re-run after release)

.. _changelog.0_1_2:

0.1.2 (2015-08-13)
------------------

* `#62 <https://github.com/jantman/awslimitchecker/issues/62>`_ - For 'RDS/DB snapshots per user' limit, only count manual snapshots. (fix bug in fix for `#54 <https://github.com/jantman/awslimitchecker/issues/54>`_)

.. _changelog.0_1_1:

0.1.1 (2015-08-13)
------------------

* `#54 <https://github.com/jantman/awslimitchecker/issues/54>`_ - For 'RDS/DB snapshots per user' limit, only count manual snapshots.
* `PR #58 <https://github.com/jantman/awslimitchecker/pull/58>`_ - Fix issue where BotoServerError exception is unhandled when checking ElastiCache limits on new accounts without EC2-Classic.
* `#55 <https://github.com/jantman/awslimitchecker/issues/55>`_ - use .version instead of .parsed_version to fix version information when using pip<6
* `#46 <https://github.com/jantman/awslimitchecker/issues/46>`_ - versioncheck integration test fixes
  * Rename ``-integration`` tox environments to ``-versioncheck``
  * Skip versioncheck git install integration tests on PRs, since they'll fail
* `#56 <https://github.com/jantman/awslimitchecker/issues/56>`_ - logging fixes
  * change the AGPL warning message to write directly to STDERR instead of logging
  * document logging configuration for library use
  * move boto log suppression from checker to runner
* Add contributing docs

.. _changelog.0_1_0:

0.1.0 (2015-07-25)
------------------

* initial released version
