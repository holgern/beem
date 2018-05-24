# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import pytest
import unittest
from beemapi.node import Nodes
from beemapi.rpcutils import (
    is_network_appbase_ready,
    get_api_name, get_query, UnauthorizedError,
    RPCConnection, RPCError, NumRetriesReached
)


class Testcases(unittest.TestCase):
    def test_sleep_and_check_retries(self):
        nodes = Nodes("test", -1, 5)
        nodes.sleep_and_check_retries("error")
        nodes = Nodes("test", 1, 5)
        nodes.increase_error_cnt()
        nodes.increase_error_cnt()
        with self.assertRaises(
            NumRetriesReached
        ):
            nodes.sleep_and_check_retries()

    def test_next(self):
        nodes = Nodes(["a", "b", "c"], -1, -1)
        self.assertEqual(nodes.working_nodes_count, len(nodes))
        self.assertEqual(nodes.url, nodes[0].url)
        next(nodes)
        self.assertEqual(nodes.url, nodes[0].url)
        next(nodes)
        self.assertEqual(nodes.url, nodes[1].url)
        next(nodes)
        self.assertEqual(nodes.url, nodes[2].url)
        next(nodes)
        self.assertEqual(nodes.url, nodes[0].url)

        nodes = Nodes("a,b,c", 5, 5)
        self.assertEqual(nodes.working_nodes_count, len(nodes))
        self.assertEqual(nodes.url, nodes[0].url)
        next(nodes)
        self.assertEqual(nodes.url, nodes[0].url)
        next(nodes)
        self.assertEqual(nodes.url, nodes[1].url)
        next(nodes)
        self.assertEqual(nodes.url, nodes[2].url)
        next(nodes)
        self.assertEqual(nodes.url, nodes[0].url)

    def test_init(self):
        nodes = Nodes(["a", "b", "c"], 5, 5)
        nodes2 = Nodes(nodes, 5, 5)
        self.assertEqual(nodes.url, nodes2.url)
