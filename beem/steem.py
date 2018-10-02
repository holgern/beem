# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from builtins import object
import json
import logging
import re
import os
import math
import ast
import time
from beemgraphenebase.py23 import bytes_types, integer_types, string_types, text_type
from datetime import datetime, timedelta, date
from beemapi.steemnoderpc import SteemNodeRPC
from beemapi.exceptions import NoAccessApi, NoApiWithName
from beemgraphenebase.account import PrivateKey, PublicKey
from beembase import transactions, operations
from beemgraphenebase.chains import known_chains
from .account import Account
from .amount import Amount
from .price import Price
from .storage import configStorage as config
from .version import version as beem_version
from .exceptions import (
    AccountExistsException,
    AccountDoesNotExistsException
)
from .wallet import Wallet
from .steemconnect import SteemConnect
from .transactionbuilder import TransactionBuilder
from .utils import formatTime, resolve_authorperm, derive_permlink, remove_from_dict, addTzInfo, formatToTimeStamp
from beem.constants import STEEM_VOTE_REGENERATION_SECONDS, STEEM_100_PERCENT, STEEM_1_PERCENT, STEEM_RC_REGEN_TIME
from collections import OrderedDict

log = logging.getLogger(__name__)


class Steem(object):
    """ Connect to the Steem network.

        :param str node: Node to connect to *(optional)*
        :param str rpcuser: RPC user *(optional)*
        :param str rpcpassword: RPC password *(optional)*
        :param bool nobroadcast: Do **not** broadcast a transaction!
            *(optional)*
        :param bool unsigned: Do **not** sign a transaction! *(optional)*
        :param bool debug: Enable Debugging *(optional)*
        :param array,dict,string keys: Predefine the wif keys to shortcut the
            wallet database *(optional)*
        :param array,dict,string wif: Predefine the wif keys to shortcut the
                wallet database *(optional)*
        :param bool offline: Boolean to prevent connecting to network (defaults
            to ``False``) *(optional)*
        :param int expiration: Delay in seconds until transactions are supposed
            to expire *(optional)* (default is 30)
        :param str blocking: Wait for broadcasted transactions to be included
            in a block and return full transaction (can be "head" or
            "irreversible")
        :param bool bundle: Do not broadcast transactions right away, but allow
            to bundle operations. It is not possible to send out more than one
            vote operation and more than one comment operation in a single broadcast *(optional)*
        :param bool appbase: Use the new appbase rpc protocol on nodes with version
            0.19.4 or higher. The settings has no effect on nodes with version of 0.19.3 or lower.
        :param int num_retries: Set the maximum number of reconnects to the nodes before
            NumRetriesReached is raised. Disabled for -1. (default is -1)
        :param int num_retries_call: Repeat num_retries_call times a rpc call on node error (default is 5)
        :param int timeout: Timeout setting for https nodes (default is 60)
        :param bool use_sc2: When True, a steemconnect object is created. Can be used for
            broadcast posting op or creating hot_links (default is False)
        :param SteemConnect steemconnect: A SteemConnect object can be set manually, set use_sc2 to True
        :param dict custom_chains: custom chain which should be added to the known chains

        Three wallet operation modes are possible:

        * **Wallet Database**: Here, the steemlibs load the keys from the
          locally stored wallet SQLite database (see ``storage.py``).
          To use this mode, simply call ``Steem()`` without the
          ``keys`` parameter
        * **Providing Keys**: Here, you can provide the keys for
          your accounts manually. All you need to do is add the wif
          keys for the accounts you want to use as a simple array
          using the ``keys`` parameter to ``Steem()``.
        * **Force keys**: This more is for advanced users and
          requires that you know what you are doing. Here, the
          ``keys`` parameter is a dictionary that overwrite the
          ``active``, ``owner``, ``posting`` or ``memo`` keys for
          any account. This mode is only used for *foreign*
          signatures!

        If no node is provided, it will connect to default nodes of
        http://geo.steem.pl. Default settings can be changed with:

        .. code-block:: python

            steem = Steem(<host>)

        where ``<host>`` starts with ``https://``, ``ws://`` or ``wss://``.

        The purpose of this class it to simplify interaction with
        Steem.

        The idea is to have a class that allows to do this:

        .. code-block:: python

            >>> from beem import Steem
            >>> steem = Steem()
            >>> print(steem.get_blockchain_version())  # doctest: +SKIP

        This class also deals with edits, votes and reading content.

        Example for adding a custom chain:

        .. code-block:: python

            from beem import Steem
            stm = Steem(node=["https://mytstnet.com"], custom_chains={"MYTESTNET":
                {'chain_assets': [{'asset': 'SBD', 'id': 0, 'precision': 3, 'symbol': 'SBD'},
                                  {'asset': 'STEEM', 'id': 1, 'precision': 3, 'symbol': 'STEEM'},
                                  {'asset': 'VESTS', 'id': 2, 'precision': 6, 'symbol': 'VESTS'}],
                 'chain_id': '79276aea5d4877d9a25892eaa01b0adf019d3e5cb12a97478df3298ccdd01674',
                 'min_version': '0.0.0',
                 'prefix': 'MTN'}
                }
            )

    """

    def __init__(self,
                 node="",
                 rpcuser=None,
                 rpcpassword=None,
                 debug=False,
                 data_refresh_time_seconds=900,
                 **kwargs):
        """Init steem

            :param str node: Node to connect to *(optional)*
            :param str rpcuser: RPC user *(optional)*
            :param str rpcpassword: RPC password *(optional)*
            :param bool nobroadcast: Do **not** broadcast a transaction!
                *(optional)*
            :param bool unsigned: Do **not** sign a transaction! *(optional)*
            :param bool debug: Enable Debugging *(optional)*
            :param array,dict,string keys: Predefine the wif keys to shortcut the
                wallet database *(optional)*
            :param array,dict,string wif: Predefine the wif keys to shortcut the
                wallet database *(optional)*
            :param bool offline: Boolean to prevent connecting to network (defaults
                to ``False``) *(optional)*
            :param int expiration: Delay in seconds until transactions are supposed
                to expire *(optional)* (default is 30)
            :param str blocking: Wait for broadcast transactions to be included
                in a block and return full transaction (can be "head" or
                "irreversible")
            :param bool bundle: Do not broadcast transactions right away, but allow
                to bundle operations *(optional)*
            :param bool use_condenser: Use the old condenser_api rpc protocol on nodes with version
                0.19.4 or higher. The settings has no effect on nodes with version of 0.19.3 or lower.
            :param int num_retries: Set the maximum number of reconnects to the nodes before
                NumRetriesReached is raised. Disabled for -1. (default is -1)
            :param int num_retries_call: Repeat num_retries_call times a rpc call on node error (default is 5)
                :param int timeout: Timeout setting for https nodes (default is 60)
            :param bool use_sc2: When True, a steemconnect object is created. Can be used for broadcast
                posting op or creating hot_links  (default is False)
            :param SteemConnect steemconnect: A SteemConnect object can be set manually, set use_sc2 to True

        """

        self.rpc = None
        self.debug = debug

        self.offline = bool(kwargs.get("offline", False))
        self.nobroadcast = bool(kwargs.get("nobroadcast", False))
        self.unsigned = bool(kwargs.get("unsigned", False))
        self.expiration = int(kwargs.get("expiration", 30))
        self.bundle = bool(kwargs.get("bundle", False))
        self.steemconnect = kwargs.get("steemconnect", None)
        self.use_sc2 = bool(kwargs.get("use_sc2", False))
        self.blocking = kwargs.get("blocking", False)
        self.custom_chains = kwargs.get("custom_chains", {})

        # Store config for access through other Classes
        self.config = config

        if not self.offline:
            self.connect(node=node,
                         rpcuser=rpcuser,
                         rpcpassword=rpcpassword,
                         **kwargs)

        self.data = {'last_refresh': None, 'last_node': None, 'dynamic_global_properties': None, 'feed_history': None,
                     'get_feed_history': None, 'hardfork_properties': None,
                     'network': None, 'witness_schedule': None, 'reserve_ratio': None,
                     'config': None, 'reward_funds': None}
        self.data_refresh_time_seconds = data_refresh_time_seconds
        # self.refresh_data()

        # txbuffers/propbuffer are initialized and cleared
        self.clear()

        self.wallet = Wallet(steem_instance=self, **kwargs)

        # set steemconnect
        if self.steemconnect is not None and not isinstance(self.steemconnect, SteemConnect):
            raise ValueError("steemconnect musst be SteemConnect object")
        if self.steemconnect is None and self.use_sc2:
            self.steemconnect = SteemConnect(steem_instance=self, **kwargs)
        elif self.steemconnect is not None and not self.use_sc2:
            self.use_sc2 = True

    # -------------------------------------------------------------------------
    # Basic Calls
    # -------------------------------------------------------------------------
    def connect(self,
                node="",
                rpcuser="",
                rpcpassword="",
                **kwargs):
        """ Connect to Steem network (internal use only)
        """
        if not node:
            node = self.get_default_nodes()
            if not bool(node):
                raise ValueError("A Steem node needs to be provided!")

        if not rpcuser and "rpcuser" in config:
            rpcuser = config["rpcuser"]

        if not rpcpassword and "rpcpassword" in config:
            rpcpassword = config["rpcpassword"]

        self.rpc = SteemNodeRPC(node, rpcuser, rpcpassword, **kwargs)

    def is_connected(self):
        """Returns if rpc is connected"""
        return self.rpc is not None

    def __repr__(self):
        if self.offline:
            return "<%s offline=True>" % (
                self.__class__.__name__)
        elif self.rpc and self.rpc.url:
            return "<%s node=%s, nobroadcast=%s>" % (
                self.__class__.__name__, str(self.rpc.url), str(self.nobroadcast))
        else:
            return "<%s, nobroadcast=%s>" % (
                self.__class__.__name__, str(self.nobroadcast))

    def refresh_data(self, force_refresh=False, data_refresh_time_seconds=None):
        """ Read and stores steem blockchain parameters
            If the last data refresh is older than data_refresh_time_seconds, data will be refreshed

            :param bool force_refresh: if True, a refresh of the data is enforced
            :param float data_refresh_time_seconds: set a new minimal refresh time in seconds

        """
        if self.offline:
            return
        if data_refresh_time_seconds is not None:
            self.data_refresh_time_seconds = data_refresh_time_seconds
        if self.data['last_refresh'] is not None and not force_refresh and self.data["last_node"] == self.rpc.url:
            if (datetime.utcnow() - self.data['last_refresh']).total_seconds() < self.data_refresh_time_seconds:
                return
        self.data['last_refresh'] = datetime.utcnow()
        self.data["last_node"] = self.rpc.url
        self.data["dynamic_global_properties"] = self.get_dynamic_global_properties(False)
        self.data['feed_history'] = self.get_feed_history(False)
        self.data['get_feed_history'] = self.get_feed_history(False)
        self.data['hardfork_properties'] = self.get_hardfork_properties(False)
        self.data['network'] = self.get_network(False)
        self.data['witness_schedule'] = self.get_witness_schedule(False)
        self.data['config'] = self.get_config(False)
        self.data['reward_funds'] = self.get_reward_funds(False)
        self.data['reserve_ratio'] = self.get_reserve_ratio(False)

    def get_dynamic_global_properties(self, use_stored_data=True):
        """ This call returns the *dynamic global properties*

            :param bool use_stored_data: if True, stored data will be returned. If stored data are
                empty or old, refresh_data() is used.

        """
        if use_stored_data:
            self.refresh_data()
            return self.data['dynamic_global_properties']
        if self.rpc is None:
            return None
        self.rpc.set_next_node_on_empty_reply(True)
        return self.rpc.get_dynamic_global_properties(api="database")

    def get_reserve_ratio(self, use_stored_data=True):
        """ This call returns the *reserve ratio*

            :param bool use_stored_data: if True, stored data will be returned. If stored data are
                empty or old, refresh_data() is used.

        """
        if use_stored_data:
            self.refresh_data()
            return self.data['reserve_ratio']

        if self.rpc is None:
            return None
        self.rpc.set_next_node_on_empty_reply(True)
        if self.rpc.get_use_appbase():
            return self.rpc.get_reserve_ratio(api="witness")
        else:
            props = self.get_dynamic_global_properties()
            # conf = self.get_config()
            reserve_ratio = {'id': 0, 'average_block_size': props['average_block_size'],
                             'current_reserve_ratio': props['current_reserve_ratio'],
                             'max_virtual_bandwidth': props['max_virtual_bandwidth']}
            return reserve_ratio

    def get_feed_history(self, use_stored_data=True):
        """ Returns the feed_history

            :param bool use_stored_data: if True, stored data will be returned. If stored data are
                empty or old, refresh_data() is used.

        """
        if use_stored_data:
            self.refresh_data()
            return self.data['feed_history']
        if self.rpc is None:
            return None
        self.rpc.set_next_node_on_empty_reply(True)
        return self.rpc.get_feed_history(api="database")

    def get_reward_funds(self, use_stored_data=True):
        """ Get details for a reward fund.

            :param bool use_stored_data: if True, stored data will be returned. If stored data are
                empty or old, refresh_data() is used.

        """
        if use_stored_data:
            self.refresh_data()
            return self.data['reward_funds']

        if self.rpc is None:
            return None
        ret = None
        self.rpc.set_next_node_on_empty_reply(True)
        if self.rpc.get_use_appbase():
            funds = self.rpc.get_reward_funds(api="database")['funds']
            if len(funds) > 0:
                funds = funds[0]
            ret = funds
        else:
            ret = self.rpc.get_reward_fund("post", api="database")
        return ret

    def get_current_median_history(self, use_stored_data=True):
        """ Returns the current median price
            :param bool use_stored_data: if True, stored data will be returned. If stored data are
            empty or old, refresh_data() is used.
        """
        if use_stored_data:
            self.refresh_data()
            if self.data['get_feed_history']:
                return self.data['get_feed_history']['current_median_history']
            else:
                return None
        if self.rpc is None:
            return None
        ret = None
        self.rpc.set_next_node_on_empty_reply(True)
        if self.rpc.get_use_appbase():
            ret = self.rpc.get_feed_history(api="database")['current_median_history']
        else:
            ret = self.rpc.get_current_median_history_price(api="database")
        return ret

    def get_hardfork_properties(self, use_stored_data=True):
        """ Returns Hardfork and live_time of the hardfork
            :param bool use_stored_data: if True, stored data will be returned. If stored data are
            empty or old, refresh_data() is used.
        """
        if use_stored_data:
            self.refresh_data()
            return self.data['hardfork_properties']
        if self.rpc is None:
            return None
        ret = None
        self.rpc.set_next_node_on_empty_reply(True)
        if self.rpc.get_use_appbase():
            ret = self.rpc.get_hardfork_properties(api="database")
        else:
            ret = self.rpc.get_next_scheduled_hardfork(api="database")

        return ret

    def get_network(self, use_stored_data=True):
        """ Identify the network
            :param bool use_stored_data: if True, stored data will be returned. If stored data are
            empty or old, refresh_data() is used.

            :returns: Network parameters
            :rtype: dict
        """
        if use_stored_data:
            self.refresh_data()
            return self.data['network']

        if self.rpc is None:
            return None
        try:
            return self.rpc.get_network()
        except:
            return known_chains["STEEM"]

    def get_median_price(self, use_stored_data=True):
        """ Returns the current median history price as Price
        """
        median_price = self.get_current_median_history(use_stored_data=use_stored_data)
        a = Price(
            None,
            base=Amount(median_price['base'], steem_instance=self),
            quote=Amount(median_price['quote'], steem_instance=self),
            steem_instance=self
        )
        return a.as_base("SBD")

    def get_block_interval(self, use_stored_data=True):
        """Returns the block interval in seconds"""
        props = self.get_config(use_stored_data=use_stored_data, replace_steemit_by_steem=True)
        if props and "STEEM_BLOCK_INTERVAL" in props:
            block_interval = props["STEEM_BLOCK_INTERVAL"]
        else:
            block_interval = 3
        return block_interval

    def get_blockchain_version(self, use_stored_data=True):
        """Returns the blockchain version"""
        props = self.get_config(use_stored_data=use_stored_data, replace_steemit_by_steem=True)
        if props and "STEEM_BLOCKCHAIN_VERSION" in props:
            blockchain_version = props["STEEM_BLOCKCHAIN_VERSION"]
        else:
            blockchain_version = '0.0.0'
        return blockchain_version

    def get_dust_threshold(self, use_stored_data=True):
        """Returns the vote dust threshold"""
        props = self.get_config(use_stored_data=use_stored_data, replace_steemit_by_steem=True)
        if props and 'STEEM_VOTE_DUST_THRESHOLD' in props:
            dust_threshold = props['STEEM_VOTE_DUST_THRESHOLD']
        else:
            dust_threshold = 0
        return dust_threshold

    def get_resource_params(self):
        """Returns the resource parameter"""
        return self.rpc.get_resource_params(api="rc")["resource_params"]

    def get_resource_pool(self):
        """Returns the resource pool"""
        return self.rpc.get_resource_pool(api="rc")["resource_pool"]

    def get_rc_cost(self, resource_count):
        """Returns the RC costs based on the resource_count"""
        pools = self.get_resource_pool()
        params = self.get_resource_params()
        config = self.get_config()
        dyn_param = self.get_dynamic_global_properties()
        rc_regen = int(Amount(dyn_param["total_vesting_shares"], steem_instance=self)) / (STEEM_RC_REGEN_TIME / config["STEEM_BLOCK_INTERVAL"])
        total_cost = 0
        if rc_regen == 0:
            return total_cost
        for resource_type in resource_count:
            curve_params = params[resource_type]["price_curve_params"]
            current_pool = int(pools[resource_type]["pool"])
            count = resource_count[resource_type]
            count *= params[resource_type]["resource_dynamics_params"]["resource_unit"]
            cost = self._compute_rc_cost(curve_params, current_pool, count, rc_regen)
            total_cost += cost
        return total_cost

    def _compute_rc_cost(self, curve_params, current_pool, resource_count, rc_regen):
        """Helper function for computing the RC costs"""
        num = int(rc_regen)
        num *= int(curve_params['coeff_a'])
        num = int(num) >> int(curve_params['shift'])
        num += 1
        num *= int(resource_count)
        denom = int(curve_params['coeff_b'])
        if int(current_pool) > 0:
            denom += int(current_pool)
        num_denom = num / denom
        return int(num_denom) + 1

    def rshares_to_sbd(self, rshares, not_broadcasted_vote=False, use_stored_data=True):
        """ Calculates the current SBD value of a vote
        """
        payout = float(rshares) * self.get_sbd_per_rshares(use_stored_data=use_stored_data,
                                                           not_broadcasted_vote_rshares=rshares if not_broadcasted_vote else 0)
        return payout

    def get_sbd_per_rshares(self, not_broadcasted_vote_rshares=0, use_stored_data=True):
        """ Returns the current rshares to SBD ratio
        """
        reward_fund = self.get_reward_funds(use_stored_data=use_stored_data)
        reward_balance = Amount(reward_fund["reward_balance"], steem_instance=self).amount
        recent_claims = float(reward_fund["recent_claims"]) + not_broadcasted_vote_rshares

        fund_per_share = reward_balance / (recent_claims)
        median_price = self.get_median_price(use_stored_data=use_stored_data)
        SBD_price = (median_price * Amount("1 STEEM", steem_instance=self)).amount
        return fund_per_share * SBD_price

    def get_steem_per_mvest(self, time_stamp=None, use_stored_data=True):
        """ Returns the MVEST to STEEM ratio

            :param int time_stamp: (optional) if set, return an estimated
                STEEM per MVEST ratio for the given time stamp. If unset the
                current ratio is returned (default). (can also be a datetime object)
        """
        if time_stamp is not None:
            if isinstance(time_stamp, (datetime, date)):
                time_stamp = formatToTimeStamp(time_stamp)
            a = 2.1325476281078992e-05
            b = -31099.685481490847
            a2 = 2.9019227739473682e-07
            b2 = 48.41432402074669

            if (time_stamp < (b2 - b) / (a - a2)):
                return a * time_stamp + b
            else:
                return a2 * time_stamp + b2
        global_properties = self.get_dynamic_global_properties(use_stored_data=use_stored_data)

        return (
            Amount(global_properties['total_vesting_fund_steem'], steem_instance=self).amount /
            (Amount(global_properties['total_vesting_shares'], steem_instance=self).amount / 1e6)
        )

    def vests_to_sp(self, vests, timestamp=None, use_stored_data=True):
        """ Converts vests to SP

            :param beem.amount.Amount vests/float vests: Vests to convert
            :param int timestamp: (Optional) Can be used to calculate
                the conversion rate from the past

        """
        if isinstance(vests, Amount):
            vests = vests.amount
        return vests / 1e6 * self.get_steem_per_mvest(timestamp, use_stored_data=use_stored_data)

    def sp_to_vests(self, sp, timestamp=None, use_stored_data=True):
        """ Converts SP to vests

            :param float sp: Steem power to convert
            :param datetime timestamp: (Optional) Can be used to calculate
                the conversion rate from the past
        """
        return sp * 1e6 / self.get_steem_per_mvest(timestamp, use_stored_data=use_stored_data)

    def sp_to_sbd(self, sp, voting_power=STEEM_100_PERCENT, vote_pct=STEEM_100_PERCENT, not_broadcasted_vote=True, use_stored_data=True):
        """ Obtain the resulting SBD vote value from Steem power
            :param number steem_power: Steem Power
            :param int voting_power: voting power (100% = 10000)
            :param int vote_pct: voting percentage (100% = 10000)
            :param bool not_broadcasted_vote: not_broadcasted or already broadcasted vote (True = not_broadcasted vote).
            Only impactful for very big votes. Slight modification to the value calculation, as the not_broadcasted
            vote rshares decreases the reward pool.
        """
        vesting_shares = int(self.sp_to_vests(sp, use_stored_data=use_stored_data))
        return self.vests_to_sbd(vesting_shares, voting_power=voting_power, vote_pct=vote_pct, not_broadcasted_vote=not_broadcasted_vote, use_stored_data=use_stored_data)

    def vests_to_sbd(self, vests, voting_power=STEEM_100_PERCENT, vote_pct=STEEM_100_PERCENT, not_broadcasted_vote=True, use_stored_data=True):
        """ Obtain the resulting SBD vote value from vests
            :param number vests: vesting shares
            :param int voting_power: voting power (100% = 10000)
            :param int vote_pct: voting percentage (100% = 10000)
            :param bool not_broadcasted_vote: not_broadcasted or already broadcasted vote (True = not_broadcasted vote).
            Only impactful for very big votes. Slight modification to the value calculation, as the not_broadcasted
            vote rshares decreases the reward pool.
        """
        vote_rshares = self.vests_to_rshares(vests, voting_power=voting_power, vote_pct=vote_pct)
        return self.rshares_to_sbd(vote_rshares, not_broadcasted_vote=not_broadcasted_vote, use_stored_data=use_stored_data)

    def _max_vote_denom(self, use_stored_data=True):
        # get props
        global_properties = self.get_dynamic_global_properties(use_stored_data=use_stored_data)
        vote_power_reserve_rate = global_properties['vote_power_reserve_rate']
        max_vote_denom = vote_power_reserve_rate * STEEM_VOTE_REGENERATION_SECONDS
        return max_vote_denom

    def _calc_resulting_vote(self, voting_power=STEEM_100_PERCENT, vote_pct=STEEM_100_PERCENT, use_stored_data=True):
        # determine voting power used
        used_power = int((voting_power * abs(vote_pct)) / STEEM_100_PERCENT * (60 * 60 * 24))
        max_vote_denom = self._max_vote_denom(use_stored_data=use_stored_data)
        used_power = int((used_power + max_vote_denom - 1) / max_vote_denom)
        return used_power

    def sp_to_rshares(self, steem_power, voting_power=STEEM_100_PERCENT, vote_pct=STEEM_100_PERCENT, use_stored_data=True):
        """ Obtain the r-shares from Steem power

            :param number steem_power: Steem Power
            :param int voting_power: voting power (100% = 10000)
            :param int vote_pct: voting percentage (100% = 10000)

        """
        # calculate our account voting shares (from vests)
        vesting_shares = int(self.sp_to_vests(steem_power, use_stored_data=use_stored_data))
        return self.vests_to_rshares(vesting_shares, voting_power=voting_power, vote_pct=vote_pct, use_stored_data=use_stored_data)

    def vests_to_rshares(self, vests, voting_power=STEEM_100_PERCENT, vote_pct=STEEM_100_PERCENT, subtract_dust_threshold=True, use_stored_data=True):
        """ Obtain the r-shares from vests

            :param number vests: vesting shares
            :param int voting_power: voting power (100% = 10000)
            :param int vote_pct: voting percentage (100% = 10000)

        """
        used_power = self._calc_resulting_vote(voting_power=voting_power, vote_pct=vote_pct, use_stored_data=use_stored_data)
        # calculate vote rshares
        rshares = int(math.copysign(vests * 1e6 * used_power / STEEM_100_PERCENT, vote_pct))
        if subtract_dust_threshold:
            if abs(rshares) <= self.get_dust_threshold(use_stored_data=use_stored_data):
                return 0
            rshares -= math.copysign(self.get_dust_threshold(use_stored_data=use_stored_data), vote_pct)
        return rshares

    def sbd_to_rshares(self, sbd, not_broadcasted_vote=False, use_stored_data=True):
        """ Obtain the r-shares from SBD

        :param str/int/Amount sbd: SBD
        :param bool not_broadcasted_vote: not_broadcasted or already broadcasted vote (True = not_broadcasted vote).
         Only impactful for very high amounts of SBD. Slight modification to the value calculation, as the not_broadcasted
         vote rshares decreases the reward pool.

        """
        if isinstance(sbd, Amount):
            sbd = Amount(sbd, steem_instance=self)
        elif isinstance(sbd, string_types):
            sbd = Amount(sbd, steem_instance=self)
        else:
            sbd = Amount(sbd, 'SBD', steem_instance=self)
        if sbd['symbol'] != 'SBD':
            raise AssertionError('Should input SBD, not any other asset!')
        reward_pool_sbd = self.get_median_price(use_stored_data=use_stored_data) * Amount(self.get_reward_funds(use_stored_data=use_stored_data)['reward_balance'])
        if sbd.amount > reward_pool_sbd.amount:
            raise ValueError('Provided more SBD than available in the reward pool.')

        # If the vote was already broadcasted we can assume the blockchain values to be true
        if not not_broadcasted_vote:
            return sbd.amount / self.get_sbd_per_rshares(use_stored_data=use_stored_data)

        # If the vote wasn't broadcasted (yet), we have to calculate the rshares while considering
        # the change our vote is causing to the recent_claims. This is more important for really
        # big votes which have a significant impact on the recent_claims.

        # Get some data from the blockchain
        reward_fund = self.get_reward_funds(use_stored_data=use_stored_data)
        reward_balance = Amount(reward_fund["reward_balance"], steem_instance=self).amount
        recent_claims = float(reward_fund["recent_claims"])
        median_price = self.get_median_price(use_stored_data=use_stored_data)
        SBD_price = (median_price * Amount("1 STEEM", steem_instance=self)).amount

        # This is the formular we can use to determine the "true" rshares
        # We get this formular by some math magic using the previous used formulas
        # FundsPerShare = (balance / (claims+newShares))*Price
        # newShares = Amount / FundsPerShare
        # We can now resolve both formulas for FundsPerShare and set the formulas to be equal
        # (balance / (claims+newShares))*Price = Amount / newShares
        # Now we resolve for newShares resulting in:
        # newShares = = claims * amount / (balance*price -amount)
        rshares = recent_claims * sbd.amount / ((reward_balance * SBD_price) - sbd.amount)

        return int(rshares)

    def rshares_to_vote_pct(self, rshares, steem_power=None, vests=None, voting_power=STEEM_100_PERCENT, use_stored_data=True):
        """ Obtain the voting percentage for a desired rshares value
            for a given Steem Power or vesting shares and voting_power
            Give either steem_power or vests, not both.
            When the output is greater than 10000 or less than -10000,
            the given absolute rshares are too high

            Returns the required voting percentage (100% = 10000)

            :param number rshares: desired rshares value
            :param number steem_power: Steem Power
            :param number vests: vesting shares
            :param int voting_power: voting power (100% = 10000)

        """
        if steem_power is None and vests is None:
            raise ValueError("Either steem_power or vests has to be set!")
        if steem_power is not None and vests is not None:
            raise ValueError("Either steem_power or vests has to be set. Not both!")
        if steem_power is not None:
            vests = int(self.sp_to_vests(steem_power, use_stored_data=use_stored_data) * 1e6)

        if self.hardfork >= 20:
            rshares += math.copysign(self.get_dust_threshold(use_stored_data=use_stored_data), rshares)

        max_vote_denom = self._max_vote_denom(use_stored_data=use_stored_data)

        used_power = int(math.ceil(abs(rshares) * STEEM_100_PERCENT / vests))
        used_power = used_power * max_vote_denom

        vote_pct = used_power * STEEM_100_PERCENT / (60 * 60 * 24) / voting_power
        return int(math.copysign(vote_pct, rshares))

    def sbd_to_vote_pct(self, sbd, steem_power=None, vests=None, voting_power=STEEM_100_PERCENT, not_broadcasted_vote=True, use_stored_data=True):
        """ Obtain the voting percentage for a desired SBD value
            for a given Steem Power or vesting shares and voting power
            Give either Steem Power or vests, not both.
            When the output is greater than 10000 or smaller than -10000,
            the SBD value is too high.

            Returns the required voting percentage (100% = 10000)

            :param str/int/Amount sbd: desired SBD value
            :param number steem_power: Steem Power
            :param number vests: vesting shares
            :param bool not_broadcasted_vote: not_broadcasted or already broadcasted vote (True = not_broadcasted vote).
             Only impactful for very high amounts of SBD. Slight modification to the value calculation, as the not_broadcasted
             vote rshares decreases the reward pool.

        """
        if isinstance(sbd, Amount):
            sbd = Amount(sbd, steem_instance=self)
        elif isinstance(sbd, string_types):
            sbd = Amount(sbd, steem_instance=self)
        else:
            sbd = Amount(sbd, 'SBD', steem_instance=self)
        if sbd['symbol'] != 'SBD':
            raise AssertionError()
        rshares = self.sbd_to_rshares(sbd, not_broadcasted_vote=not_broadcasted_vote, use_stored_data=use_stored_data)
        return self.rshares_to_vote_pct(rshares, steem_power=steem_power, vests=vests, voting_power=voting_power, use_stored_data=use_stored_data)

    def get_chain_properties(self, use_stored_data=True):
        """ Return witness elected chain properties

            Properties:::

                {
                    'account_creation_fee': '30.000 STEEM',
                    'maximum_block_size': 65536,
                    'sbd_interest_rate': 250
                }

        """
        if use_stored_data:
            self.refresh_data()
            return self.data['witness_schedule']['median_props']
        else:
            return self.get_witness_schedule(use_stored_data)['median_props']

    def get_witness_schedule(self, use_stored_data=True):
        """ Return witness elected chain properties

        """
        if use_stored_data:
            self.refresh_data()
            return self.data['witness_schedule']

        if self.rpc is None:
            return None
        self.rpc.set_next_node_on_empty_reply(True)
        return self.rpc.get_witness_schedule(api="database")

    def get_config(self, use_stored_data=True, replace_steemit_by_steem=False):
        """ Returns internal chain configuration.

            :param bool use_stored_data: If True, the chached value is returned
            :param bool replace_steemit_by_steem: If True, it replaces all
                STEEMIT keys by STEEM (only useful on non appbase nodes)
        """
        if use_stored_data:
            self.refresh_data()
            config = self.data['config']
        else:
            if self.rpc is None:
                return None
            self.rpc.set_next_node_on_empty_reply(True)
            config = self.rpc.get_config(api="database")
        if config is not None and replace_steemit_by_steem:
            new_config = {}
            for key in config:
                new_config[key.replace('STEEMIT', 'STEEM')] = config[key]
            return new_config
        else:
            return config

    @property
    def chain_params(self):
        if self.offline or self.rpc is None:
            return known_chains["STEEM"]
        else:
            return self.get_network()

    @property
    def hardfork(self):
        if self.offline or self.rpc is None:
            versions = known_chains['STEEM']['min_version']
        else:
            versions = self.get_hardfork_properties()["current_hardfork_version"]
        return int(versions.split('.')[1])

    @property
    def prefix(self):
        return self.chain_params["prefix"]

    def set_default_account(self, account):
        """ Set the default account to be used
        """
        Account(account, steem_instance=self)
        config["default_account"] = account

    def set_password_storage(self, password_storage):
        """ Set the password storage mode.

            When set to "no", the password has to be provided each time.
            When set to "environment" the password is taken from the
            UNLOCK variable

            When set to "keyring" the password is taken from the
            python keyring module. A wallet password can be stored with
            python -m keyring set beem wallet password

            :param str password_storage: can be "no",
                "keyring" or "environment"

        """
        config["password_storage"] = password_storage

    def set_default_nodes(self, nodes):
        """ Set the default nodes to be used
        """
        if bool(nodes):
            if isinstance(nodes, list):
                nodes = str(nodes)
            config["node"] = nodes
        else:
            config.delete("node")

    def get_default_nodes(self):
        """Returns the default nodes"""
        if "node" in config:
            nodes = config["node"]
        elif "nodes" in config:
            nodes = config["nodes"]
        elif "default_nodes" in config and bool(config["default_nodes"]):
            nodes = config["default_nodes"]
        else:
            nodes = []
        if isinstance(nodes, str) and nodes[0] == '[' and nodes[-1] == ']':
            nodes = ast.literal_eval(nodes)
        return nodes

    def move_current_node_to_front(self):
        """Returns the default node list, until the first entry
            is equal to the current working node url
        """
        node = self.get_default_nodes()
        if len(node) < 2:
            return
        offline = self.offline
        while not offline and node[0] != self.rpc.url and len(node) > 1:
            node = node[1:] + [node[0]]
        self.set_default_nodes(node)

    def set_default_vote_weight(self, vote_weight):
        """ Set the default vote weight to be used
        """
        config["default_vote_weight"] = vote_weight

    def finalizeOp(self, ops, account, permission, **kwargs):
        """ This method obtains the required private keys if present in
            the wallet, finalizes the transaction, signs it and
            broadacasts it

            :param operation ops: The operation (or list of operations) to
                broadcast
            :param operation account: The account that authorizes the
                operation
            :param string permission: The required permission for
                signing (active, owner, posting)
            :param object append_to: This allows to provide an instance of
                ProposalsBuilder (see :func:`steem.new_proposal`) or
                TransactionBuilder (see :func:`steem.new_tx()`) to specify
                where to put a specific operation.

            .. note:: ``append_to`` is exposed to every method used in the
                Steem class

            .. note::   If ``ops`` is a list of operation, they all need to be
                        signable by the same key! Thus, you cannot combine ops
                        that require active permission with ops that require
                        posting permission. Neither can you use different
                        accounts for different operations!

            .. note:: This uses ``beem.txbuffer`` as instance of
                :class:`beem.transactionbuilder.TransactionBuilder`.
                You may want to use your own txbuffer
        """
        if self.offline:
                return {}
        if "append_to" in kwargs and kwargs["append_to"]:

            # Append to the append_to and return
            append_to = kwargs["append_to"]
            parent = append_to.get_parent()
            if not isinstance(append_to, (TransactionBuilder)):
                raise AssertionError()
            append_to.appendOps(ops)
            # Add the signer to the buffer so we sign the tx properly
            parent.appendSigner(account, permission)
            # This returns as we used append_to, it does NOT broadcast, or sign
            return append_to.get_parent()
            # Go forward to see what the other options do ...
        else:
            # Append to the default buffer
            self.txbuffer.appendOps(ops)

        # Add signing information, signer, sign and optionally broadcast
        if self.unsigned:
            # In case we don't want to sign anything
            self.txbuffer.addSigningInformation(account, permission)
            return self.txbuffer
        elif self.bundle:
            # In case we want to add more ops to the tx (bundle)
            self.txbuffer.appendSigner(account, permission)
            return self.txbuffer.json()
        else:
            # default behavior: sign + broadcast
            self.txbuffer.appendSigner(account, permission)
            self.txbuffer.sign()
            return self.txbuffer.broadcast()

    def sign(self, tx=None, wifs=[]):
        """ Sign a provided transaction with the provided key(s)

            :param dict tx: The transaction to be signed and returned
            :param string wifs: One or many wif keys to use for signing
                a transaction. If not present, the keys will be loaded
                from the wallet as defined in "missing_signatures" key
                of the transactions.
        """
        if tx:
            txbuffer = TransactionBuilder(tx, steem_instance=self)
        else:
            txbuffer = self.txbuffer
        txbuffer.appendWif(wifs)
        txbuffer.appendMissingSignatures()
        txbuffer.sign()
        return txbuffer.json()

    def broadcast(self, tx=None):
        """ Broadcast a transaction to the Steem network

            :param tx tx: Signed transaction to broadcast

        """
        if tx:
            # If tx is provided, we broadcast the tx
            return TransactionBuilder(tx, steem_instance=self).broadcast()
        else:
            return self.txbuffer.broadcast()

    def info(self, use_stored_data=True):
        """ Returns the global properties
        """
        return self.get_dynamic_global_properties(use_stored_data=use_stored_data)

    # -------------------------------------------------------------------------
    # Wallet stuff
    # -------------------------------------------------------------------------
    def newWallet(self, pwd):
        """ Create a new wallet. This method is basically only calls
            :func:`beem.wallet.create`.

            :param str pwd: Password to use for the new wallet

            :raises beem.exceptions.WalletExists: if there is already a
                wallet created

        """
        return self.wallet.create(pwd)

    def unlock(self, *args, **kwargs):
        """ Unlock the internal wallet
        """
        return self.wallet.unlock(*args, **kwargs)

    # -------------------------------------------------------------------------
    # Transaction Buffers
    # -------------------------------------------------------------------------
    @property
    def txbuffer(self):
        """ Returns the currently active tx buffer
        """
        return self.tx()

    def tx(self):
        """ Returns the default transaction buffer
        """
        return self._txbuffers[0]

    def new_tx(self, *args, **kwargs):
        """ Let's obtain a new txbuffer

            :returns int txid: id of the new txbuffer
        """
        builder = TransactionBuilder(
            *args,
            steem_instance=self,
            **kwargs
        )
        self._txbuffers.append(builder)
        return builder

    def clear(self):
        self._txbuffers = []
        # Base/Default proposal/tx buffers
        self.new_tx()
        # self.new_proposal()

    # -------------------------------------------------------------------------
    # Account related calls
    # -------------------------------------------------------------------------
    def claim_account(self, creator, fee="0 STEEM", **kwargs):
        """"Claim account for claimed account creation.

            When fee is 0 STEEM a subsidized account is claimed and can be created
            later with create_claimed_account.
            The number of subsidized account is limited.

            :param str creator: which account should pay the registration fee (RC or STEEM)
                    (defaults to ``default_account``)
            :param str fee: when set to 0 STEEM, claim account is paid by RC
        """
        if not creator and config["default_account"]:
            creator = config["default_account"]
        if not creator:
            raise ValueError(
                "Not creator account given. Define it with " +
                "creator=x, or set the default_account using beempy")
        creator = Account(creator, steem_instance=self)
        op = {
            "fee": Amount(fee, steem_instance=self),
            "creator": creator["name"],
            "prefix": self.prefix,
        }
        op = operations.Claim_account(**op)
        return self.finalizeOp(op, creator, "active", **kwargs)

    def create_claimed_account(
        self,
        account_name,
        creator=None,
        owner_key=None,
        active_key=None,
        memo_key=None,
        posting_key=None,
        password=None,
        additional_owner_keys=[],
        additional_active_keys=[],
        additional_posting_keys=[],
        additional_owner_accounts=[],
        additional_active_accounts=[],
        additional_posting_accounts=[],
        storekeys=True,
        store_owner_key=False,
        json_meta=None,
        combine_with_claim_account=False,
        fee="0 STEEM",
        **kwargs
    ):
        """ Create new claimed account on Steem

            The brainkey/password can be used to recover all generated keys
            (see `beemgraphenebase.account` for more details.

            By default, this call will use ``default_account`` to
            register a new name ``account_name`` with all keys being
            derived from a new brain key that will be returned. The
            corresponding keys will automatically be installed in the
            wallet.

            .. warning:: Don't call this method unless you know what
                          you are doing! Be sure to understand what this
                          method does and where to find the private keys
                          for your account.

            .. note:: Please note that this imports private keys
                      (if password is present) into the wallet by
                      default when nobroadcast is set to False.
                      However, it **does not import the owner
                      key** for security reasons by default.
                      If you set store_owner_key to True, the
                      owner key is stored.
                      Do NOT expect to be able to recover it from
                      the wallet if you lose your password!

            .. note:: Account creations cost a fee that is defined by
                       the network. If you create an account, you will
                       need to pay for that fee!

            :param str account_name: (**required**) new account name
            :param str json_meta: Optional meta data for the account
            :param str owner_key: Main owner key
            :param str active_key: Main active key
            :param str posting_key: Main posting key
            :param str memo_key: Main memo_key
            :param str password: Alternatively to providing keys, one
                                 can provide a password from which the
                                 keys will be derived
            :param array additional_owner_keys:  Additional owner public keys
            :param array additional_active_keys: Additional active public keys
            :param array additional_posting_keys: Additional posting public keys
            :param array additional_owner_accounts: Additional owner account
                names
            :param array additional_active_accounts: Additional acctive account
                names
            :param bool storekeys: Store new keys in the wallet (default:
                ``True``)
            :param bool combine_with_claim_account: When set to True, a
                claim_account operation is additionally broadcasted
            :param str fee: When combine_with_claim_account is set to True,
                this parameter is used for the claim_account operation

            :param str creator: which account should pay the registration fee
                                (defaults to ``default_account``)
            :raises AccountExistsException: if the account already exists on
                the blockchain

        """
        if not creator and config["default_account"]:
            creator = config["default_account"]
        if not creator:
            raise ValueError(
                "Not creator account given. Define it with " +
                "creator=x, or set the default_account using beempy")
        if password and (owner_key or active_key or memo_key):
            raise ValueError(
                "You cannot use 'password' AND provide keys!"
            )

        try:
            Account(account_name, steem_instance=self)
            raise AccountExistsException
        except AccountDoesNotExistsException:
            pass

        creator = Account(creator, steem_instance=self)

        " Generate new keys from password"
        from beemgraphenebase.account import PasswordKey
        if password:
            active_key = PasswordKey(account_name, password, role="active", prefix=self.prefix)
            owner_key = PasswordKey(account_name, password, role="owner", prefix=self.prefix)
            posting_key = PasswordKey(account_name, password, role="posting", prefix=self.prefix)
            memo_key = PasswordKey(account_name, password, role="memo", prefix=self.prefix)
            active_pubkey = active_key.get_public_key()
            owner_pubkey = owner_key.get_public_key()
            posting_pubkey = posting_key.get_public_key()
            memo_pubkey = memo_key.get_public_key()
            active_privkey = active_key.get_private_key()
            posting_privkey = posting_key.get_private_key()
            owner_privkey = owner_key.get_private_key()
            memo_privkey = memo_key.get_private_key()
            # store private keys
            try:
                if storekeys and not self.nobroadcast:
                    if store_owner_key:
                        self.wallet.addPrivateKey(str(owner_privkey))
                    self.wallet.addPrivateKey(str(active_privkey))
                    self.wallet.addPrivateKey(str(memo_privkey))
                    self.wallet.addPrivateKey(str(posting_privkey))
            except ValueError as e:
                log.info(str(e))

        elif (owner_key and active_key and memo_key and posting_key):
            active_pubkey = PublicKey(
                active_key, prefix=self.prefix)
            owner_pubkey = PublicKey(
                owner_key, prefix=self.prefix)
            posting_pubkey = PublicKey(
                posting_key, prefix=self.prefix)
            memo_pubkey = PublicKey(
                memo_key, prefix=self.prefix)
        else:
            raise ValueError(
                "Call incomplete! Provide either a password or public keys!"
            )
        owner = format(owner_pubkey, self.prefix)
        active = format(active_pubkey, self.prefix)
        posting = format(posting_pubkey, self.prefix)
        memo = format(memo_pubkey, self.prefix)

        owner_key_authority = [[owner, 1]]
        active_key_authority = [[active, 1]]
        posting_key_authority = [[posting, 1]]
        owner_accounts_authority = []
        active_accounts_authority = []
        posting_accounts_authority = []

        # additional authorities
        for k in additional_owner_keys:
            owner_key_authority.append([k, 1])
        for k in additional_active_keys:
            active_key_authority.append([k, 1])
        for k in additional_posting_keys:
            posting_key_authority.append([k, 1])

        for k in additional_owner_accounts:
            addaccount = Account(k, steem_instance=self)
            owner_accounts_authority.append([addaccount["name"], 1])
        for k in additional_active_accounts:
            addaccount = Account(k, steem_instance=self)
            active_accounts_authority.append([addaccount["name"], 1])
        for k in additional_posting_accounts:
            addaccount = Account(k, steem_instance=self)
            posting_accounts_authority.append([addaccount["name"], 1])
        if combine_with_claim_account:
            op = {
                "fee": Amount(fee, steem_instance=self),
                "creator": creator["name"],
                "prefix": self.prefix,
            }
            op = operations.Claim_account(**op)
            ops = [op]
        op = {
            "creator": creator["name"],
            "new_account_name": account_name,
            'owner': {'account_auths': owner_accounts_authority,
                      'key_auths': owner_key_authority,
                      "address_auths": [],
                      'weight_threshold': 1},
            'active': {'account_auths': active_accounts_authority,
                       'key_auths': active_key_authority,
                       "address_auths": [],
                       'weight_threshold': 1},
            'posting': {'account_auths': active_accounts_authority,
                        'key_auths': posting_key_authority,
                        "address_auths": [],
                        'weight_threshold': 1},
            'memo_key': memo,
            "json_metadata": json_meta or {},
            "prefix": self.prefix,
        }
        op = operations.Create_claimed_account(**op)
        if combine_with_claim_account:
            ops.append(op)
            return self.finalizeOp(ops, creator, "active", **kwargs)
        else:
            return self.finalizeOp(op, creator, "active", **kwargs)

    def create_account(
        self,
        account_name,
        creator=None,
        owner_key=None,
        active_key=None,
        memo_key=None,
        posting_key=None,
        password=None,
        additional_owner_keys=[],
        additional_active_keys=[],
        additional_posting_keys=[],
        additional_owner_accounts=[],
        additional_active_accounts=[],
        additional_posting_accounts=[],
        storekeys=True,
        store_owner_key=False,
        json_meta=None,
        **kwargs
    ):
        """ Create new account on Steem

            The brainkey/password can be used to recover all generated keys
            (see `beemgraphenebase.account` for more details.

            By default, this call will use ``default_account`` to
            register a new name ``account_name`` with all keys being
            derived from a new brain key that will be returned. The
            corresponding keys will automatically be installed in the
            wallet.

            .. warning:: Don't call this method unless you know what
                          you are doing! Be sure to understand what this
                          method does and where to find the private keys
                          for your account.

            .. note:: Please note that this imports private keys
                      (if password is present) into the wallet by
                      default when nobroadcast is set to False.
                      However, it **does not import the owner
                      key** for security reasons by default.
                      If you set store_owner_key to True, the
                      owner key is stored.
                      Do NOT expect to be able to recover it from
                      the wallet if you lose your password!

            .. note:: Account creations cost a fee that is defined by
                       the network. If you create an account, you will
                       need to pay for that fee!

            :param str account_name: (**required**) new account name
            :param str json_meta: Optional meta data for the account
            :param str owner_key: Main owner key
            :param str active_key: Main active key
            :param str posting_key: Main posting key
            :param str memo_key: Main memo_key
            :param str password: Alternatively to providing keys, one
                                 can provide a password from which the
                                 keys will be derived
            :param array additional_owner_keys:  Additional owner public keys
            :param array additional_active_keys: Additional active public keys
            :param array additional_posting_keys: Additional posting public keys
            :param array additional_owner_accounts: Additional owner account
                names
            :param array additional_active_accounts: Additional acctive account
                names
            :param bool storekeys: Store new keys in the wallet (default:
                ``True``)

            :param str creator: which account should pay the registration fee
                                (defaults to ``default_account``)
            :raises AccountExistsException: if the account already exists on
                the blockchain

        """
        if not creator and config["default_account"]:
            creator = config["default_account"]
        if not creator:
            raise ValueError(
                "Not creator account given. Define it with " +
                "creator=x, or set the default_account using beempy")
        if password and (owner_key or active_key or memo_key):
            raise ValueError(
                "You cannot use 'password' AND provide keys!"
            )

        try:
            Account(account_name, steem_instance=self)
            raise AccountExistsException
        except AccountDoesNotExistsException:
            pass

        creator = Account(creator, steem_instance=self)

        " Generate new keys from password"
        from beemgraphenebase.account import PasswordKey
        if password:
            active_key = PasswordKey(account_name, password, role="active", prefix=self.prefix)
            owner_key = PasswordKey(account_name, password, role="owner", prefix=self.prefix)
            posting_key = PasswordKey(account_name, password, role="posting", prefix=self.prefix)
            memo_key = PasswordKey(account_name, password, role="memo", prefix=self.prefix)
            active_pubkey = active_key.get_public_key()
            owner_pubkey = owner_key.get_public_key()
            posting_pubkey = posting_key.get_public_key()
            memo_pubkey = memo_key.get_public_key()
            active_privkey = active_key.get_private_key()
            posting_privkey = posting_key.get_private_key()
            owner_privkey = owner_key.get_private_key()
            memo_privkey = memo_key.get_private_key()
            # store private keys
            try:
                if storekeys and not self.nobroadcast:
                    if store_owner_key:
                        self.wallet.addPrivateKey(str(owner_privkey))
                    self.wallet.addPrivateKey(str(active_privkey))
                    self.wallet.addPrivateKey(str(memo_privkey))
                    self.wallet.addPrivateKey(str(posting_privkey))
            except ValueError as e:
                log.info(str(e))

        elif (owner_key and active_key and memo_key and posting_key):
            active_pubkey = PublicKey(
                active_key, prefix=self.prefix)
            owner_pubkey = PublicKey(
                owner_key, prefix=self.prefix)
            posting_pubkey = PublicKey(
                posting_key, prefix=self.prefix)
            memo_pubkey = PublicKey(
                memo_key, prefix=self.prefix)
        else:
            raise ValueError(
                "Call incomplete! Provide either a password or public keys!"
            )
        owner = format(owner_pubkey, self.prefix)
        active = format(active_pubkey, self.prefix)
        posting = format(posting_pubkey, self.prefix)
        memo = format(memo_pubkey, self.prefix)

        owner_key_authority = [[owner, 1]]
        active_key_authority = [[active, 1]]
        posting_key_authority = [[posting, 1]]
        owner_accounts_authority = []
        active_accounts_authority = []
        posting_accounts_authority = []

        # additional authorities
        for k in additional_owner_keys:
            owner_key_authority.append([k, 1])
        for k in additional_active_keys:
            active_key_authority.append([k, 1])
        for k in additional_posting_keys:
            posting_key_authority.append([k, 1])

        for k in additional_owner_accounts:
            addaccount = Account(k, steem_instance=self)
            owner_accounts_authority.append([addaccount["name"], 1])
        for k in additional_active_accounts:
            addaccount = Account(k, steem_instance=self)
            active_accounts_authority.append([addaccount["name"], 1])
        for k in additional_posting_accounts:
            addaccount = Account(k, steem_instance=self)
            posting_accounts_authority.append([addaccount["name"], 1])

        props = self.get_chain_properties()
        required_fee_steem = Amount(props["account_creation_fee"], steem_instance=self)
        op = {
            "fee": required_fee_steem,
            "creator": creator["name"],
            "new_account_name": account_name,
            'owner': {'account_auths': owner_accounts_authority,
                      'key_auths': owner_key_authority,
                      "address_auths": [],
                      'weight_threshold': 1},
            'active': {'account_auths': active_accounts_authority,
                       'key_auths': active_key_authority,
                       "address_auths": [],
                       'weight_threshold': 1},
            'posting': {'account_auths': active_accounts_authority,
                        'key_auths': posting_key_authority,
                        "address_auths": [],
                        'weight_threshold': 1},
            'memo_key': memo,
            "json_metadata": json_meta or {},
            "prefix": self.prefix,
        }
        op = operations.Account_create(**op)
        return self.finalizeOp(op, creator, "active", **kwargs)

    def witness_set_properties(self, wif, owner, props, use_condenser_api=True):
        """ Set witness properties

            :param privkey wif: Private signing key
            :param dict props: Properties
            :param str owner: witness account name

            Properties:::

                {
                    "account_creation_fee": x,
                    "account_subsidy_budget": x,
                    "account_subsidy_decay": x,
                    "maximum_block_size": x,
                    "url": x,
                    "sbd_exchange_rate": x,
                    "sbd_interest_rate": x,
                    "new_signing_key": x
                }

        """

        owner = Account(owner, steem_instance=self)

        try:
            PrivateKey(wif, prefix=self.prefix)
        except Exception as e:
            raise e
        props_list = [["key", repr(PrivateKey(wif, prefix=self.prefix).pubkey)]]
        for k in props:
            props_list.append([k, props[k]])

        op = operations.Witness_set_properties({"owner": owner["name"], "props": props_list, "prefix": self.prefix})
        tb = TransactionBuilder(use_condenser_api=use_condenser_api, steem_instance=self)
        tb.appendOps([op])
        tb.appendWif(wif)
        tb.sign()
        return tb.broadcast()

    def witness_update(self, signing_key, url, props, account=None, **kwargs):
        """ Creates/updates a witness

            :param pubkey signing_key: Public signing key
            :param str url: URL
            :param dict props: Properties
            :param str account: (optional) witness account name

            Properties:::

                {
                    "account_creation_fee": x,
                    "maximum_block_size": x,
                    "sbd_interest_rate": x,
                }

        """
        if not account and config["default_account"]:
            account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        account = Account(account, steem_instance=self)

        try:
            PublicKey(signing_key, prefix=self.prefix)
        except Exception as e:
            raise e
        if "sbd_interest_rate" in props:
            props["sbd_interest_rate"] = Amount(props["sbd_interest_rate"], steem_instance=self)
        op = operations.Witness_update(
            **{
                "owner": account["name"],
                "url": url,
                "block_signing_key": signing_key,
                "props": props,
                "fee": Amount("0.000 STEEM", steem_instance=self),
                "prefix": self.prefix,
            })
        return self.finalizeOp(op, account, "active", **kwargs)

    def _test_weights_treshold(self, authority):
        """ This method raises an error if the threshold of an authority cannot
            be reached by the weights.

            :param dict authority: An authority of an account
            :raises ValueError: if the threshold is set too high
        """
        weights = 0
        for a in authority["account_auths"]:
            weights += int(a[1])
        for a in authority["key_auths"]:
            weights += int(a[1])
        if authority["weight_threshold"] > weights:
            raise ValueError("Threshold too restrictive!")
        if authority["weight_threshold"] == 0:
            raise ValueError("Cannot have threshold of 0")

    def custom_json(self,
                    id,
                    json_data,
                    required_auths=[],
                    required_posting_auths=[],
                    **kwargs):
        """ Create a custom json operation

            :param str id: identifier for the custom json (max length 32 bytes)
            :param json json_data: the json data to put into the custom_json
                operation
            :param list required_auths: (optional) required auths
            :param list required_posting_auths: (optional) posting auths

            Note: While reqired auths and required_posting_auths are both
            optional, one of the two are needed in order to send the custom
            json.

            .. code-block:: python

               steem.custom_json("id", "json_data",
               required_posting_auths=['account'])

        """
        account = None
        if len(required_auths):
            account = required_auths[0]
        elif len(required_posting_auths):
            account = required_posting_auths[0]
        else:
            raise Exception("At least one account needs to be specified")
        account = Account(account, full=False, steem_instance=self)
        op = operations.Custom_json(
            **{
                "json": json_data,
                "required_auths": required_auths,
                "required_posting_auths": required_posting_auths,
                "id": id,
                "prefix": self.prefix,
            })
        return self.finalizeOp(op, account, "posting", **kwargs)

    def post(self,
             title,
             body,
             author=None,
             permlink=None,
             reply_identifier=None,
             json_metadata=None,
             comment_options=None,
             community=None,
             app=None,
             tags=None,
             beneficiaries=None,
             self_vote=False,
             parse_body=False,
             **kwargs):
        """ Create a new post.
        If this post is intended as a reply/comment, `reply_identifier` needs
        to be set with the identifier of the parent post/comment (eg.
        `@author/permlink`).
        Optionally you can also set json_metadata, comment_options and upvote
        the newly created post as an author.
        Setting category, tags or community will override the values provided
        in json_metadata and/or comment_options where appropriate.

        :param str title: Title of the post
        :param str body: Body of the post/comment
        :param str author: Account are you posting from
        :param str permlink: Manually set the permlink (defaults to None).
            If left empty, it will be derived from title automatically.
        :param str reply_identifier: Identifier of the parent post/comment (only
            if this post is a reply/comment).
        :param str/dict json_metadata: JSON meta object that can be attached to
            the post.
        :param dict comment_options: JSON options object that can be
            attached to the post.

        Example::

            comment_options = {
                'max_accepted_payout': '1000000.000 SBD',
                'percent_steem_dollars': 10000,
                'allow_votes': True,
                'allow_curation_rewards': True,
                'extensions': [[0, {
                    'beneficiaries': [
                        {'account': 'account1', 'weight': 5000},
                        {'account': 'account2', 'weight': 5000},
                    ]}
                ]]
            }

        :param str community: (Optional) Name of the community we are posting
            into. This will also override the community specified in
            `json_metadata`.
        :param str app: (Optional) Name of the app which are used for posting
            when not set, beem/<version> is used
        :param str/list tags: (Optional) A list of tags to go with the
            post. This will also override the tags specified in
            `json_metadata`. The first tag will be used as a 'category'. If
            provided as a string, it should be space separated.
        :param list beneficiaries: (Optional) A list of beneficiaries
            for posting reward distribution. This argument overrides
            beneficiaries as specified in `comment_options`.

        For example, if we would like to split rewards between account1 and
        account2::

            beneficiaries = [
                {'account': 'account1', 'weight': 5000},
                {'account': 'account2', 'weight': 5000}
            ]

        :param bool self_vote: (Optional) Upvote the post as author, right after
            posting.
        :param bool parse_body: (Optional) When set to True, all mentioned users,
            used links and images are put into users, links and images array inside
            json_metadata. This will override provided links, images and users inside
            json_metadata. Hashtags will added to tags until its length is below five entries.

        """

        # prepare json_metadata
        json_metadata = json_metadata or {}
        if isinstance(json_metadata, str):
            json_metadata = json.loads(json_metadata)

        # override the community
        if community:
            json_metadata.update({'community': community})
        if app:
            json_metadata.update({'app': app})
        elif 'app' not in json_metadata:
            json_metadata.update({'app': 'beem/%s' % (beem_version)})

        if not author and config["default_account"]:
            author = config["default_account"]
        if not author:
            raise ValueError("You need to provide an account")
        account = Account(author, steem_instance=self)
        # deal with the category and tags
        if isinstance(tags, str):
            tags = list(OrderedDict({_f: None for _f in re.split("[\W_]", tags) if _f}))

        category = None
        tags = tags or json_metadata.get('tags', [])

        if parse_body:
            def get_urls(mdstring):
                return list(OrderedDict({_f: None for _f in re.findall('http[s]*://[^\s"><\)\(]+', mdstring)}))

            def get_users(mdstring):
                users = []
                for u in re.findall('(^|[^a-zA-Z0-9_!#$%&*@＠\/]|(^|[^a-zA-Z0-9_+~.-\/#]))[@＠]([a-z][-\.a-z\d]+[a-z\d])', mdstring):
                    users.append(list(u)[-1])
                return users

            def get_hashtags(mdstring):
                hashtags = []
                for t in re.findall('(^|\s)(#[-a-z\d]+)', mdstring):
                    hashtags.append(list(t)[-1])
                return hashtags

            image = []
            links = []
            for url in get_urls(body):
                img_exts = ['.jpg', '.png', '.gif', '.svg', '.jpeg']
                if os.path.splitext(url)[1].lower() in img_exts:
                    image.append(url)
                else:
                    links.append(url)
            users = get_users(body)
            hashtags = get_hashtags(body)
            users = list(set(users).difference(set([author])))
            if len(users) > 0:
                json_metadata.update({"users": users})
            if len(image) > 0:
                json_metadata.update({"image": image})
            if len(links) > 0:
                json_metadata.update({"links": links})
            if len(tags) < 5:
                for i in range(5 - len(tags)):
                    if len(hashtags) > i:
                        tags.append(hashtags[i])

        if tags:
            # first tag should be a category
            category = tags[0]
            json_metadata.update({"tags": tags})

        # can't provide a category while replying to a post
        if reply_identifier and category:
            category = None

        # deal with replies/categories
        if reply_identifier:
            parent_author, parent_permlink = resolve_authorperm(
                reply_identifier)
            if not permlink:
                permlink = derive_permlink(title, parent_permlink)
        elif category:
            parent_permlink = derive_permlink(category)
            parent_author = ""
            if not permlink:
                permlink = derive_permlink(title)
        else:
            parent_author = ""
            parent_permlink = ""
            if not permlink:
                permlink = derive_permlink(title)

        post_op = operations.Comment(
            **{
                "parent_author": parent_author,
                "parent_permlink": parent_permlink,
                "author": account["name"],
                "permlink": permlink,
                "title": title,
                "body": body,
                "json_metadata": json_metadata
            })
        ops = [post_op]

        # if comment_options are used, add a new op to the transaction
        if comment_options or beneficiaries:
            comment_op = self._build_comment_options_op(account['name'],
                                                        permlink,
                                                        comment_options,
                                                        beneficiaries)
            ops.append(comment_op)

        if self_vote:
            vote_op = operations.Vote(
                **{
                    'voter': account["name"],
                    'author': account["name"],
                    'permlink': permlink,
                    'weight': STEEM_100_PERCENT,
                })
            ops.append(vote_op)

        return self.finalizeOp(ops, account, "posting", **kwargs)

    def comment_options(self, options, identifier, beneficiaries=[],
                        account=None, **kwargs):
        """ Set the comment options

            :param dict options: The options to define.
            :param str identifier: Post identifier
            :param list beneficiaries: (optional) list of beneficiaries
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)

            For the options, you have these defaults:::

                {
                    "author": "",
                    "permlink": "",
                    "max_accepted_payout": "1000000.000 SBD",
                    "percent_steem_dollars": 10000,
                    "allow_votes": True,
                    "allow_curation_rewards": True,
                }

        """
        if not account and config["default_account"]:
            account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self)
        author, permlink = resolve_authorperm(identifier)
        op = self._build_comment_options_op(author, permlink, options,
                                            beneficiaries)
        return self.finalizeOp(op, account, "posting", **kwargs)

    def _build_comment_options_op(self, author, permlink, options,
                                  beneficiaries):
        options = remove_from_dict(options or {}, [
            'max_accepted_payout', 'percent_steem_dollars',
            'allow_votes', 'allow_curation_rewards', 'extensions'
        ], keep_keys=True)
        # override beneficiaries extension
        if beneficiaries:
            # validate schema
            # or just simply vo.Schema([{'account': str, 'weight': int}])

            weight_sum = 0
            for b in beneficiaries:
                if 'account' not in b:
                    raise ValueError(
                        "beneficiaries need an account field!"
                    )
                if 'weight' not in b:
                    b['weight'] = STEEM_100_PERCENT
                if len(b['account']) > 16:
                    raise ValueError(
                        "beneficiaries error, account name length >16!"
                    )
                if b['weight'] < 1 or b['weight'] > STEEM_100_PERCENT:
                    raise ValueError(
                        "beneficiaries error, 1<=weight<=%s!" %
                        (STEEM_100_PERCENT)
                    )
                weight_sum += b['weight']

            if weight_sum > STEEM_100_PERCENT:
                raise ValueError(
                    "beneficiaries exceed total weight limit %s" %
                    STEEM_100_PERCENT
                )

            options['beneficiaries'] = beneficiaries

        default_max_payout = "1000000.000 SBD"
        comment_op = operations.Comment_options(
            **{
                "author":
                author,
                "permlink":
                permlink,
                "max_accepted_payout":
                options.get("max_accepted_payout", default_max_payout),
                "percent_steem_dollars":
                int(options.get("percent_steem_dollars", STEEM_100_PERCENT)),
                "allow_votes":
                options.get("allow_votes", True),
                "allow_curation_rewards":
                options.get("allow_curation_rewards", True),
                "extensions":
                options.get("extensions", []),
                "beneficiaries":
                options.get("beneficiaries", []),
            })
        return comment_op

    def get_api_methods(self):
        """Returns all supported api methods"""
        return self.rpc.get_methods(api="jsonrpc")

    def get_apis(self):
        """Returns all enabled apis"""
        api_methods = self.get_api_methods()
        api_list = []
        for a in api_methods:
            api = a.split(".")[0]
            if api not in api_list:
                api_list.append(api)
        return api_list
