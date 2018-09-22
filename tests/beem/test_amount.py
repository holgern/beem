from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from parameterized import parameterized
from beem import Steem
from beem.amount import Amount
from beem.asset import Asset
from beem.nodelist import NodeList
from beem.instance import set_shared_steem_instance, SharedInstance


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodelist = NodeList()
        nodelist.update_nodes(steem_instance=Steem(node=nodelist.get_nodes(normal=True, appbase=True), num_retries=10))
        cls.bts = Steem(
            node=nodelist.get_nodes(appbase=False),
            nobroadcast=True,
            num_retries=10
        )
        cls.testnet = Steem(
            node="https://testnet.steemitdev.com",
            nobroadcast=True,
            use_condenser=False,
            num_retries=10
        )
        set_shared_steem_instance(cls.bts)
        cls.asset = Asset("SBD")
        cls.symbol = cls.asset["symbol"]
        cls.precision = cls.asset["precision"]
        cls.asset2 = Asset("STEEM")

    def dotest(self, ret, amount, symbol):
        self.assertEqual(float(ret), float(amount))
        self.assertEqual(ret["symbol"], symbol)
        self.assertIsInstance(ret["asset"], dict)
        self.assertIsInstance(ret["amount"], float)

    def test_init(self):
        stm = self.bts
        # String init
        asset = Asset("SBD", steem_instance=stm)
        symbol = asset["symbol"]
        precision = asset["precision"]
        amount = Amount("1 {}".format(symbol), steem_instance=stm)
        self.dotest(amount, 1, symbol)

        # Amount init
        amount = Amount(amount, steem_instance=stm)
        self.dotest(amount, 1, symbol)

        # blockchain dict init
        amount = Amount({
            "amount": 1 * 10 ** precision,
            "asset_id": asset["id"]
        }, steem_instance=stm)
        self.dotest(amount, 1, symbol)

        # API dict init
        amount = Amount({
            "amount": 1.3 * 10 ** precision,
            "asset": asset["id"]
        }, steem_instance=stm)
        self.dotest(amount, 1.3, symbol)

        # Asset as symbol
        amount = Amount(1.3, Asset("SBD"), steem_instance=stm)
        self.dotest(amount, 1.3, symbol)

        # Asset as symbol
        amount = Amount(1.3, symbol, steem_instance=stm)
        self.dotest(amount, 1.3, symbol)

        # keyword inits
        amount = Amount(amount=1.3, asset=Asset("SBD", steem_instance=stm), steem_instance=stm)
        self.dotest(amount, 1.3, symbol)

        # keyword inits
        amount = Amount(amount=1.3, asset=dict(Asset("SBD", steem_instance=stm)), steem_instance=stm)
        self.dotest(amount, 1.3, symbol)

        # keyword inits
        amount = Amount(amount=1.3, asset=symbol, steem_instance=stm)
        self.dotest(amount, 1.3, symbol)

    def test_copy(self):
        amount = Amount("1", self.symbol)
        self.dotest(amount.copy(), 1, self.symbol)

    def test_properties(self):
        amount = Amount("1", self.symbol)
        self.assertEqual(amount.amount, 1.0)
        self.assertEqual(amount.symbol, self.symbol)
        self.assertIsInstance(amount.asset, Asset)
        self.assertEqual(amount.asset["symbol"], self.symbol)

    def test_tuple(self):
        amount = Amount("1", self.symbol)
        self.assertEqual(
            amount.tuple(),
            (1.0, self.symbol))

    def test_json_appbase(self):
        asset = Asset("SBD", steem_instance=self.bts)
        amount = Amount("1", asset, new_appbase_format=False, steem_instance=self.bts)
        if self.bts.rpc.get_use_appbase():
            self.assertEqual(
                amount.json(),
                [str(1 * 10 ** asset.precision), asset.precision, asset.asset])
        else:
            self.assertEqual(amount.json(), "1.000 SBD")

    def test_json_appbase2(self):
        asset = Asset("SBD", steem_instance=self.bts)
        amount = Amount("1", asset, new_appbase_format=True, steem_instance=self.bts)
        if self.bts.rpc.get_use_appbase():
            self.assertEqual(
                amount.json(),
                {'amount': str(1 * 10 ** asset.precision), 'nai': asset.asset, 'precision': asset.precision})
        else:
            self.assertEqual(amount.json(), "1.000 SBD")

    def test_string(self):
        self.assertEqual(
            str(Amount("10000", self.symbol)),
            "10000.000 {}".format(self.symbol))

    def test_int(self):
        self.assertEqual(
            int(Amount("1", self.symbol)),
            1000)

    def test_float(self):
        self.assertEqual(
            float(Amount("1", self.symbol)),
            1.00000)

    def test_plus(self):
        a1 = Amount(1, self.symbol)
        a2 = Amount(2, self.symbol)
        self.dotest(a1 + a2, 3, self.symbol)
        self.dotest(a1 + 2, 3, self.symbol)
        with self.assertRaises(Exception):
            a1 + Amount(1, asset=self.asset2)
        # inline
        a2 = Amount(2, self.symbol)
        a2 += a1
        self.dotest(a2, 3, self.symbol)
        a2 += 5
        self.dotest(a2, 8, self.symbol)
        with self.assertRaises(Exception):
            a1 += Amount(1, asset=self.asset2)

    def test_minus(self):
        a1 = Amount(1, self.symbol)
        a2 = Amount(2, self.symbol)
        self.dotest(a1 - a2, -1, self.symbol)
        self.dotest(a1 - 5, -4, self.symbol)
        with self.assertRaises(Exception):
            a1 - Amount(1, asset=self.asset2)
        # inline
        a2 = Amount(2, self.symbol)
        a2 -= a1
        self.dotest(a2, 1, self.symbol)
        a2 -= 1
        self.dotest(a2, 0, self.symbol)
        self.dotest(a2 - 2, -2, self.symbol)
        with self.assertRaises(Exception):
            a1 -= Amount(1, asset=self.asset2)

    def test_mul(self):
        a1 = Amount(5, self.symbol)
        a2 = Amount(2, self.symbol)
        self.dotest(a1 * a2, 10, self.symbol)
        self.dotest(a1 * 3, 15, self.symbol)
        with self.assertRaises(Exception):
            a1 * Amount(1, asset=self.asset2)
        # inline
        a2 = Amount(2, self.symbol)
        a2 *= 5
        self.dotest(a2, 10, self.symbol)
        a2 = Amount(2, self.symbol)
        a2 *= a1
        self.dotest(a2, 10, self.symbol)
        with self.assertRaises(Exception):
            a1 *= Amount(2, asset=self.asset2)

    def test_div(self):
        a1 = Amount(15, self.symbol)
        self.dotest(a1 / 3, 5, self.symbol)
        self.dotest(a1 // 2, 7, self.symbol)
        with self.assertRaises(Exception):
            a1 / Amount(1, asset=self.asset2)
        # inline
        a2 = a1.copy()
        a2 /= 3
        self.dotest(a2, 5, self.symbol)
        a2 = a1.copy()
        a2 //= 2
        self.dotest(a2, 7, self.symbol)
        with self.assertRaises(Exception):
            a1 *= Amount(2, asset=self.asset2)

    def test_mod(self):
        a1 = Amount(15, self.symbol)
        a2 = Amount(3, self.symbol)
        self.dotest(a1 % 3, 0, self.symbol)
        self.dotest(a1 % a2, 0, self.symbol)
        self.dotest(a1 % 2, 1, self.symbol)
        with self.assertRaises(Exception):
            a1 % Amount(1, asset=self.asset2)
        # inline
        a2 = a1.copy()
        a2 %= 3
        self.dotest(a2, 0, self.symbol)
        with self.assertRaises(Exception):
            a1 %= Amount(2, asset=self.asset2)

    def test_pow(self):
        a1 = Amount(15, self.symbol)
        a2 = Amount(3, self.symbol)
        self.dotest(a1 ** 3, 15 ** 3, self.symbol)
        self.dotest(a1 ** a2, 15 ** 3, self.symbol)
        self.dotest(a1 ** 2, 15 ** 2, self.symbol)
        with self.assertRaises(Exception):
            a1 ** Amount(1, asset=self.asset2)
        # inline
        a2 = a1.copy()
        a2 **= 3
        self.dotest(a2, 15 ** 3, self.symbol)
        with self.assertRaises(Exception):
            a1 **= Amount(2, asset=self.asset2)

    def test_ltge(self):
        a1 = Amount(1, self.symbol)
        a2 = Amount(2, self.symbol)
        self.assertTrue(a1 < a2)
        self.assertTrue(a2 > a1)
        self.assertTrue(a2 > 1)
        self.assertTrue(a1 < 5)

    def test_leeq(self):
        a1 = Amount(1, self.symbol)
        a2 = Amount(1, self.symbol)
        self.assertTrue(a1 <= a2)
        self.assertTrue(a1 >= a2)
        self.assertTrue(a1 <= 1)
        self.assertTrue(a1 >= 1)

    def test_ne(self):
        a1 = Amount(1, self.symbol)
        a2 = Amount(2, self.symbol)
        self.assertTrue(a1 != a2)
        self.assertTrue(a1 != 5)
        a1 = Amount(1, self.symbol)
        a2 = Amount(1, self.symbol)
        self.assertTrue(a1 == a2)
        self.assertTrue(a1 == 1)
