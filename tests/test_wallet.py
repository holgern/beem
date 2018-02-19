import unittest
import mock
from pprint import pprint
from steempy import Steem
from steempy.account import Account
from steempy.amount import Amount
from steempy.asset import Asset
from steempy.instance import set_shared_steem_instance
from steempybase.operationids import getOperationNameForId

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
# steem_node = "wss://gtg.steem.house:8090"
steem_node = "wss://steemd.pevo.science"


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.stm = Steem(
            steem_node,
            nobroadcast=True,
            # We want to bundle many operations into a single transaction
            bundle=True,
            # Overwrite wallet to use this list of wifs only
            wif=[wif]
        )
        self.stm.set_default_account("test")
        set_shared_steem_instance(self.stm)
