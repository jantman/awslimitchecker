Changelog
=========

Pre-release (develop branch)
----------------------------

* Update trove classifier Development Status in setup.py to Beta
* Fix markup formatting issue in ``docs/source/getting_started.rst``
* temporarily disable py26 testenv in Travis; failing due to upstream bug https://github.com/pytest-dev/pytest/issues/1035
* `PR #64 <https://github.com/jantman/awslimitchecker/pull/64>`_ and `#68 <https://github.com/jantman/awslimitchecker/issues/68>`_ -
  support [STS](http://docs.aws.amazon.com/STS/latest/APIReference/Welcome.html) and regions
  * Add support for passing in a region to connect to via ``-r`` / ``--region``
  * Add support for using STS to check resources in another account, including support for ``external_id``
  * Major refactor of how service classes connect to AWS API

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
