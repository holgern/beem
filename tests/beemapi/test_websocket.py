from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import range
from builtins import super
import mock
import string
import unittest
import random
import itertools
from pprint import pprint
from beem import Steem
from beemapi.websocket import SteemWebsocket
from beem.instance import set_shared_steem_instance
# Py3 compatibility
import sys

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
core_unit = "STM"

nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://node.steem.ws", "wss://steemd.steemgigs.org", "wss://steemd.steemit.com",
         "wss://steemd.minnowsupportproject.org"]


class TestBot:
    def init(self):
        self.ws = None
        self.blocks = 0

    def new_block(self, block):
        chunk = 5
        self.blocks = self.blocks + 1
        print(str(self.blocks))
        if self.blocks % chunk == 0:
            self.ws.stop()


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        stm = Steem(node=nodes)

        self.ws = SteemWebsocket(
            urls=stm.rpc.urls,
            timeout=15,
            num_retries=10
        )

    def test_connect(self):
        tb = TestBot()
        tb.init()
        tb.ws = self.ws
        self.ws.on_block += tb.new_block
        self.ws.run_forever()
        self.assertEqual(tb.blocks, 5)
