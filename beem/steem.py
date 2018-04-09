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
import math
from beemgraphenebase.py23 import bytes_types, integer_types, string_types, text_type
from datetime import datetime, timedelta
from beemapi.steemnoderpc import SteemNodeRPC
from beemapi.exceptions import NoAccessApi
from beemgraphenebase.account import PrivateKey, PublicKey
from beembase import transactions, operations
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
from .transactionbuilder import TransactionBuilder
from .utils import formatTime, resolve_authorperm, derive_permlink, remove_from_dict

log = logging.getLogger(__name__)


class Steem(object):
    """ Connect to the Steem network.

        :param str node: Node to connect to *(optional)*
        :param str rpcuser: RPC user *(optional)*
        :param str rpcpassword: RPC password *(optional)*
        :param bool nobroadcast: Do **not** broadcast a transaction!
            *(optional)*
        :param bool debug: Enable Debugging *(optional)*
        :param array,dict,string keys: Predefine the wif keys to shortcut the
            wallet database *(optional)*
        :param array,dict,string wif: Predefine the wif keys to shortcut the
                wallet database *(optional)*
        :param bool offline: Boolean to prevent connecting to network (defaults
            to ``False``) *(optional)*
        :param int expiration: Delay in seconds until transactions are supposed
            to expire *(optional)*
        :param str blocking: Wait for broadcasted transactions to be included
            in a block and return full transaction (can be "head" or
            "irrversible")
        :param bool bundle: Do not broadcast transactions right away, but allow
            to bundle operations *(optional)*
        :param bool appbase: Use the new appbase rpc protocol on nodes with version
            0.19.4 or higher. The settings has no effect on nodes with version of 0.19.3 or lower.

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

        where ``<host>`` starts with ``ws://`` or ``wss://``.

        The purpose of this class it to simplify interaction with
        Steem.

        The idea is to have a class that allows to do this:

        .. code-block:: python

            from beem import Steem
            steem = Steem()
            print(steem.info())

        This class also deals with edits, votes and reading content.
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
            :param bool debug: Enable Debugging *(optional)*
            :param array,dict,string keys: Predefine the wif keys to shortcut the
                wallet database *(optional)*
            :param array,dict,string wif: Predefine the wif keys to shortcut the
                wallet database *(optional)*
            :param bool offline: Boolean to prevent connecting to network (defaults
                to ``False``) *(optional)*
            :param int expiration: Delay in seconds until transactions are supposed
                to expire *(optional)*
            :param str blocking: Wait for broadcasted transactions to be included
                in a block and return full transaction (can be "head" or
                "irrversible")
            :param bool bundle: Do not broadcast transactions right away, but allow
                to bundle operations *(optional)*
            :param bool appbase: Use the new appbase rpc protocol on nodes with version
                0.19.4 or higher. The settings has no effect on nodes with version of 0.19.3 or lower.
            :param int num_retries: Set the maximum number of reconnects to the nodes before NumRetriesReached is raised
        """

        self.rpc = None
        self.debug = debug

        self.offline = bool(kwargs.get("offline", False))
        self.nobroadcast = bool(kwargs.get("nobroadcast", False))
        self.unsigned = bool(kwargs.get("unsigned", False))
        self.expiration = int(kwargs.get("expiration", 30))
        self.bundle = bool(kwargs.get("bundle", False))
        self.blocking = kwargs.get("blocking", False)
        appbase = kwargs.get("appbase", True)

        # Store config for access through other Classes
        self.config = config

        if not self.offline:
            self.connect(node=node,
                         rpcuser=rpcuser,
                         rpcpassword=rpcpassword,
                         **kwargs)
            self.rpc.appbase = appbase

        self.data = {'last_refresh': None, 'dynamic_global_properties': None, 'feed_history': None,
                     'get_feed_history': None, 'hardfork_properties': None,
                     'network': None, 'witness_schedule': None, 'reserve_ratio': None,
                     'config': None, 'reward_funds': None}
        self.data_refresh_time_seconds = data_refresh_time_seconds
        # self.refresh_data()

        # txbuffers/propbuffer are initialized and cleared
        self.clear()

        self.wallet = Wallet(steem_instance=self, **kwargs)

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
            if "node" in config:
                node = config["node"]
            else:
                raise ValueError("A Steem node needs to be provided!")

        if not rpcuser and "rpcuser" in config:
            rpcuser = config["rpcuser"]

        if not rpcpassword and "rpcpassword" in config:
            rpcpassword = config["rpcpassword"]

        self.rpc = SteemNodeRPC(node, rpcuser, rpcpassword, **kwargs)

    def is_connected(self):
        """Returns if rpc is connected"""
        return self.rpc is not None

    def refresh_data(self, force_refresh=False, data_refresh_time_seconds=None):
        """
        Read and stores steem blockchain parameters
        If the last data refresh is older than data_refresh_time_seconds, data will be refreshed

            :param bool force_refresh: if True, data are forced to refreshed
            :param float data_refresh_time_seconds: set a new minimal refresh time in seconds
        """
        if self.offline:
            return
        if data_refresh_time_seconds is not None:
            self.data_refresh_time_seconds = data_refresh_time_seconds
        if self.data['last_refresh'] is not None and not force_refresh:
            if (datetime.now() - self.data['last_refresh']).total_seconds() < self.data_refresh_time_seconds:
                return
        self.data['last_refresh'] = datetime.now()
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
        count = 0
        ret = None
        while ret is None and count < 2:
            try:
                ret = self.rpc.get_dynamic_global_properties(api="database")
            except:
                ret = None
            count += 1
        return ret

    def get_reserve_ratio(self, use_stored_data=True):
        """ This call returns the *dynamic global properties*
            :param bool use_stored_data: if True, stored data will be returned. If stored data are
            empty or old, refresh_data() is used.
        """
        if use_stored_data:
            self.refresh_data()
            return self.data['reserve_ratio']

        if self.rpc is None:
            return None
        count = 0
        ret = None
        while ret is None and count < 2:
            try:
                if self.rpc.get_use_appbase():
                    return self.rpc.get_reserve_ratio(api="witness")
                else:
                    props = self.get_dynamic_global_properties()
                    return {'id': 0, 'average_block_size': props['average_block_size'],
                            'current_reserve_ratio': props['current_reserve_ratio'],
                            'max_virtual_bandwidth': props['max_virtual_bandwidth']}
            except:
                ret = None
            count += 1
        return ret

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
        count = 0
        ret = None
        while ret is None and count < 2:
            try:
                ret = self.rpc.get_feed_history(api="database")
            except:
                ret = None
            count += 1
        return ret

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
        count = 0
        ret = None
        while ret is None and count < 2:
            try:
                if self.rpc.get_use_appbase():
                    funds = self.rpc.get_reward_funds(api="database")['funds']
                    if len(funds) > 0:
                        funds = funds[0]
                    ret = funds
                else:
                    ret = self.rpc.get_reward_fund("post")
            except:
                ret = None
            count += 1
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
        count = 0
        ret = None
        while ret is None and count < 2:
            try:
                if self.rpc.get_use_appbase():
                    ret = self.rpc.get_feed_history(api="database")['current_median_history']
                else:
                    ret = self.rpc.get_current_median_history_price(api="database")
            except:
                ret = None
            count += 1
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
        count = 0
        ret = None
        while ret is None and count < 2:
            try:
                if self.rpc.get_use_appbase():
                    ret = self.rpc.get_hardfork_properties(api="database")
                else:
                    ret = self.rpc.get_next_scheduled_hardfork(api="database")
            except:
                ret = None
            count += 1
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
            return None

    def get_median_price(self):
        """ Returns the current median history price as Price
        """
        median_price = self.get_current_median_history()
        a = Price(
            None,
            base=Amount(median_price['base'], steem_instance=self),
            quote=Amount(median_price['quote'], steem_instance=self),
        )
        return a.as_base("SBD")

    def get_block_interval(self):
        """Returns the block intervall in seconds"""
        props = self.get_config()
        if props and "STEEMIT_BLOCK_INTERVAL" in props:
            block_interval = props["STEEMIT_BLOCK_INTERVAL"]
        elif props and "STEEM_BLOCK_INTERVAL" in props:
            block_interval = props["STEEM_BLOCK_INTERVAL"]
        else:
            block_interval = 3
        return block_interval

    def get_blockchain_version(self):
        """Returns the blockchain version"""
        props = self.get_config()
        if props and "STEEMIT_BLOCKCHAIN_VERSION" in props:
            blockchain_version = props["STEEMIT_BLOCKCHAIN_VERSION"]
        elif props and "STEEM_BLOCKCHAIN_VERSION" in props:
            blockchain_version = props["STEEM_BLOCKCHAIN_VERSION"]
        else:
            blockchain_version = '0.0.0'
        return blockchain_version

    def rshares_to_sbd(self, rshares):
        """ Calculates the SBD amount of a vote
        """
        payout = float(rshares) * self.get_sbd_per_rshares()
        return payout

    def get_sbd_per_rshares(self):
        """ Returns the current rshares to SBD ratio
        """
        reward_fund = self.get_reward_funds()
        reward_balance = Amount(reward_fund["reward_balance"], steem_instance=self).amount
        recent_claims = float(reward_fund["recent_claims"])

        fund_per_share = reward_balance / (recent_claims)
        SBD_price = (self.get_median_price() * Amount("1 STEEM", steem_instance=self)).amount
        return fund_per_share * SBD_price

    def get_steem_per_mvest(self, time_stamp=None):
        """ Returns the current mvest to steem ratio
        """
        if time_stamp is not None:
            a = 2.1325476281078992e-05
            b = -31099.685481490847
            a2 = 2.9019227739473682e-07
            b2 = 48.41432402074669

            if (time_stamp < (b2 - b) / (a - a2)):
                return a * time_stamp + b
            else:
                return a2 * time_stamp + b2
        global_properties = self.get_dynamic_global_properties()

        return (
            Amount(global_properties['total_vesting_fund_steem'], steem_instance=self).amount /
            (Amount(global_properties['total_vesting_shares'], steem_instance=self).amount / 1e6)
        )

    def vests_to_sp(self, vests, timestamp=None):
        if isinstance(vests, Amount):
            vests = vests.amount
        return vests / 1e6 * self.get_steem_per_mvest(timestamp)

    def sp_to_vests(self, sp, timestamp=None):
        return sp * 1e6 / self.get_steem_per_mvest(timestamp)

    def sp_to_sbd(self, sp, voting_power=10000, vote_pct=10000):
        """ Obtain the resulting sbd amount from Steem power
            :param number steem_power: Steem Power
            :param int voting_power: voting power (100% = 10000)
            :param int vote_pct: voting participation (100% = 10000)
        """
        vesting_shares = int(self.sp_to_vests(sp))
        return self.vests_to_sbd(vesting_shares, voting_power=voting_power, vote_pct=vote_pct)

    def vests_to_sbd(self, vests, voting_power=10000, vote_pct=10000):
        """ Obtain the resulting sbd voting amount from vests
            :param number vests: vesting shares
            :param int voting_power: voting power (100% = 10000)
            :param int vote_pct: voting participation (100% = 10000)
        """
        reward_fund = self.get_reward_funds()
        reward_balance = Amount(reward_fund["reward_balance"], steem_instance=self).amount
        recent_claims = float(reward_fund["recent_claims"])
        reward_share = reward_balance / recent_claims

        resulting_vote = self._calc_resulting_vote(voting_power=voting_power, vote_pct=vote_pct)
        SBD_price = (self.get_median_price() * Amount("1 STEEM", steem_instance=self)).amount
        VoteValue = (vests * resulting_vote * 100) * reward_share * SBD_price
        return VoteValue

    def _max_vote_denom(self):
        # get props
        global_properties = self.get_dynamic_global_properties()
        vote_power_reserve_rate = global_properties['vote_power_reserve_rate']
        max_vote_denom = vote_power_reserve_rate * (5 * 60 * 60 * 24) / (60 * 60 * 24)
        return max_vote_denom

    def _calc_resulting_vote(self, voting_power=10000, vote_pct=10000):
        # determine voting power used
        used_power = int((voting_power * vote_pct) / 10000)
        max_vote_denom = self._max_vote_denom()
        used_power = int((used_power + max_vote_denom - 1) / max_vote_denom)
        return used_power

    def sp_to_rshares(self, steem_power, voting_power=10000, vote_pct=10000):
        """ Obtain the r-shares from Steem power
            :param number steem_power: Steem Power
            :param int voting_power: voting power (100% = 10000)
            :param int vote_pct: voting participation (100% = 10000)
        """
        # calculate our account voting shares (from vests)
        vesting_shares = int(self.sp_to_vests(steem_power) * 1e6)
        return self.vests_to_rshares(vesting_shares, voting_power=voting_power, vote_pct=vote_pct)

    def vests_to_rshares(self, vests, voting_power=10000, vote_pct=10000):
        """ Obtain the r-shares from vests
            :param number vests: vesting shares
            :param int voting_power: voting power (100% = 10000)
            :param int vote_pct: voting participation (100% = 10000)
        """
        used_power = self._calc_resulting_vote(voting_power=voting_power, vote_pct=vote_pct)
        # calculate vote rshares
        rshares = int((vests * used_power) / 10000)
        return rshares

    def rshares_to_vote_pct(self, rshares, steem_power=None, vests=None, voting_power=10000):
        """ Obtain the voting percentage for a desired rshares value
            for a given Steem Power or vesting shares and voting_power
            Give either steem_power or vests, not both.
            When the output is greater than 10000, the given rshares
            are to high

            Returns the voting participation (100% = 10000)

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
            vests = int(self.sp_to_vests(steem_power) * 1e6)

        max_vote_denom = self._max_vote_denom()

        used_power = int(math.ceil(rshares * 10000 / vests))
        used_power = used_power * max_vote_denom

        vote_pct = int(used_power * 10000 / voting_power)
        return vote_pct

    def get_chain_properties(self, use_stored_data=True):
        """ Return witness elected chain properties

            ::
                {'account_creation_fee': '30.000 STEEM',
                 'maximum_block_size': 65536,
                 'sbd_interest_rate': 250}
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
        count = 0
        ret = None
        while ret is None and count < 2:
            try:
                ret = self.rpc.get_witness_schedule(api="database")
            except:
                ret = None
            count += 1
        return ret

    def get_config(self, use_stored_data=True):
        """ Returns internal chain configuration.
        """
        if use_stored_data:
            self.refresh_data()
            return self.data['config']
        if self.rpc is None:
            return None
        count = 0
        ret = None
        while ret is None and count < 2:
            try:
                ret = self.rpc.get_config(api="database")
            except:
                ret = None
            count += 1
        return ret

    @property
    def chain_params(self):
        if self.offline:
            from beembase.chains import known_chains
            return known_chains["STEEM"]
        else:
            return self.rpc.chain_params

    @property
    def prefix(self):
        return self.chain_params["prefix"]

    def set_default_account(self, account):
        """ Set the default account to be used
        """
        Account(account, steem_instance=self)
        config["default_account"] = account

    def finalizeOp(self, ops, account, permission, **kwargs):
        """ This method obtains the required private keys if present in
            the wallet, finalizes the transaction, signs it and
            broadacasts it

            :param operation ops: The operation (or list of operaions) to
                broadcast
            :param operation account: The account that authorizes the
                operation
            :param string permission: The required permission for
                signing (active, owner, posting)
            :param object append_to: This allows to provide an instance of
                ProposalsBuilder (see :func:`steem.new_proposal`) or
                TransactionBuilder (see :func:`steem.new_tx()`) to specify
                where to put a specific operation.

            ... note:: ``append_to`` is exposed to every method used in the
                Steem class

            ... note::

                If ``ops`` is a list of operation, they all need to be
                signable by the same key! Thus, you cannot combine ops
                that require active permission with ops that require
                posting permission. Neither can you use different
                accounts for different operations!

            ... note:: This uses ``beem.txbuffer`` as instance of
                :class:`beem.transactionbuilder.TransactionBuilder`.
                You may want to use your own txbuffer
        """
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
        """ Sign a provided transaction witht he provided key(s)

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
            return TransactionBuilder(tx).broadcast()
        else:
            return self.txbuffer.broadcast()

    def info(self):
        """ Returns the global properties
        """
        return self.get_dynamic_global_properties()

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
        delegation_fee_steem='0 STEEM',
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
                      default. However, it **does not import the owner
                      key** for security reasons. Do NOT expect to be
                      able to recover it from the wallet if you lose
                      your password!

            .. note:: Account creations cost a fee that is defined by
                       the network. If you create an account, you will
                       need to pay for that fee!
                       **You can partially pay that fee by delegating VESTS.**
                       To pay the fee in full in STEEM, leave
                       ``delegation_fee_steem`` set to ``0 STEEM`` (Default).
                       To pay the fee partially in STEEM, partially with delegated
                       VESTS, set ``delegation_fee_steem`` to a value greater than ``1
                       STEEM``. `Required VESTS will be calculated automatically.`
                       To pay the fee with maximum amount of delegation, set
                       ``delegation_fee_steem`` to ``1 STEEM``. `Required VESTS will be
                       calculated automatically.`

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
            :param delegation_fee_steem: If set, `creator` pay a
                fee of this amount, and delegate the rest with VESTS (calculated
                automatically). Minimum: 1 STEEM. If left to 0 (Default), full fee
                is paid without VESTS delegation.
            :param str creator: which account should pay the registration fee
                                (defaults to ``default_account``)
            :raises AccountExistsException: if the account already exists on
                the blockchain

        """
        if not creator and config["default_account"]:
            creator = config["default_account"]
        if not creator:
            raise ValueError(
                "Not registrar account given. Define it with " +
                "registrar=x, or set the default_account using uptick")
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
        if isinstance(delegation_fee_steem, string_types):
            delegation_fee_steem = Amount(delegation_fee_steem, steem_instance=self)
        elif isinstance(delegation_fee_steem, Amount):
            delegation_fee_steem = Amount(delegation_fee_steem, steem_instance=self)
        else:
            delegation_fee_steem = Amount(delegation_fee_steem, "STEEM", steem_instance=self)
        if not delegation_fee_steem["symbol"] == "STEEM":
            raise AssertionError()

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
                if storekeys:
                    if store_owner_key:
                        self.wallet.addPrivateKey(owner_privkey)
                    self.wallet.addPrivateKey(active_privkey)
                    self.wallet.addPrivateKey(memo_privkey)
                    self.wallet.addPrivateKey(posting_privkey)
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
        required_fee_steem = Amount(props["account_creation_fee"], steem_instance=self) * 30
        if delegation_fee_steem.amount:
            # creating accounts without delegation requires 30x
            # account_creation_fee creating account with delegation allows one
            # to use VESTS to pay the fee where the ratio must satisfy 1 STEEM
            # in fee == 5 STEEM in delegated VESTS

            delegated_sp_fee_mult = 5

            if delegation_fee_steem.amount < 1:
                raise ValueError(
                    "When creating account with delegation, at least " +
                    "1 STEEM in fee must be paid.")

            # calculate required remaining fee in vests
            remaining_fee = required_fee_steem - delegation_fee_steem
            if remaining_fee.amount > 0:
                required_sp = remaining_fee.amount * delegated_sp_fee_mult
                required_fee_vests = Amount(self.sp_to_vests(required_sp) + 1, "VESTS", steem_instance=self)
            op = {
                "fee": delegation_fee_steem,
                'delegation': required_fee_vests,
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
            op = operations.Account_create_with_delegation(**op)
        else:
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
                    required_posting_auths=[]):
        """ Create a custom json operation
            :param str id: identifier for the custom json (max length 32 bytes)
            :param json json_data: the json data to put into the custom_json
                operation
            :param list required_auths: (optional) required auths
            :param list required_posting_auths: (optional) posting auths
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
        return self.finalizeOp(op, account, "posting")

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
             self_vote=False):
        """ Create a new post.
        If this post is intended as a reply/comment, `reply_identifier` needs
        to be set with the identifier of the parent post/comment (eg.
        `@author/permlink`).
        Optionally you can also set json_metadata, comment_options and upvote
        the newly created post as an author.
        Setting category, tags or community will override the values provided
        in json_metadata and/or comment_options where appropriate.
        Args:
        title (str): Title of the post
        body (str): Body of the post/comment
        author (str): Account are you posting from
        permlink (str): Manually set the permlink (defaults to None).
            If left empty, it will be derived from title automatically.
        reply_identifier (str): Identifier of the parent post/comment (only
            if this post is a reply/comment).
        json_metadata (str, dict): JSON meta object that can be attached to
            the post.
        comment_options (str, dict): JSON options object that can be
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
        community (str): (Optional) Name of the community we are posting
            into. This will also override the community specified in
            `json_metadata`.
        app (str): (Optional) Name of the app which are used for posting
            when not set, beem/<version> is used
        tags (str, list): (Optional) A list of tags (5 max) to go with the
            post. This will also override the tags specified in
            `json_metadata`. The first tag will be used as a 'category'. If
            provided as a string, it should be space separated.
        beneficiaries (list of dicts): (Optional) A list of beneficiaries
            for posting reward distribution. This argument overrides
            beneficiaries as specified in `comment_options`.
        For example, if we would like to split rewards between account1 and
        account2::
            beneficiaries = [
                {'account': 'account1', 'weight': 5000},
                {'account': 'account2', 'weight': 5000}
            ]
        self_vote (bool): (Optional) Upvote the post as author, right after
            posting.
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
            tags = list(set([_f for _f in (re.split("[\W_]", tags)) if _f]))

        category = None
        tags = tags or json_metadata.get('tags', [])
        if tags:
            if len(tags) > 5:
                raise ValueError('Can only specify up to 5 tags per post.')

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
                "author": author,
                "permlink": permlink,
                "title": title,
                "body": body,
                "json_metadata": json_metadata
            })
        ops = [post_op]

        # if comment_options are used, add a new op to the transaction
        if comment_options or beneficiaries:
            options = remove_from_dict(comment_options or {}, [
                'max_accepted_payout', 'percent_steem_dollars', 'allow_votes',
                'allow_curation_rewards', 'extensions'
            ], keep_keys=True)
            # override beneficiaries extension
            if beneficiaries:
                # validate schema
                # or just simply vo.Schema([{'account': str, 'weight': int}])

                for b in beneficiaries:
                    if 'account' not in b:
                        raise ValueError(
                            "beneficiaries need an account field!"
                        )
                    if 'weight' not in b:
                        b['weight'] = 10000
                    if len(b['account']) > 16:
                        raise ValueError(
                            "beneficiaries error, account name length >16!"
                        )
                    if b['weight'] < 1 or b['weight'] > 10000:
                        raise ValueError(
                            "beneficiaries error, 1<=weight<=10000!"
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
                    int(options.get("percent_steem_dollars", 10000)),
                    "allow_votes":
                    options.get("allow_votes", True),
                    "allow_curation_rewards":
                    options.get("allow_curation_rewards", True),
                    "extensions":
                    options.get("extensions", []),
                    "beneficiaries":
                    options.get("beneficiaries"),
                })
            ops.append(comment_op)

        if self_vote:
            vote_op = operations.Vote(
                **{
                    'voter': author,
                    'author': author,
                    'permlink': permlink,
                    'weight': 10000,
                })
            ops.append(vote_op)

        return self.finalizeOp(ops, account, "posting")

    def comment_options(self, options, identifier, account=None):
        """ Set the comment options
            :param str identifier: Post identifier
            :param dict options: The options to define.
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
        default_max_payout = "1000000.000 SBD"
        STEEMIT_100_PERCENT = 10000
        STEEMIT_1_PERCENT = (STEEMIT_100_PERCENT / 100)
        op = operations.Comment_options(
            **{
                "author":
                author,
                "permlink":
                permlink,
                "max_accepted_payout":
                options.get("max_accepted_payout", default_max_payout),
                "percent_steem_dollars":
                options.get("percent_steem_dollars", 100) * STEEMIT_1_PERCENT,
                "allow_votes":
                options.get("allow_votes", True),
                "allow_curation_rewards":
                options.get("allow_curation_rewards", True),
            })
        return self.finalizeOp(op, account, "posting")
