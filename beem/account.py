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
from prettytable import PrettyTable
from beem.instance import shared_steem_instance
from .exceptions import AccountDoesNotExistsException, OfflineHasNoRPCException
from beemapi.exceptions import ApiNotSupported, MissingRequiredActiveAuthority
from .blockchainobject import BlockchainObject
from .blockchain import Blockchain
from .utils import formatTimeString, formatTimedelta, remove_from_dict, reputation_to_score, addTzInfo
from beem.amount import Amount
from beembase import operations
from beem.rc import RC
from beemgraphenebase.account import PrivateKey, PublicKey, PasswordKey
from beemgraphenebase.py23 import bytes_types, integer_types, string_types, text_type
from beem.constants import STEEM_VOTE_REGENERATION_SECONDS, STEEM_1_PERCENT, STEEM_100_PERCENT, STEEM_VOTING_MANA_REGENERATION_SECONDS
log = logging.getLogger(__name__)


class Account(BlockchainObject):
    """ This class allows to easily access Account data

        :param str account_name: Name of the account
        :param Steem steem_instance: Steem
               instance
        :param bool lazy: Use lazy loading
        :param bool full: Obtain all account data including orders, positions,
               etc.
        :returns: Account data
        :rtype: dictionary
        :raises beem.exceptions.AccountDoesNotExistsException: if account
                does not exist

        Instances of this class are dictionaries that come with additional
        methods (see below) that allow dealing with an account and its
        corresponding functions.

        .. code-block:: python

            >>> from beem.account import Account
            >>> from beem import Steem
            >>> stm = Steem("https://steemd.minnowsupportproject.org")
            >>> account = Account("gtg", steem_instance=stm)
            >>> print(account)
            <Account gtg>
            >>> print(account.balances) # doctest: +SKIP

        .. note:: This class comes with its own caching function to reduce the
                  load on the API server. Instances of this class can be
                  refreshed with ``Account.refresh()``. The cache can be
                  cleared with ``Account.clear_cache()``

    """

    type_id = 2

    def __init__(
        self,
        account,
        full=True,
        lazy=False,
        steem_instance=None
    ):
        """Initialize an account

        :param str account: Name of the account
        :param Steem steem_instance: Steem
               instance
        :param bool lazy: Use lazy loading
        :param bool full: Obtain all account data including orders, positions,
               etc.
        """
        self.full = full
        self.lazy = lazy
        self.steem = steem_instance or shared_steem_instance()
        if isinstance(account, dict):
            account = self._parse_json_data(account)
        super(Account, self).__init__(
            account,
            lazy=lazy,
            full=full,
            id_item="name",
            steem_instance=steem_instance
        )

    def refresh(self):
        """ Refresh/Obtain an account's data from the API server
        """
        if not self.steem.is_connected():
            return
        self.steem.rpc.set_next_node_on_empty_reply(self.steem.rpc.get_use_appbase())
        if self.steem.rpc.get_use_appbase():
                account = self.steem.rpc.find_accounts({'accounts': [self.identifier]}, api="database")
        else:
            if self.full:
                account = self.steem.rpc.get_accounts(
                    [self.identifier], api="database")
            else:
                account = self.steem.rpc.lookup_account_names(
                    [self.identifier], api="database")
        if self.steem.rpc.get_use_appbase() and "accounts" in account:
            account = account["accounts"]
        if account and isinstance(account, list) and len(account) == 1:
            account = account[0]
        if not account:
            raise AccountDoesNotExistsException(self.identifier)
        account = self._parse_json_data(account)
        self.identifier = account["name"]
        # self.steem.refresh_data()

        super(Account, self).__init__(account, id_item="name", lazy=self.lazy, full=self.full, steem_instance=self.steem)

    def _parse_json_data(self, account):
        parse_int = [
            "sbd_seconds", "savings_sbd_seconds", "average_bandwidth", "lifetime_bandwidth", "lifetime_market_bandwidth", "reputation", "withdrawn", "to_withdraw",
        ]
        for p in parse_int:
            if p in account and isinstance(account.get(p), string_types):
                account[p] = int(account.get(p, 0))
        if "proxied_vsf_votes" in account:
            proxied_vsf_votes = []
            for p_int in account["proxied_vsf_votes"]:
                if isinstance(p_int, string_types):
                    proxied_vsf_votes.append(int(p_int))
                else:
                    proxied_vsf_votes.append(p_int)
            account["proxied_vsf_votes"] = proxied_vsf_votes
        parse_times = [
            "last_owner_update", "last_account_update", "created", "last_owner_proved", "last_active_proved",
            "last_account_recovery", "last_vote_time", "sbd_seconds_last_update", "sbd_last_interest_payment",
            "savings_sbd_seconds_last_update", "savings_sbd_last_interest_payment", "next_vesting_withdrawal",
            "last_market_bandwidth_update", "last_post", "last_root_post", "last_bandwidth_update"
        ]
        for p in parse_times:
            if p in account and isinstance(account.get(p), string_types):
                account[p] = formatTimeString(account.get(p, "1970-01-01T00:00:00"))
        # Parse Amounts
        amounts = [
            "balance",
            "savings_balance",
            "sbd_balance",
            "savings_sbd_balance",
            "reward_sbd_balance",
            "reward_steem_balance",
            "reward_vesting_balance",
            "reward_vesting_steem",
            "vesting_shares",
            "delegated_vesting_shares",
            "received_vesting_shares",
            "vesting_withdraw_rate",
            "vesting_balance",
        ]
        for p in amounts:
            if p in account and isinstance(account.get(p), (string_types, list, dict)):
                account[p] = Amount(account[p], steem_instance=self.steem)
        return account

    def json(self):
        output = self.copy()
        parse_int = [
            "sbd_seconds", "savings_sbd_seconds",
        ]
        parse_int_without_zero = [
            "withdrawn", "to_withdraw", "lifetime_bandwidth", 'average_bandwidth',
        ]
        for p in parse_int:
            if p in output and isinstance(output[p], integer_types):
                output[p] = str(output[p])
        for p in parse_int_without_zero:
            if p in output and isinstance(output[p], integer_types) and output[p] != 0:
                output[p] = str(output[p])
        if "proxied_vsf_votes" in output:
            proxied_vsf_votes = []
            for p_int in output["proxied_vsf_votes"]:
                if isinstance(p_int, integer_types) and p_int != 0:
                    proxied_vsf_votes.append(str(p_int))
                else:
                    proxied_vsf_votes.append(p_int)
            output["proxied_vsf_votes"] = proxied_vsf_votes
        parse_times = [
            "last_owner_update", "last_account_update", "created", "last_owner_proved", "last_active_proved",
            "last_account_recovery", "last_vote_time", "sbd_seconds_last_update", "sbd_last_interest_payment",
            "savings_sbd_seconds_last_update", "savings_sbd_last_interest_payment", "next_vesting_withdrawal",
            "last_market_bandwidth_update", "last_post", "last_root_post", "last_bandwidth_update"
        ]
        for p in parse_times:
            if p in output:
                p_date = output.get(p, datetime(1970, 1, 1, 0, 0))
                if isinstance(p_date, (datetime, date, time)):
                    output[p] = formatTimeString(p_date)
                else:
                    output[p] = p_date
        amounts = [
            "balance",
            "savings_balance",
            "sbd_balance",
            "savings_sbd_balance",
            "reward_sbd_balance",
            "reward_steem_balance",
            "reward_vesting_balance",
            "reward_vesting_steem",
            "vesting_shares",
            "delegated_vesting_shares",
            "received_vesting_shares",
            "vesting_withdraw_rate",
            "vesting_balance",
        ]
        for p in amounts:
            if p in output:
                if p in output:
                    output[p] = output.get(p).json()
        return json.loads(str(json.dumps(output)))

    def getSimilarAccountNames(self, limit=5):
        """Deprecated, please use get_similar_account_names"""
        return self.get_similar_account_names(limit=limit)

    def get_rc(self):
        """Return RC of account"""
        b = Blockchain(steem_instance=self.steem)
        return b.find_rc_accounts(self["name"])

    def get_rc_manabar(self):
        """Returns current_mana and max_mana for RC"""
        rc_param = self.get_rc()
        max_mana = int(rc_param["max_rc"])
        last_mana = int(rc_param["rc_manabar"]["current_mana"])
        last_update_time = rc_param["rc_manabar"]["last_update_time"]
        last_update = datetime.utcfromtimestamp(last_update_time)
        diff_in_seconds = (datetime.utcnow() - last_update).total_seconds()
        current_mana = int(last_mana + diff_in_seconds * max_mana / STEEM_VOTING_MANA_REGENERATION_SECONDS)
        if current_mana > max_mana:
            current_mana = max_mana
        if max_mana > 0:
            current_pct = current_mana / max_mana * 100
        else:
            current_pct = 0
        max_rc_creation_adjustment = Amount(rc_param["max_rc_creation_adjustment"], steem_instance=self.steem)
        return {"last_mana": last_mana, "last_update_time": last_update_time, "current_mana": current_mana,
                "max_mana": max_mana, "current_pct": current_pct, "max_rc_creation_adjustment": max_rc_creation_adjustment}

    def get_similar_account_names(self, limit=5):
        """ Returns ``limit`` account names similar to the current account
            name as a list

            :param int limit: limits the number of accounts, which will be
                returned
            :returns: Similar account names as list
            :rtype: list

            This is a wrapper around :func:`beem.blockchain.Blockchain.get_similar_account_names()`
            using the current account name as reference.

        """
        b = Blockchain(steem_instance=self.steem)
        return b.get_similar_account_names(self.name, limit=limit)

    @property
    def name(self):
        """ Returns the account name
        """
        return self["name"]

    @property
    def profile(self):
        """ Returns the account profile
        """
        metadata = self.json_metadata
        if "profile" in metadata:
            return metadata["profile"]
        else:
            return {}

    @property
    def rep(self):
        """ Returns the account reputation
        """
        return self.get_reputation()

    @property
    def sp(self):
        """ Returns the accounts Steem Power
        """
        return self.get_steem_power()

    @property
    def vp(self):
        """ Returns the account voting power in the range of 0-100%
        """
        return self.get_voting_power()

    @property
    def json_metadata(self):
        if self["json_metadata"] == '':
            return {}
        return json.loads(self["json_metadata"])

    def print_info(self, force_refresh=False, return_str=False, use_table=False, **kwargs):
        """ Prints import information about the account
        """
        if force_refresh:
            self.refresh()
            self.steem.refresh_data(True)
        bandwidth = self.get_bandwidth()
        if bandwidth["allocated"] > 0:
            remaining = 100 - bandwidth["used"] / bandwidth["allocated"] * 100
            used_kb = bandwidth["used"] / 1024
            allocated_mb = bandwidth["allocated"] / 1024 / 1024
        last_vote_time_str = formatTimedelta(addTzInfo(datetime.utcnow()) - self["last_vote_time"])
        try:
            rc_mana = self.get_rc_manabar()
            rc = self.get_rc()
            rc_calc = RC(steem_instance=self.steem)
        except:
            rc_mana = None
            rc_calc = None

        if use_table:
            t = PrettyTable(["Key", "Value"])
            t.align = "l"
            t.add_row(["Name (rep)", self.name + " (%.2f)" % (self.rep)])
            t.add_row(["Voting Power", "%.2f %%, " % (self.get_voting_power())])
            t.add_row(["Vote Value", "%.2f $" % (self.get_voting_value_SBD())])
            t.add_row(["Last vote", "%s ago" % last_vote_time_str])
            t.add_row(["Full in ", "%s" % (self.get_recharge_time_str())])
            t.add_row(["Steem Power", "%.2f %s" % (self.get_steem_power(), self.steem.steem_symbol)])
            t.add_row(["Balance", "%s, %s" % (str(self.balances["available"][0]), str(self.balances["available"][1]))])
            if False and bandwidth["allocated"] > 0:
                t.add_row(["Remaining Bandwidth", "%.2f %%" % (remaining)])
                t.add_row(["used/allocated Bandwidth", "(%.0f kb of %.0f mb)" % (used_kb, allocated_mb)])
            if rc_mana is not None:
                estimated_rc = int(rc["max_rc"]) * rc_mana["current_pct"] / 100
                t.add_row(["Remaining RC", "%.2f %%" % (rc_mana["current_pct"])])
                t.add_row(["Remaining RC", "(%.0f G RC of %.0f G RC)" % (estimated_rc / 10**9, int(rc["max_rc"]) / 10**9)])
                t.add_row(["Full in ", "%s" % (self.get_manabar_recharge_time_str(rc_mana))])
                t.add_row(["Est. RC for a comment", "%.2f G RC" % (rc_calc.comment() / 10**9)])
                t.add_row(["Est. RC for a vote", "%.2f G RC" % (rc_calc.vote() / 10**9)])
                t.add_row(["Est. RC for a transfer", "%.2f G RC" % (rc_calc.transfer() / 10**9)])
                t.add_row(["Est. RC for a custom_json", "%.2f G RC" % (rc_calc.custom_json() / 10**9)])

                t.add_row(["Comments with current RC", "%d comments" % (int(estimated_rc / rc_calc.comment()))])
                t.add_row(["Votes with current RC", "%d votes" % (int(estimated_rc / rc_calc.vote()))])
                t.add_row(["Transfer with current RC", "%d transfers" % (int(estimated_rc / rc_calc.transfer()))])
                t.add_row(["Custom_json with current RC", "%d transfers" % (int(estimated_rc / rc_calc.custom_json()))])

            if return_str:
                return t.get_string(**kwargs)
            else:
                print(t.get_string(**kwargs))
        else:
            ret = self.name + " (%.2f) \n" % (self.rep)
            ret += "--- Voting Power ---\n"
            ret += "%.2f %%, " % (self.get_voting_power())
            ret += " VP = %.2f $\n" % (self.get_voting_value_SBD())
            ret += "full in %s \n" % (self.get_recharge_time_str())
            ret += "--- Balance ---\n"
            ret += "%.2f SP, " % (self.get_steem_power())
            ret += "%s, %s\n" % (str(self.balances["available"][0]), str(self.balances["available"][1]))
            if False and bandwidth["allocated"] > 0:
                ret += "--- Bandwidth ---\n"
                ret += "Remaining: %.2f %%" % (remaining)
                ret += " (%.0f kb of %.0f mb)\n" % (used_kb, allocated_mb)
            if rc_mana is not None:
                estimated_rc = int(rc["max_rc"]) * rc_mana["current_pct"] / 100
                ret += "--- RC manabar ---\n"
                ret += "Remaining: %.2f %%" % (rc_mana["current_pct"])
                ret += " (%.0f G RC of %.0f G RC)\n" % (estimated_rc / 10**9, int(rc["max_rc"]) / 10**9)
                ret += "full in %s\n" % (self.get_manabar_recharge_time_str(rc_mana))
                ret += "--- Approx Costs ---\n"
                ret += "comment - %.2f G RC - enough RC for %d comments\n" % (rc_calc.comment() / 10**9, int(estimated_rc / rc_calc.comment()))
                ret += "vote - %.2f G RC - enough RC for %d votes\n" % (rc_calc.vote() / 10**9, int(estimated_rc / rc_calc.vote()))
                ret += "transfer - %.2f G RC - enough RC for %d transfers\n" % (rc_calc.transfer() / 10**9, int(estimated_rc / rc_calc.transfer()))
                ret += "custom_json - %.2f G RC - enough RC for %d custom_json\n" % (rc_calc.custom_json() / 10**9, int(estimated_rc / rc_calc.custom_json()))
            if return_str:
                return ret
            print(ret)

    def get_reputation(self):
        """ Returns the account reputation in the (steemit) normalized form
        """
        if not self.steem.is_connected():
            return None
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            rep = self.steem.rpc.get_account_reputations({'account_lower_bound': self["name"], 'limit': 1}, api="follow")['reputations']
            if len(rep) > 0:
                rep = int(rep[0]['reputation'])
        else:
            rep = int(self['reputation'])
        return reputation_to_score(rep)

    def get_manabar(self):
        """ Return manabar
        """
        max_mana = self.get_effective_vesting_shares()
        if max_mana == 0:
            props = self.steem.get_chain_properties()
            required_fee_steem = Amount(props["account_creation_fee"], steem_instance=self.steem)
            max_mana = int(self.steem.sp_to_vests(required_fee_steem))
        last_mana = int(self["voting_manabar"]["current_mana"])
        last_update_time = self["voting_manabar"]["last_update_time"]
        last_update = datetime.utcfromtimestamp(last_update_time)
        diff_in_seconds = (addTzInfo(datetime.utcnow()) - addTzInfo(last_update)).total_seconds()
        current_mana = int(last_mana + diff_in_seconds * max_mana / STEEM_VOTING_MANA_REGENERATION_SECONDS)
        if current_mana > max_mana:
            current_mana = max_mana
        if max_mana > 0:
            current_mana_pct = current_mana / max_mana * 100
        else:
            current_mana_pct = 0
        return {"last_mana": last_mana, "last_update_time": last_update_time,
                "current_mana": current_mana, "max_mana": max_mana, "current_mana_pct": current_mana_pct}

    def get_voting_power(self, with_regeneration=True):
        """ Returns the account voting power in the range of 0-100%
        """
        if "voting_manabar" in self:
            manabar = self.get_manabar()
            if with_regeneration:
                total_vp = manabar["current_mana_pct"]
            else:
                if manabar["max_mana"] > 0:
                    total_vp = manabar["last_mana"] / manabar["max_mana"] * 100
                else:
                    total_vp = 0
        elif "voting_power" in self:
            if with_regeneration:
                last_vote_time = self["last_vote_time"]
                diff_in_seconds = (addTzInfo(datetime.utcnow()) - (last_vote_time)).total_seconds()
                regenerated_vp = diff_in_seconds * STEEM_100_PERCENT / STEEM_VOTE_REGENERATION_SECONDS / 100
            else:
                regenerated_vp = 0
            total_vp = (self["voting_power"] / 100 + regenerated_vp)
        if total_vp > 100:
            return 100
        if total_vp < 0:
            return 0
        return total_vp

    def get_vests(self, only_own_vests=False):
        """ Returns the account vests
        """
        vests = (self["vesting_shares"])
        if not only_own_vests and "delegated_vesting_shares" in self and "received_vesting_shares" in self:
            vests = vests - (self["delegated_vesting_shares"]) + (self["received_vesting_shares"])

        return vests

    def get_effective_vesting_shares(self):
        """Returns the effective vesting shares"""
        vesting_shares = int(self["vesting_shares"])
        if "delegated_vesting_shares" in self and "received_vesting_shares" in self:
            vesting_shares = vesting_shares - int(self["delegated_vesting_shares"]) + int(self["received_vesting_shares"])
        timestamp = (self["next_vesting_withdrawal"] - addTzInfo(datetime(1970, 1, 1))).total_seconds()
        if timestamp > 0 and "vesting_withdraw_rate" in self and "to_withdraw" in self and "withdrawn" in self:
            vesting_shares -= min(int(self["vesting_withdraw_rate"]), int(self["to_withdraw"]) - int(self["withdrawn"]))
        return vesting_shares

    def get_steem_power(self, onlyOwnSP=False):
        """ Returns the account steem power
        """
        return self.steem.vests_to_sp(self.get_vests(only_own_vests=onlyOwnSP))

    def get_voting_value_SBD(self, voting_weight=100, voting_power=None, steem_power=None, not_broadcasted_vote=True):
        """ Returns the account voting value in SBD
        """
        if voting_power is None:
            voting_power = self.get_voting_power()
        if steem_power is None:
            sp = self.get_steem_power()
        else:
            sp = steem_power

        VoteValue = self.steem.sp_to_sbd(sp, voting_power=voting_power * 100, vote_pct=voting_weight * 100, not_broadcasted_vote=not_broadcasted_vote)
        return VoteValue

    def get_vote_pct_for_SBD(self, sbd, voting_power=None, steem_power=None, not_broadcasted_vote=True):
        """ Returns the voting percentage needed to have a vote worth a given number of SBD.

            If the returned number is bigger than 10000 or smaller than -10000,
            the given SBD value is too high for that account

            :param sbd: The amount of SBD in vote value
            :type sbd: str, int, amount.Amount

        """
        if voting_power is None:
            voting_power = self.get_voting_power()
        if steem_power is None:
            steem_power = self.get_steem_power()

        if isinstance(sbd, Amount):
            sbd = Amount(sbd, steem_instance=self.steem)
        elif isinstance(sbd, string_types):
            sbd = Amount(sbd, steem_instance=self.steem)
        else:
            sbd = Amount(sbd, self.steem.sbd_symbol, steem_instance=self.steem)
        if sbd['symbol'] != self.steem.sbd_symbol:
            raise AssertionError('Should input SBD, not any other asset!')

        vote_pct = self.steem.rshares_to_vote_pct(self.steem.sbd_to_rshares(sbd, not_broadcasted_vote=not_broadcasted_vote), voting_power=voting_power * 100, steem_power=steem_power)
        return vote_pct

    def get_creator(self):
        """ Returns the account creator or `None` if the account was mined
        """
        if self['mined']:
            return None
        ops = list(self.get_account_history(0, 0))
        if not ops or 'creator' not in ops[0]:
            return None
        return ops[0]['creator']

    def get_recharge_time_str(self, voting_power_goal=100, starting_voting_power=None):
        """ Returns the account recharge time as string

            :param float voting_power_goal: voting power goal in percentage (default is 100)
            :param float starting_voting_power: returns recharge time if current voting power is
                the provided value.

        """
        remainingTime = self.get_recharge_timedelta(voting_power_goal=voting_power_goal, starting_voting_power=starting_voting_power)
        return formatTimedelta(remainingTime)

    def get_recharge_timedelta(self, voting_power_goal=100, starting_voting_power=None):
        """ Returns the account voting power recharge time as timedelta object

            :param float voting_power_goal: voting power goal in percentage (default is 100)
            :param float starting_voting_power: returns recharge time if current voting power is
                the provided value.

        """
        if starting_voting_power is None:
            missing_vp = voting_power_goal - self.get_voting_power()
        elif isinstance(starting_voting_power, int) or isinstance(starting_voting_power, float):
            missing_vp = voting_power_goal - starting_voting_power
        else:
            raise ValueError('starting_voting_power must be a number.')
        if missing_vp < 0:
            return 0
        recharge_seconds = missing_vp * 100 * STEEM_VOTING_MANA_REGENERATION_SECONDS / STEEM_100_PERCENT
        return timedelta(seconds=recharge_seconds)

    def get_recharge_time(self, voting_power_goal=100, starting_voting_power=None):
        """ Returns the account voting power recharge time in minutes

            :param float voting_power_goal: voting power goal in percentage (default is 100)
            :param float starting_voting_power: returns recharge time if current voting power is
                the provided value.

        """
        return addTzInfo(datetime.utcnow()) + self.get_recharge_timedelta(voting_power_goal, starting_voting_power)

    def get_manabar_recharge_time_str(self, manabar, recharge_pct_goal=100):
        """ Returns the account manabar recharge time as string

            :param dict manabar: manabar dict from get_manabar() or get_rc_manabar()
            :param float recharge_pct_goal: mana recovery goal in percentage (default is 100)

        """
        remainingTime = self.get_manabar_recharge_timedelta(manabar, recharge_pct_goal=recharge_pct_goal)
        return formatTimedelta(remainingTime)

    def get_manabar_recharge_timedelta(self, manabar, recharge_pct_goal=100):
        """ Returns the account mana recharge time as timedelta object

            :param dict manabar: manabar dict from get_manabar() or get_rc_manabar()
            :param float recharge_pct_goal: mana recovery goal in percentage (default is 100)

        """
        if "current_mana_pct" in manabar:
            missing_rc_pct = recharge_pct_goal - manabar["current_mana_pct"]
        else:
            missing_rc_pct = recharge_pct_goal - manabar["current_pct"]
        if missing_rc_pct < 0:
            return 0
        recharge_seconds = missing_rc_pct * 100 * STEEM_VOTING_MANA_REGENERATION_SECONDS / STEEM_100_PERCENT
        return timedelta(seconds=recharge_seconds)

    def get_manabar_recharge_time(self, manabar, recharge_pct_goal=100):
        """ Returns the account mana recharge time in minutes

            :param dict manabar: manabar dict from get_manabar() or get_rc_manabar()
            :param float recharge_pct_goal: mana recovery goal in percentage (default is 100)

        """
        return addTzInfo(datetime.utcnow()) + self.get_manabar_recharge_timedelta(manabar, recharge_pct_goal)

    def get_feed(self, start_entry_id=0, limit=100, raw_data=False, short_entries=False, account=None):
        """ Returns a list of items in an account’s feed

            :param int start_entry_id: default is 0
            :param int limit: default is 100
            :param bool raw_data: default is False
            :param bool short_entries: when set to True and raw_data is True, get_feed_entries is used istead of get_feed
            :param str account: When set, a different account name is used (Default is object account name)

            :rtype: list

            .. code-block:: python

                >>> from beem.account import Account
                >>> from beem import Steem
                >>> stm = Steem("https://steemd.minnowsupportproject.org")
                >>> account = Account("steemit", steem_instance=stm)
                >>> account.get_feed(0, 1, raw_data=True)
                []

        """
        if account is None:
            account = self["name"]
        elif isinstance(account, Account):
            account = account["name"]
        if not self.steem.is_connected():
            return None
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if raw_data and short_entries and self.steem.rpc.get_use_appbase():
            return [
                c for c in self.steem.rpc.get_feed_entries({'account': account, 'start_entry_id': start_entry_id, 'limit': limit}, api='follow')["feed"]
            ]
        elif raw_data and short_entries and not self.steem.rpc.get_use_appbase():
            return [
                c for c in self.steem.rpc.get_feed_entries(account, start_entry_id, limit, api='follow')
            ]
        elif raw_data and self.steem.rpc.get_use_appbase():
            return [
                c for c in self.steem.rpc.get_feed({'account': account, 'start_entry_id': start_entry_id, 'limit': limit}, api='follow')["feed"]
            ]
        elif raw_data and not self.steem.rpc.get_use_appbase():
            return [
                c for c in self.steem.rpc.get_feed(account, start_entry_id, limit, api='follow')
            ]
        elif not raw_data and self.steem.rpc.get_use_appbase():
            from .comment import Comment
            return [
                Comment(c['comment'], steem_instance=self.steem) for c in self.steem.rpc.get_feed({'account': account, 'start_entry_id': start_entry_id, 'limit': limit}, api='follow')["feed"]
            ]
        else:
            from .comment import Comment
            return [
                Comment(c['comment'], steem_instance=self.steem) for c in self.steem.rpc.get_feed(account, start_entry_id, limit, api='follow')
            ]

    def get_feed_entries(self, start_entry_id=0, limit=100, raw_data=True,
                         account=None):
        """ Returns a list of entries in an account’s feed

            :param int start_entry_id: default is 0
            :param int limit: default is 100
            :param bool raw_data: default is False
            :param bool short_entries: when set to True and raw_data is True, get_feed_entries is used istead of get_feed
            :param str account: When set, a different account name is used (Default is object account name)

            :rtype: list

            .. code-block:: python

                >>> from beem.account import Account
                >>> from beem import Steem
                >>> stm = Steem("https://steemd.minnowsupportproject.org")
                >>> account = Account("steemit", steem_instance=stm)
                >>> account.get_feed_entries(0, 1)
                []

        """
        return self.get_feed(start_entry_id=start_entry_id, limit=limit, raw_data=raw_data, short_entries=True, account=account)

    def get_blog_entries(self, start_entry_id=0, limit=100, raw_data=True,
                         account=None):
        """ Returns the list of blog entries for an account

            :param int start_entry_id: default is 0
            :param int limit: default is 100
            :param bool raw_data: default is False
            :param str account: When set, a different account name is used (Default is object account name)

            :rtype: list

            .. code-block:: python

                >>> from beem.account import Account
                >>> from beem import Steem
                >>> stm = Steem("https://steemd.minnowsupportproject.org")
                >>> account = Account("steemit", steem_instance=stm)
                >>> entry = account.get_blog_entries(0, 1, raw_data=True)[0]
                >>> print("%s - %s - %s - %s" % (entry["author"], entry["permlink"], entry["blog"], entry["reblog_on"]))
                steemit - firstpost - steemit - 1970-01-01T00:00:00

        """
        return self.get_blog(start_entry_id=start_entry_id, limit=limit, raw_data=raw_data, short_entries=True, account=account)

    def get_blog(self, start_entry_id=0, limit=100, raw_data=False, short_entries=False, account=None):
        """ Returns the list of blog entries for an account

            :param int start_entry_id: default is 0
            :param int limit: default is 100
            :param bool raw_data: default is False
            :param bool short_entries: when set to True and raw_data is True, get_blog_entries is used istead of get_blog
            :param str account: When set, a different account name is used (Default is object account name)

            :rtype: list

            .. code-block:: python

                >>> from beem.account import Account
                >>> from beem import Steem
                >>> stm = Steem("https://steemd.minnowsupportproject.org")
                >>> account = Account("steemit", steem_instance=stm)
                >>> account.get_blog(0, 1)
                [<Comment @steemit/firstpost>]

        """
        if account is None:
            account = self["name"]
        elif isinstance(account, Account):
            account = account["name"]
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if raw_data and short_entries and self.steem.rpc.get_use_appbase():
            ret = self.steem.rpc.get_blog_entries({'account': account, 'start_entry_id': start_entry_id, 'limit': limit}, api='follow')
            if isinstance(ret, dict) and "blog" in ret:
                ret = ret["blog"]
            return [
                c for c in ret
            ]
        elif raw_data and short_entries and not self.steem.rpc.get_use_appbase():
            return [
                c for c in self.steem.rpc.get_blog_entries(account, start_entry_id, limit, api='follow')
            ]
        elif raw_data and self.steem.rpc.get_use_appbase():
            ret = self.steem.rpc.get_blog({'account': account, 'start_entry_id': start_entry_id, 'limit': limit}, api='follow')
            if isinstance(ret, dict) and "blog" in ret:
                ret = ret["blog"]            
            return [
                c for c in ret
            ]
        elif raw_data and not self.steem.rpc.get_use_appbase():
            return [
                c for c in self.steem.rpc.get_blog(account, start_entry_id, limit, api='follow')
            ]
        elif not raw_data and self.steem.rpc.get_use_appbase():
            from .comment import Comment
            ret = self.steem.rpc.get_blog({'account': account, 'start_entry_id': start_entry_id, 'limit': limit}, api='follow')
            if isinstance(ret, dict) and "blog" in ret:
                ret = ret["blog"]
            return [
                Comment(c["comment"], steem_instance=self.steem) for c in ret
            ]                
        else:
            from .comment import Comment
            return [
                Comment(c["comment"], steem_instance=self.steem) for c in self.steem.rpc.get_blog(account, start_entry_id, limit, api='follow')
            ]

    def get_blog_authors(self, account=None):
        """ Returns a list of authors that have had their content reblogged on a given blog account

            :param str account: When set, a different account name is used (Default is object account name)

            :rtype: list

            .. code-block:: python

                >>> from beem.account import Account
                >>> from beem import Steem
                >>> stm = Steem("https://steemd.minnowsupportproject.org")
                >>> account = Account("steemit", steem_instance=stm)
                >>> account.get_blog_authors()
                []

        """
        if account is None:
            account = self["name"]
        elif isinstance(account, Account):
            account = account["name"]
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            return self.steem.rpc.get_blog_authors({'blog_account': account}, api='follow')['blog_authors']
        else:
            return self.steem.rpc.get_blog_authors(account, api='follow')

    def get_follow_count(self, account=None):
        """ get_follow_count """
        if account is None:
            account = self["name"]
        elif isinstance(account, Account):
            account = account["name"]
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            return self.steem.rpc.get_follow_count({'account': account}, api='follow')
        else:
            return self.steem.rpc.get_follow_count(account, api='follow')

    def get_followers(self, raw_name_list=True, limit=100):
        """ Returns the account followers as list
        """
        name_list = [x['follower'] for x in self._get_followers(direction="follower", limit=limit)]
        if raw_name_list:
            return name_list
        else:
            return Accounts(name_list, steem_instance=self.steem)

    def get_following(self, raw_name_list=True, limit=100):
        """ Returns who the account is following as list
        """
        name_list = [x['following'] for x in self._get_followers(direction="following", limit=limit)]
        if raw_name_list:
            return name_list
        else:
            return Accounts(name_list, steem_instance=self.steem)

    def get_muters(self, raw_name_list=True, limit=100):
        """ Returns the account muters as list
        """
        name_list = [x['follower'] for x in self._get_followers(direction="follower", what="ignore", limit=limit)]
        if raw_name_list:
            return name_list
        else:
            return Accounts(name_list, steem_instance=self.steem)

    def get_mutings(self, raw_name_list=True, limit=100):
        """ Returns who the account is muting as list
        """
        name_list = [x['following'] for x in self._get_followers(direction="following", what="ignore", limit=limit)]
        if raw_name_list:
            return name_list
        else:
            return Accounts(name_list, steem_instance=self.steem)

    def _get_followers(self, direction="follower", last_user="", what="blog", limit=100):
        """ Help function, used in get_followers and get_following
        """
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        followers_list = []
        limit_reached = True
        cnt = 0
        while limit_reached:
            self.steem.rpc.set_next_node_on_empty_reply(False)
            if self.steem.rpc.get_use_appbase():
                query = {'account': self.name, 'start': last_user, 'type': what, 'limit': limit}
                if direction == "follower":
                    followers = self.steem.rpc.get_followers(query, api='follow')
                    if isinstance(followers, dict) and 'followers' in followers:
                        followers = followers['followers']
                elif direction == "following":
                    followers = self.steem.rpc.get_following(query, api='follow')
                    if isinstance(followers, dict) and 'following' in followers:
                        followers = followers['following']         
            else:
                if direction == "follower":
                    followers = self.steem.rpc.get_followers(self.name, last_user, what, limit, api='follow')
                elif direction == "following":
                    followers = self.steem.rpc.get_following(self.name, last_user, what, limit, api='follow')
            if cnt == 0:
                followers_list = followers
            elif len(followers) > 1:
                followers_list += followers[1:]
            if len(followers) >= limit:
                last_user = followers[-1][direction]
                limit_reached = True
                cnt += 1
            else:
                limit_reached = False

        return followers_list

    @property
    def available_balances(self):
        """ List balances of an account. This call returns instances of
            :class:`beem.amount.Amount`.
        """
        amount_list = ["balance", "sbd_balance", "vesting_shares"]
        available_amount = []
        for amount in amount_list:
            if amount in self:
                available_amount.append(self[amount])
        return available_amount

    @property
    def saving_balances(self):
        savings_amount = []
        amount_list = ["savings_balance", "savings_sbd_balance"]
        for amount in amount_list:
            if amount in self:
                savings_amount.append(self[amount])
        return savings_amount

    @property
    def reward_balances(self):
        amount_list = ["reward_steem_balance", "reward_sbd_balance", "reward_vesting_balance"]
        rewards_amount = []
        for amount in amount_list:
            if amount in self:
                rewards_amount.append(self[amount])
        return rewards_amount

    @property
    def total_balances(self):
        symbols = []
        for balance in self.available_balances:
            symbols.append(balance["symbol"])
        ret = []
        for i in range(len(symbols)):
            balance_sum = self.get_balance(self.available_balances, symbols[i])
            balance_sum += self.get_balance(self.saving_balances, symbols[i])
            balance_sum += self.get_balance(self.reward_balances, symbols[i])
            ret.append(balance_sum)
        return ret

    @property
    def balances(self):
        """ Returns all account balances as dictionary
        """
        return self.get_balances()

    def get_balances(self):
        """ Returns all account balances as dictionary

            :returns: Account balances
            :rtype: dictionary

            Sample output:

                .. code-block:: js

                    {
                        'available': [102.985 STEEM, 0.008 SBD, 146273.695970 VESTS],
                        'savings': [0.000 STEEM, 0.000 SBD],
                        'rewards': [0.000 STEEM, 0.000 SBD, 0.000000 VESTS],
                        'total': [102.985 STEEM, 0.008 SBD, 146273.695970 VESTS]
                    }

        """
        return {
            'available': self.available_balances,
            'savings': self.saving_balances,
            'rewards': self.reward_balances,
            'total': self.total_balances,
        }

    def get_balance(self, balances, symbol):
        """ Obtain the balance of a specific Asset. This call returns instances of
            :class:`beem.amount.Amount`. Available balance types:

            * "available"
            * "saving"
            * "reward"
            * "total"

            :param str balances: Defines the balance type
            :param symbol: Can be "SBD", "STEEM" or "VESTS
            :type symbol: str, dict

            .. code-block:: python

                >>> from beem.account import Account
                >>> account = Account("beem.app")
                >>> account.get_balance("rewards", "SBD")
                0.000 SBD

        """
        if isinstance(balances, string_types):
            if balances == "available":
                balances = self.available_balances
            elif balances == "savings":
                balances = self.saving_balances
            elif balances == "rewards":
                balances = self.reward_balances
            elif balances == "total":
                balances = self.total_balances
            else:
                return
        from .amount import Amount
        if isinstance(symbol, dict) and "symbol" in symbol:
            symbol = symbol["symbol"]

        for b in balances:
            if b["symbol"] == symbol:
                return b
        return Amount(0, symbol, steem_instance=self.steem)

    def interest(self):
        """ Calculate interest for an account

            :param str account: Account name to get interest for
            :rtype: dictionary

            Sample output:

            .. code-block:: js

                {
                    'interest': 0.0,
                    'last_payment': datetime.datetime(2018, 1, 26, 5, 50, 27, tzinfo=<UTC>),
                    'next_payment': datetime.datetime(2018, 2, 25, 5, 50, 27, tzinfo=<UTC>),
                    'next_payment_duration': datetime.timedelta(-65, 52132, 684026),
                    'interest_rate': 0.0
                }

        """
        last_payment = (self["sbd_last_interest_payment"])
        next_payment = last_payment + timedelta(days=30)
        interest_rate = self.steem.get_dynamic_global_properties()[
            "sbd_interest_rate"] / 100  # percent
        interest_amount = (interest_rate / 100) * int(
            int(self["sbd_seconds"]) / (60 * 60 * 24 * 356)) * 10**-3
        return {
            "interest": interest_amount,
            "last_payment": last_payment,
            "next_payment": next_payment,
            "next_payment_duration": next_payment - addTzInfo(datetime.utcnow()),
            "interest_rate": interest_rate,
        }

    @property
    def is_fully_loaded(self):
        """ Is this instance fully loaded / e.g. all data available?

            :rtype: bool
        """
        return (self.full)

    def ensure_full(self):
        """Ensure that all data are loaded"""
        if not self.is_fully_loaded:
            self.full = True
            self.refresh()

    def get_account_bandwidth(self, bandwidth_type=1, account=None):
        """ get_account_bandwidth """
        if account is None:
            account = self["name"]
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            # return self.steem.rpc.get_account_bandwidth({'account': account, 'type': 'post'}, api="witness")
            return self.steem.rpc.get_account_bandwidth(account, bandwidth_type)
        else:
            return self.steem.rpc.get_account_bandwidth(account, bandwidth_type)

    def get_bandwidth(self):
        """ Returns used and allocated bandwidth

            :rtype: dictionary

            Sample output:

                .. code-block:: js

                    {
                        'used': 0,
                        'allocated': 2211037
                    }

        """
        account = self["name"]
        global_properties = self.steem.get_dynamic_global_properties()
        try:
            reserve_ratio = self.steem.get_reserve_ratio()
        except:
            return {"used": 0,
                    "allocated": 0}
        if "received_vesting_shares" in self:
            received_vesting_shares = self["received_vesting_shares"].amount
        else:
            received_vesting_shares = 0
        vesting_shares = self["vesting_shares"].amount
        max_virtual_bandwidth = float(reserve_ratio["max_virtual_bandwidth"])
        total_vesting_shares = Amount(global_properties["total_vesting_shares"], steem_instance=self.steem).amount
        allocated_bandwidth = (max_virtual_bandwidth * (vesting_shares + received_vesting_shares) / total_vesting_shares)
        allocated_bandwidth = round(allocated_bandwidth / 1000000)

        if not not self.steem.is_connected() and self.steem.rpc.get_use_appbase():
            account_bandwidth = self.get_account_bandwidth(bandwidth_type=1, account=account)
            if account_bandwidth is None:
                return {"used": 0,
                        "allocated": allocated_bandwidth}
            last_bandwidth_update = formatTimeString(account_bandwidth["last_bandwidth_update"])
            average_bandwidth = float(account_bandwidth["average_bandwidth"])
        else:
            last_bandwidth_update = (self["last_bandwidth_update"])
            average_bandwidth = float(self["average_bandwidth"])
        total_seconds = 604800

        seconds_since_last_update = addTzInfo(datetime.utcnow()) - last_bandwidth_update
        seconds_since_last_update = seconds_since_last_update.total_seconds()
        used_bandwidth = 0
        if seconds_since_last_update < total_seconds:
            used_bandwidth = (((total_seconds - seconds_since_last_update) * average_bandwidth) / total_seconds)
        used_bandwidth = round(used_bandwidth / 1000000)

        return {"used": used_bandwidth,
                "allocated": allocated_bandwidth}
        # print("bandwidth percent used: " + str(100 * used_bandwidth / allocated_bandwidth))
        # print("bandwidth percent remaining: " + str(100 - (100 * used_bandwidth / allocated_bandwidth)))

    def get_owner_history(self, account=None):
        """ Returns the owner history of an account.

            :param str account: When set, a different account is used for the request (Default is object account name)

            :rtype: list

            .. code-block:: python

                >>> from beem.account import Account
                >>> account = Account("beem.app")
                >>> account.get_owner_history()
                []

        """
        if account is None:
            account = self["name"]
        elif isinstance(account, Account):
            account = account["name"]
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            return self.steem.rpc.find_owner_histories({'owner': account}, api="database")['owner_auths']
        else:
            return self.steem.rpc.get_owner_history(account)

    def get_conversion_requests(self, account=None):
        """ Returns a list of SBD conversion request

            :param str account: When set, a different account is used for the request (Default is object account name)

            :rtype: list

            .. code-block:: python

                >>> from beem.account import Account
                >>> account = Account("beem.app")
                >>> account.get_conversion_requests()
                []

        """
        if account is None:
            account = self["name"]
        elif isinstance(account, Account):
            account = account["name"]
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            return self.steem.rpc.find_sbd_conversion_requests({'account': account}, api="database")['requests']
        else:
            return self.steem.rpc.get_conversion_requests(account)

    def get_vesting_delegations(self, start_account="", limit=100, account=None):
        """ Returns the vesting delegations by an account.

            :param str account: When set, a different account is used for the request (Default is object account name)
            :param str start_account: delegatee to start with, leave empty to start from the first by name
            :param int limit: maximum number of results to return
            :rtype: list

            .. code-block:: python

                >>> from beem.account import Account
                >>> account = Account("beem.app")
                >>> account.get_vesting_delegations()
                []

        """
        if account is None:
            account = self["name"]
        elif isinstance(account, Account):
            account = account["name"]
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            delegations = self.steem.rpc.list_vesting_delegations(
                {'start': [account, start_account], 'limit': limit,
                 'order': 'by_delegation'}, api="database")['delegations']
            return [d for d in delegations if d['delegator'] == account]
        else:
            return self.steem.rpc.get_vesting_delegations(account, start_account, limit)

    def get_withdraw_routes(self, account=None):
        """ Returns the withdraw routes for an account.

            :param str account: When set, a different account is used for the request (Default is object account name)

            :rtype: list

            .. code-block:: python

                >>> from beem.account import Account
                >>> account = Account("beem.app")
                >>> account.get_withdraw_routes()
                []

        """
        if account is None:
            account = self["name"]
        elif isinstance(account, Account):
            account = account["name"]
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            return self.steem.rpc.find_withdraw_vesting_routes({'account': account, 'order': 'by_withdraw_route'}, api="database")['routes']
        else:
            return self.steem.rpc.get_withdraw_routes(account, 'all')

    def get_savings_withdrawals(self, direction="from", account=None):
        """ Returns the list of savings withdrawls for an account.

            :param str account: When set, a different account is used for the request (Default is object account name)
            :param str direction: Can be either from or to (only non appbase nodes)

            :rtype: list

            .. code-block:: python

                >>> from beem.account import Account
                >>> account = Account("beem.app")
                >>> account.get_savings_withdrawals()
                []

        """
        if account is None:
            account = self["name"]
        elif isinstance(account, Account):
            account = account["name"]
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            return self.steem.rpc.find_savings_withdrawals({'account': account}, api="database")['withdrawals']
        elif direction == "from":
            return self.steem.rpc.get_savings_withdraw_from(account)
        elif direction == "to":
            return self.steem.rpc.get_savings_withdraw_to(account)

    def get_recovery_request(self, account=None):
        """ Returns the recovery request for an account

            :param str account: When set, a different account is used for the request (Default is object account name)

            :rtype: list

            .. code-block:: python

                >>> from beem.account import Account
                >>> account = Account("beem.app")
                >>> account.get_recovery_request()
                []

        """
        if account is None:
            account = self["name"]
        elif isinstance(account, Account):
            account = account["name"]
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            return self.steem.rpc.find_account_recovery_requests({'account': account}, api="database")['requests']
        else:
            return self.steem.rpc.get_recovery_request(account)

    def get_escrow(self, escrow_id=0, account=None):
        """ Returns the escrow for a certain account by id

            :param int escrow_id: Id (only pre appbase)
            :param str account: When set, a different account is used for the request (Default is object account name)

            :rtype: list

            .. code-block:: python

                >>> from beem.account import Account
                >>> account = Account("beem.app")
                >>> account.get_escrow(1234)
                []

        """
        if account is None:
            account = self["name"]
        elif isinstance(account, Account):
            account = account["name"]
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            return self.steem.rpc.find_escrows({'from': account}, api="database")['escrows']
        else:
            return self.steem.rpc.get_escrow(account, escrow_id)

    def verify_account_authority(self, keys, account=None):
        """ Returns true if the signers have enough authority to authorize an account.

            :param list keys: public key
            :param str account: When set, a different account is used for the request (Default is object account name)

            :rtype: dictionary

            .. code-block:: python

                >>> from beem.account import Account
                >>> account = Account("steemit")
                >>> print(account.verify_account_authority(["STM7Q2rLBqzPzFeteQZewv9Lu3NLE69fZoLeL6YK59t7UmssCBNTU"])["valid"])
                False

        """
        if account is None:
            account = self["name"]
        elif isinstance(account, Account):
            account = account["name"]
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        if not isinstance(keys, list):
            keys = [keys]
        self.steem.rpc.set_next_node_on_empty_reply(False)
        try:
            if self.steem.rpc.get_use_appbase():
                return self.steem.rpc.verify_account_authority({'account': account, 'signers': keys}, api="database")
            else:
                return self.steem.rpc.verify_account_authority(account, keys)
        except MissingRequiredActiveAuthority:
            return {'valid': False}

    def get_tags_used_by_author(self, account=None):
        """ Returns a list of tags used by an author.

            :param str account: When set, a different account is used for the request (Default is object account name)

            :rtype: list

            .. code-block:: python

                >>> from beem.account import Account
                >>> from beem import Steem
                >>> stm = Steem("https://steemd.minnowsupportproject.org")
                >>> account = Account("beem.app", steem_instance=stm)
                >>> account.get_tags_used_by_author()
                []

        """
        if account is None:
            account = self["name"]
        elif isinstance(account, Account):
            account = account["name"]
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            return self.steem.rpc.get_tags_used_by_author({'author': account}, api="tags")['tags']
        else:
            return self.steem.rpc.get_tags_used_by_author(account, api="tags")

    def get_expiring_vesting_delegations(self, after=None, limit=1000, account=None):
        """ Returns the expirations for vesting delegations.

            :param datetime after: expiration after (only for pre appbase nodes)
            :param int limit: limits number of shown entries (only for pre appbase nodes)
            :param str account: When set, a different account is used for the request (Default is object account name)

            :rtype: list

            .. code-block:: python

                >>> from beem.account import Account
                >>> account = Account("beem.app")
                >>> account.get_expiring_vesting_delegations()
                []

        """
        if account is None:
            account = self["name"]
        elif isinstance(account, Account):
            account = account["name"]
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if after is None:
            after = addTzInfo(datetime.utcnow()) - timedelta(days=8)
        if self.steem.rpc.get_use_appbase():
            return self.steem.rpc.find_vesting_delegation_expirations({'account': account}, api="database")['delegations']
        else:
            return self.steem.rpc.get_expiring_vesting_delegations(account, formatTimeString(after), limit)

    def get_account_votes(self, account=None):
        """ Returns all votes that the account has done

            :rtype: list

            .. code-block:: python

                >>> from beem.account import Account
                >>> from beem import Steem
                >>> stm = Steem("https://steemd.minnowsupportproject.org")
                >>> account = Account("beem.app", steem_instance=stm)
                >>> account.get_account_votes()
                []

        """
        if account is None:
            account = self["name"]
        elif isinstance(account, Account):
            account = account["name"]
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            vote_list = self.steem.rpc.get_account_votes(account, api="condenser")
        else:
            vote_list = self.steem.rpc.get_account_votes(account)
        if isinstance(vote_list, dict) and "error" in vote_list:
            start_author = ""
            start_permlink = ""
            vote_list = []
            finished = False
            while not finished:
                ret = self.steem.rpc.list_votes({"start": [account, start_author, start_permlink], "limit": 1000, "order": "by_voter_comment"}, api="database")["votes"]
                if start_author != "":
                    if len(ret) == 0:
                        finished = True                     
                    ret = ret[1:]
                for vote in ret:
                    if vote["voter"] != account:
                        finished = True
                        continue
                    vote_list.append(vote)
                    start_author = vote["author"]
                    start_permlink = vote["permlink"]
            return vote_list
        else:
            return vote_list

    def get_vote(self, comment):
        """Returns a vote if the account has already voted for comment.

            :param comment: can be a Comment object or a authorpermlink
            :type comment: str, Comment
        """
        from beem.comment import Comment
        c = Comment(comment, steem_instance=self.steem)
        for v in c["active_votes"]:
            if v["voter"] == self["name"]:
                return v
        return None

    def has_voted(self, comment):
        """Returns if the account has already voted for comment

            :param comment: can be a Comment object or a authorpermlink
            :type comment: str, Comment
        """
        from beem.comment import Comment
        c = Comment(comment, steem_instance=self.steem)
        active_votes = {v["voter"]: v for v in c["active_votes"]}
        return self["name"] in active_votes

    def virtual_op_count(self, until=None):
        """ Returns the number of individual account transactions

            :rtype: list
        """
        if until is not None:
            return self.estimate_virtual_op_num(until, stop_diff=1)
        else:
            try:
                op_count = 0
                op_count = self._get_account_history(start=-1, limit=0)
                if isinstance(op_count, list) and len(op_count) > 0 and len(op_count[0]) > 0:
                    return op_count[0][0]
                else:
                    return 0
            except IndexError:
                return 0

    def _get_account_history(self, account=None, start=-1, limit=0):
        if account is None:
            account = self
        account = Account(account, steem_instance=self.steem)
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            try:
                ret = self.steem.rpc.get_account_history({'account': account["name"], 'start': start, 'limit': limit}, api="account_history")['history']
            except ApiNotSupported:
                ret = self.steem.rpc.get_account_history(account["name"], start, limit, api="condenser")
        else:
            ret = self.steem.rpc.get_account_history(account["name"], start, limit, api="database")
            if len(ret) == 0 and limit == 0:
                ret = self.steem.rpc.get_account_history(account["name"], start, limit + 1, api="database")
        return ret

    def estimate_virtual_op_num(self, blocktime, stop_diff=0, max_count=100):
        """ Returns an estimation of an virtual operation index for a given time or blockindex

            :param blocktime: start time or start block index from which account
                operation should be fetched
            :type blocktime: int, datetime
            :param int stop_diff: Sets the difference between last estimation and
                new estimation at which the estimation stops. Must not be zero. (default is 1)
            :param int max_count: sets the maximum number of iterations. -1 disables this (default 100)

            .. testsetup::

                import pytz
                from beem.account import Account
                from beem.blockchain import Blockchain
                from datetime import datetime, timedelta
                from timeit import time as t

            .. testcode::

                utc = pytz.timezone('UTC')
                start_time = utc.localize(datetime.utcnow()) - timedelta(days=7)
                acc = Account("gtg")
                start_op = acc.estimate_virtual_op_num(start_time)

                b = Blockchain()
                start_block_num = b.get_estimated_block_num(start_time)
                start_op2 = acc.estimate_virtual_op_num(start_block_num)

            .. testcode::

                acc = Account("gtg")
                block_num = 21248120
                start = t.time()
                op_num = acc.estimate_virtual_op_num(block_num, stop_diff=1, max_count=10)
                stop = t.time()
                print(stop - start)
                for h in acc.get_account_history(op_num, 0):
                    block_est = h["block"]
                print(block_est - block_num)

        """
        def get_blocknum(index):
            op = self._get_account_history(start=(index))
            return op[0][1]['block']

        max_index = self.virtual_op_count()
        if max_index < stop_diff:
            return 0

        # calculate everything with block numbers
        created = get_blocknum(0)

        # convert blocktime to block number if given as a datetime/date/time
        if isinstance(blocktime, (datetime, date, time)):
            b = Blockchain(steem_instance=self.steem)
            target_blocknum = b.get_estimated_block_num(addTzInfo(blocktime), accurate=True)
        else:
            target_blocknum = blocktime

        # the requested blocknum/timestamp is before the account creation date
        if target_blocknum <= created:
            return 0

        # get the block number from the account's latest operation
        latest_blocknum = get_blocknum(-1)

        # requested blocknum/timestamp is after the latest account operation
        if target_blocknum >= latest_blocknum:
            return max_index

        # all account ops in a single block
        if latest_blocknum - created == 0:
            return 0

        # set initial search range
        op_num = 0
        op_lower = 0
        block_lower = created
        op_upper = max_index
        block_upper = latest_blocknum
        last_op_num = None
        cnt = 0

        while True:
            # check if the maximum number of iterations was reached
            if max_count != -1 and cnt >= max_count:
                # did not converge, return the current state
                return op_num

            # linear approximation between the known upper and
            # lower bounds for the first iteration
            if cnt < 1:
                op_num = int((target_blocknum - block_lower) / (block_upper - block_lower) * (op_upper - op_lower) + op_lower)
            else:
                # divide and conquer for the following iterations
                op_num = int((op_upper + op_lower) / 2)
                if op_upper == op_lower + 1:  # round up if we're close to target
                    op_num += 1

            # get block number for current op number estimation
            if op_num != last_op_num:
                block_num = get_blocknum(op_num)
                last_op_num = op_num

            # check if the required accuracy was reached
            if op_upper - op_lower <= stop_diff or \
               op_upper == op_lower + 1:
                return op_num

            # set new upper/lower boundaries for next iteration
            if block_num < target_blocknum:
                # current op number was too low -> search upwards
                op_lower = op_num
                block_lower = block_num
            else:
                # current op number was too high or matched the target block
                # -> search downwards
                op_upper = op_num
                block_upper = block_num
            cnt += 1

    def get_curation_reward(self, days=7):
        """Returns the curation reward of the last `days` days

            :param int days: limit number of days to be included int the return value
        """
        stop = addTzInfo(datetime.utcnow()) - timedelta(days=days)
        reward_vests = Amount(0, self.steem.vests_symbol, steem_instance=self.steem)
        for reward in self.history_reverse(stop=stop, use_block_num=False, only_ops=["curation_reward"]):
            reward_vests += Amount(reward['reward'], steem_instance=self.steem)
        return self.steem.vests_to_sp(reward_vests.amount)

    def curation_stats(self):
        """Returns the curation reward of the last 24h and 7d and the average
            of the last 7 days

            :returns: Account curation
            :rtype: dictionary

            Sample output:

            .. code-block:: js

                {
                    '24hr': 0.0,
                    '7d': 0.0,
                    'avg': 0.0
                }

        """
        return {"24hr": self.get_curation_reward(days=1),
                "7d": self.get_curation_reward(days=7),
                "avg": self.get_curation_reward(days=7) / 7}

    def get_account_history(self, index, limit, order=-1, start=None, stop=None, use_block_num=True, only_ops=[], exclude_ops=[], raw_output=False):
        """ Returns a generator for individual account transactions. This call can be used in a
            ``for`` loop.

            :param int index: first number of transactions to return
            :param int limit: limit number of transactions to return
            :param start: start number/date of transactions to
                return (*optional*)
            :type start: int, datetime
            :param stop: stop number/date of transactions to
                return (*optional*)
            :type stop: int, datetime
            :param bool use_block_num: if true, start and stop are block numbers, otherwise virtual OP count numbers.
            :param array only_ops: Limit generator by these
                operations (*optional*)
            :param array exclude_ops: Exclude thse operations from
                generator (*optional*)
            :param int batch_size: internal api call batch size (*optional*)
            :param int order: 1 for chronological, -1 for reverse order
            :param bool raw_output: if False, the output is a dict, which
                includes all values. Otherwise, the output is list.

            .. note::

                only_ops and exclude_ops takes an array of strings:
                The full list of operation ID's can be found in
                beembase.operationids.ops.
                Example: ['transfer', 'vote']

        """
        if order != -1 and order != 1:
            raise ValueError("order must be -1 or 1!")
        # self.steem.rpc.set_next_node_on_empty_reply(True)
        txs = self._get_account_history(start=index, limit=limit)
        if txs is None:
            return
        start = addTzInfo(start)
        stop = addTzInfo(stop)

        if order == -1:
            txs_list = reversed(txs)
        else:
            txs_list = txs
        for item in txs_list:
            item_index, event = item
            if start and isinstance(start, (datetime, date, time)):
                timediff = start - formatTimeString(event["timestamp"])
                if timediff.total_seconds() * float(order) > 0:
                    continue
            elif start is not None and use_block_num and order == 1 and event['block'] < start:
                continue
            elif start is not None and use_block_num and order == -1 and event['block'] > start:
                continue
            elif start is not None and not use_block_num and order == 1 and item_index < start:
                continue
            elif start is not None and not use_block_num and order == -1 and item_index > start:
                continue
            if stop is not None and isinstance(stop, (datetime, date, time)):
                timediff = stop - formatTimeString(event["timestamp"])
                if timediff.total_seconds() * float(order) < 0:
                    return
            elif stop is not None and use_block_num and order == 1 and event['block'] > stop:
                return
            elif stop is not None and use_block_num and order == -1 and event['block'] < stop:
                return
            elif stop is not None and not use_block_num and order == 1 and item_index > stop:
                return
            elif stop is not None and not use_block_num and order == -1 and item_index < stop:
                return

            if isinstance(event['op'], list):
                op_type, op = event['op']
            else:
                op_type = event['op']['type']
                if len(op_type) > 10 and op_type[len(op_type) - 10:] == "_operation":
                    op_type = op_type[:-10]
                op = event['op']['value']
            block_props = remove_from_dict(event, keys=['op'], keep_keys=False)

            def construct_op(account_name):
                # verbatim output from steemd
                if raw_output:
                    return item

                # index can change during reindexing in
                # future hard-forks. Thus we cannot take it for granted.
                immutable = op.copy()
                immutable.update(block_props)
                immutable.update({
                    'account': account_name,
                    'type': op_type,
                })
                _id = Blockchain.hash_op(immutable)
                immutable.update({
                    '_id': _id,
                    'index': item_index,
                })
                return immutable

            if exclude_ops and op_type in exclude_ops:
                continue
            if not only_ops or op_type in only_ops:
                yield construct_op(self["name"])

    def history(
        self, start=None, stop=None, use_block_num=True,
        only_ops=[], exclude_ops=[], batch_size=1000, raw_output=False
    ):
        """ Returns a generator for individual account transactions. The
            earlist operation will be first. This call can be used in a
            ``for`` loop.

            :param start: start number/date of transactions to return (*optional*)
            :type start: int, datetime
            :param stop: stop number/date of transactions to return (*optional*)
            :type stop: int, datetime
            :param bool use_block_num: if true, start and stop are block numbers,
                otherwise virtual OP count numbers.
            :param array only_ops: Limit generator by these
                operations (*optional*)
            :param array exclude_ops: Exclude thse operations from
                generator (*optional*)
            :param int batch_size: internal api call batch size (*optional*)
            :param bool raw_output: if False, the output is a dict, which
                includes all values. Otherwise, the output is list.

            .. note::
                only_ops and exclude_ops takes an array of strings:
                The full list of operation ID's can be found in
                beembase.operationids.ops.
                Example: ['transfer', 'vote']

            .. testsetup::

                from beem.account import Account
                from datetime import datetime

            .. testcode::

                acc = Account("gtg")
                max_op_count = acc.virtual_op_count()
                # Returns the 100 latest operations
                acc_op = []
                for h in acc.history(start=max_op_count - 99, stop=max_op_count, use_block_num=False):
                    acc_op.append(h)
                len(acc_op)

            .. testoutput::

                100

            .. testcode::

                acc = Account("test")
                max_block = 21990141
                # Returns the account operation inside the last 100 block. This can be empty.
                acc_op = []
                for h in acc.history(start=max_block - 99, stop=max_block, use_block_num=True):
                    acc_op.append(h)
                len(acc_op)

            .. testoutput::

                0

            .. testcode::

                acc = Account("test")
                start_time = datetime(2018, 3, 1, 0, 0, 0)
                stop_time = datetime(2018, 3, 2, 0, 0, 0)
                # Returns the account operation from 1.4.2018 back to 1.3.2018
                acc_op = []
                for h in acc.history(start=start_time, stop=stop_time):
                    acc_op.append(h)
                len(acc_op)

            .. testoutput::

                0

        """
        _limit = batch_size
        max_index = self.virtual_op_count()
        if not max_index:
            return
        start = addTzInfo(start)
        stop = addTzInfo(stop)
        if start is not None and not use_block_num and not isinstance(start, (datetime, date, time)):
            start_index = start
        elif start is not None and max_index > batch_size:
            op_est = self.estimate_virtual_op_num(start, stop_diff=1)
            est_diff = 0
            if isinstance(start, (datetime, date, time)):
                for h in self.get_account_history(op_est, 0):
                    block_date = formatTimeString(h["timestamp"])
                while(op_est > est_diff + batch_size and block_date > start):
                    est_diff += batch_size
                    if op_est - est_diff < 0:
                        est_diff = op_est
                    for h in self.get_account_history(op_est - est_diff, 0):
                        block_date = formatTimeString(h["timestamp"])
            elif not isinstance(start, (datetime, date, time)):
                for h in self.get_account_history(op_est, 0):
                    block_num = h["block"]
                while(op_est > est_diff + batch_size and block_num > start):
                    est_diff += batch_size
                    if op_est - est_diff < 0:
                        est_diff = op_est
                    for h in self.get_account_history(op_est - est_diff, 0):
                        block_num = h["block"]
            start_index = op_est - est_diff
        else:
            start_index = 0

        first = start_index + _limit
        if first > max_index:
            _limit = max_index - start_index + 1
            first = start_index + _limit
        last_round = False
        if _limit < 0:
            return
        while True:
            # RPC call
            for item in self.get_account_history(first, _limit, start=None, stop=None, order=1, raw_output=raw_output):
                if raw_output:
                    item_index, event = item
                    op_type, op = event['op']
                    timestamp = event["timestamp"]
                    block_num = event["block"]
                else:
                    item_index = item['index']
                    op_type = item['type']
                    timestamp = item["timestamp"]
                    block_num = item["block"]
                if start is not None and isinstance(start, (datetime, date, time)):
                    timediff = start - formatTimeString(timestamp)
                    if timediff.total_seconds() > 0:
                        continue
                elif start is not None and use_block_num and block_num < start:
                    continue
                elif start is not None and not use_block_num and item_index < start:
                    continue
                if stop is not None and isinstance(stop, (datetime, date, time)):
                    timediff = stop - formatTimeString(timestamp)
                    if timediff.total_seconds() < 0:
                        first = max_index + _limit
                        return
                elif stop is not None and use_block_num and block_num > stop:
                    return
                elif stop is not None and not use_block_num and item_index > stop:
                    return
                if exclude_ops and op_type in exclude_ops:
                    continue
                if not only_ops or op_type in only_ops:
                    yield item
            if first < max_index and first + _limit >= max_index and not last_round:
                _limit = max_index - first - 1
                first = max_index
                last_round = True
            else:
                first += (_limit + 1)
                if stop is not None and not use_block_num and isinstance(stop, int) and first >= stop + _limit:
                    break
                elif first > max_index or last_round:
                    break

    def history_reverse(
        self, start=None, stop=None, use_block_num=True,
        only_ops=[], exclude_ops=[], batch_size=1000, raw_output=False
    ):
        """ Returns a generator for individual account transactions. The
            latest operation will be first. This call can be used in a
            ``for`` loop.

            :param start: start number/date of transactions to
                return. If negative the virtual_op_count is added. (*optional*)
            :type start: int, datetime
            :param stop: stop number/date of transactions to
                return. If negative the virtual_op_count is added. (*optional*)
            :type stop: int, datetime
            :param bool use_block_num: if true, start and stop are block numbers,
                otherwise virtual OP count numbers.
            :param array only_ops: Limit generator by these
                operations (*optional*)
            :param array exclude_ops: Exclude thse operations from
                generator (*optional*)
            :param int batch_size: internal api call batch size (*optional*)
            :param bool raw_output: if False, the output is a dict, which
                includes all values. Otherwise, the output is list.

            .. note::
                only_ops and exclude_ops takes an array of strings:
                The full list of operation ID's can be found in
                beembase.operationids.ops.
                Example: ['transfer', 'vote']

            .. testsetup::

                from beem.account import Account
                from datetime import datetime

            .. testcode::

                acc = Account("gtg")
                max_op_count = acc.virtual_op_count()
                # Returns the 100 latest operations
                acc_op = []
                for h in acc.history_reverse(start=max_op_count, stop=max_op_count - 99, use_block_num=False):
                    acc_op.append(h)
                len(acc_op)

            .. testoutput::

                100

            .. testcode::

                max_block = 21990141
                acc = Account("test")
                # Returns the account operation inside the last 100 block. This can be empty.
                acc_op = []
                for h in acc.history_reverse(start=max_block, stop=max_block-100, use_block_num=True):
                    acc_op.append(h)
                len(acc_op)

            .. testoutput::

                0

            .. testcode::

                acc = Account("test")
                start_time = datetime(2018, 4, 1, 0, 0, 0)
                stop_time = datetime(2018, 3, 1, 0, 0, 0)
                # Returns the account operation from 1.4.2018 back to 1.3.2018
                acc_op = []
                for h in acc.history_reverse(start=start_time, stop=stop_time):
                    acc_op.append(h)
                len(acc_op)

            .. testoutput::

                0

        """
        _limit = batch_size
        first = self.virtual_op_count()
        start = addTzInfo(start)
        stop = addTzInfo(stop)
        if not first or not batch_size:
            return
        if start is not None and isinstance(start, int) and start < 0 and not use_block_num:
            start += first
        elif start is not None and isinstance(start, int) and not use_block_num:
            first = start
        elif start is not None and first > batch_size:
            op_est = self.estimate_virtual_op_num(start, stop_diff=1)
            est_diff = 0
            if isinstance(start, (datetime, date, time)):
                for h in self.get_account_history(op_est, 0):
                    block_date = formatTimeString(h["timestamp"])
                while(op_est + est_diff + batch_size < first and block_date < start):
                    est_diff += batch_size
                    if op_est + est_diff > first:
                        est_diff = first - op_est
                    for h in self.get_account_history(op_est + est_diff, 0):
                        block_date = formatTimeString(h["timestamp"])
            else:
                for h in self.get_account_history(op_est, 0):
                    block_num = h["block"]
                while(op_est + est_diff + batch_size < first and block_num < start):
                    est_diff += batch_size
                    if op_est + est_diff > first:
                        est_diff = first - op_est
                    for h in self.get_account_history(op_est + est_diff, 0):
                        block_num = h["block"]
            first = op_est + est_diff
        if stop is not None and isinstance(stop, int) and stop < 0 and not use_block_num:
            stop += first

        while True:
            # RPC call
            if first - _limit < 0:
                _limit = first
            for item in self.get_account_history(first, _limit, start=None, stop=None, order=-1, only_ops=only_ops, exclude_ops=exclude_ops, raw_output=raw_output):
                if raw_output:
                    item_index, event = item
                    op_type, op = event['op']
                    timestamp = event["timestamp"]
                    block_num = event["block"]
                else:
                    item_index = item['index']
                    op_type = item['type']
                    timestamp = item["timestamp"]
                    block_num = item["block"]
                if start is not None and isinstance(start, (datetime, date, time)):
                    timediff = start - formatTimeString(timestamp)
                    if timediff.total_seconds() < 0:
                        continue
                elif start is not None and use_block_num and block_num > start:
                    continue
                elif start is not None and not use_block_num and item_index > start:
                    continue
                if stop is not None and isinstance(stop, (datetime, date, time)):
                    timediff = stop - formatTimeString(timestamp)
                    if timediff.total_seconds() > 0:
                        first = 0
                        return
                elif stop is not None and use_block_num and block_num < stop:
                    first = 0
                    return
                elif stop is not None and not use_block_num and item_index < stop:
                    first = 0
                    return
                if exclude_ops and op_type in exclude_ops:
                    continue
                if not only_ops or op_type in only_ops:
                    yield item
            first -= (_limit + 1)
            if first < 1:
                break

    def mute(self, mute, account=None):
        """ Mute another account

            :param str mute: Mute this account
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)

        """
        return self.follow(mute, what=["ignore"], account=account)

    def unfollow(self, unfollow, account=None):
        """ Unfollow/Unmute another account's blog

            :param str unfollow: Unfollow/Unmute this account
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)

        """
        return self.follow(unfollow, what=[], account=account)

    def follow(self, other, what=["blog"], account=None):
        """ Follow/Unfollow/Mute/Unmute another account's blog

            :param str other: Follow this account
            :param list what: List of states to follow.
                ``['blog']`` means to follow ``other``,
                ``[]`` means to unfollow/unmute ``other``,
                ``['ignore']`` means to ignore ``other``,
                (defaults to ``['blog']``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)

        """
        if account is None:
            account = self["name"]
        if not account:
            raise ValueError("You need to provide an account")
        if not other:
            raise ValueError("You need to provide an account to follow/unfollow/mute/unmute")

        json_body = [
            'follow', {
                'follower': account,
                'following': other,
                'what': what
            }
        ]
        return self.steem.custom_json(
            "follow", json_body, required_posting_auths=[account])

    def update_account_profile(self, profile, account=None, **kwargs):
        """ Update an account's profile in json_metadata

            :param dict profile: The new profile to use
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)

            Sample profile structure:

            .. code-block:: js

                {
                    'name': 'Holger',
                    'about': 'beem Developer',
                    'location': 'Germany',
                    'profile_image': 'https://c1.staticflickr.com/5/4715/38733717165_7070227c89_n.jpg',
                    'cover_image': 'https://farm1.staticflickr.com/894/26382750057_69f5c8e568.jpg',
                    'website': 'https://github.com/holgern/beem'
                }

            .. code-block:: python

                from beem.account import Account
                account = Account("test")
                profile = account.profile
                profile["about"] = "test account"
                account.update_account_profile(profile)

        """
        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)

        if not isinstance(profile, dict):
            raise ValueError("Profile must be a dict type!")

        if self['json_metadata'] == '':
            metadata = {}
        else:
            metadata = json.loads(self['json_metadata'])
        metadata["profile"] = profile
        return self.update_account_metadata(metadata)

    def update_account_metadata(self, metadata, account=None, **kwargs):
        """ Update an account's profile in json_metadata

            :param dict metadata: The new metadata to use
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)

        """
        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)
        if isinstance(metadata, dict):
            metadata = json.dumps(metadata)
        elif not isinstance(metadata, str):
            raise ValueError("Profile must be a dict or string!")
        op = operations.Account_update(
            **{
                "account": account["name"],
                "memo_key": account["memo_key"],
                "json_metadata": metadata,
                "prefix": self.steem.prefix,
            })
        return self.steem.finalizeOp(op, account, "active", **kwargs)

    # -------------------------------------------------------------------------
    #  Approval and Disapproval of witnesses
    # -------------------------------------------------------------------------
    def approvewitness(self, witness, account=None, approve=True, **kwargs):
        """ Approve a witness

            :param list witness: list of Witness name or id
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)

        """
        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)

        # if not isinstance(witnesses, (list, set, tuple)):
        #     witnesses = {witnesses}

        # for witness in witnesses:
        #     witness = Witness(witness, steem_instance=self)

        op = operations.Account_witness_vote(**{
            "account": account["name"],
            "witness": witness,
            "approve": approve,
            "prefix": self.steem.prefix,
        })
        return self.steem.finalizeOp(op, account, "active", **kwargs)

    def disapprovewitness(self, witness, account=None, **kwargs):
        """ Disapprove a witness

            :param list witness: list of Witness name or id
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        return self.approvewitness(
            witness=witness, account=account, approve=False)

    def update_memo_key(self, key, account=None, **kwargs):
        """ Update an account's memo public key

            This method does **not** add any private keys to your
            wallet but merely changes the memo public key.

            :param str key: New memo public key
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)

        PublicKey(key, prefix=self.steem.prefix)

        account["memo_key"] = key
        op = operations.Account_update(**{
            "account": account["name"],
            "memo_key": account["memo_key"],
            "json_metadata": account["json_metadata"],
            "prefix": self.steem.prefix,
        })
        return self.steem.finalizeOp(op, account, "active", **kwargs)

    def update_account_keys(self, new_password, account=None, **kwargs):
        """ Updates all account keys

            This method does **not** add any private keys to your
            wallet but merely changes the memo public key.

            :param str new_password: is used to derive the owner, active,
                posting and memo key
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)

        key_auths = {}
        for role in ['owner', 'active', 'posting', 'memo']:
            pk = PasswordKey(account['name'], new_password, role=role)
            key_auths[role] = format(pk.get_public_key(), self.steem.prefix)

        op = operations.Account_update(**{
            "account": account["name"],
            'owner': {'account_auths': [],
                      'key_auths': [[key_auths['owner'], 1]],
                      "address_auths": [],
                      'weight_threshold': 1},
            'active': {'account_auths': [],
                       'key_auths': [[key_auths['active'], 1]],
                       "address_auths": [],
                       'weight_threshold': 1},
            'posting': {'account_auths': account['posting']['account_auths'],
                        'key_auths': [[key_auths['posting'], 1]],
                        "address_auths": [],
                        'weight_threshold': 1},
            'memo_key': key_auths['memo'],
            "json_metadata": account['json_metadata'],
            "prefix": self.steem.prefix,
        })

        return self.steem.finalizeOp(op, account, "owner", **kwargs)

    def change_recovery_account(self, new_recovery_account,
                                account=None, **kwargs):
        """Request a change of the recovery account.

        .. note:: It takes 30 days until the change applies. Another
            request within this time restarts the 30 day period.
            Setting the current recovery account again cancels any
            pending change request.

        :param str new_recovery_account: account name of the new
            recovery account
        :param str account: (optional) the account to change the
            recovery account for (defaults to ``default_account``)

        """
        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)
        # Account() lookup to make sure the new account is valid
        new_rec_acc = Account(new_recovery_account,
                              steem_instance=self.steem)
        op = operations.Change_recovery_account(**{
            'account_to_recover': account['name'],
            'new_recovery_account': new_rec_acc['name'],
            'extensions': []
        })
        return self.steem.finalizeOp(op, account, "owner", **kwargs)

    # -------------------------------------------------------------------------
    # Simple Transfer
    # -------------------------------------------------------------------------
    def transfer(self, to, amount, asset, memo="", account=None, **kwargs):
        """ Transfer an asset to another account.

            :param str to: Recipient
            :param float amount: Amount to transfer
            :param str asset: Asset to transfer
            :param str memo: (optional) Memo, may begin with `#` for encrypted
                messaging
            :param str account: (optional) the source account for the transfer
                if not ``default_account``


            Transfer example:

            .. code-block:: python

                from beem.account import Account
                from beem import Steem
                active_wif = "5xxxx"
                stm = Steem(keys=[active_wif])
                acc = Account("test", steem_instance=stm)
                acc.transfer("test1", 1, "STEEM", "test")

        """

        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)
        amount = Amount(amount, asset, steem_instance=self.steem)
        to = Account(to, steem_instance=self.steem)
        if memo and memo[0] == "#":
            from .memo import Memo
            memoObj = Memo(
                from_account=account,
                to_account=to,
                steem_instance=self.steem
            )
            memo = memoObj.encrypt(memo[1:])["message"]

        op = operations.Transfer(**{
            "amount": amount,
            "to": to["name"],
            "memo": memo,
            "from": account["name"],
            "prefix": self.steem.prefix,
        })
        return self.steem.finalizeOp(op, account, "active", **kwargs)

    def transfer_to_vesting(self, amount, to=None, account=None, **kwargs):
        """ Vest STEEM

            :param float amount: Amount to transfer
            :param str to: Recipient (optional) if not set equal to account
            :param str account: (optional) the source account for the transfer
                if not ``default_account``
        """
        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)
        if to is None:
            to = self  # powerup on the same account
        else:
            to = Account(to, steem_instance=self.steem)
        amount = self._check_amount(amount, self.steem.steem_symbol)

        to = Account(to, steem_instance=self.steem)

        op = operations.Transfer_to_vesting(**{
            "from": account["name"],
            "to": to["name"],
            "amount": amount,
            "prefix": self.steem.prefix,
        })
        return self.steem.finalizeOp(op, account, "active", **kwargs)

    def convert(self, amount, account=None, request_id=None):
        """ Convert SteemDollars to Steem (takes 3.5 days to settle)

            :param float amount: amount of SBD to convert
            :param str account: (optional) the source account for the transfer
                if not ``default_account``
            :param str request_id: (optional) identifier for tracking the
                conversion`

        """
        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)
        amount = self._check_amount(amount, self.steem.sbd_symbol)
        if request_id:
            request_id = int(request_id)
        else:
            request_id = random.getrandbits(32)
        op = operations.Convert(
            **{
                "owner": account["name"],
                "requestid": request_id,
                "amount": amount,
                "prefix": self.steem.prefix,
            })

        return self.steem.finalizeOp(op, account, "active")

    def transfer_to_savings(self, amount, asset, memo, to=None, account=None, **kwargs):
        """ Transfer SBD or STEEM into a 'savings' account.

            :param float amount: STEEM or SBD amount
            :param float asset: 'STEEM' or 'SBD'
            :param str memo: (optional) Memo
            :param str to: (optional) the source account for the transfer if
                not ``default_account``
            :param str account: (optional) the source account for the transfer
                if not ``default_account``

        """
        if asset not in [self.steem.steem_symbol, self.steem.sbd_symbol]:
            raise AssertionError()

        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)

        amount = Amount(amount, asset, steem_instance=self.steem)
        if to is None:
            to = account  # move to savings on same account
        else:
            to = Account(to, steem_instance=self.steem)

        op = operations.Transfer_to_savings(
            **{
                "from": account["name"],
                "to": to["name"],
                "amount": amount,
                "memo": memo,
                "prefix": self.steem.prefix,
            })
        return self.steem.finalizeOp(op, account, "active", **kwargs)

    def transfer_from_savings(self,
                              amount,
                              asset,
                              memo,
                              request_id=None,
                              to=None,
                              account=None, **kwargs):
        """ Withdraw SBD or STEEM from 'savings' account.

            :param float amount: STEEM or SBD amount
            :param float asset: 'STEEM' or 'SBD'
            :param str memo: (optional) Memo
            :param str request_id: (optional) identifier for tracking or
                cancelling the withdrawal
            :param str to: (optional) the source account for the transfer if
                not ``default_account``
            :param str account: (optional) the source account for the transfer
                if not ``default_account``

        """
        if asset not in [self.steem.steem_symbol, self.steem.sbd_symbol]:
            raise AssertionError()

        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)
        if to is None:
            to = account  # move to savings on same account
        else:
            to = Account(to, steem_instance=self.steem)
        amount = Amount(amount, asset, steem_instance=self.steem)
        if request_id:
            request_id = int(request_id)
        else:
            request_id = random.getrandbits(32)

        op = operations.Transfer_from_savings(
            **{
                "from": account["name"],
                "request_id": request_id,
                "to": to["name"],
                "amount": amount,
                "memo": memo,
                "prefix": self.steem.prefix,
            })
        return self.steem.finalizeOp(op, account, "active", **kwargs)

    def cancel_transfer_from_savings(self, request_id, account=None, **kwargs):
        """ Cancel a withdrawal from 'savings' account.

            :param str request_id: Identifier for tracking or cancelling
                the withdrawal
            :param str account: (optional) the source account for the transfer
                if not ``default_account``

        """
        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)
        op = operations.Cancel_transfer_from_savings(**{
            "from": account["name"],
            "request_id": request_id,
            "prefix": self.steem.prefix,
        })
        return self.steem.finalizeOp(op, account, "active", **kwargs)

    def _check_amount(self, amount, symbol):
        if isinstance(amount, (float, integer_types)):
            amount = Amount(amount, symbol, steem_instance=self.steem)
        elif isinstance(amount, string_types) and amount.replace('.', '', 1).replace(',', '', 1).isdigit():
            amount = Amount(float(amount), symbol, steem_instance=self.steem)
        else:
            amount = Amount(amount, steem_instance=self.steem)
        if not amount["symbol"] == symbol:
            raise AssertionError()
        return amount

    def claim_reward_balance(self,
                             reward_steem=0,
                             reward_sbd=0,
                             reward_vests=0,
                             account=None, **kwargs):
        """ Claim reward balances.
        By default, this will claim ``all`` outstanding balances. To bypass
        this behaviour, set desired claim amount by setting any of
        `reward_steem`, `reward_sbd` or `reward_vests`.

        :param str reward_steem: Amount of STEEM you would like to claim.
        :param str reward_sbd: Amount of SBD you would like to claim.
        :param str reward_vests: Amount of VESTS you would like to claim.
        :param str account: The source account for the claim if not
            ``default_account`` is used.

        """
        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)
        if not account:
            raise ValueError("You need to provide an account")

        # if no values were set by user, claim all outstanding balances on
        # account

        reward_steem = self._check_amount(reward_steem, self.steem.steem_symbol)
        reward_sbd = self._check_amount(reward_sbd, self.steem.sbd_symbol)
        reward_vests = self._check_amount(reward_vests, self.steem.vests_symbol)

        if reward_steem.amount == 0 and reward_sbd.amount == 0 and reward_vests.amount == 0:
            if len(account.balances["rewards"]) == 3:
                reward_steem = account.balances["rewards"][0]
                reward_sbd = account.balances["rewards"][1]
                reward_vests = account.balances["rewards"][2]
                op = operations.Claim_reward_balance(
                    **{
                        "account": account["name"],
                        "reward_steem": reward_steem,
                        "reward_sbd": reward_sbd,
                        "reward_vests": reward_vests,
                        "prefix": self.steem.prefix,
                    })
            else:
                reward_steem = account.balances["rewards"][0]
                reward_vests = account.balances["rewards"][1]
                op = operations.Claim_reward_balance(
                    **{
                        "account": account["name"],
                        "reward_steem": reward_steem,
                        "reward_vests": reward_vests,
                        "prefix": self.steem.prefix,
                    })

        return self.steem.finalizeOp(op, account, "posting", **kwargs)

    def delegate_vesting_shares(self, to_account, vesting_shares,
                                account=None, **kwargs):
        """ Delegate SP to another account.

        :param str to_account: Account we are delegating shares to
            (delegatee).
        :param str vesting_shares: Amount of VESTS to delegate eg. `10000
            VESTS`.
        :param str account: The source account (delegator). If not specified,
            ``default_account`` is used.
        """
        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)
        to_account = Account(to_account, steem_instance=self.steem)
        if to_account is None:
            raise ValueError("You need to provide a to_account")
        vesting_shares = self._check_amount(vesting_shares, self.steem.vests_symbol)

        op = operations.Delegate_vesting_shares(
            **{
                "delegator": account["name"],
                "delegatee": to_account["name"],
                "vesting_shares": vesting_shares,
                "prefix": self.steem.prefix,
            })
        return self.steem.finalizeOp(op, account, "active", **kwargs)

    def withdraw_vesting(self, amount, account=None, **kwargs):
        """ Withdraw VESTS from the vesting account.

            :param float amount: number of VESTS to withdraw over a period of
                13 weeks
            :param str account: (optional) the source account for the transfer
                if not ``default_account``

    """
        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)
        amount = self._check_amount(amount, self.steem.vests_symbol)

        op = operations.Withdraw_vesting(
            **{
                "account": account["name"],
                "vesting_shares": amount,
                "prefix": self.steem.prefix,
            })

        return self.steem.finalizeOp(op, account, "active", **kwargs)

    def set_withdraw_vesting_route(self,
                                   to,
                                   percentage=100,
                                   account=None,
                                   auto_vest=False, **kwargs):
        """ Set up a vesting withdraw route. When vesting shares are
            withdrawn, they will be routed to these accounts based on the
            specified weights.

            :param str to: Recipient of the vesting withdrawal
            :param float percentage: The percent of the withdraw to go
                to the 'to' account.
            :param str account: (optional) the vesting account
            :param bool auto_vest: Set to true if the 'to' account
                should receive the VESTS as VESTS, or false if it should
                receive them as STEEM. (defaults to ``False``)

        """
        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)
        op = operations.Set_withdraw_vesting_route(
            **{
                "from_account": account["name"],
                "to_account": to,
                "percent": int(percentage * STEEM_1_PERCENT),
                "auto_vest": auto_vest
            })

        return self.steem.finalizeOp(op, account, "active", **kwargs)

    def allow(
        self, foreign, weight=None, permission="posting",
        account=None, threshold=None, **kwargs
    ):
        """ Give additional access to an account by some other public
            key or account.

            :param str foreign: The foreign account that will obtain access
            :param int weight: (optional) The weight to use. If not
                define, the threshold will be used. If the weight is
                smaller than the threshold, additional signatures will
                be required. (defaults to threshold)
            :param str permission: (optional) The actual permission to
                modify (defaults to ``posting``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
            :param int threshold: (optional) The threshold that needs to be
                reached by signatures to be able to interact
        """
        from copy import deepcopy
        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)

        if permission not in ["owner", "posting", "active"]:
            raise ValueError(
                "Permission needs to be either 'owner', 'posting', or 'active"
            )
        account = Account(account, steem_instance=self.steem)

        if permission not in account:
            account = Account(account, steem_instance=self.steem, lazy=False, full=True)
            account.clear_cache()
            account.refresh()
        if permission not in account:
            account = Account(account, steem_instance=self.steem)
        if permission not in account:
            raise AssertionError("Could not access permission")

        if not weight:
            weight = account[permission]["weight_threshold"]

        authority = deepcopy(account[permission])
        try:
            pubkey = PublicKey(foreign, prefix=self.steem.prefix)
            authority["key_auths"].append([
                str(pubkey),
                weight
            ])
        except:
            try:
                foreign_account = Account(foreign, steem_instance=self.steem)
                authority["account_auths"].append([
                    foreign_account["name"],
                    weight
                ])
            except:
                raise ValueError(
                    "Unknown foreign account or invalid public key"
                )
        if threshold:
            authority["weight_threshold"] = threshold
            self.steem._test_weights_treshold(authority)

        op = operations.Account_update(**{
            "account": account["name"],
            permission: authority,
            "memo_key": account["memo_key"],
            "json_metadata": account["json_metadata"],
            "prefix": self.steem.prefix
        })
        if permission == "owner":
            return self.steem.finalizeOp(op, account, "owner", **kwargs)
        else:
            return self.steem.finalizeOp(op, account, "active", **kwargs)

    def disallow(
        self, foreign, permission="posting",
        account=None, threshold=None, **kwargs
    ):
        """ Remove additional access to an account by some other public
            key or account.

            :param str foreign: The foreign account that will obtain access
            :param str permission: (optional) The actual permission to
                modify (defaults to ``posting``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
            :param int threshold: The threshold that needs to be reached
                by signatures to be able to interact
        """
        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)

        if permission not in ["owner", "active", "posting"]:
            raise ValueError(
                "Permission needs to be either 'owner', 'posting', or 'active"
            )
        authority = account[permission]

        try:
            pubkey = PublicKey(foreign, prefix=self.steem.prefix)
            affected_items = list(
                [x for x in authority["key_auths"] if x[0] == str(pubkey)])
            authority["key_auths"] = list([x for x in authority["key_auths"] if x[0] != str(pubkey)])
        except:
            try:
                foreign_account = Account(foreign, steem_instance=self.steem)
                affected_items = list(
                    [x for x in authority["account_auths"] if x[0] == foreign_account["name"]])
                authority["account_auths"] = list([x for x in authority["account_auths"] if x[0] != foreign_account["name"]])
            except:
                raise ValueError(
                    "Unknown foreign account or unvalid public key"
                )

        if not affected_items:
            raise ValueError("Changes nothing!")
        removed_weight = affected_items[0][1]

        # Define threshold
        if threshold:
            authority["weight_threshold"] = threshold

        # Correct threshold (at most by the amount removed from the
        # authority)
        try:
            self.steem._test_weights_treshold(authority)
        except:
            log.critical(
                "The account's threshold will be reduced by %d"
                % (removed_weight)
            )
            authority["weight_threshold"] -= removed_weight
            self.steem._test_weights_treshold(authority)

        op = operations.Account_update(**{
            "account": account["name"],
            permission: authority,
            "memo_key": account["memo_key"],
            "json_metadata": account["json_metadata"],
            "prefix": self.steem.prefix,
        })
        if permission == "owner":
            return self.steem.finalizeOp(op, account, "owner", **kwargs)
        else:
            return self.steem.finalizeOp(op, account, "active", **kwargs)

    def feed_history(self, limit=None, start_author=None, start_permlink=None,
                     account=None):
        """ Stream the feed entries of an account in reverse time order.

            .. note:: RPC nodes keep a limited history of entries for the
                      user feed. Older entries may not be available via this
                      call due to these node limitations.

            :param int limit: (optional) stream the latest `limit`
                feed entries. If unset (default), all available entries
                are streamed.
            :param str start_author: (optional) start streaming the
                replies from this author. `start_permlink=None`
                (default) starts with the latest available entry.
                If set, `start_permlink` has to be set as well.
            :param str start_permlink: (optional) start streaming the
                replies from this permlink. `start_permlink=None`
                (default) starts with the latest available entry.
                If set, `start_author` has to be set as well.
            :param str account: (optional) the account to get replies
                to (defaults to ``default_account``)

            comment_history_reverse example:

            .. code-block:: python

                from beem.account import Account
                acc = Account("ned")
                for reply in acc.feed_history(limit=10):
                    print(reply)

        """
        if limit is not None:
            if not isinstance(limit, integer_types) or limit <= 0:
                raise AssertionError("`limit` has to be greater than 0`")
        if (start_author is None and start_permlink is not None) or \
           (start_author is not None and start_permlink is None):
            raise AssertionError("either both or none of `start_author` and "
                                 "`start_permlink` have to be set")

        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)
        feed_count = 0
        while True:
            query_limit = 100
            if limit is not None:
                query_limit = min(limit - feed_count + 1, query_limit)
            from .discussions import Query, Discussions_by_feed
            query = Query(start_author=start_author,
                          start_permlink=start_permlink, limit=query_limit,
                          tag=account['name'])
            results = Discussions_by_feed(query, steem_instance=self.steem)
            if len(results) == 0 or (start_permlink and len(results) == 1):
                return
            if feed_count > 0 and start_permlink:
                results = results[1:]  # strip duplicates from previous iteration
            for entry in results:
                feed_count += 1
                yield entry
                start_permlink = entry['permlink']
                start_author = entry['author']
                if feed_count == limit:
                    return

    def blog_history(self, limit=None, start=-1, reblogs=True, account=None):
        """ Stream the blog entries done by an account in reverse time order.

            .. note:: RPC nodes keep a limited history of entries for the
                      user blog. Older blog posts of an account may not be available
                      via this call due to these node limitations.

            :param int limit: (optional) stream the latest `limit`
                blog entries. If unset (default), all available blog
                entries are streamed.
            :param int start: (optional) start streaming the blog
                entries from this index. `start=-1` (default) starts
                with the latest available entry.
            :param bool reblogs: (optional) if set `True` (default)
                reblogs / resteems are included. If set `False`,
                reblogs/resteems are omitted.
            :param str account: (optional) the account to stream blog
                entries for (defaults to ``default_account``)

            blog_history_reverse example:

            .. code-block:: python

                from beem.account import Account
                acc = Account("steemitblog")
                for post in acc.blog_history(limit=10):
                    print(post)

        """
        if limit is not None:
            if not isinstance(limit, integer_types) or limit <= 0:
                raise AssertionError("`limit` has to be greater than 0`")

        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)

        post_count = 0
        start_permlink = None
        start_author = None
        while True:
            query_limit = 100
            if limit is not None and reblogs:
                query_limit = min(limit - post_count + 1, query_limit)
            if not start_permlink:
                # first iteration uses `get_blog`
                results = self.get_blog(start_entry_id=start,
                                        account=account,
                                        limit=query_limit)
            else:
                # all following iterations use `get_discussions_by_blog`
                from .discussions import Query, Discussions_by_blog
                query = Query(start_author=start_author,
                              start_permlink=start_permlink,
                              limit=query_limit, tag=account['name'])
                results = Discussions_by_blog(query,
                                              steem_instance=self.steem)
            if len(results) == 0 or (start_permlink and len(results) == 1):
                return
            if start_permlink:
                results = results[1:]  # strip duplicates from previous iteration
            for post in results:
                if post['author'] == '':
                    continue
                if (reblogs or post['author'] == account['name']):
                    post_count += 1
                    yield post
                start_permlink = post['permlink']
                start_author = post['author']
                if post_count == limit:
                    return

    def comment_history(self, limit=None, start_permlink=None,
                        account=None):
        """ Stream the comments done by an account in reverse time order.

            .. note:: RPC nodes keep a limited history of user comments for the
                      user feed. Older comments may not be available via this
                      call due to these node limitations.

            :param int limit: (optional) stream the latest `limit`
                comments. If unset (default), all available comments
                are streamed.
            :param str start_permlink: (optional) start streaming the
                comments from this permlink. `start_permlink=None`
                (default) starts with the latest available entry.
            :param str account: (optional) the account to stream
                comments for (defaults to ``default_account``)

            comment_history_reverse example:

            .. code-block:: python

                from beem.account import Account
                acc = Account("ned")
                for comment in acc.comment_history(limit=10):
                    print(comment)

        """
        if limit is not None:
            if not isinstance(limit, integer_types) or limit <= 0:
                raise AssertionError("`limit` has to be greater than 0`")

        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)

        comment_count = 0
        while True:
            query_limit = 100
            if limit is not None:
                query_limit = min(limit - comment_count + 1, query_limit)
            from .discussions import Query, Discussions_by_comments
            query = Query(start_author=account['name'],
                          start_permlink=start_permlink,
                          limit=query_limit, tag=account['name'])
            results = Discussions_by_comments(query,
                                              steem_instance=self.steem)
            if len(results) == 0 or (start_permlink and len(results) == 1):
                return
            if comment_count > 0 and start_permlink:
                results = results[1:]  # strip duplicates from previous iteration
            for comment in results:
                if comment["permlink"] == '':
                    continue
                comment_count += 1
                yield comment
                start_permlink = comment['permlink']
                if comment_count == limit:
                    return

    def reply_history(self, limit=None, start_author=None,
                      start_permlink=None, account=None):
        """ Stream the replies to an account in reverse time order.

            .. note:: RPC nodes keep a limited history of entries for the
                      replies to an author. Older replies to an account may
                      not be available via this call due to
                      these node limitations.

            :param int limit: (optional) stream the latest `limit`
                replies. If unset (default), all available replies
                are streamed.
            :param str start_author: (optional) start streaming the
                replies from this author. `start_permlink=None`
                (default) starts with the latest available entry.
                If set, `start_permlink` has to be set as well.
            :param str start_permlink: (optional) start streaming the
                replies from this permlink. `start_permlink=None`
                (default) starts with the latest available entry.
                If set, `start_author` has to be set as well.
            :param str account: (optional) the account to get replies
                to (defaults to ``default_account``)

            comment_history_reverse example:

            .. code-block:: python

                from beem.account import Account
                acc = Account("ned")
                for reply in acc.reply_history(limit=10):
                    print(reply)

        """
        if limit is not None:
            if not isinstance(limit, integer_types) or limit <= 0:
                raise AssertionError("`limit` has to be greater than 0`")
        if (start_author is None and start_permlink is not None) or \
           (start_author is not None and start_permlink is None):
            raise AssertionError("either both or none of `start_author` and "
                                 "`start_permlink` have to be set")

        if account is None:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)

        if start_author is None:
            start_author = account['name']

        reply_count = 0
        while True:
            query_limit = 100
            if limit is not None:
                query_limit = min(limit - reply_count + 1, query_limit)
            from .discussions import Query, Replies_by_last_update
            query = Query(start_parent_author=start_author,
                          start_permlink=start_permlink,
                          limit=query_limit)
            results = Replies_by_last_update(query,
                                             steem_instance=self.steem)
            if len(results) == 0 or (start_permlink and len(results) == 1):
                return
            if reply_count > 0 and start_permlink:
                results = results[1:]  # strip duplicates from previous iteration
            for reply in results:
                if reply['author'] == '':
                    continue
                reply_count += 1
                yield reply
                start_author = reply['author']
                start_permlink = reply['permlink']
                if reply_count == limit:
                    return


