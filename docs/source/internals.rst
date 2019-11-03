.. _internals:

Internals
==========


.. _internals.overall_flow:

Overall Program Flow
---------------------

:py:class:`~awslimitchecker.checker.AwsLimitChecker` provides the full and only public interface to this
project; it's used by the ``awslimitchecker`` command line script (entry point to :py:mod:`~awslimitchecker.runner`)
and should be the only portion directly used by external code.

Each AWS Service is represented by a subclass of the :py:class:`~awslimitchecker.services.base._AwsService` abstract base
class; these Service Classes are responsible for knowing which limits exist for the service they represent, what the
default values for these limits are, querying current limits from the service's API (if supported),
and how to check the current usage via the AWS API (``boto3``). When the
Service Classes are instantiated, they build a dict of all of their limits, correlating a string key (the "limit name")
with an :py:class:`~awslimitchecker.limit.AwsLimit` object. The Service Class constructors *must not* make any network
connections; connections are created lazily as needed and stored as a class attribute. This allows us to inspect the
services, limits and default limit values without ever connecting to AWS (this is also used to generate the
:ref:`Supported Limits <limits>` documentation automatically).

All calls to boto3 client ("low-level") methods that return a dict response that can
include 'NextToken' or another pagination marker, should be called through
:py:func:`~awslimitchecker.utils.paginate_dict` with the appropriate parameters.

When :py:class:`~awslimitchecker.checker.AwsLimitChecker` is instantiated, it imports :py:mod:`~awslimitchecker.services`
which in turn creates instances of all ``awslimitchecker.services.*`` classes and adds them to a dict mapping the
string Service Name to the Service Class instance. These instances are used for all interaction with the services.

So, once an instance of :py:class:`~awslimitchecker.checker.AwsLimitChecker` is created, we should have instant access
to the services and limits without any connection to AWS. This is utilized by the ``--list-services`` and
``--list-defaults`` options for the :ref:`command line client <cli_usage>`.

.. _internals.trusted_advisor:

Trusted Advisor
---------------

When :py:class:`~awslimitchecker.checker.AwsLimitChecker` is initialized, it also initializes an instance of
:py:class:`~awslimitchecker.trustedadvisor.TrustedAdvisor`. In :py:meth:`~.AwsLimitChecker.get_limits`,
:py:meth:`~.AwsLimitChecker.find_usage` and :py:meth:`~.AwsLimitChecker.check_thresholds`, when called with
``use_ta == True`` (the default), :py:meth:`~.TrustedAdvisor.update_limits` is called on the TrustedAdvisor
instance.

:py:meth:`~.TrustedAdvisor.update_limits` polls Trusted Advisor data from the Support API via
:py:meth:`~.TrustedAdvisor._poll`; this will retrieve the limits for all "flaggedResources" items in the
``Service Limits`` Trusted Advisor check result for the current AWS account. It then calls
:py:meth:`~.TrustedAdvisor._update_services`, passing in the Trusted Advisor check results and the
dict of :py:class:`~._AwsService` objects it was called with (from :py:class:`~.AwsLimitChecker`).

:py:meth:`~.TrustedAdvisor._update_services` iterates over the Services in the Trusted Advisor check result
and attempts to find a matching :py:class:`~._AwsService` (by string service name) in the dict passed
in from :py:class:`~.AwsLimitChecker`. If a match is found, it iterates over all limits for that service
in the TA result and attempts to call the ``Service``'s :py:meth:`~._AwsService._set_ta_limit` method.
If a matching Service is not found, or if ``_set_ta_limit`` raises a ValueError (matching Limit not found
for that Service), an error is logged.

When :py:class:`~awslimitchecker.checker.AwsLimitChecker` initializes
:py:class:`~awslimitchecker.trustedadvisor.TrustedAdvisor`, it passes in the
``self.services`` dictionary of all services and limits. At initialization time,
:py:class:`~awslimitchecker.trustedadvisor.TrustedAdvisor` iterates all services
and limits, and builds a new dictionary mapping the limit objects by the return
values of their :py:meth:`~awslimitchecker.limit.AwsLimit.ta_service_name`
and :py:meth:`~awslimitchecker.limit.AwsLimit.ta_limit_name` properties. This
allows limits to override the Trusted Advisor service and limit name that their
data comes from. In the default case, their service and limit names will be used
as they are set in the awslimitchecker code, and limits which have matching
Trusted Advisor data will be automatically populated.

In the :py:class:`~awslimitchecker.trustedadvisor.TrustedAdvisor` class's
:py:meth:`~.TrustedAdvisor._poll` method,
:py:meth:`~.TrustedAdvisor._get_refreshed_check_result` is used to retrieve the
check result data from Trusted Advisor. This method also implements the check
refresh logic. See the comments in the source code for the specific logic. There
are three methods of refreshing checks (refresh modes), which are controlled
by the ``ta_refresh_mode`` parameter to :py:class:`~awslimitchecker.trustedadvisor.TrustedAdvisor`:

* If ``ta_refresh_mode`` is the string "wait", the check will be refreshed and
  awslimitchecker will poll for the refresh result every 30 seconds, waiting
  for the refresh to complete (or until ``ta_refresh_timeout`` seconds have elapsed).
  This is exposed via the CLI as the ``--ta-refresh-wait`` option.
