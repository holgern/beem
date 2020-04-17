# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes, int, str
import pytz
import json
import re
from datetime import datetime, timedelta, date, time
import math
import random
import logging
from bisect import bisect_left
from beem.utils import formatTimeString, formatTimedelta, remove_from_dict, reputation_to_score, addTzInfo, parse_time
from beem.amount import Amount
from beem.account import Account
from beem.vote import Vote
from beem.instance import shared_blockchain_instance
from beem.constants import STEEM_VOTE_REGENERATION_SECONDS, STEEM_1_PERCENT, STEEM_100_PERCENT

log = logging.getLogger(__name__)


class AccountSnapshot(list):
    """ This class allows to easily access Account history

        :param str account_name: Name of the account
        :param Steem blockchain_instance: Steem
               instance
    """
    def __init__(self, account, account_history=[], blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]          
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        self.account = Account(account, blockchain_instance=self.blockchain)
        self.reset()
        super(AccountSnapshot, self).__init__(account_history)

    def reset(self):
        """ Resets the arrays not the stored account history
        """
        self.own_vests = [Amount(0, self.blockchain.vest_token_symbol, blockchain_instance=self.blockchain)]
        self.own_steem = [Amount(0, self.blockchain.token_symbol, blockchain_instance=self.blockchain)]
        self.own_sbd = [Amount(0, self.blockchain.backed_token_symbol, blockchain_instance=self.blockchain)]
        self.delegated_vests_in = [{}]
        self.delegated_vests_out = [{}]
        self.timestamps = [addTzInfo(datetime(1970, 1, 1, 0, 0, 0, 0))]
        import beembase.operationids
        self.ops_statistics = beembase.operationids.operations.copy()
        for key in self.ops_statistics:
            self.ops_statistics[key] = 0
        self.reward_timestamps = []
        self.author_rewards = []
        self.curation_rewards = []
        self.curation_per_1000_SP_timestamp = []
        self.curation_per_1000_SP = []
        self.out_vote_timestamp = []
        self.out_vote_weight = []
        self.in_vote_timestamp = []
        self.in_vote_weight = []
        self.in_vote_rep = []
        self.in_vote_rshares = []
        self.vp = []
        self.vp_timestamp = []
        self.downvote_vp = []
        self.downvote_vp_timestamp = []
        self.rep = []
        self.rep_timestamp = []

    def search(self, search_str, start=None, stop=None, use_block_num=True):
        """ Returns ops in the given range"""
        ops = []
        if start is not None:
            start = addTzInfo(start)
        if stop is not None:
            stop = addTzInfo(stop)
        for op in self:
            if use_block_num and start is not None and isinstance(start, int):
                if op["block"] < start:
                    continue
            elif not use_block_num and start is not None and isinstance(start, int):
                if op["index"] < start:
                    continue
            elif start is not None and isinstance(start, (datetime, date, time)):
                if start > formatTimeString(op["timestamp"]):
                    continue
            if use_block_num and stop is not None and isinstance(stop, int):
                if op["block"] > stop:
                    continue
            elif not use_block_num and stop is not None and isinstance(stop, int):
                if op["index"] > stop:
                    continue
            elif stop is not None and isinstance(stop, (datetime, date, time)):
                if stop < formatTimeString(op["timestamp"]):
                    continue
            op_string = json.dumps(list(op.values()))
            if re.search(search_str, op_string):
                ops.append(op)
        return ops

    def get_ops(self, start=None, stop=None, use_block_num=True, only_ops=[], exclude_ops=[]):
        """ Returns ops in the given range"""
        if start is not None:
            start = addTzInfo(start)
        if stop is not None:
            stop = addTzInfo(stop)
        for op in self:
            if use_block_num and start is not None and isinstance(start, int):
                if op["block"] < start:
                    continue
            elif not use_block_num and start is not None and isinstance(start, int):
                if op["index"] < start:
                    continue
            elif start is not None and isinstance(start, (datetime, date, time)):
                if start > formatTimeString(op["timestamp"]):
                    continue
            if use_block_num and stop is not None and isinstance(stop, int):
                if op["block"] > stop:
                    continue
            elif not use_block_num and stop is not None and isinstance(stop, int):
                if op["index"] > stop:
                    continue
            elif stop is not None and isinstance(stop, (datetime, date, time)):
                if stop < formatTimeString(op["timestamp"]):
                    continue
            if exclude_ops and op["type"] in exclude_ops:
                continue
            if not only_ops or op["type"] in only_ops:
                yield op

    def get_data(self, timestamp=None, index=0):
        """ Returns snapshot for given timestamp"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        timestamp = addTzInfo(timestamp)
        # Find rightmost value less than x
        i = bisect_left(self.timestamps, timestamp)
        if i:
            index = i - 1
        else:
            return {}
        ts = self.timestamps[index]
        own = self.own_vests[index]
        din = self.delegated_vests_in[index]
        dout = self.delegated_vests_out[index]
        steem = self.own_steem[index]
        sbd = self.own_sbd[index]
        sum_in = sum([din[key].amount for key in din])
        sum_out = sum([dout[key].amount for key in dout])
        from beem import Steem
        if isinstance(self.blockchain, Steem):
            sp_in = self.blockchain.vests_to_sp(sum_in, timestamp=ts)
            sp_out = self.blockchain.vests_to_sp(sum_out, timestamp=ts)
            sp_own = self.blockchain.vests_to_sp(own, timestamp=ts)
        else:
            sp_in = self.blockchain.vests_to_hp(sum_in, timestamp=ts)
            sp_out = self.blockchain.vests_to_hp(sum_out, timestamp=ts)
            sp_own = self.blockchain.vests_to_hp(own, timestamp=ts)            
        sp_eff = sp_own + sp_in - sp_out
        return {"timestamp": ts, "vests": own, "delegated_vests_in": din, "delegated_vests_out": dout,
                "sp_own": sp_own, "sp_eff": sp_eff, "steem": steem, "sbd": sbd, "index": index}

    def get_account_history(self, start=None, stop=None, use_block_num=True):
        """ Uses account history to fetch all related ops

            :param start: start number/date of transactions to
                return (*optional*)
            :type start: int, datetime
            :param stop: stop number/date of transactions to
                return (*optional*)
            :type stop: int, datetime
            :param bool use_block_num: if true, start and stop are block numbers,
                otherwise virtual OP count numbers.

        """
        super(AccountSnapshot, self).__init__(
            [
                h
                for h in self.account.history(start=start, stop=stop, use_block_num=use_block_num)
            ]
        )

    def update_rewards(self, timestamp, curation_reward, author_vests, author_steem, author_sbd):
        self.reward_timestamps.append(timestamp)
        self.curation_rewards.append(curation_reward)
        self.author_rewards.append({"vests": author_vests, "steem": author_steem, "sbd": author_sbd})

    def update_out_vote(self, timestamp, weight):
        self.out_vote_timestamp.append(timestamp)
        self.out_vote_weight.append(weight)

    def update_in_vote(self, timestamp, weight, op):
        v = Vote(op)
        try:
            v.refresh()
            self.in_vote_timestamp.append(timestamp)
            self.in_vote_weight.append(weight)
            self.in_vote_rep.append(int(v["reputation"]))
            self.in_vote_rshares.append(int(v["rshares"]))
        except:
            print("Could not find: %s" % v)
            return

    def update(self, timestamp, own, delegated_in=None, delegated_out=None, steem=0, sbd=0):
        """ Updates the internal state arrays

            :param datetime timestamp: datetime of the update
            :param own: vests
            :type own: amount.Amount, float
            :param dict delegated_in: Incoming delegation
            :param dict delegated_out: Outgoing delegation
            :param steem: steem
            :type steem: amount.Amount, float
            :param sbd: sbd
            :type sbd: amount.Amount, float

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
                # TODO
                # skip undelegations here, wait for 'return_vesting_delegation'
                # del new_deleg[delegated_out['account']]

        self.delegated_vests_out.append(new_deleg)

    def build(self, only_ops=[], exclude_ops=[], enable_rewards=False, enable_out_votes=False, enable_in_votes=False):
        """ Builds the account history based on all account operations

            :param array only_ops: Limit generator by these
                operations (*optional*)
            :param array exclude_ops: Exclude these operations from
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
            if op['type'] in exclude_ops:
                continue
            if len(only_ops) > 0 and op['type'] not in only_ops:
                continue
            self.ops_statistics[op['type']] += 1
            self.parse_op(op, only_ops=only_ops, enable_rewards=enable_rewards, enable_out_votes=enable_out_votes, enable_in_votes=enable_in_votes)

    def parse_op(self, op, only_ops=[], enable_rewards=False, enable_out_votes=False, enable_in_votes=False):
        """ Parse account history operation"""
        ts = parse_time(op['timestamp'])

        if op['type'] == "account_create":
            fee_steem = Amount(op['fee'], blockchain_instance=self.blockchain).amount
            fee_vests = self.blockchain.sp_to_vests(Amount(op['fee'], blockchain_instance=self.blockchain).amount, timestamp=ts)
            if op['new_account_name'] == self.account["name"]:
                self.update(ts, fee_vests, 0, 0)
                return
            if op['creator'] == self.account["name"]:
                self.update(ts, 0, 0, 0, fee_steem * (-1), 0)
                return

        elif op['type'] == "account_create_with_delegation":
            fee_steem = Amount(op['fee'], blockchain_instance=self.blockchain).amount
            from beem import Steem
            if isinstance(self.blockchain, Steem):
                fee_vests = self.blockchain.sp_to_vests(Amount(op['fee'], blockchain_instance=self.blockchain).amount, timestamp=ts)
            else:
                fee_vests = self.blockchain.hp_to_vests(Amount(op['fee'], blockchain_instance=self.blockchain).amount, timestamp=ts)
            if op['new_account_name'] == self.account["name"]:
                if Amount(op['delegation'], blockchain_instance=self.blockchain).amount > 0:
                    delegation = {'account': op['creator'], 'amount':
                                  Amount(op['delegation'], blockchain_instance=self.blockchain)}
                else:
                    delegation = None
                self.update(ts, fee_vests, delegation, 0)
                return

            if op['creator'] == self.account["name"]:
                delegation = {'account': op['new_account_name'], 'amount':
                              Amount(op['delegation'], blockchain_instance=self.blockchain)}
                self.update(ts, 0, 0, delegation, fee_steem * (-1), 0)
                return

        elif op['type'] == "delegate_vesting_shares":
            vests = Amount(op['vesting_shares'], blockchain_instance=self.blockchain)
            if op['delegator'] == self.account["name"]:
                delegation = {'account': op['delegatee'], 'amount': vests}
                self.update(ts, 0, 0, delegation)
                return
            if op['delegatee'] == self.account["name"]:
                delegation = {'account': op['delegator'], 'amount': vests}
                self.update(ts, 0, delegation, 0)
                return

        elif op['type'] == "transfer":
            amount = Amount(op['amount'], blockchain_instance=self.blockchain)
            if op['from'] == self.account["name"]:
                if amount.symbol == self.blockchain.blockchain_symbol:
                    self.update(ts, 0, 0, 0, amount * (-1), 0)
                elif amount.symbol == self.blockchain.backed_token_symbol:
                    self.update(ts, 0, 0, 0, 0, amount * (-1))
            if op['to'] == self.account["name"]:
                if amount.symbol == self.blockchain.blockchain_symbol:
                    self.update(ts, 0, 0, 0, amount, 0)
                elif amount.symbol == self.blockchain.backed_token_symbol:
                    self.update(ts, 0, 0, 0, 0, amount)
            return

        elif op['type'] == "fill_order":
            current_pays = Amount(op["current_pays"], blockchain_instance=self.blockchain)
            open_pays = Amount(op["open_pays"], blockchain_instance=self.blockchain)
            if op["current_owner"] == self.account["name"]:
                if current_pays.symbol == self.blockchain.token_symbol:
                    self.update(ts, 0, 0, 0, current_pays * (-1), open_pays)
                elif current_pays.symbol == self.blockchain.backed_token_symbol:
                    self.update(ts, 0, 0, 0, open_pays, current_pays * (-1))
            if op["open_owner"] == self.account["name"]:
                if current_pays.symbol == self.blockchain.token_symbol:
                    self.update(ts, 0, 0, 0, current_pays, open_pays * (-1))
                elif current_pays.symbol == self.blockchain.backed_token_symbol:
                    self.update(ts, 0, 0, 0, open_pays * (-1), current_pays)
            return

        elif op['type'] == "transfer_to_vesting":
            steem = Amount(op['amount'], blockchain_instance=self.blockchain)
            from beem import Steem
            if isinstance(self.blockchain, Steem):
                vests = self.blockchain.sp_to_vests(steem.amount, timestamp=ts)
            else:
                vests = self.blockchain.hp_to_vests(steem.amount, timestamp=ts)
            if op['from'] == self.account["name"] and op['to'] == self.account["name"]:
                self.update(ts, vests, 0, 0, steem * (-1), 0)  # power up from and to given account
            elif op['from'] != self.account["name"] and op['to'] == self.account["name"]:
                self.update(ts, vests, 0, 0, 0, 0)  # power up from another account
            else:  # op['from'] == self.account["name"] and op['to'] != self.account["name"]
                self.update(ts, 0, 0, 0, steem * (-1), 0)  # power up to another account
            return

        elif op['type'] == "fill_vesting_withdraw":
            vests = Amount(op['withdrawn'], blockchain_instance=self.blockchain)
            self.update(ts, vests * (-1), 0, 0)
            return

        elif op['type'] == "return_vesting_delegation":
            delegation = {'account': None, 'amount':
                          Amount(op['vesting_shares'], blockchain_instance=self.blockchain)}
            self.update(ts, 0, 0, delegation)
            return

        elif op['type'] == "claim_reward_balance":
            vests = Amount(op['reward_vests'], blockchain_instance=self.blockchain)
            steem = Amount(op['reward_steem'], blockchain_instance=self.blockchain)
            sbd = Amount(op['reward_sbd'], blockchain_instance=self.blockchain)
            self.update(ts, vests, 0, 0, steem, sbd)
            return

        elif op['type'] == "curation_reward":
            if "curation_reward" in only_ops or enable_rewards:
                vests = Amount(op['reward'], blockchain_instance=self.blockchain)
            if "curation_reward" in only_ops:
                self.update(ts, vests, 0, 0)
            if enable_rewards:
                self.update_rewards(ts, vests, 0, 0, 0)
            return

        elif op['type'] == "author_reward":
            if "author_reward" in only_ops or enable_rewards:
                vests = Amount(op['vesting_payout'], blockchain_instance=self.blockchain)
                steem = Amount(op['steem_payout'], blockchain_instance=self.blockchain)
                sbd = Amount(op['sbd_payout'], blockchain_instance=self.blockchain)
            if "author_reward" in only_ops:
                self.update(ts, vests, 0, 0, steem, sbd)
            if enable_rewards:
                self.update_rewards(ts, 0, vests, steem, sbd)
            return

        elif op['type'] == "producer_reward":
            vests = Amount(op['vesting_shares'], blockchain_instance=self.blockchain)
            self.update(ts, vests, 0, 0)
            return

        elif op['type'] == "comment_benefactor_reward":
            if op['benefactor'] == self.account["name"]:
                if "reward" in op:
                    vests = Amount(op['reward'], blockchain_instance=self.blockchain)
                    self.update(ts, vests, 0, 0)
                else:
                    vests = Amount(op['vesting_payout'], blockchain_instance=self.blockchain)
                    steem = Amount(op['steem_payout'], blockchain_instance=self.blockchain)
                    sbd = Amount(op['sbd_payout'], blockchain_instance=self.blockchain)
                    self.update(ts, vests, 0, 0, steem, sbd)
                return
            else:
                return

        elif op['type'] == "fill_convert_request":
            amount_in = Amount(op["amount_in"], blockchain_instance=self.blockchain)
            amount_out = Amount(op["amount_out"], blockchain_instance=self.blockchain)
            if op["owner"] == self.account["name"]:
                self.update(ts, 0, 0, 0, amount_out, amount_in * (-1))
            return

        elif op['type'] == "interest":
            interest = Amount(op["interest"], blockchain_instance=self.blockchain)
            self.update(ts, 0, 0, 0, 0, interest)
            return

        elif op['type'] == "vote":
            if "vote" in only_ops or enable_out_votes:
                weight = int(op['weight'])
                if op["voter"] == self.account["name"]:
                    self.update_out_vote(ts, weight)
            if "vote" in only_ops or enable_in_votes and op["author"] == self.account["name"]:
                weight = int(op['weight'])
                self.update_in_vote(ts, weight, op)
            return

        elif op['type'] == 'hardfork_hive':
            vests = Amount(op['vests_converted'])
            hbd = Amount(op['steem_transferred'])
            hive = Amount(op['sbd_transferred'])
            self.update(ts, vests * (-1), 0, 0, hive * (-1), hbd * (-1))

        elif op['type'] in ['comment', 'feed_publish', 'shutdown_witness',
                            'account_witness_vote', 'witness_update', 'custom_json',
                            'limit_order_create', 'account_update',
                            'account_witness_proxy', 'limit_order_cancel', 'comment_options',
                            'delete_comment', 'interest', 'recover_account', 'pow',
                            'fill_convert_request', 'convert', 'request_account_recovery',
                            'update_proposal_votes']:
            return

    def build_sp_arrays(self):
        """ Builds the own_sp and eff_sp array"""
        self.own_sp = []
        self.eff_sp = []
        for (ts, own, din, dout) in zip(self.timestamps, self.own_vests,
                                        self.delegated_vests_in,
                                        self.delegated_vests_out):
            sum_in = sum([din[key].amount for key in din])
            sum_out = sum([dout[key].amount for key in dout])
            from beem import Steem
            if isinstance(self.blockchain, Steem):
                sp_in = self.blockchain.vests_to_sp(sum_in, timestamp=ts)
                sp_out = self.blockchain.vests_to_sp(sum_out, timestamp=ts)
                sp_own = self.blockchain.vests_to_sp(own, timestamp=ts)
            else:
                sp_in = self.blockchain.vests_to_hp(sum_in, timestamp=ts)
                sp_out = self.blockchain.vests_to_hp(sum_out, timestamp=ts)
                sp_own = self.blockchain.vests_to_hp(own, timestamp=ts)
                
            sp_eff = sp_own + sp_in - sp_out
            self.own_sp.append(sp_own)
            self.eff_sp.append(sp_eff)

    def build_rep_arrays(self):
        """ Build reputation arrays """
        self.rep_timestamp = [self.timestamps[1]]
        self.rep = [reputation_to_score(0)]
        current_reputation = 0
        for (ts, rshares, rep) in zip(self.in_vote_timestamp, self.in_vote_rshares, self.in_vote_rep):
            if rep > 0:
                if rshares > 0 or (rshares < 0 and rep > current_reputation):
                    current_reputation += rshares >> 6
            self.rep.append(reputation_to_score(current_reputation))
            self.rep_timestamp.append(ts)

    def build_vp_arrays(self):
        """ Build vote power arrays"""
        self.vp_timestamp = [self.timestamps[1]]
        self.vp = [STEEM_100_PERCENT]
        HF_21 = datetime(2019, 8, 27, 15, tzinfo=pytz.utc)
        if self.timestamps[1] > HF_21:
            self.downvote_vp_timestamp = [self.timestamps[1]]
        else:
            self.downvote_vp_timestamp = [HF_21]
        self.downvote_vp = [STEEM_100_PERCENT]

        for (ts, weight) in zip(self.out_vote_timestamp, self.out_vote_weight):
            regenerated_vp = 0
            if ts > HF_21 and weight < 0:
                self.downvote_vp.append(self.downvote_vp[-1])
                if self.downvote_vp[-1] < STEEM_100_PERCENT:
                    regenerated_vp = ((ts - self.downvote_vp_timestamp[-1]).total_seconds()) * STEEM_100_PERCENT / STEEM_VOTE_REGENERATION_SECONDS
                    self.downvote_vp[-1] += int(regenerated_vp)

                if self.downvote_vp[-1] > STEEM_100_PERCENT:
                    self.downvote_vp[-1] = STEEM_100_PERCENT
                    recharge_time = self.account.get_manabar_recharge_timedelta({"current_mana_pct": self.downvote_vp[-2] / 100})
                    # Add full downvote VP once fully charged
                    self.downvote_vp_timestamp.append(self.downvote_vp_timestamp[-1] + recharge_time)
                    self.downvote_vp.append(STEEM_100_PERCENT)

                # Add charged downvote VP just before new Vote
                self.downvote_vp_timestamp.append(ts-timedelta(seconds=1))
                self.downvote_vp.append(min([STEEM_100_PERCENT, self.downvote_vp[-1] + regenerated_vp]))

                self.downvote_vp[-1] -= self.blockchain._calc_resulting_vote(STEEM_100_PERCENT, weight) * 4
                # Downvote mana pool is 1/4th of the upvote mana pool, so it gets drained 4 times as quick
                if self.downvote_vp[-1] < 0:
                    # There's most likely a better solution to this that what I did here
                    self.vp.append(self.vp[-1])

                    if self.vp[-1] < STEEM_100_PERCENT:
                        regenerated_vp = ((ts - self.vp_timestamp[
                            -1]).total_seconds()) * STEEM_100_PERCENT / STEEM_VOTE_REGENERATION_SECONDS
                        self.vp[-1] += int(regenerated_vp)

                    if self.vp[-1] > STEEM_100_PERCENT:
                        self.vp[-1] = STEEM_100_PERCENT
                        recharge_time = self.account.get_manabar_recharge_timedelta(
                            {"current_mana_pct": self.vp[-2] / 100})
                        # Add full VP once fully charged
                        self.vp_timestamp.append(self.vp_timestamp[-1] + recharge_time)
                        self.vp.append(STEEM_100_PERCENT)
                    if self.vp[-1] == STEEM_100_PERCENT and ts - self.vp_timestamp[-1] > timedelta(seconds=1):
                        # Add charged VP just before new Vote
                        self.vp_timestamp.append(ts-timedelta(seconds=1))
                        self.vp.append(min([STEEM_100_PERCENT, self.vp[-1] + regenerated_vp]))
                    self.vp[-1] += self.downvote_vp[-1] / 4
                    if self.vp[-1] < 0:
                        self.vp[-1] = 0

                    self.vp_timestamp.append(ts)
                    self.downvote_vp[-1] = 0
                self.downvote_vp_timestamp.append(ts)

            else:
                self.vp.append(self.vp[-1])

                if self.vp[-1] < STEEM_100_PERCENT:
                    regenerated_vp = ((ts - self.vp_timestamp[-1]).total_seconds()) * STEEM_100_PERCENT / STEEM_VOTE_REGENERATION_SECONDS
                    self.vp[-1] += int(regenerated_vp)

                if self.vp[-1] > STEEM_100_PERCENT:
                    self.vp[-1] = STEEM_100_PERCENT
                    recharge_time = self.account.get_manabar_recharge_timedelta({"current_mana_pct": self.vp[-2] / 100})
                    # Add full VP once fully charged
                    self.vp_timestamp.append(self.vp_timestamp[-1] + recharge_time)
                    self.vp.append(STEEM_100_PERCENT)
                if self.vp[-1] == STEEM_100_PERCENT and ts - self.vp_timestamp[-1] > timedelta(seconds=1):
                    # Add charged VP just before new Vote
                    self.vp_timestamp.append(ts - timedelta(seconds=1))
                    self.vp.append(min([STEEM_100_PERCENT, self.vp[-1] + regenerated_vp]))
                self.vp[-1] -= self.blockchain._calc_resulting_vote(self.vp[-1], weight)
                if self.vp[-1] < 0:
                    self.vp[-1] = 0

                self.vp_timestamp.append(ts)

        if self.account.get_voting_power() == 100:
            self.vp.append(10000)
            recharge_time = self.account.get_manabar_recharge_timedelta({"current_mana_pct": self.vp[-2] / 100})
            self.vp_timestamp.append(self.vp_timestamp[-1] + recharge_time)

        if self.account.get_downvoting_power() == 100:
            self.downvote_vp.append(10000)
            recharge_time = self.account.get_manabar_recharge_timedelta(
                {"current_mana_pct": self.downvote_vp[-2] / 100})
            self.downvote_vp_timestamp.append(self.vp_timestamp[-1] + recharge_time)

        self.vp.append(self.account.get_voting_power() * 100)
        self.downvote_vp.append(self.account.get_downvoting_power() * 100)
        self.downvote_vp_timestamp.append(datetime.utcnow())
        self.vp_timestamp.append(datetime.utcnow())

    def build_curation_arrays(self, end_date=None, sum_days=7):
        """ Build curation arrays"""
        self.curation_per_1000_SP_timestamp = []
        self.curation_per_1000_SP = []
        if sum_days <= 0:
            raise ValueError("sum_days must be greater than 0")
        index = 0
        curation_sum = 0
        days = (self.reward_timestamps[-1] - self.reward_timestamps[0]).days // sum_days * sum_days
        if end_date is None:
            end_date = self.reward_timestamps[-1] - timedelta(days=days)
        for (ts, vests) in zip(self.reward_timestamps, self.curation_rewards):
            if vests == 0:
                continue
            from beem import Steem
            if isinstance(self.blockchain, Steem):
                sp = self.blockchain.vests_to_sp(vests, timestamp=ts)
            else:
                sp = self.blockchain.vests_to_hp(vests, timestamp=ts)
            data = self.get_data(timestamp=ts, index=index)
            index = data["index"]
            if "sp_eff" in data and data["sp_eff"] > 0:
                curation_1k_sp = sp / data["sp_eff"] * 1000 / sum_days * 7
            else:
                curation_1k_sp = 0
            if ts < end_date:
                curation_sum += curation_1k_sp
            else:
                self.curation_per_1000_SP_timestamp.append(end_date)
                self.curation_per_1000_SP.append(curation_sum)
                end_date = end_date + timedelta(days=sum_days)
                curation_sum = 0

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__, str(self.account["name"]))
