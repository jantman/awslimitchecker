.. _getting_started:

Getting Started
===============

.. _getting_started.requirements:

Requirements
------------

* Python 2.6 or 2.7 (`boto <http://docs.pythonboto.org/en/latest/>`_ currently has incomplete python3 support)
* Python `VirtualEnv <http://www.virtualenv.org/>`_ and ``pip`` (recommended installation method; your OS/distribution should have packages for these)
* `boto <http://docs.pythonboto.org/en/latest/>`_


.. _getting_started.installing:

Installing
----------

It's recommended that you install into a virtual environment (virtualenv /
venv). See the `virtualenv usage documentation <http://www.virtualenv.org/en/latest/>`_
for information on how to create a venv. If you really want to install
system-wide, you can (using sudo).

.. code-block:: bash

    pip install awslimitchecker

.. _getting_started.credentials:
Credentials
------------

awslimitchecker does nothing with AWS credentials, it leaves that to boto itself.
You must either have your credentials configured in one of boto's supported config
files, or set as environment variables. See
`the boto configuration documentation <http://docs.pythonboto.org/en/latest/boto_config_tut.html>`_
for further information.

.. _getting_started.permissions:
Required Permissions
---------------------

You can view a sample IAM policy listing the permissions required for awslimitchecker to function properly
either via the CLI client:

.. code-block:: bash

    awslimitchecker --iam-policy

Or as a python dict:

.. code-block:: python

    from awslimitchecker.checker import AwsLimitChecker
    c = AwsLimitChecker()
    iam_policy = c.get_required_iam_policy()

You can also view the required permissions for the current version of awslimitchecker at :ref:`Required IAM Permissions <.iam_policy>`.
