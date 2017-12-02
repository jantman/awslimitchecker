#!/usr/bin/env python
# List EC2 Instance Types
# see: https://aws.amazon.com/blogs/aws/new-aws-price-list-api/

import requests

offers = requests.get(
    'https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json'
)
ec2_offer_path = offers.json()['offers']['AmazonEC2']['currentVersionUrl']
ec2offer = requests.get(
    'https://pricing.us-east-1.amazonaws.com%s' % ec2_offer_path
)

uniq = set()
for sku, data in ec2offer['products'].items():
    if data['productFamily'] != 'Compute Instance':
        # skip anything that's not an EC2 Instance
        continue
    uniq.add(data['attributes']['instanceType'])
for itype in sorted(uniq):
    print(itype)
