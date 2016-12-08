import datetime
import json
import math
import time
from collections import namedtuple
from contextlib import suppress

import dateutil
import numpy as np
import steem as stm
from dateutil import parser
from funcy import walk_keys
from steem.amount import Amount
from steemtools.helpers import time_diff, simple_cache, remove_from_dict
from steemtools.node import Node
from werkzeug.contrib.cache import SimpleCache

base_cache = SimpleCache()  # is this threadsafe?


class Account(object):
    def __init__(self, account_name, steem=None):
        if not steem:
            steem = Node().default()
        self.steem = steem

        self.name = account_name

        self.converter = Converter(steem=self.steem)

        # caches
        self._blog = None
        self._props = None

    def get_props(self):
        if self._props is None:
            self._props = self.steem.rpc.get_account(self.name)
        return self._props

    def get_blog(self):
        if self._blog is None:
            def _get_blog(steem, user):
                state = steem.rpc.get_state("/@%s/blog" % user)
                posts = state["accounts"][user].get("blog", [])
                return [stm.steem.Post(steem, "@%s" % x) for x in posts if x]

            self._blog = _get_blog(self.steem, self.name)
        return self._blog

    @property
    def profile(self):
        with suppress(Exception):
            meta_str = self.get_props().get("json_metadata", "")
            return json.loads(meta_str).get('profile', dict())

    @property
    def sp(self):
        return self.get_sp()

    @property
    def rep(self):
        return self.reputation()

    def get_sp(self):
        vests = Amount(self.get_props()['vesting_shares']).amount
        return self.converter.vests_to_sp(vests)

    def get_balances(self):
        my_account_balances = self.steem.get_balances(self.name)
        return {
            "STEEM": my_account_balances["balance"].amount,
            "SBD": my_account_balances["sbd_balance"].amount,
            "VESTS": my_account_balances["vesting_shares"].amount,
        }

    def reputation(self):
        rep = int(self.get_props()['reputation'])
        if rep < 0:
            return -1
        if rep == 0:
            return 25

        score = (math.log10(abs(rep)) - 9) * 9 + 25
        return float("%.2f" % score)

    def voting_power(self):
        return self.get_props()['voting_power'] / 100

    def number_of_winning_posts(self, skip=1, payout_requirement=300, max_posts=10):
        winning_posts = 0
        blog = self.get_blog()[skip:max_posts + skip]
        for post in blog:
            total_payout = Amount(post['total_payout_reward']).amount
            if total_payout >= payout_requirement:
                winning_posts += 1

        nt = namedtuple('WinningPosts', ['winners', 'blog_posts'])
        return nt(winning_posts, len(blog))

    def avg_payout_per_post(self, skip=1, max_posts=10):
        total_payout = 0
        blog = self.get_blog()[skip:max_posts + skip]
        for post in blog:
            total_payout += Amount(post['total_payout_reward']).amount

        if len(blog) == 0:
            return 0

        return total_payout / len(blog)

    def time_to_whale(self, verbose=False, whale_sp=1e5, skip=1, max_posts=10, mean_of_recent=3):
        blog = self.get_blog()[skip:max_posts + skip]

        max_rshares = self.converter.sp_to_rshares(whale_sp)
        time_to_whale = []

        for post in blog:
            votes = []
            rshares_sum = 0

            for vote in post['active_votes']:
                vote['time_elapsed'] = int(time_diff(post['created'], vote['time']))
                votes.append(vote)

            # note: this function will already filter out posts without votes
            for vote in sorted(votes, key=lambda k: k['time_elapsed']):
                rshares_sum += int(vote['rshares'])
                if rshares_sum >= max_rshares:
                    ttw = time_diff(post['created'], vote['time'])
                    if verbose:
                        print('%s on %s' % (ttw, post['permlink']))
                    time_to_whale.append(ttw)
                    break

        if len(time_to_whale) == 0:
            return None
        return np.mean(time_to_whale[:mean_of_recent])

    def get_followers(self):
        return [x['follower'] for x in self._get_followers(direction="follower")]

    def get_following(self):
        return [x['following'] for x in self._get_followers(direction="following")]

    def _get_followers(self, direction="follower", last_user=""):
        if direction == "follower":
            followers = self.steem.rpc.get_followers(self.name, last_user, "blog", 100, api="follow")
        elif direction == "following":
            followers = self.steem.rpc.get_following(self.name, last_user, "blog", 100, api="follow")
        if len(followers) == 100:
            followers += self._get_followers(direction=direction, last_user=followers[-1][direction])[1:]
        return followers

    def check_if_already_voted(self, post):
        for v in self.history2(filter_by="vote"):
            vote = v['op']
            if vote['permlink'] == post['permlink']:
                return True

        return False

    def curation_stats(self):
        trailing_24hr_t = time.time() - datetime.timedelta(hours=24).total_seconds()
        trailing_7d_t = time.time() - datetime.timedelta(days=7).total_seconds()

        reward_24h = 0.0
        reward_7d = 0.0

        for event in self.history2(filter_by="curation_reward", take=10000):

            if parser.parse(event['timestamp'] + "UTC").timestamp() > trailing_7d_t:
                reward_7d += Amount(event['op']['reward']).amount

            if parser.parse(event['timestamp'] + "UTC").timestamp() > trailing_24hr_t:
                reward_24h += Amount(event['op']['reward']).amount

        reward_7d = self.converter.vests_to_sp(reward_7d)
        reward_24h = self.converter.vests_to_sp(reward_24h)
        return {
            "24hr": reward_24h,
            "7d": reward_7d,
            "avg": reward_7d / 7,
        }

    def get_features(self, max_posts=10, payout_requirement=300):
        num_winning_posts, post_count = self.number_of_winning_posts(payout_requirement=payout_requirement,
                                                                     max_posts=max_posts)
        return {
            "name": self.name,
            "settings": {
                "max_posts": max_posts,
                "payout_requirement": payout_requirement,
            },
            "author": {
                "post_count": post_count,
                "winners": num_winning_posts,
                "sp": int(self.get_sp()),
                "rep": self.reputation(),
                "followers": len(self.get_followers()),
                "ttw": self.time_to_whale(max_posts=max_posts),
                "ppp": self.avg_payout_per_post(max_posts=max_posts),
            },
        }

    def virtual_op_count(self):
        try:
            last_item = self.steem.rpc.get_account_history(self.name, -1, 0)[0][0]
        except IndexError:
            return 0
        else:
            return last_item

    def history(self, filter_by=None, start=0):
        """
        Take all elements from start to last from history, oldest first.
        """
        batch_size = 1000
        max_index = self.virtual_op_count()
        if not max_index:
            return

        start_index = start + batch_size
        i = start_index
        while True:
            if i == start_index:
                limit = batch_size
            else:
                limit = batch_size - 1
            history = self.steem.rpc.get_account_history(self.name, i, limit)
            for item in history:
                index = item[0]
                if index >= max_index:
                    return

                op_type = item[1]['op'][0]
                op = item[1]['op'][1]
                timestamp = item[1]['timestamp']
                trx_id = item[1]['trx_id']

                def construct_op():
                    return {
                        "index": index,
                        "trx_id": trx_id,
                        "timestamp": timestamp,
                        "op_type": op_type,
                        "op": op,
                    }

                if filter_by is None:
                    yield construct_op()
                else:
                    if type(filter_by) is list:
                        if op_type in filter_by:
                            yield construct_op()

                    if type(filter_by) is str:
                        if op_type == filter_by:
                            yield construct_op()
            i += batch_size

    def history2(self, filter_by=None, take=1000):
        """
        Take X elements from most recent history, oldest first.
        """
        max_index = self.virtual_op_count()
        start_index = max_index - take
        if start_index < 0:
            start_index = 0

        return self.history(filter_by, start=start_index)

    def get_account_votes(self):
        return self.steem.rpc.get_account_votes(self.name)

    def get_withdraw_routes(self):
        return self.steem.rpc.get_withdraw_routes(self.name, 'all')

    def get_conversion_requests(self):
        return self.steem.rpc.get_conversion_requests(self.name)

    @staticmethod
    def filter_by_date(items, start_time, end_time=None):
        start_time = dateutil.parser.parse(start_time + "UTC").timestamp()
        if end_time:
            end_time = dateutil.parser.parse(end_time + "UTC").timestamp()
        else:
            end_time = time.time()

        filtered_items = []
        for item in items:
            if 'time' in item:
                item_time = item['time']
            elif 'timestamp' in item:
                item_time = item['timestamp']
            timestamp = dateutil.parser.parse(item_time + "UTC").timestamp()
            if end_time > timestamp > start_time:
                filtered_items.append(item)

        return filtered_items

    def mongo_export(self):
        followers = self.get_followers()
        following = self.get_following()

        return {
            **self.get_props(),
            "profile": self.profile,
            "sp": self.sp,
            "rep": self.rep,
            "balances": walk_keys(str.upper, self.get_balances()),
            "followers": followers,
            "followers_count": len(followers),
            "following": following,
            "following_count": len(following),
            "curation_stats": self.curation_stats(),
            "withdrawal_routes": self.get_withdraw_routes(),
            "conversion_requests": self.get_conversion_requests(),
            "account_votes": self.get_account_votes(),
        }


