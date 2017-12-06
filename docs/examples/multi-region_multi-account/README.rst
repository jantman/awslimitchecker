awslimitchecker multi-region multi-account wrapper example
==========================================================

This is an example of a multi-region, multi-account wrapper script for awslimitchecker,
based on the one currently in use at my employer. It supports limit and threshold overrides,
per-account roles to assume with a pattern-based default, account names (hard-coded in the
config in case you don't want to or can't call
`IAM ListAccountAliases <http://docs.aws.amazon.com/IAM/latest/APIReference/API_ListAccountAliases.html>`_),
and running for a specified subset of all accounts if desired.

This is intended as an example only, and certainly could be improved on. However, given the needs of different
organizations (how to assume roles, how configuration is stored, how to notify/alert on the output, whether
alerts for different accounts go to different destinations or have different levels of urgency, etc.) I don't
think it's within the scope of awslimitchecker to either develop an "official" solution for this or include
it in the core of the software. In the author's experience, the three employers he's used awslimitchecker at
all had very different needs around configuration and alerting on the final output.

Configuration
-------------

This example uses a nested directory structure and JSON configuration files. It uses a single class
(``Config``) to read the files from disk and build the configuration, so you could just as easily
replace that class with one that reads from a single file, a key/value store, a database, etc.

The general config layout is as follows:

.. code-block::

    config/
      ACCOUNT-NUMBER/
        config.json (account name, IAM role, etc.)
        REGION_NAME/
          limit_overrides.json
          threshold_overrides.json
        ...

* Accounts are enumerated by listing directories under ``config/`` with names matching ``^[0-9]+$``
* Account-wide configuration (account name and IAM role to assume, if not the default) is in ``config.json`` under each account
* The regions to run for each account are found by listing the subdirectories under the account directory.

  * If ``limit_overrides.json`` and/or ``threshold_overrides.json`` are present for a region, the overrides are set according to that file.
  * If a region has no overrides, the directory should be empty or the override files should contain empty objects/dicts.

Per-Account config.json Schema
++++++++++++++++++++++++++++++

* ``name`` - (string) A name to use for this account. We could call `iam:ListAccountAliases <http://docs.aws.amazon.com/IAM/latest/APIReference/API_ListAccountAliases.html>`_ to get the account Alias that AWS knows, but temporary credentials generated `with sts:GetFederationToken or sts:GetSessionToken <http://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp_request.html#stsapi_comparison>`_ may not be able to call IAM APIs, and some organizations may not allow cross-account roles to call IAM APIs. So, we hard-code an account name in our configs. If calling ``ListAccountAliases`` works for you, you may wish to modify this code accordingly.
* ``role_name`` - (string) The **Name** (just the name, not full ARN) of a role to assume to get access to the account. This should only be specified if you need to override the default role name specified in the ``ROLE_NAME`` constant near the top of ``alc_multi_account.py``. If you set this to ``null`` in the JSON, no role will be assumed and all checks will be run against the current account.

Usage
-----

To run for everything:

.. code-block:: bash

    $ ./alc_multi_account.py

    111111111111 (accountOne) us-east-1
        EBS 'Active snapshots' usage (8020) exceeds warning threshold (limit=10000)
        EBS 'Active volumes' usage (4998) exceeds critical threshold (limit=5000)

    111111111111 (accountOne) us-west-2
        No problems found.

    222222222222 (accountTwo) eu-central-1
        RDS 'DB Clusters' usage (39) exceeds critical threshold (limit=40)

    PROBLEMS FOUND. See above output for details.

To run for one account named "accountOne":

.. code-block:: bash

    $ ./alc_multi_account.py accountOne

    111111111111 (accountOne) us-east-1
        EBS 'Active snapshots' usage (8020) exceeds warning threshold (limit=10000)
        EBS 'Active volumes' usage (4998) exceeds critical threshold (limit=5000)

    111111111111 (accountOne) us-west-2
        No problems found.

    PROBLEMS FOUND. See above output for details.

To run for all accounts in one region (eu-central-1):

.. code-block:: bash

    $ ./alc_multi_account.py -r eu-central-1

    Account 111111111111 is not configured for region eu-central-1

    222222222222 (accountTwo) eu-central-1
        RDS 'DB Clusters' usage (39) exceeds critical threshold (limit=40)

    PROBLEMS FOUND. See above output for details.
