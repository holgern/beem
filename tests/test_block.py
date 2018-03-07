from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from parameterized import parameterized
from pprint import pprint
from beem import Steem, exceptions
from beem.block import Block, BlockHeader
from datetime import datetime
from beem.instance import set_shared_steem_instance

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://node.steem.ws", "wss://steemd.steemgigs.org", "wss://steemd.steemit.com",
         "wss://steemd.minnowsupportproject.org"]
nodes_appbase = ["https://api.steemitstage.com"]


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
    def test_block(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        block = Block(1, steem_instance=bts)
        self.assertEqual(block.identifier, 1)
        self.assertEqual(block.id, 1)
        self.assertTrue(isinstance(block.time(), datetime))
        self.assertTrue(isinstance(block["block"], dict))

        block2 = Block(2, steem_instance=bts)
        self.assertTrue(block2.time() > block.time())
        with self.assertRaises(
            exceptions.BlockDoesNotExistsException
        ):
            Block(0, steem_instance=bts)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_block_header(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        block = BlockHeader(1, steem_instance=bts)
        self.assertEqual(block.identifier, 1)
        self.assertEqual(block.id, 1)
        self.assertTrue(isinstance(block.time(), datetime))
        self.assertTrue(isinstance(block["header"], dict))

        block2 = BlockHeader(2, steem_instance=bts)
        self.assertTrue(block2.time() > block.time())
        with self.assertRaises(
            exceptions.BlockDoesNotExistsException
        ):
            BlockHeader(0, steem_instance=bts)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_block_ops(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        block = Block(20000000, steem_instance=bts)
        self.assertTrue(len(block.ops()))
        self.assertTrue(isinstance(block.ops_statistics(), dict))
