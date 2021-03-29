from builtins import chr
from builtins import range
from builtins import str
import unittest
import hashlib
from binascii import hexlify, unhexlify
import os
import json
from pprint import pprint
from beemstorage.base import InRamConfigurationStore, InRamEncryptedKeyStore
from beemstorage.exceptions import WrongMasterPasswordException


class Testcases(unittest.TestCase):
    def test_masterpassword(self):
        password = "foobar"
        config = InRamConfigurationStore()
        keys = InRamEncryptedKeyStore(config=config)
        self.assertFalse(keys.has_masterpassword())
        master = keys._new_masterpassword(password)
        self.assertEqual(
            len(master),
            len("66eaab244153031e8172e6ffed321" "7288515ddb63646bbefa981a654bdf25b9f"),
        )
        with self.assertRaises(Exception):
            keys._new_masterpassword(master)

        keys.lock()

        with self.assertRaises(Exception):
            keys.change_password("foobar")

        keys.unlock(password)
        self.assertEqual(keys.decrypted_master, master)

        new_pass = "new_secret_password"
        keys.change_password(new_pass)
        keys.lock()
        keys.unlock(new_pass)
        self.assertEqual(keys.decrypted_master, master)

    def test_wrongmastermass(self):
        config = InRamConfigurationStore()
        keys = InRamEncryptedKeyStore(config=config)
        keys._new_masterpassword("foobar")
        keys.lock()
        with self.assertRaises(WrongMasterPasswordException):
            keys.unlock("foobar2")

    def test_masterpwd(self):
        with self.assertRaises(Exception):
            InRamEncryptedKeyStore()
        config = InRamConfigurationStore()
        config["password_storage"] = "environment"
        keys = InRamEncryptedKeyStore(config=config)
        self.assertTrue(keys.locked())
        keys.unlock("foobar")
        keys.password = "FOoo"
        with self.assertRaises(Exception):
            keys._decrypt_masterpassword()
        keys.lock()

        with self.assertRaises(WrongMasterPasswordException):
            keys.unlock("foobar2")

        with self.assertRaises(Exception):
            keys._get_encrypted_masterpassword()

        self.assertFalse(keys.unlocked())

        os.environ["UNLOCK"] = "foobar"
        self.assertTrue(keys.unlocked())

        self.assertFalse(keys.locked())
