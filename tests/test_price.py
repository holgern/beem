from beem import Steem
from beem.instance import set_shared_steem_instance
from beem.amount import Amount
from beem.price import Price
from beem.asset import Asset
import unittest
nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://node.steem.ws", "wss://steemd.steemgigs.org", "wss://steemd.steemit.com",
         "wss://steemd.minnowsupportproject.org"]


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(Testcases, self).__init__(*args, **kwargs)
        steem = Steem(
            nodes,
            nobroadcast=True,
        )
        set_shared_steem_instance(steem)

    def test_init(self):
        # self.assertEqual(1, 1)

        Price("0.315 STEEM/SBD")
        Price(1.0, "STEEM/SBD")
        Price(0.315, base="STEEM", quote="SBD")
        Price(0.315, base=Asset("STEEM"), quote=Asset("SBD"))
        Price({
            "base": {"amount": 1, "asset_id": "SBD"},
            "quote": {"amount": 10, "asset_id": "STEEM"}})
        Price(quote="10 SBD", base="1 STEEM")
        Price("10 SBD", "1 STEEM")
        Price(Amount("10 SBD"), Amount("1 STEEM"))

    def test_multiplication(self):
        p1 = Price(10.0, "STEEM/SBD")
        p2 = Price(5.0, "VESTS/STEEM")
        p3 = p1 * p2
        p4 = p3.as_base("SBD")

        self.assertEqual(p4["quote"]["symbol"], "VESTS")
        self.assertEqual(p4["base"]["symbol"], "SBD")
        # 10 STEEM/SBD * 0.2 VESTS/STEEM = 50 VESTS/SBD = 0.02 SBD/VESTS
        self.assertEqual(float(p4), 0.02)

        # Inline multiplication
        p5 = p1
        p5 *= p2
        p4 = p5.as_base("SBD")
        self.assertEqual(p4["quote"]["symbol"], "VESTS")
        self.assertEqual(p4["base"]["symbol"], "SBD")
        # 10 STEEM/SBD * 0.2 VESTS/STEEM = 2 VESTS/SBD = 0.02 SBD/VESTS
        self.assertEqual(float(p4), 0.02)

    def test_div(self):
        p1 = Price(10.0, "STEEM/SBD")
        p2 = Price(5.0, "STEEM/VESTS")

        # 10 STEEM/SBD / 5 STEEM/VESTS = 2 VESTS/SBD
        p3 = p1 / p2
        p4 = p3.as_base("VESTS")
        self.assertEqual(p4["base"]["symbol"], "VESTS")
        self.assertEqual(p4["quote"]["symbol"], "SBD")
        # 10 STEEM/SBD * 0.2 VESTS/STEEM = 2 VESTS/SBD = 0.5 SBD/VESTS
        self.assertEqual(float(p4), 2)

    def test_div2(self):
        p1 = Price(10.0, "STEEM/SBD")
        p2 = Price(5.0, "STEEM/SBD")

        # 10 STEEM/SBD / 5 STEEM/VESTS = 2 VESTS/SBD
        p3 = p1 / p2
        self.assertTrue(isinstance(p3, (float, int)))
        self.assertEqual(float(p3), 2.0)

    def test_ltge(self):
        p1 = Price(10.0, "STEEM/SBD")
        p2 = Price(5.0, "STEEM/SBD")

        self.assertTrue(p1 > p2)
        self.assertTrue(p2 < p1)

    def test_leeq(self):
        p1 = Price(10.0, "STEEM/SBD")
        p2 = Price(5.0, "STEEM/SBD")

        self.assertTrue(p1 >= p2)
        self.assertTrue(p2 <= p1)

    def test_ne(self):
        p1 = Price(10.0, "STEEM/SBD")
        p2 = Price(5.0, "STEEM/SBD")

        self.assertTrue(p1 != p2)
        self.assertTrue(p1 == p1)
