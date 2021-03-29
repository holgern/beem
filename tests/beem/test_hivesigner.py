# -*- coding: utf-8 -*-
import string
import unittest
from parameterized import parameterized
import random
import json
from pprint import pprint
from beem import Steem, exceptions
from beem.amount import Amount
from beem.memo import Memo
from beem.version import version as beem_version
from beem.wallet import Wallet
from beem.witness import Witness
from beem.account import Account
from beemgraphenebase.account import PrivateKey
from beem.instance import set_shared_steem_instance
from .nodes import get_hive_nodes, get_steem_nodes
from beem.hivesigner import HiveSigner
# Py3 compatibility
import sys
core_unit = "STM"


class Testcases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bts = Steem(
            node=get_hive_nodes(),
            nobroadcast=True,
            unsigned=True,
            data_refresh_time_seconds=900,
            num_retries=10)

        cls.account = Account("test", full=True, steem_instance=cls.bts)

    def test_transfer(self):
        bts = self.bts
        acc = self.account
        acc.blockchain.txbuffer.clear()
        tx = acc.transfer(
            "test1", 1.000, "HIVE", memo="test")
        sc2 = HiveSigner(steem_instance=bts)
        url = sc2.url_from_tx(tx)
        url_test = 'https://hivesigner.com/sign/transfer?from=test&to=test1&amount=1.000+HIVE&memo=test'
        self.assertEqual(len(url), len(url_test))
        self.assertEqual(len(url.split('?')), 2)
        self.assertEqual(url.split('?')[0], url_test.split('?')[0])

        url_parts = (url.split('?')[1]).split('&')
        url_test_parts = (url_test.split('?')[1]).split('&')

        self.assertEqual(len(url_parts), 4)
        self.assertEqual(len(list(set(url_parts).intersection(set(url_test_parts)))), 4)

    def test_login_url(self):
        bts = self.bts
        sc2 = HiveSigner(steem_instance=bts)
        url = sc2.get_login_url("localhost", scope="login,vote")
        url_test = 'https://hivesigner.com/oauth2/authorize?client_id=None&redirect_uri=localhost&scope=login,vote'
        self.assertEqual(len(url), len(url_test))
        self.assertEqual(len(url.split('?')), 2)
        self.assertEqual(url.split('?')[0], url_test.split('?')[0])

        url_parts = (url.split('?')[1]).split('&')
        url_test_parts = (url_test.split('?')[1]).split('&')

        self.assertEqual(len(url_parts), 3)
        self.assertEqual(len(list(set(url_parts).intersection(set(url_test_parts)))), 3)
