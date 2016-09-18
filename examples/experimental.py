from steemtools.experimental import Transactions
from steemtools.helpers import read_asset
from steemtools.node import Node

steem = Node().default()


# get wif for our account
def get_active_key_from_piston_wallet(account_name):
    if steem.wallet.locked():
        wallet_password = steem.wallet.getPassword()
        steem.wallet.unlock(wallet_password)

    if not steem.wallet.locked():
        wif = steem.wallet.getActiveKeyForAccount(account_name)
        if wif and isinstance(wif, str) and len(wif) > 0:
            return wif

    return False


# power up 0.1 STEEM, if our balance is sufficient
wif = get_active_key_from_piston_wallet("furion")
my_account_balances = steem.get_balances("furion")
steem_balance = read_asset(my_account_balances["balance"])['value']
if wif and steem_balance > 0.1:
    tx = Transactions().transfer_to_vesting("furion", 0.1, "furion", wif, sim_mode=True)
    print(tx)