class Post(stm.steem.Post):
    def __init__(self, post, steem=None):
        if not steem:
            steem = Node().default()
        if isinstance(post, stm.steem.Post):
            post = post.identifier
        super(Post, self).__init__(steem, post)

    @property
    def payout(self):
        return Amount(self['total_payout_reward']).amount

    @property
    def meta(self):
        with suppress(Exception):
            meta_str = self.get("json_metadata", "")
            return json.loads(meta_str)

    def is_main_post(self):
        return len(self['title']) > 0 and not self['depth'] and not self['parent_author']

    def is_comment(self):
        if len(self['title']) == 0:
            return True

        if self['depth'] > 0:
            return True

        if len(self['parent_author']) > 0:
            return True

        return False

    def get_votes(self, from_account=None):
        votes = []
        for vote in self['active_votes']:
            vote['time_elapsed'] = int(time_diff(self['created'], vote['time']))
            if from_account and vote['voter'] == from_account:
                return vote
            votes.append(vote)
        return votes

    def get_metadata(self):
        rshares = int(self["vote_rshares"])
        weight = int(self["total_vote_weight"])

        if int(self["total_vote_weight"]) == 0 and self.time_elapsed() > 3600:
            weight = 0
            rshares = 0
            for vote in self['active_votes']:
                weight += int(vote['weight'])
                rshares += int(vote['rshares'])

        return {
            "rshares": rshares,
            "weight": weight,
            "time_elapsed": self.time_elapsed(),
        }

    def time_elapsed(self):
        created_at = parser.parse(self['created'] + "UTC").timestamp()
        now_adjusted = time.time()
        return now_adjusted - created_at

    def calc_reward_pct(self):
        reward = (self.time_elapsed() / 1800) * 100
        if reward > 100:
            reward = 100
        return reward

    def mongo_export(self):
        return remove_from_dict(self, ['steem'])


