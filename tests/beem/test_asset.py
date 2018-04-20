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
from beem.utils import get_node_list


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bts = Steem(
            node=get_node_list(appbase=False),
            nobroadcast=True,
            num_retries=10
        )
        cls.appbase = Steem(
            node=get_node_list(appbase=True),
            nobroadcast=True,
            num_retries=10
        )
        set_shared_steem_instance(cls.bts)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_assert(self, node_param):
        if node_param == "non_appbase":
            stm = self.bts
        else:
            stm = self.appbase
        with self.assertRaises(AssetDoesNotExistsException):
            Asset("FOObarNonExisting", full=False, steem_instance=stm)

    @parameterized.expand([
        ("non_appbase", "SBD", "SBD", 3, "SBD"),
        ("non_appbase", "STEEM", "STEEM", 3, "STEEM"),
        ("non_appbase", "VESTS", "VESTS", 6, "VESTS"),
        ("appbase", "SBD", "SBD", 3, "@@000000013"),
        ("appbase", "STEEM", "STEEM", 3, "@@000000021"),
        ("appbase", "VESTS", "VESTS", 6, "@@000000037"),
        ("appbase", "@@000000013", "SBD", 3, "@@000000013"),
        ("appbase", "@@000000021", "STEEM", 3, "@@000000021"),
        ("appbase", "@@000000037", "VESTS", 6, "@@000000037"),
    ])
    def test_properties(self, node_param, data, symbol_str, precision, asset_str):
        if node_param == "non_appbase":
            stm = self.bts
        else:
            stm = self.appbase
        asset = Asset(data, full=False, steem_instance=stm)
        self.assertEqual(asset.symbol, symbol_str)
        self.assertEqual(asset.precision, precision)
        self.assertEqual(asset.asset, asset_str)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_assert_equal(self, node_param):
        if node_param == "non_appbase":
            stm = self.bts
        else:
            stm = self.appbase
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