class AccountsObject(list):
    def printAsTable(self):
        t = PrettyTable(["Name"])
        t.align = "l"
        for acc in self:
            t.add_row([acc['name']])
        print(t)

    def print_summarize_table(self, tag_type="Follower", return_str=False, **kwargs):
        t = PrettyTable([
            "Key", "Value"
        ])
        t.align = "r"
        t.add_row([tag_type + " count", str(len(self))])
        own_mvest = []
        eff_sp = []
        rep = []
        last_vote_h = []
        last_post_d = []
        no_vote = 0
        no_post = 0
        for f in self:
            rep.append(f.rep)
            own_mvest.append(f.balances["available"][2].amount / 1e6)
            eff_sp.append(f.get_steem_power())
            last_vote = addTzInfo(datetime.utcnow()) - (f["last_vote_time"])
            if last_vote.days >= 365:
                no_vote += 1
            else:
                last_vote_h.append(last_vote.total_seconds() / 60 / 60)
            last_post = addTzInfo(datetime.utcnow()) - (f["last_root_post"])
            if last_post.days >= 365:
                no_post += 1
            else:
                last_post_d.append(last_post.total_seconds() / 60 / 60 / 24)

        t.add_row(["Summed MVest value", "%.2f" % sum(own_mvest)])
        if (len(rep) > 0):
            t.add_row(["Mean Rep.", "%.2f" % (sum(rep) / len(rep))])
            t.add_row(["Max Rep.", "%.2f" % (max(rep))])
        if (len(eff_sp) > 0):
            t.add_row(["Summed eff. SP", "%.2f" % sum(eff_sp)])
            t.add_row(["Mean eff. SP", "%.2f" % (sum(eff_sp) / len(eff_sp))])
            t.add_row(["Max eff. SP", "%.2f" % max(eff_sp)])
        if (len(last_vote_h) > 0):
            t.add_row(["Mean last vote diff in hours", "%.2f" % (sum(last_vote_h) / len(last_vote_h))])
        if len(last_post_d) > 0:
            t.add_row(["Mean last post diff in days", "%.2f" % (sum(last_post_d) / len(last_post_d))])
        t.add_row([tag_type + " without vote in 365 days", no_vote])
        t.add_row([tag_type + " without post in 365 days", no_post])
        if return_str:
            return t.get_string(**kwargs)
        else:
            print(t.get_string(**kwargs))


class Accounts(AccountsObject):
    """ Obtain a list of accounts

        :param list name_list: list of accounts to fetch
        :param int batch_limit: (optional) maximum number of accounts
            to fetch per call, defaults to 100
        :param Steem steem_instance: Steem() instance to use when
            accessing a RPCcreator = Account(creator, steem_instance=self)
    """
    def __init__(self, name_list, batch_limit=100, lazy=False, full=True, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        if not self.steem.is_connected():
            return
        accounts = []
        name_cnt = 0

        while name_cnt < len(name_list):
            self.steem.rpc.set_next_node_on_empty_reply(False)
            if self.steem.rpc.get_use_appbase():
                accounts += self.steem.rpc.find_accounts({'accounts': name_list[name_cnt:batch_limit + name_cnt]}, api="database")["accounts"]
            else:
                accounts += self.steem.rpc.get_accounts(name_list[name_cnt:batch_limit + name_cnt])
            name_cnt += batch_limit

        super(Accounts, self).__init__(
            [
                Account(x, lazy=lazy, full=full, steem_instance=self.steem)
                for x in accounts
            ]
        )
