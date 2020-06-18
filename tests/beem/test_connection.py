import unittest
from beem import Hive, Steem
from beem.account import Account
from beem.instance import set_shared_steem_instance, SharedInstance
from beem.blockchainobject import BlockchainObject
from beem.nodelist import NodeList

import logging
log = logging.getLogger()


class Testcases(unittest.TestCase):

    def test_stm1stm2(self):
        nodelist = NodeList()
        nodelist.update_nodes(steem_instance=Hive(node=nodelist.get_hive_nodes(), num_retries=10))
        b1 = Steem(
            node="https://api.steemit.com",
            nobroadcast=True,
            num_retries=10
        )
        node_list = nodelist.get_hive_nodes()

        b2 = Hive(
            node=node_list,
            nobroadcast=True,
            num_retries=10
        )

        self.assertNotEqual(b1.rpc.url, b2.rpc.url)

    def test_default_connection(self):
        nodelist = NodeList()
        nodelist.update_nodes(steem_instance=Hive(node=nodelist.get_hive_nodes(), num_retries=10))

        b2 = Hive(
            node=nodelist.get_hive_nodes(),
            nobroadcast=True,
        )
        set_shared_steem_instance(b2)
        bts = Account("beem")
        self.assertEqual(bts.blockchain.prefix, "STM")
