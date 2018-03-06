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
        b = Blockchain(steem_instance=self.bts)
        num = b.get_current_block_num()
        self.start = num - 100
        self.stop = num

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

    def test_get_all_accounts(self):
        bts = self.bts
        b = Blockchain(steem_instance=bts)        
        
        accounts = []
        for acc in b.get_all_accounts(steps=100, limit=100):
            accounts.append(acc)
        self.assertEqual(len(accounts), 100)

    def test_stream(self):
        bts = self.bts
        b = Blockchain(steem_instance=bts)
        ops_stream = []
        opNames=["transfer", "vote"]
        for op in b.stream(opNames=opNames, start=self.start, stop=self.stop):
            ops_stream.append(op)
        self.assertTrue(len(ops_stream) > 0)
        op_stat = b.ops_statistics(start=self.start, stop=self.stop)
        op_stat2 = {"transfer": 0, "vote": 0}
        for op in ops_stream:
            self.assertIn(op["type"], opNames)
            op_stat2[op["type"]] += 1
            self.assertTrue(op["block_num"] >= self.start)
            self.assertTrue(op["block_num"] <= self.stop)
        self.assertEqual(op_stat["transfer"], op_stat2["transfer"])
        self.assertEqual(op_stat["vote"], op_stat2["vote"])

        ops_ops = []
        for op in b.ops(start=self.start, stop=self.stop):
            ops_ops.append(op)
        self.assertTrue(len(ops_ops) > 0)
        op_stat3 = {"transfer": 0, "vote": 0}

        for op in ops_ops:
            if op["op"][0] in opNames:
                op_stat3[op["op"][0]] += 1
            self.assertTrue(op["block_num"] >= self.start)
            self.assertTrue(op["block_num"] <= self.stop)
        self.assertEqual(op_stat["transfer"], op_stat3["transfer"])
        self.assertEqual(op_stat["vote"], op_stat3["vote"])        

        ops_blocks = []
        for op in b.blocks(start=self.start, stop=self.stop):
            ops_blocks.append(op)
        op_stat4 = {"transfer": 0, "vote": 0}
        self.assertTrue(len(ops_blocks) > 0)
        for block in ops_blocks:
            for tran in block["transactions"]:
                for op in tran['operations']:
                    if op[0] in opNames:
                        op_stat4[op[0]] += 1            
            self.assertTrue(block["block_num"] >= self.start)
            self.assertTrue(block["block_num"] <= self.stop)
        self.assertEqual(op_stat["transfer"], op_stat4["transfer"])
        self.assertEqual(op_stat["vote"], op_stat4["vote"])
