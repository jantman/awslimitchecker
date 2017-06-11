"""
awslimitchecker/tests/services/test_firehose.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2016 Hugo Lopes Tavares <hltbra@gmail.com>

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
Hugo Lopes Tavares <hltbra@gmail.com>
################################################################################
"""

import sys
from awslimitchecker.services.firehose import _FirehoseService
from awslimitchecker.tests.services import result_fixtures
from botocore.exceptions import EndpointConnectionError

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import call, patch, Mock
else:
    from unittest.mock import call, patch, Mock


fixtures = result_fixtures.Firehose()


class Test_FirehoseService(object):

    pbm = 'awslimitchecker.services.firehose'  # module patch base
    pb = '%s._FirehoseService' % pbm  # class patch pase

    def test_init(self):
        """test __init__()"""
        cls = _FirehoseService(21, 43)
        assert cls.service_name == 'Firehose'
        assert cls.api_name == 'firehose'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _FirehoseService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Delivery streams per region',
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _FirehoseService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        responses = fixtures.test_list_delivery_streams
        # create a flat list of delivery stream names from the fixture
        response_streams = []
        for resp in responses:
            for stream_name in resp['DeliveryStreamNames']:
                response_streams.append(stream_name)
        mock_conn = Mock()
        mock_conn.list_delivery_streams.side_effect = responses
        cls = _FirehoseService(21, 43, {'region_name': 'us-west-2'})
        cls.conn = mock_conn
        cls.find_usage()
        assert mock_conn.list_delivery_streams.call_count == len(responses)
        assert cls._have_usage is True
        usage = cls.limits['Delivery streams per region'].get_current_usage()
        assert len(usage) == 1
        assert usage[0].value == len(response_streams)
        assert usage[0].resource_id == 'us-west-2'
        assert usage[0].aws_type == 'AWS::KinesisFirehose::DeliveryStream'

    def test_required_iam_permissions(self):
        cls = _FirehoseService(21, 43)
        assert cls.required_iam_permissions() == [
            "firehose:ListDeliveryStreams",
        ]

    def test_find_usage_with_endpoint_connection_error(self):
        mock_conn = Mock()
        client_error = EndpointConnectionError(
            endpoint_url='https://firehose.bad-region.amazonaws.com/')
        mock_conn.list_delivery_streams.side_effect = client_error
        cls = _FirehoseService(21, 43)
        cls.conn = mock_conn
        with patch('%s.logger' % self.pbm, autospec=True) as mock_logger:
            cls.find_usage()
        error_msg = (
            'Caught exception when trying to use Firehose ('
            'perhaps the Firehose service is not available in this region?): '
            '%s')
        assert call.warning(error_msg, client_error) in mock_logger.mock_calls
