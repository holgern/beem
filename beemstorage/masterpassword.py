# -*- coding: utf-8 -*-
# Inspired by https://raw.githubusercontent.com/xeroc/python-graphenelib/master/graphenestorage/masterpassword.py
import os
import hashlib
import logging
import warnings

from binascii import hexlify
from beemgraphenebase.py23 import py23_bytes
from beemgraphenebase import bip38
from beemgraphenebase.aes import AESCipher
from .exceptions import WrongMasterPasswordException, WalletLocked
try:
    import keyring
    if not isinstance(keyring.get_keyring(), keyring.backends.fail.Keyring):
        KEYRING_AVAILABLE = True
    else:
        KEYRING_AVAILABLE = False
except ImportError:
    KEYRING_AVAILABLE = False

log = logging.getLogger(__name__)


class MasterPassword(object):
    """ The keys are encrypted with a Masterpassword that is stored in
        the configurationStore. It has a checksum to verify correctness
        of the password
        The encrypted private keys in `keys` are encrypted with a random
        **masterkey/masterpassword** that is stored in the configuration
        encrypted by the user-provided password.

        :param ConfigStore config: Configuration store to get access to the
            encrypted master password
    """

    def __init__(self, config=None, **kwargs):
        if config is None:
            raise ValueError("If using encrypted store, a config store is required!")
        self.config = config
        self.password = None
        self.decrypted_master = None
        self.config_key = "encrypted_master_password"

    @property
    def masterkey(self):
        """ Contains the **decrypted** master key
        """
        return self.decrypted_master

    def has_masterpassword(self):
        """ Tells us if the config store knows an encrypted masterpassword
        """
        return self.config_key in self.config

    def locked(self):
        """ Is the store locked. E.g. Is a valid password known that can be
            used to decrypt the master key?
        """
        return not self.unlocked()

    def unlocked(self):
        """ Is the store unlocked so that I can decrypt the content?
        """
        if self.password is not None:
            return bool(self.password)
        else:
            password_storage = self.config["password_storage"]
            if (
                "UNLOCK" in os.environ
                and os.environ["UNLOCK"]
                and self.config_key in self.config
                and self.config[self.config_key]
                and password_storage == "environment"
            ):
                log.debug("Trying to use environmental " "variable to unlock wallet")
                self.unlock(os.environ.get("UNLOCK"))
                return bool(self.password)
            elif (
                password_storage == "keyring"
                and KEYRING_AVAILABLE
                and self.config_key in self.config
                and self.config[self.config_key]                
            ):
                log.debug("Trying to use keyring to unlock wallet")
                pwd = keyring.get_password("beem", "wallet")
                self.unlock(pwd)
                return bool(self.password)
        return False

    def lock(self):
        """ Lock the store so that we can no longer decrypt the content of the
            store
        """
        self.password = None
        self.decrypted_master = None

    def unlock(self, password):
        """ The password is used to encrypt this masterpassword. To
            decrypt the keys stored in the keys database, one must use
            BIP38, decrypt the masterpassword from the configuration
            store with the user password, and use the decrypted
            masterpassword to decrypt the BIP38 encrypted private keys
            from the keys storage!

            :param str password: Password to use for en-/de-cryption
        """
        self.password = password
        if self.config_key in self.config and self.config[self.config_key]:
            self._decrypt_masterpassword()
        else:
            self._new_masterpassword(password)
            self._save_encrypted_masterpassword()

    def wipe_masterpassword(self):
        """ Removes the encrypted masterpassword from config storage"""
        if self.config_key in self.config and self.config[self.config_key]:
            self.config[self.config_key] = None

    def _decrypt_masterpassword(self):
        """ Decrypt the encrypted masterkey
        """
        aes = AESCipher(self.password)
        checksum, encrypted_master = self.config[self.config_key].split("$")
        try:
            decrypted_master = aes.decrypt(encrypted_master)
        except Exception:
            self._raise_wrongmasterpassexception()
        if checksum != self._derive_checksum(decrypted_master):
            self._raise_wrongmasterpassexception()
        self.decrypted_master = decrypted_master

    def _raise_wrongmasterpassexception(self):
        self.password = None
        raise WrongMasterPasswordException

    def _save_encrypted_masterpassword(self):
        self.config[self.config_key] = self._get_encrypted_masterpassword()

    def _new_masterpassword(self, password):
        """ Generate a new random masterkey, encrypt it with the password and
            store it in the store.

            :param str password: Password to use for en-/de-cryption
        """
        # make sure to not overwrite an existing key
        if self.config_key in self.config and self.config[self.config_key]:
            raise Exception("Storage already has a masterpassword!")

        self.decrypted_master = hexlify(os.urandom(32)).decode("ascii")

        # Encrypt and save master
        self.password = password
        self._save_encrypted_masterpassword()
        return self.masterkey

    def _derive_checksum(self, s):
        """ Derive the checksum

            :param str s: Random string for which to derive the checksum
        """
        checksum = hashlib.sha256(bytes(s, "ascii")).hexdigest()
        return checksum[:4]

    def _get_encrypted_masterpassword(self):
        """ Obtain the encrypted masterkey

            .. note:: The encrypted masterkey is checksummed, so that we can
                figure out that a provided password is correct or not. The
                checksum is only 4 bytes long!
        """
        if not self.unlocked():
            raise WalletLocked
        aes = AESCipher(self.password)
        return "{}${}".format(
            self._derive_checksum(self.masterkey), aes.encrypt(self.masterkey)
        )

    def change_password(self, newpassword):
        """ Change the password that allows to decrypt the master key
        """
        if not self.unlocked():
            raise WalletLocked
        self.password = newpassword
        self._save_encrypted_masterpassword()

    def decrypt(self, wif):
        """ Decrypt the content according to BIP38

            :param str wif: Encrypted key
        """
        if not self.unlocked():
            raise WalletLocked
        return format(bip38.decrypt(wif, self.masterkey), "wif")

    def deriveChecksum(self, s):
        """ Derive the checksum
        """
        checksum = hashlib.sha256(py23_bytes(s, "ascii")).hexdigest()
        return checksum[:4]

    def encrypt_text(self, txt):
        """ Encrypt the content according to BIP38

            :param str wif: Unencrypted key
        """
        if not self.unlocked():
            raise WalletLocked
        aes = AESCipher(self.masterkey)
        return "{}${}".format(self.deriveChecksum(txt), aes.encrypt(txt))

    def decrypt_text(self, enctxt):
        """ Decrypt the content according to BIP38

            :param str wif: Encrypted key
        """
        if not self.unlocked():
            raise WalletLocked
        aes = AESCipher(self.masterkey)
        checksum, encrypted_text = enctxt.split("$")
        try:
            decrypted_text = aes.decrypt(encrypted_text)
        except:
            raise WrongMasterPasswordException
        if checksum != self.deriveChecksum(decrypted_text):
            raise WrongMasterPasswordException
        return decrypted_text

    def encrypt(self, wif):
        """ Encrypt the content according to BIP38

            :param str wif: Unencrypted key
        """
        if not self.unlocked():
            raise WalletLocked
        return format(bip38.encrypt(str(wif), self.masterkey), "encwif")

    def changePassword(self, newpassword):  # pragma: no cover
        warnings.warn(
            "changePassword will be replaced by change_password in the future",
            PendingDeprecationWarning,
        )
        return self.change_password(newpassword)
