import time
from pprint import pprint

from steemtools.experimental import Transactions
from steemtools.node import Node

steem = Node().default()

witness_name = "furion"
active_key = "<PRIVATE_ACTIVE_KEY>"

missed = steem.rpc.get_witness_by_account(witness_name)['total_missed']
treshold = missed + 10

while True:
    if steem.rpc.get_witness_by_account(witness_name)['total_missed'] > treshold:
        t = Transactions()
        props = {
            "account_creation_fee": "15.000 STEEM",
            "maximum_block_size": 65536,
            "sbd_interest_rate": 500,
        }
        tx = t.witness_update(witness_name=witness_name, signing_key=None,
                              url="https://steemdb.com/@furion/witness", props=props,
                              wif=active_key, sim_mode=False)

        pprint(tx)
        quit("Witness %s Disabled!" % witness_name)

    time.sleep(60)
