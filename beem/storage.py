# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes
from builtins import object
from beemgraphenebase.py23 import py23_bytes, bytes_types
import shutil
import time
import os
import sqlite3
from .aes import AESCipher
from appdirs import user_data_dir
from datetime import datetime
import logging
from binascii import hexlify
import random
import hashlib
from .exceptions import WrongMasterPasswordException, NoWriteAccess
from .nodelist import NodeList
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

timeformat = "%Y%m%d-%H%M%S"


class DataDir(object):
    """ This class ensures that the user's data is stored in its OS
        preotected user directory:

        **OSX:**

         * `~/Library/Application Support/<AppName>`

        **Windows:**

         * `C:\\Documents and Settings\\<User>\\Application Data\\Local Settings\\<AppAuthor>\\<AppName>`
         * `C:\\Documents and Settings\\<User>\\Application Data\\<AppAuthor>\\<AppName>`

        **Linux:**

         * `~/.local/share/<AppName>`

         Furthermore, it offers an interface to generated backups
         in the `backups/` directory every now and then.
    """
    appname = "beem"
    appauthor = "beem"
    storageDatabase = "beem.sqlite"

    data_dir = user_data_dir(appname, appauthor)
    sqlDataBaseFile = os.path.join(data_dir, storageDatabase)

    def __init__(self):
        #: Storage
        self.mkdir_p()

    def mkdir_p(self):
        """ Ensure that the directory in which the data is stored
            exists
        """
        if os.path.isdir(self.data_dir):
            return
        else:
            try:
                os.makedirs(self.data_dir)
            except FileExistsError:
                self.sqlDataBaseFile = ":memory:"
                return
            except OSError:
                self.sqlDataBaseFile = ":memory:"
                return

    def sqlite3_backup(self, backupdir):
        """ Create timestamped database copy
        """
        if self.sqlDataBaseFile == ":memory:":
            return
        if not os.path.isdir(backupdir):
            os.mkdir(backupdir)
        backup_file = os.path.join(
            backupdir,
            os.path.basename(self.storageDatabase) +
            datetime.utcnow().strftime("-" + timeformat))
        self.sqlite3_copy(self.sqlDataBaseFile, backup_file)
        configStorage["lastBackup"] = datetime.utcnow().strftime(timeformat)

    def sqlite3_copy(self, src, dst):
        """Copy sql file from src to dst"""
        if self.sqlDataBaseFile == ":memory:":
            return
        if not os.path.isfile(src):
            return
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        # Lock database before making a backup
        cursor.execute('begin immediate')
        # Make new backup file
        shutil.copyfile(src, dst)
        log.info("Creating {}...".format(dst))
        # Unlock database
        connection.rollback()

    def recover_with_latest_backup(self, backupdir="backups"):
        """ Replace database with latest backup"""
        file_date = 0
        if self.sqlDataBaseFile == ":memory:":
            return
        if not os.path.isdir(backupdir):
            backupdir = os.path.join(self.data_dir, backupdir)
        if not os.path.isdir(backupdir):
            return
        newest_backup_file = None
        for filename in os.listdir(backupdir):
            backup_file = os.path.join(backupdir, filename)
            if os.stat(backup_file).st_ctime > file_date:
                if os.path.isfile(backup_file):
                    file_date = os.stat(backup_file).st_ctime
                    newest_backup_file = backup_file
        if newest_backup_file is not None:
            self.sqlite3_copy(newest_backup_file, self.sqlDataBaseFile)

    def clean_data(self):
        """ Delete files older than 70 days
        """
        if self.sqlDataBaseFile == ":memory:":
            return
        log.info("Cleaning up old backups")
        for filename in os.listdir(self.data_dir):
            backup_file = os.path.join(self.data_dir, filename)
            if os.stat(backup_file).st_ctime < (time.time() - 70 * 86400):
                if os.path.isfile(backup_file):
                    os.remove(backup_file)
                    log.info("Deleting {}...".format(backup_file))

    def refreshBackup(self):
        """ Make a new backup
        """
        backupdir = os.path.join(self.data_dir, "backups")
        self.sqlite3_backup(backupdir)
        self.clean_data()


