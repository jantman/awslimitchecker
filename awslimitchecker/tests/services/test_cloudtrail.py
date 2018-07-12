import sys

from awslimitchecker.tests.services import result_fixtures
from awslimitchecker.limit import AwsLimit
from awslimitchecker.services.cloudtrail import _CloudTrailService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, Mock
else:
    from unittest.mock import patch, Mock

module_base = 'awslimitchecker.services.cloudtrail.'
PATCH_BASE = '%s_CloudTrailService' % module_base
AWS_TYPE = "AWS::CloudTrail::Trail"


class Test_CloudTrailService(object):

    def test_init(self):
        with patch('%s.get_limits' % PATCH_BASE):
            cls = _CloudTrailService(21, 43)
        assert cls.service_name == 'CloudTrail'
        assert cls.api_name == 'cloudtrail'
        assert cls.conn is None
        assert cls.resource_conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _CloudTrailService(21, 43)

        limit_dict = cls.get_limits()
        for limit in limit_dict:
            assert isinstance(limit_dict[limit], AwsLimit)
            assert limit == limit_dict[limit].name
            assert limit_dict[limit].service == cls
        assert len(limit_dict) == 3

        trails_limit = limit_dict['Trails Per Region']
        assert trails_limit.limit_type == AWS_TYPE
        assert trails_limit.default_limit == 5

        event_selectors_limit = limit_dict['Event Selectors Per Trail']
        assert event_selectors_limit.limit_type == AWS_TYPE
        assert event_selectors_limit.default_limit == 5

        data_resources_limit = limit_dict['Data Resources Per Trail']
        assert data_resources_limit.limit_type == AWS_TYPE
        assert data_resources_limit.default_limit == 250

    def test_get_limits_again(self):
        """Test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock(spec_set=AwsLimit)
        cls = _CloudTrailService(21, 43)
        cls.limits = mock_limits
        response = cls.get_limits()
        assert response == mock_limits

    def test_find_usage(self):
        mock_trails = Mock()
        mock_trails.describe_trails.return_value = \
            result_fixtures.CloudTrail.mock_describe_trails
        mock_trails.get_event_selectors.return_value = \
            result_fixtures.CloudTrail.mock_get_event_selectors

        with patch('%s.connect' % PATCH_BASE,) as mock_connect:
            cls = _CloudTrailService(21, 43)
            cls.conn = mock_trails
            assert cls._have_usage is False
            cls.find_usage()

        assert len(mock_connect.mock_calls) == 2
        assert cls._have_usage is True

        usage = cls.limits['Trails Per Region'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].get_value() == 3

        usage = cls.limits['Event Selectors Per Trail'].get_current_usage()
        assert len(usage) == 3
        assert usage[0].get_value() == 1
        assert usage[1].get_value() == 1
        assert usage[2].get_value() == 1

        usage = cls.limits['Data Resources Per Trail'].get_current_usage()
        assert len(usage) == 3
        assert usage[0].get_value() == 3
        assert usage[1].get_value() == 3
        assert usage[2].get_value() == 3

    def test_required_iam_permissions(self):
        cls = _CloudTrailService(21, 43)
        assert cls.required_iam_permissions() == [
            "cloudtrail:DescribeTrails",
            "cloudtrail:GetTrailStatus",
        ]
