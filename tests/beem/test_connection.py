import unittest
from beem import Steem
from beem.account import Account
from beem.instance import set_shared_steem_instance, SharedInstance
from beem.blockchainobject import BlockchainObject
from beem.nodelist import NodeList

import logging
log = logging.getLogger()


class Testcases(unittest.TestCase):

    def test_stm1stm2(self):
        nodelist = NodeList()
        nodelist.update_nodes(steem_instance=Steem(node=nodelist.get_nodes(normal=True, appbase=True), num_retries=10))
        b1 = Steem(
            node=nodelist.get_testnet(testnet=False, testnetdev=True),
            nobroadcast=True,
            num_retries=10
        )

        b2 = Steem(
            node=nodelist.get_nodes(appbase=False),
            nobroadcast=True,
            num_retries=10
        )

        self.assertNotEqual(b1.rpc.url, b2.rpc.url)

    def test_default_connection(self):
        nodelist = NodeList()
        nodelist.update_nodes(steem_instance=Steem(node=nodelist.get_nodes(normal=True, appbase=True), num_retries=10))
        b1 = Steem(
            node=nodelist.get_testnet(testnet=False, testnetdev=True),
            nobroadcast=True,
        )
        set_shared_steem_instance(b1)
        test = Account("test")

        b2 = Steem(
            node=nodelist.get_nodes(appbase=False),
            nobroadcast=True,
        )
        set_shared_steem_instance(b2)

        bts = Account("test")

        self.assertEqual(test.steem.prefix, "TST")
        self.assertEqual(bts.steem.prefix, "STM")
