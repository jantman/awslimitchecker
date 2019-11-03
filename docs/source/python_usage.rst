
.. _python_usage:

Python Usage
=============

The full feature set of awslimitchecker is available through the Python API.
This page attempts to document some examples of usage, but the best resources are
:py:mod:`~.runner`, the command line wrapper, and the
:ref:`API documentation <modindex>`.

Full Jenkins Example
---------------------

A full example of a wrapper script with limit and threshold overrides, and a Jenkins job to run it,
is available in the ``docs/examples`` directory of awslimitchecker.

See `docs/examples/README.rst on GitHub <https://github.com/jantman/awslimitchecker/blob/master/docs/examples/README.rst>`_.

Simple Examples
----------------

Many of these examples use :py:mod:`pprint` to make output a bit nicer.

Instantiating the Class
++++++++++++++++++++++++

Here we import and instantiate the :py:class:`~.AwsLimitChecker` class; note that we also setup
Python's :py:mod:`logging` module, which is used by ``awslimitchecker``.
We also import :py:mod:`pprint` to make the output nicer.

.. code-block:: pycon

   >>> import logging
   >>> logging.basicConfig()
   >>> logger = logging.getLogger()
   >>>
   >>> from awslimitchecker.checker import AwsLimitChecker
   >>> c = AwsLimitChecker()

Specifying a Region
+++++++++++++++++++

To specify a region ("us-west-2" in this example), specify it as the ``region`` string
parameter to the class constructor:

.. code-block:: pycon

   >>> import logging
   >>> logging.basicConfig()
   >>> logger = logging.getLogger()
   >>>
   >>> from awslimitchecker.checker import AwsLimitChecker
   >>> c = AwsLimitChecker(region='us-west-2')

Refreshing Trusted Advisor Check Results
++++++++++++++++++++++++++++++++++++++++

Trusted Advisor check refresh behavior is controlled by the ``ta_refresh_mode``
and ``ta_refresh_timeout`` parameters on the :py:class:`~awslimitchecker.checker.AwsLimitChecker`
constructor, which are passed through to the :py:class:`~awslimitchecker.trustedadvisor.TrustedAdvisor`
constructor. See :ref:`Internals - Trusted Advisor <internals.trusted_advisor>`
for details of their possible values and meanings.

The below example shows constructing an :py:class:`~awslimitchecker.checker.AwsLimitChecker`
class that will refresh Trusted Advisor limit checks only if their data is at least
6 hours (21600 seconds) old, and will allow up to 30 minutes (1800 seconds) for
the refresh to complete (if it times out, awslimitchecker will continue on with
the old data):

.. code-block:: pycon

   >>> import logging
   >>> logging.basicConfig()
   >>> logger = logging.getLogger()
   >>>
   >>> from awslimitchecker.checker import AwsLimitChecker
   >>> c = AwsLimitChecker(ta_refresh_mode=21600, ta_refresh_timeout=1800)

Assuming a Role with STS
++++++++++++++++++++++++

To check limits for another account using a Role assumed via `STS <http://docs.aws.amazon.com/STS/latest/APIReference/Welcome.html>`_,
specify the ``region``, ``account_id`` and ``account_role`` parameters to the class constructor. If an external ID is needed,
this can be specified by the ``external_id`` parameter. All are strings:

.. code-block:: pycon

   >>> import logging
   >>> logging.basicConfig()
   >>> logger = logging.getLogger()
   >>>
   >>> from awslimitchecker.checker import AwsLimitChecker
   >>> c = AwsLimitChecker(
   >>>     region='us-west-2',
   >>>     account_id='012345678901',
   >>>     account_role='myRoleName',
   >>>     external_id='myid'
   >>> )

.. _python_usage.limit_overrides:

Setting a Limit Override
+++++++++++++++++++++++++

Override EC2's "EC2-Classic Elastic IPs" limit from its default to 20,
using :py:meth:`~.AwsLimitChecker.set_limit_override`.

.. code-block:: pycon

   >>> c.set_limit_override('EC2', 'EC2-Classic Elastic IPs', 20)

.. _python_usage.threshold_overrides:

Setting a Threshold Override
++++++++++++++++++++++++++++

``awslimitchecker`` has two sets of thresholds, warning and critical (intended to be used to
trigger different levels of alert/alarm or action). The default thresholds for warning and critical
are 80% and 99%, respectively; these program-wide defaults can be overridden by passing the
``warning_threshold`` and/or ``critical_threshold`` arguments to the :py:class:`~.AwsLimitChecker`
class constructor.

It is also possible to override these values on a per-limit basis, using the AwsLimitChecker
class's :py:meth:`~.AwsLimitChecker.set_threshold_override` (single limit's threshold override)
and :py:meth:`~.AwsLimitChecker.set_threshold_overrides` (dict of overrides) methods. When setting
threshold overrides, you can specify not only the percent threshold, but also a ``count`` of usage;
any limits which have a usage of more than this number will be detected as a warning or critical,
respectively.

