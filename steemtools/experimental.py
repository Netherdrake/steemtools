from steembase.account import PrivateKey
from steembase.operations import Transfer_to_vesting, Transfer_to_savings, Transfer_from_savings, \
    Cancel_transfer_from_savings, Feed_publish, Witness_update
from steemtools.node import Node


class Transactions(object):
    def __init__(self, steem=None):
        if not steem:
            steem = Node().default()
        self.steem = steem

    def transfer_to_vesting(self, to, amount, account_name, wif, sim_mode=True):
        op = Transfer_to_vesting(
            **{
                "from": account_name,
                "to": to,
                "amount": "%s STEEM" % amount,
            }
        )
        tx = self.steem.constructTx(op, wif)
        if sim_mode:
            return tx
        return self.steem.broadcast(tx)

    def transfer_to_savings(self, transfer_from, transfer_to, amount, currency, memo, wif, sim_mode=True):
        self._check_currency(currency)
        op = Transfer_to_savings(
            **{
                "from": transfer_from,
                "to": transfer_to,
                "amount": "%s %s" % (amount, currency),
                "memo": memo,
            }
        )
        tx = self.steem.constructTx(op, wif)
        if sim_mode:
            return tx
        return self.steem.broadcast(tx)

    def transfer_from_savings(self, transfer_from, transfer_to, amount, currency, memo, request_id, wif, sim_mode=True):
        self._check_currency(currency)
        op = Transfer_from_savings(
            **{
                "from": transfer_from,
                "request_id": request_id,
                "to": transfer_to,
                "amount": "%s %s" % (amount, currency),
                "memo": memo,
            }
        )
        tx = self.steem.constructTx(op, wif)
        if sim_mode:
            return tx
        return self.steem.broadcast(tx)

    def transfer_from_savings_cancel(self, transfer_from, request_id, wif, sim_mode=True):
        op = Cancel_transfer_from_savings(
            **{
                "from": transfer_from,
                "request_id": request_id,
            }
        )
        tx = self.steem.constructTx(op, wif)
        if sim_mode:
            return tx
        return self.steem.broadcast(tx)

    def witness_feed_publish(self, steem_usd_price, witness_name, wif, sim_mode=True):
        op = Feed_publish(
            **{
                "publisher": witness_name,
                "exchange_rate": {
                    "base": "%s SBD" % steem_usd_price,
                    "quote": "1.000 STEEM"
                }
            }
        )
        tx = self.steem.constructTx(op, wif)
        if sim_mode:
            return tx
        return self.steem.broadcast(tx)

    def witness_update(self, witness_name, signing_key, url, props, wif, sim_mode=True):
        op = Witness_update(
            **{
                "owner": witness_name,
                "url": url,
                "block_signing_key": signing_key,
                "props": props,
                "fee": "0.000 STEEM",
            }
        )
        tx = self.steem.constructTx(op, wif)
        if sim_mode:
            return tx
        return self.steem.broadcast(tx)

    def is_wif_valid(self, account_name, wif, role):
        wif_pub = PrivateKey(wif).pubkey
        role_keys = self.steem.rpc.get_account(account_name)[role]['key_auths'][0]
        return (self.steem.wallet.getAccountFromPrivateKey(wif) == account_name) and (wif_pub in role_keys)

    @staticmethod
    def _check_currency(currency):
        if currency not in ['STEEM', 'SBD']:
            raise TypeError("Unsupported currency %s" % currency)
