"""
awslimitchecker/tests/metrics/test_base.py

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

from awslimitchecker.metrics.base import MetricsProvider
from awslimitchecker.metrics import Dummy, Datadog

import pytest


class MPTester(MetricsProvider):

    def flush(self):
        pass


class TestMetricsProvider(object):

    def test_init(self):
        cls = MPTester('foo')
        assert cls._region_name == 'foo'
        assert cls._duration == 0.0
        assert cls._limits == []

    def test_set_run_duration(self):
        cls = MPTester('foo')
        assert cls._duration == 0.0
        cls.set_run_duration(123.45)
        assert cls._duration == 123.45

    def test_add_limit(self):
        cls = MPTester('foo')
        assert cls._limits == []
        cls.add_limit(1)
        cls.add_limit(2)
        assert cls._limits == [1, 2]

    def test_providers_by_name(self):
        assert MetricsProvider.providers_by_name() == {
            'Dummy': Dummy,
            'MPTester': MPTester,
            'Datadog': Datadog
        }

    def test_get_provider_by_name(self):
        assert MetricsProvider.get_provider_by_name('Dummy') == Dummy

    def test_get_provider_by_name_exception(self):
        with pytest.raises(RuntimeError) as exc:
            MetricsProvider.get_provider_by_name('3993fhej')
        assert str(exc.value) == 'ERROR: "3993fhej" is not a valid ' \
                                 'MetricsProvider class name'
