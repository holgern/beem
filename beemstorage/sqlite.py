# -*- coding: utf-8 -*-
# Inspired by https://raw.githubusercontent.com/xeroc/python-graphenelib/master/graphenestorage/sqlite.py
import os
import sqlite3
import logging
import shutil
from datetime import datetime
from appdirs import user_data_dir
import time

from .interfaces import StoreInterface

log = logging.getLogger(__name__)
timeformat = "%Y%m%d-%H%M%S"


class SQLiteFile:
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

         .. note:: The file name can be overwritten when providing a keyword
            argument ``profile``.
    """

    def __init__(self, *args, **kwargs):
        appauthor = "beem"
        appname = kwargs.get("appname", "beem")
        self.data_dir = kwargs.get("data_dir", user_data_dir(appname, appauthor))

        if "profile" in kwargs:
            self.storageDatabase = "{}.sqlite".format(kwargs["profile"])
        else:
            self.storageDatabase = "{}.sqlite".format(appname)
        
        self.sqlite_file = os.path.join(self.data_dir, self.storageDatabase)

        """ Ensure that the directory in which the data is stored
            exists
        """
        if os.path.isdir(self.data_dir):  # pragma: no cover
            return
        else:  # pragma: no cover
            os.makedirs(self.data_dir)

    def sqlite3_backup(self, backupdir):
        """ Create timestamped database copy
        """
        if not os.path.isdir(backupdir):
            os.mkdir(backupdir)
        backup_file = os.path.join(
            backupdir,
            os.path.basename(self.storageDatabase) +
            datetime.utcnow().strftime("-" + timeformat))
        self.sqlite3_copy(self.sqlite_file, backup_file)

    def sqlite3_copy(self, src, dst):
        """Copy sql file from src to dst"""
        if not os.path.isfile(src):
            return
        connection = sqlite3.connect(self.sqlite_file)
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
            self.sqlite3_copy(newest_backup_file, self.sqlite_file)

    def clean_data(self, backupdir="backups"):
        """ Delete files older than 70 days
        """
        log.info("Cleaning up old backups")
        backupdir = os.path.join(self.data_dir, backupdir)
        for filename in os.listdir(backupdir):
            backup_file = os.path.join(backupdir, filename)
            if os.stat(backup_file).st_ctime < (time.time() - 70 * 86400):
                if os.path.isfile(backup_file):
                    os.remove(backup_file)
                    log.info("Deleting {}...".format(backup_file))

    def refreshBackup(self):
        """ Make a new backup
        """
        backupdir = os.path.join(self.data_dir, "backups")
        self.sqlite3_backup(backupdir)
        self.clean_data(backupdir)


class SQLiteCommon(object):
    """ This class abstracts away common sqlite3 operations.

        This class should not be used directly.

        When inheriting from this class, the following instance members must
        be defined:

            * ``sqlite_file``: Path to the SQLite Database file
    """
    def sql_fetchone(self, query):
        connection = sqlite3.connect(self.sqlite_file)
        try:
            cursor = connection.cursor()
            cursor.execute(*query)
            result = cursor.fetchone()
        finally:
            connection.close()
        return result

    def sql_fetchall(self, query):
        connection = sqlite3.connect(self.sqlite_file)
        try:
            cursor = connection.cursor()
            cursor.execute(*query)
            results = cursor.fetchall()
        finally:
            connection.close()
        return results

    def sql_execute(self, query, lastid=False):
        connection = sqlite3.connect(self.sqlite_file)
        try:
            cursor = connection.cursor()
            cursor.execute(*query)
            connection.commit()
        except:
            connection.close()
            raise
        ret = None
        try:
            if lastid:
                cursor = connection.cursor()
                cursor.execute("SELECT last_insert_rowid();")
                ret = cursor.fetchone()[0]
        finally:
            connection.close()
        return ret


class SQLiteStore(SQLiteFile, SQLiteCommon, StoreInterface):
    """ The SQLiteStore deals with the sqlite3 part of storing data into a
        database file.

        .. note:: This module is limited to two columns and merely stores
            key/value pairs into the sqlite database

        On first launch, the database file as well as the tables are created
        automatically.

        When inheriting from this class, the following three class members must
        be defined:

            * ``__tablename__``: Name of the table
            * ``__key__``: Name of the key column
            * ``__value__``: Name of the value column
    """

    #:
    __tablename__ = None
    __key__ = None
    __value__ = None

    def __init__(self, *args, **kwargs):
        #: Storage
        SQLiteFile.__init__(self, *args, **kwargs)
        StoreInterface.__init__(self, *args, **kwargs)
        if self.__tablename__ is None or self.__key__ is None or self.__value__ is None:
            raise ValueError("Values missing for tablename, key, or value!")
        if not self.exists():  # pragma: no cover
            self.create()

    def _haveKey(self, key):
        """ Is the key `key` available?
        """
        query = (
            "SELECT {} FROM {} WHERE {}=?".format(
                self.__value__,
                self.__tablename__,
                self.__key__
            ), (key,))
        return True if self.sql_fetchone(query) else False

    def __setitem__(self, key, value):
        """ Sets an item in the store

            :param str key: Key
            :param str value: Value
        """
        if self._haveKey(key):
            query = (
                "UPDATE {} SET {}=? WHERE {}=?".format(
                    self.__tablename__, self.__value__, self.__key__
                ),
                (value, key),
            )
        else:
            query = (
                "INSERT INTO {} ({}, {}) VALUES (?, ?)".format(
                    self.__tablename__, self.__key__, self.__value__
                ),
                (key, value),
            )
        self.sql_execute(query)

    def __getitem__(self, key):
        """ Gets an item from the store as if it was a dictionary

            :param str value: Value
        """
        query = (
            "SELECT {} FROM {} WHERE {}=?".format(
                self.__value__,
                self.__tablename__,
                self.__key__
            ), (key,))
        result = self.sql_fetchone(query)
        if result:
            return result[0]
        else:
            if key in self.defaults:
                return self.defaults[key]
            else:
                return None

    def __iter__(self):
        """ Iterates through the store
        """
        return iter(self.keys())

    def keys(self):
        query = ("SELECT {} from {}".format(
            self.__key__,
            self.__tablename__), )
        return [x[0] for x in self.sql_fetchall(query)]

    def __len__(self):
        """ return lenght of store
        """
        query = ("SELECT id from {}".format(self.__tablename__), )
        return len(self.sql_fetchall(query))

    def __contains__(self, key):
        """ Tests if a key is contained in the store.

            May test againsts self.defaults

            :param str value: Value
        """
        if self._haveKey(key) or key in self.defaults:
            return True
        else:
            return False

    def items(self):
        """ returns all items off the store as tuples
        """
        query = ("SELECT {}, {} from {}".format(
            self.__key__,
            self.__value__,
            self.__tablename__), )
        r = []
        for key, value in self.sql_fetchall(query):
            r.append((key, value))
        return r

    def get(self, key, default=None):
        """ Return the key if exists or a default value

            :param str value: Value
            :param str default: Default value if key not present
        """
        if key in self:
            return self.__getitem__(key)
        else:
            return default

    # Specific for this library
    def delete(self, key):
        """ Delete a key from the store

            :param str value: Value
        """
        query = (
            "DELETE FROM {} WHERE {}=?".format(
                self.__tablename__,
                self.__key__
            ), (key,))
        self.sql_execute(query)

    def wipe(self):
        """ Wipe the store
        """
        query = ("DELETE FROM {}".format(self.__tablename__), )
        self.sql_execute(query)

    def exists(self):
        """ Check if the database table exists
        """
        query = ("SELECT name FROM sqlite_master " +
                 "WHERE type='table' AND name=?",
                 (self.__tablename__, ))
        return True if self.sql_fetchone(query) else False

    def create(self):  # pragma: no cover
        """ Create the new table in the SQLite database
        """
        query = ((
            """
            CREATE TABLE {} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {} STRING(256),
                {} STRING(256)
            )"""
        ).format(
            self.__tablename__,
            self.__key__,
            self.__value__
        ), )
        self.sql_execute(query)
