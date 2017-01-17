import time
from pprint import pprint

import steem as stm
from steem.block import Block
from steem.utils import parse_time


class Blockchain(object):
    def __init__(
            self,
            steem_instance=None,
            mode="irreversible"
    ):
        """ This class allows to access the blockchain and read data
            from it

            :param Steem steem: Steem() instance to use when accesing a RPC
            :param str mode: (default) Irreversible block
                    (``irreversible``) or actual head block (``head``)
        """
        if not steem_instance:
            steem_instance = stm.Steem()
        self.steem = steem_instance

        if mode == "irreversible":
            self.mode = 'last_irreversible_block_num'
        elif mode == "head":
            self.mode = "head_block_number"
        else:
            raise ValueError("invalid value for 'mode'!")

    def info(self):
        """ This call returns the *dynamic global properties*
        """
        return self.steem.rpc.get_dynamic_global_properties()

    def config(self):
        return self.steem.rpc.get_config()

    def get_current_block_num(self):
        """ This call returns the current block
        """
        return self.info().get(self.mode)

    def get_current_block(self):
        """ This call returns the current block
        """
        return Block(self.get_current_block_num())

    def blocks(self, start=None, stop=None):
        """ Yields blocks starting from ``start``.

            :param int start: Starting block
            :param int stop: Stop at this block
            :param str mode: We here have the choice between
                 * "head": the last block
                 * "irreversible": the block that is confirmed by 2/3 of all block producers and is thus irreversible!
        """
        # Let's find out how often blocks are generated!
        block_interval = self.config().get("STEEMIT_BLOCK_INTERVAL")

        if not start:
            start = self.get_current_block_num()

        # We are going to loop indefinitely
        while True:

            # Get chain properies to identify the
            head_block = self.get_current_block_num()

            # Blocks from start until head block
            for blocknum in range(start, head_block + 1):
                # Get full block
                block = self.steem.rpc.get_block(blocknum)
                block.update({"block_num": blocknum})
                yield block

            # Set new start
            start = head_block + 1

            if stop and start > stop:
                break

            # Sleep for one block
            time.sleep(block_interval)

    def ops(self, start=None, stop=None, only_virtual_ops=False):
        """ Yields all operations (including virtual operations) starting from ``start``.

            :param int start: Starting block
            :param int stop: Stop at this block
            :param str mode: We here have the choice between
                 * "head": the last block
                 * "irreversible": the block that is confirmed by 2/3 of all block producers and is thus irreversible!
            :param bool only_virtual_ops: Only yield virtual operations

            This call returns a list with elements that look like
            this and carries only one operation each:::

                {'block': 8411453,
                 'op': ['vote',
                        {'author': 'dana-edwards',
                         'permlink': 'church-encoding-numbers-defined-as-functions',
                         'voter': 'juanmiguelsalas',
                         'weight': 6000}],
                 'op_in_trx': 0,
                 'timestamp': '2017-01-12T12:26:03',
                 'trx_id': 'e897886e8b7560f37da31eb1a42177c6f236c985',
                 'trx_in_block': 1,
                 'virtual_op': 0}

        """

        # Let's find out how often blocks are generated!
        block_interval = self.config().get("STEEMIT_BLOCK_INTERVAL")

        if not start:
            start = self.get_current_block_num()

        # We are going to loop indefinitely
        while True:

            # Get chain properies to identify the
            head_block = self.get_current_block_num()

            # Blocks from start until head block
            for block_num in range(start, head_block + 1):
                # Get full block
                yield from self.steem.rpc.get_ops_in_block(block_num, only_virtual_ops)

            # Set new start
            start = head_block + 1

            if stop and start > stop:
                break

            # Sleep for one block
            time.sleep(block_interval)

    def stream(self, filter_by=list(), *args, **kwargs):
        """ Yield a stream of blocks

            :param array filter_by: List of operations to filter for, e.g.
                vote, comment, transfer, transfer_to_vesting,
                withdraw_vesting, limit_order_create, limit_order_cancel,
                feed_publish, convert, account_create, account_update,
                witness_update, account_witness_vote, account_witness_proxy,
                pow, custom, report_over_production, fill_convert_request,
                comment_reward, curate_reward, liquidity_reward, interest,
                fill_vesting_withdraw, fill_order,
            :param int start: Start at this block
            :param int stop: Stop at this block
            :param str mode: We here have the choice between
                 * "head": the last block
                 * "irreversible": the block that is confirmed by 2/3 of all block producers and is thus irreversible!
        """
        if isinstance(filter_by, str):
            filter_by = [filter_by]

        # for block in self.blocks(*args, **kwargs):
        #     for tx in block.get("transactions"):
        #         for op in tx["operations"]:
        #             yield {
        #                 **op[1],
        #                 "type": op[0],
        #                 "timestamp": block.get("timestamp"),
        #                 "block_num": block.get("block_num")
        #             }.update(op[1])

        for event in self.ops(*args, **kwargs):
            op_type, op = event['op']
            if not filter_by or op_type in filter_by:
                yield {
                    **op,
                    "type": op_type,
                    "timestamp": parse_time(event.get("timestamp")),
                    "block_num": event.get("block"),
                    "trx_id": event.get("trx_id"),
                }

    def replay(self, start_block=1, end_block=None, filter_by=list(), **kwargs):
        """ Same as ``stream`` with different prototyp
        """
        return self.stream(
            filter_by=filter_by,
            start=start_block,
            stop=end_block,
            mode=self.mode,
            **kwargs
        )

    @staticmethod
    def block_time(block_num):
        """ Returns a datetime of the block with the given block
            number.

            :param int block_num: Block number
        """
        return Block(block_num).time()

    @staticmethod
    def block_timestamp(block_num):
        """ Returns the timestamp of the block with the given block
            number.

            :param int block_num: Block number
        """
        return int(Block(block_num).time().timestamp())

    def get_block_from_time(self, timestring, error_margin=10):
        """ Estimate block number from given time

            :param str timestring: String representing time
            :param int error_margin: Estimate block number within this interval (in seconds)

        """
        known_block = self.get_current_block()['block_num']
        known_block_timestamp = self.block_timestamp(known_block)
        timestring_timestamp = parse_time(timestring).timestamp()
        delta = known_block_timestamp - timestring_timestamp
        block_delta = delta / 3
        guess_block = known_block - block_delta
        guess_block_timestamp = self.block_timestamp(guess_block)
        error = timestring_timestamp - guess_block_timestamp
        while abs(error) > error_margin:
            guess_block += error / 3
            guess_block_timestamp = self.block_timestamp(guess_block)
            error = timestring_timestamp - guess_block_timestamp
        return int(guess_block)


def get_all_usernames(last_user=-1, steem=None):
    if not steem:
        steem = stm.Steem()

    usernames = steem.rpc.lookup_accounts(last_user, 1000)
    batch = []
    while len(batch) != 1:
        batch = steem.rpc.lookup_accounts(usernames[-1], 1000)
        usernames += batch[1:]

    return usernames


def get_usernames_batch(last_user=-1, steem=None):
    if not steem:
        steem = stm.Steem()

    return steem.rpc.lookup_accounts(last_user, 1000)


if __name__ == '__main__':
    b = Blockchain()
    for e in b.stream():
        pprint(e)
        print()
