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
from beem.wallet import Wallet
from beem.transactionbuilder import TransactionBuilder
from beembase.operations import Transfer
from beemgraphenebase.account import PasswordKey, PrivateKey, PublicKey
from beem.utils import parse_time, formatTimedelta
from beemapi.rpcutils import NumRetriesReached

# Py3 compatibility
import sys

core_unit = "STM"


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stm = shared_steem_instance()
        stm.config.refreshBackup()
        stm.set_default_nodes("")
        del stm
        cls.url = "https://api.steemitdev.com"
        bts = Steem(
            node=[cls.url],
            nobroadcast=True,
            num_retries=10
        )
        set_shared_steem_instance(bts)

    @classmethod
    def tearDownClass(cls):
        stm = shared_steem_instance()
        stm.config.recover_with_latest_backup()

    def test_account(self):
        acc = Account("test")
        self.assertEqual(acc.steem.rpc.url, self.url)
        self.assertEqual(acc["balance"].steem.rpc.url, self.url)

    def test_amount(self):
        o = Amount("1 SBD")
        self.assertEqual(o.steem.rpc.url, self.url)

    def test_block(self):
        o = Block(1)
        self.assertEqual(o.steem.rpc.url, self.url)

    def test_blockchain(self):
        o = Blockchain()
        self.assertEqual(o.steem.rpc.url, self.url)

    def test_comment(self):
        o = Comment("@gtg/witness-gtg-log")
        self.assertEqual(o.steem.rpc.url, self.url)

    def test_market(self):
        o = Market()
        self.assertEqual(o.steem.rpc.url, self.url)

    def test_price(self):
        o = Price(10.0, "STEEM/SBD")
        self.assertEqual(o.steem.rpc.url, self.url)

    def test_vote(self):
        o = Vote("@gtg/ffdhu-gtg-witness-log|gandalf")
        self.assertEqual(o.steem.rpc.url, self.url)

    def test_wallet(self):
        o = Wallet()
        self.assertEqual(o.steem.rpc.url, self.url)

    def test_witness(self):
        o = Witness("gtg")
        self.assertEqual(o.steem.rpc.url, self.url)

    def test_transactionbuilder(self):
        o = TransactionBuilder()
        self.assertEqual(o.steem.rpc.url, self.url)

    def test_steem(self):
        stm = shared_steem_instance()
        stm = Steem()
        del stm
        o = shared_steem_instance()
        self.assertEqual(o.rpc.url, self.url)

    def test_config(self):
        set_shared_config({"node": [self.url]})
        set_shared_steem_instance(None)
        o = shared_steem_instance()
        self.assertEqual(o.rpc.url, self.url)
