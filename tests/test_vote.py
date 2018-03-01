from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from pprint import pprint
from beem import Steem
from beem.comment import Comment
from beem.vote import Vote, ActiveVotes, AccountVotes
from beembase.operationids import getOperationNameForId
from beem.instance import set_shared_steem_instance

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://steemd.steemgigs.org",
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

    def test_vote(self):
        bts = self.bts
        vote = Vote("@gtg/witness-gtg-log|fminerten", steem_instance=bts)
        self.assertEqual(u"fminerten", vote["voter"])

    def test_activevotes(self):
        bts = self.bts
        votes = ActiveVotes("@gtg/witness-gtg-log", steem_instance=bts)
        votes.printAsTable()

    def test_accountvotes(self):
        bts = self.bts
        votes = AccountVotes("gtg", steem_instance=bts)
        self.assertTrue(len(votes) > 0)
        self.assertTrue(isinstance(votes[0], Vote))
