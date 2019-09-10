.. _docker:

Docker Usage
============

As of version 7.1.0, awslimitchecker now ships an official Docker image that can
be used instead of installing locally. This image should be suitable both for
using locally or using in a Docker-based system such as AWS ECS.

.. _docker.versions:

Versions / Tags
---------------

awslimitchecker has a documented :ref:`versioning policy <development.versioning_policy>`
intended to prevent your installation from unexpectedly breaking because of changes.
It is up to you to decide whether you'd rather have stability at the expense of not
receiving bug fixes and feature additions as soon as possible, or receive updates
as soon as possible but risk awslimitchecker execution failing without manual intervention.

For each ``X.Y.Z`` release version, four Docker images are created with the following tags:

* ``latest``
* ``X.Y.Z``
* ``X.Y``
* ``X``

Note that only the full ``X.Y.Z`` tag is immutable; the other tags will be updated
with subsequent releases.

These tags allow you to specify a Docker image for your particular desired balance of
stability vs updates, according to the :ref:`versioning policy <development.versioning_policy>`.

.. _docker.usage:

Basic Usage
-----------

The Docker image uses the ``awslimitchecker`` CLI as an entrypoint, so you need
only to specify the arguments that you would normally pass to the ``awslimitchecker``
command for :ref:`cli_usage`. For example, to show help:

.. code-block:: console

    $ docker run jantman/awslimitchecker --help
    usage: awslimitchecker [-h] [-S [SERVICE [SERVICE ...]]]
                       [--skip-service SKIP_SERVICE] [--skip-check SKIP_CHECK]
                       [-s] [-l] [--list-defaults] [-L LIMIT] [-u]
                       [--iam-policy] [-W WARNING_THRESHOLD]
                       [-C CRITICAL_THRESHOLD] [-P PROFILE_NAME]
                       [-A STS_ACCOUNT_ID] [-R STS_ACCOUNT_ROLE]
                       [-E EXTERNAL_ID] [-M MFA_SERIAL_NUMBER] [-T MFA_TOKEN]
                       [-r REGION] [--skip-ta]
                       [--ta-refresh-wait | --ta-refresh-trigger | --ta-refresh-older TA_REFRESH_OLDER]
                       [--ta-refresh-timeout TA_REFRESH_TIMEOUT] [--no-color]
                       [--no-check-version] [-v] [-V]

    Report on AWS service limits and usage via boto3, optionally warn about any
    services with usage nearing or exceeding their limits. For further help, see
    <http://awslimitchecker.readthedocs.org/>

    optional arguments:
    -h, --help            show this help message and exit
    -S [SERVICE [SERVICE ...]], --service [SERVICE [SERVICE ...]]
                        perform action for only the specified service name;
                        see -s|--list-services for valid names
    --skip-service SKIP_SERVICE
                        avoid performing actions for the specified service
                        name; see -s|--list-services for valid names
    --skip-check SKIP_CHECK
                        avoid performing actions for the specified check name
    -s, --list-services   print a list of all AWS service types that
                        awslimitchecker knows how to check
    -l, --list-limits     print all AWS effective limits in
                        "service_name/limit_name" format
    --list-defaults       print all AWS default limits in
                        "service_name/limit_name" format
    -L LIMIT, --limit LIMIT
                        override a single AWS limit, specified in
                        "service_name/limit_name=value" format; can be
                        specified multiple times.
    -u, --show-usage      find and print the current usage of all AWS services
                        with known limits
    --iam-policy          output a JSON serialized IAM Policy listing the
                        required permissions for awslimitchecker to run
                        correctly.
    -W WARNING_THRESHOLD, --warning-threshold WARNING_THRESHOLD
                        default warning threshold (percentage of limit);
                        default: 80
    -C CRITICAL_THRESHOLD, --critical-threshold CRITICAL_THRESHOLD
                        default critical threshold (percentage of limit);
                        default: 99
    -P PROFILE_NAME, --profile PROFILE_NAME
                        Name of profile in the AWS cross-sdk credentials file
                        to use credentials from; similar to the corresponding
                        awscli option
    -A STS_ACCOUNT_ID, --sts-account-id STS_ACCOUNT_ID
                        for use with STS, the Account ID of the destination
                        account (account to assume a role in)
    -R STS_ACCOUNT_ROLE, --sts-account-role STS_ACCOUNT_ROLE
                        for use with STS, the name of the IAM role to assume
    -E EXTERNAL_ID, --external-id EXTERNAL_ID
                        External ID to use when assuming a role via STS
    -M MFA_SERIAL_NUMBER, --mfa-serial-number MFA_SERIAL_NUMBER
                        MFA Serial Number to use when assuming a role via STS
    -T MFA_TOKEN, --mfa-token MFA_TOKEN
                        MFA Token to use when assuming a role via STS
    -r REGION, --region REGION
                        AWS region name to connect to; required for STS
    --skip-ta             do not attempt to pull *any* information on limits
                        from Trusted Advisor
    --ta-refresh-wait     If applicable, refresh all Trusted Advisor limit-
                        related checks, and wait for the refresh to complete
                        before continuing.
    --ta-refresh-trigger  If applicable, trigger refreshes for all Trusted
                        Advisor limit-related checks, but do not wait for them
                        to finish refreshing; trigger the refresh and continue
                        on (useful to ensure checks are refreshed before the
                        next scheduled run).
    --ta-refresh-older TA_REFRESH_OLDER
                        If applicable, trigger refreshes for all Trusted
                        Advisor limit-related checks with results more than
                        this number of seconds old. Wait for the refresh to
                        complete before continuing.
    --ta-refresh-timeout TA_REFRESH_TIMEOUT
                        If waiting for TA checks to refresh, wait up to this
                        number of seconds before continuing on anyway.
    --no-color            do not colorize output
    --no-check-version    do not check latest version at startup
    -v, --verbose         verbose output. specify twice for debug-level output.
    -V, --version         print version number and exit.

    awslimitchecker is AGPLv3-licensed Free Software. Anyone using this program,
    even remotely over a network, is entitled to a copy of the source code. Use
    `--version` for information on the source code location.

