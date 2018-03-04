from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from datetime import datetime, timedelta
import pytz
from pprint import pprint
from beem import Steem
from beem.blockchain import Blockchain
from beem.block import Block
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

    def test_blockchain(self):
        bts = self.bts
        b = Blockchain(steem_instance=bts)
        num = b.get_current_block_num()
        self.assertTrue(num > 0)
        block = b.get_current_block()
        self.assertTrue(isinstance(block, Block))
        self.assertEqual(num, block.identifier)

    def test_estimate_block_num(self):
        bts = self.bts
        b = Blockchain(steem_instance=bts)
        last_block = b.get_current_block()
        num = last_block.identifier
        now = last_block.time()
        date = now - timedelta(seconds=60 * 3)
        est_block_num = b.get_estimated_block_num(date)
        self.assertEqual(est_block_num, num - 60)