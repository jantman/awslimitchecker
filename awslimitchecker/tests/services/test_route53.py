"""
awslimitchecker/tests/services/Route53.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2015-2018 Jason Antman <jason@jasonantman.com>

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

import sys
from awslimitchecker.tests.services import result_fixtures
from awslimitchecker.services.route53 import _Route53Service

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT

pbm = 'awslimitchecker.services.route53'  # module patch base
pb = '%s._Route53Service' % pbm  # class patch pase


class Test_Route53Service(object):

    def test_init(self):
        """test __init__()"""
        cls = _Route53Service(21, 43)
        assert cls.service_name == 'Route53'
        assert cls.api_name == 'route53'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _Route53Service(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Hosted Zone RecordSets',
            'Hosted Zone VPC Associations',
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _Route53Service(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def mock_get_hosted_zone_limit(self, Type, HostedZoneId):
        if HostedZoneId in result_fixtures.Route53.test_get_hosted_zone_limit:
            return result_fixtures.Route53.test_get_hosted_zone_limit[
                HostedZoneId][Type]

    def test_find_usage(self):
        """test find usage method calls other methods"""
        mock_conn = Mock()
        with patch('%s.connect' % pb) as mock_connect:
            with patch.multiple(
                    pb,
                    _find_usage_recordsets=DEFAULT,
                    _find_usage_vpc_associations=DEFAULT,
            ) as mocks:
                cls = _Route53Service(21, 43)
                cls.conn = mock_conn
                assert cls._have_usage is False
                cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        assert mock_conn.mock_calls == []
        for x in [
            '_find_usage_recordsets',
            '_find_usage_vpc_associations',
        ]:
            assert mocks[x].mock_calls == [call()]

    def test_find_usage_recordsets(self):
        cls = _Route53Service(21, 43)
        self._mock_reponse_init(cls)
        cls._find_usage_recordsets()

        limit_key = cls.MAX_RRSETS_BY_ZONE["name"]
        assert cls.limits[limit_key].get_current_usage()[0].get_value() == 7500
        assert cls.limits[limit_key].get_current_usage()[1].get_value() == 2500
        assert cls.limits[limit_key].get_current_usage()[2].get_value() == 5678

        # retest to validate cache
        cls._find_usage_recordsets()
        assert cls.limits[limit_key].get_current_usage()[0].get_value() == 7500
        assert cls.limits[limit_key].get_current_usage()[1].get_value() == 2500

    def test_find_usage_vpc_associations(self):
        cls = _Route53Service(21, 43)
        self._mock_reponse_init(cls)
        cls._find_usage_vpc_associations()

        limit_key = cls.MAX_VPCS_ASSOCIATED_BY_ZONE["name"]
        assert cls.limits[limit_key].get_current_usage()[0].get_value() == 10
        assert cls.limits[limit_key].get_current_usage()[1].get_value() == 2

        # retest to validate cache
        cls._find_usage_vpc_associations()
        assert cls.limits[limit_key].get_current_usage()[0].get_value() == 10
        assert cls.limits[limit_key].get_current_usage()[1].get_value() == 2

    def _mock_reponse_init(self, cls):
        response = result_fixtures.Route53.test_get_hosted_zones
        mock_conn = Mock()
        mock_conn.list_hosted_zones.return_value = response
        mock_conn.get_hosted_zone_limit = self.mock_get_hosted_zone_limit
        cls.conn = mock_conn

    def test_update_limits_from_api(self):
        cls = _Route53Service(21, 43)
        self._mock_reponse_init(cls)
        cls._update_limits_from_api()

        limit_key = cls.MAX_RRSETS_BY_ZONE["name"]
        assert cls.limits[limit_key].get_limit() == 10000

        limit_key = cls.MAX_VPCS_ASSOCIATED_BY_ZONE["name"]
        assert cls.limits[limit_key].get_limit() == 100

    def test_required_iam_permissions(self):
        cls = _Route53Service(21, 43)
        assert cls.required_iam_permissions() == [
            "route53:GetHostedZone",
            "route53:ListHostedZones",
        ]
