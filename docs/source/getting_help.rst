.. _getting_help:

Getting Help
=============

If you have a quick question or need some simple assistance, you can try the
`gitter.im chat channel <https://gitter.im/awslimitchecker/Lobby>`_.

.. _getting_help.paid_support:

Enterprise Support Agreements and Contract Development
-------------------------------------------------------

For Commercial or Enterprise support agreements for awslimitchecker,
or for paid as-needed feature development or bug fixes, please contact Jason
Antman at jason@jasonantman.com.

.. _getting_help.reporting_bugs_and_questions:

Reporting Bugs and Asking Questions
------------------------------------

.. NOTE: be sure to update .github/ISSUE_TEMPLATE.md when changing this

Questions, bug reports and feature requests are happily accepted via the
`GitHub Issue Tracker <https://github.com/jantman/awslimitchecker/issues>`_.
Pull requests are welcome; see the :ref:`development` documentation for information
on PRs. Issues that don't have an accompanying pull request
will be worked on as my time and priority allows, and I'll do my best to
complete feature requests as quickly as possible. Please take into account that
I work on this project solely in my personal time, I don't get paid to work on it
and I can't work on it for my day job, so there may be some delay in getting
things implemented.

.. _getting_help.guidelines_for_reporting_issues:

Guidelines for Reporting Issues
-------------------------------

Opening a `new issue on GitHub <https://github.com/jantman/awslimitchecker/issues/new>`_
should pre-populate the issue description with a template of the following:

.. _getting_help.feature_requests:

Feature Requests
++++++++++++++++

If your feature request is for support of a service or limit not currently
supported by awslimitchecker, you can simply title the issue ``add support for
<name of service, or name of service and limit>`` and add a simple description.
For anything else, please follow these guidelines:

1. Describe in detail the feature you would like to see implemented, especially
   how it would work from a user perspective and what benefits it adds. Your description
   should be detailed enough to be used to determine if code written for the feature
   adequately solves the problem.
2. Describe one or more use cases for why this feature will be useful.
3. Indicate whether or not you will be able to assist in testing pre-release
   code for the feature.

.. _getting_help.bug_reports:

Bug Reports
+++++++++++

When reporting a bug in awslimitchecker, please provide all of the following information,
as well as any additional details that may be useful in reproducing or fixing
the issue:

1. awslimitchecker version, as reported by ``awslimitchecker --version``.
2. How was awslimitchecker installed (provide as much detail as possible, ideally
   the exact command used and whether it was installed in a virtualenv or not).
3. The output of ``python --version`` and ``virtualenv --version`` in the environment
   that awslimitchecker is running in.
4. Your operating system type and version.
5. The output of awslimitchecker, run with the ``-vv`` (debug-level output) flag
   that shows the issue.
6. The output that you expected (what's wrong).
7. If the bug/issue is related to TrustedAdvisor, which support contract your account has.
8. Whether or not you are willing and able to assist in testing pre-release code
   intended to fix the issue.
