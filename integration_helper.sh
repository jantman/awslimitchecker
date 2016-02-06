#!/bin/bash -x

# ## CONFIGURATION:
#
# resources are in my master account, the ID of which is set by Travis in the
#   AWS_MASTER_ACCOUNT_ID environment variable
# default keys give access to that account with the 'awslimitchecker' policy
# STS access is from the awslimitchecker account
#
# ## STS:
#
# The credentials for the awslimitchecker account ('alc-integration') are
# set by Travis as AWS_INTEGRATION_ACCESS_KEY_ID and
# AWS_INTEGRATION_SECRET_KEY respectively.
#
# * the 'alc-integration-sts' role gives access from the awslimitchecker account
# * the 'alc-integration-sts-extid' role gives access from the awslimitchecker
#    account with the External ID set by Travis in $AWS_EXTERNAL_ID
#

if [[ "$TRAVIS_PULL_REQUEST" != "false" ]]; then
    echo "Not running integration tests for pull requests."
    exit 0
fi

FAILURES=0

# NOTE - these run using the restricted IAM permissions suggested by awslimitchecker;
# if the tests start failing, it's probably because someone with access to the
# limitchecker test AWS account needs to manually update the IAM permissions
# on the test user.
awslimitchecker -vv -r us-west-2 -l || { FAILURES=1; echo -e "\n\n>>>> ABOVE TEST FAILED <<<<\n\n"; }
awslimitchecker -vv -r us-west-2 -u || { FAILURES=1; echo -e "\n\n>>>> ABOVE TEST FAILED <<<<\n\n"; }

while read svcname; do
    awslimitchecker -vv -r us-west-2 -l -S $svcname || { FAILURES=1; echo -e "\n\n>>>> ABOVE TEST FAILED <<<<\n\n"; }
    awslimitchecker -vv -r us-west-2 -u -S $svcname || { FAILURES=1; echo -e "\n\n>>>> ABOVE TEST FAILED <<<<\n\n"; }
done< <(awslimitchecker -s)

###############################################################################
# STS tests
# Since connection logic is shared by all service classes and TrustedAdvisor,
# just running a single service should suffice to test for STS functionality.
# As of 0.3.0, VPC seems to be the fastest service to query, so we'll use that.
# In reality, all we care about in these further (STS) tests are that we can
# connect and auth.
###############################################################################

# STS tests
set +x
AWS_ACCESS_KEY_ID=$AWS_INTEGRATION_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$AWS_INTEGRATION_SECRET_KEY

# STS normal role
echo "running: awslimitchecker -vv -r us-west-2 -l -S VPC --sts-account-id=XXX --sts-account-role=alc-integration-sts"
awslimitchecker -vv -r us-west-2 -l -S VPC --sts-account-id=${AWS_MASTER_ACCOUNT_ID} --sts-account-role=alc-integration-sts || { FAILURES=1; echo -e "\n\n>>>> ABOVE TEST FAILED <<<<\n\n"; }
echo "running: awslimitchecker -vv -r us-west-2 -u -S VPC --sts-account-id=XXX --sts-account-role=alc-integration-sts"
awslimitchecker -vv -r us-west-2 -u -S VPC --sts-account-id=${AWS_MASTER_ACCOUNT_ID} --sts-account-role=alc-integration-sts || { FAILURES=1; echo -e "\n\n>>>> ABOVE TEST FAILED <<<<\n\n"; }

# STS external ID role
echo "running: awslimitchecker -vv -r us-west-2 -l -S VPC --sts-account-id=XXX --sts-account-role=alc-integration-sts-extid --external-id=XXX"
awslimitchecker -vv -r us-west-2 -l -S VPC --sts-account-id=${AWS_MASTER_ACCOUNT_ID} --sts-account-role=alc-integration-sts-extid --external-id="$AWS_EXTERNAL_ID" || { FAILURES=1; echo -e "\n\n>>>> ABOVE TEST FAILED <<<<\n\n"; }
echo "running: awslimitchecker -vv -r us-west-2 -u -S VPC --sts-account-id=XXX --sts-account-role=alc-integration-sts-extid --external-id=XXX"
awslimitchecker -vv -r us-west-2 -u -S VPC --sts-account-id=${AWS_MASTER_ACCOUNT_ID} --sts-account-role=alc-integration-sts-extid --external-id="$AWS_EXTERNAL_ID" || { FAILURES=1; echo -e "\n\n>>>> ABOVE TEST FAILED <<<<\n\n"; }

if [ "$FAILURES" -eq 1 ]; then
    echo "ERROR: some tests failed!"
    exit 1
fi
