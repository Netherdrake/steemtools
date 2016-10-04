import datetime
import math
import time

import dateutil
import numpy as np
import piston
from dateutil import parser
from steemtools.helpers import read_asset, parse_payout, time_diff
from steemtools.node import Node


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
            self._blog = self.steem.get_blog(self.name)
        return self._blog

    def get_sp(self):
        vests = int(parse_payout(self.get_props()['vesting_shares']))
        return self.converter.vests_to_sp(vests)

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
            total_payout = parse_payout(post['total_payout_reward'])
            if total_payout >= payout_requirement:
                winning_posts += 1

        return winning_posts, len(blog)

    def avg_payout_per_post(self, skip=1, max_posts=10):
        total_payout = 0
        blog = self.get_blog()[skip:max_posts + skip]
        for post in blog:
            total_payout += parse_payout(post['total_payout_reward'])

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

        for event in self.history2(filter_by="curation_reward", limit=2000):

            if parser.parse(event['timestamp'] + "UTC").timestamp() > trailing_7d_t:
                reward_7d += parse_payout(event['op']['reward'])

            if parser.parse(event['timestamp'] + "UTC").timestamp() > trailing_24hr_t:
                reward_24h += parse_payout(event['op']['reward'])

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

    def history(self, filter_by=None):
        item_id_repeat = 0
        all_ids = []

        i = 0
        while True:
            i += 1
            history = self.steem.rpc.get_account_history(self.name, i, 1)

            for item in history:
                id = item[1]['id']
                if item_id_repeat > 100:
                    return
                if id in all_ids:
                    item_id_repeat += 1
                    break
                all_ids.append(id)
                item_id_repeat = 0

                op_type = item[1]['op'][0]
                op = item[1]['op'][1]
                timestamp = item[1]['timestamp']

                def construct_op():
                    return {
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

    def history2(self, filter_by=None, limit=1000):
        item_id_repeat = 0
        all_ids = []

        history = self.steem.rpc.get_account_history(self.name, -1, limit)

        for item in history:
            id = item[1]['id']
            if item_id_repeat > 100:
                return
            if id in all_ids:
                item_id_repeat += 1
                break
            all_ids.append(id)
            item_id_repeat = 0

            op_type = item[1]['op'][0]
            op = item[1]['op'][1]
            timestamp = item[1]['timestamp']

            def construct_op():
                return {
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


class Post(piston.steem.Post):
    def __init__(self, post, steem=None):
        if not steem:
            steem = Node().default()
        if isinstance(post, piston.steem.Post):
            post = post.identifier
        super(Post, self).__init__(steem, post)

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

    def contains_tags(self, filter_by=('spam', 'test', 'nsfw')):
        for tag in filter_by:
            if tag in self['_tags']:
                return True

        return False

    def get_url(self):
        return "https://steemit.com/%s/%s" % (self.category, self.identifier)

    def time_elapsed(self):
        created_at = parser.parse(self['created'] + "UTC").timestamp()
        now_adjusted = time.time()
        return now_adjusted - created_at

    def payout(self):
        return parse_payout(self['total_payout_reward'])

    def calc_reward_pct(self):
        reward = (self.time_elapsed() / 1800) * 100
        if reward > 100:
            reward = 100
        return reward


class Converter(object):
    def __init__(self, cache_timeout=5*60, steem=None):
        if not steem:
            steem = Node().default()
        self.steem = steem
        self.CONTENT_CONSTANT = 2000000000000

        # caches, lazy loading
        self._cache_timeout = cache_timeout  # 5 minutes
        self._cache_timer = time.time()
        self._sbd_median_price = None
        self._steem_per_mvests = None

    def _has_cache_expired(self):
        if time.time() - self._cache_timer > self._cache_timeout:
            self._cache_timer = time.time()
            return True
        return False

    def sbd_median_price(self):
        if (self._sbd_median_price is None) or self._has_cache_expired():
            price = read_asset(self.steem.rpc.get_feed_history()['current_median_history']['base'])['value']
            self._sbd_median_price = price

        return self._sbd_median_price

    def steem_per_mvests(self):
        if (self._steem_per_mvests is None) or self._has_cache_expired():
            info = self.steem.rpc.get_dynamic_global_properties()
            self._steem_per_mvests = (
                float(info["total_vesting_fund_steem"].split(" ")[0]) /
                (float(info["total_vesting_shares"].split(" ")[0]) / 1e6)
            )
        return self._steem_per_mvests

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
        total_reward_fund_steem = read_asset(props['total_reward_fund_steem'])['value']
        total_reward_shares2 = int(props['total_reward_shares2'])

        post_rshares2 = (steem_payout / total_reward_fund_steem) * total_reward_shares2

        rshares = math.sqrt(self.CONTENT_CONSTANT ** 2 + post_rshares2) - self.CONTENT_CONSTANT
        return rshares

    def rshares_2_weight(self, rshares):
        _max = 2 ** 64 - 1
        return (_max * rshares) / (2 * self.CONTENT_CONSTANT + rshares)
