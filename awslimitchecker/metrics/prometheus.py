import logging
import time
import os

from string import maketrans
from awslimitchecker.checker import AwsLimitChecker
from prometheus_client import start_http_server, Summary, Gauge


REQUEST_TIME = Summary(
                        'update_processing_seconds',
                        'Time spent querying aws for limits'
                    )
gauges = {}
trantab = maketrans(' -.', '___')


def main():
    port = int(os.environ.get('ALC_PORT', '8080'))
    interval = int(os.environ.get('ALC_INTERVAL', '60'))
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)

    checkers = {}
    for region in ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']:
        checkers[region] = AwsLimitChecker(region=region)

    start_http_server(port)
    for region, checker in checkers.iteritems():
        update(checker, region)
        time.sleep(interval)


@REQUEST_TIME.time()
def update(checker, region):
    try:
        checker.find_usage()

        labels = {'region': region}
        for service, svc_limits in sorted(checker.get_limits().items()):
            for limit_name, limit in sorted(svc_limits.items()):
                path = '.'.join([service, limit_name])
                usage = limit.get_current_usage()
                metric = limit.get_limit()
                update_service(path, usage, metric, region)
    except Exception as e:
        logging.exception("message")


def update_service(path, usage, limit, region):
    g = gauge(path)

    g.labels(region=region, type='limit').set(limit)
    for resource in usage:
        metric_type = 'current'
        if resource.resource_id:
            metric_type = resource.resource_id
        g.labels(region=region, type=metric_type).set(resource.get_value())


def gauge(path):
    path = path.lower().translate(trantab, '()')
    g = gauges.get(path, None)
    if g is None:
        g = Gauge(path, '', ['region', 'type'])
        gauges[path] = g
    return g


if __name__ == "__main__":
    main()
