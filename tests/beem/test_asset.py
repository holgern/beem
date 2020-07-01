from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from builtins import super
import unittest
from parameterized import parameterized
from beem import Steem
from beem.asset import Asset
from beem.instance import set_shared_steem_instance
from beem.exceptions import AssetDoesNotExistsException
from beem.nodelist import NodeList


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodelist = NodeList()
        nodelist.update_nodes(steem_instance=Steem(node=nodelist.get_steem_nodes(), num_retries=10))
        cls.bts = Steem(
            node=nodelist.get_steem_nodes(),
            nobroadcast=True,
            num_retries=10
        )
        cls.steemit = Steem(
            node="https://api.steemit.com",
            nobroadcast=True,
            num_retries=10
        )
        set_shared_steem_instance(cls.bts)

    @parameterized.expand([
        ("normal"),
        ("steemit"),
    ])
    def test_assert(self, node_param):
        if node_param == "normal":
            stm = self.bts
        else:
            stm = self.steemit
        with self.assertRaises(AssetDoesNotExistsException):
            Asset("FOObarNonExisting", full=False, steem_instance=stm)

    @parameterized.expand([
        ("normal", "SBD", "SBD", 3, "@@000000013"),
        ("normal", "STEEM", "STEEM", 3, "@@000000021"),
        ("normal", "VESTS", "VESTS", 6, "@@000000037"),
        ("normal", "@@000000013", "SBD", 3, "@@000000013"),
        ("normal", "@@000000021", "STEEM", 3, "@@000000021"),
        ("normal", "@@000000037", "VESTS", 6, "@@000000037"),
    ])
    def test_properties(self, node_param, data, symbol_str, precision, asset_str):
        if node_param == "normal":
            stm = self.bts
        else:
            stm = self.testnet
        asset = Asset(data, full=False, steem_instance=stm)
        self.assertEqual(asset.symbol, symbol_str)
        self.assertEqual(asset.precision, precision)
        self.assertEqual(asset.asset, asset_str)

    @parameterized.expand([
        ("normal"),
        ("steemit"),
    ])
    def test_assert_equal(self, node_param):
        if node_param == "normal":
            stm = self.bts
        else:
            stm = self.steemit
        asset1 = Asset("SBD", full=False, steem_instance=stm)
        asset2 = Asset("SBD", full=False, steem_instance=stm)
        self.assertTrue(asset1 == asset2)
        self.assertTrue(asset1 == "SBD")
        self.assertTrue(asset2 == "SBD")
        asset3 = Asset("STEEM", full=False, steem_instance=stm)
        self.assertTrue(asset1 != asset3)
        self.assertTrue(asset3 != "SBD")
        self.assertTrue(asset1 != "STEEM")

        a = {'asset': '@@000000021', 'precision': 3, 'id': 'STEEM', 'symbol': 'STEEM'}
        b = {'asset': '@@000000021', 'precision': 3, 'id': '@@000000021', 'symbol': 'STEEM'}
        self.assertTrue(Asset(a, steem_instance=stm) == Asset(b, steem_instance=stm))

    """
    # Mocker comes from pytest-mock, providing an easy way to have patched objects
    # for the life of the test.
    def test_calls(mocker):
        asset = Asset("USD", lazy=True, steem_instance=Steem(offline=True))
        method = mocker.patch.object(Asset, 'get_call_orders')
        asset.calls
        method.assert_called_with(10)
    """
