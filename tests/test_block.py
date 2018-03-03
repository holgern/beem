from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from pprint import pprint
from beem import Steem
from beem.block import Block
from datetime import datetime
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

    def test_block(self):
        bts = self.bts
        block = Block(1, steem_instance=bts)
        self.assertEqual(block.identifier, 1)
        self.assertTrue(isinstance(block.time(), datetime))

        block2 = Block(2, steem_instance=bts)
        self.assertTrue(block2.time() > block.time())
        block2.change_block_number(3)
        self.assertEqual(block2.identifier, 3)

    def test_block_ops(self):
        bts = self.bts
        block = Block(20000000, steem_instance=bts)
        self.assertTrue(len(block.ops))
        self.assertTrue(isinstance(block.ops_statistics(), dict))
