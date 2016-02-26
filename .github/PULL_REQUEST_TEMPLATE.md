Before submitting pull requests, please see the
[Development documentation](http://awslimitchecker.readthedocs.org/en/latest/development.html)
and specifically the [Pull Request Guidelines](http://awslimitchecker.readthedocs.org/en/latest/development.html#pull-requests).

# Pull Request Checklist

- [ ] Code should conform to the [Development Guidelines](http://awslimitchecker.readthedocs.org/en/latest/development.html#guidelines):
    - [ ] pep8 compliant with some exceptions (see pytest.ini)
    - [ ] 100% test coverage with pytest (with valid tests). If you have difficulty
      writing tests for the code, feel free to ask for help or submit the PR without tests.
    - [ ] Complete, correctly-formatted documentation for all classes, functions and methods.
    - [ ] documentation has been rebuilt with ``tox -e docs``
    - [ ] Connections to the AWS services should only be made by the class's
      ``connect()`` and ``connect_resource()`` methods, inherited from
      [awslimitchecker.connectable.Connectable](http://awslimitchecker.readthedocs.org/en/latest/awslimitchecker.connectable.html)
    - [ ] All modules should have (and use) module-level loggers.
    - [ ] **Commit messages** should be meaningful, and reference the Issue number
      if you're working on a GitHub issue (i.e. "issue #x - <message>"). Please
      refrain from using the "fixes #x" notation unless you are *sure* that the
      the issue is fixed in that commit.
    - [ ] Git history is fully intact; please do not squash or rewrite history.
- [] If you made changes to the ``versioncheck`` code, be sure to locally run the
``-versioncheck`` tox tests.
