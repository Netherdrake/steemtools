import datetime
import re
import time

import dateutil
from dateutil import parser

from funcy import contextmanager, decorator
from werkzeug.contrib.cache import SimpleCache


@contextmanager
def timeit():
    t1 = time.time()
    yield
    print("Time Elapsed: %.2f" % (time.time() - t1))


@decorator
def simple_cache(func, cache_obj, timeout=3600):
    if type(cache_obj) is not SimpleCache:
        return func()
    name = "%s_%s_%s" % (func._func.__name__, func._args, func._kwargs)
    cache_value = cache_obj.get(name)
    if cache_value:
        return cache_value
    else:
        out = func()
        cache_obj.set(name, out, timeout=timeout)
        return out


def read_asset(asset_string):
    re_asset = re.compile(r'(?P<number>\d*\.?\d+)\s?(?P<unit>[a-zA-Z]+)')
    res = re_asset.match(asset_string)
    return {'value': float(res.group('number')), 'symbol': res.group('unit')}


def parse_payout(payout):
    return read_asset(payout)['value']


def time_diff(time1, time2):
    time1 = parser.parse(time1 + "UTC").timestamp()
    time2 = parser.parse(time2 + "UTC").timestamp()
    return time2 - time1


def is_comment(item):
    if item['permlink'][:3] == "re-":
        return True

    return False


def time_elapsed(time1):
    created_at = parser.parse(time1 + "UTC").timestamp()
    now_adjusted = time.time()
    return now_adjusted - created_at


def parse_time(block_time):
    return dateutil.parser.parse(block_time + "UTC").astimezone(datetime.timezone.utc)
