Changelog
=========

Pre-release (develop branch)
----------------------------

* #54 - For 'RDS/DB snapshots per user' limit, only count manual snapshots.
* PR #58 - Fix issue where BotoServerError exception is unhandled when checking ElastiCache limits on new accounts without EC2-Classic.
* #55 - use .version instead of .parsed_version to fix version information when using pip<6
* #46 - versioncheck integration test fixes
  * Rename ``-integration`` tox environments to ``-versioncheck``
  * Skip versioncheck git install integration tests on PRs, since they'll fail
* #56 - logging fixes
  * change the AGPL warning message to write directly to STDERR instead of logging
  * document logging configuration for library use
  * move boto log suppression from checker to runner

0.1.0 (2015-07-25)
------------------

* initial released version
