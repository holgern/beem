from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from pprint import pprint
from beem import Steem
from beem.market import Market
from beem.price import Price
from beem.amount import Amount
from beembase.operationids import getOperationNameForId
from beem.instance import set_shared_steem_instance

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://node.steem.ws", "wss://steemd.steemgigs.org", "wss://steemd.steemit.com",
         "wss://steemd.minnowsupportproject.org"]


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bts = Steem(
            node=nodes,
            nobroadcast=True,
            keys={"active": wif},
        )
        # from getpass import getpass
        # self.bts.wallet.unlock(getpass())
        set_shared_steem_instance(self.bts)
        self.bts.set_default_account("test")

    def test_market(self):
        bts = self.bts
        m = Market(steem_instance=bts)
        self.assertEqual(m.get_string(), u'STEEM:SBD')

    def test_ticker(self):
        bts = self.bts
        m = Market(steem_instance=bts)
        ticker = m.ticker()
        self.assertEqual(len(ticker), 6)
        self.assertEqual(ticker['steemVolume']["symbol"], u'STEEM')
        self.assertEqual(ticker['sbdVolume']["symbol"], u'SBD')

    def test_volume(self):
        bts = self.bts
        m = Market(steem_instance=bts)
        volume = m.volume24h()
        self.assertEqual(volume['STEEM']["symbol"], u'STEEM')
        self.assertEqual(volume['SBD']["symbol"], u'SBD')

    def test_orderbook(self):
        bts = self.bts
        m = Market(steem_instance=bts)
        orderbook = m.orderbook(limit=10)
        self.assertEqual(len(orderbook['asks_date']), 10)
        self.assertEqual(len(orderbook['asks']), 10)
        self.assertEqual(len(orderbook['bids_date']), 10)
        self.assertEqual(len(orderbook['bids']), 10)

    def test_recenttrades(self):
        bts = self.bts
        m = Market(steem_instance=bts)
        recenttrades = m.recent_trades(limit=10)
        self.assertEqual(len(recenttrades['date']), 10)
        self.assertEqual(len(recenttrades['order']), 10)

    def test_trades(self):
        bts = self.bts
        m = Market(steem_instance=bts)
        trades = m.trades(limit=10)
        self.assertEqual(len(trades['date']), 10)
        self.assertEqual(len(trades['order']), 10)

    def test_market_history(self):
        bts = self.bts
        m = Market(steem_instance=bts)
        buckets = m.market_history_buckets()
        history = m.market_history(buckets[2])
        self.assertTrue(len(history) > 0)

    def test_accountopenorders(self):
        bts = self.bts
        m = Market(steem_instance=bts)
        openOrder = m.accountopenorders("test")
        self.assertTrue(isinstance(openOrder, list))

    def test_buy(self):
        bts = self.bts
        m = Market(steem_instance=bts)
        tx = m.buy(5, 0.1, account="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "limit_order_create"
        )
        op = tx["operations"][0][1]
        self.assertIn("test", op["owner"])
        self.assertEqual(u'0.100 STEEM', op["min_to_receive"])
        self.assertEqual(u'0.500 SBD', op["amount_to_sell"])

        p = Price(5, u"SBD:STEEM")
        tx = m.buy(p, 0.1, account="test")
        op = tx["operations"][0][1]
        self.assertEqual(u'0.100 STEEM', op["min_to_receive"])
        self.assertEqual(u'0.500 SBD', op["amount_to_sell"])

        p = Price(5, u"SBD:STEEM")
        a = Amount(0.1, "STEEM")
        tx = m.buy(p, a, account="test")
        op = tx["operations"][0][1]
        self.assertEqual(u'0.100 STEEM', op["min_to_receive"])
        self.assertEqual(u'0.500 SBD', op["amount_to_sell"])

    def test_sell(self):
        bts = self.bts
        m = Market(steem_instance=bts)
        tx = m.sell(5, 0.1, account="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "limit_order_create"
        )
        op = tx["operations"][0][1]
        self.assertIn("test", op["owner"])
        self.assertEqual(u'0.500 SBD', op["min_to_receive"])
        self.assertEqual(u'0.100 STEEM', op["amount_to_sell"])

        p = Price(5, u"SBD:STEEM")
        tx = m.sell(p, 0.1, account="test")
        op = tx["operations"][0][1]
        self.assertEqual(u'0.500 SBD', op["min_to_receive"])
        self.assertEqual(u'0.100 STEEM', op["amount_to_sell"])

        p = Price(5, u"SBD:STEEM")
        a = Amount(0.1, "STEEM")
        tx = m.sell(p, a, account="test")
        op = tx["operations"][0][1]
        self.assertEqual(u'0.500 SBD', op["min_to_receive"])
        self.assertEqual(u'0.100 STEEM', op["amount_to_sell"])

    def test_cancel(self):
        bts = self.bts
        m = Market(steem_instance=bts)
        tx = m.cancel(5, account="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "limit_order_cancel"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["owner"])
