
.. _python_usage:

Python Usage
=============

The full feature set of awslimitchecker is available through the Python API.
This page attempts to document some examples of usage, but the best resources are
:py:mod:`~AwsLimitchecker.runner`, the command line wrapper, and the
:ref:`API documentation <modindex>`.

Simple Examples
----------------

Many of these examples use :py:mod:`pprint` to make output a bit nicer.

Instantiating the Class
++++++++++++++++++++++++

Here we import and instantiate the :py:class:`class <~.AwsLimitChecker>`; note that we also setup
Python's :py:mod:`logging` module, which is used by ``awslimitchecker``.
We also import :py:mod:`pprint` to make the output nicer.

.. code-block:: pycon

   >>> import pprint
   >>> import logging
   >>> logging.basicConfig()
   >>> logger = logging.getLogger()
   >>> 
   >>> from awslimitchecker.checker import AwsLimitChecker
   >>> c = AwsLimitChecker()

Setting a Limit Override
+++++++++++++++++++++++++

Override EC2's "EC2-Classic Elastic IPs" limit from its default to 20,
using :py:meth:`~.AwsLimitChecker.set_limit_override`.

.. code-block:: pycon

   >>> c.set_limit_override('EC2', 'EC2-Classic Elastic IPs', 20)

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

   >>> result['EC2']['Magnetic volume storage (TiB)'].get_criticals()[0].id
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

Advanced Examples
------------------

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
