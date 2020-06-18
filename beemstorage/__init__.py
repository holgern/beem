# -*- coding: utf-8 -*-
# Load modules from other classes
# # Inspired by https://raw.githubusercontent.com/xeroc/python-graphenelib/master/graphenestorage/__init__.py
from .base import (
    InRamConfigurationStore,
    InRamPlainKeyStore,
    InRamEncryptedKeyStore,
    InRamPlainTokenStore,
    InRamEncryptedTokenStore,    
    SqliteConfigurationStore,
    SqlitePlainKeyStore,
    SqliteEncryptedKeyStore,
    SqlitePlainTokenStore,
    SqliteEncryptedTokenStore,    
)
from .sqlite import SQLiteFile, SQLiteCommon

__all__ = ["interfaces", "masterpassword", "base", "sqlite", "ram"]


def get_default_config_store(*args, **kwargs):
    """ This method returns the default **configuration** store
        that uses an SQLite database internally.
        :params str appname: The appname that is used internally to distinguish
            different SQLite files
    """
    kwargs["appname"] = kwargs.get("appname", "beem")
    return SqliteConfigurationStore(*args, **kwargs)


def get_default_key_store(*args, config, **kwargs):
    """ This method returns the default **key** store
        that uses an SQLite database internally.
        :params str appname: The appname that is used internally to distinguish
            different SQLite files
    """
    kwargs["appname"] = kwargs.get("appname", "beem")
    return SqliteEncryptedKeyStore(config=config, **kwargs)
