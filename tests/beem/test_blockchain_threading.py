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
            num_retries=30,
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

    def test_block_threading(self):
        bts = self.bts
        b = Blockchain(steem_instance=bts)
        blocks_no_threading = []
        for block in b.blocks(start=self.start, stop=self.stop, threading=False, thread_num=8):
            blocks_no_threading.append(block)

        for n in range(5):
            blocks = []
            for block in b.blocks(start=self.start, stop=self.stop, threading=True, thread_num=8):
                blocks.append(block)

            for i in range(min(len(blocks), len(blocks_no_threading))):
                self.assertEqual(blocks[i]["block_id"], blocks_no_threading[i]["block_id"])
            self.assertEqual(len(blocks_no_threading), len(blocks))

    def test_stream_threading(self):
        bts = self.bts
        b = Blockchain(steem_instance=bts)

        ops_stream_no_threading = []
        opNames = ["transfer", "vote"]

        block_num_list2 = []
        for op in b.stream(opNames=opNames, start=self.start, stop=self.stop, threading=False):
            ops_stream_no_threading.append(op)
            if op["block_num"] not in block_num_list2:
                block_num_list2.append(op["block_num"])
        for n in range(5):
            ops_stream = []
            block_num_list = []
            for op in b.stream(opNames=opNames, start=self.start, stop=self.stop, threading=True, thread_num=8):
                ops_stream.append(op)
                if op["block_num"] not in block_num_list:
                    block_num_list.append(op["block_num"])

            self.assertEqual(ops_stream[0]["block_num"], ops_stream_no_threading[0]["block_num"])
            self.assertEqual(ops_stream[-1]["block_num"], ops_stream_no_threading[-1]["block_num"])
            self.assertEqual(len(ops_stream_no_threading), len(ops_stream))

        self.assertEqual(len(block_num_list), len(block_num_list2))
        for i in range(len(block_num_list)):
            self.assertEqual(block_num_list[i], block_num_list2[i])

    def test_stream_threading2(self):
        bts = self.bts
        b = Blockchain(steem_instance=bts)

        ops_stream = []
        start_block = 25097000
        stop_block = 25097100
        opNames = ["account_create", "custom_json"]
        for op in b.stream(start=int(start_block), stop=int(stop_block), opNames=opNames, threading=True, thread_num=8):
            ops_stream.append(op)
        self.assertTrue(ops_stream[0]["block_num"] >= start_block)
        self.assertTrue(ops_stream[-1]["block_num"] <= stop_block)
        op_stat = b.ops_statistics(start=start_block, stop=stop_block)
        self.assertEqual(op_stat["account_create"] + op_stat["custom_json"], len(ops_stream))
