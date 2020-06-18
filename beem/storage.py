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
from beemgraphenebase.aes import AESCipher
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
from beemstorage import (
    SqliteConfigurationStore,
    SqliteEncryptedKeyStore,
)

timeformat = "%Y%m%d-%H%M%S"

#: Default configuration
nodelist = NodeList()
blockchain = "hive"
if blockchain == "hive":
    nodes = nodelist.get_hive_nodes(testnet=False)
elif blockchain == "steem":
    nodes = nodelist.get_steem_nodes(testnet=False)
else:
    nodes = []

SqliteConfigurationStore.setdefault("node", nodes)
SqliteConfigurationStore.setdefault("default_chain", blockchain)
SqliteConfigurationStore.setdefault("password_storage", "environment")
SqliteConfigurationStore.setdefault("rpcpassword", "")
SqliteConfigurationStore.setdefault("rpcuser", "")
SqliteConfigurationStore.setdefault("order-expiration", 7 * 24 * 60 * 60)
SqliteConfigurationStore.setdefault("client_id", "")
SqliteConfigurationStore.setdefault("sc2_client_id", None)
SqliteConfigurationStore.setdefault("hs_client_id", None)
SqliteConfigurationStore.setdefault("hot_sign_redirect_uri", None)
SqliteConfigurationStore.setdefault("sc2_api_url", "https://api.steemconnect.com/api/")
SqliteConfigurationStore.setdefault("oauth_base_url", "https://api.steemconnect.com/oauth2/")
SqliteConfigurationStore.setdefault("hs_api_url", "https://hivesigner.com/api/")
SqliteConfigurationStore.setdefault("hs_oauth_base_url", "https://hivesigner.com/oauth2/")
SqliteConfigurationStore.setdefault("default_canonical_url", "https://hive.blog")
SqliteConfigurationStore.setdefault("default_path", "48'/13'/0'/0'/0'")


def get_default_config_store(*args, **kwargs):
    return SqliteConfigurationStore(*args, **kwargs)


def get_default_key_store(config, *args, **kwargs):
    return SqliteEncryptedKeyStore(config=config, **kwargs)
