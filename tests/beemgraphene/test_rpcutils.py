# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import pytest
import unittest
from beemgrapheneapi.rpcutils import (
    is_network_appbase_ready, sleep_and_check_retries,
    get_api_name, get_query, UnauthorizedError,
    RPCConnection, RPCError, NumRetriesReached
)


class Testcases(unittest.TestCase):
    def test_is_network_appbase_ready(self):
        self.assertTrue(is_network_appbase_ready({'STEEM_BLOCKCHAIN_VERSION': '0.19.4'}))
        self.assertTrue(is_network_appbase_ready({'STEEMIT_BLOCKCHAIN_VERSION': '0.19.4'}))
        self.assertFalse(is_network_appbase_ready({'STEEM_BLOCKCHAIN_VERSION': '0.19.2'}))
        self.assertFalse(is_network_appbase_ready({'STEEM_BLOCKCHAIN_VERSION': '0.19.2'}))

    def test_get_api_name(self):
        self.assertEqual(get_api_name(True, api="test"), "test_api")
        self.assertEqual(get_api_name(True, api="test_api"), "test_api")
        self.assertEqual(get_api_name(True, api="jsonrpc"), "jsonrpc")

        self.assertEqual(get_api_name(True), "condenser_api")
        self.assertEqual(get_api_name(False, api="test"), "test_api")
        self.assertEqual(get_api_name(False, api="test_api"), "test_api")
        self.assertTrue(get_api_name(False, api="") is None)
        self.assertTrue(get_api_name(False) is None)

    def test_get_query(self):
        query = get_query(True, 1, "test_api", "test", args="")
        self.assertEqual(query["method"], 'test_api.test')
        self.assertEqual(query["jsonrpc"], '2.0')
        self.assertEqual(query["id"], 1)
        self.assertTrue(isinstance(query["params"], dict))

        args = [{"a": "b"}]
        query = get_query(True, 1, "test_api", "test", args=args)
        self.assertEqual(query["method"], 'test_api.test')
        self.assertEqual(query["jsonrpc"], '2.0')
        self.assertEqual(query["id"], 1)
        self.assertTrue(isinstance(query["params"], dict))
        self.assertEqual(query["params"], args[0])

        args = ["b"]
        query = get_query(True, 1, "test_api", "test", args=args)
        self.assertEqual(query["method"], 'call')
        self.assertEqual(query["jsonrpc"], '2.0')
        self.assertEqual(query["id"], 1)
        self.assertTrue(isinstance(query["params"], list))
        self.assertEqual(query["params"], ["test_api", "test", args])

        query = get_query(True, 1, "condenser_api", "test", args="")
        self.assertEqual(query["method"], 'condenser_api.test')
        self.assertEqual(query["jsonrpc"], '2.0')
        self.assertEqual(query["id"], 1)
        self.assertTrue(isinstance(query["params"], list))

        args = ["b"]
        query = get_query(False, 1, "test_api", "test", args=args)
        self.assertEqual(query["method"], 'call')
        self.assertEqual(query["jsonrpc"], '2.0')
        self.assertEqual(query["id"], 1)
        self.assertTrue(isinstance(query["params"], list))
        self.assertEqual(query["params"], ["test_api", "test", args])

    def test_sleep_and_check_retries(self):
        sleep_and_check_retries(-1, 0, "test")
        sleep_and_check_retries(-1, -1, "test")
        with self.assertRaises(
            NumRetriesReached
        ):
            sleep_and_check_retries(1, 2, "test")
