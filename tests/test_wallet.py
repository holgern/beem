import unittest
import mock
from pprint import pprint
from steem import Steem
from steem.account import Account
from steem.amount import Amount
from steem.asset import Asset
from steem.instance import set_shared_steem_instance
from steembase.operationids import getOperationNameForId

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.stm = Steem(
            nobroadcast=True,
            # We want to bundle many operations into a single transaction
            bundle=True,
            # Overwrite wallet to use this list of wifs only
            wif=[wif]
        )
        self.stm.set_default_account("init0")
        set_shared_steem_instance(self.stm)
