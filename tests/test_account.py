import unittest
import mock
from pprint import pprint
from steem import Steem, exceptions
from steem.account import Account
from steem.amount import Amount
from steem.asset import Asset
from steem.instance import set_shared_steem_instance
from steembase.operationids import getOperationNameForId

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bts = Steem(
            "wss://testnet.steem.vc",
            nobroadcast=True,
            # We want to bundle many operations into a single transaction
            bundle=True,
            # Overwrite wallet to use this list of wifs only
            wif={"active": wif}
        )
        self.bts.set_default_account("test")
        set_shared_steem_instance(self.bts)

    def test_account(self):
        Account("test")
        with self.assertRaises(
            exceptions.AccountDoesNotExistsException
        ):        
            Account("DoesNotExistsXXX")
        # asset = Asset("1.3.0")
        # symbol = asset["symbol"]
        account = Account("test", full=True)
        self.assertEqual(account.name, "test")
        self.assertEqual(account["name"], account.name)
        self.assertIsInstance(account.balance("available", "SBD"), Amount)
        # self.assertIsInstance(account.balance({"symbol": symbol}), Amount)
        self.assertIsInstance(account.available_balances, list)
        for h in account.history(limit=1):
            pass

        # BlockchainObjects method
        account.cached = False
        self.assertTrue(account.items())
        account.cached = False
        self.assertIn("id", account)
        account.cached = False
        # self.assertEqual(account["id"], "1.2.1")
        self.assertEqual(str(account), "<Account test>")
        self.assertIsInstance(Account(account), Account)


