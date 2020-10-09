# -*- coding: utf-8 -*-
import unittest
from parameterized import parameterized
from beem import Steem
from beem.instance import set_shared_steem_instance
from beem.transactionbuilder import TransactionBuilder
from beembase.signedtransactions import Signed_Transaction
from beembase.operations import Transfer
from beem.account import Account
from beem.block import Block
from beemgraphenebase.base58 import Base58
from beem.amount import Amount
from beem.exceptions import (
    InsufficientAuthorityError,
    MissingKeyError,
    InvalidWifError
)
from beemstorage.exceptions import WalletLocked
from beemapi import exceptions
from beem.wallet import Wallet
from beem.utils import formatTimeFromNow
from .nodes import get_hive_nodes, get_steem_nodes
wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
wif2 = "5JKu2dFfjKAcD6aP1HqBDxMNbdwtvPS99CaxBzvMYhY94Pt6RDS"
wif3 = "5K1daXjehgPZgUHz6kvm55ahEArBHfCHLy6ew8sT7sjDb76PU2P"


class Testcases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        node_list = get_hive_nodes()
        cls.stm = Steem(
            node=node_list,
            keys={"active": wif, "owner": wif2, "memo": wif3},
            nobroadcast=True,
            num_retries=10
        )
        cls.steemit = Steem(
            node="https://api.steemit.com",
            nobroadcast=True,
            keys={"active": wif, "owner": wif2, "memo": wif3},
            num_retries=10
        )
        set_shared_steem_instance(cls.stm)
        cls.stm.set_default_account("test")

    def test_emptyTransaction(self):
        stm = self.stm
        tx = TransactionBuilder(steem_instance=stm)
        self.assertTrue(tx.is_empty())
        self.assertTrue(tx["ref_block_num"] is not None)

    def test_verify_transaction(self):
        stm = self.stm
        block = Block(22005665, steem_instance=stm)
        trx = block.transactions[28]
        signed_tx = Signed_Transaction(trx)
        key = signed_tx.verify(chain=stm.chain_params, recover_parameter=False)
        public_key = format(Base58(key[0]), stm.prefix)
        self.assertEqual(public_key, "STM4tzr1wjmuov9ftXR6QNv7qDWsbShMBPQpuwatZsfSc5pKjRDfq")
