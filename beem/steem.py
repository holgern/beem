from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from builtins import object
import json
import logging

from datetime import datetime, timedelta
from beemapi.steemnoderpc import SteemNodeRPC
from beemapi.exceptions import NoAccessApi
from beembase.account import PrivateKey, PublicKey
from beembase import transactions, operations
from .asset import Asset
from .account import Account
from .amount import Amount
from .price import Price
from .witness import Witness
from .storage import configStorage as config
from .exceptions import (
    AccountExistsException,
)
from .wallet import Wallet
from .transactionbuilder import TransactionBuilder
from .utils import formatTime, resolve_authorperm

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
        :param bool offline: Boolean to prevent connecting to network (defaults
            to ``False``) *(optional)*
        :param str proposer: Propose a transaction using this proposer
            *(optional)*
        :param int proposal_expiration: Expiration time (in seconds) for the
            proposal *(optional)*
        :param int proposal_review: Review period (in seconds) for the proposal
            *(optional)*
        :param int expiration: Delay in seconds until transactions are supposed
            to expire *(optional)*
        :param str blocking: Wait for broadcasted transactions to be included
            in a block and return full transaction (can be "head" or
            "irrversible")
        :param bool bundle: Do not broadcast transactions right away, but allow
            to bundle operations *(optional)*

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
          ``active``, ``owner``, or ``memo`` keys for
          any account. This mode is only used for *foreign*
          signatures!

        If no node is provided, it will connect to the node of
        http://uptick.rocks. It is **highly** recommended that you
        pick your own node instead. Default settings can be changed with:

        .. code-block:: python

            uptick set node <host>

        where ``<host>`` starts with ``ws://`` or ``wss://``.

        The purpose of this class it to simplify interaction with
        Steem.

        The idea is to have a class that allows to do this:

        .. code-block:: python

            from beem import Steem
            steem = Steem()
            print(steem.info())

        All that is requires is for the user to have added a key with
        ``uptick``

        .. code-block:: bash

            uptick addkey

        and setting a default author:

        .. code-block:: bash

            uptick set default_account xeroc

        This class also deals with edits, votes and reading content.
    """

    def __init__(self,
                 node="",
                 rpcuser="",
                 rpcpassword="",
                 debug=False,
                 data_refresh_time_seconds=900,
                 **kwargs):

        # More specific set of APIs to register to
        if "apis" not in kwargs:
            kwargs["apis"] = [
                "database",
                "network_broadcast",
                "market_history",
                "follow",
                "account_by_key",
                # "tag",
                # "raw_block"
            ]

        self.rpc = None
        self.debug = debug

        self.offline = bool(kwargs.get("offline", False))
        self.nobroadcast = bool(kwargs.get("nobroadcast", False))
        self.unsigned = bool(kwargs.get("unsigned", False))
        self.expiration = int(kwargs.get("expiration", 30))
        self.bundle = bool(kwargs.get("bundle", False))
        self.blocking = kwargs.get("blocking", False)

        # Store config for access through other Classes
        self.config = config

        if not self.offline:
            self.connect(node=node,
                         rpcuser=rpcuser,
                         rpcpassword=rpcpassword,
                         **kwargs)

        # Try Optional APIs
        self.register_apis()

        self.wallet = Wallet(self.rpc, **kwargs)

        self.data = {'last_refresh': None, 'dynamic_global_properties': None, 'feed_history': None,
                     'current_median_history_price': None, 'next_scheduled_hardfork': None,
                     'hardfork_version': None, 'network': None, 'chain_properties': None,
                     'config': None, 'reward_fund': None}
        self.data_refresh_time_seconds = data_refresh_time_seconds
        # self.refresh_data()

        # txbuffers/propbuffer are initialized and cleared
        self.clear()

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

    def register_apis(self, apis=["network_broadcast", "account_by_key", "follow", "market_history"]):

        # Try Optional APIs
        try:
            self.rpc.register_apis(apis)
        except NoAccessApi as e:
            log.info(str(e))

    def refresh_data(self, force_refresh=False):
        if self.offline:
            return
        if self.data['last_refresh'] is not None and not force_refresh:
            if (datetime.now() - self.data['last_refresh']).total_seconds() < self.data_refresh_time_seconds:
                return
        self.data['last_refresh'] = datetime.now()
        self.data["dynamic_global_properties"] = self.get_dynamic_global_properties(False)
        self.data['feed_history'] = self.get_feed_history(False)
        self.data['current_median_history_price'] = self.get_current_median_history_price(False)
        self.data['next_scheduled_hardfork'] = self.get_next_scheduled_hardfork(False)
        self.data['hardfork_version'] = self.get_hardfork_version(False)
        self.data['network'] = self.get_network(False)
        self.data['chain_properties'] = self.get_chain_properties(False)
        self.data['config'] = self.get_config(False)
        self.data['reward_fund'] = {"post": self.get_reward_fund("post", False)}

    def get_dynamic_global_properties(self, use_stored_data=True):
        """ This call returns the *dynamic global properties*
        """
        if use_stored_data:
            self.refresh_data()
            return self.data['dynamic_global_properties']
        else:
            return self.rpc.get_dynamic_global_properties()

    def get_feed_history(self, use_stored_data=True):
        """ Returns the feed_history
        """
        if use_stored_data:
            self.refresh_data()
            return self.data['feed_history']
        else:
            return self.rpc.get_feed_history()

    def get_reward_fund(self, fund_name="post", use_stored_data=True):
        """ Get details for a reward fund.
        """
        if use_stored_data:
            self.refresh_data()
            return self.data['reward_fund'][fund_name]
        else:
            return self.rpc.get_reward_fund(fund_name)

    def get_current_median_history_price(self, use_stored_data=True):
        """ Returns the current median price
        """
        if use_stored_data:
            self.refresh_data()
            return self.data['current_median_history_price']
        else:
            return self.rpc.get_current_median_history_price()

    def get_next_scheduled_hardfork(self, use_stored_data=True):
        """ Returns Hardfork and live_time of the hardfork
        """
        if use_stored_data:
            self.refresh_data()
            return self.data['next_scheduled_hardfork']
        else:
            return self.rpc.get_next_scheduled_hardfork()

    def get_hardfork_version(self, use_stored_data=True):
        """ Current Hardfork Version as String
        """
        if use_stored_data:
            self.refresh_data()
            return self.data['hardfork_version']
        else:
            return self.rpc.get_hardfork_version()

    def get_network(self, use_stored_data=True):
        """ Identify the network

            :returns: Network parameters
            :rtype: dict
        """
        if use_stored_data:
            self.refresh_data()
            return self.data['network']
        else:
            return self.rpc.get_network()

    def get_median_price(self):
        median_price = self.get_current_median_history_price()
        a = (
            Amount(median_price['base']) /
            Amount(median_price['quote'])
        )
        return a.as_base("SBD")

    def get_payout_from_rshares(self, rshares):
        reward_fund = self.get_reward_fund()
        reward_balance = Amount(reward_fund["reward_balance"]).amount
        recent_claims = float(reward_fund["recent_claims"])

        fund_per_share = reward_balance / (recent_claims)
        SBD_price = (self.get_median_price() * Amount("1 STEEM")).amount
        payout = float(rshares) * fund_per_share * SBD_price
        return payout

    def get_steem_per_mvest(self, time_stamp=None):

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
            Amount(global_properties['total_vesting_fund_steem']).amount /
            (Amount(global_properties['total_vesting_shares']).amount / 1e6)
        )

    def vests_to_sp(self, vests, timestamp=None):
        if isinstance(vests, Amount):
            vests = vests.amount
        return vests / 1e6 * self.get_steem_per_mvest(timestamp)

    def sp_to_vests(self, sp, timestamp=None):
        return sp * 1e6 / self.get_steem_per_mvest(timestamp)

    def sp_to_sbd(self, sp, voting_power=10000, vote_pct=10000):
        reward_fund = self.get_reward_fund()
        reward_balance = Amount(reward_fund["reward_balance"]).amount
        recent_claims = float(reward_fund["recent_claims"])
        reward_share = reward_balance / recent_claims

        resulting_vote = ((voting_power * (vote_pct) / 10000) + 49) / 50
        vesting_shares = int(self.sp_to_vests(sp))
        SBD_price = (self.get_median_price() * Amount("1 STEEM")).amount
        VoteValue = (vesting_shares * resulting_vote * 100) * reward_share * SBD_price
        return VoteValue

    def sp_to_rshares(self, sp, voting_power=10000, vote_pct=10000):
        """ Obtain the r-shares
            :param number sp: Steem Power
            :param int voting_power: voting power (100% = 10000)
            :param int vote_pct: voting participation (100% = 10000)
        """
        # calculate our account voting shares (from vests), mine is 6.08b
        vesting_shares = int(self.sp_to_vests(sp) * 1e6)

        # get props
        global_properties = self.get_dynamic_global_properties()
        vote_power_reserve_rate = global_properties['vote_power_reserve_rate']

        # determine voting power used
        used_power = int((voting_power * vote_pct) / 10000)
        max_vote_denom = vote_power_reserve_rate * (5 * 60 * 60 * 24) / (60 * 60 * 24)
        used_power = int((used_power + max_vote_denom - 1) / max_vote_denom)
        # calculate vote rshares
        rshares = ((vesting_shares * used_power) / 10000)

        return rshares

    def get_chain_properties(self, use_stored_data=True):
        """ Return witness elected chain properties

            ::
                {'account_creation_fee': '30.000 STEEM',
                 'maximum_block_size': 65536,
                 'sbd_interest_rate': 250}

        """
        if use_stored_data:
            self.refresh_data()
            return self.data['chain_properties']
        else:
            return self.rpc.get_chain_properties()

    def get_state(self, path="value"):
        """ get_state
        """
        return self.rpc.get_state(path)

    def get_config(self, use_stored_data=True):
        """ Returns internal chain configuration.
        """
        if use_stored_data:
            self.refresh_data()
            return self.data['config']
        else:
            return self.rpc.get_config()

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
        Account(account)
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
            assert isinstance(append_to, (TransactionBuilder))
            append_to.appendOps(ops)
            # Add the signer to the buffer so we sign the tx properly
            parent.appendSigner(account, permission)
            # This returns as we used append_to, it does NOT broadcast, or sign
            return append_to.get_parent()
            # Go forward to see what the other options do ...
        else:
            # Append tot he default buffer
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
        return self.rpc.get_dynamic_global_properties()

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
        **kwargs
    ):
        """ Create new account on Steem

            The brainkey/password can be used to recover all generated keys
            (see `beembase.account` for more details.

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

            :param str account_name: (**required**) new account name
            :param str registrar: which account should pay the registration fee
                                (defaults to ``default_account``)
            :param str owner_key: Main owner key
            :param str active_key: Main active key
            :param str memo_key: Main memo_key
            :param str password: Alternatively to providing keys, one
                                 can provide a password from which the
                                 keys will be derived
            :param array additional_owner_keys:  Additional owner public keys
            :param array additional_active_keys: Additional active public keys
            :param array additional_owner_accounts: Additional owner account
                names
            :param array additional_active_accounts: Additional acctive account
                names
            :param bool storekeys: Store new keys in the wallet (default:
                ``True``)
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
        except:
            pass

        # creator = Account(creator, steem_instance=self)

        " Generate new keys from password"
        from beembase.account import PasswordKey, PublicKey
        if password:
            active_key = PasswordKey(account_name, password, role="active")
            owner_key = PasswordKey(account_name, password, role="owner")
            posting_key = PasswordKey(account_name, password, role="posting")
            memo_key = PasswordKey(account_name, password, role="memo")
            active_pubkey = active_key.get_public_key()
            owner_pubkey = owner_key.get_public_key()
            posting_pubkey = posting_key.get_public_key()
            memo_pubkey = memo_key.get_public_key()
            active_privkey = active_key.get_private_key()
            posting_privkey = posting_key.get_private_key()
            owner_privkey = owner_key.get_private_key()
            memo_privkey = memo_key.get_private_key()
            # store private keys
            if storekeys:
                if store_owner_key:
                    self.wallet.addPrivateKey(owner_privkey)
                self.wallet.addPrivateKey(active_privkey)
                self.wallet.addPrivateKey(memo_privkey)
                self.wallet.addPrivateKey(posting_privkey)
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

        op = {
            "fee": Amount(0, "STEEM"),
            "creator": creator,
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
            "json_metadata": {},
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
                modify (defaults to ``active``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
            :param int threshold: The threshold that needs to be reached
                by signatures to be able to interact
        """
        from copy import deepcopy
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        if permission not in ["owner", "posting", "active"]:
            raise ValueError(
                "Permission needs to be either 'owner', 'posting', or 'active"
            )
        account = Account(account, steem_instance=self)

        if permission not in account:
            account = Account(account, steem_instance=self, lazy=False, full=True)
            account.clear_cache()
            account.refresh()
        if permission not in account:
            account = Account(account, steem_instance=self.steem)
        assert permission in account, "Could not access permission"

        if not weight:
            weight = account[permission]["weight_threshold"]

        authority = deepcopy(account[permission])
        try:
            pubkey = PublicKey(foreign, prefix=self.prefix)
            authority["key_auths"].append([
                str(pubkey),
                weight
            ])
        except:
            try:
                foreign_account = Account(foreign, steem_instance=self)
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
            self._test_weights_treshold(authority)

        op = operations.Account_update(**{
            "account": account["name"],
            permission: authority,
            "memo_key": account["memo_key"],
            "json_metadata": account["json_metadata"],
        })
        if permission == "owner":
            return self.finalizeOp(op, account, "owner", **kwargs)
        else:
            return self.finalizeOp(op, account, "active", **kwargs)

    def disallow(
        self, foreign, permission="posting",
        account=None, threshold=None, **kwargs
    ):
        """ Remove additional access to an account by some other public
            key or account.

            :param str foreign: The foreign account that will obtain access
            :param str permission: (optional) The actual permission to
                modify (defaults to ``active``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
            :param int threshold: The threshold that needs to be reached
                by signatures to be able to interact
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        if permission not in ["owner", "active", "posting"]:
            raise ValueError(
                "Permission needs to be either 'owner', 'posting', or 'active"
            )
        account = Account(account, steem_instance=self)
        authority = account[permission]

        try:
            pubkey = PublicKey(foreign, prefix=self.prefix)
            affected_items = list(
                [x for x in authority["key_auths"] if x[0] == str(pubkey)])
            authority["key_auths"] = list([x for x in authority["key_auths"] if x[0] != str(pubkey)])
        except:
            try:
                foreign_account = Account(foreign, steem_instance=self)
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
            self.self.cm(authority)
        except:
            log.critical(
                "The account's threshold will be reduced by %d"
                % (removed_weight)
            )
            authority["weight_threshold"] -= removed_weight
            self.self.cm(authority)

        op = operations.Account_update(**{
            "account": account["name"],
            permission: authority,
            "memo_key": account["memo_key"],
            "json_metadata": account["json_metadata"]
        })
        if permission == "owner":
            return self.finalizeOp(op, account, "owner", **kwargs)
        else:
            return self.finalizeOp(op, account, "active", **kwargs)

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
                "id": id
            })
        return self.finalizeOp(op, account, "posting")
