from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from parameterized import parameterized
from pprint import pprint
from beem import Steem
from beem.market import Market
from beem.price import Price
from beem.asset import Asset
from beem.amount import Amount
from beem.instance import set_shared_steem_instance
from beem.nodelist import NodeList

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"


class Testcases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        nodelist = NodeList()
        cls.bts = Steem(
            node=nodelist.get_nodes(appbase=False),
            nobroadcast=True,
            unsigned=True,
            keys={"active": wif},
            num_retries=10
        )
        cls.appbase = Steem(
            node=nodelist.get_nodes(normal=False, appbase=True),
            nobroadcast=True,
            unsigned=True,
            keys={"active": wif},
            num_retries=10
        )
        # from getpass import getpass
        # self.bts.wallet.unlock(getpass())
        set_shared_steem_instance(cls.bts)
        cls.bts.set_default_account("test")

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_market(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        m1 = Market(u'STEEM', u'SBD', steem_instance=bts)
        self.assertEqual(m1.get_string(), u'SBD:STEEM')
        m2 = Market(steem_instance=bts)
        self.assertEqual(m2.get_string(), u'SBD:STEEM')
        m3 = Market(u'STEEM:SBD', steem_instance=bts)
        self.assertEqual(m3.get_string(), u'STEEM:SBD')
        self.assertTrue(m1 == m2)

        base = Asset("SBD", steem_instance=bts)
        quote = Asset("STEEM", steem_instance=bts)
        m = Market(base, quote, steem_instance=bts)
        self.assertEqual(m.get_string(), u'STEEM:SBD')

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_ticker(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        m = Market(u'STEEM:SBD', steem_instance=bts)
        ticker = m.ticker()
        self.assertEqual(len(ticker), 6)
        self.assertEqual(ticker['steem_volume']["symbol"], u'STEEM')
        self.assertEqual(ticker['sbd_volume']["symbol"], u'SBD')

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_volume(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        m = Market(u'STEEM:SBD', steem_instance=bts)
        volume = m.volume24h()
        self.assertEqual(volume['STEEM']["symbol"], u'STEEM')
        self.assertEqual(volume['SBD']["symbol"], u'SBD')

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_orderbook(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        m = Market(u'STEEM:SBD', steem_instance=bts)
        orderbook = m.orderbook(limit=10)
        self.assertEqual(len(orderbook['asks_date']), 10)
        self.assertEqual(len(orderbook['asks']), 10)
        self.assertEqual(len(orderbook['bids_date']), 10)
        self.assertEqual(len(orderbook['bids']), 10)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_recenttrades(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        m = Market(u'STEEM:SBD', steem_instance=bts)
        recenttrades = m.recent_trades(limit=10)
        recenttrades_raw = m.recent_trades(limit=10, raw_data=True)
        self.assertEqual(len(recenttrades), 10)
        self.assertEqual(len(recenttrades_raw), 10)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_trades(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        m = Market(u'STEEM:SBD', steem_instance=bts)
        trades = m.trades(limit=10)
        trades_raw = m.trades(limit=10, raw_data=True)
        trades_history = m.trade_history(limit=10)
        self.assertEqual(len(trades), 10)
        self.assertTrue(len(trades_history) > 0)
        self.assertEqual(len(trades_raw), 10)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_market_history(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        m = Market(u'STEEM:SBD', steem_instance=bts)
        buckets = m.market_history_buckets()
        history = m.market_history(buckets[2])
        self.assertTrue(len(history) > 0)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_accountopenorders(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        m = Market(u'STEEM:SBD', steem_instance=bts)
        openOrder = m.accountopenorders("test")
        self.assertTrue(isinstance(openOrder, list))

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_buy(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        m = Market(u'STEEM:SBD', steem_instance=bts)
        bts.txbuffer.clear()
        tx = m.buy(5, 0.1, account="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "limit_order_create"
        )
        op = tx["operations"][0][1]
        self.assertIn("test", op["owner"])
        self.assertEqual(Amount('0.100 STEEM', steem_instance=bts).json(), op["min_to_receive"])
        self.assertEqual(Amount('0.500 SBD', steem_instance=bts).json(), op["amount_to_sell"])

        p = Price(5, u"SBD:STEEM", steem_instance=bts)
        tx = m.buy(p, 0.1, account="test")
        op = tx["operations"][0][1]
        self.assertEqual(Amount('0.100 STEEM', steem_instance=bts).json(), op["min_to_receive"])
        self.assertEqual(Amount('0.500 SBD', steem_instance=bts).json(), op["amount_to_sell"])

        p = Price(5, u"SBD:STEEM", steem_instance=bts)
        a = Amount(0.1, "STEEM", steem_instance=bts)
        tx = m.buy(p, a, account="test")
        op = tx["operations"][0][1]
        self.assertEqual(a.json(), op["min_to_receive"])
        self.assertEqual(Amount('0.500 SBD', steem_instance=bts).json(), op["amount_to_sell"])

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_sell(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        bts.txbuffer.clear()
        m = Market(u'STEEM:SBD', steem_instance=bts)
        tx = m.sell(5, 0.1, account="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "limit_order_create"
        )
        op = tx["operations"][0][1]
        self.assertIn("test", op["owner"])
        self.assertEqual(Amount('0.500 SBD', steem_instance=bts).json(), op["min_to_receive"])
        self.assertEqual(Amount('0.100 STEEM', steem_instance=bts).json(), op["amount_to_sell"])

        p = Price(5, u"SBD:STEEM")
        tx = m.sell(p, 0.1, account="test")
        op = tx["operations"][0][1]
        self.assertEqual(Amount('0.500 SBD', steem_instance=bts).json(), op["min_to_receive"])
        self.assertEqual(Amount('0.100 STEEM', steem_instance=bts).json(), op["amount_to_sell"])

        p = Price(5, u"SBD:STEEM", steem_instance=bts)
        a = Amount(0.1, "STEEM", steem_instance=bts)
        tx = m.sell(p, a, account="test")
        op = tx["operations"][0][1]
        self.assertEqual(Amount('0.500 SBD', steem_instance=bts).json(), op["min_to_receive"])
        self.assertEqual(Amount('0.100 STEEM', steem_instance=bts).json(), op["amount_to_sell"])

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_cancel(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        bts.txbuffer.clear()
        m = Market(u'STEEM:SBD', steem_instance=bts)
        tx = m.cancel(5, account="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "limit_order_cancel"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["owner"])
