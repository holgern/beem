# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes, int, str
import pytz
import json
from datetime import datetime, timedelta, date, time
import math
import random
import logging
from beem.utils import formatTimeString, formatTimedelta, remove_from_dict, reputation_to_score, addTzInfo, parse_time
from beem.amount import Amount
from beem.account import Account
from beem.instance import shared_steem_instance

log = logging.getLogger(__name__)


class AccountSnapshot(list):
    def __init__(self, account, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        self.account = Account(account, steem_instance=self.steem)
        self.own_vests = [Amount("0 VESTS", steem_instance=self.steem)]
        self.delegated_vests_in = [{}]
        self.delegated_vests_out = [{}]
        self.timestamps = [addTzInfo(datetime(1970, 1, 1, 0, 0, 0, 0))]
        self.own_sp = []
        self.eff_sp = []

    def get_account_history(self):
        super(AccountSnapshot, self).__init__(
            [
                h
                for h in self.account.history()
            ]
        )

    def update(self, timestamp, own, delegated_in, delegated_out):
        self.timestamps.append(timestamp - timedelta(seconds=1))
        self.own_vests.append(self.own_vests[-1])
        self.delegated_vests_in.append(self.delegated_vests_in[-1])
        self.delegated_vests_out.append(self.delegated_vests_out[-1])

        self.timestamps.append(timestamp)
        self.own_vests.append(self.own_vests[-1] + own)

        new_deleg = dict(self.delegated_vests_in[-1])
        if delegated_in:
            if delegated_in['amount'] == 0:
                del new_deleg[delegated_in['account']]
            else:
                new_deleg[delegated_in['account']] = delegated_in['amount']
        self.delegated_vests_in.append(new_deleg)

        new_deleg = dict(self.delegated_vests_out[-1])
        if delegated_out:
            if delegated_out['account'] is None:
                # return_vesting_delegation
                for delegatee in new_deleg:
                    if new_deleg[delegatee]['amount'] == delegated_out['amount']:
                        del new_deleg[delegatee]
                        break

            elif delegated_out['amount'] != 0:
                # new or updated non-zero delegation
                new_deleg[delegated_out['account']] = delegated_out['amount']

                # skip undelegations here, wait for 'return_vesting_delegation'
                # del new_deleg[delegated_out['account']]

        self.delegated_vests_out.append(new_deleg)

    def build_vests_history(self):
        for op in sorted(self, key=lambda k: k['timestamp']):
            ts = parse_time(op['timestamp'])
            # print(op)
            if op['type'] == "account_create":
                fee_vests = self.steem.sp_to_vests(Amount(op['fee'], steem_instance=self.steem).amount, timestamp=ts)
                # print(fee_vests)
                if op['new_account_name'] == self.account["name"]:
                    self.update(ts, fee_vests, 0, 0)
                    continue
                if op['creator'] == self.account["name"]:
                    self.update(ts, fee_vests * (-1), 0, 0)
                    continue

            if op['type'] == "account_create_with_delegation":
                fee_vests = self.steem.sp_to_vests(Amount(op['fee'], steem_instance=self.steem).amount, timestamp=ts)
                if op['new_account_name'] == self.account["name"]:
                    if Amount(op['delegation'], steem_instance=self.steem).amount > 0:
                        delegation = {'account': op['creator'], 'amount':
                                      Amount(op['delegation'], steem_instance=self.steem)}
                    else:
                        delegation = None
                    self.update(ts, fee_vests, delegation, 0)
                    continue
                if op['creator'] == self.account["name"]:
                    delegation = {'account': op['new_account_name'], 'amount':
                                  Amount(op['delegation'], steem_instance=self.steem)}
                    self.update(ts, fee_vests * (-1), 0, delegation)
                    continue

            if op['type'] == "delegate_vesting_shares":
                vests = Amount(op['vesting_shares'], steem_instance=self.steem)
                # print(op)

                if op['delegator'] == self.account["name"]:
                    delegation = {'account': op['delegatee'], 'amount': vests}
                    self.update(ts, 0, 0, delegation)
                    continue
                if op['delegatee'] == self.account["name"]:
                    delegation = {'account': op['delegator'], 'amount': vests}
                    self.update(ts, 0, delegation, 0)
                    continue

            if op['type'] == "transfer_to_vesting":
                vests = self.steem.sp_to_vests(Amount(op['amount'], steem_instance=self.steem).amount, timestamp=ts)
                # print(op)
                # print(op, vests)
                self.update(ts, vests, 0, 0)
                continue

            if op['type'] == "fill_vesting_withdraw":
                # print(op)
                vests = Amount(op['withdrawn'], steem_instance=self.steem)
                self.update(ts, vests * (-1), 0, 0)
                continue

            if op['type'] == "return_vesting_delegation":
                delegation = {'account': None, 'amount':
                              Amount(op['vesting_shares'], steem_instance=self.steem)}
                self.update(ts, 0, 0, delegation)
                continue

            if op['type'] == "claim_reward_balance":
                vests = Amount(op['reward_vests'], steem_instance=self.steem)
                self.update(ts, vests, 0, 0)
                continue

            if op['type'] == "producer_reward":
                vests = Amount(op['vesting_shares'], steem_instance=self.steem)
                self.update(ts, vests, 0, 0)
                continue

            if op['type'] == "comment_benefactor_reward":
                if op['benefactor'] == self.account["name"]:
                    vests = Amount(op['reward'], steem_instance=self.steem)
                    self.update(ts, vests, 0, 0)
                    continue
                else:
                    continue

            if op['type'] in ['comment', 'vote', 'curation_reward', 'transfer',
                              'author_reward', 'feed_publish', 'shutdown_witness',
                              'account_witness_vote', 'witness_update', 'custom_json',
                              'fill_order', 'limit_order_create', 'account_update',
                              'account_witness_proxy', 'limit_order_cancel', 'comment_options',
                              'delete_comment']:
                continue

            # if "vests" in str(op).lower():
            #     print(op)
            # else:
            #    print(op)

    def build_arrays(self):
        for (ts, own, din, dout) in zip(self.timestamps, self.own_vests,
                                        self.delegated_vests_in,
                                        self.delegated_vests_out):
            sum_in = sum([din[key].amount for key in din])
            sum_out = sum([dout[key].amount for key in dout])
            sp_in = self.steem.vests_to_sp(sum_in, timestamp=ts)
            sp_out = self.steem.vests_to_sp(sum_out, timestamp=ts)
            sp_own = self.steem.vests_to_sp(own, timestamp=ts)
            sp_eff = sp_own + sp_in - sp_out
            self.own_sp.append(sp_own)
            self.eff_sp.append(sp_eff)
