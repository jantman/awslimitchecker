#!/usr/bin/env python
"""
awslimitchecker/dev/spot_instances.py

Test script to create spot instance or fleet requests that will
(hopefully) never run before being canceled.

NOTE:
This script will deploy the instance into the first available subnet it finds,
 in the first VPC it finds.

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2015 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

    This file is part of awslimitchecker, also known as awslimitchecker.

    awslimitchecker is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    awslimitchecker is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with awslimitchecker.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)
################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/awslimitchecker> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

import boto3
import sys
import argparse
import logging
from datetime import datetime, timedelta
import uuid
from pprint import pformat

FORMAT = "[%(levelname)s %(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.WARNING, format=FORMAT)
logger = logging.getLogger(__name__)


class SpotInstanceTest:
    """ might as well use a class. It'll make things easier later. """

    def __init__(self):
        """ init method, run at class creation """
        self.conn = boto3.client('ec2')

    def list(self, i_type, az):
        """
        list existing requests
        """
        res = self.conn.describe_spot_instance_requests()
        logger.warning('Found %d spot instance requests',
                       len(res['SpotInstanceRequests']))
        for req in res['SpotInstanceRequests']:
            print('{state} ({status}) {id} - {price} (actual={actual} for '
                  '{minutes} min) - {itype} - {vfrom} to {vuntil}'.format(
                state=req['State'],
                status=req['Status']['Message'],
                id=req['SpotInstanceRequestId'],
                price=req['SpotPrice'],
                actual=req.get('ActualBlockHourlyPrice', '?'),
                itype=req['LaunchSpecification']['InstanceType'],
                minutes=req['BlockDurationMinutes'],
                vfrom=req['ValidFrom'],
                vuntil=req['ValidUntil']
            ))
        price = self.get_current_price(i_type, az)
        print("\n")
        print('Current %s spot price: %s' % (i_type, price))

    def create(self, i_type, az):
        """create a spot instance request"""
        market_price = self.get_current_price(i_type, az)
        bid_price = market_price * 0.25
        logger.warning('Current market price: %s; setting bid price to: %s',
                       market_price, bid_price)
        valid_from = datetime.now() + timedelta(days=14)
        valid_to = valid_from + timedelta(seconds=1)
        args = {
            'SpotPrice': '%s' % bid_price,
            'ClientToken': str(uuid.uuid4()),
            'InstanceCount': 1,
            'Type': 'one-time',
            'ValidFrom': valid_from,
            'ValidUntil': valid_to,
            'BlockDurationMinutes': 60,
            'LaunchSpecification': {
                'ImageId': 'ami-d2c924b2',  # Centos 7 HVM, us-west-2
                'SecurityGroups': ['default'],
                'InstanceType': i_type,
                'Placement': {
                    'AvailabilityZone': az
                },
            }
        }
        logger.info('Requesting spot instance: %s', pformat(args))
        res = self.conn.request_spot_instances(**args)
        logger.info('Result: %s', pformat(res))

    def cancel(self):
        """cancel ALL spot instance requests"""
        res = self.conn.describe_spot_instance_requests()
        logger.warning('Found %d spot instance requests',
                       len(res['SpotInstanceRequests']))
        for req in res['SpotInstanceRequests']:
            if req['State'] not in ['open', 'active']:
                logger.debug('Skipping request %s in state %s',
                             req['SpotInstanceRequestId'], req['State'])
                continue
            logger.info('Canceling request %s in state %s',
                        req['SpotInstanceRequestId'], req['State'])
            res = self.conn.cancel_spot_instance_requests(
                SpotInstanceRequestIds=[req['SpotInstanceRequestId']]
            )
            logger.info('Result: %s', pformat(res))

    def get_current_price(self, i_type, az):
        """get the current spot instance price"""
        now = datetime.now()
        start = now - timedelta(hours=12)
        end = now + timedelta(hours=12)
        res = self.conn.describe_spot_price_history(
            InstanceTypes=[i_type],
            ProductDescriptions=['Linux/UNIX (Amazon VPC)', 'Linux/UNIX'],
            AvailabilityZone=az,
            StartTime=start,
            EndTime=end
        )
        #logger.debug('Spot price history: %s', pformat(res))
        curr = sorted(res['SpotPriceHistory'], key=lambda k: k['Timestamp'])[-1]
        logger.info('Latest spot price for %s in %s: %s (as of %s)' % (
            curr['InstanceType'], curr['AvailabilityZone'], curr['SpotPrice'],
            curr['Timestamp']
        ))
        return float(curr['SpotPrice'])


def parse_args(argv):
    """
    parse arguments/options

    this uses the new argparse module instead of optparse
    see: <https://docs.python.org/2/library/argparse.html>
    """
    p = argparse.ArgumentParser(
        description='awslimitchecker spot instance test. This should ONLY EVER '
                    'be run on accounts that don\'t have any spot instance or '
                    'fleet requests!')
    p.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-t', '--type', dest='instance_type', action='store',
                   type=str, default='m3.medium',
                   help='instance type (default: t1.micro)')
    p.add_argument('-a', '--az', action='store', dest='az', type=str,
                   default='us-west-2b',
                   help='Availability Zone (default: us-west-2b)')
    p.add_argument('-k', '--key-name', action='store', type=str, dest='key',
                   default='phoenix-jantman', help='keypair name')
    p.add_argument('ACTION', action='store', default='list',
                   choices=['list', 'create', 'cancel'],
                   help='Action - "list" spot instance requests, "create" '
                        'requests, or "cancel" requests')

    args = p.parse_args(argv)

    return args

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    if args.verbose > 1:
        logger.setLevel(logging.DEBUG)
    elif args.verbose > 0:
        logger.setLevel(logging.INFO)
    script = SpotInstanceTest()
    if args.ACTION == 'create':
        script.create(args.instance_type, args.az)
    elif args.ACTION == 'cancel':
        script.cancel()
    else:
        script.list(args.instance_type, args.az)
