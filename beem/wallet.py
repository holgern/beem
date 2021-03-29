# -*- coding: utf-8 -*-
import logging
import os
from beemgraphenebase.account import PrivateKey
from beem.instance import shared_blockchain_instance
from .account import Account
from .exceptions import (
    MissingKeyError,
    InvalidWifError,
    WalletExists,
    OfflineHasNoRPCException,
    AccountDoesNotExistsException
)
from beemstorage.exceptions import KeyAlreadyInStoreException, WalletLocked


log = logging.getLogger(__name__)


class Wallet(object):
    """ The wallet is meant to maintain access to private keys for
        your accounts. It either uses manually provided private keys
        or uses a SQLite database managed by storage.py.

        :param SteemNodeRPC rpc: RPC connection to a Steem node
        :param keys: Predefine the wif keys to shortcut the
               wallet database
        :type keys: array, dict, str

        Three wallet operation modes are possible:

        * **Wallet Database**: Here, beem loads the keys from the
          locally stored wallet SQLite database (see ``storage.py``).
          To use this mode, simply call :class:`beem.steem.Steem` without the
          ``keys`` parameter
        * **Providing Keys**: Here, you can provide the keys for
          your accounts manually. All you need to do is add the wif
          keys for the accounts you want to use as a simple array
          using the ``keys`` parameter to :class:`beem.steem.Steem`.
        * **Force keys**: This more is for advanced users and
          requires that you know what you are doing. Here, the
          ``keys`` parameter is a dictionary that overwrite the
          ``active``, ``owner``, ``posting`` or ``memo`` keys for
          any account. This mode is only used for *foreign*
          signatures!

        A new wallet can be created by using:

        .. code-block:: python

           from beem import Steem
           steem = Steem()
           steem.wallet.wipe(True)
           steem.wallet.create("supersecret-passphrase")

        This will raise :class:`beem.exceptions.WalletExists` if you already have a wallet installed.


        The wallet can be unlocked for signing using

        .. code-block:: python

           from beem import Steem
           steem = Steem()
           steem.wallet.unlock("supersecret-passphrase")

        A private key can be added by using the
        :func:`addPrivateKey` method that is available
        **after** unlocking the wallet with the correct passphrase:

        .. code-block:: python

           from beem import Steem
           steem = Steem()
           steem.wallet.unlock("supersecret-passphrase")
           steem.wallet.addPrivateKey("5xxxxxxxxxxxxxxxxxxxx")

        .. note:: The private key has to be either in hexadecimal or in wallet
                  import format (wif) (starting with a ``5``).

    """


    def __init__(self, blockchain_instance=None, *args, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()

        # Compatibility after name change from wif->keys
        if "wif" in kwargs and "keys" not in kwargs:
            kwargs["keys"] = kwargs["wif"]

        if "keys" in kwargs and len(kwargs["keys"]) > 0:
            from beemstorage import InRamPlainKeyStore
            self.store = InRamPlainKeyStore()
            self.setKeys(kwargs["keys"])
        else:
            """ If no keys are provided manually we load the SQLite
                keyStorage
            """
            from beemstorage import SqliteEncryptedKeyStore
            self.store = kwargs.get(
                "key_store",
                SqliteEncryptedKeyStore(config=self.blockchain.config, **kwargs),
            )

    @property
    def prefix(self):
        if self.blockchain.is_connected():
            prefix = self.blockchain.prefix
        else:
            # If not connected, load prefix from config
            prefix = self.blockchain.config["prefix"]
        return prefix or "STM"   # default prefix is STM

    @property
    def rpc(self):
        if not self.blockchain.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        return self.blockchain.rpc

    def setKeys(self, loadkeys):
        """ This method is strictly only for in memory keys that are
            passed to Wallet with the ``keys`` argument
        """
        log.debug("Force setting of private keys. Not using the wallet database!")
        if isinstance(loadkeys, dict):
            loadkeys = list(loadkeys.values())
        elif not isinstance(loadkeys, (list, set)):
            loadkeys = [loadkeys]
        for wif in loadkeys:
            pub = self.publickey_from_wif(wif)
            self.store.add(str(wif), pub)

    def is_encrypted(self):
        """ Is the key store encrypted?
        """
        return self.store.is_encrypted()

    def unlock(self, pwd):
        """ Unlock the wallet database
        """
        unlock_ok = None
        if self.store.is_encrypted():
            unlock_ok = self.store.unlock(pwd)
        return unlock_ok

    def lock(self):
        """ Lock the wallet database
        """
        lock_ok = False
        if self.store.is_encrypted():
            lock_ok =  self.store.lock()       
        return lock_ok

    def unlocked(self):
        """ Is the wallet database unlocked?
        """
        unlocked = True
        if self.store.is_encrypted():
            unlocked = not self.store.locked()   
        return unlocked

    def locked(self):
        """ Is the wallet database locked?
        """
        if self.store.is_encrypted():
            return self.store.locked()
        else:
            return False

    def changePassphrase(self, new_pwd):
        """ Change the passphrase for the wallet database
        """
        self.store.change_password(new_pwd)

    def created(self):
        """ Do we have a wallet database already?
        """
        if len(self.store.getPublicKeys()):
            # Already keys installed
            return True
        else:
            return False

    def create(self, pwd):
        """ Alias for :func:`newWallet`

            :param str pwd: Passphrase for the created wallet
        """
        self.newWallet(pwd)

    def newWallet(self, pwd):
        """ Create a new wallet database

            :param str pwd: Passphrase for the created wallet
        """
        if self.created():
            raise WalletExists("You already have created a wallet!")
        self.store.unlock(pwd)

    def privatekey(self, key):
        return PrivateKey(key, prefix=self.prefix)

    def publickey_from_wif(self, wif):
        return str(self.privatekey(str(wif)).pubkey)

    def addPrivateKey(self, wif):
        """Add a private key to the wallet database

            :param str wif: Private key
        """
        try:
            pub = self.publickey_from_wif(wif)
        except Exception:
            raise InvalidWifError("Invalid Key format!")
        if str(pub) in self.store:
            raise KeyAlreadyInStoreException("Key already in the store")
        self.store.add(str(wif), str(pub))

    def getPrivateKeyForPublicKey(self, pub):
        """ Obtain the private key for a given public key

            :param str pub: Public Key
        """
        if str(pub) not in self.store:
            raise MissingKeyError
        return self.store.getPrivateKeyForPublicKey(str(pub))

    def removePrivateKeyFromPublicKey(self, pub):
        """ Remove a key from the wallet database

            :param str pub: Public key
        """
        self.store.delete(str(pub))

    def removeAccount(self, account):
        """ Remove all keys associated with a given account

            :param str account: name of account to be removed
        """
        accounts = self.getAccounts()
        for a in accounts:
            if a["name"] == account:
                self.store.delete(a["pubkey"])

    def getKeyForAccount(self, name, key_type):
        """ Obtain `key_type` Private Key for an account from the wallet database

            :param str name: Account name
            :param str key_type: key type, has to be one of "owner", "active",
                "posting" or "memo"
        """
        if key_type not in ["owner", "active", "posting", "memo"]:
            raise AssertionError("Wrong key type")

        if self.rpc.get_use_appbase():
            account = self.rpc.find_accounts({'accounts': [name]}, api="database")['accounts']
        else:
            account = self.rpc.get_account(name)
        if not account:
            return
        if len(account) == 0:
            return
        if key_type == "memo":
            key = self.getPrivateKeyForPublicKey(
                account[0]["memo_key"])
            if key:
                return key
        else:
            key = None
            for authority in account[0][key_type]["key_auths"]:
                try:
                    key = self.getPrivateKeyForPublicKey(authority[0])
                    if key:
                        return key
                except MissingKeyError:
                    key = None
            if key is None:
                raise MissingKeyError("No private key for {} found".format(name))
        return

    def getKeysForAccount(self, name, key_type):
        """ Obtain a List of `key_type` Private Keys for an account from the wallet database

            :param str name: Account name
            :param str key_type: key type, has to be one of "owner", "active",
                "posting" or "memo"
        """
        if key_type not in ["owner", "active", "posting", "memo"]:
            raise AssertionError("Wrong key type")

        if self.rpc.get_use_appbase():
            account = self.rpc.find_accounts({'accounts': [name]}, api="database")['accounts']
        else:
            account = self.rpc.get_account(name)
        if not account:
            return
        if len(account) == 0:
            return
        if key_type == "memo":
            key = self.getPrivateKeyForPublicKey(
                account[0]["memo_key"])
            if key:
                return [key]
        else:
            keys = []
            key = None
            for authority in account[0][key_type]["key_auths"]:
                try:
                    key = self.getPrivateKeyForPublicKey(authority[0])
                    if key:
                        keys.append(key)
                except MissingKeyError:
                    key = None
            if key is None:
                raise MissingKeyError("No private key for {} found".format(name))
            return keys
        return

    def getOwnerKeyForAccount(self, name):
        """ Obtain owner Private Key for an account from the wallet database
        """
        return self.getKeyForAccount(name, "owner")

    def getMemoKeyForAccount(self, name):
        """ Obtain owner Memo Key for an account from the wallet database
        """
        return self.getKeyForAccount(name, "memo")

    def getActiveKeyForAccount(self, name):
        """ Obtain owner Active Key for an account from the wallet database
        """
        return self.getKeyForAccount(name, "active")

    def getPostingKeyForAccount(self, name):
        """ Obtain owner Posting Key for an account from the wallet database
        """
        return self.getKeyForAccount(name, "posting")

    def getOwnerKeysForAccount(self, name):
        """ Obtain list of all owner Private Keys for an account from the wallet database
        """
        return self.getKeysForAccount(name, "owner")

    def getActiveKeysForAccount(self, name):
        """ Obtain list of all owner Active Keys for an account from the wallet database
        """
        return self.getKeysForAccount(name, "active")

    def getPostingKeysForAccount(self, name):
        """ Obtain list of all owner Posting Keys for an account from the wallet database
        """
        return self.getKeysForAccount(name, "posting")

    def getAccountFromPrivateKey(self, wif):
        """ Obtain account name from private key
        """
        pub = self.publickey_from_wif(wif)
        return self.getAccountFromPublicKey(pub)

    def getAccountsFromPublicKey(self, pub):
        """ Obtain all account names associated with a public key

            :param str pub: Public key
        """
        if not self.blockchain.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.blockchain.rpc.set_next_node_on_empty_reply(False)
        if self.blockchain.rpc.get_use_appbase():
            names = self.blockchain.rpc.get_key_references({'keys': [pub]}, api="account_by_key")["accounts"]
        else:
            names = self.blockchain.rpc.get_key_references([pub], api="account_by_key")
        for name in names:
            for i in name:
                yield i

    def getAccountFromPublicKey(self, pub):
        """ Obtain the first account name from public key

            :param str pub: Public key

            Note: this returns only the first account with the given key. To
            get all accounts associated with a given public key, use
            :func:`getAccountsFromPublicKey`.
        """
        names = list(self.getAccountsFromPublicKey(pub))
        if not names:
            return None
        else:
            return names[0]

    def getAllAccounts(self, pub):
        """ Get the account data for a public key (all accounts found for this
            public key)

            :param str pub: Public key
        """
        for name in self.getAccountsFromPublicKey(pub):
            try:
                account = Account(name, blockchain_instance=self.blockchain)
            except AccountDoesNotExistsException:
                continue
            yield {"name": account["name"],
                   "account": account,
                   "type": self.getKeyType(account, pub),
                   "pubkey": pub}

    def getAccount(self, pub):
        """ Get the account data for a public key (first account found for this
            public key)

            :param str pub: Public key
        """
        name = self.getAccountFromPublicKey(pub)
        if not name:
            return {"name": None, "type": None, "pubkey": pub}
        else:
            try:
                account = Account(name, blockchain_instance=self.blockchain)
            except:
                return
            return {"name": account["name"],
                    "account": account,
                    "type": self.getKeyType(account, pub),
                    "pubkey": pub}

    def getKeyType(self, account, pub):
        """ Get key type

            :param beem.account.Account/dict account: Account data
            :type account: Account, dict
            :param str pub: Public key

        """
        for authority in ["owner", "active", "posting"]:
            for key in account[authority]["key_auths"]:
                if str(pub) == key[0]:
                    return authority
        if str(pub) == account["memo_key"]:
            return "memo"
        return None

    def getAccounts(self):
        """ Return all accounts installed in the wallet database
        """
        pubkeys = self.getPublicKeys()
        accounts = []
        for pubkey in pubkeys:
            # Filter those keys not for our network
            if pubkey[:len(self.prefix)] == self.prefix:
                accounts.extend(self.getAllAccounts(pubkey))
        return accounts

    def getPublicKeys(self, current=False):
        """ Return all installed public keys
            :param bool current: If true, returns only keys for currently
                connected blockchain
        """
        pubkeys = self.store.getPublicKeys()
        if not current:
            return pubkeys
        pubs = []
        for pubkey in pubkeys:
            # Filter those keys not for our network
            if pubkey[: len(self.prefix)] == self.prefix:
                pubs.append(pubkey)
        return pubs

    def wipe(self, sure=False):
        if not sure:
            log.error(
                "You need to confirm that you are sure "
                "and understand the implications of "
                "wiping your wallet!"
            )
            return
        else:
            self.store.wipe()
            self.store.wipe_masterpassword()
