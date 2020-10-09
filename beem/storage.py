# -*- coding: utf-8 -*-
import logging
from .nodelist import NodeList
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())
from beemstorage import (
    SqliteConfigurationStore,
    SqliteEncryptedKeyStore,
)

timeformat = "%Y%m%d-%H%M%S"


def generate_config_store(config, blockchain="hive"):
    #: Default configuration
    nodelist = NodeList()
    if blockchain == "hive":
        nodes = nodelist.get_hive_nodes(testnet=False)
    elif blockchain == "steem":
        nodes = nodelist.get_steem_nodes(testnet=False)
    else:
        nodes = []
    
    config.setdefault("node", nodes)
    config.setdefault("default_chain", blockchain)
    config.setdefault("password_storage", "environment")
    config.setdefault("rpcpassword", "")
    config.setdefault("rpcuser", "")
    config.setdefault("order-expiration", 7 * 24 * 60 * 60)
    config.setdefault("client_id", "")
    config.setdefault("sc2_client_id", None)
    config.setdefault("hs_client_id", None)
    config.setdefault("hot_sign_redirect_uri", None)
    config.setdefault("sc2_api_url", "https://api.steemconnect.com/api/")
    config.setdefault("oauth_base_url", "https://api.steemconnect.com/oauth2/")
    config.setdefault("hs_api_url", "https://hivesigner.com/api/")
    config.setdefault("hs_oauth_base_url", "https://hivesigner.com/oauth2/")
    config.setdefault("default_canonical_url", "https://hive.blog")
    config.setdefault("default_path", "48'/13'/0'/0'/0'")
    config.setdefault("use_condenser", True)
    return config

def get_default_config_store(*args, **kwargs):
    return generate_config_store(SqliteConfigurationStore, blockchain="hive")(*args, **kwargs)


def get_default_key_store(config, *args, **kwargs):
    return SqliteEncryptedKeyStore(config=config, **kwargs)
