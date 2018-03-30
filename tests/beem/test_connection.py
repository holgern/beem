import unittest
from beem import Steem
from beem.account import Account
from beem.instance import set_shared_steem_instance, SharedInstance
from beem.blockchainobject import BlockchainObject

import logging
log = logging.getLogger()
nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://node.steem.ws", "wss://steemd.steemgigs.org", "wss://steemd.steemit.com",
         "wss://steemd.minnowsupportproject.org"]


class Testcases(unittest.TestCase):

    def test_stm1stm2(self):
        b1 = Steem(
            node=["wss://testnet.steem.vc"],
            nobroadcast=True,
        )

        b2 = Steem(
            node=nodes,
            nobroadcast=True,
        )

        self.assertNotEqual(b1.rpc.url, b2.rpc.url)

    def test_default_connection(self):
        b1 = Steem(
            node=["wss://testnet.steem.vc"],
            nobroadcast=True,
        )
        set_shared_steem_instance(b1)
        test = Account("test")

        b2 = Steem(
            node=nodes,
            nobroadcast=True,
        )
        set_shared_steem_instance(b2)

        bts = Account("test")

        self.assertEqual(test.steem.prefix, "STX")
        self.assertEqual(bts.steem.prefix, "STM")
