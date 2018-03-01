from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from pprint import pprint
from beem import Steem
from beem.witness import Witness, Witnesses, WitnessesVotedByAccount, WitnessesRankedByVote
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
            node=nodes,
            nobroadcast=True,
            keys={"active": wif},
        )
        # from getpass import getpass
        # self.bts.wallet.unlock(getpass())
        set_shared_steem_instance(self.bts)
        self.bts.set_default_account("test")

    def test_feed_publish(self):
        bts = self.bts
        w = Witness("gtg", steem_instance=bts)
        tx = w.feed_publish("4 SBD", "1 STEEM")
        self.assertEqual(
            (tx["operations"][0][0]),
            "feed_publish"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "gtg",
            op["publisher"])

    def test_update(self):
        bts = self.bts
        w = Witness("gtg", steem_instance=bts)
        props = {"account_creation_fee": "0.1 STEEM",
                 "maximum_block_size": 32000,
                 "sbd_interest_rate": 0}
        tx = w.update(wif, "", props)
        self.assertEqual((tx["operations"][0][0]), "witness_update")
        op = tx["operations"][0][1]
        self.assertIn(
            "gtg",
            op["owner"])

    def test_witnesses(self):
        bts = self.bts
        w = Witnesses(steem_instance=bts)
        w.printAsTable()
        self.assertTrue(len(w) > 0)
        self.assertTrue(isinstance(w[0], Witness))

    def test_WitnessesVotedByAccount(self):
        bts = self.bts
        w = WitnessesVotedByAccount("gtg", steem_instance=bts)
        w.printAsTable()
        self.assertTrue(len(w) > 0)
        self.assertTrue(isinstance(w[0], Witness))

    def test_WitnessesRankedByVote(self):
        bts = self.bts
        w = WitnessesRankedByVote(steem_instance=bts)
        w.printAsTable()
        self.assertTrue(len(w) > 0)
        self.assertTrue(isinstance(w[0], Witness))
