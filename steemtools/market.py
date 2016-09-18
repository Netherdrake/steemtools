from decimal import Decimal

import numpy as np
import requests
from steemtools.helpers import parse_payout
from steemtools.node import Node


class Tickers(object):
    @staticmethod
    def btc_usd_ticker():
        prices = {}
        try:
            r = requests.get("https://api.bitfinex.com/v1/pubticker/BTCUSD").json()
            prices['bitfinex'] = {'price': float(r['last_price']), 'volume': float(r['volume'])}
        except:
            pass
        try:
            r = requests.get("https://api.exchange.coinbase.com/products/BTC-USD/ticker").json()
            prices['coinbase'] = {'price': float(r['price']), 'volume': float(r['volume'])}
        except:
            pass
        try:
            r = requests.get("https://www.okcoin.com/api/v1/ticker.do?symbol=btc_usd").json()["ticker"]
            prices['okcoin'] = {'price': float(r['last']), 'volume': float(r['vol'])}
        except:
            pass
        try:
            r = requests.get("https://www.bitstamp.net/api/v2/ticker/btcusd/").json()
            prices['bitstamp'] = {'price': float(r['last']), 'volume': float(r['volume'])}
        except:
            pass

        # vwap
        return np.average([x['price'] for x in prices.values()], weights=[x['volume'] for x in prices.values()])

    @staticmethod
    def steem_btc_ticker():
        prices = {}
        try:
            r = requests.get("https://poloniex.com/public?command=returnTicker").json()["BTC_STEEM"]
            prices['poloniex'] = {'price': float(r['last']), 'volume': float(r['baseVolume'])}
        except:
            pass
        try:
            r = requests.get("https://bittrex.com/api/v1.1/public/getticker?market=BTC-STEEM").json()["result"]
            price = (r['Bid'] + r['Ask']) / 2
            prices['bittrex'] = {'price': price, 'volume': 0}
        except:
            pass

        return np.mean([x['price'] for x in prices.values()])

    @staticmethod
    def sbd_btc_ticker(verbose=False):
        prices = {}
        try:
            r = requests.get("https://poloniex.com/public?command=returnTicker").json()["BTC_SBD"]
            if verbose:
                print("Spread on Poloniex is %.2f%%" % Tickers.calc_spread(r['highestBid'], r['lowestAsk']))
            prices['poloniex'] = {'price': float(r['last']), 'volume': float(r['baseVolume'])}
        except:
            pass
        try:
            r = requests.get("https://bittrex.com/api/v1.1/public/getticker?market=BTC-SBD").json()["result"]
            if verbose:
                print("Spread on Bittrex is %.2f%%" % Tickers.calc_spread(r['Bid'], r['Ask']))
            price = (r['Bid'] + r['Ask']) / 2
            prices['bittrex'] = {'price': price, 'volume': 0}
        except:
            pass

        return np.mean([x['price'] for x in prices.values()])

    @staticmethod
    def steem_sbd_implied(verbose=True):
        return Tickers.steem_btc_ticker() / Tickers.sbd_btc_ticker(verbose)

    @staticmethod
    def steem_usd_implied():
        return Tickers.steem_btc_ticker() * Tickers.btc_usd_ticker()

    @staticmethod
    def calc_spread(bid, ask):
        return (1 - (Decimal(bid) / Decimal(ask))) * 100


class Market(Tickers):
    def __init__(self, steem=Node().default()):
        self.steem = steem

    def avg_witness_price(self, take=10):
        price_history = self.steem.rpc.get_feed_history()['price_history']
        return np.mean([parse_payout(x['base']) for x in price_history[-take:]])
