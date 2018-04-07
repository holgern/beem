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
nodes_appbase = ["https://api.steemit.com", "wss://appbasetest.timcliff.com"]
test_list = ["wss://steemd.doesnot.exists", "wss://api.steemit.com", "wss://steemd.pevo.science", "wss://gtg.steem.house:8090",
             "https://api.steemit.com", "wss://appbasetest.timcliff.com", 'https://steemd.privex.io',
             'https://steemd.pevo.science', 'https://rpc.steemliberator.com',
             'https://rpc.buildteam.io', 'https://steemd.minnowsupportproject.org', 'https://gtg.steem.house:8090', 'https://seed.bitcoiner.me']


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bts = Steem(
            node=nodes,
            nobroadcast=True,
            keys={"active": wif, "owner": wif, "memo": wif},
            num_retries=10
        )
        self.appbase = Steem(
            node=nodes_appbase,
            nobroadcast=True,
            keys={"active": wif, "owner": wif, "memo": wif},
            num_retries=10
        )
        self.rpc = SteemNodeRPC(urls=test_list)
        # from getpass import getpass
        # self.bts.wallet.unlock(getpass())
        set_shared_steem_instance(self.bts)
        self.bts.set_default_account("test")

    def get_reply(self, msg):
        reply = '<html>  <head><title>403 Forbidden</title></head><body bgcolor="white"><center><h1>' \
                '%s</h1></center><hr><center>nginx</center></body>    </html>' % (msg)
        return reply

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

    def test_connect_test_node(self):
        rpc = self.rpc
        self.assertIn(rpc.url, nodes + nodes_appbase + nodes_https)
        rpc.rpcclose()
        rpc.rpcconnect()
        self.assertIn(rpc.url, nodes + nodes_appbase + nodes_https)

    def test_connect_test_node2(self):
        rpc = self.rpc
        self.assertIn(rpc.url, nodes + nodes_appbase + nodes_https)
        rpc.next()
        self.assertIn(rpc.url, nodes + nodes_appbase + nodes_https)

    def test_connect_test_str_list(self):
        str_list = "wss://steemd.pevo.science;wss://gtg.steem.house:8090;wss://rpc.steemliberator.com;wss://rpc.buildteam.io"
        rpc = SteemNodeRPC(urls=str_list)
        self.assertIn(rpc.url, nodes + nodes_appbase + nodes_https)
        rpc.next()
        self.assertIn(rpc.url, nodes + nodes_appbase + nodes_https)

    def test_connect_test_str_list2(self):
        str_list = "wss://steemd.pevo.science, wss://gtg.steem.house:8090, wss://rpc.steemliberator.com, wss://rpc.buildteam.io"
        rpc = SteemNodeRPC(urls=str_list)
        self.assertIn(rpc.url, nodes + nodes_appbase + nodes_https)
        rpc.next()
        self.assertIn(rpc.url, nodes + nodes_appbase + nodes_https)

    def test_server_error(self):
        rpc = self.rpc
        with self.assertRaises(
            exceptions.RPCErrorDoRetry
        ):
            rpc._check_for_server_error(self.get_reply("500 Internal Server Error"))
        with self.assertRaises(
            exceptions.RPCError
        ):
            rpc._check_for_server_error(self.get_reply("501 Not Implemented"))

        with self.assertRaises(
            exceptions.RPCErrorDoRetry
        ):
            rpc._check_for_server_error(self.get_reply("502 Bad Gateway"))

        with self.assertRaises(
            exceptions.RPCErrorDoRetry
        ):
            rpc._check_for_server_error(self.get_reply("503 Service Temporarily Unavailable"))

        with self.assertRaises(
            exceptions.RPCErrorDoRetry
        ):
            rpc._check_for_server_error(self.get_reply("504 Gateway Time-out"))

        with self.assertRaises(
            exceptions.RPCError
        ):
            rpc._check_for_server_error(self.get_reply("505 HTTP Version not supported"))
        with self.assertRaises(
            exceptions.RPCError
        ):
            rpc._check_for_server_error(self.get_reply("506 Variant Also Negotiates"))

        with self.assertRaises(
            exceptions.RPCError
        ):
            rpc._check_for_server_error(self.get_reply("507 Insufficient Storage"))

        with self.assertRaises(
            exceptions.RPCError
        ):
            rpc._check_for_server_error(self.get_reply("508 Loop Detected"))

        with self.assertRaises(
            exceptions.RPCError
        ):
            rpc._check_for_server_error(self.get_reply("509 Bandwidth Limit Exceeded"))
        with self.assertRaises(
            exceptions.RPCError
        ):
            rpc._check_for_server_error(self.get_reply("510 Not Extended"))

        with self.assertRaises(
            exceptions.RPCError
        ):
            rpc._check_for_server_error(self.get_reply("511 Network Authentication Required"))
