from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str, bytes
from builtins import object
import logging
import os
import hashlib
from beemgraphenebase import bip38
from beemgraphenebase.account import PrivateKey
from beem.instance import shared_steem_instance
from .account import Account
from .aes import AESCipher
from .exceptions import (
    MissingKeyError,
    InvalidWifError,
    WalletExists,
    WalletLocked,
    WrongMasterPasswordException,
    NoWalletException,
    OfflineHasNoRPCException,
    AccountDoesNotExistsException,
)
from beemapi.exceptions import NoAccessApi
from beemgraphenebase.py23 import py23_bytes
from .storage import configStorage as config
try:
    import keyring
    if not isinstance(keyring.get_keyring(), keyring.backends.fail.Keyring):
        KEYRING_AVAILABLE = True
    else:
        KEYRING_AVAILABLE = False
except ImportError:
    KEYRING_AVAILABLE = False

log = logging.getLogger(__name__)


class Wallet(object):
    """ The wallet is meant to maintain access to private keys for
        your accounts. It either uses manually provided private keys
        or uses a SQLite database managed by storage.py.

        :param SteemNodeRPC rpc: RPC connection to a Steem node
        :param array,dict,string keys: Predefine the wif keys to shortcut the
               wallet database

        Three wallet operation modes are possible:

        * **Wallet Database**: Here, beem loads the keys from the
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

        A new wallet can be created by using:

        .. code-block:: python

           from beem import Steem
           steem = Steem()
           steem.wallet.wipe(True)
           steem.wallet.create("supersecret-passphrase")

        This will raise an exception if you already have a wallet installed.


        The wallet can be unlocked for signing using

        .. code-block:: python

           from beem import Steem
           steem = Steem()
           steem.wallet.unlock("supersecret-passphrase")

        A private key can be added by using the
        :func:`steem.wallet.Wallet.addPrivateKey` method that is available
        **after** unlocking the wallet with the correct passphrase:

        .. code-block:: python

           from beem import Steem
           steem = Steem()
           steem.wallet.unlock("supersecret-passphrase")
           steem.wallet.addPrivateKey("5xxxxxxxxxxxxxxxxxxxx")

        .. note:: The private key has to be either in hexadecimal or in wallet
                  import format (wif) (starting with a ``5``).

    """
    masterpassword = None

    # Keys from database
    configStorage = None
    MasterPassword = None
    keyStorage = None
    tokenStorage = None

    # Manually provided keys
    keys = {}  # struct with pubkey as key and wif as value
    token = {}
    keyMap = {}  # type:wif pairs to force certain keys

    def __init__(self, steem_instance=None, *args, **kwargs):
        self.steem = steem_instance or shared_steem_instance()

        # Compatibility after name change from wif->keys
        if "wif" in kwargs and "keys" not in kwargs:
            kwargs["keys"] = kwargs["wif"]
        master_password_set = False
        if "keys" in kwargs:
            self.setKeys(kwargs["keys"])
        else:
            """ If no keys are provided manually we load the SQLite
                keyStorage
            """
            from .storage import (keyStorage,
                                  MasterPassword)
            self.MasterPassword = MasterPassword
            master_password_set = True
            self.keyStorage = keyStorage

        if "token" in kwargs:
            self.setToken(kwargs["token"])
        else:
            """ If no keys are provided manually we load the SQLite
                keyStorage
            """
            from .storage import tokenStorage
            if not master_password_set:
                from .storage import MasterPassword
                self.MasterPassword = MasterPassword
            self.tokenStorage = tokenStorage

    @property
    def prefix(self):
        if self.steem.is_connected():
            prefix = self.steem.prefix
        else:
            # If not connected, load prefix from config
            prefix = config["prefix"]
        return prefix or "STM"   # default prefix is STM

    @property
    def rpc(self):
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        return self.steem.rpc

    def setKeys(self, loadkeys):
        """ This method is strictly only for in memory keys that are
            passed to Wallet/Steem with the ``keys`` argument
        """
        log.debug(
            "Force setting of private keys. Not using the wallet database!")
        self.clear_local_keys()
        if isinstance(loadkeys, dict):
            Wallet.keyMap = loadkeys
            loadkeys = list(loadkeys.values())
        elif not isinstance(loadkeys, list):
            loadkeys = [loadkeys]

        for wif in loadkeys:
            pub = self._get_pub_from_wif(wif)
            Wallet.keys[pub] = str(wif)

    def setToken(self, loadtoken):
        """ This method is strictly only for in memory token that are
            passed to Wallet/Steem with the ``token`` argument
        """
        log.debug(
            "Force setting of private token. Not using the wallet database!")
        self.clear_local_token()
        if isinstance(loadtoken, dict):
            Wallet.token = loadtoken
        else:
            raise ValueError("token must be a dict variable!")

    def unlock(self, pwd=None):
        """ Unlock the wallet database
        """
        if not self.created():
            raise NoWalletException

        if not pwd:
            self.tryUnlockFromEnv()
        else:
            if (self.masterpassword is None and
                    config[self.MasterPassword.config_key]):
                self.masterpwd = self.MasterPassword(pwd)
                self.masterpassword = self.masterpwd.decrypted_master

    def tryUnlockFromEnv(self):
        """ Try to fetch the unlock password from UNLOCK environment variable and keyring when no password is given.
        """
        password_storage = self.steem.config["password_storage"]
        if password_storage == "environment" and "UNLOCK" in os.environ:
            log.debug("Trying to use environmental variable to unlock wallet")
            pwd = os.environ.get("UNLOCK")
            self.unlock(pwd)
        elif password_storage == "keyring" and KEYRING_AVAILABLE:
            log.debug("Trying to use keyring to unlock wallet")
            pwd = keyring.get_password("beem", "wallet")
            self.unlock(pwd)
        else:
            raise WrongMasterPasswordException

    def lock(self):
        """ Lock the wallet database
        """
        self.masterpassword = None

    def unlocked(self):
        """ Is the wallet database unlocked?
        """
        return not self.locked()

    def locked(self):
        """ Is the wallet database locked?
        """
        if Wallet.keys:  # Keys have been manually provided!
            return False
        try:
            self.tryUnlockFromEnv()
        except WrongMasterPasswordException:
            pass
        return not bool(self.masterpassword)

    def changePassphrase(self, new_pwd):
        """ Change the passphrase for the wallet database
        """
        if self.locked():
            raise AssertionError()
        self.masterpwd.changePassword(new_pwd)

    def created(self):
        """ Do we have a wallet database already?
        """
        if len(self.getPublicKeys()):
            # Already keys installed
            return True
        elif self.MasterPassword.config_key in config:
            # no keys but a master password
            return True
        else:
            return False

    def create(self, pwd):
        """ Alias for newWallet()
        """
        self.newWallet(pwd)

    def newWallet(self, pwd):
        """ Create a new wallet database
        """
        if self.created():
            raise WalletExists("You already have created a wallet!")
        self.masterpwd = self.MasterPassword(pwd)
        self.masterpassword = self.masterpwd.decrypted_master
        self.masterpwd.saveEncrytpedMaster()

    def wipe(self, sure=False):
        """ Purge all data in wallet database
        """
        if not sure:
            log.error(
                "You need to confirm that you are sure "
                "and understand the implications of "
                "wiping your wallet!"
            )
            return
        else:
            from .storage import (
                keyStorage,
                tokenStorage,
                MasterPassword
            )
            MasterPassword.wipe(sure)
            keyStorage.wipe(sure)
            tokenStorage.wipe(sure)
            self.clear_local_keys()

    def clear_local_keys(self):
        """Clear all manually provided keys"""
        Wallet.keys = {}
        Wallet.keyMap = {}

    def clear_local_token(self):
        """Clear all manually provided token"""
        Wallet.token = {}

    def encrypt_wif(self, wif):
        """ Encrypt a wif key
        """
        if self.locked():
            raise AssertionError()
        return format(
            bip38.encrypt(PrivateKey(wif, prefix=self.prefix), self.masterpassword), "encwif")

    def decrypt_wif(self, encwif):
        """ decrypt a wif key
        """
        try:
            # Try to decode as wif
            PrivateKey(encwif, prefix=self.prefix)
            return encwif
        except (ValueError, AssertionError):
            pass
        if self.locked():
            raise AssertionError()
        return format(bip38.decrypt(encwif, self.masterpassword), "wif")

    def deriveChecksum(self, s):
        """ Derive the checksum
        """
        checksum = hashlib.sha256(py23_bytes(s, "ascii")).hexdigest()
        return checksum[:4]

    def encrypt_token(self, token):
        """ Encrypt a token key
        """
        if self.locked():
            raise AssertionError()
        aes = AESCipher(self.masterpassword)
        return "{}${}".format(self.deriveChecksum(token), aes.encrypt(token))

    def decrypt_token(self, enctoken):
        """ decrypt a wif key
        """
        if self.locked():
            raise AssertionError()
        aes = AESCipher(self.masterpassword)
        checksum, encrypted_token = enctoken.split("$")
        try:
            decrypted_token = aes.decrypt(encrypted_token)
        except:
            raise WrongMasterPasswordException
        if checksum != self.deriveChecksum(decrypted_token):
            raise WrongMasterPasswordException
        return decrypted_token

    def _get_pub_from_wif(self, wif):
        """ Get the pubkey as string, from the wif key as string
        """
        # it could be either graphenebase or steem so we can't check
        # the type directly
        if isinstance(wif, PrivateKey):
            wif = str(wif)
        try:
            return format(PrivateKey(wif).pubkey, self.prefix)
        except:
            raise InvalidWifError(
                "Invalid Private Key Format. Please use WIF!")

    def addToken(self, name, token):
        if self.tokenStorage:
            if not self.created():
                raise NoWalletException
            self.tokenStorage.add(name, self.encrypt_token(token))

    def getTokenForAccountName(self, name):
        """ Obtain the private token for a given public name

            :param str name: Public name
        """
        if(Wallet.token):
            if name in Wallet.token:
                return Wallet.token[name]
            else:
                raise MissingKeyError("No private token for {} found".format(name))
        else:
            # Test if wallet exists
            if not self.created():
                raise NoWalletException

            if not self.unlocked():
                raise WalletLocked

            enctoken = self.tokenStorage.getTokenForPublicName(name)
            if not enctoken:
                raise MissingKeyError("No private token for {} found".format(name))
            return self.decrypt_token(enctoken)

    def removeTokenFromPublicName(self, name):
        """ Remove a token from the wallet database
        """
        if self.tokenStorage:
            # Test if wallet exists
            if not self.created():
                raise NoWalletException
            self.tokenStorage.delete(name)

    def addPrivateKey(self, wif):
        """Add a private key to the wallet database"""
        pub = self._get_pub_from_wif(wif)
        if isinstance(wif, PrivateKey):
            wif = str(wif)
        if self.keyStorage:
            # Test if wallet exists
            if not self.created():
                raise NoWalletException
            self.keyStorage.add(self.encrypt_wif(wif), pub)

    def getPrivateKeyForPublicKey(self, pub):
        """ Obtain the private key for a given public key

            :param str pub: Public Key
        """
        if(Wallet.keys):
            if pub in Wallet.keys:
                return Wallet.keys[pub]
            else:
                raise MissingKeyError("No private key for {} found".format(pub))
        else:
            # Test if wallet exists
            if not self.created():
                raise NoWalletException

            if not self.unlocked():
                raise WalletLocked

            encwif = self.keyStorage.getPrivateKeyForPublicKey(pub)
            if not encwif:
                raise MissingKeyError("No private key for {} found".format(pub))
            return self.decrypt_wif(encwif)

    def removePrivateKeyFromPublicKey(self, pub):
        """ Remove a key from the wallet database
        """
        if self.keyStorage:
            # Test if wallet exists
            if not self.created():
                raise NoWalletException
            self.keyStorage.delete(pub)

    def removeAccount(self, account):
        """ Remove all keys associated with a given account
        """
        accounts = self.getAccounts()
        for a in accounts:
            if a["name"] == account:
                self.removePrivateKeyFromPublicKey(a["pubkey"])

    def getKeyForAccount(self, name, key_type):
        """ Obtain `key_type` Private Key for an account from the wallet database
        """
        if key_type not in ["owner", "active", "posting", "memo"]:
            raise AssertionError("Wrong key type")
        if key_type in Wallet.keyMap:
            return Wallet.keyMap.get(key_type)
        else:
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
        """
        if key_type not in ["owner", "active", "posting", "memo"]:
            raise AssertionError("Wrong key type")
        if key_type in Wallet.keyMap:
            return Wallet.keyMap.get(key_type)
        else:
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
        pub = self._get_pub_from_wif(wif)
        return self.getAccountFromPublicKey(pub)

    def getAccountsFromPublicKey(self, pub):
        """ Obtain all accounts associated with a public key
        """
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            names = self.steem.rpc.get_key_references({'keys': [pub]}, api="account_by_key")["accounts"]
        else:
            names = self.steem.rpc.get_key_references([pub], api="account_by_key")
        for name in names:
            for i in name:
                yield i

    def getAccountFromPublicKey(self, pub):
        """ Obtain the first account name from public key
        """
        # FIXME, this only returns the first associated key.
        # If the key is used by multiple accounts, this
        # will surely lead to undesired behavior
        if self.rpc.get_use_appbase():
            names = self.rpc.get_key_references({'keys': [pub]}, api="account_by_key")["accounts"][0]
        else:
            names = self.rpc.get_key_references([pub], api="account_by_key")[0]
        if not names:
            return None
        else:
            return names[0]

    def getAllAccounts(self, pub):
        """ Get the account data for a public key (all accounts found for this
            public key)
        """
        for name in self.getAccountsFromPublicKey(pub):
            try:
                account = Account(name, steem_instance=self.steem)
            except AccountDoesNotExistsException:
                continue
            yield {"name": account["name"],
                   "account": account,
                   "type": self.getKeyType(account, pub),
                   "pubkey": pub}

    def getAccount(self, pub):
        """ Get the account data for a public key (first account found for this
            public key)
        """
        name = self.getAccountFromPublicKey(pub)
        if not name:
            return {"name": None, "type": None, "pubkey": pub}
        else:
            try:
                account = Account(name, steem_instance=self.steem)
            except:
                return
            return {"name": account["name"],
                    "account": account,
                    "type": self.getKeyType(account, pub),
                    "pubkey": pub}

    def getKeyType(self, account, pub):
        """ Get key type
        """
        for authority in ["owner", "active", "posting"]:
            for key in account[authority]["key_auths"]:
                if pub == key[0]:
                    return authority
        if pub == account["memo_key"]:
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

    def getPublicKeys(self):
        """ Return all installed public keys
        """
        if self.keyStorage:
            return self.keyStorage.getPublicKeys()
        else:
            return list(Wallet.keys.keys())

    def getPublicNames(self):
        """ Return all installed public token
        """
        if self.tokenStorage:
            return self.tokenStorage.getPublicNames()
        else:
            return list(Wallet.token.keys())
