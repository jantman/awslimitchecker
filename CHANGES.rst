Changelog
=========

Unreleased Changes
------------------

* Update README with correct boto version requirement. (Thanks to `nadlerjessie <https://github.com/nadlerjessie>`_ for the contribution.)
* Update minimum ``boto3`` version requirement from 1.2.3 to 1.4.4; the code for `Issue #268 <https://github.com/jantman/awslimitchecker/issues/268>`_ released in 0.11.0 requires boto3 >= 1.4.4 to make the ElasticLoadBalancing ``DescribeAccountLimits`` call.
* **Bug fix for "Running On-Demand EC2 instances" limit** - `Issue #308 <https://github.com/jantman/awslimitchecker/issues/308>`_ - The fix for `Issue #215 <https://github.com/jantman/awslimitchecker/issues/215>`_ / `PR #223 <https://github.com/jantman/awslimitchecker/pull/223>`_, released in 0.6.0 on November 11, 2016 was based on `incorrect information <https://github.com/jantman/awslimitchecker/issues/215#issuecomment-259144130>`_ about how Regional Benefit Reserved Instances (RIs) impact the service limit. The code implemented at that time subtracted Regional Benefit RIs from the count of running instances that we use to establish usage. Upon further review, as well as confirmation from AWS Support, some AWS TAMs, and the `relevant AWS documentation <http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-reserved-instances.html#ri-limits>`_, only Zonal RIs (AZ-specific) are exempt from the Running On-Demand Instances limit. Regional Benefit RIs are counted the same as any other On-Demand Instances, as they don't have reserved capacity. This release stops subtracting Regional Benefit RIs from the count of Running Instances, which was causing awslimitchecker to report inaccurately low Running Instances usage.

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

0.10.0 (2017-06-25)
-------------------

This release **removes the ElastiCache Clusters limit**, which no longer exists.

* `Issue #283 <https://github.com/jantman/awslimitchecker/issues/283>`_ - Add gitter.im chat link to README and docs.
* `Issue #282 <https://github.com/jantman/awslimitchecker/issues/282>`_ - versionfinder caused awslimitchecker to die unexpectedly on systems without a ``git`` binary on the PATH. Bump versionfinder requirement to ``>= 0.1.1``.
* `Issue #284 <https://github.com/jantman/awslimitchecker/issues/284>`_ - Fix ElastiCache limits to reflect what AWS Support and the `current documentation <http://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html#limits_elasticache>`_ say, instead of a `support ticket from July 2015 <https://github.com/jantman/awslimitchecker/issues/38#issuecomment-118806921>`_.

  * Remove the "Clusters" limit, which no longer exists.
  * "Nodes per Cluster" limit is Memcached only.
  * Add "Subnets per subnet group" limit.

* `Issue #279 <https://github.com/jantman/awslimitchecker/issues/279>`_ - Add Github release to release process.

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

0.5.0 (2016-07-06)
------------------

This release includes a change to ``awslimitchecker``'s Python API. `awslimitchecker.limit.AwsLimit.get_limit <https://awslimitchecker.readthedocs.io/en/latest/awslimitchecker.limit.html#awslimitchecker.limit.AwsLimit.get_limit>`_ can now return either an ``int`` or ``None``, as TrustedAdvisor now lists some service limits as being explicitly "unlimited".

* `#195 <https://github.com/jantman/awslimitchecker/issues/195>`_ - Handle TrustedAdvisor explicitly reporting some limits as "unlimited". This introduces the concept of unlimited limits, where the effective limit is ``None``.

0.4.4 (2016-06-27)
------------------

* `PR #190 <https://github.com/jantman/awslimitchecker/pull/19>`_ / `#189 <https://github.com/jantman/awslimitchecker/issues/189>`_ - Add support for EBS st1 and sc1 volume types (adds "EBS/Throughput Optimized (HDD) volume storage (GiB)" and "EBS/Cold (HDD) volume storage (GiB)" limits).

0.4.3 (2016-05-08)
------------------

