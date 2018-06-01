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
from six import PY2
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
from beem.nodelist import NodeList
from beem.steemconnect import SteemConnect
# Py3 compatibility
import sys
core_unit = "STM"


class Testcases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        nodelist = NodeList()
        cls.bts = Steem(
            node=nodelist.get_nodes(appbase=False),
            nobroadcast=True,
            unsigned=True,
            data_refresh_time_seconds=900,
            num_retries=10)
        cls.appbase = Steem(
            node=nodelist.get_nodes(normal=False, appbase=True),
            nobroadcast=True,
            unsigned=True,
            data_refresh_time_seconds=900,
            num_retries=10)

        cls.account = Account("test", full=True, steem_instance=cls.bts)
        cls.account_appbase = Account("test", full=True, steem_instance=cls.appbase)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_transfer(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
            acc = self.account
        elif node_param == "appbase":
            bts = self.appbase
            acc = self.account_appbase
        acc.steem.txbuffer.clear()
        tx = acc.transfer(
            "test1", 1.000, "STEEM", memo="test")
        sc2 = SteemConnect(steem_instance=bts)
        url = sc2.url_from_tx(tx)
        if PY2:
            self.assertEqual(url, 'https://v2.steemconnect.com/sign/transfer?from=test&memo=test&to=test1&amount=1.000+STEEM')
        else:
            self.assertEqual(url, 'https://v2.steemconnect.com/sign/transfer?from=test&to=test1&amount=1.000+STEEM&memo=test')

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_login_url(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        elif node_param == "appbase":
            bts = self.appbase
        sc2 = SteemConnect(steem_instance=bts)
        url = sc2.get_login_url("localhost", scope="login,vote")
        if PY2:
            self.assertEqual(url, 'https://v2.steemconnect.com/oauth2/authorize?client_id=None&scope=login,vote&redirect_uri=localhost')
        else:
            self.assertEqual(url, 'https://v2.steemconnect.com/oauth2/authorize?client_id=None&redirect_uri=localhost&scope=login,vote')
