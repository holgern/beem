from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import range
from builtins import super
import mock
import string
import unittest
from parameterized import parameterized
import random
import itertools
from pprint import pprint
from beem import Steem
from beemapi.steemnoderpc import SteemNodeRPC
from beemapi.websocket import SteemWebsocket
from beemapi import exceptions
from beem.instance import set_shared_steem_instance
# Py3 compatibility
import sys

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
core_unit = "STM"
nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://node.steem.ws", "wss://steemd.steemgigs.org", "wss://steemd.steemit.com",
         "wss://steemd.minnowsupportproject.org"]
nodes_https = ['https://api.steemit.com', 'https://steemd.privex.io', 'https://steemd.pevo.science', 'https://rpc.steemliberator.com',
               'https://rpc.buildteam.io', 'https://steemd.minnowsupportproject.org', 'https://gtg.steem.house:8090', 'https://seed.bitcoiner.me']
nodes_appbase = ["https://api.steemitstage.com", "wss://appbasetest.timcliff.com"]
test_list = ["wss://steemd.doesnot.exists", "wss://api.steemit.com", "wss://steemd.pevo.science", "wss://gtg.steem.house:8090",
             "https://api.steemit.com", "https://api.steemitstage.com", "wss://appbasetest.timcliff.com", 'https://steemd.privex.io',
             'https://steemd.pevo.science', 'https://rpc.steemliberator.com',
             'https://rpc.buildteam.io', 'https://steemd.minnowsupportproject.org', 'https://gtg.steem.house:8090', 'https://seed.bitcoiner.me']


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bts = Steem(
            node=nodes,
            nobroadcast=True,
            keys={"active": wif, "owner": wif, "memo": wif}
        )
        self.appbase = Steem(
            node=nodes_appbase,
            nobroadcast=True,
            keys={"active": wif, "owner": wif, "memo": wif}
        )
        # from getpass import getpass
        # self.bts.wallet.unlock(getpass())
        set_shared_steem_instance(self.bts)
        self.bts.set_default_account("test")

    def test_non_appbase(self):
        bts = self.bts
        self.assertTrue(bts.chain_params['min_version'] == '0.0.0')
        self.assertFalse(bts.rpc.get_use_appbase())
        self.assertTrue(isinstance(bts.rpc.get_config(api="database"), dict))
        with self.assertRaises(
            exceptions.NoMethodWithName
        ):
            bts.rpc.get_config_abc()

    def test_appbase(self):
        bts = self.appbase
        self.assertTrue(bts.chain_params['min_version'] == '0.19.4')
        self.assertTrue(bts.rpc.get_use_appbase())
        self.assertTrue(isinstance(bts.rpc.get_config(api="database"), dict))
        with self.assertRaises(
            exceptions.NoApiWithName
        ):
            bts.rpc.get_config(api="abc")
        with self.assertRaises(
            exceptions.NoMethodWithName
        ):
            bts.rpc.get_config_abc()
        bts.rpc.register_apis(apis=["database"])

    def test_connect_test_node(self):
        rpc = SteemNodeRPC(urls=test_list)
        self.assertIn(rpc.url, nodes + nodes_appbase + nodes_https)
        rpc.rpcclose()
        rpc.rpcconnect()
        rpc.register_apis()
        self.assertIn(rpc.url, nodes + nodes_appbase + nodes_https)
