"""
awslimitchecker/tests/services/test_base.py

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
bugs please submit them at <https://github.com/jantman/pydnstest> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

from mock import Mock, patch, call
from awslimitchecker.services.base import _AwsService
from awslimitchecker.services import _services
import pytest


class Test_AwsService(object):

    def test_init(self):
        with pytest.raises(TypeError) as excinfo:
            _AwsService()
        assert excinfo.value.message == "Can't instantiate abstract class " \
            "_AwsService with abstract methods " \
            "connect" \
            ", find_usage" \
            ", get_limits" \
            ", required_iam_permissions"


class Test_AwsServiceSubclasses(object):

    def verify_subclass(self, clsname, cls):
        # ensure we set limits in the constructor
        mock_limits = Mock()
        mock_get_limits = Mock()
        mock_get_limits.return_value = mock_limits
        with patch.object(cls, 'get_limits', mock_get_limits):
            inst = cls()
        assert inst.limits == mock_limits
        assert mock_get_limits.mock_calls == [call()]
        # ensure service name is changed
        assert inst.service_name != 'baseclass'
        # ensure an IAM permissions list, even if empty
        assert isinstance(inst.required_iam_permissions(), list)

    def test_subclass_init(self):
        for clsname, cls in _services.iteritems():
            yield "verify_subclass %s" % clsname, \
                self.verify_subclass, clsname, cls
