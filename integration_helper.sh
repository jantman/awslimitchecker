#!/bin/bash -e

if [[ "$TRAVIS_PULL_REQUEST" != "false" ]]; then
    echo "Not running integration tests for pull requests."
    exit 0
fi

# NOTE - these run using the restricted IAM permissions suggested by awslimitchecker;
# if the tests start failing, it's probably because someone with access to the
# limitchecker test AWS account needs to manually update the IAM permissions
# on the test user.
awslimitchecker -vv -r us-west-2 -l
awslimitchecker -vv -r us-west-2 -u
