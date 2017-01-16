import time
from pprint import pprint

from steem import Steem

steem = Steem()

witness_name = "furion"

missed = steem.rpc.get_witness_by_account(witness_name)['total_missed']
treshold = missed + 10

while True:
    if steem.rpc.get_witness_by_account(witness_name)['total_missed'] > treshold:
        props = {
            "account_creation_fee": "15.000 STEEM",
            "maximum_block_size": 65536,
            "sbd_interest_rate": 500,
        }

        tx = steem.witness_update(signing_key=None,
                                  url="https://steemdb.com/@furion/witness",
                                  props=props,
                                  account=witness_name)

        pprint(tx)
        quit("Witness %s Disabled!" % witness_name)

    time.sleep(60)
