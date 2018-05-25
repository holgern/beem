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
import json
from pprint import pprint
from beem import Steem
from beem.amount import Amount
from beem.memo import Memo
from beem.version import version as beem_version
from beem.wallet import Wallet
from beem.witness import Witness
from beem.account import Account
from beemgraphenebase.account import PrivateKey
from beem.instance import set_shared_steem_instance, shared_steem_instance
from beem.nodelist import NodeList
# Py3 compatibility
import sys
core_unit = "STM"
wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stm = shared_steem_instance()
        stm.config.refreshBackup()
        nodelist = NodeList()

        cls.stm = Steem(
            node=nodelist.get_nodes(appbase=False),
            nobroadcast=True,
            # We want to bundle many operations into a single transaction
            bundle=True,
            num_retries=10
            # Overwrite wallet to use this list of wifs only
        )
        cls.appbase = Steem(
            node=nodelist.get_nodes(normal=False, appbase=True),
            nobroadcast=True,
            bundle=True,
            num_retries=10
        )
        cls.stm.set_default_account("test")
        set_shared_steem_instance(cls.stm)
        # self.stm.newWallet("TestingOneTwoThree")

        cls.wallet = Wallet(steem_instance=cls.stm)
        cls.wallet.wipe(True)
        cls.wallet.newWallet(pwd="TestingOneTwoThree")
        cls.wallet.unlock(pwd="TestingOneTwoThree")
        cls.wallet.addPrivateKey(wif)

    @classmethod
    def tearDownClass(cls):
        stm = shared_steem_instance()
        stm.config.recover_with_latest_backup()

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_set_default_account(self, node_param):
        if node_param == "non_appbase":
            stm = self.stm
        elif node_param == "appbase":
            stm = self.appbase
        stm.set_default_account("test")

        self.assertEqual(stm.config["default_account"], "test")
