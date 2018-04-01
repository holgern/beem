from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from beem import Steem
from beem.instance import set_shared_steem_instance
from beem.transactionbuilder import TransactionBuilder
from beembase.operations import Transfer
from beem.account import Account
from beem.exceptions import (
    InsufficientAuthorityError,
    MissingKeyError,
    InvalidWifError,
    WalletLocked
)
from beemapi import exceptions
from beem.wallet import Wallet

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://node.steem.ws", "wss://steemd.steemgigs.org", "wss://steemd.steemit.com",
         "wss://steemd.minnowsupportproject.org"]


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.stm = Steem(
            node=nodes,
            keys={"active": wif, "owner": wif, "memo": wif},
            nobroadcast=True,
        )
        set_shared_steem_instance(self.stm)
        self.stm.set_default_account("test")

    def test_appendWif(self):
        stm = self.stm
        tx = TransactionBuilder(steem_instance=stm)
        tx.appendOps(Transfer(**{"from": "test",
                                 "to": "test1",
                                 "amount": "1 STEEM",
                                 "memo": ""}))
        with self.assertRaises(
            MissingKeyError
        ):
            tx.sign()
        with self.assertRaises(
            InvalidWifError
        ):
            tx.appendWif("abcdefg")
        tx.appendWif(wif)
        tx.sign()
        self.assertTrue(len(tx["signatures"]) > 0)

    def test_appendSigner(self):
        stm = self.stm
        tx = TransactionBuilder(steem_instance=stm)
        tx.appendOps(Transfer(**{"from": "test",
                                 "to": "test1",
                                 "amount": "1 STEEM",
                                 "memo": ""}))
        account = Account("test", steem_instance=stm)
        with self.assertRaises(
            AssertionError
        ):
            tx.appendSigner(account, "abcdefg")
        tx.appendSigner(account, "active")
        self.assertTrue(len(tx.wifs) > 0)
        tx.sign()
        self.assertTrue(len(tx["signatures"]) > 0)

    def test_TransactionConstructor(self):
        stm = self.stm
        opTransfer = Transfer(**{"from": "test",
                                 "to": "test1",
                                 "amount": "1 STEEM",
                                 "memo": ""})
        tx1 = TransactionBuilder(steem_instance=stm)
        tx1.appendOps(opTransfer)
        tx = TransactionBuilder(tx1, steem_instance=stm)
        self.assertFalse(tx.is_empty())
        self.assertTrue(len(tx.list_operations()) == 1)
        self.assertTrue(repr(tx) is not None)
        self.assertTrue(str(tx) is not None)
        account = Account("test", steem_instance=stm)
        tx.appendSigner(account, "active")
        self.assertTrue(len(tx.wifs) > 0)
        tx.sign()
        self.assertTrue(len(tx["signatures"]) > 0)

    def test_emptyTransaction(self):
        stm = self.stm
        tx = TransactionBuilder(steem_instance=stm)
        self.assertTrue(tx.is_empty())
        self.assertTrue(tx["ref_block_num"] is not None)

    def test_verifyAuthority(self):
        stm = self.stm
        tx = TransactionBuilder(steem_instance=stm)
        tx.appendOps(Transfer(**{"from": "test",
                                 "to": "test1",
                                 "amount": "1 STEEM",
                                 "memo": ""}))
        account = Account("test", steem_instance=stm)
        tx.appendSigner(account, "active")
        tx.appendWif(wif)
        self.assertTrue(len(tx.wifs) > 0)
        tx.sign()
        with self.assertRaises(
            exceptions.MissingRequiredActiveAuthority
        ):
            tx.verify_authority()
        self.assertTrue(len(tx["signatures"]) > 0)