To warn when our ``EC2-Classic Elastic IPs`` usage is above 50% (as opposed to the default of 80%)
and store a critical alert when it's above 75% (as opposed to 99%):

.. code-block:: pycon

   >>> c.set_threshold_override('EC2', 'EC2-Classic Elastic IPs', warn_percent=50, crit_percent=75)

Another use could be to warn when certain services are used at all. As of the time of writing, the
i2.8xlarge instances cost USD $6.82/hour, or $163/day.

To report a critical status if *any* i2.8xlarge instances are running:

.. code-block:: pycon

   >>> c.set_threshold_override('EC2', 'Running On-Demand i2.8xlarge instances', crit_count=1)

You do not need to also override the percent thresholds. Because of how :py:meth:`~.AwsLimitChecker.check_thresholds`
evaluates thresholds, *any* crossed threshold will be considered an error condition.

Checking Thresholds
++++++++++++++++++++

To check the current usage against limits, use :py:meth:`~.AwsLimitChecker.check_thresholds`. The
return value is a nested dict of all limits with current usage meeting or exceeding the configured thresholds.
Keys are the AWS Service names (string), values are dicts of limit name (string) to :py:class:`~.AwsLimit`
instances representing the limit and its current usage.

.. code-block:: pycon

   >>> result = c.check_thresholds()
   >>> pprint.pprint(result)
   {'EC2': {'Magnetic volume storage (TiB)': <awslimitchecker.limit.AwsLimit object at 0x7f398db62750>,
            'Running On-Demand EC2 instances': <awslimitchecker.limit.AwsLimit object at 0x7f398db55910>,
            'Running On-Demand m3.medium instances': <awslimitchecker.limit.AwsLimit object at 0x7f398db55a10>,
            'Security groups per VPC': <awslimitchecker.limit.AwsLimit object at 0x7f398db62790>}}

Looking at one of the entries, its :py:meth:`~.AwsLimit.get_warnings` method tells us that the usage
did not exceed its warning threshold:

.. code-block:: pycon

   >>> result['EC2']['Magnetic volume storage (TiB)'].get_warnings()
   []

But its :py:meth:`~.AwsLimit.get_criticals` method tells us that it did meet or exceed the critical threshold:

.. code-block:: pycon

   >>> result['EC2']['Magnetic volume storage (TiB)'].get_criticals()
   [<awslimitchecker.limit.AwsLimitUsage object at 0x7f2074dfeed0>]

We can then inspect the :py:class:`~.AwsLimitUsage` instance for more information about current usage
that crossed the threshold:

In this particular case, there is no resource ID associated with the usage, because it is an aggregate
(type-, rather than resource-specific) limit:

.. code-block:: pycon

   >>> result['EC2']['Magnetic volume storage (TiB)'].get_criticals()[0].resource_id
   >>>

The usage is of the EC2 Volume resource type (where one exists, we use the
`CloudFormation Resource Type strings <http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html>`_ to identify resource types).

.. code-block:: pycon

   >>> result['EC2']['Magnetic volume storage (TiB)'].get_criticals()[0].aws_type
   'AWS::EC2::Volume'

We can query the actual numeric usage value:

.. code-block:: pycon

   >>> pprint.pprint(result['EC2']['Magnetic volume storage (TiB)'].get_criticals()[0].get_value())
   23.337

Or a string description of it:

.. code-block:: pycon

   >>> print(str(result['EC2']['Magnetic volume storage (TiB)'].get_criticals()[0]))
   23.337

The "Security groups per VPC" limit also crossed thresholds, and we can see that it has one
critical usage value:

.. code-block:: pycon

   >>> len(result['EC2']['Security groups per VPC'].get_warnings())
   0
   >>> len(result['EC2']['Security groups per VPC'].get_criticals())
   1

As this limit is per-VPC, our string representation of the current usage includes the VPC ID that
crossed the critical threshold:

.. code-block:: pycon

   >>> for usage in result['EC2']['Security groups per VPC'].get_criticals():
   ...     print(str(usage))
   ...
   vpc-c300b9a6=100

Disabling Trusted Advisor
++++++++++++++++++++++++++

To disable querying Trusted Advisor for limit information, call :py:meth:`~.AwsLimitChecker.get_limits`
or :py:meth:`~.AwsLimitChecker.check_thresholds` with ``use_ta=False``:

.. code-block:: pycon

   >>> result = c.check_thresholds(use_ta=False)

.. _python_usage.disabling_service_quotas:

Disabling Service Quotas
++++++++++++++++++++++++

To disable querying the Service Quotas service for current limits, pass ``skip_quotas=True``
in to the :py:class:`~.AwsLimitChecker` class constructor:

.. code-block:: python

    checker = AwsLimitChecker(skip_quotas=True)

.. _python_usage.partitions:

Partitions and Trusted Advisor Regions
++++++++++++++++++++++++++++++++++++++

