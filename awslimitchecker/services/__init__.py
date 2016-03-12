"""
awslimitchecker/services/__init__.py

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

from awslimitchecker.services.base import _AwsService
from awslimitchecker.services.ec2 import _Ec2Service
from awslimitchecker.services.vpc import _VpcService
from awslimitchecker.services.autoscaling import _AutoscalingService
from awslimitchecker.services.ebs import _EbsService
from awslimitchecker.services.elb import _ElbService
from awslimitchecker.services.elasticache import _ElastiCacheService
from awslimitchecker.services.rds import _RDSService
from awslimitchecker.services.iam import _IamService

# dynamically generate the service name to class dict
_services = {}
for cls in _AwsService.__subclasses__():
    _services[cls.service_name] = cls
