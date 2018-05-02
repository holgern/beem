from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
from builtins import str
import time
import unittest
from beem import Steem, exceptions
from beem.instance import set_shared_steem_instance
from beem.blockchainobject import ObjectCache
from beem.account import Account
from beem.utils import get_node_list


class Testcases(unittest.TestCase):

    def test_cache(self):
        cache = ObjectCache(default_expiration=1, auto_clean=False)
        self.assertEqual(str(cache), "ObjectCache(n=0, default_expiration=1)")

        # Data
        cache["foo"] = "bar"
        self.assertIn("foo", cache)
        self.assertEqual(cache["foo"], "bar")
        self.assertEqual(cache.get("foo", "New"), "bar")

        # Expiration
        time.sleep(2)
        self.assertNotIn("foo", cache)
        self.assertEqual(str(cache), "ObjectCache(n=1, default_expiration=1)")

        # Get
        self.assertEqual(cache.get("foo", "New"), "New")

    def test_cache_autoclean(self):
        cache = ObjectCache(default_expiration=1, auto_clean=True)
        self.assertEqual(str(cache), "ObjectCache(n=0, default_expiration=1)")

        # Data
        cache["foo"] = "bar"
        self.assertEqual(str(cache), "ObjectCache(n=1, default_expiration=1)")
        self.assertIn("foo", cache)
        self.assertEqual(cache["foo"], "bar")
        self.assertEqual(cache.get("foo", "New"), "bar")

        # Expiration
        time.sleep(2)
        self.assertNotIn("foo", cache)
        self.assertEqual(str(cache), "ObjectCache(n=0, default_expiration=1)")

        # Get
        self.assertEqual(cache.get("foo", "New"), "New")
