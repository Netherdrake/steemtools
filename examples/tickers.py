from steemtools.market import Tickers

if __name__ == "__main__":
    print("Fetching BTC/USD Price...")
    btc_usd = Tickers.btc_usd_ticker()
    print(btc_usd)

    print("\nFetching STEEM/BTC Price...")
    steem_btc = Tickers.steem_btc_ticker()
    print(steem_btc)

    print("\nFetching SBD/BTC Price...")
    sbd_btc = Tickers.sbd_btc_ticker()
    print(sbd_btc)

    print("\nCalculating implied STEEM/SBD price...")
    print(Tickers.steem_sbd_implied())

    print("\nCalculating implied STEEM/USD price...")
    print(Tickers.steem_usd_implied())
