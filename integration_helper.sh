#!/bin/bash -x

if [[ "$TRAVIS_PULL_REQUEST" != "false" ]]; then
    echo "Not running integration tests for pull requests."
    exit 0
fi

FAILURES=0
# NOTE - these run using the restricted IAM permissions suggested by awslimitchecker;
# if the tests start failing, it's probably because someone with access to the
# limitchecker test AWS account needs to manually update the IAM permissions
# on the test user.
awslimitchecker -vv -r us-west-2 -l || FAILURES=1
awslimitchecker -vv -r us-west-2 -u || FAILURES=1

while read svcname; do
    awslimitchecker -vv -r us-west-2 -l -S $svcname || FAILURES=1
    awslimitchecker -vv -r us-west-2 -u -S $svcname || FAILURES=1
done< <(awslimitchecker -s)

if [ "$FAILURES" -eq 1 ]; then
    echo "ERROR: some tests failed!"
    exit 1
fi