* If ``ta_refresh_mode`` is an integer, it will operate like the "wait" mode above,
  but only if the current result data for the check is more than ``ta_refresh_mode``
  seconds old. This is exposed via the CLI as the ``--ta-refresh-older`` option.
* If ``ta_refresh_mode`` is the string "trigger", the check will be refreshed and
  the program will continue on immediately, without waiting for the refresh to
  complete; this will almost certainly result in stale check results in the current
  run. However, this may be useful if you desire to keep ``awslimitchecker`` runs
  short, and run it on a regular schedule (i.e. if you run ``awslimitchecker``
  every 6 hours, and are OK with Trusted Advisor check data being 6 hours old).
  This is exposed via the CLI as the ``--ta-refresh-trigger`` option.

Additionally, :py:class:`~awslimitchecker.trustedadvisor.TrustedAdvisor` has a
``ta_refresh_timeout`` parameter. If this is set to a non-``None`` value (an integer),
refreshes of the check will time out after that number of seconds. If a timeout
occurs, a message will be logged at error level, but the program will continue
running (most likely using the old result data). This parameter is exposed via
the CLI as the ``--ta-refresh-timeout`` option.

**Important:** It may take 30 to 60 *minutes* for the Service Limits check to
refresh on large accounts. Please be aware of this when enabling the refresh
options.

Using the check refresh options will require the ``trustedadvisor:RefreshCheck``
IAM permission.

For use via Python, these same parameters (``ta_refresh_mode`` and ``ta_refresh_timeout``)
are exposed as parameters on the
:py:class:`~awslimitchecker.checker.AwsLimitChecker` constructor.

.. _internals.quotas:

Service Quotas service
----------------------

Unless use of Serivce Quotas is disabled with the ``--skip-quotas`` command line option or by passing ``skip_quotas=False`` to the :py:class:`~awslimitchecker.checker.AwsLimitChecker` constructor, awslimitchecker will retrieve all relevant data from the Service Quotas service. In the :py:class:`~.AwsLimitChecker` constructor (so long as ``skip_quotas`` is True), an instance of the :py:class:`~.ServiceQuotasClient` class is constructed, passing in our boto3 connection keyword arguments for the current region. This client class instance is then passed to the constructor of every Service class (:py:class:`~._AwsService` subclass) when the class is created, via the ``quotas_client`` argument. Each :py:class:`~._AwsService` class stores this as the ``_quotas_client`` instance variable.

As the :py:class:`~.AwsLimitChecker` class iterates over all (configured) services in its :py:meth:`~.AwsLimitChecker.get_limits`, :py:meth:`~.AwsLimitChecker.find_usage`, and :py:meth:`~.AwsLimitChecker.check_thresholds` methods, it will call the service class's :py:meth:`~._AwsService._update_service_quotas` method after calling :py:meth:`~.TrustedAdvisor.update_limits` and the service class's ``_update_limits_from_api()`` method (if present), and before the actual operation of getting limits, finding usage, or checking thresholds.

The :py:meth:`._AwsService._update_service_quotas` method will iterate through all limits (:py:class:`~.AwsLimit`) for the service and call the :py:meth:`~.ServiceQuotasClient.get_quota_value` method for each. Assuming it returns a non-``None`` result, that result will be passed to the limit's :py:meth:`~.AwsLimit._set_quotas_limit` method for later use in :py:meth:`~.AwsLimit.get_limit`.

When retrieving values from Service Quotas, the ``ServiceCode`` is taken from the :py:attr:`._AwsService.quotas_service_code` attribute on the Service class. If that is set to ``None``, Service Quotas will not be consulted for that service. The ``ServiceCode`` can also be overridden on a per-limit basis via the ``quotas_service_code`` argument to the :py:class:`~.AwsLimit` constructor. The ``QuotaName`` used by each limit defaults to the limit name itself (:py:class:`.AwsLimit` instance variable ``name``) but can be overridden with the ``quota_name`` argument to the :py:class:`~.AwsLimit` constructor.

Note that quota names are stored and compared in lower case.

Service API Limit Information
-----------------------------

Some services provide API calls to retrieve at least some of the current limits, such as the ``DescribeAccountAttributes``
API calls for `RDS <http://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DescribeAccountAttributes.html>`_
and `EC2 <http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeAccountAttributes.html>`_. Services that
support such calls should make them in a ``_update_limits_from_api()`` method, which will be automatically called from
:py:meth:`~.awslimitchecker.checker.AwsLimitChecker.get_limits`. The ``_update_limits_from_api()`` method should make the API call, and then
update all relevant limits via the :py:class:`~.AwsLimit` class's :py:meth:`~.AwsLimit._set_api_limit` method.

Limit Value Precedence
----------------------

The value used for a limit is the first match in the following list:

1. Limit Override (set at runtime)
2. API Limit
3. Service Quotas
4. Trusted Advisor
5. Hard-coded default

Threshold Overrides
-------------------

For more information on overriding thresholds, see
:ref:`Python Usage / Setting a Threshold Override <python_usage.threshold_overrides>` as well as the
documentation for :py:meth:`.AwsLimitChecker.check_thresholds` and :py:meth:`.AwsLimitChecker.set_threshold_override`.