awslimitchecker currently supports operating against non-standard `partitions <https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html>`_, such as GovCloud and AWS China (Beijing). Partition names, as seen in the ``partition`` field of ARNs, can be specified with the ``role_partition`` keyword argument to the :py:class:`~.AwsLimitChecker` class. Similarly, the region name to use for the ``support`` API for Trusted Advisor can be specified with the ``ta_api_region`` keyword argument to the :py:class:`~.AwsLimitChecker` class.

Skipping Specific Services
++++++++++++++++++++++++++

You can completely disable all interaction with specific Services with the
:py:meth:`~.AwsLimitChecker.remove_services` method. This method takes a list of
string Service names to remove from AwsLimitChecker's internal ``services`` dict,
which will prevent those services from being queried or reported on.

To remove the Firehose and EC2 services:

.. code-block:: pycon

    c.remove_services(['Firehose', 'EC2'])

.. _python_usage.throttling:

Handling Throttling and Rate Limiting
+++++++++++++++++++++++++++++++++++++

See :ref:`CLI Usage - Handling Throttling and Rate Limiting <cli_usage.throttling>`; this is handled the same way in Python, though you'd likely set the environment variables using ``os.environ`` instead of exporting them outside of Python.

Logging
-------

awslimitchecker uses the python :py:mod:`logging` library for logging, with module-level loggers
defined in each file. If you already have a root-level logger defined in your program and are using
a simple configuration (i.e. ``logging.basicConfig()``), awslimitchecker logs will be emitted at
the same level as that which the root logger is configured.

Assuming you have a root-level logger defined and configured, and you only want to see awslimitchecker
log messages of WARNING level and above, you can set the level of awslimitchecker's logger before
instantiating the class:

.. code-block:: python

   alc_log = logging.getLogger('awslimitchecker')
   alc_log.setLevel(logging.WARNING)
   checker = AwsLimitChecker()

It's _highly_ recommended that you do not suppress log messages of WARNING or above, as these
indicate situations where the checker may not present accurate or complete results.

If your application does not define a root-level logger, this becomes a bit more complicated.
Assuming your application has a more complex configuration that uses a top-level logger 'myapp'
with its own handlers defined, you can do something like the following. Note that this is highly
specific to your logging setup:

.. code-block:: python

   # setup logging for awslimitchecker
   alc_log = logging.getLogger('awslimitchecker')
   # WARNING or higher should pass through
   alc_log.setLevel(logging.WARNING)
   # use myapp's handler(s)
   for h in logging.getLogger('cm').handlers:
       alc_log.addHandler(h)
   # instantiate the class
   checker = AwsLimitChecker()

Advanced Examples
------------------

For more examples, see `docs/examples/README.rst on GitHub <https://github.com/jantman/awslimitchecker/blob/master/docs/examples/README.rst>`_.

CI / Deployment Checks
+++++++++++++++++++++++

This example checks usage, logs a message at ``WARNING`` level for any warning thresholds surpassed,
and logs a message at ``CRITICAL`` level for any critical thresholds passed. If any critical thresholds
were passed, it exits the script non-zero, i.e. to fail a CI or build job. In this example, we have
multiple critical thresholds crossed.

.. code-block:: pycon

   >>> import logging
   >>> logging.basicConfig()
   >>> logger = logging.getLogger()
   >>>
   >>> from awslimitchecker.checker import AwsLimitChecker
   >>> c = AwsLimitChecker()
   >>> result = c.check_thresholds()
   >>>
   >>> have_critical = False
   >>> for service, svc_limits in result.items():
   ...     for limit_name, limit in svc_limits.items():
   ...         for warn in limit.get_warnings():
   ...             logger.warning("{service} '{limit_name}' usage ({u}) exceeds "
   ...                            "warning threshold (limit={l})".format(
   ...                                service=service,
   ...                                limit_name=limit_name,
   ...                                u=str(warn),
   ...                                l=limit.get_limit(),
   ...                            )
   ...             )
   ...         for crit in limit.get_criticals():
   ...             have_critical = True
   ...             logger.critical("{service} '{limit_name}' usage ({u}) exceeds "
   ...                            "critical threshold (limit={l})".format(
   ...                                service=service,
   ...                                limit_name=limit_name,
   ...                                u=str(crit),
   ...                                l=limit.get_limit(),
   ...                            )
   ...             )
   ...
   CRITICAL:root:EC2 'Magnetic volume storage (TiB)' usage (23.417) exceeds critical threshold (limit=20)
   CRITICAL:root:EC2 'Running On-Demand EC2 instances' usage (97) exceeds critical threshold (limit=20)
   WARNING:root:EC2 'Security groups per VPC' usage (vpc-c300b9a6=96) exceeds warning threshold (limit=100)
   CRITICAL:root:EC2 'Running On-Demand m3.medium instances' usage (53) exceeds critical threshold (limit=20)
   CRITICAL:root:EC2 'EC2-Classic Elastic IPs' usage (5) exceeds critical threshold (limit=5)
   >>> if have_critical:
   ...     raise SystemExit(1)
   ...
   (awslimitchecker)$ echo $?
   1