class Key(DataDir):
    """ This is the key storage that stores the public key and the
        (possibly encrypted) private key in the `keys` table in the
        SQLite3 database.
    """
    __tablename__ = 'keys'

    def __init__(self):
        super(Key, self).__init__()

    def exists_table(self):
        """ Check if the database table exists
        """
        query = ("SELECT name FROM sqlite_master "
                 "WHERE type='table' AND name=?", (self.__tablename__, ))
        try:
            connection = sqlite3.connect(self.sqlDataBaseFile)
            cursor = connection.cursor()
            cursor.execute(*query)
            return True if cursor.fetchone() else False
        except sqlite3.OperationalError:
            self.sqlDataBaseFile = ":memory:"
            log.warning("Could not read(database: %s)" % (self.sqlDataBaseFile))
            return True

    def create_table(self):
        """ Create the new table in the SQLite database
        """
        query = ("CREATE TABLE {0} ("
                 "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "pub STRING(256),"
                 "wif STRING(256))".format(self.__tablename__))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()

    def getPublicKeys(self):
        """ Returns the public keys stored in the database
        """
        query = ("SELECT pub from {0} ".format(self.__tablename__))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            return [x[0] for x in results]
        except sqlite3.OperationalError:
            return []

    def getPrivateKeyForPublicKey(self, pub):
        """Returns the (possibly encrypted) private key that
           corresponds to a public key

           :param str pub: Public key

           The encryption scheme is BIP38
        """
        query = ("SELECT wif from {0} WHERE pub=?".format(self.__tablename__), (pub,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        key = cursor.fetchone()
        if key:
            return key[0]
        else:
            return None

    def updateWif(self, pub, wif):
        """ Change the wif to a pubkey

           :param str pub: Public key
           :param str wif: Private key
        """
        query = ("UPDATE {0} SET wif=? WHERE pub=?".format(self.__tablename__), (wif, pub))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()

    def add(self, wif, pub):
        """Add a new public/private key pair (correspondence has to be
           checked elsewhere!)

           :param str pub: Public key
           :param str wif: Private key
        """
        if self.getPrivateKeyForPublicKey(pub):
            raise ValueError("Key already in storage")
        query = ("INSERT INTO {0} (pub, wif) VALUES (?, ?)".format(self.__tablename__), (pub, wif))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()

    def delete(self, pub):
        """ Delete the key identified as `pub`

           :param str pub: Public key
        """
        query = ("DELETE FROM {0} WHERE pub=?".format(self.__tablename__), (pub,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()

    def wipe(self, sure=False):
        """Purge the entire wallet. No keys will survive this!"""
        if not sure:
            log.error(
                "You need to confirm that you are sure "
                "and understand the implications of "
                "wiping your wallet!"
            )
            return
        else:
            query = ("DELETE FROM {0} ".format(self.__tablename__))
            connection = sqlite3.connect(self.sqlDataBaseFile)
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()


class Token(DataDir):
    """ This is the token storage that stores the public username and the
        (possibly encrypted) token in the `token` table in the
        SQLite3 database.
    """
    __tablename__ = 'token'

    def __init__(self):
        super(Token, self).__init__()

    def exists_table(self):
        """ Check if the database table exists
        """
        query = ("SELECT name FROM sqlite_master "
                 "WHERE type='table' AND name=?", (self.__tablename__, ))
        try:
            connection = sqlite3.connect(self.sqlDataBaseFile)
            cursor = connection.cursor()
            cursor.execute(*query)
            return True if cursor.fetchone() else False
        except sqlite3.OperationalError:
            self.sqlDataBaseFile = ":memory:"
            log.warning("Could not read(database: %s)" % (self.sqlDataBaseFile))
            return True

    def create_table(self):
        """ Create the new table in the SQLite database
        """
        query = ("CREATE TABLE {0} ("
                 "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "name STRING(256),"
                 "token STRING(256))".format(self.__tablename__))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()

    def getPublicNames(self):
        """ Returns the public names stored in the database
        """
        query = ("SELECT name from {0} ".format(self.__tablename__))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            return [x[0] for x in results]
        except sqlite3.OperationalError:
            return []

    def getTokenForPublicName(self, name):
        """Returns the (possibly encrypted) private token that
           corresponds to a public name

           :param str pub: Public name

           The encryption scheme is BIP38
        """
        query = ("SELECT token from {0} WHERE name=?".format(self.__tablename__), (name,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        token = cursor.fetchone()
        if token:
            return token[0]
        else:
            return None

    def updateToken(self, name, token):
        """ Change the token to a name

           :param str name: Public name
           :param str token: Private token
        """
        query = ("UPDATE {0} SET token=? WHERE name=?".format(self.__tablename__), (token, name))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()

    def add(self, name, token):
        """Add a new public/private token pair (correspondence has to be
           checked elsewhere!)

           :param str name: Public name
           :param str token: Private token
        """
        if self.getTokenForPublicName(name):
            raise ValueError("Key already in storage")
        query = ("INSERT INTO {0} (name, token) VALUES (?, ?)".format(self.__tablename__), (name, token))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()

    def delete(self, name):
        """ Delete the key identified as `name`

           :param str name: Public name
        """
        query = ("DELETE FROM {0} WHERE name=?".format(self.__tablename__), (name,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()

    def wipe(self, sure=False):
        """Purge the entire wallet. No keys will survive this!"""
        if not sure:
            log.error(
                "You need to confirm that you are sure "
                "and understand the implications of "
                "wiping your wallet!"
            )
            return
        else:
            query = ("DELETE FROM {0} ".format(self.__tablename__))
            connection = sqlite3.connect(self.sqlDataBaseFile)
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()


class Configuration(DataDir):
    """ This is the configuration storage that stores key/value
        pairs in the `config` table of the SQLite3 database.
    """
    __tablename__ = "config"

    #: Default configuration
    nodelist = NodeList()
    nodes = nodelist.get_nodes(normal=True, appbase=True, dev=False, testnet=False)
    config_defaults = {
        "node": nodes,
        "password_storage": "environment",
        "rpcpassword": "",
        "rpcuser": "",
        "order-expiration": 7 * 24 * 60 * 60,
        "client_id": "",
        "hot_sign_redirect_uri": None,
        "sc2_api_url": "https://steemconnect.com/api/",
        "oauth_base_url": "https://steemconnect.com/oauth2/"}

    def __init__(self):
        super(Configuration, self).__init__()

    def exists_table(self):
        """ Check if the database table exists
        """
        query = ("SELECT name FROM sqlite_master "
                 "WHERE type='table' AND name=?", (self.__tablename__,))
        try:
            connection = sqlite3.connect(self.sqlDataBaseFile)
            cursor = connection.cursor()
            cursor.execute(*query)
            return True if cursor.fetchone() else False
        except sqlite3.OperationalError:
            self.sqlDataBaseFile = ":memory:"
            log.warning("Could not read(database: %s)" % (self.sqlDataBaseFile))
            return True

    def create_table(self):
        """ Create the new table in the SQLite database
        """
        query = ("CREATE TABLE {0} ("
                 "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "key STRING(256),"
                 "value STRING(256))".format(self.__tablename__))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            connection.commit()
        except sqlite3.OperationalError:
            log.error("Could not write to database: %s" % (self.__tablename__))
            raise NoWriteAccess("Could not write to database: %s" % (self.__tablename__))

    def checkBackup(self):
        """ Backup the SQL database every 7 days
        """
        if ("lastBackup" not in configStorage or
                configStorage["lastBackup"] == ""):
            print("No backup has been created yet!")
            self.refreshBackup()
        try:
            if (
                datetime.utcnow() -
                datetime.strptime(configStorage["lastBackup"],
                                  timeformat)
            ).days > 7:
                print("Backups older than 7 days!")
                self.refreshBackup()
        except:
            self.refreshBackup()

    def _haveKey(self, key):
        """ Is the key `key` available int he configuration?
        """
        query = ("SELECT value FROM {0} WHERE key=?".format(self.__tablename__), (key,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        try:
            cursor.execute(*query)
            return True if cursor.fetchone() else False
        except sqlite3.OperationalError:
            log.warning("Could not read %s (database: %s)" % (str(key), self.__tablename__))
            return False

    def __getitem__(self, key):
        """ This method behaves differently from regular `dict` in that
            it returns `None` if a key is not found!
        """
        query = ("SELECT value FROM {0} WHERE key=?".format(self.__tablename__), (key,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        try:
            cursor.execute(*query)
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                if key in self.config_defaults:
                    return self.config_defaults[key]
                else:
                    return None
        except sqlite3.OperationalError:
            log.warning("Could not read %s (database: %s)" % (str(key), self.__tablename__))
            if key in self.config_defaults:
                return self.config_defaults[key]
            else:
                return None

    def get(self, key, default=None):
        """ Return the key if exists or a default value
        """
        if key in self:
            return self.__getitem__(key)
        else:
            return default

    def __contains__(self, key):
        if self._haveKey(key) or key in self.config_defaults:
            return True
        else:
            return False

    def __setitem__(self, key, value):
        if self._haveKey(key):
            query = ("UPDATE {0} SET value=? WHERE key=?".format(self.__tablename__), (value, key))
        else:
            query = ("INSERT INTO {0} (key, value) VALUES (?, ?)".format(self.__tablename__), (key, value))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        try:
            cursor.execute(*query)
            connection.commit()
        except sqlite3.OperationalError:
            log.error("Could not write to %s (database: %s)" % (str(key), self.__tablename__))
            raise NoWriteAccess("Could not write to %s (database: %s)" % (str(key), self.__tablename__))

    def delete(self, key):
        """ Delete a key from the configuration store
        """
        query = ("DELETE FROM {0} WHERE key=?".format(self.__tablename__), (key,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        try:
            cursor.execute(*query)
            connection.commit()
        except sqlite3.OperationalError:
            log.error("Could not write to %s (database: %s)" % (str(key), self.__tablename__))
            raise NoWriteAccess("Could not write to %s (database: %s)" % (str(key), self.__tablename__))

    def __iter__(self):
        return iter(list(self.items()))

    def items(self):
        query = ("SELECT key, value from {0} ".format(self.__tablename__))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(query)
        r = {}
        for key, value in cursor.fetchall():
            r[key] = value
        return r

    def __len__(self):
        query = ("SELECT id from {0} ".format(self.__tablename__))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(query)
        return len(cursor.fetchall())


class MasterPassword(object):
    """ The keys are encrypted with a Masterpassword that is stored in
        the configurationStore. It has a checksum to verify correctness
        of the password
    """

    password = ""  # nosec
    decrypted_master = ""

    #: This key identifies the encrypted master password stored in the confiration
    config_key = "encrypted_master_password"

    def __init__(self, password):
        """ The encrypted private keys in `keys` are encrypted with a
            random encrypted masterpassword that is stored in the
            configuration.

            The password is used to encrypt this masterpassword. To
            decrypt the keys stored in the keys database, one must use
            BIP38, decrypt the masterpassword from the configuration
            store with the user password, and use the decrypted
            masterpassword to decrypt the BIP38 encrypted private keys
            from the keys storage!

            :param str password: Password to use for en-/de-cryption
        """
        self.password = password
        if self.config_key not in configStorage:
            self.newMaster()
            self.saveEncrytpedMaster()
        else:
            self.decryptEncryptedMaster()

    def decryptEncryptedMaster(self):
        """ Decrypt the encrypted masterpassword
        """
        aes = AESCipher(self.password)
        checksum, encrypted_master = configStorage[self.config_key].split("$")
        try:
            decrypted_master = aes.decrypt(encrypted_master)
        except:
            raise WrongMasterPasswordException
        if checksum != self.deriveChecksum(decrypted_master):
            raise WrongMasterPasswordException
        self.decrypted_master = decrypted_master

    def saveEncrytpedMaster(self):
        """ Store the encrypted master password in the configuration
            store
        """
        configStorage[self.config_key] = self.getEncryptedMaster()

    def newMaster(self):
        """ Generate a new random masterpassword
        """
        # make sure to not overwrite an existing key
        if (self.config_key in configStorage and
                configStorage[self.config_key]):
            return
        self.decrypted_master = hexlify(os.urandom(32)).decode("ascii")

    def deriveChecksum(self, s):
        """ Derive the checksum
        """
        checksum = hashlib.sha256(py23_bytes(s, "ascii")).hexdigest()
        return checksum[:4]

    def getEncryptedMaster(self):
        """ Obtain the encrypted masterkey
        """
        if not self.decrypted_master:
            raise Exception("master not decrypted")
        aes = AESCipher(self.password)
        return "{}${}".format(self.deriveChecksum(self.decrypted_master),
                              aes.encrypt(self.decrypted_master))

    def changePassword(self, newpassword):
        """ Change the password
        """
        self.password = newpassword
        self.saveEncrytpedMaster()

    @staticmethod
    def wipe(sure=False):
        """Remove all keys from configStorage"""
        if not sure:
            log.error(
                "You need to confirm that you are sure "
                "and understand the implications of "
                "wiping your wallet!"
            )
            return
        else:
            configStorage.delete(MasterPassword.config_key)


# Create keyStorage
keyStorage = Key()
tokenStorage = Token()
configStorage = Configuration()

# Create Tables if database is brand new
if not configStorage.exists_table():
    configStorage.create_table()

newKeyStorage = False
if not keyStorage.exists_table():
    newKeyStorage = True
    keyStorage.create_table()

newTokenStorage = False
if not tokenStorage.exists_table():
    newTokenStorage = True
    tokenStorage.create_table()
