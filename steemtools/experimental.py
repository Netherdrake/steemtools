from graphenebase.objects import GrapheneObject, isArgsThisClass
from graphenebase.types import OrderedDict, String, Uint32, Uint16
from steembase.account import PrivateKey, PublicKey
from steembase.operations import Amount, Transfer_to_vesting
from steemtools.node import Node


# this class was copied from
# https://github.com/aaroncox/steemfeed
# once it makes it into steembase, it will be removed from here
class Exchange_rate(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            super().__init__(OrderedDict([
                ('base', Amount(kwargs["base"])),
                ('quote', Amount(kwargs["quote"])),
            ]))


# this class was copied from
# https://github.com/aaroncox/steemfeed
# once it makes it into steembase, it will be removed from here
class Feed_publish(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('publisher', String(kwargs["publisher"])),
                ('exchange_rate', Exchange_rate(kwargs["exchange_rate"])),
            ]))


class Witness_props(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            super().__init__(OrderedDict([
                ('account_creation_fee', Amount(kwargs["account_creation_fee"])),
                ('maximum_block_size', Uint32(kwargs["maximum_block_size"])),
                ('sbd_interest_rate', Uint16(kwargs["sbd_interest_rate"])),
            ]))


class Witness_update(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('owner', String(kwargs["owner"])),
                ('url', String(kwargs["url"])),
                ('block_signing_key', PublicKey(kwargs["block_signing_key"])),
                ('props', Witness_props(kwargs["props"])),
                ('fee', Amount(kwargs["fee"])),
            ]))


class Transactions(object):
    def __init__(self, steem=Node().default()):
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
