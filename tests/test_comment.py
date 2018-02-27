from builtins import super
import unittest
from pprint import pprint
from beem import Steem
from beem.comment import Comment
from beembase.operationids import getOperationNameForId
from beem.instance import set_shared_steem_instance

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://node.steem.ws", "wss://steemd.steemgigs.org", "wss://steemd.steemit.com",
         "wss://steemd.minnowsupportproject.org"]


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bts = Steem(
            nodes,
            nobroadcast=True,
            keys={"active": wif},
        )
        # from getpass import getpass
        # self.bts.wallet.unlock(getpass())
        set_shared_steem_instance(self.bts)
        self.bts.set_default_account("test")

    def test_vote(self):
        bts = self.bts
        c = Comment("@gtg/witness-gtg-log", steem_instance=bts)
        tx = c.vote(100, account="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "vote"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["voter"])

    def test_export(self):
        bts = self.bts
        content = bts.rpc.get_content("gtg", "witness-gtg-log")
        c = Comment("@gtg/witness-gtg-log", steem_instance=bts)
        keys = list(content.keys())
        json_content = c.json()

        for k in keys:
            if k not in "json_metadata":
                self.assertEqual(content[k], json_content[k])

    def test_resteem(self):
        bts = self.bts
        c = Comment("@gtg/witness-gtg-log", steem_instance=bts)
        tx = c.resteem(account="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "custom_json"
        )

    def test_reply(self):
        bts = self.bts
        c = Comment("@gtg/witness-gtg-log", steem_instance=bts)
        tx = c.reply(body="Good post!", author="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "comment"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["author"])

    def test_delete(self):
        bts = self.bts
        c = Comment("@gtg/witness-gtg-log", steem_instance=bts)
        tx = c.delete(account="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "delete_comment"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "gtg",
            op["author"])
