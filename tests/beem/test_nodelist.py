# -*- coding: utf-8 -*-
import unittest
from beem import Steem, exceptions, Hive
from beem.instance import set_shared_blockchain_instance
from beem.account import Account
from beem.nodelist import NodeList


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodelist = NodeList()
        cls.bts = Hive(
            node=nodelist.get_hive_nodes(),
            nobroadcast=True,
            num_retries=10
        )
        set_shared_blockchain_instance(cls.bts)

    def test_get_nodes(self):
        nodelist = NodeList()
        all_nodes = nodelist.get_nodes(exclude_limited=False, dev=True, testnet=True, testnetdev=True)
        self.assertEqual(len(nodelist) - 16, len(all_nodes))
        https_nodes = nodelist.get_nodes(wss=False)
        self.assertEqual(https_nodes[0][:5], 'https')

    def test_hive_nodes(self):
        nodelist = NodeList()
        nodelist.update_nodes()
        hive_nodes = nodelist.get_hive_nodes()
        for node in hive_nodes:
            blockchainobject = Hive(node=node)
            assert blockchainobject.is_hive

    def test_steem_nodes(self):
        nodelist = NodeList()
        nodelist.update_nodes()
        steem_nodes = nodelist.get_steem_nodes()
        for node in steem_nodes:
            blockchainobject = Steem(node=node)
            assert blockchainobject.is_steem

    def test_nodes_update(self):
        nodelist = NodeList()
        all_nodes = nodelist.get_hive_nodes()
        nodelist.update_nodes(blockchain_instance=self.bts)
        nodes = nodelist.get_hive_nodes()
        self.assertIn(nodes[0], all_nodes)

        all_nodes = nodelist.get_steem_nodes()
        nodelist.update_nodes(blockchain_instance=self.bts)
        nodes = nodelist.get_steem_nodes()
        self.assertIn(nodes[0], all_nodes)        
