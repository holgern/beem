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
from beem.notify import Notify
from beem.instance import set_shared_steem_instance
from beem.nodelist import NodeList
# Py3 compatibility
import sys

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
core_unit = "STM"


class TestBot:
    def init(self):
        self.notify = None
        self.blocks = 0

    def new_block(self, block):
        chunk = 5
        self.blocks = self.blocks + 1
        if self.blocks >= chunk:
            self.notify.close()


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        nodelist = NodeList()
        nodelist.update_nodes(steem_instance=Steem(node=nodelist.get_nodes(normal=True, appbase=True), num_retries=10))
        self.bts = Steem(
            node=nodelist.get_nodes(),
            nobroadcast=True,
            num_retries=10
        )

    def test_connect(self):
        tb = TestBot()
        tb.init()
        notify = Notify(on_block=tb.new_block, steem_instance=self.bts)
        tb.notify = notify
        notify.listen()
        self.assertEqual(tb.blocks, 5)