class Converter(object):
    def __init__(self, steem=None):
        if not steem:
            steem = Node().default()
        self.steem = steem
        self.CONTENT_CONSTANT = 2000000000000

    @simple_cache(base_cache, timeout=5 * 60)
    def sbd_median_price(self):
        return Amount(self.steem.rpc.get_feed_history()['current_median_history']['base']).amount

    @simple_cache(base_cache, timeout=5 * 60)
    def steem_per_mvests(self):
        info = self.steem.rpc.get_dynamic_global_properties()
        return (
            Amount(info["total_vesting_fund_steem"]).amount /
            (Amount(info["total_vesting_shares"]).amount / 1e6)
        )

    def vests_to_sp(self, vests):
        return vests * self.steem_per_mvests() / 1e6

    def sp_to_vests(self, sp):
        return sp * 1e6 / self.steem_per_mvests()

    def sp_to_rshares(self, sp, voting_power=10000, vote_pct=10000):
        # calculate our account voting shares (from vests), mine is 6.08b
        vesting_shares = int(self.sp_to_vests(sp) * 1e6)

        # calculate vote rshares
        power = (((voting_power * vote_pct) / 10000) / 200) + 1
        rshares = (power * vesting_shares) / 10000

        return rshares

    def steem_to_sbd(self, amount_steem):
        return self.sbd_median_price() * amount_steem

    def sbd_to_steem(self, amount_sbd):
        return amount_sbd / self.sbd_median_price()

    def sbd_to_shares(self, sbd_payout):
        steem_payout = self.sbd_to_steem(sbd_payout)

        props = self.steem.rpc.get_dynamic_global_properties()
        total_reward_fund_steem = Amount(props['total_reward_fund_steem']).amount
        total_reward_shares2 = int(props['total_reward_shares2'])

        post_rshares2 = (steem_payout / total_reward_fund_steem) * total_reward_shares2

        rshares = math.sqrt(self.CONTENT_CONSTANT ** 2 + post_rshares2) - self.CONTENT_CONSTANT
        return rshares

    def rshares_2_weight(self, rshares):
        _max = 2 ** 64 - 1
        return (_max * rshares) / (2 * self.CONTENT_CONSTANT + rshares)
