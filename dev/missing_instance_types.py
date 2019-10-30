#!/usr/bin/env python
# List EC2 Instance Types
# see: https://aws.amazon.com/blogs/aws/new-aws-price-list-api/

import requests
from awslimitchecker.services.ec2 import _Ec2Service

print('GETing AWS Pricing Offers index JSON')
offers = requests.get(
    'https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json'
)
ec2_offer_path = offers.json()['offers']['AmazonEC2']['currentVersionUrl']
purl = 'https://pricing.us-east-1.amazonaws.com%s' % ec2_offer_path
print('GETing EC2 Offers from: %s' % purl)
ec2offer = requests.get(purl).json()

uniq = set()
for sku, data in ec2offer['products'].items():
    if data['productFamily'] != 'Compute Instance':
        # skip anything that's not an EC2 Instance
        continue
    uniq.add(data['attributes']['instanceType'])

print('Finding _Ec2Service current instance types')
s = _Ec2Service(1, 2)
alctypes = s._instance_types()

missing = []
for itype in sorted(uniq):
    if itype not in alctypes:
        print('MISSING INSTANCE TYPE: %s' % itype)
        missing.append(itype)
print('awslimitchecker currently has %d of %d instance types' % (
    len(alctypes), len(uniq)
))
if len(missing) > 0:
    print('Missing types: %s' % missing)
extra = []
for itype in sorted(alctypes):
    if itype not in uniq:
        print('EXTRA INSTANCE TYPE: %s' % itype)
        extra.append(itype)
print('awslimitchecker currently has %d extra instance types' % len(extra))
if len(extra) > 0:
    print('Extra types: %s' % extra)
