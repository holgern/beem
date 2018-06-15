from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from parameterized import parameterized
from datetime import datetime, timedelta
import pytz
import time
from pprint import pprint
from beem import Steem
from beem.blockchain import Blockchain
from beem.block import Block
from beem.instance import set_shared_steem_instance
from beem.nodelist import NodeList


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodelist = NodeList()
        nodelist.update_nodes(steem_instance=Steem(node=nodelist.get_nodes(normal=True, appbase=True), num_retries=10))
        cls.bts = Steem(
            node=nodelist.get_nodes(),
            nobroadcast=True,
            timeout=30,
            num_retries=10,
        )
        # from getpass import getpass
        # self.bts.wallet.unlock(getpass())
        set_shared_steem_instance(cls.bts)
        cls.bts.set_default_account("test")

        b = Blockchain(steem_instance=cls.bts)
        num = b.get_current_block_num()
        # num = 23346630
        cls.start = num - 25
        cls.stop = num
        # cls.N_transfer = 121
        # cls.N_vote = 2825

    def test_stream_threading(self):
        bts = self.bts
        b = Blockchain(steem_instance=bts)
        ops_stream = []
        opNames = ["transfer", "vote"]

        for op in b.stream(opNames=opNames, start=self.start, stop=self.stop, threading=True, thread_num=8):
            ops_stream.append(op)
        # self.assertEqual(self.N_transfer + self.N_vote, len(ops_stream))

        op_stat = b.ops_statistics(start=self.start, stop=self.stop, with_virtual_ops=False)
        self.assertEqual(op_stat["vote"] + op_stat["transfer"], len(ops_stream))

        ops_blocks = []
        last_id = self.start - 1
        for op in b.blocks(start=self.start, stop=self.stop, threading=True, thread_num=8):
            ops_blocks.append(op)
            self.assertEqual(op.identifier, last_id + 1)
            last_id += 1
        op_stat4 = {"transfer": 0, "vote": 0}
        self.assertTrue(len(ops_blocks) > 0)
        for block in ops_blocks:
            for op in block.operations:
                if isinstance(op, dict) and 'type' in op:
                    op_type = op["type"]
                    if len(op_type) > 10 and op_type[len(op_type) - 10:] == "_operation":
                        op_type = op_type[:-10]
                else:
                    if "op" in op:
                        op_type = op["op"][0]
                    else:
                        op_type = op[0]
                if op_type in opNames:
                    op_stat4[op_type] += 1
            self.assertTrue(block.identifier >= self.start)
            self.assertTrue(block.identifier <= self.stop)
        self.assertEqual(op_stat["transfer"], op_stat4["transfer"])
        self.assertEqual(op_stat["vote"], op_stat4["vote"])