* `PR #184 <https://github.com/jantman/awslimitchecker/pull/184>`_ Fix default VPC/Security groups per VPC limit from 100 to 500, per `VPC limits documentation <http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_Appendix_Limits.html#vpc-limits-security-groups>`_ (this limit was increased at some point recently). Thanks to `Travis Thieman <https://github.com/thieman>`_ for this contribution.

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

0.4.1 (2016-03-15)
------------------

* `#170 <https://github.com/jantman/awslimitchecker/issues/170>`_ Critical bug fix in implementation of `#71 <https://github.com/jantman/awslimitchecker/issues/71>`_ - SES only supports three regions (us-east-1, us-west-2, eu-west-1) and causes an unhandled connection error if used in another region.

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

0.3.2 (2016-03-11)
------------------

* `#155 <https://github.com/jantman/awslimitchecker/issues/155>`_ Bug fix for uncaught KeyError on accounts with Trusted Advisor (business-level support and above). This was caused by an undocumented change released by AWS between Thu, 10 Mar 2016 07:00:00 GMT and Fri, 11 Mar 2016 07:00:00 GMT, where five new IAM-related checks were introduced that lack the ``region`` data field (which the `TrustedAdvisorResourceDetail API docs <https://docs.aws.amazon.com/awssupport/latest/APIReference/API_TrustedAdvisorResourceDetail.html>`_ still list as a required field).

0.3.1 (2016-03-04)
------------------

* `#117 <https://github.com/jantman/awslimitchecker/issues/117>`_ fix Python 3.5 TravisCI tests and re-enable automatic testing for 3.5.
* `#116 <https://github.com/jantman/awslimitchecker/issues/116>`_ add t2.nano EC2 instance type; fix typo - "m4.8xlarge" should have been "m4.10xlarge"; update default limits for m4.(4|10)xlarge
* `#134 <https://github.com/jantman/awslimitchecker/issues/134>`_ Minor update to project description in docs and setup.py; use only _VERSION (not git) when building in RTD; include short description in docs HTML title; set meta description on docs index.rst.
* `#128 <https://github.com/jantman/awslimitchecker/issues/128>`_ Update Development and Getting Help documentation; add GitHub CONTRIBUTING.md file with link back to docs, as well as Issue and PR templates.
* `#131 <https://github.com/jantman/awslimitchecker/issues/131>`_ Refactor TrustedAdvisor interaction with limits for special naming cases (limits where the TrustedAdvisor service or limit name doesn't match that of the awslimitchecker limit); enable newly-available TrustedAdvisor data for some EC2 on-demand instance usage.

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

0.2.3 (2015-12-16)
------------------

* `PR #100 <https://github.com/jantman/awslimitchecker/pull/100>`_ support MFA tokens when using STS assume role
* `#107 <https://github.com/jantman/awslimitchecker/issues/107>`_ add support to explicitly disable pagination, and use for TrustedAdvisor to prevent pagination warnings

0.2.2 (2015-12-02)
------------------

* `#83 <https://github.com/jantman/awslimitchecker/issues/83>`_ remove the "v" prefix from version tags so ReadTheDocs will build them automatically.
* `#21 <https://github.com/jantman/awslimitchecker/issues/21>`_ run simple integration tests of ``-l`` and ``-u`` for commits to main repo branches.

0.2.1 (2015-12-01)
------------------

* `#101 <https://github.com/jantman/awslimitchecker/issues/101>`_ Ignore stopped and terminated instances from EC2 Running On-Demand Instances usage count.
* `#47 <https://github.com/jantman/awslimitchecker/issues/47>`_ In VersionCheck git -e tests, explicitly fetch git tags at beginning of test.

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

0.1.2 (2015-08-13)
------------------

* `#62 <https://github.com/jantman/awslimitchecker/issues/62>`_ - For 'RDS/DB snapshots per user' limit, only count manual snapshots. (fix bug in fix for `#54 <https://github.com/jantman/awslimitchecker/issues/54>`_)

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

0.1.0 (2015-07-25)
------------------

* initial released version
