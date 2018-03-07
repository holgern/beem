from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from parameterized import parameterized
from pprint import pprint
from beem import Steem
from beem.discussions import (
    Query, Discussions_by_trending, Comment_discussions_by_payout,
    Post_discussions_by_payout, Discussions_by_created, Discussions_by_active,
    Discussions_by_cashout, Discussions_by_votes,
    Discussions_by_children, Discussions_by_hot, Discussions_by_feed, Discussions_by_blog,
    Discussions_by_comments, Discussions_by_promoted
)
from datetime import datetime
from beem.instance import set_shared_steem_instance

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://node.steem.ws", "wss://steemd.steemgigs.org", "wss://steemd.steemit.com",
         "wss://steemd.minnowsupportproject.org"]
nodes_appbase = ["https://api.steemitstage.com", "wss://appbasetest.timcliff.com"]


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bts = Steem(
            node=nodes,
            nobroadcast=True,
            keys={"active": wif},
        )
        self.appbase = Steem(
            node=nodes_appbase,
            nobroadcast=True,
            keys={"active": wif},
        )
        # from getpass import getpass
        # self.bts.wallet.unlock(getpass())
        set_shared_steem_instance(self.bts)
        self.bts.set_default_account("test")

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_trending(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        query = Query()
        query["limit"] = 10
        query["tag"] = "steemit"
        d = Discussions_by_trending(query, steem_instance=bts)
        self.assertEqual(len(d), 10)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_comment_payout(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        query = Query()
        query["limit"] = 10
        query["tag"] = "steemit"
        d = Comment_discussions_by_payout(query, steem_instance=bts)
        self.assertEqual(len(d), 10)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_post_payout(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        query = Query()
        query["limit"] = 10
        query["tag"] = "steemit"
        d = Post_discussions_by_payout(query, steem_instance=bts)
        self.assertEqual(len(d), 10)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_created(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        query = Query()
        query["limit"] = 10
        query["tag"] = "steemit"
        d = Discussions_by_created(query, steem_instance=bts)
        self.assertEqual(len(d), 10)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_active(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        query = Query()
        query["limit"] = 10
        query["tag"] = "steemit"
        d = Discussions_by_active(query, steem_instance=bts)
        self.assertEqual(len(d), 10)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_cashout(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        query = Query()
        query["limit"] = 10
        Discussions_by_cashout({"limit": 10}, steem_instance=bts)
        # self.assertEqual(len(d), 10)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_votes(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        query = Query()
        query["limit"] = 10
        query["tag"] = "steemit"
        d = Discussions_by_votes(query, steem_instance=bts)
        self.assertEqual(len(d), 10)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_children(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        query = Query()
        query["limit"] = 10
        query["tag"] = "steemit"
        d = Discussions_by_children(query, steem_instance=bts)
        self.assertEqual(len(d), 10)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_feed(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        query = Query()
        query["limit"] = 10
        query["tag"] = "gtg"
        d = Discussions_by_feed(query, steem_instance=bts)
        self.assertEqual(len(d), 10)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_blog(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        query = Query()
        query["limit"] = 10
        query["tag"] = "gtg"
        d = Discussions_by_blog(query, steem_instance=bts)
        self.assertEqual(len(d), 10)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_comments(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        query = Query()
        query["limit"] = 10
        query["filter_tags"] = ["gtg"]
        query["start_author"] = "gtg"
        d = Discussions_by_comments(query, steem_instance=bts)
        self.assertEqual(len(d), 10)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_promoted(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        query = Query()
        query["limit"] = 10
        query["tag"] = "steemit"
        d = Discussions_by_promoted(query, steem_instance=bts)
        self.assertEqual(len(d), 10)
