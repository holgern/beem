# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from builtins import super
from beem.instance import shared_steem_instance
from .exceptions import AccountDoesNotExistsException
from .blockchainobject import BlockchainObject
from .utils import formatTimeString
from beem.amount import Amount
from datetime import datetime, timedelta
import pytz
from beembase import operations
from beembase.account import PrivateKey, PublicKey
import json
import math
import random


class Account(BlockchainObject):
    """ This class allows to easily access Account data

        :param str account_name: Name of the account
        :param steem.steem.Steem steem_instance: Steem
               instance
        :param bool lazy: Use lazy loading
        :param bool full: Obtain all account data including orders, positions,
               etc.
        :returns: Account data
        :rtype: dictionary
        :raises beem.exceptions.AccountDoesNotExistsException: if account
                does not exist

        Instances of this class are dictionaries that come with additional
        methods (see below) that allow dealing with an account and it's
        corresponding functions.

        .. code-block:: python

            from beem.account import Account
            account = Account("test")
            print(account)
            print(account.balances)

        .. note:: This class comes with its own caching function to reduce the
                  load on the API server. Instances of this class can be
                  refreshed with ``Account.refresh()``.

    """

    type_id = 2

    def __init__(
        self,
        account,
        full=True,
        lazy=False,
        steem_instance=None
    ):
        self.full = full
        super().__init__(
            account,
            lazy=lazy,
            full=full,
            id_item="name",
            steem_instance=steem_instance
        )

    def refresh(self):
        """ Refresh/Obtain an account's data from the API server
        """
        if self.full:
            account = self.steem.rpc.get_accounts(
                [self.identifier])
        else:
            account = self.steem.rpc.lookup_account_names(
                [self.identifier])
        if not account:
            raise AccountDoesNotExistsException(self.identifier)
        else:
            account = account[0]
        if not account:
            raise AccountDoesNotExistsException(self.identifier)
        self.identifier = account["name"]
        self.steem.refresh_data()

        super(Account, self).__init__(account, id_item="name")

    def getSimilarAccountNames(self, limit=5):
        """ Returns limit similar accounts with name as array
        """
        return self.steem.rpc.lookup_accounts(self.name, limit)

    @property
    def name(self):
        """ Returns the account name
        """
        return self["name"]

    @property
    def profile(self):
        """ Returns the account profile
        """
        return json.loads(self["json_metadata"])["profile"]

    @property
    def rep(self):
        """ Returns the account reputation
        """
        return self.reputation()

    def print_info(self, force_refresh=False, return_str=False):
        """ Prints import information about the account
        """
        if force_refresh:
            self.refresh()
            self.steem.refresh_data(True)
        ret = self.name + " (" + str(round(self.rep, 3)) + ") "
        ret += str(self.voting_power()) + "%, full in " + self.get_recharge_time_str()
        ret += " VP = " + str(self.get_voting_value_SBD()) + "$\n"
        ret += str(round(self.steem_power(), 2)) + " SP, "
        ret += str(self.balances["available"][0]) + ", " + str(self.balances["available"][1])
        bandwidth = self.get_bandwidth()
        if bandwidth["allocated"] > 0:
            ret += "\n"
            ret += "Remaining Bandwidth: " + str(round(100 - bandwidth["used"] / bandwidth["allocated"] * 100, 2)) + " %"
            ret += " (" + str(round(bandwidth["used"] / 1024)) + " kb of " + str(round(bandwidth["allocated"] / 1024 / 1024)) + " mb)"
        if return_str:
            return ret
        print(ret)

    def reputation(self, precision=2):
        """ Returns the account reputation
        """
        rep = int(self['reputation'])
        if rep == 0:
            return 25.
        score = max([math.log10(abs(rep)) - 9, 0])
        if rep < 0:
            score *= -1
        score = (score * 9.) + 25.
        if precision is not None:
            return round(score, precision)
        else:
            return score

    def voting_power(self, precision=2, with_regeneration=True):
        """ Returns the account voting power
        """
        if with_regeneration:
            utc = pytz.timezone('UTC')
            diff_in_seconds = (utc.localize(datetime.utcnow()) - formatTimeString(self["last_vote_time"])).total_seconds()
            regenerated_vp = diff_in_seconds * 10000 / 86400 / 5 / 100
        else:
            regenerated_vp = 0
        total_vp = (self["voting_power"] / 100 + regenerated_vp)
        if total_vp > 100:
            return 100
        if total_vp < 0:
            return 0
        if precision is not None:
            return round(total_vp, precision)
        else:
            return total_vp

    def steem_power(self, onlyOwnSP=False):
        """ Returns the account steem power
        """
        if onlyOwnSP:
            vests = Amount(self["vesting_shares"])
        else:
            vests = Amount(self["vesting_shares"]) - Amount(self["delegated_vesting_shares"]) + Amount(self["received_vesting_shares"])
        return self.steem.vests_to_sp(vests)

    def get_voting_value_SBD(self, voting_weight=100, voting_power=None, steem_power=None, precision=2):
        """ Returns the account voting value in SBD
        """
        if voting_power is None:
            voting_power = self.voting_power()
        if steem_power is None:
            sp = self.steem_power()
        else:
            sp = steem_power

        VoteValue = self.steem.sp_to_sbd(sp, voting_power=voting_power * 100, vote_pct=voting_weight * 100)
        return round(VoteValue, precision)

    def get_recharge_time_str(self, voting_power_goal=100):
        """ Returns the account recharge time
        """
        hours = math.floor(self.get_recharge_hours(voting_power_goal=voting_power_goal, precision=3))
        minutes = math.floor(self.get_recharge_reminder_minutes(voting_power_goal=voting_power_goal, precision=0))
        return str(hours) + ":" + str(minutes).zfill(2)

    def get_recharge_hours(self, voting_power_goal=100, precision=2):
        """ Returns the account voting power recharge time in hours
        """
        missing_vp = voting_power_goal - self.voting_power(precision=10)
        if missing_vp < 0:
            return 0
        recharge_seconds = missing_vp * 100 * 5 * 86400 / 10000
        return round(recharge_seconds / 60 / 60, precision)

    def get_recharge_reminder_minutes(self, voting_power_goal=100, precision=0):
        """ Returns the account voting power recharge time in minutes
        """
        hours = self.get_recharge_hours(voting_power_goal=voting_power_goal, precision=5)
        reminder_in_minuts = (hours - math.floor(hours)) * 60
        return round(reminder_in_minuts, precision)

    def get_feed(self, entryId=0, limit=100, raw_data=True, account=None):
        if account is None:
            account = self["name"]
        self.steem.register_apis(["follow"])
        if raw_data:
            return [
                c for c in self.steem.rpc.get_feed(account, entryId, limit, api='follow')
            ]
        else:
            from .comment import Comment
            return [
                Comment(c['comment'], steem_instance=self.steem) for c in self.steem.rpc.get_feed(account, entryId, limit, api='follow')
            ]

    def get_blog_entries(self, entryId=0, limit=100, raw_data=True, account=None):
        if account is None:
            account = self["name"]
        self.steem.register_apis(["follow"])
        if raw_data:
            return [
                c for c in self.steem.rpc.get_blog_entries(account, entryId, limit, api='follow')
            ]
        else:
            from .comment import Comment
            return [
                Comment(c, steem_instance=self.steem) for c in self.steem.rpc.get_blog_entries(account, entryId, limit, api='follow')
            ]

    def get_blog(self, entryId=0, limit=100, raw_data=True, account=None):
        if account is None:
            account = self["name"]
        self.steem.register_apis(["follow"])
        if raw_data:
            return [
                c for c in self.steem.rpc.get_blog(account, entryId, limit, api='follow')
            ]
        else:
            from .comment import Comment
            return [
                Comment(c["comment"], steem_instance=self.steem) for c in self.steem.rpc.get_blog(account, entryId, limit, api='follow')
            ]

    def get_blog_account(self, account=None):
        if account is None:
            account = self["name"]
        self.steem.register_apis(["follow"])
        return self.steem.rpc.get_blog_authors(account, api='follow')

    def get_follow_count(self, account=None):
        """ get_follow_count """
        if account is None:
            account = self["name"]
        self.steem.register_apis(["follow"])
        return self.steem.rpc.get_follow_count(account, api='follow')

    def get_followers(self, raw_data=True):
        """ Returns the account followers as list
        """
        if raw_data:
            return [
                x['follower'] for x in self._get_followers(direction="follower")
            ]
        else:
            return [
                Account(x['follower'], steem_instance=self.steem) for x in self._get_followers(direction="follower")
            ]

    def get_following(self, raw_data=True):
        """ Returns who the account is following as list
        """
        if raw_data:
            return [
                x['following'] for x in self._get_followers(direction="following")
            ]
        else:
            return [
                Account(x['following'], steem_instance=self.steem) for x in self._get_followers(direction="following")
            ]

    def _get_followers(self, direction="follower", last_user=""):
        """ Help function, used in get_followers and get_following
        """
        self.steem.register_apis(["follow"])
        if direction == "follower":
            followers = self.steem.rpc.get_followers(self.name, last_user, "blog", 100, api='follow')
        elif direction == "following":
            followers = self.steem.rpc.get_following(self.name, last_user, "blog", 100, api='follow')
        if len(followers) >= 100:
            followers += self._get_followers(
                direction=direction, last_user=followers[-1][direction])[1:]
        return followers

    @property
    def available_balances(self):
        """ List balances of an account. This call returns instances of
            :class:`steem.amount.Amount`.
        """
        from .amount import Amount
        available_str = [self["balance"], self["sbd_balance"], self["vesting_shares"]]
        return [
            Amount(b, steem_instance=self.steem)
            for b in available_str  # if int(b["amount"]) > 0
        ]

    @property
    def saving_balances(self):
        from .amount import Amount
        savings_str = [self["savings_balance"], self["savings_sbd_balance"]]
        return [
            Amount(b, steem_instance=self.steem)
            for b in savings_str  # if int(b["amount"]) > 0
        ]

    @property
    def reward_balances(self):
        from .amount import Amount
        rewards_str = [self["reward_steem_balance"], self["reward_sbd_balance"], self["reward_vesting_balance"]]
        return [
            Amount(b, steem_instance=self.steem)
            for b in rewards_str  # if int(b["amount"]) > 0
        ]

    @property
    def total_balances(self):
        return [
            self.balance(self.available_balances, "STEEM") + self.balance(self.saving_balances, "STEEM") +
            self.balance(self.reward_balances, "STEEM"),
            self.balance(self.available_balances, "SBD") + self.balance(self.saving_balances, "SBD") +
            self.balance(self.reward_balances, "SBD"),
            self.balance(self.available_balances, "VESTS") + self.balance(self.reward_balances, "VESTS"),
        ]

    @property
    def balances(self):

        return {
            'available': self.available_balances,
            'savings': self.saving_balances,
            'rewards': self.reward_balances,
            'total': self.total_balances,
        }

    def balance(self, balances, symbol):
        """ Obtain the balance of a specific Asset. This call returns instances of
            :class:`steem.amount.Amount`.
        """
        if isinstance(balances, str):
            if balances == "available":
                balances = self.available_balances
            elif balances == "saving":
                balances = self.saving_balances
            elif balances == "reward":
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
        return Amount(0, symbol)

    def interest(self):
        """ Caluclate interest for an account
            :param str account: Account name to get interest for
        """
        last_payment = formatTimeString(self["sbd_last_interest_payment"])
        next_payment = last_payment + timedelta(days=30)
        interest_rate = self.steem.get_dynamic_global_properties()[
            "sbd_interest_rate"] / 100  # percent
        interest_amount = (interest_rate / 100) * int(
            int(self["sbd_seconds"]) / (60 * 60 * 24 * 356)) * 10**-3
        utc = pytz.timezone('UTC')
        return {
            "interest": interest_amount,
            "last_payment": last_payment,
            "next_payment": next_payment,
            "next_payment_duration": next_payment - utc.localize(datetime.now()),
            "interest_rate": interest_rate,
        }

    @property
    def is_fully_loaded(self):
        """ Is this instance fully loaded / e.g. all data available?
        """
        return (self.full)

    def ensure_full(self):
        if not self.is_fully_loaded:
            self.full = True
            self.refresh()

    def get_bandwidth(self, bandwidth_type=1, account=None, raw_data=False):
        """ get_account_bandwidth """
        if account is None:
            account = self["name"]
        if raw_data:
            return self.steem.rpc.get_account_bandwidth(account, bandwidth_type)
        else:
            global_properties = self.steem.get_dynamic_global_properties()
            received_vesting_shares = Amount(self["received_vesting_shares"]).amount
            vesting_shares = Amount(self["vesting_shares"]).amount
            max_virtual_bandwidth = float(global_properties["max_virtual_bandwidth"])
            total_vesting_shares = Amount(global_properties["total_vesting_shares"]).amount
            allocated_bandwidth = (max_virtual_bandwidth * (vesting_shares + received_vesting_shares) / total_vesting_shares)
            allocated_bandwidth = round(allocated_bandwidth / 1000000)

            total_seconds = 604800
            date_bandwidth = formatTimeString(self["last_bandwidth_update"])
            utc = pytz.timezone('UTC')
            seconds_since_last_update = utc.localize(datetime.utcnow()) - date_bandwidth
            seconds_since_last_update = seconds_since_last_update.total_seconds()
            average_bandwidth = float(self["average_bandwidth"])
            used_bandwidth = 0
            if seconds_since_last_update < total_seconds:
                used_bandwidth = (((total_seconds - seconds_since_last_update) * average_bandwidth) / total_seconds)
            used_bandwidth = round(used_bandwidth / 1000000)

            return {"used": used_bandwidth,
                    "allocated": allocated_bandwidth}
            # print("bandwidth percent used: " + str(100 * used_bandwidth / allocated_bandwidth))
            # print("bandwidth percent remaining: " + str(100 - (100 * used_bandwidth / allocated_bandwidth)))

    def get_owner_history(self, account=None):
        """ get_owner_history """
        if account is None:
            account = self["name"]
        return self.steem.rpc.get_owner_history(account)

    def get_conversion_requests(self, account=None):
        """ get_owner_history """
        if account is None:
            account = self["name"]
        return self.steem.rpc.get_conversion_requests(account)

    def get_recovery_request(self, account=None):
        """ get_recovery_request """
        if account is None:
            account = self["name"]
        return self.steem.rpc.get_recovery_request(account)

    def verify_account_authority(self, keys, account=None):
        """ verify_account_authority """
        if account is None:
            account = self["name"]
        return self.steem.rpc.verify_account_authority(account, keys)

    def get_account_votes(self, account=None):
        if account is None:
            account = self["name"]
        return self.steem.rpc.get_account_votes(account)

    def history(
        self, limit=100,
        only_ops=[], exclude_ops=[]
    ):
        """ Returns a generator for individual account transactions. The
            latest operation will be first. This call can be used in a
            ``for`` loop.

            :param int/datetime limit: limit number of transactions to
                return (*optional*)
            :param array only_ops: Limit generator by these
                operations (*optional*)
            :param array exclude_ops: Exclude thse operations from
                generator (*optional*)
        """
        _limit = 100
        cnt = 0

        mostrecent = self.steem.rpc.get_account_history(
            self["name"],
            -1,
            1
        )
        if not mostrecent:
            return
        if limit < 2:
            yield mostrecent
            return
        first = int(mostrecent[0][0])

        while True:
            # RPC call
            txs = self.steem.rpc.get_account_history(
                self["name"],
                first,
                _limit,
            )
            for i in reversed(txs):
                if exclude_ops and i[1]["op"][0] in exclude_ops:
                    continue
                if not only_ops or i[1]["op"][0] in only_ops:
                    cnt += 1
                    if isinstance(limit, datetime):
                        timediff = limit - formatTimeString(i[1]["timestamp"])
                        if timediff.total_seconds() > 0:
                            return
                        yield i
                    else:
                        yield i
                        if limit >= 0 and cnt >= limit:
                            return
            if not txs:
                break
            if len(txs) < _limit:
                break
            # first = int(txs[-1]["id"].split(".")[2])
            first = txs[0][0]
            if first < 2:
                break
            if first < _limit:
                _limit = first - 1

    def unfollow(self, unfollow, what=["blog"], account=None):
        """ Unfollow another account's blog
            :param str unfollow: Follow this account
            :param list what: List of states to follow
                (defaults to ``['blog']``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        # FIXME: removing 'blog' from the array requires to first read
        # the follow.what from the blockchain
        return self.follow(unfollow, what=[], account=account)

    def follow(self, follow, what=["blog"], account=None):
        """ Follow another account's blog
            :param str follow: Follow this account
            :param list what: List of states to follow
                (defaults to ``['blog']``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        if not account:
            account = self["name"]
        if not account:
            raise ValueError("You need to provide an account")

        json_body = [
            'follow', {
                'follower': account,
                'following': follow,
                'what': what
            }
        ]
        return self.steem.custom_json(
            id="follow", json=json_body, required_posting_auths=[account])

    def update_account_profile(self, profile, account=None):
        """ Update an account's meta data (json_meta)
            :param dict json: The meta data to use (i.e. use Profile() from
                account.py)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        if not account:
            account = self["name"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self.steem)
        op = operations.Account_update(
            **{
                "account": account["name"],
                "memo_key": account["memo_key"],
                "json_metadata": profile
            })
        return self.steem.finalizeOp(op, account["name"], "active")

    # -------------------------------------------------------------------------
    #  Approval and Disapproval of witnesses
    # -------------------------------------------------------------------------
    def approvewitness(self, witness, account=None, approve=True, **kwargs):
        """ Approve a witness

            :param list witnesses: list of Witness name or id
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        if not account:
            account = self["name"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self.steem)

        # if not isinstance(witnesses, (list, set, tuple)):
        #     witnesses = {witnesses}

        # for witness in witnesses:
        #     witness = Witness(witness, steem_instance=self)

        op = operations.Account_witness_vote(**{
            "account": account["name"],
            "witness": witness,
            "approve": approve
        })
        return self.steem.finalizeOp(op, account["name"], "active", **kwargs)

    def disapprovewitness(self, witness, account=None, **kwargs):
        """ Disapprove a witness

            :param list witnesses: list of Witness name or id
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
        if not account:
            account = self
        if not account:
            raise ValueError("You need to provide an account")

        PublicKey(key, prefix=self.steem.prefix)

        account = Account(account, steem_instance=self.steem)
        account["memo_key"] = key
        op = operations.Account_update(**{
            "account": account["name"],
            "memo_key": account["memo_key"],
            "json_metadata": account["json_metadata"]
        })
        return self.steem.finalizeOp(op, account["name"], "active", **kwargs)

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
        """
        from .memo import Memo
        if not account:
            account = self
        if not account:
            raise ValueError("You need to provide an account")

        account = Account(account, steem_instance=self.steem)
        amount = Amount(amount, asset, steem_instance=self.steem)
        to = Account(to, steem_instance=self.steem)

        memoObj = Memo(
            from_account=account,
            to_account=to,
            steem_instance=self.steem
        )
        op = operations.Transfer(**{
            "amount": amount,
            "to": to["name"],
            "memo": memoObj.encrypt(memo),
            "from": account["name"],
        })
        return self.steem.finalizeOp(op, account, "active", **kwargs)

    def transfer_to_vesting(self, amount, to=None, account=None, **kwargs):
        """ Vest STEEM

            :param float amount: Amount to transfer
            :param str to: Recipient (optional) if not set equal to account
            :param str account: (optional) the source account for the transfer
                if not ``default_account``
        """
        if not account:
            account = self
        if not account:
            raise ValueError("You need to provide an account")
        if not to:
            to = account  # powerup on the same account
        account = Account(account, steem_instance=self.steem)
        if isinstance(amount, str):
            amount = Amount(amount, steem_instance=self.steem)
        elif isinstance(amount, Amount):
            amount = Amount(amount, steem_instance=self.steem)
        else:
            amount = Amount(amount, "STEEM", steem_instance=self.steem)
        assert amount["symbol"] == "STEEM"
        to = Account(to, steem_instance=self.steem)

        op = operations.Transfer_to_vesting(**{
            "from": account["name"],
            "to": to["name"],
            "amount": amount,
        })
        return self.steem.finalizeOp(op, account, "active", **kwargs)

    def convert(self, amount, account=None, request_id=None):
        """ Convert SteemDollars to Steem (takes one week to settle)
            :param float amount: number of VESTS to withdraw
            :param str account: (optional) the source account for the transfer
            if not ``default_account``
            :param str request_id: (optional) identifier for tracking the
            conversion`
        """
        if not account:
            account = self
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self.steem)
        if isinstance(amount, str):
            amount = Amount(amount, steem_instance=self.steem)
        elif isinstance(amount, Amount):
            amount = Amount(amount, steem_instance=self.steem)
        else:
            amount = Amount(amount, "SBD", steem_instance=self.steem)
        assert amount["symbol"] == "SBD"
        if request_id:
            request_id = int(request_id)
        else:
            request_id = random.getrandbits(32)
        op = operations.Convert(
            **{
                "owner": account["name"],
                "requestid": request_id,
                "amount": amount
            })

        return self.steem.finalizeOp(op, account, "active")

    def transfer_to_savings(self, amount, asset, memo, to=None, account=None):
        """ Transfer SBD or STEEM into a 'savings' account.
            :param float amount: STEEM or SBD amount
            :param float asset: 'STEEM' or 'SBD'
            :param str memo: (optional) Memo
            :param str to: (optional) the source account for the transfer if
            not ``default_account``
            :param str account: (optional) the source account for the transfer
            if not ``default_account``
        """
        assert asset in ['STEEM', 'SBD']

        if not account:
            account = self
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self.steem)
        amount = Amount(amount, asset, steem_instance=self.steem)
        if not to:
            to = account  # move to savings on same account

        op = operations.Transfer_to_savings(
            **{
                "from": account["name"],
                "to": to["name"],
                "amount": amount,
                "memo": memo,
            })
        return self.steem.finalizeOp(op, account, "active")

    def transfer_from_savings(self,
                              amount,
                              asset,
                              memo,
                              request_id=None,
                              to=None,
                              account=None):
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
        assert asset in ['STEEM', 'SBD']

        if not account:
            account = self
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self.steem)
        if not to:
            to = account  # move to savings on same account
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
            })
        return self.steem.finalizeOp(op, account, "active")

    def cancel_transfer_from_savings(self, request_id, account=None):
        """ Cancel a withdrawal from 'savings' account.
            :param str request_id: Identifier for tracking or cancelling
            the withdrawal
            :param str account: (optional) the source account for the transfer
            if not ``default_account``
        """
        if not account:
            account = self
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self.steem)
        op = operations.Cancel_transfer_from_savings(**{
            "from": account["name"],
            "request_id": request_id,
        })
        return self.steem.finalizeOp(op, account, "active")

    def claim_reward_balance(self,
                             reward_steem='0 STEEM',
                             reward_sbd='0 SBD',
                             reward_vests='0 VESTS',
                             account=None):
        """ Claim reward balances.
        By default, this will claim ``all`` outstanding balances. To bypass
        this behaviour, set desired claim amount by setting any of
        `reward_steem`, `reward_sbd` or `reward_vests`.
        Args:
            reward_steem (string): Amount of STEEM you would like to claim.
            reward_sbd (string): Amount of SBD you would like to claim.
            reward_vests (string): Amount of VESTS you would like to claim.
            account (string): The source account for the claim if not
            ``default_account`` is used.
        """
        if not account:
            account = self
        else:
            account = Account(account, steem_instance=self.steem)
        if not account:
            raise ValueError("You need to provide an account")

        # if no values were set by user, claim all outstanding balances on
        # account
        if isinstance(reward_steem, str):
            reward_steem = Amount(reward_steem, steem_instance=self.steem)
        elif isinstance(reward_steem, Amount):
            reward_steem = Amount(reward_steem, steem_instance=self.steem)
        else:
            reward_steem = Amount(reward_steem, "STEEM", steem_instance=self.steem)
        assert reward_steem["symbol"] == "STEEM"

        if isinstance(reward_sbd, str):
            reward_sbd = Amount(reward_sbd, steem_instance=self.steem)
        elif isinstance(reward_sbd, Amount):
            reward_sbd = Amount(reward_sbd, steem_instance=self.steem)
        else:
            reward_sbd = Amount(reward_sbd, "SBD", steem_instance=self.steem)
        assert reward_sbd["symbol"] == "SBD"

        if isinstance(reward_vests, str):
            reward_vests = Amount(reward_vests, steem_instance=self.steem)
        elif isinstance(reward_vests, Amount):
            reward_vests = Amount(reward_vests, steem_instance=self.steem)
        else:
            reward_vests = Amount(reward_vests, "VESTS", steem_instance=self.steem)
        assert reward_vests["symbol"] == "VESTS"
        if reward_steem.amount == 0 and reward_sbd.amount == 0 and reward_vests.amount == 0:
            reward_steem = account.balances["rewards"][0]
            reward_sbd = account.balances["rewards"][1]
            reward_vests = account.balances["rewards"][2]

        op = operations.Claim_reward_balance(
            **{
                "account": account["name"],
                "reward_steem": reward_steem,
                "reward_sbd": reward_sbd,
                "reward_vests": reward_vests,
            })
        return self.steem.finalizeOp(op, account, "posting")

    def delegate_vesting_shares(self, to_account, vesting_shares,
                                account=None):
        """ Delegate SP to another account.
        Args:
            to_account (string): Account we are delegating shares to
            (delegatee).
            vesting_shares (string): Amount of VESTS to delegate eg. `10000
            VESTS`.
            account (string): The source account (delegator). If not specified,
            ``default_account`` is used.
        """
        if not account:
            account = self["name"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self.steem)
        if isinstance(vesting_shares, str):
            vesting_shares = Amount(vesting_shares, steem_instance=self.steem)
        elif isinstance(vesting_shares, Amount):
            vesting_shares = Amount(vesting_shares, steem_instance=self.steem)
        else:
            vesting_shares = Amount(vesting_shares, "VESTS", steem_instance=self.steem)
        assert vesting_shares["symbol"] == "VESTS"
        op = operations.Delegate_vesting_shares(
            **{
                "delegator": account,
                "delegatee": to_account,
                "vesting_shares": vesting_shares,
            })
        return self.steem.finalizeOp(op, account, "active")

    def withdraw_vesting(self, amount, account=None):
        """ Withdraw VESTS from the vesting account.
            :param float amount: number of VESTS to withdraw over a period of
            104 weeks
            :param str account: (optional) the source account for the transfer
            if not ``default_account``
    """
        if not account:
            account = self["name"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self.steem)
        if isinstance(amount, str):
            amount = Amount(amount, steem_instance=self.steem)
        elif isinstance(amount, Amount):
            amount = Amount(amount, steem_instance=self.steem)
        else:
            amount = Amount(amount, "VESTS", steem_instance=self.steem)
        assert amount["symbol"] == "VESTS"
        op = operations.Withdraw_vesting(
            **{
                "account": account["name"],
                "vesting_shares": amount,
            })

        return self.steem.finalizeOp(op, account, "active")
