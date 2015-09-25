awslimitchecker example scripts
===============================

check_aws_limits.py
-------------------

This is an example of a wrapper around awslimitchecker with the following functionality:

* Set some overrides for specific limits
* Set threshold overrides for specific limits
* Print warning-level thresholds in yellow and critical-level thresholds in red
* Print a summary of the number of warnings and criticals
* Exit code 1 if any criticals, or if any warnings and ``--error-on-warning`` specified

Feel free to use this as a starting point for your own wrapper.

Jenkins-AWS_Limit_Check.xml
----------------------------

This is a sample Jenkins job to run ``check_aws_limits.py`` every 6 hours, 

test_check_aws_limits.py
------------------------

pytest script to test ``check_aws_limits.py``. Requires ``mock``, ``pytest``, ``pytest-cov``, ``pytest-flakes`` and ``pytest-pep8``.

To run: ``py.test -vv -s --cov-report term-missing --cov-report html --cov=check_aws_limits.py test_check_aws_limits.py``
