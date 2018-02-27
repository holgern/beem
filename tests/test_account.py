from builtins import str
import unittest
import mock
from pprint import pprint
from beem import Steem, exceptions
from beem.account import Account
from beem.amount import Amount
from beem.asset import Asset
from beem.instance import set_shared_steem_instance
from beembase.operationids import getOperationNameForId

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://node.steem.ws", "wss://steemd.steemgigs.org", "wss://steemd.steemit.com",
         "wss://steemd.minnowsupportproject.org"]


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bts = Steem(
            nodes,
            nobroadcast=True,
            bundle=False,
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
        self.assertTrue(list(account.items()))
        account.cached = False
        self.assertIn("id", account)
        account.cached = False
        # self.assertEqual(account["id"], "1.2.1")
        self.assertEqual(str(account), "<Account test>")
        self.assertIsInstance(Account(account), Account)

    def test_account_props(self):
        account = Account("test", full=True)
        rep = account.reputation()
        self.assertTrue(isinstance(rep, float))
        vp = account.voting_power()
        self.assertTrue(vp >= 0)
        self.assertTrue(vp <= 100)
        sp = account.steem_power()
        self.assertTrue(sp >= 0)
        vv = account.get_voting_value_SBD()
        self.assertTrue(vv >= 0)
        bw = account.get_bandwidth()
        self.assertTrue(bw['used'] <= bw['allocated'])
        followers = account.get_followers()
        self.assertTrue(isinstance(followers, list))
        following = account.get_following()
        self.assertTrue(isinstance(following, list))
        count = account.get_follow_count()
        self.assertEqual(count['follower_count'], len(followers))
        self.assertEqual(count['following_count'], len(following))

    def test_withdraw_vesting(self):
        bts = self.bts
        w = Account("test", steem_instance=bts)
        tx = w.withdraw_vesting("100 VESTS")
        self.assertEqual(
            (tx["operations"][0][0]),
            "withdraw_vesting"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["account"])

    def test_delegate_vesting_shares(self):
        bts = self.bts
        w = Account("test", steem_instance=bts)
        tx = w.delegate_vesting_shares("test1", "100 VESTS")
        self.assertEqual(
            (tx["operations"][0][0]),
            "delegate_vesting_shares"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["delegator"])

    def test_claim_reward_balance(self):
        bts = self.bts
        w = Account("test", steem_instance=bts)
        tx = w.claim_reward_balance()
        self.assertEqual(
            (tx["operations"][0][0]),
            "claim_reward_balance"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["account"])

    def test_cancel_transfer_from_savings(self):
        bts = self.bts
        w = Account("test", steem_instance=bts)
        tx = w.cancel_transfer_from_savings(0)
        self.assertEqual(
            (tx["operations"][0][0]),
            "cancel_transfer_from_savings"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["from"])

    def test_transfer_from_savings(self):
        bts = self.bts
        w = Account("test", steem_instance=bts)
        tx = w.transfer_from_savings(1, "STEEM", "")
        self.assertEqual(
            (tx["operations"][0][0]),
            "transfer_from_savings"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["from"])

    def test_transfer_to_savings(self):
        bts = self.bts
        w = Account("test", steem_instance=bts)
        tx = w.transfer_to_savings(1, "STEEM", "")
        self.assertEqual(
            (tx["operations"][0][0]),
            "transfer_to_savings"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["from"])

    def test_convert(self):
        bts = self.bts
        w = Account("test", steem_instance=bts)
        tx = w.convert("1 SBD")
        self.assertEqual(
            (tx["operations"][0][0]),
            "convert"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["owner"])

    def test_transfer_to_vesting(self):
        bts = self.bts
        w = Account("test", steem_instance=bts)
        tx = w.transfer_to_vesting("1 STEEM")
        self.assertEqual(
            (tx["operations"][0][0]),
            "transfer_to_vesting"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["from"])
