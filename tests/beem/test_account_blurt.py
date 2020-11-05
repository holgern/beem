# -*- coding: utf-8 -*-
import unittest
import pytz
from datetime import datetime, timedelta
from parameterized import parameterized
from pprint import pprint
from beem import Steem, exceptions, Blurt
from beem.account import Account, extract_account_name
from beem.block import Block
from beem.amount import Amount
from beem.asset import Asset
from beem.utils import formatTimeString
from beem.instance import set_shared_blockchain_instance
from .nodes import get_blurt_nodes

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"


class Testcases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
      
        cls.bts = Blurt(
            node=get_blurt_nodes(),
            nobroadcast=True,
            bundle=False,
            unsigned=True,
            # Overwrite wallet to use this list of wifs only
            keys={"active": wif},
            num_retries=10
        )
        cls.account = Account("beembot", steem_instance=cls.bts)      
        set_shared_blockchain_instance(cls.bts)

    def test_account(self):
        stm = self.bts
        account = self.account
        Account("beembot", steem_instance=stm)
        with self.assertRaises(
            exceptions.AccountDoesNotExistsException
        ):
            Account("DoesNotExistsXXX", steem_instance=stm)
        # asset = Asset("1.3.0")
        # symbol = asset["symbol"]
        self.assertEqual(account.name, "beembot")
        self.assertEqual(account["name"], account.name)
        self.assertIsInstance(account.get_balance("available", "BLURT"), Amount)
        account.print_info()
        # self.assertIsInstance(account.balance({"symbol": symbol}), Amount)
        self.assertIsInstance(account.available_balances, list)
        # self.assertTrue(account.virtual_op_count() > 0)

        # BlockchainObjects method
        account.cached = False
        self.assertTrue(list(account.items()))
        account.cached = False
        self.assertIn("id", account)
        account.cached = False
        # self.assertEqual(account["id"], "1.2.1")
        self.assertEqual(str(account), "<Account beembot>")
        self.assertIsInstance(Account(account), Account)

    def test_history_index(self):
        stm = self.bts
        account = Account("beembot", steem_instance=stm)
        h_list = []
        for h in account.history(start=1, stop=10, use_block_num=False, batch_size=10, raw_output=True):
            h_list.append(h)
        for i in range(len(h_list)):
            self.assertEqual(h_list[i][0], i + 1)

        h_list = []
        for h in account.history(start=1, stop=10, use_block_num=False, batch_size=2, raw_output=True):
            h_list.append(h)
        for i in range(len(h_list)):
            self.assertEqual(h_list[i][0], i + 1)

    def test_account_props(self):
        account = self.account
        rep = account.get_reputation()
        self.assertTrue(isinstance(rep, float))
        vp = account.get_voting_power()
        self.assertTrue(vp >= 0)
        self.assertTrue(vp <= 100)
        sp = account.get_token_power()
        self.assertTrue(sp >= 0)
        vv = account.get_voting_value_SBD()
        self.assertTrue(vv >= 0)
        bw = account.get_bandwidth()
        # self.assertTrue(bw['used'] <= bw['allocated'])
        followers = account.get_followers()
        self.assertTrue(isinstance(followers, list))
        following = account.get_following()
        self.assertTrue(isinstance(following, list))
        count = account.get_follow_count()
        self.assertEqual(count['follower_count'], len(followers))
        self.assertEqual(count['following_count'], len(following))
        

    def test_MissingKeyError(self):
        w = self.account
        w.blockchain.txbuffer.clear()
        tx = w.convert("1 BLURT")
        with self.assertRaises(
            exceptions.MissingKeyError
        ):
            tx.sign()

    def test_withdraw_vesting(self):
        w = self.account
        w.blockchain.txbuffer.clear()
        tx = w.withdraw_vesting("100 VESTS")
        self.assertEqual(
            (tx["operations"][0][0]),
            "withdraw_vesting"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "beembot",
            op["account"])

    def test_delegate_vesting_shares(self):
        w = self.account
        w.blockchain.txbuffer.clear()
        tx = w.delegate_vesting_shares("test1", "100 VESTS")
        self.assertEqual(
            (tx["operations"][0][0]),
            "delegate_vesting_shares"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "beembot",
            op["delegator"])

    def test_claim_reward_balance(self):
        w = self.account
        w.blockchain.txbuffer.clear()
        #tx = w.claim_reward_balance()
        #self.assertEqual(
        #    (tx["operations"][0][0]),
        #    "claim_reward_balance"
        #)
        #op = tx["operations"][0][1]
        #self.assertIn(
        #    "beembot",
        #    op["account"])

    def test_cancel_transfer_from_savings(self):
        w = self.account
        w.blockchain.txbuffer.clear()
        tx = w.cancel_transfer_from_savings(0)
        self.assertEqual(
            (tx["operations"][0][0]),
            "cancel_transfer_from_savings"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "beembot",
            op["from"])

    def test_transfer_from_savings(self):
        w = self.account
        w.blockchain.txbuffer.clear()
        tx = w.transfer_from_savings(1, "BLURT", "")
        self.assertEqual(
            (tx["operations"][0][0]),
            "transfer_from_savings"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "beembot",
            op["from"])

    def test_transfer_to_savings(self):
        w = self.account
        w.blockchain.txbuffer.clear()
        tx = w.transfer_to_savings(1, "BLURT", "")
        self.assertEqual(
            (tx["operations"][0][0]),
            "transfer_to_savings"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "beembot",
            op["from"])

    def test_convert(self):
        w = self.account
        w.blockchain.txbuffer.clear()
        tx = w.convert("1 BLURT")
        self.assertEqual(
            (tx["operations"][0][0]),
            "convert"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "beembot",
            op["owner"])

    def test_proxy(self):
        w = self.account
        w.blockchain.txbuffer.clear()
        tx = w.setproxy(proxy="gtg")
        self.assertEqual(
            (tx["operations"][0][0]),
            "account_witness_proxy"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "gtg",
            op["proxy"])

    def test_transfer_to_vesting(self):
        w = self.account
        w.blockchain.txbuffer.clear()
        tx = w.transfer_to_vesting("1 BLURT")
        self.assertEqual(
            (tx["operations"][0][0]),
            "transfer_to_vesting"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "beembot",
            op["from"])

        w.blockchain.txbuffer.clear()
        tx = w.transfer_to_vesting("1 BLURT", skip_account_check=True)
        self.assertEqual(
            (tx["operations"][0][0]),
            "transfer_to_vesting"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "beembot",
            op["from"])

    def test_transfer(self):
        w = self.account
        w.blockchain.txbuffer.clear()
        tx = w.transfer("beembot", "1", "BLURT")
        self.assertEqual(
            (tx["operations"][0][0]),
            "transfer"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "beembot",
            op["from"])
        self.assertIn(
            "beembot",
            op["to"])        

        w.blockchain.txbuffer.clear()
        tx = w.transfer("beembot", "1", "BLURT", skip_account_check=True)
        self.assertEqual(
            (tx["operations"][0][0]),
            "transfer"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "beembot",
            op["from"])
        self.assertIn(
            "beembot",
            op["to"])        

    def test_json_export(self):
        account = Account("beembot", steem_instance=self.bts)
        if account.blockchain.rpc.get_use_appbase():
            content = self.bts.rpc.find_accounts({'accounts': [account["name"]]}, api="database")["accounts"][0]
        else:
            content = self.bts.rpc.get_accounts([account["name"]])[0]
        keys = list(content.keys())
        json_content = account.json()
        exclude_list = ['owner_challenged', 'average_bandwidth']  # ['json_metadata', 'reputation', 'active_votes', 'savings_sbd_seconds']
        for k in keys:
            if k not in exclude_list:
                if isinstance(content[k], dict) and isinstance(json_content[k], list):
                    content_list = [content[k]["amount"], content[k]["precision"], content[k]["nai"]]
                    self.assertEqual(content_list, json_content[k])
                else:
                    self.assertEqual(content[k], json_content[k])

    def test_reply_history(self):
        account = self.account
        replies = []
        for r in account.reply_history(limit=1):
            replies.append(r)
        #self.assertEqual(len(replies), 1)
        if len(replies) > 0:
            self.assertTrue(replies[0].is_comment())
            self.assertTrue(replies[0].depth > 0)

    def test_history(self):
        stm = self.bts
        account = Account("holger80", steem_instance=stm)        
        h_all_raw = []
        for h in account.history(raw_output=False):
            h_all_raw.append(h)
        index = h_all_raw[0]["index"]
        for op in h_all_raw:
            self.assertEqual(op["index"], index)
            index += 1
