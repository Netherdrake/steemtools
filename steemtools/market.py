import numpy as np
from steemtools.helpers import parse_payout
from steemtools.node import default


class Tickers(object):
    pass


class Market(Tickers):
    def __init__(self, steem=default()):
        self.steem = steem

    def avg_witness_price(self, take=10):
        price_history = self.steem.rpc.get_feed_history()['price_history']
        return np.mean([parse_payout(x['base']) for x in price_history[-take:]])
