"""
awslimitchecker/tests/alerts/test_base.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2015-2019 Jason Antman <jason@jasonantman.com>

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

from awslimitchecker.alerts.base import AlertProvider
from awslimitchecker.alerts import Dummy, PagerDutyV1

import pytest


class APTester(AlertProvider):

    def on_success(self):
        pass

    def on_critical(self):
        pass

    def on_warning(self):
        pass


class TestAlertProvider(object):

    def test_init(self):
        cls = APTester('foo')
        assert cls._region_name == 'foo'

    def test_providers_by_name(self):
        assert AlertProvider.providers_by_name() == {
            'APTester': APTester,
            'Dummy': Dummy,
            'PagerDutyV1': PagerDutyV1
        }

    def test_get_provider_by_name(self):
        assert AlertProvider.get_provider_by_name('APTester') == APTester

    def test_get_provider_by_name_exception(self):
        with pytest.raises(RuntimeError) as exc:
            AlertProvider.get_provider_by_name('3993fhej')
        assert str(exc.value) == 'ERROR: "3993fhej" is not a valid ' \
                                 'AlertProvider class name'
