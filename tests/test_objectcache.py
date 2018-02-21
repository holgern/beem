import time
import unittest
from beem import Steem, exceptions
from beem.instance import set_shared_steem_instance
from beem.blockchainobject import ObjectCache
nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://node.steem.ws", "wss://steemd.steemgigs.org", "wss://steemd.steemit.com",
         "wss://steemd.minnowsupportproject.org"]


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bts = Steem(
            nodes,
            nobroadcast=True,
        )
        set_shared_steem_instance(self.bts)

    def test_cache(self):
        cache = ObjectCache(default_expiration=1)
        self.assertEqual(str(cache), "ObjectCache(n=0, default_expiration=1)")

        # Data
        cache["foo"] = "bar"
        self.assertIn("foo", cache)
        self.assertEqual(cache["foo"], "bar")
        self.assertEqual(cache.get("foo", "New"), "bar")

        # Expiration
        time.sleep(2)
        self.assertNotIn("foo", cache)

        # Get
        self.assertEqual(cache.get("foo", "New"), "New")
