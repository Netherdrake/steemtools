from graphenebase.objects import GrapheneObject, isArgsThisClass
from graphenebase.types import OrderedDict, String, Uint32, Uint16
from steembase import operations
from steembase.account import PrivateKey, PublicKey
from steembase.operations import Amount, Transfer_to_vesting
from steemtools.node import Node

operations.operations["vote"] = 0
operations.operations["comment"] = 1
operations.operations["transfer"] = 2
operations.operations["transfer_to_vesting"] = 3
operations.operations["withdraw_vesting"] = 4
operations.operations["limit_order_create"] = 5
operations.operations["limit_order_cancel"] = 6
operations.operations["feed_publish"] = 7
operations.operations["convert"] = 8
operations.operations["account_create"] = 9
operations.operations["account_update"] = 10
operations.operations["witness_update"] = 11
operations.operations["account_witness_vote"] = 12
operations.operations["account_witness_proxy"] = 13
operations.operations["pow"] = 14
operations.operations["custom"] = 15
operations.operations["report_over_production"] = 16
operations.operations["delete_comment"] = 17
operations.operations["custom_json"] = 18
operations.operations["comment_options"] = 19
operations.operations["set_withdraw_vesting_route"] = 20
operations.operations["limit_order_create2"] = 21
operations.operations["challenge_authority"] = 22
operations.operations["prove_authority"] = 23
operations.operations["request_account_recovery"] = 24
operations.operations["recover_account"] = 25
operations.operations["change_recovery_account"] = 26
operations.operations["escrow_transfer"] = 27
operations.operations["escrow_dispute"] = 28
operations.operations["escrow_release"] = 29
operations.operations["pow2"] = 30
operations.operations["escrow_approve"] = 31
operations.operations["transfer_to_savings"] = 32
operations.operations["transfer_from_savings"] = 33
operations.operations["cancel_transfer_from_savings"] = 34


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
            if not kwargs["block_signing_key"]:
                kwargs["block_signing_key"] = "STM1111111111111111111111111111111114T1Anm"
            super().__init__(OrderedDict([
                ('owner', String(kwargs["owner"])),
                ('url', String(kwargs["url"])),
                ('block_signing_key', PublicKey(kwargs["block_signing_key"])),
                ('props', Witness_props(kwargs["props"])),
                ('fee', Amount(kwargs["fee"])),
            ]))


class Transfer_to_savings(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "memo" not in kwargs:
                kwargs["memo"] = ""
            super().__init__(OrderedDict([
                ('from', String(kwargs["from"])),
                ('to', String(kwargs["to"])),
                ('amount', Amount(kwargs["amount"])),
                ('memo', String(kwargs["memo"])),
            ]))


class Transfer_from_savings(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "memo" not in kwargs:
                kwargs["memo"] = ""

            super().__init__(OrderedDict([
                ('from', String(kwargs["from"])),
                ('request_id', Uint32(int(kwargs["request_id"]))),
                ('to', String(kwargs["to"])),
                ('amount', Amount(kwargs["amount"])),
                ('memo', String(kwargs["memo"])),
            ]))


class Cancel_transfer_from_savings(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('from', String(kwargs["from"])),
                ('request_id', Uint32(int(kwargs["request_id"]))),
            ]))


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
            raise ("Unsupported currency %s" % currency)