Or to show the current limits for the ELB service, when using credentials from environment variables:

.. code-block:: console

    $ docker run -e AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN jantman/awslimitchecker -l -S ELB
    ELB/Application load balancers                  1500 (API)
    ELB/Certificates per application load balancer  25
    ELB/Classic load balancers                      1500 (API)
    ELB/Listeners per application load balancer     50 (API)
    ELB/Listeners per load balancer                 100 (API)
    ELB/Listeners per network load balancer         50 (API)
    ELB/Network load balancers                      20 (API)
    ELB/Registered instances per load balancer      1000 (API)
    ELB/Rules per application load balancer         100 (API)
    ELB/Target groups                               3000 (API)

    awslimitchecker 7.0.0 is AGPL-licensed free software; all users have a right to the full source code of this version. See <https://github.com/jantman/awslimitchecker>

.. _docker.credentials:

AWS Credentials
---------------

Running awslimitchecker in docker may make it slightly more difficult to provide
your AWS credentials. In general, you will have to use one of the following methods,
depending on where your credentials are located.

.. _docker.credentials_env:

AWS Credential Environment Variables
++++++++++++++++++++++++++++++++++++

If your AWS credentials are currently set as environment variables, you will need
to explicitly pass those in to the container:

.. code-block:: console

    $ docker run \
        -e AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION \
        -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
        -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
        -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
        jantman/awslimitchecker --version

.. _docker.credentials_file:

AWS Credentials File
++++++++++++++++++++

If your AWS credentials are currently set in the AWS Credentials File
(at ``~/.aws/credentials``), you will need to mount that in to the container
at ``/root/.aws/credentials``:

.. code-block:: console

    $ docker run \
        -v $(readlink -f ~/.aws/credentials):/root/.aws/credentials \
        jantman/awslimitchecker --version

.. _docker.network_credentials:

EC2 Instance Profile or Task Role Credentials
++++++++++++++++++++++++++++++++++++++++++++++++++++++

For credentials provided via an EC2 Instance Profile (Role) or an ECS Task Role,
they should be automatically recognized so long as nothing is explicitly blocking
Docker containers from accessing them. You may still need to set the ``AWS_DEFAULT_REGION``
environment variable for the container.

.. _docker.fargate:

Deployment on ECS Fargate using Terraform
-----------------------------------------

An example terraform module, and an example of using the module, to deploy Dockerized
awslimitchecker on ECS Fargate with the PagerDuty :ref:`alert provider <cli_usage.alerts>`
and the Datadog :ref:`metrics store <cli_usage.metrics>`, along with an example Datadog
monitor to detect if awslimitchecker hasn't run in over a day, is available in the
GitHub repo at: `https://github.com/jantman/awslimitchecker/tree/master/docs/examples/terraform-fargate <https://github.com/jantman/awslimitchecker/tree/master/docs/examples/terraform-fargate>`__
