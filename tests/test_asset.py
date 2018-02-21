import unittest
from steempy import Steem
from steempy.asset import Asset
from steempy.instance import set_shared_steem_instance
from steempy.exceptions import AssetDoesNotExistsException
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

    def test_assert(self):
        with self.assertRaises(AssetDoesNotExistsException):
            Asset("FOObarNonExisting", full=False)

    def test_properties(self):
        asset = Asset("sbd_symbol", full=False)
        self.assertIsInstance(asset.symbol, str)
        self.assertIsInstance(asset.precision, int)

    """
    # Mocker comes from pytest-mock, providing an easy way to have patched objects
    # for the life of the test.
    def test_calls(mocker):
        asset = Asset("USD", lazy=True, steem_instance=Steem(offline=True))
        method = mocker.patch.object(Asset, 'get_call_orders')
        asset.calls
        method.assert_called_with(10)
    """
