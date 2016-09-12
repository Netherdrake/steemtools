import time

import dateutil
from dateutil import parser

from .node import default


class Blockchain(object):
    def __init__(self, steem=default()):
        self.steem = steem

    @staticmethod
    def parse_block(block, block_id, verbose=False):
        if "transactions" in block:
            timestamp = block['timestamp']
            if verbose:
                print("Processing #%d - %s" % (block_id, timestamp))
            for tx in block["transactions"]:
                for opObj in tx["operations"]:
                    op_type = opObj[0]
                    op = opObj[1]

                    yield {
                        "block_id": block_id,
                        "timestamp": timestamp,
                        "op_type": op_type,
                        "op": op,
                    }

    def replay(self, start_block=0, end_block=None, filter_by=None, **kwargs):
        """
        :param start_block: Block number of the first block to parse.
        :param end_block: Block number of the last block to parse.
        :param filter_by: A string or list of filters. ie: "vote" or ["comment", "vote"]
        :param kwargs: Arguments for the parser, namely verbose=False
        :return: Returns a generator
        """
        # Let's find out how often blocks are generated!
        config = self.steem.rpc.get_config()
        block_interval = config["STEEMIT_BLOCK_INTERVAL"]

        current_block = start_block

        while True:
            props = self.steem.rpc.get_dynamic_global_properties()
            last_confirmed_block = props['last_irreversible_block_num']

            while current_block < last_confirmed_block:

                block = self.steem.rpc.get_block(current_block)
                if block is None:
                    raise Exception('Block is None. Are you trying to fetch a block from the future?')
                for operation in self.parse_block(block, current_block, **kwargs):
                    if filter_by is None:
                        yield operation
                    else:
                        if type(filter_by) is list:
                            if operation['op_type'] in filter_by:
                                yield operation

                        if type(filter_by) is str:
                            if operation['op_type'] == filter_by:
                                yield operation

                current_block += 1

                if end_block is not None and current_block >= end_block:
                    print("All done!")
                    return

            # Sleep for one block
            time.sleep(block_interval)

    def get_current_block(self):
        return self.steem.rpc.get_dynamic_global_properties()['last_irreversible_block_num']

    def get_block_time(self, block_num, verbose=False):
        block = self.steem.rpc.get_block(block_num)
        time = block['timestamp']
        if verbose:
            print("Block %d was minted on: %s" % (block_num, time))
        return dateutil.parser.parse(time + "UTC").timestamp()

    def get_block_from_time(self, timestring, error_margin=10, verbose=False):
        known_block = self.get_current_block()
        known_block_timestamp = self.get_block_time(known_block)

        timestring_timestamp = dateutil.parser.parse(timestring + "UTC").timestamp()

        delta = known_block_timestamp - timestring_timestamp
        block_delta = delta / 3

        if verbose:
            print("Guess:")
        guess_block = known_block - block_delta
        guess_block_timestamp = self.get_block_time(guess_block, verbose=verbose)

        error = timestring_timestamp - guess_block_timestamp
        while abs(error) > error_margin:
            if verbose:
                print("Error: %s" % error)
            guess_block += error / 3
            guess_block_timestamp = self.get_block_time(guess_block, verbose=verbose)

            error = timestring_timestamp - guess_block_timestamp

        return int(guess_block)

    def get_all_usernames(self):
        users = self.steem.rpc.lookup_accounts(-1, 1000)
        more = True
        while more:
            new_users = self.steem.rpc.lookup_accounts(users[-1], 1000)
            if len(new_users) < 1000:
                more = False
            users = users + new_users

        return users
