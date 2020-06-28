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
from beemgraphenebase.chains import known_chains
from .amount import Amount
from .utils import formatTime, resolve_authorperm, derive_permlink, sanitize_permlink, remove_from_dict, addTzInfo, formatToTimeStamp
from beem.constants import STEEM_VOTE_REGENERATION_SECONDS, STEEM_100_PERCENT, STEEM_1_PERCENT, STEEM_RC_REGEN_TIME
from beem.blockchaininstance import BlockChainInstance
log = logging.getLogger(__name__)


class Blurt(BlockChainInstance):
    """ Connect to the Blurt network.

        :param str node: Node to connect to *(optional)*
        :param str rpcuser: RPC user *(optional)*
        :param str rpcpassword: RPC password *(optional)*
        :param bool nobroadcast: Do **not** broadcast a transaction!
            *(optional)*
        :param bool unsigned: Do **not** sign a transaction! *(optional)*
        :param bool debug: Enable Debugging *(optional)*
        :param keys: Predefine the wif keys to shortcut the
            wallet database *(optional)*
        :type keys: array, dict, string
        :param wif: Predefine the wif keys to shortcut the
                wallet database *(optional)*
        :type wif: array, dict, string
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
        :param dict custom_chains: custom chain which should be added to the known chains

        Three wallet operation modes are possible:

        * **Wallet Database**: Here, the steemlibs load the keys from the
          locally stored wallet SQLite database (see ``storage.py``).
          To use this mode, simply call ``Blurt()`` without the
          ``keys`` parameter
        * **Providing Keys**: Here, you can provide the keys for
          your accounts manually. All you need to do is add the wif
          keys for the accounts you want to use as a simple array
          using the ``keys`` parameter to ``Blurt()``.
        * **Force keys**: This more is for advanced users and
          requires that you know what you are doing. Here, the
          ``keys`` parameter is a dictionary that overwrite the
          ``active``, ``owner``, ``posting`` or ``memo`` keys for
          any account. This mode is only used for *foreign*
          signatures!

        If no node is provided, it will connect to default nodes of
        http://geo.steem.pl. Default settings can be changed with:

        .. code-block:: python

            steem = Blurt(<host>)

        where ``<host>`` starts with ``https://``, ``ws://`` or ``wss://``.

        The purpose of this class it to simplify interaction with
        Blurt.

        The idea is to have a class that allows to do this:

        .. code-block:: python

            >>> from beem import Blurt
            >>> steem = Blurt()
            >>> print(steem.get_blockchain_version())  # doctest: +SKIP

        This class also deals with edits, votes and reading content.

        Example for adding a custom chain:

        .. code-block:: python

            from beem import Blurt
            stm = Blurt(node=["https://mytstnet.com"], custom_chains={"MYTESTNET":
                {'chain_assets': [{'asset': 'BLURT', 'id': 1, 'precision': 3, 'symbol': 'BLURT'},
                                  {'asset': 'VESTS', 'id': 2, 'precision': 6, 'symbol': 'VESTS'}],
                 'chain_id': '79276aea5d4877d9a25892eaa01b0adf019d3e5cb12a97478df3298ccdd01674',
                 'min_version': '0.0.0',
                 'prefix': 'BLT'}
                }
            )

    """

    def get_network(self, use_stored_data=True, config=None):
        """ Identify the network

            :param bool use_stored_data: if True, stored data will be returned. If stored data are
                                         empty or old, refresh_data() is used.

            :returns: Network parameters
            :rtype: dictionary
        """
        if use_stored_data:
            self.refresh_data('config')
            return self.data['network']

        if self.rpc is None:
            return known_chains["BLURT"]
        try:
            return self.rpc.get_network(props=config)
        except:
            return known_chains["BLURT"]

    def get_blurt_per_mvest(self, time_stamp=None, use_stored_data=True):
        """ Returns the MVEST to BLURT ratio

            :param int time_stamp: (optional) if set, return an estimated
                STEEM per MVEST ratio for the given time stamp. If unset the
                current ratio is returned (default). (can also be a datetime object)
        """
        if self.offline and time_stamp is None:
            time_stamp =datetime.utcnow()

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
            float(Amount(global_properties['total_vesting_fund_blurt'], blockchain_instance=self)) /
            (float(Amount(global_properties['total_vesting_shares'], blockchain_instance=self)) / 1e6)
        )

    def vests_to_bp(self, vests, timestamp=None, use_stored_data=True):
        """ Converts vests to BP

            :param amount.Amount vests/float vests: Vests to convert
            :param int timestamp: (Optional) Can be used to calculate
                the conversion rate from the past

        """
        if isinstance(vests, Amount):
            vests = float(vests)
        return float(vests) / 1e6 * self.get_blurt_per_mvest(timestamp, use_stored_data=use_stored_data)

    def vests_to_token_power(self, vests, timestamp=None, use_stored_data=True):
        return self.vests_to_bp(vests, timestamp=timestamp, use_stored_data=use_stored_data)

    def token_power_to_vests(self, token_power, timestamp=None, use_stored_data=True):
        return self.bp_to_vests(token_power, timestamp=timestamp, use_stored_data=use_stored_data)

    def get_token_per_mvest(self, time_stamp=None, use_stored_data=True):
        return self.get_blurt_per_mvest(time_stamp=time_stamp, use_stored_data=use_stored_data)

    def bp_to_vests(self, sp, timestamp=None, use_stored_data=True):
        """ Converts SP to vests

            :param float sp: Blurt power to convert
            :param datetime timestamp: (Optional) Can be used to calculate
                the conversion rate from the past
        """
        return sp * 1e6 / self.get_blurt_per_mvest(timestamp, use_stored_data=use_stored_data)

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

    def bp_to_rshares(self, blurt_power, post_rshares=0, voting_power=STEEM_100_PERCENT, vote_pct=STEEM_100_PERCENT, use_stored_data=True):
        """ Obtain the r-shares from Blurt power

            :param number blurt_power: Blurt Power
            :param int post_rshares: rshares of post which is voted
            :param int voting_power: voting power (100% = 10000)
            :param int vote_pct: voting percentage (100% = 10000)

        """
        # calculate our account voting shares (from vests)
        vesting_shares = int(self.sp_to_vests(blurt_power, use_stored_data=use_stored_data))
        return self.vests_to_rshares(vesting_shares, post_rshares=post_rshares, voting_power=voting_power, vote_pct=vote_pct, use_stored_data=use_stored_data)

    def vests_to_rshares(self, vests, post_rshares=0, voting_power=STEEM_100_PERCENT, vote_pct=STEEM_100_PERCENT, subtract_dust_threshold=True, use_stored_data=True):
        """ Obtain the r-shares from vests

            :param number vests: vesting shares
            :param int post_rshares: rshares of post which is voted
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
        rshares = self._calc_vote_claim(rshares, post_rshares)        
        return rshares

    def rshares_to_vote_pct(self, rshares, post_rshares=0, blurt_power=None, vests=None, voting_power=STEEM_100_PERCENT, use_stored_data=True):
        """ Obtain the voting percentage for a desired rshares value
            for a given Blurt Power or vesting shares and voting_power
            Give either blurt_power or vests, not both.
            When the output is greater than 10000 or less than -10000,
            the given absolute rshares are too high

            Returns the required voting percentage (100% = 10000)

            :param number rshares: desired rshares value
            :param number blurt_power: Blurt Power
            :param number vests: vesting shares
            :param int voting_power: voting power (100% = 10000)

        """
        if blurt_power is None and vests is None:
            raise ValueError("Either blurt_power or vests has to be set!")
        if blurt_power is not None and vests is not None:
            raise ValueError("Either blurt_power or vests has to be set. Not both!")
        if blurt_power is not None:
            vests = int(self.sp_to_vests(blurt_power, use_stored_data=use_stored_data) * 1e6)

        if self.hardfork >= 20:
            rshares += math.copysign(self.get_dust_threshold(use_stored_data=use_stored_data), rshares)

        if post_rshares >= 0 and rshares > 0:
            rshares = math.copysign(self._calc_revert_vote_claim(abs(rshares), post_rshares), rshares)

        max_vote_denom = self._max_vote_denom(use_stored_data=use_stored_data)

        used_power = int(math.ceil(abs(rshares) * STEEM_100_PERCENT / vests))
        used_power = used_power * max_vote_denom

        vote_pct = used_power * STEEM_100_PERCENT / (60 * 60 * 24) / voting_power
        return int(math.copysign(vote_pct, rshares))

    @property
    def chain_params(self):
        if self.offline or self.rpc is None:
            return known_chains["BLURT"]
        else:
            return self.get_network()

    @property
    def hardfork(self):
        if self.offline or self.rpc is None:
            versions = known_chains['BLURT']['min_version']
        else:
            hf_prop = self.get_hardfork_properties()
            if "current_hardfork_version" in hf_prop:
                versions = hf_prop["current_hardfork_version"]
            else:
                versions = self.get_blockchain_version()
        return int(versions.split('.')[1])

    @property
    def is_blurt(self):
        config = self.get_config()
        if config is None:
            return True
        return 'BLURT_CHAIN_ID' in self.get_config()

    @property
    def blurt_symbol(self):
        """ get the current chains symbol for BLURT (e.g. "TESTS" on testnet) """
        return self._get_asset_symbol(1)

    @property
    def vests_symbol(self):
        """ get the current chains symbol for VESTS """
        return self._get_asset_symbol(2)
