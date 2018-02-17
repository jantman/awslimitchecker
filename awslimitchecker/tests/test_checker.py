"""
awslimitchecker/tests/test_checker.py

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

from awslimitchecker.services.base import _AwsService
from awslimitchecker.checker import AwsLimitChecker
from awslimitchecker.version import _get_version_info
from awslimitchecker.limit import AwsLimit
from awslimitchecker.trustedadvisor import TrustedAdvisor
from .support import sample_limits


# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT
else:
    from unittest.mock import patch, call, Mock, DEFAULT

pbm = 'awslimitchecker.checker'  # patch base path - module
pb = '%s.AwsLimitChecker' % pbm  # patch base path


class ApiServiceSpec(_AwsService):
    """
    Used for Mock's ``spec_set`` parameter to represent classes that have
    an ``_update_limits_from_api`` method.
    """

    def _update_limits_from_api(self):
        pass


class TestAwsLimitChecker(object):

    def setup(self):
        self.mock_ver_info = Mock(
            release='1.2.3',
            url='http://myurl',
            commit='abcd',
            tag='mytag',
            version_str='1.2.3@mytag'
        )
        self.mock_svc1 = Mock(spec_set=_AwsService)
        self.mock_svc2 = Mock(spec_set=ApiServiceSpec)
        self.mock_foo = Mock(spec_set=_AwsService)
        self.mock_bar = Mock(spec_set=_AwsService)
        self.mock_ta = Mock(spec_set=TrustedAdvisor)
        self.mock_foo.return_value = self.mock_svc1
        self.mock_bar.return_value = self.mock_svc2
        self.svcs = {'SvcFoo': self.mock_foo, 'SvcBar': self.mock_bar}
        with patch.dict('%s._services' % pbm, values=self.svcs, clear=True):
            with patch.multiple(
                    'awslimitchecker.checker',
                    logger=DEFAULT,
                    _get_version_info=DEFAULT,
                    TrustedAdvisor=DEFAULT,
                    _get_latest_version=DEFAULT,
                    autospec=True,
            ) as mocks:
                self.mock_logger = mocks['logger']
                self.mock_version = mocks['_get_version_info']
                self.mock_ta_constr = mocks['TrustedAdvisor']
                self.mock_glv = mocks['_get_latest_version']
                mocks['TrustedAdvisor'].return_value = self.mock_ta
                mocks['_get_latest_version'].return_value = None
                self.mock_version.return_value = self.mock_ver_info
                self.cls = AwsLimitChecker(check_version=False)

    def test_init(self):
        # dict should be of _AwsService instances
        services = {
            'SvcFoo': self.mock_svc1,
            'SvcBar': self.mock_svc2
        }
        assert self.cls.services == services
        # _AwsService instances should exist, but have no other calls
        assert self.mock_foo.mock_calls == [
            call(80, 99, {'region_name': None})
        ]
        assert self.mock_bar.mock_calls == [
            call(80, 99, {'region_name': None})
        ]
        assert self.mock_ta_constr.mock_calls == [
            call(services, {'region_name': None},
                 ta_refresh_mode=None, ta_refresh_timeout=None)
        ]
        assert self.mock_svc1.mock_calls == []
        assert self.mock_svc2.mock_calls == []
        assert self.cls.ta == self.mock_ta
        assert self.mock_version.mock_calls == [call()]
        assert self.cls.vinfo == self.mock_ver_info
        assert self.mock_glv.mock_calls == []
        assert self.mock_logger.mock_calls == [
            call.debug('Connecting to region %s', None)
        ]

    def test_init_AGPL_message(self, capsys):
        # get rid of the class
        self.cls = None
        # clear out/err
        out, err = capsys.readouterr()
        # run setup again
        self.setup()
        # check out/err
        out, err = capsys.readouterr()
        assert out == ''
        assert (err) == (
            "awslimitchecker 1.2.3@mytag is AGPL-licensed free software; "
            "all users have a right to the full source code of "
            "this version. See <http://myurl>\n")

    def test_check_version_old(self):
        with patch.multiple(
            'awslimitchecker.checker',
            logger=DEFAULT,
            _get_version_info=DEFAULT,
            TrustedAdvisor=DEFAULT,
            _get_latest_version=DEFAULT,
            autospec=True,
        ) as mocks:
            mocks['_get_version_info'].return_value = self.mock_ver_info
            mocks['_get_latest_version'].return_value = '3.4.5'
            AwsLimitChecker()
        assert mocks['_get_latest_version'].mock_calls == [call()]
        assert mocks['logger'].mock_calls == [
            call.warning(
                'You are running awslimitchecker %s, but the latest version'
                ' is %s; please consider upgrading.', '1.2.3', '3.4.5'
            ),
            call.debug('Connecting to region %s', None)
        ]

    def test_check_version_not_old(self):
        with patch.multiple(
            'awslimitchecker.checker',
            logger=DEFAULT,
            _get_version_info=DEFAULT,
            TrustedAdvisor=DEFAULT,
            _get_latest_version=DEFAULT,
            autospec=True,
        ) as mocks:
            mocks['_get_version_info'].return_value = self.mock_ver_info
            mocks['_get_latest_version'].return_value = None
            AwsLimitChecker()
        assert mocks['_get_latest_version'].mock_calls == [call()]
        assert mocks['logger'].mock_calls == [
            call.debug('Connecting to region %s', None)
        ]

    def test_init_thresholds(self):
        mock_svc1 = Mock(spec_set=_AwsService)
        mock_svc2 = Mock(spec_set=_AwsService)
        mock_foo = Mock(spec_set=_AwsService)
        mock_bar = Mock(spec_set=_AwsService)
        mock_ta = Mock(spec_set=TrustedAdvisor)
        mock_foo.return_value = mock_svc1
        mock_bar.return_value = mock_svc2
        svcs = {'SvcFoo': mock_foo, 'SvcBar': mock_bar}
        with patch.dict('%s._services' % pbm, values=svcs, clear=True):
            with patch.multiple(
                    'awslimitchecker.checker',
                    logger=DEFAULT,
                    _get_version_info=DEFAULT,
                    TrustedAdvisor=DEFAULT,
                    _get_latest_version=DEFAULT,
                    autospec=True,
            ) as mocks:
                mock_version = mocks['_get_version_info']
                mock_version.return_value = self.mock_ver_info
                mock_ta_constr = mocks['TrustedAdvisor']
                mocks['TrustedAdvisor'].return_value = mock_ta
                mocks['_get_latest_version'].return_value = None
                cls = AwsLimitChecker(
                    warning_threshold=5,
                    critical_threshold=22,
                )
        # dict should be of _AwsService instances
        services = {
            'SvcFoo': mock_svc1,
            'SvcBar': mock_svc2
        }
        assert cls.services == services
        # _AwsService instances should exist, but have no other calls
        assert mock_foo.mock_calls == [
            call(5, 22, {'region_name': None})
        ]
        assert mock_bar.mock_calls == [
            call(5, 22, {'region_name': None})
        ]
        assert mock_ta_constr.mock_calls == [
            call(services, {'region_name': None},
                 ta_refresh_mode=None, ta_refresh_timeout=None)
        ]
        assert mock_svc1.mock_calls == []
        assert mock_svc2.mock_calls == []
        assert self.mock_version.mock_calls == [call()]
        assert self.cls.vinfo == self.mock_ver_info

    def test_init_region_profile(self):
        mock_svc1 = Mock(spec_set=_AwsService)
        mock_svc2 = Mock(spec_set=_AwsService)
        mock_foo = Mock(spec_set=_AwsService)
        mock_bar = Mock(spec_set=_AwsService)
        mock_ta = Mock(spec_set=TrustedAdvisor)
        mock_foo.return_value = mock_svc1
        mock_bar.return_value = mock_svc2
        svcs = {'SvcFoo': mock_foo, 'SvcBar': mock_bar}
        with patch('%s.boto3' % pbm) as mock_boto3:
            with patch.dict('%s._services' % pbm, values=svcs, clear=True):
                with patch.multiple(
                        'awslimitchecker.checker',
                        logger=DEFAULT,
                        _get_version_info=DEFAULT,
                        TrustedAdvisor=DEFAULT,
                        _get_latest_version=DEFAULT,
                        autospec=True,
                ) as mocks:
                    mock_boto3.Session.return_value._session = Mock()
                    mock_version = mocks['_get_version_info']
                    mock_version.return_value = self.mock_ver_info
                    mocks['TrustedAdvisor'].return_value = mock_ta
                    mocks['_get_latest_version'].return_value = None
                    cls = AwsLimitChecker(region='regionX', profile_name='foo')
        # dict should be of _AwsService instances
        services = {
            'SvcFoo': mock_svc1,
            'SvcBar': mock_svc2
        }
        assert cls.profile_name == 'foo'
        assert cls.region == 'regionX'
        assert cls.services == services
        assert mock_svc1.mock_calls == []
        assert mock_svc2.mock_calls == []
        assert self.mock_version.mock_calls == [call()]
        assert self.cls.vinfo == self.mock_ver_info

    def test_init_sts(self):
        mock_svc1 = Mock(spec_set=_AwsService)
        mock_svc2 = Mock(spec_set=_AwsService)
        mock_foo = Mock(spec_set=_AwsService)
        mock_bar = Mock(spec_set=_AwsService)
        mock_ta = Mock(spec_set=TrustedAdvisor)
        mock_foo.return_value = mock_svc1
        mock_bar.return_value = mock_svc2
        svcs = {'SvcFoo': mock_foo, 'SvcBar': mock_bar}
        with patch('%s.boto3' % pbm):
            with patch.dict('%s._services' % pbm, values=svcs, clear=True):
                with patch.multiple(
                    'awslimitchecker.checker',
                    logger=DEFAULT,
                    _get_version_info=DEFAULT,
                    TrustedAdvisor=DEFAULT,
                    _get_latest_version=DEFAULT,
                    autospec=True,
                ) as mocks:
                    mock_version = mocks['_get_version_info']
                    mock_version.return_value = self.mock_ver_info
                    mocks['TrustedAdvisor'].return_value = mock_ta
                    mocks['_get_latest_version'].return_value = None
                    cls = AwsLimitChecker(
                        account_id='123456789012',
                        account_role='myrole',
                        region='myregion'
                    )
        # dict should be of _AwsService instances
        services = {
            'SvcFoo': mock_svc1,
            'SvcBar': mock_svc2
        }
        assert cls.services == services
        assert mock_svc1.mock_calls == []
        assert mock_svc2.mock_calls == []
        assert self.mock_version.mock_calls == [call()]
        assert self.cls.vinfo == self.mock_ver_info

    def test_init_sts_external_id_ta_refresh(self):
        mock_svc1 = Mock(spec_set=_AwsService)
        mock_svc2 = Mock(spec_set=_AwsService)
        mock_foo = Mock(spec_set=_AwsService)
        mock_bar = Mock(spec_set=_AwsService)
        mock_ta = Mock(spec_set=TrustedAdvisor)
        mock_foo.return_value = mock_svc1
        mock_bar.return_value = mock_svc2
        svcs = {'SvcFoo': mock_foo, 'SvcBar': mock_bar}
        with patch('%s.boto3' % pbm):
            with patch.dict('%s._services' % pbm, values=svcs, clear=True):
                with patch.multiple(
                        'awslimitchecker.checker',
                        logger=DEFAULT,
                        _get_version_info=DEFAULT,
                        TrustedAdvisor=DEFAULT,
                        _get_latest_version=DEFAULT,
                        autospec=True,
                ) as mocks:
                    mock_version = mocks['_get_version_info']
                    mock_version.return_value = self.mock_ver_info
                    mocks['TrustedAdvisor'].return_value = mock_ta
                    mocks['_get_latest_version'].return_value = None
                    cls = AwsLimitChecker(
                        account_id='123456789012',
                        account_role='myrole',
                        region='myregion',
                        external_id='myextid',
                        mfa_serial_number=123,
                        mfa_token=456,
                        ta_refresh_mode=123,
                        ta_refresh_timeout=456
                    )
        # dict should be of _AwsService instances
        services = {
            'SvcFoo': mock_svc1,
            'SvcBar': mock_svc2
        }
        assert cls.services == services
        assert mock_svc1.mock_calls == []
        assert mock_svc2.mock_calls == []
        assert self.mock_version.mock_calls == [call()]
        assert self.cls.vinfo == self.mock_ver_info

    def test_boto3_connection_kwargs(self):
        cls = AwsLimitChecker()

        with patch('%s._get_sts_token' % pb) as mock_get_sts:
            with patch('%s.logger' % pbm) as mock_logger:
                with patch('%s.boto3.Session' % pbm) as mock_sess:
                    res = cls._boto_conn_kwargs
        assert mock_get_sts.mock_calls == []
        assert mock_logger.mock_calls == [
            call.debug('Connecting to region %s', None)
        ]
        assert mock_sess.mock_calls == []
        assert res == {
            'region_name': None
        }

    def test_boto3_connection_kwargs_profile(self):
        with patch('%s.boto3' % pbm):
            with patch(
                'awslimitchecker.services.dynamodb._DynamodbService'
                '.get_limits'
            ):
                cls = AwsLimitChecker(profile_name='myprof')
        m_creds = Mock()
        type(m_creds).access_key = 'ak'
        type(m_creds).secret_key = 'sk'
        type(m_creds).token = 'tkn'
        mock_session = Mock()
        m_sess = Mock()
        m_sess.get_credentials.return_value = m_creds
        type(mock_session)._session = m_sess

        with patch('%s._get_sts_token' % pb) as mock_get_sts:
            with patch('%s.logger' % pbm) as mock_logger:
                with patch('%s.boto3.Session' % pbm) as mock_sess:
                    mock_sess.return_value = mock_session
                    res = cls._boto_conn_kwargs
        assert mock_get_sts.mock_calls == []
        assert mock_logger.mock_calls == [
            call.debug('Using credentials profile: %s', 'myprof')
        ]
        assert mock_sess.mock_calls == [call(profile_name='myprof')]
        assert res == {
            'region_name': None,
            'aws_access_key_id': 'ak',
            'aws_secret_access_key': 'sk',
            'aws_session_token': 'tkn'
        }

    def test_boto3_connection_kwargs_region(self):
        with patch('%s.boto3' % pbm):
            cls = AwsLimitChecker(region='myregion')

        with patch('%s._get_sts_token' % pb) as mock_get_sts:
            with patch('%s.logger' % pbm) as mock_logger:
                with patch('%s.boto3.Session' % pbm) as mock_sess:
                    res = cls._boto_conn_kwargs
        assert mock_get_sts.mock_calls == []
        assert mock_logger.mock_calls == [
            call.debug('Connecting to region %s', 'myregion')
        ]
        assert mock_sess.mock_calls == []
        assert res == {
            'region_name': 'myregion'
        }

    def test_boto3_connection_kwargs_sts(self):
        with patch('%s.boto3' % pbm):
            with patch(
                'awslimitchecker.services.dynamodb._DynamodbService'
                '.get_limits'
            ):
                cls = AwsLimitChecker(account_id='123',
                                      account_role='myrole',
                                      region='myregion')
        mock_creds = Mock()
        type(mock_creds).access_key = 'sts_ak'
        type(mock_creds).secret_key = 'sts_sk'
        type(mock_creds).session_token = 'sts_token'

        with patch('%s._get_sts_token' % pb) as mock_get_sts:
            with patch('%s.logger' % pbm) as mock_logger:
                with patch('%s.boto3.Session' % pbm) as mock_sess:
                    mock_get_sts.return_value = mock_creds
                    res = cls._boto_conn_kwargs
        assert mock_get_sts.mock_calls == [call()]
        assert mock_logger.mock_calls == [
            call.debug("Connecting for account %s role '%s' with STS "
                       "(region: %s)", '123', 'myrole', 'myregion')
        ]
        assert mock_sess.mock_calls == []
        assert res == {
            'region_name': 'myregion',
            'aws_access_key_id': 'sts_ak',
            'aws_secret_access_key': 'sts_sk',
            'aws_session_token': 'sts_token'
        }

    def test_get_version(self):
        with patch('%s._get_version_info' % pbm,
                   spec_set=_get_version_info) as mock_version:
            self.cls.vinfo = self.mock_ver_info
            res = self.cls.get_version()
        assert res == '1.2.3@mytag'
        assert mock_version.mock_calls == []

    def test_get_project_url(self):
        with patch('%s._get_version_info' % pbm,
                   spec_set=_get_version_info) as mock_version:
            self.cls.vinfo = self.mock_ver_info
            res = self.cls.get_project_url()
        assert res == 'http://myurl'
        assert mock_version.mock_calls == []

    def test_remove_services_none(self):
        self.cls.remove_services()
        assert self.cls.services == {
            'SvcFoo': self.mock_svc1,
            'SvcBar': self.mock_svc2
        }

    def test_remove_services_one(self):
        self.cls.remove_services(['SvcFoo'])
        assert self.cls.services == {
            'SvcBar': self.mock_svc2
        }

    def test_remove_services_all(self):
        self.cls.remove_services(['SvcFoo', 'SvcBar'])
        assert self.cls.services == {}

    def test_get_service_names(self):
        res = self.cls.get_service_names()
        assert res == ['SvcBar', 'SvcFoo']

    def test_get_limits(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.mock_svc2.get_limits.return_value = limits['SvcBar']
        res = self.cls.get_limits()
        assert res == limits
        assert self.mock_ta.mock_calls == [
            call.update_limits()
        ]
        assert self.mock_svc1.mock_calls == [
            call.get_limits()
        ]
        assert self.mock_svc2.mock_calls == [
            call._update_limits_from_api(),
            call.get_limits()
        ]

    def test_get_limits_no_ta(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.mock_svc2.get_limits.return_value = limits['SvcBar']
        res = self.cls.get_limits(use_ta=False)
        assert res == limits
        assert self.mock_ta.mock_calls == []
        assert self.mock_svc1.mock_calls == [
            call.get_limits()
        ]
        assert self.mock_svc2.mock_calls == [
            call._update_limits_from_api(),
            call.get_limits()
        ]

    def test_get_limits_service(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.mock_svc2.get_limits.return_value = limits['SvcBar']
        res = self.cls.get_limits(service=['SvcFoo'])
        assert res == {'SvcFoo': limits['SvcFoo']}
        assert self.mock_ta.mock_calls == [
            call.update_limits()
        ]
        assert self.mock_svc1.mock_calls == [
            call.get_limits()
        ]
        assert self.mock_svc2.mock_calls == []

    def test_get_limits_service_with_api(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.mock_svc2.get_limits.return_value = limits['SvcBar']
        res = self.cls.get_limits(service=['SvcBar'])
        assert res == {'SvcBar': limits['SvcBar']}
        assert self.mock_ta.mock_calls == [
            call.update_limits()
        ]
        assert self.mock_svc1.mock_calls == []
        assert self.mock_svc2.mock_calls == [
            call._update_limits_from_api(),
            call.get_limits()
        ]

    def test_find_usage(self):
        self.cls.find_usage()
        assert self.mock_svc1.mock_calls == [
            call.find_usage()
        ]
        assert self.mock_svc2.mock_calls == [
            call._update_limits_from_api(),
            call.find_usage()
        ]
        assert self.mock_ta.mock_calls == [
            call.update_limits()
        ]

    def test_find_usage_no_ta(self):
        self.cls.find_usage(use_ta=False)
        assert self.mock_svc1.mock_calls == [
            call.find_usage()
        ]
        assert self.mock_svc2.mock_calls == [
            call._update_limits_from_api(),
            call.find_usage()
        ]
        assert self.mock_ta.mock_calls == []

    def test_find_usage_service(self):
        self.cls.find_usage(service=['SvcFoo'])
        assert self.mock_svc1.mock_calls == [
            call.find_usage()
        ]
        assert self.mock_svc2.mock_calls == []
        assert self.mock_ta.mock_calls == [
            call.update_limits()
        ]

    def test_find_usage_service_with_api(self):
        self.cls.find_usage(service=['SvcBar'])
        assert self.mock_svc1.mock_calls == []
        assert self.mock_svc2.mock_calls == [
            call._update_limits_from_api(),
            call.find_usage()
        ]
        assert self.mock_ta.mock_calls == [
            call.update_limits()
        ]

    def test_set_threshold_overrides(self):
        limits = sample_limits()
        limits['SvcFoo']['zz3'] = AwsLimit(
            'zz3',
            self.mock_svc1,
            1,
            2,
            3,
        )
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.mock_svc2.get_limits.return_value = limits['SvcBar']
        overrides = {
            'SvcBar': {
                'barlimit1': {
                    'warning': {
                        'percent': 10,
                        'count': 12
                    },
                    'critical': {
                        'percent': 14,
                        'count': 16
                    }
                },
                'bar limit2': {
                    'critical': {
                        'count': 15,
                    }
                },
                'zz3': {
                    'warning': {
                        'count': 41
                    },
                    'critical': {
                        'percent': 52
                    }
                }
            },
            'SvcFoo': {
                'foo limit3': {
                    'warning': {
                        'percent': 91
                    },
                }
            },
        }
        self.cls.set_threshold_overrides(overrides)
        assert self.mock_svc1.mock_calls == [
            call.set_threshold_override(
                'foo limit3',
                warn_percent=91,
            )
        ]
        assert self.mock_svc2.mock_calls == [
            call.set_threshold_override(
                'bar limit2',
                crit_count=15
            ),
            call.set_threshold_override(
                'barlimit1',
                warn_percent=10,
                warn_count=12,
                crit_percent=14,
                crit_count=16
            ),
            call.set_threshold_override(
                'zz3',
                warn_count=41,
                crit_percent=52
            ),
        ]

    def test_set_limit_overrides(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.mock_svc2.get_limits.return_value = limits['SvcBar']
        overrides = {
            'SvcBar': {
                'barlimit1': 100,
            },
            'SvcFoo': {
                'foo limit3': 99,
            },
        }
        self.cls.set_limit_overrides(overrides)
        assert self.mock_svc1.mock_calls == [
            call.set_limit_override('foo limit3', 99, override_ta=True)
        ]
        assert self.mock_svc2.mock_calls == [
            call.set_limit_override('barlimit1', 100, override_ta=True)
        ]

    def test_set_limit_overrides_ta(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.mock_svc2.get_limits.return_value = limits['SvcBar']
        overrides = {
            'SvcBar': {
                'bar limit2': 100,
            },
            'SvcFoo': {
                'foo limit3': 3,
            },
        }
        self.cls.set_limit_overrides(overrides, override_ta=False)
        assert self.mock_svc1.mock_calls == [
            call.set_limit_override('foo limit3', 3, override_ta=False)
        ]
        assert self.mock_svc2.mock_calls == [
            call.set_limit_override('bar limit2', 100, override_ta=False)
        ]

    def test_set_limit_override(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.cls.set_limit_override('SvcFoo', 'foo limit3', 99)
        assert self.mock_svc1.mock_calls == [
            call.set_limit_override('foo limit3', 99, override_ta=True)
        ]

    def test_set_limit_override_ta(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.cls.set_limit_override(
            'SvcFoo',
            'foo limit3',
            99,
            override_ta=False
        )
        assert self.mock_svc1.mock_calls == [
            call.set_limit_override(
                'foo limit3',
                99,
                override_ta=False
            )
        ]

    def test_set_threshold_override(self):
        limits = sample_limits()
        self.mock_svc1.get_limits.return_value = limits['SvcFoo']
        self.cls.set_threshold_override(
            'SvcFoo',
            'foo limit3',
            warn_percent=10,
            warn_count=12,
            crit_percent=14,
            crit_count=16
        )
        assert self.mock_svc1.mock_calls == [
            call.set_threshold_override(
                'foo limit3',
                warn_percent=10,
                warn_count=12,
                crit_percent=14,
                crit_count=16
            )
        ]

    def test_get_required_iam_policy(self):
        expected = {
            'Version': '2012-10-17',
            'Statement': [{
                'Effect': 'Allow',
                'Resource': '*',
                'Action': [
                    'ec2:bar',
                    'ec2:foo',
                    'foo:perm1',
                    'foo:perm2',
                    'support:*',
                    'trustedadvisor:Describe*',
                    'trustedadvisor:RefreshCheck'
                ],
            }],
        }
        self.mock_svc1.required_iam_permissions.return_value = [
            'ec2:foo',
            'ec2:bar',
            'foo:perm1'
        ]
        self.mock_svc2.required_iam_permissions.return_value = [
            'foo:perm1',
            'foo:perm2',
        ]
        res = self.cls.get_required_iam_policy()
        assert res == expected
        assert self.mock_svc1.mock_calls == [call.required_iam_permissions()]
        assert self.mock_svc2.mock_calls == [call.required_iam_permissions()]

    def test_check_thresholds(self):
        self.mock_svc1.check_thresholds.return_value = {
            'foo': 'bar',
            'baz': 'blam',
        }
        self.mock_svc2.check_thresholds.return_value = {}
        res = self.cls.check_thresholds()
        assert res == {
            'SvcFoo': {
                'foo': 'bar',
                'baz': 'blam',
            }
        }
        assert self.mock_ta.mock_calls == [
            call.update_limits(),
        ]
        assert self.mock_svc1.mock_calls == [
            call.check_thresholds()
        ]
        assert self.mock_svc2.mock_calls == [
            call._update_limits_from_api(),
            call.check_thresholds()
        ]

    def test_check_thresholds_service(self):
        self.mock_svc1.check_thresholds.return_value = {'foo': 'bar'}
        self.mock_svc2.check_thresholds.return_value = {'baz': 'blam'}
        res = self.cls.check_thresholds(service=['SvcFoo'])
        assert res == {
            'SvcFoo': {
                'foo': 'bar',
            }
        }
        assert self.mock_ta.mock_calls == [
            call.update_limits()
        ]
        assert self.mock_svc1.mock_calls == [
            call.check_thresholds()
        ]
        assert self.mock_svc2.mock_calls == []

    def test_check_thresholds_service_api(self):
        self.mock_svc1.check_thresholds.return_value = {'foo': 'bar'}
        self.mock_svc2.check_thresholds.return_value = {'baz': 'blam'}
        res = self.cls.check_thresholds(service=['SvcBar'])
        assert res == {
            'SvcBar': {
                'baz': 'blam',
            }
        }
        assert self.mock_ta.mock_calls == [
            call.update_limits()
        ]
        assert self.mock_svc1.mock_calls == []
        assert self.mock_svc2.mock_calls == [
            call._update_limits_from_api(),
            call.check_thresholds()
        ]

    def test_check_thresholds_no_ta(self):
        self.mock_svc1.check_thresholds.return_value = {
            'foo': 'bar',
            'baz': 'blam',
        }
        self.mock_svc2.check_thresholds.return_value = {}
        self.cls.use_ta = False
        res = self.cls.check_thresholds(use_ta=False)
        assert res == {
            'SvcFoo': {
                'foo': 'bar',
                'baz': 'blam',
            }
        }
        assert self.mock_ta.mock_calls == []
        assert self.mock_svc1.mock_calls == [
            call.check_thresholds()
        ]
        assert self.mock_svc2.mock_calls == [
            call._update_limits_from_api(),
            call.check_thresholds()
        ]
