# -*- coding: utf-8 -*-
import unittest
import pytz
from datetime import datetime, timedelta
from parameterized import parameterized
from pprint import pprint
from beem import Steem, exceptions, Hive
from beem.account import Account, extract_account_name
from beem.block import Block
from beem.amount import Amount
from beem.asset import Asset
from beem.utils import formatTimeString
from beem.instance import set_shared_blockchain_instance
from .nodes import get_hive_nodes, get_steem_nodes

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"


class Testcases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
      
        cls.bts = Hive(
            node=get_hive_nodes(),
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
        self.assertIsInstance(account.get_balance("available", "HBD"), Amount)
        account.print_info()
        # self.assertIsInstance(account.balance({"symbol": symbol}), Amount)
        self.assertIsInstance(account.available_balances, list)
        self.assertTrue(account.virtual_op_count() > 0)

        # BlockchainObjects method
        account.cached = False
        self.assertTrue(list(account.items()))
        account.cached = False
        self.assertIn("id", account)
        account.cached = False
        # self.assertEqual(account["id"], "1.2.1")
        self.assertEqual(str(account), "<Account beembot>")
        self.assertIsInstance(Account(account), Account)

    def test_history(self):
        account = self.account
        zero_element = 0
        h_all_raw = []
        for h in account.history_reverse(raw_output=True):
            h_all_raw.append(h)
        index = h_all_raw[0][0]
        for op in h_all_raw:
            self.assertEqual(op[0], index)
            index -= 1
        # h_all_raw = h_all_raw[zero_element:]
        zero_element = h_all_raw[-1][0]
        h_list = []
        for h in account.history(stop=10, use_block_num=False, batch_size=10, raw_output=True):
            h_list.append(h)
        # self.assertEqual(h_list[0][0], zero_element)
        self.assertEqual(h_list[-1][0], 10)
        self.assertEqual(h_list[0][1]['block'], h_all_raw[-1][1]['block'])
        self.assertEqual(h_list[-1][1]['block'], h_all_raw[-11 + zero_element][1]['block'])
        h_list = []
        for h in account.history(start=1, stop=9, use_block_num=False, batch_size=10, raw_output=True):
            h_list.append(h)
        self.assertEqual(h_list[0][0], 1)
        self.assertEqual(h_list[-1][0], 9)
        self.assertEqual(h_list[0][1]['block'], h_all_raw[-2 + zero_element][1]['block'])
        self.assertEqual(h_list[-1][1]['block'], h_all_raw[-10 + zero_element][1]['block'])
        start = formatTimeString(h_list[0][1]["timestamp"])
        stop = formatTimeString(h_list[-1][1]["timestamp"])
        h_list = []
        for h in account.history(start=start, stop=stop, use_block_num=False, batch_size=10, raw_output=True):
            h_list.append(h)
        self.assertEqual(h_list[0][0], 1)
        self.assertEqual(h_list[-1][0], 9)
        self.assertEqual(h_list[0][1]['block'], h_all_raw[-2 + zero_element][1]['block'])
        self.assertEqual(h_list[-1][1]['block'], h_all_raw[-10 + zero_element][1]['block'])
        h_list = []
        for h in account.history_reverse(start=10, stop=0, use_block_num=False, batch_size=10, raw_output=False):
            h_list.append(h)
        # zero_element = h_list[-1]['index']
        self.assertEqual(h_list[0]['index'], 10)
        # self.assertEqual(h_list[-1]['index'], zero_element)
        self.assertEqual(h_list[0]['block'], h_all_raw[-11 + zero_element][1]['block'])
        self.assertEqual(h_list[-1]['block'], h_all_raw[-1][1]['block'])
        h_list = []
        for h in account.history_reverse(start=9, stop=1, use_block_num=False, batch_size=10, raw_output=True):
            h_list.append(h)
        self.assertEqual(h_list[0][0], 9)
        self.assertEqual(h_list[-1][0], 1)
        self.assertEqual(h_list[0][1]['block'], h_all_raw[-10 + zero_element][1]['block'])
        self.assertEqual(h_list[-1][1]['block'], h_all_raw[-2 + zero_element][1]['block'])
        start = formatTimeString(h_list[0][1]["timestamp"])
        stop = formatTimeString(h_list[-1][1]["timestamp"])
        h_list = []
        for h in account.history_reverse(start=start, stop=stop, use_block_num=False, batch_size=10, raw_output=True):
            h_list.append(h)
        # self.assertEqual(h_list[0][0], 8)
        self.assertEqual(h_list[-1][0], 1)
        self.assertEqual(h_list[0][1]['block'], h_all_raw[-10 + zero_element][1]['block'])
        self.assertEqual(h_list[-1][1]['block'], h_all_raw[-2 + zero_element][1]['block'])
        h_list = []
        for h in account.get_account_history(10, 10, use_block_num=False, order=1, raw_output=True):
            h_list.append(h)
        # self.assertEqual(h_list[0][0], zero_element)
        self.assertEqual(h_list[-1][0], 10)
        self.assertEqual(h_list[0][1]['block'], h_all_raw[-1][1]['block'])
        self.assertEqual(h_list[-1][1]['block'], h_all_raw[-11 + zero_element][1]['block'])
        h_list = []
        for h in account.get_account_history(10, 10, use_block_num=False, start=1, stop=9, order=1, raw_output=True):
            h_list.append(h)
        self.assertEqual(h_list[0][0], 1)
        self.assertEqual(h_list[-1][0], 9)
        self.assertEqual(h_list[0][1]['block'], h_all_raw[-2 + zero_element][1]['block'])
        self.assertEqual(h_list[-1][1]['block'], h_all_raw[-10 + zero_element][1]['block'])
        start = formatTimeString(h_list[0][1]["timestamp"])
        stop = formatTimeString(h_list[-1][1]["timestamp"])
        h_list = []
        for h in account.get_account_history(10, 10, use_block_num=False, start=start, stop=stop, order=1, raw_output=True):
            h_list.append(h)
        self.assertEqual(h_list[0][0], 1)
        self.assertEqual(h_list[-1][0], 9)
        self.assertEqual(h_list[0][1]['block'], h_all_raw[-2 + zero_element][1]['block'])
        self.assertEqual(h_list[-1][1]['block'], h_all_raw[-10 + zero_element][1]['block'])
        h_list = []
        for h in account.get_account_history(10, 10, use_block_num=False, order=-1, raw_output=True):
            h_list.append(h)
        self.assertEqual(h_list[0][0], 10)
        # self.assertEqual(h_list[-1][0], zero_element)
        self.assertEqual(h_list[0][1]['block'], h_all_raw[-11 + zero_element][1]['block'])
        self.assertEqual(h_list[-1][1]['block'], h_all_raw[-1][1]['block'])
        h_list = []
        for h in account.get_account_history(10, 10, use_block_num=False, start=9, stop=1, order=-1, raw_output=True):
            h_list.append(h)
        self.assertEqual(h_list[0][0], 9)
        self.assertEqual(h_list[-1][0], 1)
        self.assertEqual(h_list[0][1]['block'], h_all_raw[-10 + zero_element][1]['block'])
        self.assertEqual(h_list[-1][1]['block'], h_all_raw[-2 + zero_element][1]['block'])
        start = formatTimeString(h_list[0][1]["timestamp"])
        stop = formatTimeString(h_list[-1][1]["timestamp"])
        h_list = []
        for h in account.get_account_history(10, 10, start=start, stop=stop, order=-1, raw_output=True):
            h_list.append(h)
        for i in range(len(h_list)):
            self.assertEqual(h_list[i][0], 9 - i)
        
        self.assertEqual(h_list[0][1]['block'], h_all_raw[-10 + zero_element][1]['block'])
        self.assertEqual(h_list[-1][1]['block'], h_all_raw[-2 + zero_element][1]['block'])

    def test_history2(self):
        stm = self.bts
        account = Account("beembot", steem_instance=stm)
        h_list = []
        max_index = account.virtual_op_count()
        for h in account.history(start=max_index - 4, stop=max_index, use_block_num=False, batch_size=2, raw_output=False):
            h_list.append(h)
        self.assertEqual(len(h_list), 5)
        for i in range(1, 5):
            self.assertEqual(h_list[i]["index"] - h_list[i - 1]["index"], 1)

        h_list = []
        for h in account.history(start=max_index - 4, stop=max_index, use_block_num=False, batch_size=6, raw_output=False):
            h_list.append(h)
        self.assertEqual(len(h_list), 5)
        for i in range(1, 5):
            self.assertEqual(h_list[i]["index"] - h_list[i - 1]["index"], 1)

        h_list = []
        for h in account.history(start=max_index - 4, stop=max_index, use_block_num=False, batch_size=2, raw_output=True):
            h_list.append(h)
        self.assertEqual(len(h_list), 5)
        for i in range(1, 5):
            self.assertEqual(h_list[i][0] - h_list[i - 1][0], 1)

        h_list = []
        for h in account.history(start=max_index - 4, stop=max_index, use_block_num=False, batch_size=6, raw_output=True):
            h_list.append(h)
        self.assertEqual(len(h_list), 5)
        for i in range(1, 5):
            self.assertEqual(h_list[i][0] - h_list[i - 1][0], 1)

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

    def test_history_reverse2(self):
        stm = self.bts
        account = Account("beembot", steem_instance=stm)
        h_list = []
        max_index = account.virtual_op_count()
        for h in account.history_reverse(start=max_index, stop=max_index - 4, use_block_num=False, batch_size=2, raw_output=False):
            h_list.append(h)
        self.assertEqual(len(h_list), 5)
        for i in range(1, 5):
            self.assertEqual(h_list[i]["index"] - h_list[i - 1]["index"], -1)

        h_list = []
        for h in account.history_reverse(start=max_index, stop=max_index - 4, use_block_num=False, batch_size=6, raw_output=False):
            h_list.append(h)
        self.assertEqual(len(h_list), 5)
        for i in range(1, 5):
            self.assertEqual(h_list[i]["index"] - h_list[i - 1]["index"], -1)

        h_list = []
        for h in account.history_reverse(start=max_index, stop=max_index - 4, use_block_num=False, batch_size=6, raw_output=True):
            h_list.append(h)
        self.assertEqual(len(h_list), 5)
        for i in range(1, 5):
            self.assertEqual(h_list[i][0] - h_list[i - 1][0], -1)

        h_list = []
        for h in account.history_reverse(start=max_index, stop=max_index - 4, use_block_num=False, batch_size=2, raw_output=True):
            h_list.append(h)
        self.assertEqual(len(h_list), 5)
        for i in range(1, 5):
            self.assertEqual(h_list[i][0] - h_list[i - 1][0], -1)

    def test_history_block_num(self):
        stm = self.bts
        zero_element = 0
        account = Account("beembot", steem_instance=stm)
        h_all_raw = []
        for h in account.history_reverse(use_block_num=False, stop=-15, raw_output=True):
            h_all_raw.append(h)
        h_list = []
        self.assertTrue(len(h_all_raw) > 0)
        self.assertTrue(len(h_all_raw[0]) > 1)
        self.assertTrue("block" in h_all_raw[0][1])
        for h in account.history(start=h_all_raw[-1][1]["block"], stop=h_all_raw[0][1]["block"], use_block_num=True, batch_size=10, raw_output=True):
            h_list.append(h)
        # self.assertEqual(h_list[0][0], zero_element)
        self.assertEqual(h_list[-1][0], h_all_raw[0][0])
        self.assertEqual(h_list[0][1]['block'], h_all_raw[-1][1]['block'])
        self.assertEqual(h_list[-1][1]['block'], h_all_raw[0][1]['block'])
        h_list = []
        for h in account.history_reverse(start=h_all_raw[0][1]["block"], stop=h_all_raw[-1][1]["block"], use_block_num=True, batch_size=10, raw_output=True):
            h_list.append(h)
        # self.assertEqual(h_list[0][0], 10)
        
        self.assertEqual(h_list[0][0], h_all_raw[0][0])
        self.assertEqual(h_list[0][1]['block'], h_all_raw[0][1]['block'])
        self.assertEqual(h_list[-1][1]['block'], h_all_raw[-1][1]['block'])

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
        tx = w.convert("1 HBD")
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
        tx = w.claim_reward_balance()
        self.assertEqual(
            (tx["operations"][0][0]),
            "claim_reward_balance"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "beembot",
            op["account"])

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
        tx = w.transfer_from_savings(1, "HIVE", "")
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
        tx = w.transfer_to_savings(1, "HIVE", "")
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
        tx = w.convert("1 HBD")
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
        tx = w.transfer_to_vesting("1 HIVE")
        self.assertEqual(
            (tx["operations"][0][0]),
            "transfer_to_vesting"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "beembot",
            op["from"])

        w.blockchain.txbuffer.clear()
        tx = w.transfer_to_vesting("1 HIVE", skip_account_check=True)
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
        tx = w.transfer("beembot", "1", "HIVE")
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
        tx = w.transfer("beembot", "1", "HIVE", skip_account_check=True)
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

    def test_estimate_virtual_op_num(self):
        stm = self.bts
        account = Account("gtg", steem_instance=stm)
        block_num = 21248120
        block = Block(block_num, steem_instance=stm)
        op_num1 = account.estimate_virtual_op_num(block.time(), stop_diff=1, max_count=100)
        op_num2 = account.estimate_virtual_op_num(block_num, stop_diff=1, max_count=100)
        op_num3 = account.estimate_virtual_op_num(block_num, stop_diff=100, max_count=100)
        op_num4 = account.estimate_virtual_op_num(block_num, stop_diff=0.00001, max_count=100)
        self.assertTrue(abs(op_num1 - op_num2) < 2)
        self.assertTrue(abs(op_num1 - op_num4) < 2)
        self.assertTrue(abs(op_num1 - op_num3) < 200)
        block_diff1 = 0
        block_diff2 = 0
        for h in account.get_account_history(op_num4 - 1, 1):
            block_diff1 = (block_num - h["block"])
        for h in account.get_account_history(op_num4 + 1, 1):
            block_diff2 = (block_num - h["block"])
        self.assertTrue(block_diff1 > 0)
        self.assertTrue(block_diff1 < 1000)
        self.assertTrue(block_diff2 <= 0)
        self.assertTrue(block_diff2 > -1000)

    def test_estimate_virtual_op_num2(self):
        account = self.account
        h_all_raw = []
        for h in account.history(raw_output=False):
            h_all_raw.append(h)
        index = h_all_raw[0]["index"]
        for op in h_all_raw:
            self.assertEqual(op["index"], index)
            index += 1
        last_block = h_all_raw[0]["block"]
        i = 1
        for op in h_all_raw[1:5]:
            new_block = op["block"]
            block_num = last_block + int((new_block - last_block) / 2)
            op_num = account.estimate_virtual_op_num(block_num, stop_diff=0.1, max_count=100)
            if op_num > 0:
                op_num -= 1
            self.assertTrue(op_num <= i)
            i += 1
            last_block = new_block

    def test_history_votes(self):
        stm = self.bts
        account = Account("gtg", steem_instance=stm)
        utc = pytz.timezone('UTC')
        limit_time = utc.localize(datetime.utcnow()) - timedelta(days=2)
        votes_list = []
        for v in account.history(start=limit_time, only_ops=["vote"]):
            votes_list.append(v)
        start_num = votes_list[0]["block"]
        votes_list2 = []
        for v in account.history(start=start_num, only_ops=["vote"]):
            votes_list2.append(v)
        self.assertTrue(abs(len(votes_list) - len(votes_list2)) < 2)

        account = Account("beembot", blockchain_instance=stm)
        votes_list = list(account.history(only_ops=["vote"]))
        votes_list2 = list(account.history_reverse(only_ops=["vote"]))
        self.assertEqual(len(votes_list), len(votes_list2))
        self.assertEqual(votes_list[0]["voter"], votes_list2[-1]["voter"])
        self.assertEqual(votes_list[-1]["voter"], votes_list2[0]["voter"])

    def test_history_op_filter(self):
        stm = Hive("https://api.hive.blog")
        account = Account("beembot", blockchain_instance=stm)
        votes_list = list(account.history(only_ops=["vote"]))
        other_list = list(account.history(exclude_ops=["vote"]))
        all_list = list(account.history())
        self.assertEqual(len(all_list), len(votes_list) + len(other_list))
        index = 0
        for h in sorted((votes_list + other_list), key=lambda h: h["index"]):
            self.assertEqual(index, h["index"])
            index += 1
        votes_list = list(account.history_reverse(only_ops=["vote"]))
        other_list = list(account.history_reverse(exclude_ops=["vote"]))
        all_list = list(account.history_reverse())
        self.assertEqual(len(all_list), len(votes_list) + len(other_list))
        index = 0
        for h in sorted((votes_list + other_list), key=lambda h: h["index"]):
            self.assertEqual(index, h["index"])
            index += 1        

    def test_history_op_filter2(self):
        stm = Hive("https://api.hive.blog")
        batch_size = 100
        account = Account("beembot", blockchain_instance=stm)
        votes_list = list(account.history(only_ops=["vote"], batch_size=batch_size))
        other_list = list(account.history(exclude_ops=["vote"], batch_size=batch_size))
        all_list = list(account.history(batch_size=batch_size))
        self.assertEqual(len(all_list), len(votes_list) + len(other_list))
        index = 0
        for h in sorted((votes_list + other_list), key=lambda h: h["index"]):
            self.assertEqual(index, h["index"])
            index += 1
        votes_list = list(account.history_reverse(only_ops=["vote"], batch_size=batch_size))
        other_list = list(account.history_reverse(exclude_ops=["vote"], batch_size=batch_size))
        all_list = list(account.history_reverse(batch_size=batch_size))
        self.assertEqual(len(all_list), len(votes_list) + len(other_list))
        index = 0
        for h in sorted((votes_list + other_list), key=lambda h: h["index"]):
            self.assertEqual(index, h["index"])
            index += 1    

    def test_comment_history(self):
        account = self.account
        comments = []
        for c in account.comment_history(limit=1):
            comments.append(c)
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0]["author"], account["name"])
        self.assertTrue(comments[0].is_comment())
        self.assertTrue(comments[0].depth > 0)

    def test_blog_history(self):
        account = Account("holger80", steem_instance=self.bts)
        posts = []
        for p in account.blog_history(limit=5):
            if p["author"] != account["name"]:
                continue
            posts.append(p)
        self.assertTrue(len(posts) >= 1)
        self.assertEqual(posts[0]["author"], account["name"])
        self.assertTrue(posts[0].is_main_post())
        self.assertTrue(posts[0].depth == 0)

    def test_reply_history(self):
        account = self.account
        replies = []
        for r in account.reply_history(limit=1):
            replies.append(r)
        #self.assertEqual(len(replies), 1)
        if len(replies) > 0:
            self.assertTrue(replies[0].is_comment())
            self.assertTrue(replies[0].depth > 0)

    def test_get_vote_pct_for_vote_value(self):
        account = self.account
        for vote_pwr in range(5, 100, 5):
            self.assertTrue(9900 <= account.get_vote_pct_for_vote_value(account.get_voting_value(voting_power=vote_pwr), voting_power=vote_pwr) <= 11000)

    def test_list_subscriptions(self):
        stm = self.bts
        account = Account("holger80", steem_instance=stm)
        assert len(account.list_all_subscriptions()) > 0

    def test_account_feeds(self):
        stm = self.bts
        account = Account("holger80", steem_instance=stm)
        assert len(account.get_account_posts()) > 0

    def test_notifications(self):
        stm = self.bts
        account = Account("gtg", steem_instance=stm)
        assert isinstance(account.get_notifications(), list)

    def test_extract_account_name(self):
        stm = self.bts
        account = Account("holger80", steem_instance=stm)
        self.assertEqual(extract_account_name(account), "holger80")
        self.assertEqual(extract_account_name("holger80"), "holger80")
        self.assertEqual(extract_account_name({"name": "holger80"}), "holger80")
        self.assertEqual(extract_account_name(""), "")

    def test_get_blocknum_from_hist(self):
        stm = Hive("https://api.hive.blog")
        account = Account("beembot", blockchain_instance=stm)
        created, min_index = account._get_first_blocknum()
        if min_index == 0:
            self.assertEqual(created, 23687631)
            block = account._get_blocknum_from_hist(0, min_index=min_index)
            self.assertEqual(block, 23687631)
            hist_num = account.estimate_virtual_op_num(block, min_index=min_index)
            self.assertEqual(hist_num, 0)
        else:
            self.assertEqual(created, 23721519)
        min_index = 1
        block = account._get_blocknum_from_hist(0, min_index=min_index)
        self.assertEqual(block, 23721519)
