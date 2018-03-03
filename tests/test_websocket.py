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


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ws = SteemWebsocket(
            nodes,
        )

    def test_connect(self):
        self.assertIn(next(self.ws.urls), nodes)
        self.assertIn(next(self.ws.urls), nodes)
        self.assertIn(next(self.ws.urls), nodes)
        self.assertIn(next(self.ws.urls), nodes)

        