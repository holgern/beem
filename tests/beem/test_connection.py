import unittest
from beem import Steem
from beem.account import Account
from beem.instance import set_shared_steem_instance, SharedInstance
from beem.blockchainobject import BlockchainObject
from beem.utils import get_node_list, get_test_node_list

import logging
log = logging.getLogger()


class Testcases(unittest.TestCase):

    def test_stm1stm2(self):
        b1 = Steem(
            node=get_test_node_list(),
            nobroadcast=True,
            num_retries=10
        )

        b2 = Steem(
            node=get_node_list(appbase=False),
            nobroadcast=True,
            num_retries=10
        )

        self.assertNotEqual(b1.rpc.url, b2.rpc.url)

    def test_default_connection(self):
        b1 = Steem(
            node=get_test_node_list(),
            nobroadcast=True,
        )
        set_shared_steem_instance(b1)
        test = Account("test")

        b2 = Steem(
            node=get_node_list(appbase=False),
            nobroadcast=True,
        )
        set_shared_steem_instance(b2)

        bts = Account("test")

        self.assertEqual(test.steem.prefix, "STX")
        self.assertEqual(bts.steem.prefix, "STM")
