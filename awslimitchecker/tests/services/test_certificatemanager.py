"""
awslimitchecker/tests/services/test_certificatemanager.py

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
from awslimitchecker.services.certificatemanager import \
    _CertificatemanagerService

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT


pbm = 'awslimitchecker.services.certificatemanager'  # module patch base
pb = '%s._CertificatemanagerService' % pbm  # class patch pase


class Test_CertificatemanagerService(object):

    def test_init(self):
        """test __init__()"""
        cls = _CertificatemanagerService(21, 43, {}, None)
        assert cls.service_name == 'CertificateManager'
        assert cls.api_name == 'acm'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_get_limits(self):
        cls = _CertificatemanagerService(21, 43, {}, None)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'ACM certificates',
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _CertificatemanagerService(21, 43, {}, None)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        """
        Test overall find_usage method
        Check that find_usage() method calls the other methods.
        """
        with patch.multiple(
            pb,
            connect=DEFAULT,
            _find_usage_certificates=DEFAULT,
            autospec=True
        ) as mocks:
            cls = _CertificatemanagerService(21, 43, {}, None)
            assert cls._have_usage is False
            cls.find_usage()

        assert cls._have_usage is True
        assert len(mocks) == 2
        # the other methods should have been called
        for x in [
            "_find_usage_certificates"
        ]:
            assert mocks[x].mock_calls == [call(cls)]

    def test_find_usage_certificates_empty(self):
        """
        Verify the correctness of usage (when there are no certificates)
        This test mocks the AWS list_certificates response (after pagination).
        """
        # Setup the mock and call the tested function
        resp = result_fixtures.CertificateManager\
            .test_find_usage_certificates_empty
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CertificatemanagerService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = resp
            cls._find_usage_certificates()

        # Check that usage values are correctly set
        assert len(
            cls.limits["ACM certificates"].get_current_usage()
        ) == 1
        assert (
            cls.limits["ACM certificates"].get_current_usage()[0]
            .get_value() == 0
        )
        assert (
            cls.limits["ACM certificates"].get_current_usage()[0]
            .resource_id is None
        )

    def test_find_usage_certificates(self):
        """
        Verify the correctness of usage
        This test mocks the AWS list_certificates response (after pagination).
        """
        # Setup the mock and call the tested function
        resp = result_fixtures.CertificateManager.test_find_usage_certificates
        mock_conn = Mock()
        with patch("%s.paginate_dict" % pbm) as mock_paginate:
            cls = _CertificatemanagerService(21, 43, {}, None)
            cls.conn = mock_conn
            mock_paginate.return_value = resp
            cls._find_usage_certificates()

        # Check that usage values are correctly set
        assert len(
            cls.limits["ACM certificates"].get_current_usage()
        ) == 1
        assert (
            cls.limits["ACM certificates"].get_current_usage()[0]
            .get_value() == 3
        )
        assert (
            cls.limits["ACM certificates"].get_current_usage()[0]
            .resource_id is None
        )

    def test_required_iam_permissions(self):
        cls = _CertificatemanagerService(21, 43, {}, None)
        assert cls.required_iam_permissions() == [
            "acm:ListCertificates"
        ]
