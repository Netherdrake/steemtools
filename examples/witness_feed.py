import time

from steemtools.experimental import Transactions
from steemtools.markets import Markets
from steemtools.node import Node

settings = {
    "sleep_time_seconds": 60,
    "minimum_spread_pct": 1.0,
    "sbd_usd_peg": True,
}
witness = "furion"
wif = "<PRIVATE ACTIVE KEY HERE>"

if __name__ == '__main__':
    steem = Node().default()
    markets = Markets()


    def get_last_published_price():
        my_info = steem.rpc.get_witness_by_account(witness)
        price = 0
        if float(my_info["sbd_exchange_rate"]["quote"].split()[0]) != 0:
            price = float(my_info["sbd_exchange_rate"]["base"].split()[0]) / float(
                my_info["sbd_exchange_rate"]["quote"].split()[0])
        return price


    while True:
        print("\n" + time.ctime())
        last_price = get_last_published_price()
        print("Published STEEM/USD price is: " + format(last_price, ".3f"))

        current_price = markets.steem_usd_implied()
        quote = "1.000"
        if settings['sbd_usd_peg']:
            quote = "%.3f" % (1 / markets.sbd_usd_implied())
        print("Implied STEEM/USD price is: %.3f" % current_price)

        # if price diverged for more than our defined %, update the feed
        spread = abs(markets.calc_spread(last_price, current_price/float(quote)))
        print("Spread Between Prices: %.3f%%" % spread)
        if spread > settings['minimum_spread_pct']:
            tx = Transactions().witness_feed_publish(current_price, witness, wif, quote=quote, sim_mode=False)
            # print(tx)
            print("Updated the witness price feed.")

        time.sleep(settings['sleep_time_seconds'])
