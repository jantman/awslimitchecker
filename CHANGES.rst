Changelog
=========

Pre-release (develop branch)
----------------------------

* #54 - For 'RDS/DB snapshots per user' limit, only count manual snapshots.
* PR #58 - Fix issue where BotoServerError exception is unhandled when checking ElastiCache limits on new accounts without EC2-Classic.
* #46 - Rename ``-integration`` tox environments to ``-versioncheck`` and disable on Travis; update development docs to run these manually.

0.1.0 (2015-07-25)
------------------

* initial released version
