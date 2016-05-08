Changelog
=========

Pre-release (develop branch)
----------------------------

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
