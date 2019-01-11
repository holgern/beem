from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from beem import Steem, exceptions
from beem.instance import set_shared_steem_instance
from beem.account import Account
from beem.nodelist import NodeList


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodelist = NodeList()
        cls.bts = Steem(
            node=nodelist.get_nodes(),
            nobroadcast=True,
            num_retries=10
        )
        set_shared_steem_instance(cls.bts)

    def test_get_nodes(self):
        nodelist = NodeList()
        all_nodes = nodelist.get_nodes(normal=True, appbase=True, dev=True, testnet=True, testnetdev=True)
        self.assertEqual(len(nodelist) - 13, len(all_nodes))
        https_nodes = nodelist.get_nodes(wss=False)
        self.assertEqual(https_nodes[0][:5], 'https')

    def test_nodes_update(self):
        nodelist = NodeList()
        all_nodes = nodelist.get_nodes(normal=True, appbase=True, dev=True, testnet=True)
        nodelist.update_nodes(steem_instance=self.bts)
        nodes = nodelist.get_nodes()
        self.assertIn(nodes[0], all_nodes)
