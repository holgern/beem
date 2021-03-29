# -*- coding: utf-8 -*-
import time
import unittest
from beem import Steem, exceptions
from beem.instance import set_shared_steem_instance
from beem.blockchainobject import ObjectCache


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
        self.assertEqual(len(list(cache)), 0)

        # Get
        self.assertEqual(cache.get("foo", "New"), "New")

    def test_cache2(self):
        cache = ObjectCache(default_expiration=3, auto_clean=True)
        self.assertEqual(str(cache), "ObjectCache(n=0, default_expiration=3)")

        # Data
        cache["foo"] = "bar"
        self.assertEqual(str(cache), "ObjectCache(n=1, default_expiration=3)")
        self.assertIn("foo", cache)
        self.assertEqual(cache["foo"], "bar")
        self.assertEqual(cache.get("foo", "New"), "bar")
        time.sleep(1)
        cache["foo2"] = "bar2"
        time.sleep(1)
        cache["foo3"] = "bar3"
        self.assertEqual(str(cache), "ObjectCache(n=3, default_expiration=3)")
        # Expiration
        time.sleep(2)
        self.assertNotIn("foo", cache)
        self.assertEqual(str(cache), "ObjectCache(n=1, default_expiration=3)")
        self.assertEqual(len(list(cache)), 1)
        # Get
        self.assertEqual(cache.get("foo", "New"), "New")
