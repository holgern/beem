from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import range
from builtins import super
import string
import unittest
import random
import itertools
from pprint import pprint
from beem import Steem
from beemapi.websocket import SteemWebsocket
from beem.instance import set_shared_steem_instance
from beem.nodelist import NodeList
# Py3 compatibility
import sys

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
core_unit = "STM"


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        nodelist = NodeList()
        nodelist.update_nodes(steem_instance=Steem(node=nodelist.get_nodes(normal=True, appbase=True), num_retries=10))
        stm = Steem(node=nodelist.get_nodes())

        self.ws = SteemWebsocket(
            urls=stm.rpc.nodes,
            num_retries=10
        )

    def test_connect(self):
        ws = self.ws
        self.assertTrue(len(next(ws.nodes)) > 0)
