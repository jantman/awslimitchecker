.. _internals:

Internals
==========


.. _internals.overall_flow:

Overall Program Flow
---------------------

:py:class:`~awslimitchecker.checker._AwsLimitChecker` provides the full and only public interface to this
project; it's used by the ``awslimitchecker`` command line script (entry point to :py:mod:`~awslimitchecker.runner`)
and should be the only portion directly used by external code.

Each AWS Service is represented by a subclass of the :py:class:`~awslimitchecker.services.base._AwsService` abstract base
class; these Service Classes are responsible for knowing which limits exist for the service they represent, what the
default values for these limits are, and how to check the current usage via the AWS API (via :py:pkg:`boto`). When the
Service Classes are instantiated, they build a dict of all of their limits, correlating a string key (the "limit name")
with an :py:class:`~awslimitchecker.limit._AwsLimit` object. The Service Class constructors *must not* make any network
connections; connections are created lazily as needed and stored as a class attribute. This allows us to inspect the
services, limits and default limit values without ever connecting to AWS (this is also used to generate the
:ref:`Checks <_checks>` documentation automatically).

When :py:class:`~awslimitchecker.checker._AwsLimitChecker` is instantiated, it imports :py:mod:`~awslimitchecker.services`
which in turn creates instances of all ``awslimitchecker.services.*`` classes and adds them to a dict mapping the
string Service Name to the Service Class instance. These instances are used for all interaction with the services.

So, once an instance of :py:class:`~awslimitchecker.checker._AwsLimitChecker` is created, we should have instant access
to the services and limits without any connection to AWS. This is utilized by the ``--list-services`` and
``--list-defaults`` options for the :ref:`command line client <_cli>`.
