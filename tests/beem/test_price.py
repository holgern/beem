# -*- coding: utf-8 -*-
from beem import Steem
from beem.instance import set_shared_steem_instance
from beem.amount import Amount
from beem.price import Price, Order, FilledOrder
from beem.asset import Asset
import unittest
from .nodes import get_hive_nodes, get_steem_nodes


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        steem = Steem(
            node=get_hive_nodes(),
            nobroadcast=True,
            num_retries=10
        )
        set_shared_steem_instance(steem)

    def test_init(self):
        # self.assertEqual(1, 1)

        Price("0.315 HIVE/HBD")
        Price(1.0, "HIVE/HBD")
        Price(0.315, base="HIVE", quote="HBD")
        Price(0.315, base=Asset("HIVE"), quote=Asset("HBD"))
        Price({
            "base": {"amount": 1, "asset_id": "HBD"},
            "quote": {"amount": 10, "asset_id": "HIVE"}})
        Price("", quote="10 HBD", base="1 HIVE")
        Price("10 HBD", "1 HIVE")
        Price(Amount("10 HBD"), Amount("1 HIVE"))

    def test_multiplication(self):
        p1 = Price(10.0, "HIVE/HBD")
        p2 = Price(5.0, "VESTS/HIVE")
        p3 = p1 * p2
        p4 = p3.as_base("HBD")
        p4_2 = p3.as_quote("VESTS")

        self.assertEqual(p4["quote"]["symbol"], "VESTS")
        self.assertEqual(p4["base"]["symbol"], "HBD")
        # 10 HIVE/HBD * 0.2 VESTS/HIVE = 50 VESTS/HBD = 0.02 HBD/VESTS
        self.assertEqual(float(p4), 0.02)
        self.assertEqual(p4_2["quote"]["symbol"], "VESTS")
        self.assertEqual(p4_2["base"]["symbol"], "HBD")
        self.assertEqual(float(p4_2), 0.02)
        p3 = p1 * 5
        self.assertEqual(float(p3), 50)

        # Inline multiplication
        p5 = Price(10.0, "HIVE/HBD")
        p5 *= p2
        p4 = p5.as_base("HBD")
        self.assertEqual(p4["quote"]["symbol"], "VESTS")
        self.assertEqual(p4["base"]["symbol"], "HBD")
        # 10 HIVE/HBD * 0.2 VESTS/HIVE = 2 VESTS/HBD = 0.02 HBD/VESTS
        self.assertEqual(float(p4), 0.02)
        p6 = Price(10.0, "HIVE/HBD")
        p6 *= 5
        self.assertEqual(float(p6), 50)

    def test_div(self):
        p1 = Price(10.0, "HIVE/HBD")
        p2 = Price(5.0, "HIVE/VESTS")

        # 10 HIVE/HBD / 5 HIVE/VESTS = 2 VESTS/HBD
        p3 = p1 / p2
        p4 = p3.as_base("VESTS")
        self.assertEqual(p4["base"]["symbol"], "VESTS")
        self.assertEqual(p4["quote"]["symbol"], "HBD")
        # 10 HIVE/HBD * 0.2 VESTS/HIVE = 2 VESTS/HBD = 0.5 HBD/VESTS
        self.assertEqual(float(p4), 2)

    def test_div2(self):
        p1 = Price(10.0, "HIVE/HBD")
        p2 = Price(5.0, "HIVE/HBD")

        # 10 HIVE/HBD / 5 HIVE/VESTS = 2 VESTS/HBD
        p3 = p1 / p2
        self.assertTrue(isinstance(p3, (float, int)))
        self.assertEqual(float(p3), 2.0)
        p3 = p1 / 5
        self.assertEqual(float(p3), 2.0)
        p3 = p1 / Amount("1 HBD")
        self.assertEqual(float(p3), 0.1)
        p3 = p1
        p3 /= p2
        self.assertEqual(float(p3), 2.0)
        p3 = p1
        p3 /= 5
        self.assertEqual(float(p3), 2.0)

    def test_ltge(self):
        p1 = Price(10.0, "HIVE/HBD")
        p2 = Price(5.0, "HIVE/HBD")

        self.assertTrue(p1 > p2)
        self.assertTrue(p2 < p1)
        self.assertTrue(p1 > 5)
        self.assertTrue(p2 < 10)

    def test_leeq(self):
        p1 = Price(10.0, "HIVE/HBD")
        p2 = Price(5.0, "HIVE/HBD")

        self.assertTrue(p1 >= p2)
        self.assertTrue(p2 <= p1)
        self.assertTrue(p1 >= 5)
        self.assertTrue(p2 <= 10)

    def test_ne(self):
        p1 = Price(10.0, "HIVE/HBD")
        p2 = Price(5.0, "HIVE/HBD")

        self.assertTrue(p1 != p2)
        self.assertTrue(p1 == p1)
        self.assertTrue(p1 != 5)
        self.assertTrue(p1 == 10)

    def test_order(self):
        order = Order(Amount("2 HBD"), Amount("1 HIVE"))
        self.assertTrue(repr(order) is not None)

    def test_filled_order(self):
        order = {"date": "1900-01-01T00:00:00", "current_pays": "2 HBD", "open_pays": "1 HIVE"}
        filledOrder = FilledOrder(order)
        self.assertTrue(repr(filledOrder) is not None)
        self.assertEqual(filledOrder.json()["current_pays"], Amount("2.000 HBD").json())
