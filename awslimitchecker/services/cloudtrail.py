import logging

from .base import _AwsService
from ..limit import AwsLimit

logger = logging.getLogger(__name__)


class _CloudTrailService(_AwsService):
    service_name = 'CloudTrail'
    api_name = 'cloudtrail'
    aws_type = 'AWS::CloudTrail::Trail'

    def find_usage(self):
        """
        Determine the current usage for each limit of this service,
        and update corresponding Limit via
        :py:meth:`~.AwsLimit._add_current_usage`.
        """
        logger.debug("Checking usage for service %s", self.service_name)

        self.connect()
        for lim in self.limits.values():
            lim._reset_usage()

        self._find_usage_cloudtrail()
        self._have_usage = True
        logger.debug("Done checking usage.")

    def _find_usage_cloudtrail(self):
        """Calculate current usage for CloudTrail related metrics"""

        trail_list = self.conn.describe_trails()['trailList']
        trail_count = len(trail_list) if trail_list else 0

        for trail in trail_list:
            data_resource_count = 0

            response = self.conn.get_event_selectors(TrailName=trail['Name'])
            event_selectors = response['EventSelectors']

            for event_selector in event_selectors:
                data_resources = event_selector['DataResources']
                data_resource_count += len(event_selector['DataResources']) \
                    if data_resources else 0

            self.limits['Event Selectors Per Trail']._add_current_usage(
                len(event_selectors),
                aws_type=self.aws_type
            )

            self.limits['Data Resources Per Trail']._add_current_usage(
                data_resource_count,
                aws_type=self.aws_type
            )

        self.limits['Trails Per Region']._add_current_usage(
            trail_count,
            aws_type=self.aws_type
        )

    def get_limits(self):
        """
        Return all known limits for this service, as a dict of their names
        to :py:class:`~.AwsLimit` objects.

        :returns: dict of limit names to :py:class:`~.AwsLimit` objects
        :rtype: dict
        """
        logger.debug("Gathering %s's limits from AWS", self.service_name)

        self.connect()

        if self.limits:
            return self.limits
        limits = {}

        limits['Trails Per Region'] = AwsLimit(
            'Trails Per Region',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type=self.aws_type
        )

        limits['Event Selectors Per Trail'] = AwsLimit(
            'Event Selectors Per Trail',
            self,
            5,
            self.warning_threshold,
            self.critical_threshold,
            limit_type=self.aws_type
        )

        limits['Data Resources Per Trail'] = AwsLimit(
            'Data Resources Per Trail',
            self,
            250,
            self.warning_threshold,
            self.critical_threshold,
            limit_type=self.aws_type
        )

        self.limits = limits
        return limits

    def required_iam_permissions(self):
        """
        Return a list of IAM Actions required for this Service to function
        properly. All Actions will be shown with an Effect of "Allow"
        and a Resource of "*".

        :returns: list of IAM Action strings
        :rtype: list
        """
        return [
            "cloudtrail:DescribeTrails",
            "cloudtrail:GetTrailStatus",
        ]
