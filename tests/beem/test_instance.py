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
from parameterized import parameterized
from pprint import pprint
from beem import Steem
from beem.amount import Amount
from beem.witness import Witness
from beem.account import Account
from beem.instance import set_shared_steem_instance, shared_steem_instance, set_shared_config
from beem.blockchain import Blockchain
from beem.block import Block
from beem.market import Market
from beem.price import Price
from beem.comment import Comment
from beem.vote import Vote
from beemapi.exceptions import RPCConnection
from beem.wallet import Wallet
from beem.transactionbuilder import TransactionBuilder
from beembase.operations import Transfer
from beemgraphenebase.account import PasswordKey, PrivateKey, PublicKey
from beem.utils import parse_time, formatTimedelta
from beem.nodelist import NodeList

# Py3 compatibility
import sys

core_unit = "STM"


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodelist = NodeList()
        cls.nodelist.update_nodes(steem_instance=Steem(node=cls.nodelist.get_nodes(normal=True, appbase=True), num_retries=10))
        stm = Steem(node=cls.nodelist.get_nodes())
        stm.config.refreshBackup()
        stm.set_default_nodes(["xyz"])
        del stm

        cls.urls = cls.nodelist.get_nodes()
        cls.bts = Steem(
            node=cls.urls,
            nobroadcast=True,
            num_retries=10
        )
        set_shared_steem_instance(cls.bts)

    @classmethod
    def tearDownClass(cls):
        stm = Steem(node=cls.nodelist.get_nodes())
        stm.config.recover_with_latest_backup()

    @parameterized.expand([
        ("instance"),
        ("steem")
    ])
    def test_account(self, node_param):
        if node_param == "instance":
            set_shared_steem_instance(self.bts)
            acc = Account("test")
            self.assertIn(acc.steem.rpc.url, self.urls)
            self.assertIn(acc["balance"].steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Account("test", steem_instance=Steem(node="https://abc.d", autoconnect=False, num_retries=1))
        else:
            set_shared_steem_instance(Steem(node="https://abc.d", autoconnect=False, num_retries=1))
            stm = self.bts
            acc = Account("test", steem_instance=stm)
            self.assertIn(acc.steem.rpc.url, self.urls)
            self.assertIn(acc["balance"].steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Account("test")

    @parameterized.expand([
        ("instance"),
        ("steem")
    ])
    def test_amount(self, node_param):
        if node_param == "instance":
            stm = Steem(node="https://abc.d", autoconnect=False, num_retries=1)
            set_shared_steem_instance(self.bts)
            o = Amount("1 SBD")
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Amount("1 SBD", steem_instance=stm)
        else:
            set_shared_steem_instance(Steem(node="https://abc.d", autoconnect=False, num_retries=1))
            stm = self.bts
            o = Amount("1 SBD", steem_instance=stm)
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Amount("1 SBD")

    @parameterized.expand([
        ("instance"),
        ("steem")
    ])
    def test_block(self, node_param):
        if node_param == "instance":
            set_shared_steem_instance(self.bts)
            o = Block(1)
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Block(1, steem_instance=Steem(node="https://abc.d", autoconnect=False, num_retries=1))
        else:
            set_shared_steem_instance(Steem(node="https://abc.d", autoconnect=False, num_retries=1))
            stm = self.bts
            o = Block(1, steem_instance=stm)
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Block(1)

    @parameterized.expand([
        ("instance"),
        ("steem")
    ])
    def test_blockchain(self, node_param):
        if node_param == "instance":
            set_shared_steem_instance(self.bts)
            o = Blockchain()
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Blockchain(steem_instance=Steem(node="https://abc.d", autoconnect=False, num_retries=1))
        else:
            set_shared_steem_instance(Steem(node="https://abc.d", autoconnect=False, num_retries=1))
            stm = self.bts
            o = Blockchain(steem_instance=stm)
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Blockchain()

    @parameterized.expand([
        ("instance"),
        ("steem")
    ])
    def test_comment(self, node_param):
        if node_param == "instance":
            set_shared_steem_instance(self.bts)
            o = Comment("@gtg/witness-gtg-log")
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Comment("@gtg/witness-gtg-log", steem_instance=Steem(node="https://abc.d", autoconnect=False, num_retries=1))
        else:
            set_shared_steem_instance(Steem(node="https://abc.d", autoconnect=False, num_retries=1))
            stm = self.bts
            o = Comment("@gtg/witness-gtg-log", steem_instance=stm)
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Comment("@gtg/witness-gtg-log")

    @parameterized.expand([
        ("instance"),
        ("steem")
    ])
    def test_market(self, node_param):
        if node_param == "instance":
            set_shared_steem_instance(self.bts)
            o = Market()
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Market(steem_instance=Steem(node="https://abc.d", autoconnect=False, num_retries=1))
        else:
            set_shared_steem_instance(Steem(node="https://abc.d", autoconnect=False, num_retries=1))
            stm = self.bts
            o = Market(steem_instance=stm)
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Market()

    @parameterized.expand([
        ("instance"),
        ("steem")
    ])
    def test_price(self, node_param):
        if node_param == "instance":
            set_shared_steem_instance(self.bts)
            o = Price(10.0, "STEEM/SBD")
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Price(10.0, "STEEM/SBD", steem_instance=Steem(node="https://abc.d", autoconnect=False, num_retries=1))
        else:
            set_shared_steem_instance(Steem(node="https://abc.d", autoconnect=False, num_retries=1))
            stm = self.bts
            o = Price(10.0, "STEEM/SBD", steem_instance=stm)
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Price(10.0, "STEEM/SBD")

    @parameterized.expand([
        ("instance"),
        ("steem")
    ])
    def test_vote(self, node_param):
        if node_param == "instance":
            set_shared_steem_instance(self.bts)
            o = Vote("@gtg/ffdhu-gtg-witness-log|gandalf")
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Vote("@gtg/ffdhu-gtg-witness-log|gandalf", steem_instance=Steem(node="https://abc.d", autoconnect=False, num_retries=1))
        else:
            set_shared_steem_instance(Steem(node="https://abc.d", autoconnect=False, num_retries=1))
            stm = self.bts
            o = Vote("@gtg/ffdhu-gtg-witness-log|gandalf", steem_instance=stm)
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Vote("@gtg/ffdhu-gtg-witness-log|gandalf")

    @parameterized.expand([
        ("instance"),
        ("steem")
    ])
    def test_wallet(self, node_param):
        if node_param == "instance":
            set_shared_steem_instance(self.bts)
            o = Wallet()
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                o = Wallet(steem_instance=Steem(node="https://abc.d", autoconnect=False, num_retries=1))
                o.steem.get_config()
        else:
            set_shared_steem_instance(Steem(node="https://abc.d", autoconnect=False, num_retries=1))
            stm = self.bts
            o = Wallet(steem_instance=stm)
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                o = Wallet()
                o.steem.get_config()

    @parameterized.expand([
        ("instance"),
        ("steem")
    ])
    def test_witness(self, node_param):
        if node_param == "instance":
            set_shared_steem_instance(self.bts)
            o = Witness("gtg")
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Witness("gtg", steem_instance=Steem(node="https://abc.d", autoconnect=False, num_retries=1))
        else:
            set_shared_steem_instance(Steem(node="https://abc.d", autoconnect=False, num_retries=1))
            stm = self.bts
            o = Witness("gtg", steem_instance=stm)
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                Witness("gtg")

    @parameterized.expand([
        ("instance"),
        ("steem")
    ])
    def test_transactionbuilder(self, node_param):
        if node_param == "instance":
            set_shared_steem_instance(self.bts)
            o = TransactionBuilder()
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                o = TransactionBuilder(steem_instance=Steem(node="https://abc.d", autoconnect=False, num_retries=1))
                o.steem.get_config()
        else:
            set_shared_steem_instance(Steem(node="https://abc.d", autoconnect=False, num_retries=1))
            stm = self.bts
            o = TransactionBuilder(steem_instance=stm)
            self.assertIn(o.steem.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                o = TransactionBuilder()
                o.steem.get_config()

    @parameterized.expand([
        ("instance"),
        ("steem")
    ])
    def test_steem(self, node_param):
        if node_param == "instance":
            set_shared_steem_instance(self.bts)
            o = Steem(node=self.urls)
            o.get_config()
            self.assertIn(o.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                stm = Steem(node="https://abc.d", autoconnect=False, num_retries=1)
                stm.get_config()
        else:
            set_shared_steem_instance(Steem(node="https://abc.d", autoconnect=False, num_retries=1))
            stm = self.bts
            o = stm
            o.get_config()
            self.assertIn(o.rpc.url, self.urls)
            with self.assertRaises(
                RPCConnection
            ):
                stm = shared_steem_instance()
                stm.get_config()

    def test_config(self):
        set_shared_config({"node": self.urls})
        set_shared_steem_instance(None)
        o = shared_steem_instance()
        self.assertIn(o.rpc.url, self.urls)
