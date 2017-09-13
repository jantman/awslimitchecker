Before submitting pull requests, please see the
[Development documentation](http://awslimitchecker.readthedocs.org/en/latest/development.html)
and specifically the [Pull Request Guidelines](http://awslimitchecker.readthedocs.org/en/latest/development.html#pull-requests).

__IMPORTANT:__ Please take note of the below checklist, especially the first three items.

# Summary

*Add a summary of what your PR does here. This could be as simple as "adds support for X service" or "fixes default limit for Y", or a longer explanation for less straightforward changes.*

# Pull Request Checklist

- [ ] All pull requests should be __against the develop branch__, not master.
- [ ] All pull requests must include the Contributor License Agreement (see below).
- [ ] Whether or not your PR includes unit tests:
    - [ ] Please make sure you have run the exact code contained in the PR locally, and it functions as desired.
    - [ ] Please make sure the TravisCI build passes or, if not, you've corrected any obvious problems identified by the tests.
- [ ] Code should conform to the [Development Guidelines](http://awslimitchecker.readthedocs.org/en/latest/development.html#guidelines):
    - [ ] pep8 compliant with some exceptions (see pytest.ini)
    - [ ] 100% test coverage with pytest (with valid tests). If you have difficulty
      writing tests for the code, that's fine, just mention that in the summary and either
      ask for assistance, or clarify that you'd like someone else to handle the tests. PRs that
      include complete test coverage will usually be merged faster.
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

## Contributor License Agreement

By submitting this work for inclusion in awslimitchecker, I agree to the following terms:

* The contribution included in this request (and any subsequent revisions or versions of it)
  is being made under the same license as the awslimitchecker project (the Affero GPL v3,
  or any subsequent version of that license if adopted by awslimitchecker).
* My contribution may perpetually be included in and distributed with awslimitchecker; submitting
  this pull request grants a perpetual, global, unlimited license for it to be used and distributed
  under the terms of awslimitchecker's license.
* I have the legal power and rights to agree to these terms.
