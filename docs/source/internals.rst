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
default values for these limits are, and how to check the current usage via the AWS API (via :py:pkg:`boto`). When the
Service Classes are instantiated, they build a dict of all of their limits, correlating a string key (the "limit name")
with an :py:class:`~awslimitchecker.limit.AwsLimit` object. The Service Class constructors *must not* make any network
connections; connections are created lazily as needed and stored as a class attribute. This allows us to inspect the
services, limits and default limit values without ever connecting to AWS (this is also used to generate the
:ref:`Supported Limits <limits>` documentation automatically).

When :py:class:`~awslimitchecker.checker.AwsLimitChecker` is instantiated, it imports :py:mod:`~awslimitchecker.services`
which in turn creates instances of all ``awslimitchecker.services.*`` classes and adds them to a dict mapping the
string Service Name to the Service Class instance. These instances are used for all interaction with the services.

So, once an instance of :py:class:`~awslimitchecker.checker.AwsLimitChecker` is created, we should have instant access
to the services and limits without any connection to AWS. This is utilized by the ``--list-services`` and
``--list-defaults`` options for the :ref:`command line client <cli_usage>`.

.. _internals.trusted_advisor:

Trusted Advisor
-----------------

When :py:class:`~awslimitchecker.checker.AwsLimitChecker` is initialized, it also initializes an instance of
:py:class:`~awslimitchecker.trustedadvisor.TrustedAdvisor`. In :py:meth:`~.AwsLimitChecker.get_limits`,
:py:meth:`~.AwsLimitChecker.find_usage` and :py:meth:`~.AwsLimitChecker.check_thresholds`, when called with
``use_ta == True`` (the default), :py:meth:`~.TrustedAdvisor.update_limits` is called on the TrustedAdvisor
instance.

:py:meth:`~.TrustedAdvisor.update_limits` polls Trusted Advisor data is from the Support API via
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

Using this methodology, no additional code is needed to support new/additional Trusted Advisor limit checks;
*so long as* the Service and Limit name strings match between the Trusted Advisor API response and their
corresponding :py:class:`~._AwsService` and :py:class:`~.AwsLimit` instances, the TA limits will be automatically
added to the corresponding ``AwsLimit``.
