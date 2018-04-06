from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from parameterized import parameterized
from beem import Steem
from beem.instance import set_shared_steem_instance
from beem.transactionbuilder import TransactionBuilder
from beembase.operations import Transfer
from beem.account import Account
from beem.amount import Amount
from beem.exceptions import (
    InsufficientAuthorityError,
    MissingKeyError,
    InvalidWifError,
    WalletLocked
)
from beemgraphenebase.transactions import formatTimeFromNow
from beemapi import exceptions
from beem.wallet import Wallet
from beem.utils import get_node_list

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.stm = Steem(
            node=get_node_list(appbase=False),
            keys={"active": wif, "owner": wif, "memo": wif},
            nobroadcast=True,
            num_retries=10
        )
        self.appbase = Steem(
            node=get_node_list(appbase=True),
            nobroadcast=True,
            keys={"active": wif, "owner": wif, "memo": wif},
            num_retries=10
        )
        set_shared_steem_instance(self.stm)
        self.stm.set_default_account("test")

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_appendWif(self, node_param):
        if node_param == "non_appbase":
            stm = self.stm
        else:
            stm = self.appbase
        tx = TransactionBuilder(steem_instance=stm)
        tx.appendOps(Transfer(**{"from": "test",
                                 "to": "test1",
                                 "amount": Amount("1 STEEM", steem_instance=stm),
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

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_appendSigner(self, node_param):
        if node_param == "non_appbase":
            stm = self.stm
        else:
            stm = self.appbase
        tx = TransactionBuilder(steem_instance=stm)
        tx.appendOps(Transfer(**{"from": "test",
                                 "to": "test1",
                                 "amount": Amount("1 STEEM", steem_instance=stm),
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

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_TransactionConstructor(self, node_param):
        if node_param == "non_appbase":
            stm = self.stm
        else:
            stm = self.appbase
        opTransfer = Transfer(**{"from": "test",
                                 "to": "test1",
                                 "amount": Amount("1 STEEM", steem_instance=stm),
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
                                 "amount": Amount("1 STEEM", steem_instance=stm),
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

    def test_verifyAuthority_appbase(self):
        stm = self.appbase
        tx = TransactionBuilder(steem_instance=stm)
        tx.appendOps(Transfer(**{"from": "test",
                                 "to": "test1",
                                 "amount": Amount("1 STEEM", steem_instance=stm),
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

    def test_Transfer_broadcast(self):
        stm = Steem(node=get_node_list(appbase=False),
                    keys=[wif],
                    num_retries=10)
        tx = TransactionBuilder(expiration=10, steem_instance=stm)
        tx.appendOps(Transfer(**{"from": "test",
                                 "to": "test1",
                                 "amount": Amount("1 STEEM", steem_instance=stm),
                                 "memo": ""}))
        tx.appendSigner("test", "active")
        tx.sign()
        with self.assertRaises(
            exceptions.MissingRequiredActiveAuthority
        ):
            tx.broadcast()

    def test_Transfer_broadcast_appbase(self):
        stm = Steem(node=get_node_list(appbase=True),
                    keys=[wif],
                    num_retries=10)
        tx = TransactionBuilder(expiration=10, steem_instance=stm)
        tx.appendOps(Transfer(**{"from": "test",
                                 "to": "test1",
                                 "amount": Amount("1 STEEM", steem_instance=stm),
                                 "memo": ""}))
        tx.appendSigner("test", "active")
        tx.sign()
        with self.assertRaises(
            exceptions.MissingRequiredActiveAuthority
        ):
            tx.broadcast()
