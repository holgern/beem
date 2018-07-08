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
    """ This class allows to easily access Account history

        :param str account_name: Name of the account
        :param beem.steem.Steem steem_instance: Steem
               instance
    """
    def __init__(self, account, account_history=[], steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        self.account = Account(account, steem_instance=self.steem)
        self.reset()
        super(AccountSnapshot, self).__init__(account_history)

    def reset(self):
        """ Resets the arrays not the stored account history
        """
        self.own_vests = [Amount("0 VESTS", steem_instance=self.steem)]
        self.own_steem = [Amount("0 STEEM", steem_instance=self.steem)]
        self.own_sbd = [Amount("0 SBD", steem_instance=self.steem)]
        self.delegated_vests_in = [{}]
        self.delegated_vests_out = [{}]
        self.timestamps = [addTzInfo(datetime(1970, 1, 1, 0, 0, 0, 0))]
        import beembase.operationids
        self.ops_statistics = beembase.operationids.operations.copy()
        for key in self.ops_statistics:
            self.ops_statistics[key] = 0

    def get_data(self, timestamp=None):
        """ Returns snapshot for given timestamp"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        timestamp = addTzInfo(timestamp)
        for (ts, own, din, dout, steem, sbd) in zip(self.timestamps, self.own_vests,
                                                    self.delegated_vests_in,
                                                    self.delegated_vests_out,
                                                    self.own_steem,
                                                    self.own_sbd):
            sum_in = sum([din[key].amount for key in din])
            sum_out = sum([dout[key].amount for key in dout])
            sp_in = self.steem.vests_to_sp(sum_in, timestamp=ts)
            sp_out = self.steem.vests_to_sp(sum_out, timestamp=ts)
            sp_own = self.steem.vests_to_sp(own, timestamp=ts)
            sp_eff = sp_own + sp_in - sp_out
            if timestamp < ts:
                continue
            else:
                return {"timestamp": ts, "vests": own, "delegated_vests_in": din, "delegated_vests_out": dout,
                        "sp_own": sp_own, "sp_eff": sp_eff, "steem": steem, "sbd": sbd}
        return {}

    def get_account_history(self, start=None, stop=None, use_block_num=True):
        """ Uses account history to fetch all related ops

            :param int/datetime start: start number/date of transactions to
                return (*optional*)
            :param int/datetime stop: stop number/date of transactions to
                return (*optional*)
            :param bool use_block_num: if true, start and stop are block numbers,
                otherwise virtual OP count numbers.

        """
        super(AccountSnapshot, self).__init__(
            [
                h
                for h in self.account.history(start=start, stop=stop, use_block_num=use_block_num)
            ]
        )

    def update(self, timestamp, own, delegated_in=None, delegated_out=None, steem=0, sbd=0):
        """ Updates the internal state arrays

            :param datetime timestamp: datetime of the update
            :param Amount/float own: vests
            :param dict delegated_in: Incoming delegation
            :param dict delegated_out: Outgoing delegation
            :param Amount/float steem: steem
            :param Amount/float sbd: sbd

        """
        self.timestamps.append(timestamp - timedelta(seconds=1))
        self.own_vests.append(self.own_vests[-1])
        self.own_steem.append(self.own_steem[-1])
        self.own_sbd.append(self.own_sbd[-1])
        self.delegated_vests_in.append(self.delegated_vests_in[-1])
        self.delegated_vests_out.append(self.delegated_vests_out[-1])

        self.timestamps.append(timestamp)
        self.own_vests.append(self.own_vests[-1] + own)
        self.own_steem.append(self.own_steem[-1] + steem)
        self.own_sbd.append(self.own_sbd[-1] + sbd)

        new_deleg = dict(self.delegated_vests_in[-1])
        if delegated_in is not None and delegated_in:
            if delegated_in['amount'] == 0:
                del new_deleg[delegated_in['account']]
            else:
                new_deleg[delegated_in['account']] = delegated_in['amount']
        self.delegated_vests_in.append(new_deleg)

        new_deleg = dict(self.delegated_vests_out[-1])
        if delegated_out is not None and delegated_out:
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

    def build(self, only_ops=[], exclude_ops=[]):
        """ Builds the account history based on all account operations

            :param array only_ops: Limit generator by these
                operations (*optional*)
            :param array exclude_ops: Exclude thse operations from
                generator (*optional*)

        """
        if len(self.timestamps) > 0:
            start_timestamp = self.timestamps[-1]
        else:
            start_timestamp = None
        for op in sorted(self, key=lambda k: k['timestamp']):
            ts = parse_time(op['timestamp'])
            if start_timestamp is not None and start_timestamp > ts:
                continue
            # print(op)
            if op['type'] in exclude_ops:
                continue
            if len(only_ops) > 0 and op['type'] not in only_ops:
                continue
            self.ops_statistics[op['type']] += 1
            if op['type'] == "account_create":
                fee_steem = Amount(op['fee'], steem_instance=self.steem).amount
                fee_vests = self.steem.sp_to_vests(Amount(op['fee'], steem_instance=self.steem).amount, timestamp=ts)
                # print(fee_vests)
                if op['new_account_name'] == self.account["name"]:
                    self.update(ts, fee_vests, 0, 0)
                    continue
                if op['creator'] == self.account["name"]:
                    self.update(ts, 0, 0, 0, fee_steem * (-1), 0)
                    continue

            if op['type'] == "account_create_with_delegation":
                fee_steem = Amount(op['fee'], steem_instance=self.steem).amount
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
                    self.update(ts, 0, 0, delegation, fee_steem * (-1), 0)
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

            if op['type'] == "transfer":
                amount = Amount(op['amount'], steem_instance=self.steem)
                # print(op)
                if op['from'] == self.account["name"]:
                    if amount.symbol == "STEEM":
                        self.update(ts, 0, 0, 0, amount * (-1), 0)
                    elif amount.symbol == "SBD":
                        self.update(ts, 0, 0, 0, 0, amount * (-1))
                if op['to'] == self.account["name"]:
                    if amount.symbol == "STEEM":
                        self.update(ts, 0, 0, 0, amount, 0)
                    elif amount.symbol == "SBD":
                        self.update(ts, 0, 0, 0, 0, amount)
                # print(op, vests)
                # self.update(ts, vests, 0, 0)
                continue

            if op['type'] == "fill_order":
                current_pays = Amount(op["current_pays"], steem_instance=self.steem)
                open_pays = Amount(op["open_pays"], steem_instance=self.steem)
                if op["current_owner"] == self.account["name"]:
                    if current_pays.symbol == "STEEM":
                        self.update(ts, 0, 0, 0, current_pays * (-1), open_pays)
                    elif current_pays.symbol == "SBD":
                        self.update(ts, 0, 0, 0, open_pays, current_pays * (-1))
                if op["open_owner"] == self.account["name"]:
                    if current_pays.symbol == "STEEM":
                        self.update(ts, 0, 0, 0, current_pays, open_pays * (-1))
                    elif current_pays.symbol == "SBD":
                        self.update(ts, 0, 0, 0, open_pays * (-1), current_pays)
                # print(op)
                continue

            if op['type'] == "transfer_to_vesting":
                steem = Amount(op['amount'], steem_instance=self.steem)
                vests = self.steem.sp_to_vests(steem.amount, timestamp=ts)
                if op['from'] == self.account["name"]:
                    self.update(ts, vests, 0, 0, steem * (-1), 0)
                else:
                    self.update(ts, vests, 0, 0, 0, 0)
                # print(op)
                # print(op, vests)
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
                steem = Amount(op['reward_steem'], steem_instance=self.steem)
                sbd = Amount(op['reward_sbd'], steem_instance=self.steem)
                self.update(ts, vests, 0, 0, steem, sbd)
                continue

            if op['type'] == "curation_reward":
                if "curation_reward" in only_ops:
                    vests = Amount(op['reward'], steem_instance=self.steem)
                    self.update(ts, vests, 0, 0)
                continue

            if op['type'] == "author_reward":
                if "author_reward" in only_ops:
                    # print(op)
                    vests = Amount(op['vesting_payout'], steem_instance=self.steem)
                    steem = Amount(op['steem_payout'], steem_instance=self.steem)
                    sbd = Amount(op['sbd_payout'], steem_instance=self.steem)
                    self.update(ts, vests, 0, 0, steem, sbd)
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

            if op['type'] == "fill_convert_request":
                amount_in = Amount(op["amount_in"], steem_instance=self.steem)
                amount_out = Amount(op["amount_out"], steem_instance=self.steem)
                if op["owner"] == self.account["name"]:
                    self.update(ts, 0, 0, 0, amount_out, amount_in * (-1))
                continue

            if op['type'] == "interest":
                interest = Amount(op["interest"], steem_instance=self.steem)
                self.update(ts, 0, 0, 0, 0, interest)
                continue

            if op['type'] in ['comment', 'vote', 'feed_publish', 'shutdown_witness',
                              'account_witness_vote', 'witness_update', 'custom_json',
                              'limit_order_create', 'account_update',
                              'account_witness_proxy', 'limit_order_cancel', 'comment_options',
                              'delete_comment', 'interest', 'recover_account', 'pow',
                              'fill_convert_request', 'convert', 'request_account_recovery']:
                continue

            # if "vests" in str(op).lower():
            #     print(op)
            # else:
            # print(op)

    def build_sp_arrays(self):
        """ Builds the own_sp and eff_sp array"""
        self.own_sp = []
        self.eff_sp = []
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

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__, str(self.account["name"]))
