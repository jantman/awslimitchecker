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

    pip install botolimitchecker

.. _getting_started.credentials:
Credentials
------------

botolimitchecker does nothing with AWS credentials, it leaves that to boto itself.
You must either have your credentials configured in one of boto's supported config
files, or set as environment variables. See
`the boto configuration documentation <http://docs.pythonboto.org/en/latest/boto_config_tut.html>`_
for further information.

.. _getting_started.cli_usage:

Basic Command Line Usage
-------------------------

TODO

.. _getting_started.python_usage:

Basic Python Package Usage
---------------------------

TODO
