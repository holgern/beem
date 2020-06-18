# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes, int, str
import os
import ast
import json
import sys
from prettytable import PrettyTable
from datetime import datetime, timedelta
import calendar
import pytz
import secrets
import string
import time
import hashlib
import math
import random
import logging
import click
from click_shell import shell
import yaml
import re
from beem.instance import set_shared_blockchain_instance, shared_blockchain_instance
from beem.amount import Amount
from beem.price import Price
from beem.account import Account
from beem.steem import Steem
from beem.hive import Hive
from beem.comment import Comment
from beem.message import Message
from beem.market import Market
from beem.block import Block
from beem.profile import Profile
from beem.wallet import Wallet
from beem.steemconnect import SteemConnect
from beem.hivesigner import HiveSigner
from beem.memo import Memo
from beem.asset import Asset
from beem.witness import Witness, WitnessesRankedByVote, WitnessesVotedByAccount
from beem.blockchain import Blockchain
from beem.utils import formatTimeString, construct_authorperm, derive_beneficiaries, derive_tags, seperate_yaml_dict_from_body, derive_permlink
from beem.vote import AccountVotes, ActiveVotes, Vote
from beem import exceptions
from beem.version import version as __version__
from beem.asciichart import AsciiChart
from beem.transactionbuilder import TransactionBuilder
from timeit import default_timer as timer
from beembase import operations
from beemgraphenebase.account import PrivateKey, PublicKey, BrainKey, PasswordKey, MnemonicKey, Mnemonic
from beemgraphenebase.base58 import Base58
from beem.nodelist import NodeList, node_answer_time
from beem.conveyor import Conveyor
from beem.imageuploader import ImageUploader
from beem.rc import RC
from beem.blockchaininstance import BlockChainInstance

click.disable_unicode_literals_warning = True
log = logging.getLogger(__name__)
try:
    import keyring
    if not isinstance(keyring.get_keyring(), keyring.backends.fail.Keyring):
        KEYRING_AVAILABLE = True
    else:
        KEYRING_AVAILABLE = False
except ImportError:
    KEYRING_AVAILABLE = False


availableConfigurationKeys = [
    "default_account",
    "default_vote_weight",
    "nodes",
    "password_storage",
    "client_id",
    "default_canonical_url",
    "default_path"
]


def prompt_callback(ctx, param, value):
    if value in ["yes", "y", "ye"]:
        value = True
    else:
        print("Please write yes, ye or y to confirm!")
        ctx.abort()


def asset_callback(ctx, param, value):
    if value not in ["STEEM", "SBD", "HIVE", "HBD"]:
        print("Please STEEM/HIVE or SBD/HBD as asset!")
        ctx.abort()
    else:
        return value


def prompt_flag_callback(ctx, param, value):
    if not value:
        ctx.abort()


def unlock_wallet(stm, password=None, allow_wif=True):
    if stm.unsigned and stm.nobroadcast:
        return True
    if stm.use_ledger:
        return True
    if not stm.wallet.locked():
        return True
    if not stm.wallet.store.is_encrypted():
        return True
    password_storage = stm.config["password_storage"]
    if not password and KEYRING_AVAILABLE and password_storage == "keyring":
        password = keyring.get_password("beem", "wallet")
    if not password and password_storage == "environment" and "UNLOCK" in os.environ:
        password = os.environ.get("UNLOCK")
    if bool(password):
        stm.wallet.unlock(password)
    else:
        if allow_wif:
            password = click.prompt("Password to unlock wallet or posting/active wif", confirmation_prompt=False, hide_input=True)
        else:
            password = click.prompt("Password to unlock wallet", confirmation_prompt=False, hide_input=True)
        try:
            stm.wallet.unlock(password)
        except:
            try:
                stm.wallet.setKeys([password])
                print("Wif accepted!")
                return True                
            except:
                if allow_wif:
                    raise exceptions.WrongMasterPasswordException("entered password is not a valid password/wif")
                else:
                    raise exceptions.WrongMasterPasswordException("entered password is not a valid password")

    if stm.wallet.locked():
        if password_storage == "keyring" or password_storage == "environment":
            print("Wallet could not be unlocked with %s!" % password_storage)
            password = click.prompt("Password to unlock wallet", confirmation_prompt=False, hide_input=True)
            if bool(password):
                unlock_wallet(stm, password=password)
                if not stm.wallet.locked():
                    return True
        else:
            print("Wallet could not be unlocked!")
        return False
    else:
        print("Wallet Unlocked!")
        return True


def unlock_token_wallet(stm, sc2, password=None):
    if stm.unsigned and stm.nobroadcast:
        return True
    if stm.use_ledger:
        return True
    if not sc2.locked():
        return True
    if not sc2.store.is_encrypted():
        return True
    password_storage = stm.config["password_storage"]
    if not password and KEYRING_AVAILABLE and password_storage == "keyring":
        password = keyring.get_password("beem", "wallet")
    if not password and password_storage == "environment" and "UNLOCK" in os.environ:
        password = os.environ.get("UNLOCK")
    if bool(password):
        sc2.unlock(password)
    else:
        password = click.prompt("Password to unlock wallet", confirmation_prompt=False, hide_input=True)
        try:
            sc2.unlock(password)
        except:
            raise exceptions.WrongMasterPasswordException("entered password is not a valid password")

    if sc2.locked():
        if password_storage == "keyring" or password_storage == "environment":
            print("Wallet could not be unlocked with %s!" % password_storage)
            password = click.prompt("Password to unlock wallet", confirmation_prompt=False, hide_input=True)
            if bool(password):
                unlock_token_wallet(stm, password=password)
                if not sc2.locked():
                    return True
        else:
            print("Wallet could not be unlocked!")
        return False
    else:
        print("Wallet Unlocked!")
        return True


@shell(prompt='beempy> ', intro='Starting beempy... (use help to list all commands)', chain=True)
# @click.group(chain=True)
@click.option(
    '--node', '-n', default="", help="URL for public Steem API (e.g. https://api.steemit.com)")
@click.option(
    '--offline', '-o', is_flag=True, default=False, help="Prevent connecting to network")
@click.option(
    '--no-broadcast', '-d', is_flag=True, default=False, help="Do not broadcast")
@click.option(
    '--no-wallet', '-p', is_flag=True, default=False, help="Do not load the wallet")
@click.option(
    '--unsigned', '-x', is_flag=True, default=False, help="Nothing will be signed")
@click.option(
    '--create-link', '-l', is_flag=True, default=False, help="Creates steemconnect/hivesigner links from all broadcast operations")
@click.option(
    '--steem', '-s', is_flag=True, default=False, help="Connect to the Steem blockchain")
@click.option(
    '--hive', '-h', is_flag=True, default=False, help="Connect to the Hive blockchain")
@click.option(
    '--keys', '-k', help="JSON file that contains account keys, when set, the wallet cannot be used.")
@click.option(
    '--use-ledger', '-u', is_flag=True, default=False, help="Uses the ledger device Nano S for signing.")
@click.option(
    '--path', help="BIP32 path from which the keys are derived, when not set, default_path is used.")
@click.option(
    '--token', '-t', is_flag=True, default=False, help="Uses a hivesigner/steemconnect token to broadcast (only broadcast operation with posting permission)")
@click.option(
    '--expires', '-e', default=30,
    help='Delay in seconds until transactions are supposed to expire(defaults to 60)')
@click.option(
    '--verbose', '-v', default=3, help='Verbosity')
@click.version_option(version=__version__)
def cli(node, offline, no_broadcast, no_wallet, unsigned, create_link, steem, hive, keys, use_ledger, path, token, expires, verbose):

    # Logging
    log = logging.getLogger(__name__)
    verbosity = ["critical", "error", "warn", "info", "debug"][int(
        min(verbose, 4))]
    log.setLevel(getattr(logging, verbosity.upper()))
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, verbosity.upper()))
    ch.setFormatter(formatter)
    log.addHandler(ch)

    keys_list = []
    autoconnect = False
    if keys and keys != "":
        if not os.path.isfile(keys):
            raise Exception("File %s does not exist!" % keys)
        with open(keys) as fp:
            keyfile = fp.read()
        if keyfile.find('\0') > 0:
            with open(keys, encoding='utf-16') as fp:
                keyfile = fp.read()
        keyfile = ast.literal_eval(keyfile)
        for account in keyfile:
            for role in ["owner", "active", "posting", "memo"]:
                if role in keyfile[account]:
                    keys_list.append(keyfile[account][role])
    if len(keys_list) > 0:
        autoconnect = True
    if create_link:
        no_broadcast = True
        unsigned = True
        if hive:
            sc2 = HiveSigner()
        else:
            sc2 = SteemConnect()
    else:
        sc2 = None
    debug = verbose > 0
    if hive:
        stm = Hive(
            node=node,
            nobroadcast=no_broadcast,
            keys=keys_list,
            offline=offline,
            nowallet=no_wallet,
            unsigned=unsigned,
            use_hs=token,
            expiration=expires,
            hivesigner=sc2,
            use_ledger=use_ledger,
            path=path,
            debug=debug,
            num_retries=10,
            num_retries_call=3,
            timeout=15,
            autoconnect=autoconnect
        )
    else:
        stm = Steem(
            node=node,
            nobroadcast=no_broadcast,
            offline=offline,
            keys=keys_list,
            nowallet=no_wallet,
            unsigned=unsigned,
            use_sc2=token,
            expiration=expires,
            steemconnect=sc2,
            use_ledger=use_ledger,
            path=path,
            debug=debug,
            num_retries=10,
            num_retries_call=3,
            timeout=15,
            autoconnect=autoconnect
        )
            
    set_shared_blockchain_instance(stm)

    pass


@cli.command()
@click.argument('key')
@click.argument('value')
def set(key, value):
    """ Set default_account, default_vote_weight or nodes

        set [key] [value]

        Examples:

        Set the default vote weight to 50 %:
        set default_vote_weight 50
    """
    stm = shared_blockchain_instance()
    if key == "default_account":
        if stm.rpc is not None:
            stm.rpc.rpcconnect()
        stm.set_default_account(value)
    elif key == "default_vote_weight":
        stm.set_default_vote_weight(value)
    elif key == "nodes" or key == "node":
        if bool(value) or value != "default":
            stm.set_default_nodes(value)
        else:
            stm.set_default_nodes("")
    elif key == "default_chain":
        stm.config["default_chain"] = value
    elif key == "password_storage":
        stm.config["password_storage"] = value
        if KEYRING_AVAILABLE and value == "keyring":
            password = click.prompt("Password to unlock wallet (Will be stored in keyring)", confirmation_prompt=False, hide_input=True)
            password = keyring.set_password("beem", "wallet", password)
        elif KEYRING_AVAILABLE and value != "keyring":
            try:
                keyring.delete_password("beem", "wallet")
            except keyring.errors.PasswordDeleteError:
                print("")
        if value == "environment":
            print("The wallet password can be stored in the UNLOCK environment variable to skip password prompt!")
    elif key == "client_id":
        stm.config["client_id"] = value
    elif key == "hot_sign_redirect_uri":
        stm.config["hot_sign_redirect_uri"] = value
    elif key == "sc2_api_url":
        stm.config["sc2_api_url"] = value
    elif key == "hs_api_url":
        stm.config["hs_api_url"] = value
    elif key == "oauth_base_url":
        stm.config["oauth_base_url"] = value
    elif key == "default_path":
        stm.config["default_path"] = value
    elif key == "default_canonical_url":
        stm.config["default_canonical_url"] = value
    else:
        print("wrong key")


@cli.command()
@click.option('--results', is_flag=True, default=False, help="Shows result of changing the node.")
def nextnode(results):
    """ Uses the next node in list
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    stm.move_current_node_to_front()
    node = stm.get_default_nodes()
    offline = stm.offline
    if len(node) < 2:
        print("At least two nodes are needed!")
        return
    node = node[1:] + [node[0]]
    if not offline:
        stm.rpc.next()
        stm.get_blockchain_version()
    while not offline and node[0] != stm.rpc.url and len(node) > 1:
        node = node[1:] + [node[0]]
    stm.set_default_nodes(node)
    if not results:
        return

    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    if not offline:
        t.add_row(["Node-Url", stm.rpc.url])
    else:
        t.add_row(["Node-Url", node[0]])
    if not offline:
        t.add_row(["Version", stm.get_blockchain_version()])
        t.add_row(["HIVE", stm.is_hive])
    else:
        t.add_row(["Version", "beempy is in offline mode..."])
    print(t)


@cli.command()
@click.option(
    '--sort', '-s', is_flag=True, default=False,
    help="Sort all nodes by ping value")
@click.option(
    '--remove', '-r', is_flag=True, default=False,
    help="Remove node with errors from list")
def pingnode(sort, remove):
    """ Returns the answer time in milliseconds
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    nodes = stm.get_default_nodes()
    
    t = PrettyTable(["Node", "Answer time [ms]"])
    t.align = "l"
    if sort:
        sorted_node_list = []
        nodelist = NodeList()
        sorted_nodes = nodelist.get_node_answer_time(nodes)
        for node in sorted_nodes:
            t.add_row([node["url"], "%.2f" % (node["delay_ms"])])
            sorted_node_list.append(node["url"])
        print(t)
        stm.set_default_nodes(sorted_node_list)
    else:
        node = stm.rpc.url
        rpc_answer_time = node_answer_time(node)
        rpc_time_str = "%.2f" % (rpc_answer_time * 1000)
        t.add_row([node, rpc_time_str])
        print(t)


@cli.command()
def about():
    """ About beempy"""
    print("")
    print("beempy version: %s" % __version__)
    print("")
    print("By @holger80")
    print("")


@cli.command()
@click.option(
    '--version', is_flag=True, default=False,
    help="Returns only the raw version value")
@click.option(
    '--url', is_flag=True, default=False,
    help="Returns only the raw url value")
def currentnode(version, url):
    """ Sets the currently working node at the first place in the list
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    offline = stm.offline
    stm.move_current_node_to_front()
    node = stm.get_default_nodes()
    if version and not offline:
        print(stm.get_blockchain_version())
        return
    elif version and offline:
        print("Node is offline")
        return
    if url and not offline:
        print(stm.rpc.url)
        return
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    if not offline:
        t.add_row(["Node-Url", stm.rpc.url])
    else:
        t.add_row(["Node-Url", node[0]])
    if not offline:
        t.add_row(["Version", stm.get_blockchain_version()])
        t.add_row(["Chain", stm.get_blockchain_name()])
    else:
        t.add_row(["Version", "steempy is in offline mode..."])
    print(t)


@cli.command()
@click.option(
    '--show', '-s', is_flag=True, default=False,
    help="Prints the updated nodes")
@click.option(
    '--hive', '-h', is_flag=True, default=False,
    help="Switch to HIVE blockchain, when set to true.")
@click.option(
    '--steem', '-e', is_flag=True, default=False,
    help="Switch to STEEM nodes, when set to true.")
@click.option(
    '--test', '-t', is_flag=True, default=False,
    help="Do change the node list, only print the newest nodes setup.")
@click.option(
    '--only-https', is_flag=True, default=False,
    help="Use only https nodes.")
@click.option(
    '--only-wss', is_flag=True, default=False,
    help="Use only websocket nodes.")
def updatenodes(show, hive, steem, test, only_https, only_wss):
    """ Update the nodelist from @fullnodeupdate
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if steem and hive:
        print("hive and steem cannot be active both")
        return
    t = PrettyTable(["node", "Version", "score"])
    t.align = "l"
    if steem:
        blockchain = "steem"
    elif hive:
        blockchain = "hive"
    else:
        blockchain = stm.config["default_chain"]
    nodelist = NodeList()
    nodelist.update_nodes(blockchain_instance=stm)
    if hive:
        nodes = nodelist.get_hive_nodes(wss=not only_https, https=not only_wss)
        if stm.config["default_chain"] == "steem":
            stm.config["default_chain"] = "hive"
    elif steem:
        nodes = nodelist.get_steem_nodes(wss=not only_https, https=not only_wss)
        if stm.config["default_chain"] == "hive":
            stm.config["default_chain"] = "steem"    
    elif stm.config["default_chain"] == "steem":
        nodes = nodelist.get_steem_nodes(wss=not only_https, https=not only_wss)
    else:
        nodes = nodelist.get_hive_nodes(wss=not only_https, https=not only_wss)
    if show or test:
        sorted_nodes = sorted(nodelist, key=lambda node: node["score"], reverse=True)
        for node in sorted_nodes:
            if node["url"] in nodes:
                score = float("{0:.1f}".format(node["score"]))
                t.add_row([node["url"], node["version"], score])
        print(t)
    if not test:
        stm.set_default_nodes(nodes)
        stm.rpc.nodes.set_node_urls(nodes)
        stm.rpc.current_rpc = 0
        stm.rpc.rpcclose()
        stm.rpc.rpcconnect()


@cli.command()
def config():
    """ Shows local configuration
    """
    stm = shared_blockchain_instance()
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    for key in stm.config:
        # hide internal config data
        if key in availableConfigurationKeys and key != "nodes" and key != "node":
            t.add_row([key, stm.config[key]])
    node = stm.get_default_nodes()
    blockchain = stm.config["default_chain"]
    nodes = json.dumps(node, indent=4)
    t.add_row(["default_chain", blockchain])
    t.add_row(["nodes", nodes])
    if "password_storage" not in availableConfigurationKeys:
        t.add_row(["password_storage", stm.config["password_storage"]])
    t.add_row(["data_dir", stm.config.data_dir])
    print(t)


@cli.command()
@click.option('--wipe', is_flag=True, default=False,
              help="Wipe old wallet without prompt.")
def createwallet(wipe):
    """ Create new wallet with a new password
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if stm.wallet.created() and not wipe:
        wipe_answer = click.prompt("'Do you want to wipe your wallet? Are your sure? This is IRREVERSIBLE! If you dont have a backup you may lose access to your account! [y/n]",
                                   default="n")
        if wipe_answer in ["y", "ye", "yes"]:
            stm.wallet.wipe(True)
        else:
            return
    elif wipe:
        stm.wallet.wipe(True)
    password = None
    password = click.prompt("New wallet password", confirmation_prompt=True, hide_input=True)
    if not bool(password):
        print("Password cannot be empty! Quitting...")
        return
    password_storage = stm.config["password_storage"]
    if KEYRING_AVAILABLE and password_storage == "keyring":
        password = keyring.set_password("beem", "wallet", password)
    elif password_storage == "environment":
        print("The new wallet password can be stored in the UNLOCK environment variable to skip password prompt!")
    stm.wallet.wipe(True)
    stm.wallet.create(password)
    set_shared_blockchain_instance(stm)


@cli.command()
@click.option('--unlock', '-u', is_flag=True, default=False, help='Unlock wallet')
@click.option('--lock', '-l', is_flag=True, default=False, help='Lock wallet')
def walletinfo(unlock, lock):
    """ Show info about wallet
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if lock:
        stm.wallet.lock()
    elif unlock:
        unlock_wallet(stm, allow_wif=False)
      
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    t.add_row(["created", stm.wallet.created()])
    t.add_row(["locked", stm.wallet.locked()])
    t.add_row(["Number of stored keys", len(stm.wallet.getPublicKeys())])
    t.add_row(["sql-file", stm.wallet.store.sqlite_file])
    password_storage = stm.config["password_storage"]
    t.add_row(["password_storage", password_storage])
    password = os.environ.get("UNLOCK")
    if password is not None:
        t.add_row(["UNLOCK env set", "yes"])
    else:
        t.add_row(["UNLOCK env set", "no"])
    if KEYRING_AVAILABLE:
        t.add_row(["keyring installed", "yes"])
    else:
        t.add_row(["keyring installed", "no"])

    if unlock:
        if unlock_wallet(stm, allow_wif=False):
            t.add_row(["Wallet unlock", "successful"])
        else:
            t.add_row(["Wallet unlock", "not working"])
    # t.add_row(["getPublicKeys", str(stm.wallet.getPublicKeys())])
    print(t)


@cli.command()
@click.option('--unsafe-import-key',
              help='WIF key to parse (unsafe, unless shell history is deleted afterwards)', multiple=True)
def parsewif(unsafe_import_key):
    """ Parse a WIF private key without importing
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if unsafe_import_key:
        for key in unsafe_import_key:
            try:
                pubkey = PrivateKey(key, prefix=stm.prefix).pubkey
                print(pubkey)
                account = stm.wallet.getAccountFromPublicKey(str(pubkey))
                account = Account(account, blockchain_instance=stm)
                key_type = stm.wallet.getKeyType(account, str(pubkey))
                print("Account: %s - %s" % (account["name"], key_type))
            except Exception as e:
                print(str(e))
    else:
        while True:
            wifkey = click.prompt("Enter private key", confirmation_prompt=False, hide_input=True)
            if not wifkey or wifkey == "quit" or wifkey == "exit":
                break
            try:
                pubkey = PrivateKey(wifkey, prefix=stm.prefix).pubkey
                print(pubkey)
                account = stm.wallet.getAccountFromPublicKey(str(pubkey))
                account = Account(account, blockchain_instance=stm)
                key_type = stm.wallet.getKeyType(account, str(pubkey))
                print("Account: %s - %s" % (account["name"], key_type))
            except Exception as e:
                print(str(e))
                continue


@cli.command()
@click.option('--unsafe-import-key',
              help='Private key to import to wallet (unsafe, unless shell history is deleted afterwards)')
def addkey(unsafe_import_key):
    """ Add key to wallet

        When no [OPTION] is given, a password prompt for unlocking the wallet
        and a prompt for entering the private key are shown.
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not unlock_wallet(stm, allow_wif=False):
        return
    if not unsafe_import_key:
        unsafe_import_key = click.prompt("Enter private key", confirmation_prompt=False, hide_input=True)
    stm.wallet.addPrivateKey(unsafe_import_key)
    set_shared_blockchain_instance(stm)


@cli.command()
@click.option('--confirm',
              prompt='Are your sure? This is IRREVERSIBLE! If you dont have a backup you may lose access to your account!',
              hide_input=False, callback=prompt_flag_callback, is_flag=True,
              confirmation_prompt=False, help='Please confirm!')
@click.argument('pub')
def delkey(confirm, pub):
    """ Delete key from the wallet

        PUB is the public key from the private key
        which will be deleted from the wallet
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not unlock_wallet(stm, allow_wif=False):
        return
    stm.wallet.removePrivateKeyFromPublicKey(pub)
    set_shared_blockchain_instance(stm)


@cli.command()
@click.option('--import-word-list', '-l', help='Imports a BIP39 wordlist and derives a private and public key', is_flag=True, default=False)
@click.option('--strength', help='Defines word list length for BIP39 (default = 256).', default=256)
@click.option('--passphrase', '-p', help='Sets a BIP39 passphrase', is_flag=True, default=False)
@click.option('--path', '-m', help='Sets a path for BIP39 key creations. When path is set, network, role, account_keys, account and sequence is not used')
@click.option('--network', '-n', help='Network index, when using BIP39, 0 for steem and 13 for hive, (default is 13)', default=13)
@click.option('--role', '-r', help='Defines the key role for BIP39 when a single key is generated (default = owner).', default="owner")
@click.option('--account-keys', '-k', help='Derives four BIP39 keys for each role', is_flag=True, default=False)
@click.option('--sequence', '-s', help='Sequence key number, when using BIP39 (default is 0)', default=0)
@click.option('--account', '-a', help='account name for password based key generation or sequence number for BIP39 key, default = 0')
@click.option('--import-password', '-i', help='Imports a password and derives all four account keys', is_flag=True, default=False)
@click.option('--create-password', '-c', help='Creates a new password and derives four account keys from it', is_flag=True, default=False)
@click.option('--wif', '-w', help='Defines how many times the password is replaced by its WIF representation for password based keys (default = 0).', default=0)
@click.option('--export-pub', '-u', help='Exports the public account keys to a json file for account creation or keychange')
@click.option('--export', '-e', help='The results are stored in a text file and will not be shown')
def keygen(import_word_list, strength, passphrase, path, network, role, account_keys, sequence, account, import_password, create_password, wif, export_pub, export):
    """ Creates a new random BIP39 key or password based key and prints its derived private key and public key.
        The generated key is not stored. Can also be used to create new keys for an account.
        Can also be used to derive account keys from a password or BIP39 wordlist
    """
    stm = shared_blockchain_instance()
    if not account and import_password or create_password:
        account = stm.config["default_account"]
    if import_password:
        import_password = click.prompt("Enter password", confirmation_prompt=False, hide_input=True)
    elif create_password:
        alphabet = string.ascii_letters + string.digits
        while True:
            import_password = ''.join(secrets.choice(alphabet) for i in range(32))
            if (any(c.islower() for c in import_password) and any(c.isupper() for c in import_password) and any(c.isdigit() for c in import_password)):
                break
    pub_json = {"owner": "", "active": "", "posting": "", "memo": ""}
    
    if not account_keys and len(role.split(",")) > 1:
        roles = role.split(",")
        account_keys = True
    else:
        roles = ['owner', 'active', 'posting', 'memo']    
    
    if import_password or create_password:
        if wif > 0:
            password = import_password
            for _ in range(wif):
                pk = PasswordKey("", password, role="")
                password = str(pk.get_private())
            password = 'P' + password
        else:
            password = import_password
        t = PrettyTable(["Key", "Value"])
        t_pub = PrettyTable(["Key", "Value"])
        t.add_row(["Username", account])
        t_pub.add_row(["Username", account])
        t.align = "l"
        t_pub.align = "l"
        for r in roles:
            pk = PasswordKey(account, password, role=r)
            t.add_row(["%s Private Key" % r, str(pk.get_private())])
            t_pub.add_row(["%s Public Key" % r, format(pk.get_public(), "STM")])
            pub_json[r] = format(pk.get_public(), "STM")
        t.add_row(["Backup (Master) Password", password])
        if wif > 0:
            t.add_row(["WIF itersions", wif])
            t.add_row(["Entered/created Password", import_password])
    elif stm.use_ledger:
        if stm.rpc is not None:
            stm.rpc.rpcconnect()        
        ledgertx = stm.new_tx()
        ledgertx.constructTx()
        if account is None:
            account = 0
        else:
            account = int(account)
        t = PrettyTable(["Key", "Value"])
        t_pub = PrettyTable(["Key", "Value"])
        t.align = "l"
        t_pub.align = "l"
        t.add_row(["Account sequence", account])
        t.add_row(["Key sequence", sequence])

        
        if account_keys and path is None:  
            for r in roles:
                path = ledgertx.ledgertx.build_path(r, account, sequence)
                pubkey = ledgertx.ledgertx.get_pubkey(path, request_screen_approval=False)
                aprove_key = PrettyTable(["Approve %s Key" % r])
                aprove_key.align = "l"
                aprove_key.add_row([format(pubkey, "STM")])
                print(aprove_key)
                ledgertx.ledgertx.get_pubkey(path, request_screen_approval=True)
                t_pub.add_row(["%s Public Key" % r, format(pubkey, "STM")])
                t.add_row(["%s path" % r, path])               
                pub_json[r] = format(pubkey, "STM")          
        else:
            if path is None:
                path = ledgertx.ledgertx.build_path(role, account, sequence)            
            t.add_row(["Key role", role])
            t.add_row(["path", path])
            pubkey = ledgertx.ledgertx.get_pubkey(path, request_screen_approval=False)
            aprove_key = PrettyTable(["Approve %s Key" % role])
            aprove_key.align = "l"
            aprove_key.add_row([format(pubkey, "STM")])
            print(aprove_key)
            ledgertx.ledgertx.get_pubkey(path, request_screen_approval=True)
            t_pub.add_row(["Public Key", format(pubkey, "STM")])
            pub_json[role] = format(pubkey, "STM")        
    else:
        if account is None:
            account = 0
        else:
            account = int(account)
        if import_word_list:
            n_words = click.prompt("Enter word list length or complete word list")
            if len(n_words.split(" ")) > 0:
                word_list = n_words
            else:
                n_words = int(n_words)
                word_array = []
                word = None
                m = Mnemonic()
                while len(word_array) < n_words:
                    word = click.prompt("Enter %d. mnemnoric word" % (len(word_array) + 1), type=str)
                    word = m.expand_word(word)
                    if m.check_word(word):
                        word_array.append(word)
                    print(" ".join(word_array))
                word_list = " ".join(word_array)
            if passphrase:
                passphrase = import_password = click.prompt("Enter passphrase", confirmation_prompt=True, hide_input=True)
            else:
                passphrase = ""
            mk = MnemonicKey(word_list=word_list, passphrase=passphrase, account_sequence=account, key_sequence=sequence)
            if path is not None:
                mk.set_path(path)
            else:
                mk.set_path_BIP48(network_index=network, role=role, account_sequence=account, key_sequence=sequence)
        else:
            mk = MnemonicKey(account_sequence=account, key_sequence=sequence)
            if path is not None:
                mk.set_path(path)
            else:
                mk.set_path_BIP48(network_index=network, role=role, account_sequence=account, key_sequence=sequence)
            if passphrase:
                passphrase = import_password = click.prompt("Enter passphrase", confirmation_prompt=True, hide_input=True)
            else:
                passphrase = ""
            word_list = mk.generate_mnemonic(passphrase=passphrase, strength=strength)
        t = PrettyTable(["Key", "Value"])
        t_pub = PrettyTable(["Key", "Value"])
        t.align = "l"
        t_pub.align = "l"
        t.add_row(["Account sequence", account])
        t.add_row(["Key sequence", sequence])   
        if account_keys and path is None:  
            for r in roles:
                t.add_row(["%s Private Key" % r, str(mk.get_private())])
                mk.set_path_BIP48(network_index=network, role=r, account_sequence=account, key_sequence=sequence)
                t_pub.add_row(["%s Public Key" % r, format(mk.get_public(), "STM")])
                t.add_row(["%s path" % r, mk.get_path()])               
                pub_json[r] = format(mk.get_public(), "STM")
            if passphrase != "":
                t.add_row(["Passphrase", passphrase])                
            t.add_row(["BIP39 wordlist", word_list])
        else:
            t.add_row(["Key role", role])
            t.add_row(["path", mk.get_path()])
            t.add_row(["BIP39 wordlist", word_list.lower()])
            if passphrase != "":
                t.add_row(["Passphrase", passphrase])                 
            t.add_row(["Private Key", str(mk.get_private())])
            t_pub.add_row(["Public Key", format(mk.get_public(), "STM")])
            pub_json[role] = format(mk.get_public(), "STM")
    if export_pub and export_pub != "":
        pub_json = json.dumps(pub_json, indent=4)
        with open(export_pub, 'w') as fp:
            fp.write(pub_json)
        print("%s was sucessfully saved." % export_pub)
    if export and export != "":
        with open(export, 'w') as fp:
            fp.write(str(t))
            fp.write(str(t_pub))
        print("%s was sucessfully saved." % export)
    else:
        print(t_pub)
        print(t)


@cli.command()
@click.argument('name')
@click.option('--unsafe-import-token',
              help='Private key to import to wallet (unsafe, unless shell history is deleted afterwards)')
def addtoken(name, unsafe_import_token):
    """ Add key to wallet

        When no [OPTION] is given, a password prompt for unlocking the wallet
        and a prompt for entering the private key are shown.
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    sc2 = SteemConnect(blockchain_instance=stm)
    if not unlock_token_wallet(stm, sc2):
        return    
    if not unsafe_import_token:
        unsafe_import_token = click.prompt("Enter private token", confirmation_prompt=False, hide_input=True)
    sc2.addToken(name, unsafe_import_token)
    set_shared_blockchain_instance(stm)


@cli.command()
@click.option('--confirm',
              prompt='Are your sure?',
              hide_input=False, callback=prompt_flag_callback, is_flag=True,
              confirmation_prompt=False, help='Please confirm!')
@click.argument('name')
def deltoken(confirm, name):
    """ Delete name from the wallet

        name is the public name from the private token
        which will be deleted from the wallet
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    sc2 = SteemConnect(blockchain_instance=stm)
    if not unlock_token_wallet(stm, sc2):
        return    
    sc2.removeTokenFromPublicName(name)
    set_shared_blockchain_instance(stm)


@cli.command()
@click.option('--path', '-p', help='Set path (when using ledger)')
@click.option('--ledger-approval', '-a', is_flag=True, default=False, help='When set, you can confirm the shown pubkey on your ledger.')
def listkeys(path, ledger_approval):
    """ Show stored keys
    
    Can be used to receive and approve the pubkey obtained from the ledger
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()

    if stm.use_ledger:
        if path is None:
            path = stm.config["default_path"]
        t = PrettyTable(["Available Key for %s" % path])
        t.align = "l"        
        ledgertx = stm.new_tx()
        ledgertx.constructTx()
        pubkey = ledgertx.ledgertx.get_pubkey(path, request_screen_approval=False)
        t.add_row([str(pubkey)])
        if ledger_approval:
            print(t)
            ledgertx.ledgertx.get_pubkey(path, request_screen_approval=True)
    else:
        t = PrettyTable(["Available Key"])
        t.align = "l"        
        for key in stm.wallet.getPublicKeys():
            t.add_row([key])
    print(t)

@cli.command()
def listtoken():
    """ Show stored token
    """
    stm = shared_blockchain_instance()
    t = PrettyTable(["name", "scope", "status"])
    t.align = "l"
    sc2 = SteemConnect(blockchain_instance=stm)
    if not unlock_token_wallet(stm, sc2):
        return    
    for name in sc2.getPublicNames():
        ret = sc2.me(username=name)
        if "error" in ret:
            t.add_row([name, "-", ret["error"]])
        else:
            t.add_row([name, ret["scope"], "ok"])
    print(t)


@cli.command()
@click.option('--role', '-r', help='When set, limits the shown keys for this role')
@click.option('--max-account-index', '-a', help='Set maximum account index to check pubkeys (only when using ledger)', default=5)
@click.option('--max-sequence', '-s', help='Set maximum key sequence to check pubkeys (only when using ledger)', default=2)
def listaccounts(role, max_account_index, max_sequence):
    """Show stored accounts
    
    Can be used with the ledger to obtain all accounts that uses pubkeys derived from this ledger
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()

    if stm.use_ledger:
        t = PrettyTable(["Name", "Type", "Available Key", "Path"])
        t.align = "l"        
        ledgertx = stm.new_tx()
        ledgertx.constructTx()
        key_found = False
        path = None
        current_account_index = 0
        current_key_index = 0
        role_list = ["owner", "active", "posting", "memo"]
        if role:
            role_list = [role]
        while not key_found and current_account_index < max_account_index:
            for perm in role_list:
                path = ledgertx.ledgertx.build_path(perm, current_account_index, current_key_index)
                current_pubkey = ledgertx.ledgertx.get_pubkey(path)
                account = stm.wallet.getAccountFromPublicKey(str(current_pubkey))
                if account is not None:
                    t.add_row([str(account), perm, str(current_pubkey), path])
            if current_key_index < max_sequence:
                current_key_index += 1
            else:
                current_key_index = 0
                current_account_index += 1  
    else:
        t = PrettyTable(["Name", "Type", "Available Key"])
        t.align = "l"        
        for account in stm.wallet.getAccounts():
            t.add_row([
                account["name"] or "n/a", account["type"] or "n/a",
                account["pubkey"]
            ])
    print(t)


@cli.command()
@click.argument('post', nargs=1)
@click.option('--weight', '-w', help='Vote weight (from 0.1 to 100.0)')
@click.option('--account', '-a', help='Voter account name')
def upvote(post, account, weight):
    """Upvote a post/comment

        POST is @author/permlink
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not weight:
        weight = stm.config["default_vote_weight"]        
    else:
        weight = float(weight)
        if weight > 100:
            raise ValueError("Maximum vote weight is 100.0!")
        elif weight < 0:
            raise ValueError("Minimum vote weight is 0!")

    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    try:
        post = Comment(post, blockchain_instance=stm)
        tx = post.upvote(weight, voter=account)
        if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
            tx = stm.steemconnect.url_from_tx(tx)
        elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
            tx = stm.hivesigner.url_from_tx(tx)
    except exceptions.VotingInvalidOnArchivedPost:
        print("Post/Comment is older than 7 days! Did not upvote.")
        tx = {}
    tx = json.dumps(tx, indent=4)
    print(tx)

@cli.command()
@click.argument('post', nargs=1)
@click.option('--account', '-a', help='Voter account name')
def delete(post, account):
    """delete a post/comment

        POST is @author/permlink
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()

    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    try:
        post = Comment(post, blockchain_instance=stm)
        tx = post.delete(account=account)
        if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
            tx = stm.steemconnect.url_from_tx(tx)
        elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
            tx = stm.hivesigner.url_from_tx(tx)    
    except exceptions.VotingInvalidOnArchivedPost:
        print("Could not delete post.")
        tx = {}
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('post', nargs=1)
@click.option('--account', '-a', help='Voter account name')
@click.option('--weight', '-w', default=100, help='Downvote weight (from 0.1 to 100.0)')
def downvote(post, account, weight):
    """Downvote a post/comment

        POST is @author/permlink
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()

    weight = float(weight)
    if weight > 100:
        raise ValueError("Maximum downvote weight is 100.0!")
    elif weight < 0:
        raise ValueError("Minimum downvote weight is 0!")
    
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    try:
        post = Comment(post, blockchain_instance=stm)
        tx = post.downvote(weight, voter=account)
        if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
            tx = stm.steemconnect.url_from_tx(tx)
        elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
            tx = stm.hivesigner.url_from_tx(tx)    
    except exceptions.VotingInvalidOnArchivedPost:
        print("Post/Comment is older than 7 days! Did not downvote.")
        tx = {}
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('to', nargs=1)
@click.argument('amount', nargs=1)
@click.argument('asset', nargs=1, callback=asset_callback)
@click.argument('memo', nargs=1, required=False)
@click.option('--account', '-a', help='Transfer from this account')
def transfer(to, amount, asset, memo, account):
    """Transfer SBD/HD STEEM/HIVE"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not bool(memo):
        memo = ''
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    tx = acc.transfer(to, amount, asset, memo)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1)
@click.option('--account', '-a', help='Powerup from this account')
@click.option('--to', help='Powerup this account', default=None)
def powerup(amount, account, to):
    """Power up (vest STEEM/HIVE as STEEM/HIVE POWER)"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    try:
        amount = float(amount)
    except:
        amount = str(amount)
    tx = acc.transfer_to_vesting(amount, to=to)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1)
@click.option('--account', '-a', help='Powerup from this account')
def powerdown(amount, account):
    """Power down (start withdrawing VESTS from Steem POWER)

        amount is in VESTS
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    try:
        amount = float(amount)
    except:
        amount = str(amount)
    tx = acc.withdraw_vesting(amount)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1)
@click.argument('to_account', nargs=1)
@click.option('--account', '-a', help='Delegate from this account')
def delegate(amount, to_account, account):
    """Delegate (start delegating VESTS to another account)

        amount is in VESTS / Steem
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    try:
        amount = float(amount)
    except:
        amount = Amount(str(amount), blockchain_instance=stm)
        if amount.symbol == stm.token_symbol and isinstance(stm, Steem):
            amount = stm.sp_to_vests(float(amount))
        elif amount.symbol == stm.token_symbol and isinstance(stm, Hive):
            amount = stm.hp_to_vests(float(amount))        

    tx = acc.delegate_vesting_shares(to_account, amount)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('to', nargs=1)
@click.option('--percentage', default=100, help='The percent of the withdraw to go to the "to" account')
@click.option('--account', '-a', help='Powerup from this account')
@click.option('--auto_vest', help='Set to true if the from account should receive the VESTS as'
              'VESTS, or false if it should receive them as STEEM/HIVE.', is_flag=True)
def powerdownroute(to, percentage, account, auto_vest):
    """Setup a powerdown route"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    tx = acc.set_withdraw_vesting_route(to, percentage, auto_vest=auto_vest)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)

@cli.command()
@click.argument('new_recovery_account', nargs=1)
@click.option('--account', '-a', help='Change the recovery account from this account')
def changerecovery(new_recovery_account, account):
    """Changes the recovery account with the owner key (needs 30 days to be active)"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    #if not unlock_wallet(stm):
    #    return
    new_recovery_account = Account(new_recovery_account, blockchain_instance=stm)
    account = Account(account, blockchain_instance=stm)
    op = operations.Change_recovery_account(**{
        'account_to_recover': account['name'],
        'new_recovery_account': new_recovery_account['name'],
        'extensions': []
    })

    tb = TransactionBuilder(blockchain_instance=stm)
    tb.appendOps([op])
    if stm.unsigned:
        tb.addSigningInformation(account["name"], "owner")
        tx = tb
    else:
        key = click.prompt('Owner key for %s' % account["name"], confirmation_prompt=False, hide_input=True)
        owner_key = PrivateKey(wif=key)
        tb.appendWif(str(owner_key))
        tb.sign()
        tx = tb.broadcast()
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1)
@click.option('--account', '-a', help='Powerup from this account')
def convert(amount, account):
    """Convert SBD/HBD to Steem/Hive (takes a week to settle)"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    try:
        amount = float(amount)
    except:
        amount = str(amount)
    tx = acc.convert(amount)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
def changewalletpassphrase():
    """ Change wallet password
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()    
    if not unlock_wallet(stm, allow_wif=False):
        return
    newpassword = None
    newpassword = click.prompt("New wallet password", confirmation_prompt=True, hide_input=True)
    if not bool(newpassword):
        print("Password cannot be empty! Quitting...")
        return
    password_storage = stm.config["password_storage"]
    if KEYRING_AVAILABLE and password_storage == "keyring":
        keyring.set_password("beem", "wallet", newpassword)
    elif password_storage == "environment":
        print("The new wallet password can be stored in the UNLOCK invironment variable to skip password prompt!")
    stm.wallet.changePassphrase(newpassword)


@cli.command()
@click.argument('account', nargs=-1)
def power(account):
    """ Shows vote power and bandwidth
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if len(account) == 0:
        if "default_account" in stm.config:
            account = [stm.config["default_account"]]
    for name in account:
        a = Account(name, blockchain_instance=stm)
        print("\n@%s" % a.name)
        a.print_info(use_table=True)


@cli.command()
@click.argument('account', nargs=-1)
def balance(account):
    """ Shows balance
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if len(account) == 0:
        if "default_account" in stm.config:
            account = [stm.config["default_account"]]
    for name in account:
        a = Account(name, blockchain_instance=stm)
        print("\n@%s" % a.name)
        t = PrettyTable(["Account", stm.token_symbol, stm.backed_token_symbol, "VESTS"])
        t.align = "r"
        t.add_row([
            'Available',
            str(a.balances['available'][0]),
            str(a.balances['available'][1]),
            str(a.balances['available'][2]),
        ])
        t.add_row([
            'Rewards',
            str(a.balances['rewards'][0]),
            str(a.balances['rewards'][1]),
            str(a.balances['rewards'][2]),
        ])
        t.add_row([
            'Savings',
            str(a.balances['savings'][0]),
            str(a.balances['savings'][1]),
            'N/A',
        ])
        t.add_row([
            'TOTAL',
            str(a.balances['total'][0]),
            str(a.balances['total'][1]),
            str(a.balances['total'][2]),
        ])
        print(t)


@cli.command()
@click.argument('account', nargs=-1, required=False)
def interest(account):
    """ Get information about interest payment
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        if "default_account" in stm.config:
            account = [stm.config["default_account"]]

    t = PrettyTable([
        "Account", "Last Interest Payment", "Next Payment",
        "Interest rate", "Interest"
    ])
    t.align = "r"
    for a in account:
        a = Account(a, blockchain_instance=stm)
        i = a.interest()
        t.add_row([
            a["name"],
            i["last_payment"],
            "in %s" % (i["next_payment_duration"]),
            "%.1f%%" % i["interest_rate"],
            "%.3f %s" % (i["interest"], stm.backed_token_symbol),
        ])
    print(t)


@cli.command()
@click.argument('account', nargs=-1, required=False)
def follower(account):
    """ Get information about followers
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        if "default_account" in stm.config:
            account = [stm.config["default_account"]]
    for a in account:
        a = Account(a, blockchain_instance=stm)
        print("\nFollowers statistics for @%s (please wait...)" % a.name)
        followers = a.get_followers(False)
        followers.print_summarize_table(tag_type="Followers")


@cli.command()
@click.argument('account', nargs=-1, required=False)
def following(account):
    """ Get information about following
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        if "default_account" in stm.config:
            account = [stm.config["default_account"]]
    for a in account:
        a = Account(a, blockchain_instance=stm)
        print("\nFollowing statistics for @%s (please wait...)" % a.name)
        following = a.get_following(False)
        following.print_summarize_table(tag_type="Following")


@cli.command()
@click.argument('account', nargs=-1, required=False)
def muter(account):
    """ Get information about muter
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        if "default_account" in stm.config:
            account = [stm.config["default_account"]]
    for a in account:
        a = Account(a, blockchain_instance=stm)
        print("\nMuters statistics for @%s (please wait...)" % a.name)
        muters = a.get_muters(False)
        muters.print_summarize_table(tag_type="Muters")


@cli.command()
@click.argument('account', nargs=-1, required=False)
def muting(account):
    """ Get information about muting
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        if "default_account" in stm.config:
            account = [stm.config["default_account"]]
    for a in account:
        a = Account(a, blockchain_instance=stm)
        print("\nMuting statistics for @%s (please wait...)" % a.name)
        muting = a.get_mutings(False)
        muting.print_summarize_table(tag_type="Muting")


@cli.command()
@click.argument('account', nargs=1, required=False)
@click.option('--limit', '-l', help='Limits shown notifications')
@click.option('--all', '-a', help='Show all notifications (when not set, only unread are shown)', is_flag=True, default=False)
@click.option('--mark_as_read', '-m', help='Broadcast a mark all as read custom json', is_flag=True, default=False)
@click.option('--replies', '-r', help='Show only replies', is_flag=True, default=False)
@click.option('--mentions', '-t', help='Show only mentions', is_flag=True, default=False)
@click.option('--follows', '-f', help='Show only follows', is_flag=True, default=False)
@click.option('--votes', '-v', help='Show only upvotes', is_flag=True, default=False)
@click.option('--reblogs', '-b', help='Show only reblogs', is_flag=True, default=False)
@click.option('--reverse', '-s', help='Reverse sorting of notifications', is_flag=True, default=False)
def notifications(account, limit, all, mark_as_read, replies, mentions, follows, votes, reblogs, reverse):
    """ Show notifications of an account
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if account is None or account == "":
        if "default_account" in stm.config:
            account = stm.config["default_account"]
    if mark_as_read and not unlock_wallet(stm):
        return    
    if not replies and not mentions and not follows and not votes and not reblogs:
        show_all = True
    else:
        show_all = False
    account = Account(account, blockchain_instance=stm)
    t = PrettyTable(["Date", "Type", "Message"], hrules=0)
    t.align = "r"
    last_read = None
    if limit is not None:
        limit = int(limit)
    all_notifications = account.get_notifications(only_unread=not all, limit=limit)
    if reverse:
        all_notifications = all_notifications[::-1]
    for note in all_notifications:
        if not show_all:
            if note["type"] == "reblog" and not reblogs:
                continue
            elif note["type"] == "reply" and not replies:
                continue
            elif note["type"] == "reply_comment" and not replies:
                continue            
            elif note["type"] == "mention" and not mentions:
                continue
            elif note["type"] == "follow" and not follows:
                continue
            elif note["type"] == "vote" and not votes:
                continue            
        t.add_row([
            str(datetime.fromtimestamp(calendar.timegm(note["date"].timetuple()))),
            note["type"],
            note["msg"],
        ])
        last_read = note["date"]
    print(t)
    if mark_as_read:
        account.mark_notifications_as_read(last_read=last_read)


@cli.command()
@click.argument('account', nargs=1, required=False)
def permissions(account):
    """ Show permissions of an account
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        if "default_account" in stm.config:
            account = stm.config["default_account"]
    account = Account(account, blockchain_instance=stm)
    t = PrettyTable(["Permission", "Threshold", "Key/Account"], hrules=0)
    t.align = "r"
    for permission in ["owner", "active", "posting"]:
        auths = []
        for type_ in ["account_auths", "key_auths"]:
            for authority in account[permission][type_]:
                auths.append("%s (%d)" % (authority[0], authority[1]))
        t.add_row([
            permission,
            account[permission]["weight_threshold"],
            "\n".join(auths),
        ])
    print(t)


@cli.command()
@click.argument('foreign_account', nargs=1, required=False)
@click.option('--permission', default="posting", help='The permission to grant (defaults to "posting")')
@click.option('--account', '-a', help='The account to allow action for')
@click.option('--weight', help='The weight to use instead of the (full) threshold. '
              'If the weight is smaller than the threshold, '
              'additional signatures are required')
@click.option('--threshold', help='The permission\'s threshold that needs to be reached '
              'by signatures to be able to interact')
def allow(foreign_account, permission, account, weight, threshold):
    """Allow an account/key to interact with your account

        foreign_account: The account or key that will be allowed to interact with account.
            When not given, password will be asked, from which a public key is derived.
            This derived key will then interact with your account.
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    if permission not in ["posting", "active", "owner"]:
        print("Wrong permission, please use: posting, active or owner!")
        return
    acc = Account(account, blockchain_instance=stm)
    if not foreign_account:
        from beemgraphenebase.account import PasswordKey
        pwd = click.prompt("Password for Key Derivation", confirmation_prompt=True, hide_input=True)
        foreign_account = format(PasswordKey(account, pwd, permission).get_public(), stm.prefix)
    if threshold is not None:
        threshold = int(threshold)
    tx = acc.allow(foreign_account, weight=weight, permission=permission, threshold=threshold)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('foreign_account', nargs=1, required=False)
@click.option('--permission', default="posting", help='The permission to grant (defaults to "posting")')
@click.option('--account', '-a', help='The account to disallow action for')
@click.option('--threshold', help='The permission\'s threshold that needs to be reached '
              'by signatures to be able to interact')
def disallow(foreign_account, permission, account, threshold):
    """Remove allowance an account/key to interact with your account"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    if permission not in ["posting", "active", "owner"]:
        print("Wrong permission, please use: posting, active or owner!")
        return
    if threshold is not None:
        threshold = int(threshold)
    acc = Account(account, blockchain_instance=stm)
    if not foreign_account:
        from beemgraphenebase.account import PasswordKey
        pwd = click.prompt("Password for Key Derivation", confirmation_prompt=True)
        foreign_account = [format(PasswordKey(account, pwd, permission).get_public(), stm.prefix)]
    tx = acc.disallow(foreign_account, permission=permission, threshold=threshold)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('creator', nargs=1, required=True)
@click.option('--fee', help='When fee is 0 (default) a subsidized account is claimed and can be created later with create_claimed_account', default=0.0)
@click.option('--number', '-n', help='Number of subsidized accounts to be claimed (default = 1), when fee = 0 STEEM', default=1)
def claimaccount(creator, fee, number):
    """Claim account for claimed account creation."""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not creator:
        creator = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    creator = Account(creator, blockchain_instance=stm)
    fee = Amount("%.3f %s" % (float(fee), stm.token_symbol), blockchain_instance=stm)
    tx = None
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.claim_account(creator, fee=fee)
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.claim_account(creator, fee=fee)
        tx = stm.hivesigner.url_from_tx(tx)
    elif float(fee) == 0:
        rc = RC(blockchain_instance=stm)
        current_costs = rc.claim_account(tx_size=200)
        current_mana = creator.get_rc_manabar()["current_mana"]
        last_mana = current_mana
        cnt = 0
        print("Current costs %.2f G RC - current mana %.2f G RC" % (current_costs / 1e9, current_mana / 1e9))
        print("Account can claim %d accounts" % (int(current_mana / current_costs)))
        while current_costs + 10 < current_mana and cnt < number:
            if cnt > 0:
                print("Current costs %.2f G RC - current mana %.2f G RC" % (current_costs / 1e9, current_mana / 1e9))
                tx = json.dumps(tx, indent=4)
                print(tx)
            cnt += 1
            tx = stm.claim_account(creator, fee=fee)
            time.sleep(10)
            creator.refresh()
            current_mana = creator.get_rc_manabar()["current_mana"]
            print("Account claimed and %.2f G RC paid." % ((last_mana - current_mana) / 1e9))
            last_mana = current_mana
        if cnt == 0:
            print("Not enough RC for a claim!")
    else:
        tx = stm.claim_account(creator, fee=fee)
    if tx is not None:
        tx = json.dumps(tx, indent=4)
        print(tx)


@cli.command()
@click.argument('account', nargs=1, required=True)
@click.option('--owner', help='Main owner public key - when not given, a passphrase is used to create keys.')
@click.option('--active', help='Active public key - when not given, a passphrase is used to create keys.')
@click.option('--posting', help='posting public key - when not given, a passphrase is used to create keys.')
@click.option('--memo', help='Memo public key - when not given, a passphrase is used to create keys.')
@click.option('--import-pub', '-i', help='Load public keys from file.')
def changekeys(account, owner, active, posting, memo, import_pub):
    """Changes all keys for the specified account 
    Keys are given in their public form.
    Asks for the owner key for broadcasting the op to the chain."""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    account = Account(account, blockchain_instance=stm)

    if import_pub and import_pub != "":
        if not os.path.isfile(import_pub):
            raise Exception("File %s does not exist!" % import_pub)
        with open(import_pub) as fp:
            pubkeys = fp.read()
        if pubkeys.find('\0') > 0:
            with open(import_pub, encoding='utf-16') as fp:
                pubkeys = fp.read()
        pubkeys = ast.literal_eval(pubkeys)
        owner = pubkeys["owner"]
        active = pubkeys["active"]
        posting = pubkeys["posting"]
        memo = pubkeys["memo"]

    if owner is None and active is None and memo is None and posting is None:
        raise ValueError("All pubkeys are None or empty!")
    if owner == "" or owner is None:
        owner = account["owner"]["key_auths"][0][0]
    if active == "" or active is None:
        active = account["active"]["key_auths"][0][0]
    if posting == "" or posting is None:
        posting = account["posting"]["key_auths"][0][0]
    if memo == "" or memo is None:
        memo = account["memo_key"]

    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    t.add_row(["account", account["name"]])
    t.add_row(["new owner pubkey", str(owner)])
    t.add_row(["new active pubkey", str(active)])
    t.add_row(["new posting pubkey", str(posting)])
    t.add_row(["new memo pubkey", str(memo)])
    print(t)
    if not stm.unsigned:
        wif = click.prompt('Owner key for %s' % account["name"], confirmation_prompt=False, hide_input=True)
        stm.wallet.setKeys([wif])

    tx = stm.update_account(account, owner_key=owner, active_key=active,
                            posting_key=posting, memo_key=memo, password=None)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('accountname', nargs=1, required=True)
@click.option('--account', '-a', help='Account that pays the fee or uses account tickets')
@click.option('--owner', help='Main public owner key - when not given, a passphrase is used to create keys.')
@click.option('--active', help='Active public key - when not given, a passphrase is used to create keys.')
@click.option('--memo', help='Memo public key - when not given, a passphrase is used to create keys.')
@click.option('--posting', help='posting public key - when not given, a passphrase is used to create keys.')
@click.option('--wif', '-w', help='Defines how many times the password is replaced by its WIF representation for password based keys (default = 0).', default=0)
@click.option('--create-claimed-account', '-c', help='Instead of paying the account creation fee a subsidized account is created.', is_flag=True, default=False)
@click.option('--import-pub', '-i', help='Load public keys from file.')
def newaccount(accountname, account, owner, active, memo, posting, wif, create_claimed_account, import_pub):
    """Create a new account
       Default setting is that a fee is payed for account creation
       Use --create-claimed-account for free account creation

       Please use keygen and set public keys
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    if import_pub and import_pub != "":
        if not os.path.isfile(import_pub):
            raise Exception("File %s does not exist!" % import_pub)
        with open(import_pub) as fp:
            pubkeys = fp.read()
        if pubkeys.find('\0') > 0:
            with open(import_pub, encoding='utf-16') as fp:
                pubkeys = fp.read()
        pubkeys = ast.literal_eval(pubkeys)
        owner = pubkeys["owner"]
        active = pubkeys["active"]
        posting = pubkeys["posting"]
        memo = pubkeys["memo"]
        if create_claimed_account:
            tx = stm.create_claimed_account(accountname, creator=acc, owner_key=owner, active_key=active, memo_key=memo, posting_key=posting)
        else:
            tx = stm.create_account(accountname, creator=acc, owner_key=owner, active_key=active, memo_key=memo, posting_key=posting)        
    elif owner is None or active is None or memo is None or posting is None:
        import_password = click.prompt("Keys were not given - Passphrase is used to create keys\n New Account Passphrase", confirmation_prompt=True, hide_input=True)
        if not import_password:
            print("You cannot chose an empty password")
            return
        if wif > 0:
            password = import_password
            for _ in range(wif):
                pk = PasswordKey("", password, role="")
                password = str(pk.get_private())
            password = 'P' + password
        else:
            password = import_password        
        if create_claimed_account:
            tx = stm.create_claimed_account(accountname, creator=acc, password=password)
        else:
            tx = stm.create_account(accountname, creator=acc, password=password)
    else:
        if create_claimed_account:
            tx = stm.create_claimed_account(accountname, creator=acc, owner_key=owner, active_key=active, memo_key=memo, posting_key=posting)
        else:
            tx = stm.create_account(accountname, creator=acc, owner_key=owner, active_key=active, memo_key=memo, posting_key=posting)        
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('variable', nargs=1, required=False)
@click.argument('value', nargs=1, required=False)
@click.option('--account', '-a', help='setprofile as this user')
@click.option('--pair', '-p', help='"Key=Value" pairs', multiple=True)
def setprofile(variable, value, account, pair):
    """Set a variable in an account\'s profile"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    keys = []
    values = []
    if pair:
        for p in pair:
            key, value = p.split("=")
            keys.append(key)
            values.append(value)
    if variable and value:
        keys.append(variable)
        values.append(value)

    profile = Profile(keys, values)

    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)

    json_metadata = Profile(acc["json_metadata"] if acc["json_metadata"] else {})
    json_metadata.update(profile)
    tx = acc.update_account_profile(json_metadata)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('variable', nargs=-1, required=True)
@click.option('--account', '-a', help='delprofile as this user')
def delprofile(variable, account):
    """Delete a variable in an account\'s profile"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()

    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    json_metadata = Profile(acc["json_metadata"])

    for var in variable:
        json_metadata.remove(var)

    tx = acc.update_account_profile(json_metadata)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('account', nargs=1, required=True)
@click.option('--roles', help='Import specified keys (owner, active, posting, memo).', default=["active", "posting", "memo"])
def importaccount(account, roles):
    """Import an account using a passphrase"""
    from beemgraphenebase.account import PasswordKey
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not unlock_wallet(stm):
        return
    account = Account(account, blockchain_instance=stm)
    imported = False
    password = click.prompt("Account Passphrase", confirmation_prompt=False, hide_input=True)
    if not password:
        print("You cannot chose an empty Passphrase")
        return
    if "owner" in roles:
        owner_key = PasswordKey(account["name"], password, role="owner")
        owner_pubkey = format(owner_key.get_public_key(), stm.prefix)
        if owner_pubkey in [x[0] for x in account["owner"]["key_auths"]]:
            print("Importing owner key!")
            owner_privkey = owner_key.get_private_key()
            stm.wallet.addPrivateKey(owner_privkey)
            imported = True

    if "active" in roles:
        active_key = PasswordKey(account["name"], password, role="active")
        active_pubkey = format(active_key.get_public_key(), stm.prefix)
        if active_pubkey in [x[0] for x in account["active"]["key_auths"]]:
            print("Importing active key!")
            active_privkey = active_key.get_private_key()
            stm.wallet.addPrivateKey(active_privkey)
            imported = True

    if "posting" in roles:
        posting_key = PasswordKey(account["name"], password, role="posting")
        posting_pubkey = format(posting_key.get_public_key(), stm.prefix)
        if posting_pubkey in [
            x[0] for x in account["posting"]["key_auths"]
        ]:
            print("Importing posting key!")
            posting_privkey = posting_key.get_private_key()
            stm.wallet.addPrivateKey(posting_privkey)
            imported = True

    if "memo" in roles:
        memo_key = PasswordKey(account["name"], password, role="memo")
        memo_pubkey = format(memo_key.get_public_key(), stm.prefix)
        if memo_pubkey == account["memo_key"]:
            print("Importing memo key!")
            memo_privkey = memo_key.get_private_key()
            stm.wallet.addPrivateKey(memo_privkey)
            imported = True

    if not imported:
        print("No matching key(s) found. Password correct?")


@cli.command()
@click.option('--account', '-a', help='The account to updatememokey action for')
@click.option('--key', help='The new memo key')
def updatememokey(account, key):
    """Update an account\'s memo key"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    if not key:
        from beemgraphenebase.account import PasswordKey
        pwd = click.prompt("Password for Memo Key Derivation", confirmation_prompt=True, hide_input=True)
        memo_key = PasswordKey(account, pwd, "memo")
        key = format(memo_key.get_public_key(), stm.prefix)
        memo_privkey = memo_key.get_private_key()
        if not stm.nobroadcast:
            stm.wallet.addPrivateKey(memo_privkey)
    tx = acc.update_memo_key(key)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('authorperm', nargs=1)
@click.argument('beneficiaries', nargs=-1)
def beneficiaries(authorperm, beneficiaries):
    """Set beneficaries"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    c = Comment(authorperm, blockchain_instance=stm)
    account = c["author"]

    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return

    options = {"author": c["author"],
               "permlink": c["permlink"],
               "max_accepted_payout": c["max_accepted_payout"],
               "percent_steem_dollars": c["percent_steem_dollars"],
               "allow_votes": c["allow_votes"],
               "allow_curation_rewards": c["allow_curation_rewards"]}

    if isinstance(beneficiaries, tuple) and len(beneficiaries) == 1:
        beneficiaries = beneficiaries[0].split(",")
    beneficiaries_list_sorted = derive_beneficiaries(beneficiaries)
    for b in beneficiaries_list_sorted:
        Account(b["account"], blockchain_instance=stm)
    tx = stm.comment_options(options, authorperm, beneficiaries_list_sorted, account=account)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('message_file', nargs=1, required=False)
@click.option('--account', '-a', help='Account which should sign')
@click.option('--verify', '-v', help='Verify a message instead of signing it', is_flag=True, default=False)
def message(message_file, account, verify):
    """Sign and verify a message

    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if message_file is not None:
        with open(message_file) as f:
            message = f.read()
    elif verify:
        print("Please store the signed message into a text file and append the file path to beempy message -v")
        return
    else:
        message = input("Enter message: ")
    m = Message(message, blockchain_instance=stm)
    if verify:
        if m.verify():
            print("Could verify message!")
        else:
            print("Could not verify message!")
    else:
        if not unlock_wallet(stm):
            return        
        out = m.sign(account)
    if message_file is not None:
        with open(message_file, "w", encoding="utf-8") as f:
            f.write(out)
    else:
        print(out)


@cli.command()
@click.argument('memo', nargs=-1)
@click.option('--account', '-a', help='Account which decrypts the memo with its memo key')
@click.option('--output', '-o', help='Output file name. Result is stored, when set instead of printed.')
@click.option('--info', '-i', help='Shows information about public keys and used nonce', is_flag=True, default=False)
@click.option('--text', '-t', help='Reads the text file content', is_flag=True, default=False)
@click.option('--binary', '-b', help='Reads the binary file content', is_flag=True, default=False)
def decrypt(memo, account, output, info, text, binary):
    """decrypt a (or more than one) decrypted memo/file with your memo key

    """
    if text and binary:
        print("You cannot set text and binary!")
        return
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    m = Memo(from_account=None, to_account=account, blockchain_instance=stm)

    if not unlock_wallet(stm):
        return
    for entry in memo:
        print("\n")
        if not binary and info:
            from_key, to_key, nonce = m.extract_decrypt_memo_data(entry)
            try:
                from_account = stm.wallet.getAccountFromPublicKey(str(from_key))
                to_account = stm.wallet.getAccountFromPublicKey(str(to_key))
                if from_account is not None:
                    print("from: %s" % str(from_account))
                else:
                    print("from: %s" % str(from_key))
                if to_account is not None:
                    print("to: %s" % str(to_account))
                else:
                    print("to: %s" % str(to_key))
                print("nonce: %s" % nonce)
            except:
                print("from: %s" % str(from_key))
                print("to: %s" % str(to_key))
                print("nonce: %s" % nonce)
        if text:
            with open(entry) as f:
                message = f.read()
        elif binary:
            if output is None:
                output = entry + ".dec"
            ret = m.decrypt_binary(entry, output, buffer_size=2048)
            if info:
                t = PrettyTable(["Key", "Value"])
                t.align = "l"
                t.add_row(["file", entry])
                for key in ret:
                    t.add_row([key, ret[key]])
                print(t)
        else:
            message = entry
        if text:
            out = m.decrypt(message)
            if output is None:
                output = entry
            with open(output, "w", encoding="utf-8") as f:
                f.write(out)
        elif not binary:
            out = m.decrypt(message)
            if info:
                print("message: %s" % out)              
            if output:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(out)
            elif not info:
                print(out)


@cli.command()
@click.argument('receiver', nargs=1)
@click.argument('memo', nargs=-1)
@click.option('--account', '-a', help='Account which encrypts the memo with its memo key')
@click.option('--output', '-o', help='Output file name. Result is stored, when set instead of printed.')
@click.option('--text', '-t', help='Reads the text file content', is_flag=True, default=False)
@click.option('--binary', '-b', help='Reads the binary file content', is_flag=True, default=False)
def encrypt(receiver, memo, account, output, text, binary):
    """encrypt a (or more than one) memo text/file with the your memo key

    """
    if text and binary:
        print("You cannot set text and binary!")
        return    
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    m = Memo(from_account=account, to_account=receiver, blockchain_instance=stm)
    if not unlock_wallet(stm):
        return
    for entry in memo:
        print("\n")
        if text:
            with open(entry) as f:
                message = f.read()
            if message[0] == "#":
                message = message[1:]
        elif binary:
            if output is None:
                output = entry + ".enc"
            m.encrypt_binary(entry, output, buffer_size=2048)      
        else:
            message = entry
            if message[0] == "#":
                message = message[1:]

        if text:
            out = m.encrypt(message)["message"]
            if output is None:
                output = entry        
            with open(output, "w", encoding="utf-8") as f:
                f.write(out)
        elif not binary:
            out = m.encrypt(message)["message"]
            if output is None:
                print(out)
            else:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(out)                


@cli.command()
@click.argument('image', nargs=1)
@click.option('--account', '-a', help='Account name')
@click.option('--image-name', '-n', help='Image name')
def uploadimage(image, account, image_name):
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    iu = ImageUploader(blockchain_instance=stm)
    tx = iu.upload(image, account, image_name)
    if image_name is None:
        print("![](%s)" % tx["url"])
    else:
        print("![%s](%s)" % (image_name, tx["url"]))

@cli.command()
@click.argument('permlink', nargs=-1)
@click.option('--account', '-a', help='Account are you posting from')
@click.option('--save', '-s', help="Saves markdown in current directoy as date_permlink.md", is_flag=True, default=False)
@click.option('--export', '-e', default=None, help="Export markdown to given a md-file name")
def download(permlink, account, save, export):
    """Download body with yaml header"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if account is None:
        account = stm.config["default_account"]
    account = Account(account, blockchain_instance=stm)
    if len(permlink) == 0:
        permlink = []
        progress_length = account.virtual_op_count()
        print("Reading post history...")
        last_index = 0
        with click.progressbar(length=progress_length) as bar:
            for h in account.history(only_ops=["comment"]):
                if h["parent_author"] != '':
                    continue
                if h["author"] != account["name"]:
                    continue
                if h["permlink"] in permlink:
                    continue
                else:
                    permlink.append(h["permlink"])
                    bar.update(h["index"] - last_index)
                    last_index = h["index"]

    for p in permlink:
        if p[0] == "@":
            authorperm = p
        elif os.path.exists(p):
            with open(p) as f:
                content = f.read()
            body, parameter = seperate_yaml_dict_from_body(content)
            if "author" in parameter and "permlink" in parameter:
                authorperm = construct_authorperm(parameter["author"], parameter["permlink"])
            else:
                authorperm = construct_authorperm(account["name"], p)
        else:
            authorperm = construct_authorperm(account["name"], p)
        if len(permlink) > 1:
            print(authorperm)
        comment = Comment(authorperm, blockchain_instance=stm)
        if comment["parent_author"] != "" and comment["parent_permlink"] != "":
            reply_identifier = construct_authorperm(comment["parent_author"], comment["parent_permlink"])
        else:
            reply_identifier = None

        yaml_prefix = '---\n'
        if comment["title"] != "":
            yaml_prefix += 'title: "%s"\n' % comment["title"]
        yaml_prefix += 'permlink: %s\n' % comment["permlink"]
        yaml_prefix += 'author: %s\n' % comment["author"]
        if "author" in comment.json_metadata:
            yaml_prefix += 'authored by: %s\n' % comment.json_metadata["author"]
        if "description" in comment.json_metadata:
            yaml_prefix += 'description: "%s"\n' % comment.json_metadata["description"]
        if "canonical_url" in comment.json_metadata:
            yaml_prefix += 'canonical_url: %s\n' % comment.json_metadata["canonical_url"]
        if "app" in comment.json_metadata:
            yaml_prefix += 'app: %s\n' % comment.json_metadata["app"]
        yaml_prefix += 'last_update: %s\n' % comment.json()["last_update"]
        yaml_prefix += 'max_accepted_payout: %s\n' % str(comment["max_accepted_payout"])
        yaml_prefix += 'percent_steem_dollars: %s\n' %  str(comment["percent_steem_dollars"])
        if "tags" in comment.json_metadata:
            if len(comment.json_metadata["tags"]) > 0 and comment["category"] != comment.json_metadata["tags"][0] and len(comment["category"]) > 0:
                yaml_prefix += 'community: %s\n' % comment["category"]
            yaml_prefix += 'tags: %s\n' % ",".join(comment.json_metadata["tags"])
        if "beneficiaries" in comment:
            beneficiaries = []
            for b in comment["beneficiaries"]:
                beneficiaries.append("%s:%.2f%%" % (b["account"], b["weight"] / 10000 * 100))
            if len(beneficiaries) > 0:
                yaml_prefix += 'beneficiaries: %s\n' % ",".join(beneficiaries)
        if reply_identifier is not None:
            yaml_prefix += 'reply_identifier: %s\n' % reply_identifier    
        yaml_prefix += '---\n'
        if save or export is not None:
            if export is None or len(permlink) > 0:
                export = comment.json()["created"].replace(":", "-") + "_" + comment["permlink"] + ".md"
            if export[-3:] != ".md":
                export += ".md"
            
            with open(export, "w", encoding="utf-8") as f:
                f.write(yaml_prefix + comment["body"])
        else:
            print(yaml_prefix + comment["body"])


@cli.command()
@click.argument('markdown-file', nargs=1)
@click.option('--account', '-a', help='Account are you posting from')
@click.option('--title', '-t', help='Title of the post')
@click.option('--tags', '-g', help='A komma separated list of tags to go with the post.')
@click.option('--community', '-c', help=' Name of the community (optional)')
@click.option('--beneficiaries', '-b', help='Post beneficiaries (komma separated, e.g. a:10%,b:20%)')
@click.option('--percent-steem-dollars', '-d', help='50% SBD /50% SP is 10000 (default), 100% SP is 0')
@click.option('--max-accepted-payout', '-m', help='Default is 1000000.000 [SBD]')
@click.option('--no-parse-body', '-n', help='Disable parsing of links, tags and images', is_flag=True, default=False)
def createpost(markdown_file, account, title, tags, community, beneficiaries, percent_steem_dollars, max_accepted_payout, no_parse_body):
    """Creates a new markdown file with YAML header"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    yaml_prefix = '---\n'                
    if account is None:
        account = input("author: ")
    if title is None:
        title = input("title: ")
    if tags is None:
        tags = input("tags (comma seperated):")
    if community is None:
        community = input("community account:")
    if beneficiaries is None:
        beneficiaries = input("beneficiaries (komma separated, e.g. a:10%,b:20%):")
    if percent_steem_dollars is None:
        ret = None
        while ret is None:
            ret = input("Reward: 50% or 100% Hive Power [50 or 100]?")
            if ret not in ["50", "100"]:
                ret = None
        if ret == "50":
            percent_steem_dollars = 10000
        else:
            percent_steem_dollars = 0
    if max_accepted_payout is None:
        max_accepted_payout = input("max accepted payout [return to skip]: ")
    
    yaml_prefix += 'title: "%s"\n' % title
    yaml_prefix += 'author: %s\n' % account
    yaml_prefix += 'tags: %s\n' % tags
    yaml_prefix += 'percent_steem_dollars: %d\n' % percent_steem_dollars
    if community is not None and community != "":
        yaml_prefix += 'community: %s\n' % community
    if beneficiaries is not None and beneficiaries != "":
        yaml_prefix += 'beneficiaries: %s\n' % beneficiaries
    if max_accepted_payout is not None and max_accepted_payout != "":
        yaml_prefix += 'max_accepted_payout: %s\n' % max_accepted_payout
    yaml_prefix += '---\n'     
    with open(markdown_file, "w", encoding="utf-8") as f:
        f.write(yaml_prefix)    


@cli.command()
@click.argument('markdown-file', nargs=1)
@click.option('--account', '-a', help='Account are you posting from')
@click.option('--title', '-t', help='Title of the post')
@click.option('--permlink', '-p', help='Manually set the permlink (optional)')
@click.option('--tags', '-g', help='A komma separated list of tags to go with the post.')
@click.option('--reply-identifier', '-r', help=' Identifier of the parent post/comment, when set a comment is broadcasted')
@click.option('--community', '-c', help=' Name of the community (optional)')
@click.option('--canonical-url', '-u', help='Canonical url, can also set to https://hive.blog or https://peakd.com (optional)')
@click.option('--beneficiaries', '-b', help='Post beneficiaries (komma separated, e.g. a:10%,b:20%)')
@click.option('--percent-steem-dollars', '-d', help='50% SBD /50% SP is 10000 (default), 100% SP is 0')
@click.option('--max-accepted-payout', '-m', help='Default is 1000000.000 [SBD]')
@click.option('--no-parse-body', '-n', help='Disable parsing of links, tags and images', is_flag=True, default=False)
@click.option('--no-patch-on-edit', '-e', help='Disable patch posting on edits (when the permlink already exists)', is_flag=True, default=False)
def post(markdown_file, account, title, permlink, tags, reply_identifier, community, canonical_url, beneficiaries, percent_steem_dollars, max_accepted_payout, no_parse_body, no_patch_on_edit):
    """broadcasts a post/comment. All image links which links to a file will be uploaded.
    The yaml header can contain:
    
    ---
    title: your title
    tags: tag1,tag2
    community: hive-100000
    beneficiaries: beempy:5%,holger80:5%
    ---
    
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()

    with open(markdown_file) as f:
        content = f.read()
    body, parameter = seperate_yaml_dict_from_body(content)
    if title is not None:
        parameter["title"] = title
    if account is not None:
        parameter["author"] = account
    if tags is not None:
        parameter["tags"] = tags
    if permlink is not None:
        parameter["permlink"] = permlink
    if beneficiaries is not None:
        parameter["beneficiaries"] = beneficiaries
    if community is not None:
        parameter["community"] = community
    if reply_identifier is not None:
        parameter["reply_identifier"] = reply_identifier
    if percent_steem_dollars is not None:
        parameter["percent_steem_dollars"] = percent_steem_dollars
    elif "percent-steem-dollars" in parameter:
        parameter["percent_steem_dollars"] = parameter["percent-steem-dollars"]
    if max_accepted_payout is not None:
        parameter["max_accepted_payout"] = max_accepted_payout
    elif "max-accepted-payout" in parameter:
        parameter["max_accepted_payout"] = parameter["max-accepted-payout"]

    if canonical_url is not None:
        parameter["canonical_url"] = canonical_url

    if not unlock_wallet(stm):
        return
    tags = None
    if "tags" in parameter:
        tags = derive_tags(parameter["tags"])
    title = ""
    if "title" in parameter:
        title = parameter["title"]
    if "author" in parameter:
        author = parameter["author"]
    else:
        author = stm.config["default_account"]
    permlink = None
    if "permlink" in parameter:
        permlink = parameter["permlink"]
    reply_identifier = None
    if "reply_identifier" in parameter:
        reply_identifier = parameter["reply_identifier"]
    community = None
    if "community" in parameter:
        community = parameter["community"]
    if "parse_body" in parameter:
        parse_body = bool(parameter["parse_body"])
    else:
        parse_body = not no_parse_body
    max_accepted_payout = None

    percent_steem_dollars = None
    if "percent_steem_dollars" in parameter:
        percent_steem_dollars = parameter["percent_steem_dollars"]
    max_accepted_payout = None
    if "max_accepted_payout" in parameter:
        max_accepted_payout = parameter["max_accepted_payout"]
    comment_options = None
    if max_accepted_payout is not None or percent_steem_dollars is not None:
        comment_options = {}
    if max_accepted_payout is not None:
        if stm.backed_token_symbol not in max_accepted_payout:
            max_accepted_payout = str(Amount(float(max_accepted_payout), stm.backed_token_symbol, blockchain_instance=stm))
        comment_options["max_accepted_payout"] = max_accepted_payout
    if percent_steem_dollars is not None:
        comment_options["percent_steem_dollars"] = percent_steem_dollars
    beneficiaries = None
    if "beneficiaries" in parameter:
        beneficiaries = derive_beneficiaries(parameter["beneficiaries"])
        for b in beneficiaries:
            Account(b["account"], blockchain_instance=stm)
 

    if permlink is not None:
        try:
            comment = Comment(construct_authorperm(author, permlink), blockchain_instance=stm)
        except:
            comment = None
    else:
        comment = None
        
    iu = ImageUploader(blockchain_instance=stm)
    for link in list(re.findall(r'!\[[^"\'@\]\(]*\]\([^"\'@\(\)]*\.(?:png|jpg|jpeg|gif|png|svg)\)', body)):
        image = link.split("(")[1].split(")")[0]
        image_name = link.split("![")[1].split("]")[0]
        if image[:4] == "http":
            continue
        if stm.unsigned:
            continue
        basepath = os.path.dirname(markdown_file)
        if os.path.exists(image):
            tx = iu.upload(image, author, image_name)
            body = body.replace(image, tx["url"])
        elif os.path.exists(os.path.join(basepath, image)):
            tx = iu.upload(image, author, image_name)
            body = body.replace(image, tx["url"])
    
    if comment is None and permlink is None and reply_identifier is None:
        permlink = derive_permlink(title, with_suffix=False)
        try:
            comment = Comment(construct_authorperm(author, permlink), blockchain_instance=stm)
        except:
            comment = None
    if comment is None:
        json_metadata = {}
    else:
        json_metadata = comment.json_metadata
    if "authored_by" in parameter:
        json_metadata["authored_by"] = parameter["authored_by"]
    if "description" in parameter:
        json_metadata["description"] = parameter["description"] 
    if "canonical_url" in parameter:
        json_metadata["canonical_url"] = parameter["canonical_url"]
    else:
        json_metadata["canonical_url"] = stm.config["default_canonical_url"] or "https://hive.blog"

    if "canonical_url" in json_metadata and json_metadata["canonical_url"].find("@") < 0:
        if json_metadata["canonical_url"][-1] != "/":
                json_metadata["canonical_url"] += "/"
        if json_metadata["canonical_url"][:8] != 'https://':
            json_metadata["canonical_url"] = 'https://' + json_metadata["canonical_url"] 
        if community is None:
            json_metadata["canonical_url"] += tags[0] + "/@" + author + "/" + permlink
        else:
            json_metadata["canonical_url"] += community + "/@" + author + "/" + permlink

    if comment is None or no_patch_on_edit:

        if reply_identifier is None and (len(tags) == 0 or tags is None):
            raise ValueError("Tags must not be empty!")
        tx = stm.post(title, body, author=author, permlink=permlink, reply_identifier=reply_identifier, community=community,
                      tags=tags, json_metadata=json_metadata, comment_options=comment_options, beneficiaries=beneficiaries, parse_body=parse_body,
                      app='beempy/%s' % (__version__))
    else:
        import diff_match_patch as dmp_module
        dmp = dmp_module.diff_match_patch()
        patch = dmp.patch_make(comment.body, body)
        patch_text = dmp.patch_toText(patch)
        if patch_text == "":
            print("No changes on post body detected.")
        else:
            print(patch_text)
        edit_ok = click.prompt("Should I broadcast %s [y/n]" % (str(permlink)))
        if edit_ok not in ["y", "ye", "yes"]:                
            return
        tx = stm.post(title, patch_text, author=author, permlink=permlink, reply_identifier=reply_identifier, community=community,
                      tags=tags, json_metadata=json_metadata, parse_body=False, app='beempy/%s' % (__version__))        
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('authorperm', nargs=1)
@click.argument('body', nargs=1)
@click.option('--account', '-a', help='Account are you posting from')
@click.option('--title', '-t', help='Title of the post')
def reply(authorperm, body, account, title):
    """replies to a comment"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()

    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    
    if title is None:
        title = ""
    tx = stm.post(title, body, json_metadata=None, author=account, reply_identifier=authorperm,
                  app='beempy/%s' % (__version__))
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('witness', nargs=1)
@click.option('--account', '-a', help='Your account')
def approvewitness(witness, account):
    """Approve a witnesses"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    tx = acc.approvewitness(witness, approve=True)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('witness', nargs=1)
@click.option('--account', '-a', help='Your account')
def disapprovewitness(witness, account):
    """Disapprove a witnesses"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    tx = acc.disapprovewitness(witness)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('proxy', nargs=1)
@click.option('--account', '-a', help='Your account')
def setproxy(proxy, account):
    """Set your witness/proposal system proxy"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    tx = acc.setproxy(proxy, account)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.option('--account', '-a', help='Your account')
def delproxy(account):
    """Delete your witness/proposal system proxy"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    tx = acc.setproxy('', account)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.option('--file', '-i', help='Load transaction from file. If "-", read from stdin (defaults to "-")')
@click.option('--outfile', '-o', help='Load transaction from file. If "-", read from stdin (defaults to "-")')
def sign(file, outfile):
    """Sign a provided transaction with available and required keys"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not unlock_wallet(stm):
        return
    if file and file != "-":
        if not os.path.isfile(file):
            raise Exception("File %s does not exist!" % file)
        with open(file) as fp:
            tx = fp.read()
        if tx.find('\0') > 0:
            with open(file, encoding='utf-16') as fp:
                tx = fp.read()
    else:
        tx = click.get_text_stream('stdin')
    tx = ast.literal_eval(tx)
    tx = stm.sign(tx, reconstruct_tx=False)
    tx = json.dumps(tx, indent=4)
    if outfile and outfile != "-":
        with open(outfile, 'w') as fp:
            fp.write(tx)
    else:
        print(tx)


@cli.command()
@click.option('--file', help='Load transaction from file. If "-", read from stdin (defaults to "-")')
def broadcast(file):
    """broadcast a signed transaction"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if file and file != "-":
        if not os.path.isfile(file):
            raise Exception("File %s does not exist!" % file)
        with open(file) as fp:
            tx = fp.read()
        if tx.find('\0') > 0:
            with open(file, encoding='utf-16') as fp:
                tx = fp.read()
    else:
        tx = click.get_text_stream('stdin')
    tx = ast.literal_eval(tx)
    tx = stm.broadcast(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.option('--sbd-to-steem', '-i', help='Show ticker in SBD/STEEM', is_flag=True, default=False)
def ticker(sbd_to_steem):
    """ Show ticker
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    market = Market(blockchain_instance=stm)
    ticker = market.ticker()
    for key in ticker:
        if key in ["highest_bid", "latest", "lowest_ask"] and sbd_to_steem:
            t.add_row([key, str(ticker[key].as_base(stm.backed_token_symbol))])
        elif key in "percent_change" and sbd_to_steem:
            t.add_row([key, "%.2f %%" % -ticker[key]])
        elif key in "percent_change":
            t.add_row([key, "%.2f %%" % ticker[key]])
        else:
            t.add_row([key, str(ticker[key])])
    print(t)


@cli.command()
@click.option('--width', '-w', help='Plot width (default 75)', default=75)
@click.option('--height', '-h', help='Plot height (default 15)', default=15)
@click.option('--ascii', help='Use only ascii symbols', is_flag=True, default=False)
def pricehistory(width, height, ascii):
    """ Show price history
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    feed_history = stm.get_feed_history()
    current_base = Amount(feed_history['current_median_history']["base"], blockchain_instance=stm)
    current_quote = Amount(feed_history['current_median_history']["quote"], blockchain_instance=stm)
    price_history = feed_history["price_history"]
    price = []
    for h in price_history:
        base = Amount(h["base"], blockchain_instance=stm)
        quote = Amount(h["quote"], blockchain_instance=stm)
        price.append(float(base.amount / quote.amount))
    if ascii:
        charset = u'ascii'
    else:
        charset = u'utf8'
    chart = AsciiChart(height=height, width=width, offset=4, placeholder='{:6.2f} $', charset=charset)
    print("\n            Price history for %s (median price %4.2f $)\n" % (stm.token_symbol, float(current_base) / float(current_quote)))

    chart.adapt_on_series(price)
    chart.new_chart()
    chart.add_axis()
    if (float(current_base) / float(current_quote)) <= max(price):
        chart._draw_h_line(chart._map_y(float(current_base) / float(current_quote)), 1, int(chart.n / chart.skip), line=chart.char_set["curve_hl_dot"])
    chart.add_curve(price)
    print(str(chart))


@cli.command()
@click.option('--days', '-d', help='Limit the days of shown trade history (default 7)', default=7.)
@click.option('--hours', help='Limit the intervall history intervall (default 2 hours)', default=2.0)
@click.option('--sbd-to-steem', '-i', help='Show ticker in SBD/STEEM', is_flag=True, default=False)
@click.option('--limit', '-l', help='Limit number of trades which is fetched at each intervall point (default 100)', default=100)
@click.option('--width', '-w', help='Plot width (default 75)', default=75)
@click.option('--height', '-h', help='Plot height (default 15)', default=15)
@click.option('--ascii', help='Use only ascii symbols', is_flag=True, default=False)
def tradehistory(days, hours, sbd_to_steem, limit, width, height, ascii):
    """ Show price history
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    m = Market(blockchain_instance=stm)
    utc = pytz.timezone('UTC')
    stop = utc.localize(datetime.utcnow())
    start = stop - timedelta(days=days)
    intervall = timedelta(hours=hours)
    trades = m.trade_history(start=start, stop=stop, limit=limit, intervall=intervall)
    price = []
    if sbd_to_steem:
        base_str = stm.token_symbol
    else:
        base_str = stm.backed_token_symbol
    for trade in trades:
        base = 0
        quote = 0
        for order in trade:
            base += float(order.as_base(base_str)["base"])
            quote += float(order.as_base(base_str)["quote"])
        price.append(base / quote)
    if ascii:
        charset = u'ascii'
    else:
        charset = u'utf8'
    chart = AsciiChart(height=height, width=width, offset=3, placeholder='{:6.2f} ', charset=charset)
    if sbd_to_steem:
        print("\n     Trade history %s - %s \n\n%s/%s" % (formatTimeString(start), formatTimeString(stop),
                                                          stm.backed_token_symbol, stm.token_symbol))
    else:
        print("\n     Trade history %s - %s \n\n%s/%s" % (formatTimeString(start), formatTimeString(stop),
                                                          stm.token_symbol, stm.backed_token_symbol))
    chart.adapt_on_series(price)
    chart.new_chart()
    chart.add_axis()
    chart.add_curve(price)
    print(str(chart))


@cli.command()
@click.option('--chart', help='Enable charting', is_flag=True)
@click.option('--limit', '-l', help='Limit number of returned open orders (default 25)', default=25)
@click.option('--show-date', help='Show dates', is_flag=True, default=False)
@click.option('--width', '-w', help='Plot width (default 75)', default=75)
@click.option('--height', '-h', help='Plot height (default 15)', default=15)
@click.option('--ascii', help='Use only ascii symbols', is_flag=True, default=False)
def orderbook(chart, limit, show_date, width, height, ascii):
    """Obtain orderbook of the internal market"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    market = Market(blockchain_instance=stm)
    orderbook = market.orderbook(limit=limit, raw_data=False)
    if not show_date:
        header = ["Asks Sum " + stm.backed_token_symbol, "Sell Orders", "Bids Sum " + stm.backed_token_symbol, "Buy Orders"]
    else:
        header = ["Asks date", "Sell Orders", "Bids date", "Buy Orders"]
    t = PrettyTable(header, hrules=0)
    t.align = "r"
    asks = []
    bids = []
    asks_date = []
    bids_date = []
    sumsum_asks = []
    sum_asks = 0
    sumsum_bids = []
    sum_bids = 0
    n = 0
    for order in orderbook["asks"]:
        asks.append(order)
        sum_asks += float(order.as_base(stm.backed_token_symbol)["base"])
        sumsum_asks.append(sum_asks)
    if n < len(asks):
        n = len(asks)
    for order in orderbook["bids"]:
        bids.append(order)
        sum_bids += float(order.as_base(stm.backed_token_symbol)["base"])
        sumsum_bids.append(sum_bids)
    if n < len(bids):
        n = len(bids)
    if show_date:
        for order in orderbook["asks_date"]:
            asks_date.append(order)
        if n < len(asks_date):
            n = len(asks_date)
        for order in orderbook["bids_date"]:
            bids_date.append(order)
        if n < len(bids_date):
            n = len(bids_date)
    if chart:
        if ascii:
            charset = u'ascii'
        else:
            charset = u'utf8'
        chart = AsciiChart(height=height, width=width, offset=4, placeholder=' {:10.2f} $', charset=charset)
        print("\n            Orderbook \n")
        chart.adapt_on_series(sumsum_asks[::-1] + sumsum_bids)
        chart.new_chart()
        chart.add_axis()
        y0 = chart._map_y(chart.minimum)
        y1 = chart._map_y(chart.maximum)
        chart._draw_v_line(y0 + 1, y1, int(chart.n / chart.skip / 2), line=chart.char_set["curve_vl_dot"])
        chart.add_curve(sumsum_asks[::-1] + sumsum_bids)
        print(str(chart))
        return
    for i in range(n):
        row = []
        if len(asks_date) > i:
            row.append(formatTimeString(asks_date[i]))
        elif show_date:
            row.append([""])
        if len(sumsum_asks) > i and not show_date:
            row.append("%.2f" % sumsum_asks[i])
        elif not show_date:
            row.append([""])
        if len(asks) > i:
            row.append(str(asks[i]))
        else:
            row.append([""])
        if len(bids_date) > i:
            row.append(formatTimeString(bids_date[i]))
        elif show_date:
            row.append([""])
        if len(sumsum_bids) > i and not show_date:
            row.append("%.2f" % sumsum_bids[i])
        elif not show_date:
            row.append([""])
        if len(bids) > i:
            row.append(str(bids[i]))
        else:
            row.append([""])
        t.add_row(row)
    print(t)


@cli.command()
@click.argument('amount', nargs=1)
@click.argument('asset', nargs=1)
@click.argument('price', nargs=1, required=False)
@click.option('--account', '-a', help='Buy with this account (defaults to "default_account")')
@click.option('--orderid', help='Set an orderid')
def buy(amount, asset, price, account, orderid):
    """Buy STEEM/HIVE or SBD/HBD from the internal market

        Limit buy price denoted in (SBD per STEEM or HBD per HIVE)
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if account is None:
        account = stm.config["default_account"]
    if asset == stm.backed_token_symbol:
        market = Market(base=Asset(stm.token_symbol), quote=Asset(stm.backed_token_symbol), blockchain_instance=stm)
    else:
        market = Market(base=Asset(stm.backed_token_symbol), quote=Asset(stm.token_symbol), blockchain_instance=stm)
    if price is None:
        orderbook = market.orderbook(limit=1, raw_data=False)
        if asset == stm.token_symbol and len(orderbook["bids"]) > 0:
            p = Price(orderbook["bids"][0]["base"], orderbook["bids"][0]["quote"], blockchain_instance=stm).invert()
            p_show = p
        elif len(orderbook["asks"]) > 0:
            p = Price(orderbook["asks"][0]["base"], orderbook["asks"][0]["quote"], blockchain_instance=stm).invert()
            p_show = p
        price_ok = click.prompt("Is the following Price ok: %s [y/n]" % (str(p_show)))
        if price_ok not in ["y", "ye", "yes"]:
            return
    else:
        p = Price(float(price), u"%s:%s" % (stm.backed_token_symbol, stm.token_symbol), blockchain_instance=stm)
    if not unlock_wallet(stm):
        return

    a = Amount(float(amount), asset, blockchain_instance=stm)
    acc = Account(account, blockchain_instance=stm)
    tx = market.buy(p, a, account=acc, orderid=orderid)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1)
@click.argument('asset', nargs=1)
@click.argument('price', nargs=1, required=False)
@click.option('--account', '-a', help='Sell with this account (defaults to "default_account")')
@click.option('--orderid', help='Set an orderid')
def sell(amount, asset, price, account, orderid):
    """Sell STEEM/HIVE or SBD/HBD from the internal market

        Limit sell price denoted in (SBD per STEEM) or (HBD per HIVE)
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if asset == stm.backed_token_symbol:
        market = Market(base=Asset(stm.token_symbol), quote=Asset(stm.backed_token_symbol), blockchain_instance=stm)
    else:
        market = Market(base=Asset(stm.backed_token_symbol), quote=Asset(stm.token_symbol), blockchain_instance=stm)
    if not account:
        account = stm.config["default_account"]
    if not price:
        orderbook = market.orderbook(limit=1, raw_data=False)
        if asset == stm.backed_token_symbol and len(orderbook["bids"]) > 0:
            p = Price(orderbook["bids"][0]["base"], orderbook["bids"][0]["quote"], blockchain_instance=stm).invert()
            p_show = p
        else:
            p = Price(orderbook["asks"][0]["base"], orderbook["asks"][0]["quote"], blockchain_instance=stm).invert()
            p_show = p
        price_ok = click.prompt("Is the following Price ok: %s [y/n]" % (str(p_show)))
        if price_ok not in ["y", "ye", "yes"]:
            return
    else:
        p = Price(float(price), u"%s:%s" % (stm.backed_token_symbol, stm.token_symbol), blockchain_instance=stm)
    if not unlock_wallet(stm):
        return
    a = Amount(float(amount), asset, blockchain_instance=stm)
    acc = Account(account, blockchain_instance=stm)
    tx = market.sell(p, a, account=acc, orderid=orderid)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('orderid', nargs=1)
@click.option('--account', '-a', help='Sell with this account (defaults to "default_account")')
def cancel(orderid, account):
    """Cancel order in the internal market"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    market = Market(blockchain_instance=stm)
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    tx = market.cancel(orderid, account=acc)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('account', nargs=1, required=False)
def openorders(account):
    """Show open orders"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    market = Market(blockchain_instance=stm)
    if not account:
        account = stm.config["default_account"]
    acc = Account(account, blockchain_instance=stm)
    openorders = market.accountopenorders(account=acc)
    t = PrettyTable(["Orderid", "Created", "Order", "Account"], hrules=0)
    t.align = "r"
    for order in openorders:
        t.add_row([order["orderid"],
                   formatTimeString(order["created"]),
                   str(order["order"]),
                   account])
    print(t)


@cli.command()
@click.argument('identifier', nargs=1)
@click.option('--account', '-a', help='Reblog as this user')
def reblog(identifier, account):
    """Reblog an existing post"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    post = Comment(identifier, blockchain_instance=stm)
    tx = post.resteem(account=acc)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('follow', nargs=1)
@click.option('--account', '-a', help='Follow from this account')
@click.option('--what', help='Follow these objects (defaults to ["blog"])', default=["blog"])
def follow(follow, account, what):
    """Follow another account"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if isinstance(what, str):
        what = [what]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    tx = acc.follow(follow, what=what)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('mute', nargs=1)
@click.option('--account', '-a', help='Mute from this account')
@click.option('--what', help='Mute these objects (defaults to ["ignore"])', default=["ignore"])
def mute(mute, account, what):
    """Mute another account"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if isinstance(what, str):
        what = [what]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    tx = acc.follow(mute, what=what)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('unfollow', nargs=1)
@click.option('--account', '-a', help='UnFollow/UnMute from this account')
def unfollow(unfollow, account):
    """Unfollow/Unmute another account"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    tx = acc.unfollow(unfollow)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.option('--witness', help='Witness name')
@click.option('--maximum_block_size', help='Max block size')
@click.option('--account_creation_fee', help='Account creation fee')
@click.option('--sbd_interest_rate', help='SBD interest rate in percent')
@click.option('--url', help='Witness URL')
@click.option('--signing_key', help='Signing Key')
def witnessupdate(witness, maximum_block_size, account_creation_fee, sbd_interest_rate, url, signing_key):
    """Change witness properties"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not witness:
        witness = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    witness = Witness(witness, blockchain_instance=stm)
    props = witness["props"]
    if account_creation_fee is not None:
        props["account_creation_fee"] = str(
            Amount("%.3f %s" % (float(account_creation_fee), stm.token_symbol), blockchain_instance=stm))
    if maximum_block_size is not None:
        props["maximum_block_size"] = int(maximum_block_size)
    if sbd_interest_rate is not None:
        props["sbd_interest_rate"] = int(float(sbd_interest_rate) * 100)
    tx = witness.update(signing_key or witness["signing_key"], url or witness["url"], props)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('witness', nargs=1)
def witnessdisable(witness):
    """Disable a witness"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not witness:
        witness = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    witness = Witness(witness, blockchain_instance=stm)
    if not witness.is_active:
        print("Cannot disable a disabled witness!")
        return
    props = witness["props"]
    tx = witness.update('STM1111111111111111111111111111111114T1Anm', witness["url"], props)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('witness', nargs=1)
@click.argument('signing_key', nargs=1)
def witnessenable(witness, signing_key):
    """Enable a witness"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not witness:
        witness = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    witness = Witness(witness, blockchain_instance=stm)
    props = witness["props"]
    tx = witness.update(signing_key, witness["url"], props)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('witness', nargs=1)
@click.argument('pub_signing_key', nargs=1)
@click.option('--maximum_block_size', help='Max block size', default=65536)
@click.option('--account_creation_fee', help='Account creation fee', default=0.1)
@click.option('--sbd_interest_rate', help='SBD interest rate in percent', default=0.0)
@click.option('--url', help='Witness URL', default="")
def witnesscreate(witness, pub_signing_key, maximum_block_size, account_creation_fee, sbd_interest_rate, url):
    """Create a witness"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not unlock_wallet(stm):
        return
    props = {
        "account_creation_fee":
            Amount("%.3f %s" % (float(account_creation_fee), stm.token_symbol), blockchain_instance=stm),
        "maximum_block_size":
            int(maximum_block_size),
        "sbd_interest_rate":
            int(sbd_interest_rate * 100)
    }

    tx = stm.witness_update(pub_signing_key, url, props, account=witness)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('witness', nargs=1)
@click.argument('wif', nargs=1)
@click.option('--account_creation_fee', help='Account creation fee (float)')
@click.option('--account_subsidy_budget', help='Account subisidy per block')
@click.option('--account_subsidy_decay', help='Per block decay of the account subsidy pool')
@click.option('--maximum_block_size', help='Max block size')
@click.option('--sbd_interest_rate', help='SBD interest rate in percent')
@click.option('--new_signing_key', help='Set new signing key')
@click.option('--url', help='Witness URL')
def witnessproperties(witness, wif, account_creation_fee, account_subsidy_budget, account_subsidy_decay, maximum_block_size, sbd_interest_rate, new_signing_key, url):
    """Update witness properties of witness WITNESS with the witness signing key WIF"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    # if not unlock_wallet(stm):
    #    return
    props = {}
    if account_creation_fee is not None:
        props["account_creation_fee"] = Amount("%.3f %s" % (float(account_creation_fee), stm.token_symbol), blockchain_instance=stm)
    if account_subsidy_budget is not None:
        props["account_subsidy_budget"] = int(account_subsidy_budget)
    if account_subsidy_decay is not None:
        props["account_subsidy_decay"] = int(account_subsidy_decay)
    if maximum_block_size is not None:
        props["maximum_block_size"] = int(maximum_block_size)
    if sbd_interest_rate is not None:
        props["sbd_interest_rate"] = int(sbd_interest_rate * 100)
    if new_signing_key is not None:
        props["new_signing_key"] = new_signing_key
    if url is not None:
        props["url"] = url

    tx = stm.witness_set_properties(wif, witness, props)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('witness', nargs=1)
@click.argument('wif', nargs=1, required=False)
@click.option('--base', '-b', help='Set base manually, when not set the base is automatically calculated.')
@click.option('--quote', '-q', help='Steem quote manually, when not set the base is automatically calculated.')
@click.option('--support-peg', help='Supports peg adjusting the quote, is overwritten by --set-quote!', is_flag=True, default=False)
def witnessfeed(witness, wif, base, quote, support_peg):
    """Publish price feed for a witness"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if wif is None:
        if not unlock_wallet(stm):
            return
    witness = Witness(witness, blockchain_instance=stm)
    market = Market(blockchain_instance=stm)
    old_base = witness["sbd_exchange_rate"]["base"]
    old_quote = witness["sbd_exchange_rate"]["quote"]
    last_published_price = Price(witness["sbd_exchange_rate"], blockchain_instance=stm)
    steem_usd = None
    hive_usd = None
    print("Old price %.3f (base: %s, quote %s)" % (float(last_published_price), old_base, old_quote))
    if quote is None and not support_peg:
        quote = Amount("1.000 %s" % stm.token_symbol, blockchain_instance=stm)
    elif quote is None and not stm.is_hive:
        latest_price = market.ticker()['latest']
        if steem_usd is None:
            steem_usd = market.steem_usd_implied()
        sbd_usd = float(latest_price.as_base(stm.backed_token_symbol)) * steem_usd
        quote = Amount(1. / sbd_usd, stm.token_symbol, blockchain_instance=stm)
    elif quote is None and stm.is_hive:
        latest_price = market.ticker()['latest']
        if hive_usd is None:
            hive_usd = market.hive_usd_implied()
        hbd_usd = float(latest_price.as_base(stm.backed_token_symbol)) * hive_usd
        quote = Amount(1. / hbd_usd, stm.token_symbol, blockchain_instance=stm)        
    else:
        if str(quote[-5:]).upper() == stm.token_symbol:
            quote = Amount(quote, blockchain_instance=stm)
        else:
            quote = Amount(quote, stm.token_symbol, blockchain_instance=stm)
    if base is None and not stm.is_hive:
        if steem_usd is None:
            steem_usd = market.steem_usd_implied()
        base = Amount(steem_usd, stm.backed_token_symbol, blockchain_instance=stm)
    elif base is None and stm.is_hive:
        if hive_usd is None:
            hive_usd = market.hive_usd_implied()
        base = Amount(hive_usd, stm.backed_token_symbol, blockchain_instance=stm)        
    else:
        if str(quote[-3:]).upper() == stm.backed_token_symbol:
            base = Amount(base, blockchain_instance=stm)
        else:
            base = Amount(base, stm.backed_token_symbol, blockchain_instance=stm)
    new_price = Price(base=base, quote=quote, blockchain_instance=stm)
    print("New price %.3f (base: %s, quote %s)" % (float(new_price), base, quote))
    if wif is not None:
        props = {"sbd_exchange_rate": new_price}
        tx = stm.witness_set_properties(wif, witness["owner"], props)
    else:
        tx = witness.feed_publish(base, quote=quote)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('witness', nargs=1)
def witness(witness):
    """ List witness information
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    witness = Witness(witness, blockchain_instance=stm)
    witness_json = witness.json()
    witness_schedule = stm.get_witness_schedule()
    config = stm.get_config()
    if "VIRTUAL_SCHEDULE_LAP_LENGTH2" in config:
        lap_length = int(config["VIRTUAL_SCHEDULE_LAP_LENGTH2"])
    elif "HIVE_VIRTUAL_SCHEDULE_LAP_LENGTH2" in config:
        lap_length = int(config["HIVE_VIRTUAL_SCHEDULE_LAP_LENGTH2"])
    else:
        lap_length = int(config["STEEM_VIRTUAL_SCHEDULE_LAP_LENGTH2"])
    rank = 0
    active_rank = 0
    found = False
    witnesses = WitnessesRankedByVote(limit=250, blockchain_instance=stm)
    vote_sum = witnesses.get_votes_sum()
    for w in witnesses:
        rank += 1
        if w.is_active:
            active_rank += 1
        if w["owner"] == witness["owner"]:
            found = True
            break
    virtual_time_to_block_num = int(witness_schedule["num_scheduled_witnesses"]) / (lap_length / (vote_sum + 1))
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    for key in sorted(witness_json):
        value = witness_json[key]
        if key in ["props", "sbd_exchange_rate"]:
            value = json.dumps(value, indent=4)
        t.add_row([key, value])
    if found:
        t.add_row(["rank", rank])
        t.add_row(["active_rank", active_rank])
    virtual_diff = int(witness_json["virtual_scheduled_time"]) - int(witness_schedule['current_virtual_time'])
    block_diff_est = virtual_diff * virtual_time_to_block_num
    if active_rank > 20:
        t.add_row(["virtual_time_diff", virtual_diff])
        t.add_row(["block_diff_est", int(block_diff_est)])
        next_block_s = int(block_diff_est) * 3
        next_block_min = next_block_s / 60
        next_block_h = next_block_min / 60
        next_block_d = next_block_h / 24
        time_diff_est = ""
        if next_block_d > 1:
            time_diff_est = "%.2f days" % next_block_d
        elif next_block_h > 1:
            time_diff_est = "%.2f hours" % next_block_h
        elif next_block_min > 1:
            time_diff_est = "%.2f minutes" % next_block_min
        else:
            time_diff_est = "%.2f seconds" % next_block_s
        t.add_row(["time_diff_est", time_diff_est])
    print(t)


@cli.command()
@click.argument('account', nargs=1, required=False)
@click.option('--limit', help='How many witnesses should be shown', default=100)
def witnesses(account, limit):
    """ List witnesses
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if account:
        account = Account(account, blockchain_instance=stm)
        account_name = account["name"]
        if account["proxy"] != "":
            account_name = account["proxy"]
            account_type = "Proxy"
        else:
            account_type = "Account"
        witnesses = WitnessesVotedByAccount(account_name, blockchain_instance=stm)
        print("%s: @%s (%d of 30)" % (account_type, account_name, len(witnesses)))
    else:
        witnesses = WitnessesRankedByVote(limit=limit, blockchain_instance=stm)
    witnesses.printAsTable()


@cli.command()
@click.argument('account', nargs=1, required=False)
@click.option('--direction', default=None, help="in or out")
@click.option('--outgoing', '-o', help='Show outgoing votes', is_flag=True, default=False)
@click.option('--incoming', '-i', help='Show incoming votes', is_flag=True, default=False)
@click.option('--days', '-d', default=2., help="Limit shown vote history by this amount of days (default: 2)")
@click.option('--export', '-e', default=None, help="Export results to TXT-file")
def votes(account, direction, outgoing, incoming, days, export):
    """ List outgoing/incoming account votes
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if direction is None and not incoming and not outgoing:
        direction = "in"
    utc = pytz.timezone('UTC')
    limit_time = utc.localize(datetime.utcnow()) - timedelta(days=days)
    out_votes_str = ""
    in_votes_str = ""
    if direction == "out" or outgoing:
        votes = AccountVotes(account, start=limit_time, blockchain_instance=stm)
        out_votes_str = votes.printAsTable(start=limit_time, return_str=True)
    if direction == "in" or incoming:
        account = Account(account, blockchain_instance=stm)
        votes_list = []
        for v in account.history(start=limit_time, only_ops=["vote"]):
            vote = Vote(v, blockchain_instance=stm)
            vote.refresh()
            votes_list.append(vote)
        votes = ActiveVotes(votes_list, blockchain_instance=stm)
        in_votes_str = votes.printAsTable(votee=account["name"], return_str=True)
    if export:
        with open(export, 'w') as w:
            w.write(out_votes_str)
            w.write("\n")
            w.write(in_votes_str)
    else:
        print(out_votes_str)
        print(in_votes_str)


@cli.command()
@click.argument('authorperm', nargs=1, required=False)
@click.option('--account', '-a', help='Show only curation for this account')
@click.option('--limit', '-m', help='Show only the first minutes')
@click.option('--min-vote', '-v', help='Show only votes higher than the given value')
@click.option('--max-vote', '-w', help='Show only votes lower than the given value')
@click.option('--min-performance', '-x', help='Show only votes with performance higher than the given value in HBD/SBD')
@click.option('--max-performance', '-y', help='Show only votes with performance lower than the given value in HBD/SBD')
@click.option('--payout', default=None, help="Show the curation for a potential payout in SBD as float")
@click.option('--export', '-e', default=None, help="Export results to HTML-file")
@click.option('--short', '-s', is_flag=True, default=False, help="Show only Curation without sum")
@click.option('--length', '-l', help='Limits the permlink character length', default=None)
@click.option('--permlink', '-p', help='Show the permlink for each entry', is_flag=True, default=False)
@click.option('--title', '-t', help='Show the title for each entry', is_flag=True, default=False)
@click.option('--days', '-d', default=7., help="Limit shown rewards by this amount of days (default: 7), max is 7 days.")
def curation(authorperm, account, limit, min_vote, max_vote, min_performance, max_performance, payout, export, short, length, permlink, title, days):
    """ Lists curation rewards of all votes for authorperm

        When authorperm is empty or "all", the curation rewards
        for all account votes are shown.

        authorperm can also be a number. e.g. 5 is equivalent to
        the fifth account vote in the given time duration (default is 7 days)

    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    SP_symbol = "SP"
    if stm.is_hive:
        SP_symbol = "HP"
    if authorperm is None:
        authorperm = 'all'
    if account is None and authorperm != 'all':
        show_all_voter = True
    else:
        show_all_voter = False
    if authorperm == 'all' or authorperm.isdigit():
        if not account:
            account = stm.config["default_account"]
        utc = pytz.timezone('UTC')
        limit_time = utc.localize(datetime.utcnow()) - timedelta(days=7)
        votes = AccountVotes(account, start=limit_time, blockchain_instance=stm)
        authorperm_list = [vote.authorperm for vote in votes]
        if authorperm.isdigit():
            if len(authorperm_list) < int(authorperm):
                raise ValueError("Authorperm id must be lower than %d" % (len(authorperm_list) + 1))
            authorperm_list = [authorperm_list[int(authorperm) - 1]]
            all_posts = False
        else:
            all_posts = True
    else:
        authorperm_list = [authorperm]
        all_posts = False
    if (all_posts) and permlink:
        t = PrettyTable(["Author", "permlink", "Voting time", "Vote", "Early vote loss", "Curation", "Performance"])
        t.align = "l"
    elif (all_posts) and title:
        t = PrettyTable(["Author", "permlink", "Voting time", "Vote", "Early vote loss", "Curation", "Performance"])
        t.align = "l"
    elif all_posts:
        t = PrettyTable(["Author", "Voting time", "Vote", "Early vote loss", "Curation", "Performance"])
        t.align = "l"
    elif (export) and permlink:
        t = PrettyTable(["Author", "permlink", "Voter", "Voting time", "Vote", "Early vote loss", "Curation", "Performance"])
        t.align = "l"
    elif (export) and title:
        t = PrettyTable(["Author", "permlink", "Voter", "Voting time", "Vote", "Early vote loss", "Curation", "Performance"])
        t.align = "l"
    elif export:
        t = PrettyTable(["Author", "Voter", "Voting time", "Vote", "Early vote loss", "Curation", "Performance"])
        t.align = "l"
    else:
        t = PrettyTable(["Voter", "Voting time", "Vote", "Early vote loss", "Curation", "Performance"])
        t.align = "l"
    index = 0
    for authorperm in authorperm_list:
        index += 1
        comment = Comment(authorperm, blockchain_instance=stm)
        if payout is not None and comment.is_pending():
            payout = float(payout)
        elif payout is not None:
            payout = None
        curation_rewards_SBD = comment.get_curation_rewards(pending_payout_SBD=True, pending_payout_value=payout)
        curation_rewards_SP = comment.get_curation_rewards(pending_payout_SBD=False, pending_payout_value=payout)
        rows = []
        sum_curation = [0, 0, 0, 0]
        max_curation = [0, 0, 0, 0, 0, 0]
        highest_vote = [0, 0, 0, 0, 0, 0]
        for vote in comment.get_votes():
            vote_time = vote["time"]
            
            vote_SBD = stm.rshares_to_sbd(int(vote["rshares"]))
            curation_SBD = curation_rewards_SBD["active_votes"][vote["voter"]]
            curation_SP = curation_rewards_SP["active_votes"][vote["voter"]]
            if vote_SBD > 0:
                penalty = ((comment.get_curation_penalty(vote_time=vote_time)) * vote_SBD)
                performance = (float(curation_SBD) / vote_SBD * 100)
            else:
                performance = 0
                penalty = 0
            vote_befor_min = (((vote_time) - comment["created"]).total_seconds() / 60)
            sum_curation[0] += vote_SBD
            sum_curation[1] += penalty
            sum_curation[2] += float(curation_SP)
            sum_curation[3] += float(curation_SBD)
            row = [vote["voter"],
                   vote_befor_min,
                   vote_SBD,
                   penalty,
                   float(curation_SP),
                   performance]
            

            rows.append(row)
        sortedList = sorted(rows, key=lambda row: (row[1]), reverse=False)
        new_row = []
        new_row2 = []
        voter = []
        voter2 = []
        if (all_posts or export) and permlink:
            if length:
                new_row = [comment.author, comment.permlink[:int(length)]]
            else:
                new_row = [comment.author, comment.permlink]
            new_row2 = ["", ""]
        elif (all_posts or export) and title:
            if length:
                new_row = [comment.author, comment.title[:int(length)]]
            else:
                new_row = [comment.author, comment.title]
            new_row2 = ["", ""]
        elif (all_posts or export):
            new_row = [comment.author]
            new_row2 = [""]
        if not all_posts:
            voter = [""]
            voter2 = [""]
        found_voter = False
        for row in sortedList:
            if limit is not None and row[1] > float(limit):
                continue
            if min_vote is not None and float(row[2]) < float(min_vote):
                continue
            if max_vote is not None and float(row[2]) > float(max_vote):
                continue
            if min_performance is not None and float(row[5]) < float(min_performance):
                continue
            if max_performance is not None and float(row[5]) > float(max_performance):
                continue
            if row[-1] > max_curation[-1]:
                max_curation = row
            if row[2] > highest_vote[2]:
                highest_vote = row            
            if show_all_voter or account == row[0]:
                if not all_posts:
                    voter = [row[0]]
                if all_posts:
                    new_row[0] = "%d. %s" % (index, comment.author)
                if not found_voter:
                    found_voter = True
                t.add_row(new_row + voter + ["%.1f min" % row[1],
                                             "%.3f %s" % (float(row[2]), stm.backed_token_symbol),
                                             "%.3f %s" % (float(row[3]), stm.backed_token_symbol),
                                             "%.3f %s" % (row[4], SP_symbol),
                                             "%.1f %%" % (row[5])])
                if len(authorperm_list) == 1:
                    new_row = new_row2
        if not short and found_voter:
            t.add_row(new_row2 + voter2 + ["", "", "", "", ""])
            if sum_curation[0] > 0:
                curation_sum_percentage = sum_curation[3] / sum_curation[0] * 100
            else:
                curation_sum_percentage = 0
            sum_line = new_row2 + voter2
            sum_line[-1] = "High. vote"

            t.add_row(sum_line + ["%.1f min" % highest_vote[1],
                                  "%.3f %s" % (float(highest_vote[2]), stm.backed_token_symbol),
                                  "%.3f %s" % (float(highest_vote[3]), stm.backed_token_symbol),
                                  "%.3f %s" % (highest_vote[4], SP_symbol),
                                  "%.1f %%" % (highest_vote[5])])
            sum_line[-1] = "High. Cur."
            t.add_row(sum_line + ["%.1f min" % max_curation[1],
                                  "%.3f %s" % (float(max_curation[2]), stm.backed_token_symbol),
                                  "%.3f %s" % (float(max_curation[3]), stm.backed_token_symbol),
                                  "%.3f %s" % (max_curation[4], SP_symbol),
                                  "%.1f %%" % (max_curation[5])])
            sum_line[-1] = "Sum"
            t.add_row(sum_line + ["-",
                                  "%.3f %s" % (sum_curation[0], stm.backed_token_symbol),
                                  "%.3f %s" % (sum_curation[1], stm.backed_token_symbol),
                                  "%.3f %s" % (sum_curation[2], SP_symbol),
                                  "%.2f %%" % curation_sum_percentage])
            if all_posts or export:
                t.add_row(new_row2 + voter2 + ["-", "-", "-", "-", "-"])
        if not (all_posts or export):
            print("curation for %s" % (authorperm))
            print(t)
    if export:
        with open(export, 'w') as w:
            w.write(str(t.get_html_string()))
    elif all_posts:
        print("curation for @%s" % account)
        print(t)


@cli.command()
@click.argument('accounts', nargs=-1, required=False)
@click.option('--only-sum', '-s', help='Show only the sum', is_flag=True, default=False)
@click.option('--post', '-p', help='Show post payout', is_flag=True, default=False)
@click.option('--comment', '-c', help='Show comments payout', is_flag=True, default=False)
@click.option('--curation', '-v', help='Shows  curation', is_flag=True, default=False)
@click.option('--length', '-l', help='Limits the permlink character length', default=None)
@click.option('--author', '-a', help='Show the author for each entry', is_flag=True, default=False)
@click.option('--permlink', '-e', help='Show the permlink for each entry', is_flag=True, default=False)
@click.option('--title', '-t', help='Show the title for each entry', is_flag=True, default=False)
@click.option('--days', '-d', default=7., help="Limit shown rewards by this amount of days (default: 7)")
def rewards(accounts, only_sum, post, comment, curation, length, author, permlink, title, days):
    """ Lists received rewards
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not accounts:
        accounts = [stm.config["default_account"]]
    if not comment and not curation and not post:
        post = True
        permlink = True
    if days < 0:
        days = 1

    utc = pytz.timezone('UTC')
    now = utc.localize(datetime.utcnow())
    limit_time = now - timedelta(days=days)
    for account in accounts:
        sum_reward = [0, 0, 0, 0, 0]
        account = Account(account, blockchain_instance=stm)
        median_price = Price(stm.get_current_median_history(), blockchain_instance=stm)
        m = Market(blockchain_instance=stm)
        latest = m.ticker()["latest"]
        if author and permlink:
            t = PrettyTable(["Author", "Permlink", "Payout", stm.backed_token_symbol, "SP + STEEM", "Liquid USD", "Invested USD"])
        elif author and title:
                t = PrettyTable(["Author", "Title", "Payout", stm.backed_token_symbol, "SP + STEEM", "Liquid USD", "Invested USD"])
        elif author:
            t = PrettyTable(["Author", "Payout", stm.backed_token_symbol, "SP + STEEM", "Liquid USD", "Invested USD"])
        elif not author and permlink:
            t = PrettyTable(["Permlink", "Payout", stm.backed_token_symbol, "SP + STEEM", "Liquid USD", "Invested USD"])
        elif not author and title:
            t = PrettyTable(["Title", "Payout", stm.backed_token_symbol, "SP + STEEM", "Liquid USD", "Invested USD"])
        else:
            t = PrettyTable(["Received", stm.backed_token_symbol, "SP + STEEM", "Liquid USD", "Invested USD"])
        t.align = "l"
        rows = []
        start_op = account.estimate_virtual_op_num(limit_time)
        if start_op > 0:
            start_op -= 1
        only_ops = ['author_reward', 'curation_reward']
        progress_length = (account.virtual_op_count() - start_op) / 1000
        with click.progressbar(account.history(start=start_op, use_block_num=False, only_ops=only_ops), length=progress_length) as comment_hist:
            for v in comment_hist:
                if not curation and v["type"] == "curation_reward":
                    continue
                if not post and not comment and v["type"] == "author_reward":
                    continue
                if v["type"] == "author_reward":
                    c = Comment(v, blockchain_instance=stm)
                    try:
                        c.refresh()
                    except exceptions.ContentDoesNotExistsException:
                        continue
                    if not post and not c.is_comment():
                        continue
                    if not comment and c.is_comment():
                        continue
                    payout_SBD = Amount(v["sbd_payout"], blockchain_instance=stm)
                    payout_STEEM = Amount(v["steem_payout"], blockchain_instance=stm)
                    sum_reward[0] += float(payout_SBD)
                    sum_reward[1] += float(payout_STEEM)
                    payout_SP = stm.vests_to_sp(Amount(v["vesting_payout"], blockchain_instance=stm))
                    sum_reward[2] += float(payout_SP)
                    liquid_USD = float(payout_SBD) / float(latest) * float(median_price) + float(payout_STEEM) * float(median_price)
                    sum_reward[3] += liquid_USD
                    invested_USD = float(payout_SP) * float(median_price)
                    sum_reward[4] += invested_USD
                    if c.is_comment():
                        permlink_row = c.parent_permlink
                    else:
                        if title:
                            permlink_row = c.title
                        else:
                            permlink_row = c.permlink
                    rows.append([c["author"],
                                 permlink_row,
                                 ((now - formatTimeString(v["timestamp"])).total_seconds() / 60 / 60 / 24),
                                 (payout_SBD),
                                 (payout_STEEM),
                                 (payout_SP),
                                 (liquid_USD),
                                 (invested_USD)])
                elif v["type"] == "curation_reward":
                    reward = Amount(v["reward"], blockchain_instance=stm)
                    payout_SP = stm.vests_to_sp(reward)
                    liquid_USD = 0
                    invested_USD = float(payout_SP) * float(median_price)
                    sum_reward[2] += float(payout_SP)
                    sum_reward[4] += invested_USD
                    if title:
                        c = Comment(construct_authorperm(v["comment_author"], v["comment_permlink"]), blockchain_instance=stm)
                        permlink_row = c.title
                    else:
                        permlink_row = v["comment_permlink"]
                    rows.append([v["comment_author"],
                                 permlink_row,
                                 ((now - formatTimeString(v["timestamp"])).total_seconds() / 60 / 60 / 24),
                                 0.000,
                                 0.000,
                                 payout_SP,
                                 (liquid_USD),
                                 (invested_USD)])
        sortedList = sorted(rows, key=lambda row: (row[2]), reverse=False)
        if only_sum:
            sortedList = []
        for row in sortedList:
            if length:
                permlink_row = row[1][:int(length)]
            else:
                permlink_row = row[1]
            if author and (permlink or title):
                t.add_row([row[0],
                           permlink_row,
                           "%.1f days" % row[2],
                           "%.3f" % float(row[3]),
                           "%.3f" % (float(row[4]) + float(row[5])),
                           "%.2f $" % (row[6]),
                           "%.2f $" % (row[7])])
            elif author and not (permlink or title):
                t.add_row([row[0],
                           "%.1f days" % row[2],
                           "%.3f" % float(row[3]),
                           "%.3f" % (float(row[4]) + float(row[5])),
                           "%.2f $" % (row[5]),
                           "%.2f $" % (row[6])])
            elif not author and (permlink or title):
                t.add_row([permlink_row,
                           "%.1f days" % row[2],
                           "%.3f" % float(row[3]),
                           "%.3f" % (float(row[4]) + float(row[5])),
                           "%.2f $" % (row[5]),
                           "%.2f $" % (row[6])])
            else:
                t.add_row(["%.1f days" % row[2],
                           "%.3f" % float(row[3]),
                           "%.3f" % (float(row[4]) + float(row[5])),
                           "%.2f $" % (row[5]),
                           "%.2f $" % (row[6])])

        if author and (permlink or title):
            if not only_sum:
                t.add_row(["", "", "", "", "", "", ""])
            t.add_row(["Sum",
                       "-",
                       "-",
                       "%.2f %s" % (sum_reward[0], stm.backed_token_symbol),
                       "%.2f SP" % (sum_reward[1] + sum_reward[2]),
                       "%.2f $" % (sum_reward[3]),
                       "%.2f $" % (sum_reward[4])])
        elif not author and not (permlink or title):
            t.add_row(["", "", "", "", ""])
            t.add_row(["Sum",
                       "%.2f %s" % (sum_reward[0], stm.backed_token_symbol),
                       "%.2f SP" % (sum_reward[1] + sum_reward[2]),
                       "%.2f $" % (sum_reward[2]),
                       "%.2f $" % (sum_reward[3])])
        else:
            t.add_row(["", "", "", "", "", ""])
            t.add_row(["Sum",
                       "-",
                       "%.2f %s" % (sum_reward[0], stm.backed_token_symbol),
                       "%.2f SP" % (sum_reward[1] + sum_reward[2]),
                       "%.2f $" % (sum_reward[3]),
                       "%.2f $" % (sum_reward[4])])
        message = "\nShowing "
        if post:
            if comment + curation == 0:
                message += "post "
            elif comment + curation == 1:
                message += "post and "
            else:
                message += "post, "
        if comment:
            if curation == 0:
                message += "comment "
            else:
                message += "comment and "
        if curation:
            message += "curation "
        message += "rewards for @%s" % account.name
        print(message)
        print(t)


@cli.command()
@click.argument('accounts', nargs=-1, required=False)
@click.option('--only-sum', '-s', help='Show only the sum', is_flag=True, default=False)
@click.option('--post', '-p', help='Show pending post payout', is_flag=True, default=False)
@click.option('--comment', '-c', help='Show pending comments payout', is_flag=True, default=False)
@click.option('--curation', '-v', help='Shows  pending curation', is_flag=True, default=False)
@click.option('--length', '-l', help='Limits the permlink character length', default=None)
@click.option('--author', '-a', help='Show the author for each entry', is_flag=True, default=False)
@click.option('--permlink', '-e', help='Show the permlink for each entry', is_flag=True, default=False)
@click.option('--title', '-t', help='Show the title for each entry', is_flag=True, default=False)
@click.option('--days', '-d', default=7., help="Limit shown rewards by this amount of days (default: 7), max is 7 days.")
@click.option('--from', '-f', '_from', default=0., help="Start day from which on rewards are shown (default: 0), max is 7 days.")
def pending(accounts, only_sum, post, comment, curation, length, author, permlink, title, days, _from):
    """ Lists pending rewards
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not accounts:
        accounts = [stm.config["default_account"]]
    if not comment and not curation and not post:
        post = True
        permlink = True
    if days < 0:
        days = 1
    if days > 7:
        days = 7
    if _from < 0:
        _from = 0
    if _from > 7:
        _from = 7
    if _from + days > 7:
        days = 7 - _from
    sp_symbol = "SP"
    if stm.is_hive:
        sp_symbol = "HP"

    utc = pytz.timezone('UTC')
    max_limit_time = utc.localize(datetime.utcnow()) - timedelta(days=7)
    limit_time = utc.localize(datetime.utcnow()) - timedelta(days=_from + days)
    start_time = utc.localize(datetime.utcnow()) - timedelta(days=_from)
    for account in accounts:
        sum_reward = [0, 0, 0, 0]
        account = Account(account, blockchain_instance=stm)
        median_price = Price(stm.get_current_median_history(), blockchain_instance=stm)
        m = Market(blockchain_instance=stm)
        latest = m.ticker()["latest"]
        if author and permlink:
            t = PrettyTable(["Author", "Permlink", "Cashout", stm.backed_token_symbol, sp_symbol, "Liquid USD", "Invested USD"])
        elif author and title:
            t = PrettyTable(["Author", "Title", "Cashout", stm.backed_token_symbol, sp_symbol, "Liquid USD", "Invested USD"])
        elif author:
            t = PrettyTable(["Author", "Cashout", stm.backed_token_symbol, sp_symbol, "Liquid USD", "Invested USD"])
        elif not author and permlink:
            t = PrettyTable(["Permlink", "Cashout", stm.backed_token_symbol, sp_symbol, "Liquid USD", "Invested USD"])
        elif not author and title:
            t = PrettyTable(["Title", "Cashout", stm.backed_token_symbol, sp_symbol, "Liquid USD", "Invested USD"])
        else:
            t = PrettyTable(["Cashout", stm.backed_token_symbol, sp_symbol, "Liquid USD", "Invested USD"])
        t.align = "l"
        rows = []
        c_list = {}
        start_op = account.estimate_virtual_op_num(limit_time)
        stop_op = account.estimate_virtual_op_num(start_time)
        if start_op > 0:
            start_op -= 1
        progress_length = (stop_op - start_op) / 1000
        with click.progressbar(map(Comment, account.history(start=start_op, stop=stop_op, use_block_num=False, only_ops=["comment"])), length=progress_length) as comment_hist:
            for v in comment_hist:
                try:
                    v.refresh()
                except exceptions.ContentDoesNotExistsException:
                    continue
                author_reward = v.get_author_rewards()
                if float(author_reward["total_payout_SBD"]) < 0.001:
                    continue
                if v.permlink in c_list:
                    continue
                c_list[v.permlink] = 1
                if not v.is_pending():
                    continue
                if not post and not v.is_comment():
                    continue
                if not comment and v.is_comment():
                    continue
                if v["author"] != account["name"]:
                    continue
                payout_SBD = author_reward["payout_SBD"]
                sum_reward[0] += float(payout_SBD)
                payout_SP = author_reward["payout_SP"]
                sum_reward[1] += float(payout_SP)
                liquid_USD = float(author_reward["payout_SBD"]) / float(latest) * float(median_price)
                sum_reward[2] += liquid_USD
                invested_USD = float(author_reward["payout_SP"]) * float(median_price)
                sum_reward[3] += invested_USD
                if v.is_comment():
                    permlink_row = v.permlink
                else:
                    if title:
                        permlink_row = v.title
                    else:
                        permlink_row = v.permlink
                rows.append([v["author"],
                             permlink_row,
                             ((v["created"] - max_limit_time).total_seconds() / 60 / 60 / 24),
                             (payout_SBD),
                             (payout_SP),
                             (liquid_USD),
                             (invested_USD)])
        if curation:
            votes = AccountVotes(account, start=limit_time, stop=start_time, blockchain_instance=stm)
            for vote in votes:
                authorperm = construct_authorperm(vote["author"], vote["permlink"])
                c = Comment(authorperm, blockchain_instance=stm)
                rewards = c.get_curation_rewards()
                if not rewards["pending_rewards"]:
                    continue
                days_to_payout = ((c["created"] - max_limit_time).total_seconds() / 60 / 60 / 24)
                if days_to_payout < 0:
                    continue
                payout_SP = rewards["active_votes"][account["name"]]
                liquid_USD = 0
                invested_USD = float(payout_SP) * float(median_price)
                sum_reward[1] += float(payout_SP)
                sum_reward[3] += invested_USD
                if title:
                    permlink_row = c.title
                else:
                    permlink_row = c.permlink
                rows.append([c["author"],
                             permlink_row,
                             days_to_payout,
                             0.000,
                             payout_SP,
                             (liquid_USD),
                             (invested_USD)])
        sortedList = sorted(rows, key=lambda row: (row[2]), reverse=True)
        if only_sum:
            sortedList = []
        for row in sortedList:
            if length:
                permlink_row = row[1][:int(length)]
            else:
                permlink_row = row[1]
            if author and (permlink or title):
                t.add_row([row[0],
                           permlink_row,
                           "%.1f days" % row[2],
                           "%.3f" % float(row[3]),
                           "%.3f" % float(row[4]),
                           "%.2f $" % (row[5]),
                           "%.2f $" % (row[6])])
            elif author and not (permlink or title):
                t.add_row([row[0],
                           "%.1f days" % row[2],
                           "%.3f" % float(row[3]),
                           "%.3f" % float(row[4]),
                           "%.2f $" % (row[5]),
                           "%.2f $" % (row[6])])
            elif not author and (permlink or title):
                t.add_row([permlink_row,
                           "%.1f days" % row[2],
                           "%.3f" % float(row[3]),
                           "%.3f" % float(row[4]),
                           "%.2f $" % (row[5]),
                           "%.2f $" % (row[6])])
            else:
                t.add_row(["%.1f days" % row[2],
                           "%.3f" % float(row[3]),
                           "%.3f" % float(row[4]),
                           "%.2f $" % (row[5]),
                           "%.2f $" % (row[6])])

        if author and (permlink or title):
            if not only_sum:
                t.add_row(["", "", "", "", "", "", ""])
            t.add_row(["Sum",
                       "-",
                       "-",
                       "%.2f %s" % (sum_reward[0], stm.backed_token_symbol),
                       "%.2f %s" % (sum_reward[1], sp_symbol),
                       "%.2f $" % (sum_reward[2]),
                       "%.2f $" % (sum_reward[3])])
        elif not author and not (permlink or title):
            t.add_row(["", "", "", "", ""])
            t.add_row(["Sum",
                       "%.2f %s" % (sum_reward[0], stm.backed_token_symbol),
                       "%.2f %s" % (sum_reward[1], sp_symbol),
                       "%.2f $" % (sum_reward[2]),
                       "%.2f $" % (sum_reward[3])])
        else:
            t.add_row(["", "", "", "", "", ""])
            t.add_row(["Sum",
                       "-",
                       "%.2f %s" % (sum_reward[0], stm.backed_token_symbol),
                       "%.2f %s" % (sum_reward[1], sp_symbol),
                       "%.2f $" % (sum_reward[2]),
                       "%.2f $" % (sum_reward[3])])
        message = "\nShowing pending "
        if post:
            if comment + curation == 0:
                message += "post "
            elif comment + curation == 1:
                message += "post and "
            else:
                message += "post, "
        if comment:
            if curation == 0:
                message += "comment "
            else:
                message += "comment and "
        if curation:
            message += "curation "
        message += "rewards for @%s" % account.name
        print(message)
        print(t)


@cli.command()
@click.argument('account', nargs=1, required=False)
@click.option('--reward_steem', help='Amount of STEEM/HIVE you would like to claim', default=0)
@click.option('--reward_sbd', help='Amount of SBD/HBD you would like to claim', default=0)
@click.option('--reward_vests', help='Amount of VESTS you would like to claim', default=0)
@click.option('--claim_all_steem', help='Claim all STEEM/HIVE, overwrites reward_steem', is_flag=True)
@click.option('--claim_all_sbd', help='Claim all SBD/HBD, overwrites reward_sbd', is_flag=True)
@click.option('--claim_all_vests', help='Claim all VESTS, overwrites reward_vests', is_flag=True)
def claimreward(account, reward_steem, reward_sbd, reward_vests, claim_all_steem, claim_all_sbd, claim_all_vests):
    """Claim reward balances

        By default, this will claim ``all`` outstanding balances.
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    acc = Account(account, blockchain_instance=stm)
    r = acc.balances["rewards"]
    if len(r) == 3 and r[0].amount + r[1].amount + r[2].amount == 0:
        print("Nothing to claim.")
        return
    elif len(r) == 2 and r[0].amount + r[1].amount:
        print("Nothing to claim.")
        return
    if not unlock_wallet(stm):
        return
    if claim_all_steem:
        reward_steem = r[0]
    if claim_all_sbd:
        reward_sbd = r[1]
    if claim_all_vests:
        reward_vests = r[2]

    tx = acc.claim_reward_balance(reward_steem, reward_sbd, reward_vests)
    if stm.unsigned and stm.nobroadcast and stm.steemconnect is not None:
        tx = stm.steemconnect.url_from_tx(tx)
    elif stm.unsigned and stm.nobroadcast and stm.hivesigner is not None:
        tx = stm.hivesigner.url_from_tx(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('jsonid', nargs=1)
@click.argument('json_data', nargs=-1)
@click.option('--account', '-a', help='The account which broadcasts the custom_json')
@click.option('--active', '-t', help='When set, the active key is used for broadcasting', is_flag=True, default=False)
def customjson(jsonid, json_data, account, active):
    """Broadcasts a custom json
    
        First parameter is the cusom json id, the second field is a json file or a json key value combination
        e.g. beempy customjson -a holger80 dw-heist username holger80 amount 100
    """
    if jsonid is None:
        print("First argument must be the custom_json id")
    if json_data is None:
        print("Second argument must be the json_data, can be a string or a file name.")
    if isinstance(json_data, tuple) and len(json_data) > 1:
        data = {}
        key = None
        for j in json_data:
            if key is None:
                key = j
            else:
                data[key] = j
                key = None
        if key is not None:
            print("Value is missing for key: %s" % key)
            return
    else:
        try:
            with open(json_data[0], 'r') as f:
                data = json.load(f)            
        except:
            print("%s is not a valid file or json field" % json_data)
            return
    for d in data:
        if isinstance(data[d], str) and data[d][0] == "{" and data[d][-1] == "}":
            field = {}
            for keyvalue in data[d][1:-1].split(","):
                key = keyvalue.split(":")[0].strip()
                value = keyvalue.split(":")[1].strip()
                if jsonid == "ssc-mainnet1" and key == "quantity":
                    value = float(value)
                field[key] = value
            data[d] = field
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, blockchain_instance=stm)
    if active:
        tx = stm.custom_json(jsonid, data, required_auths=[account])
    else:
        tx = stm.custom_json(jsonid, data, required_posting_auths=[account])
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('blocknumber', nargs=1, required=False)
@click.option('--trx', '-t', help='Show only one transaction number', default=None)
@click.option('--use-api', '-u', help='Uses the get_potential_signatures api call', is_flag=True, default=False)
def verify(blocknumber, trx, use_api):
    """Returns the public signing keys for a block"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    b = Blockchain(blockchain_instance=stm)
    i = 0
    if not blocknumber:
        blocknumber = b.get_current_block_num()
    try:
        int(blocknumber)
        block = Block(blocknumber, blockchain_instance=stm)
        if trx is not None:
            i = int(trx)
            trxs = [block.json_transactions[int(trx)]]
        else:
            trxs = block.json_transactions
    except Exception:
        trxs = [b.get_transaction(blocknumber)]
        blocknumber = trxs[0]["block_num"]
    wallet = Wallet(blockchain_instance=stm)
    t = PrettyTable(["trx", "Signer key", "Account"])
    t.align = "l"
    if not use_api:
        from beembase.signedtransactions import Signed_Transaction
    for trx in trxs:
        if not use_api:
            # trx is now identical to the output of get_transaction
            # This is just for testing porpuse
            if True:
                signed_tx = Signed_Transaction(trx.copy())
            else:
                tx = b.get_transaction(trx["transaction_id"])
                signed_tx = Signed_Transaction(tx)
            public_keys = []
            for key in signed_tx.verify(chain=stm.chain_params, recover_parameter=True):
                public_keys.append(format(Base58(key, prefix=stm.prefix), stm.prefix))
        else:
            tx = TransactionBuilder(tx=trx, blockchain_instance=stm)
            public_keys = tx.get_potential_signatures()
        accounts = []
        empty_public_keys = []
        for key in public_keys:
            account = wallet.getAccountFromPublicKey(key)
            if account is None:
                empty_public_keys.append(key)
            else:
                accounts.append(account)
        new_public_keys = []
        for key in public_keys:
            if key not in empty_public_keys or use_api:
                new_public_keys.append(key)
        if len(new_public_keys) == 0:
            for key in public_keys:
                new_public_keys.append(key)            
        if isinstance(new_public_keys, list) and len(new_public_keys) == 1:
            new_public_keys = new_public_keys[0]
        else:
            new_public_keys = json.dumps(new_public_keys, indent=4)
        if isinstance(accounts, list) and len(accounts) == 1:
            accounts = accounts[0]
        else:
            accounts = json.dumps(accounts, indent=4)
        t.add_row(["%d" % i, new_public_keys, accounts])
        i += 1
    print(t)


@cli.command()
@click.argument('objects', nargs=-1)
def info(objects):
    """ Show basic blockchain info

        General information about the blockchain, a block, an account,
        a post/comment and a public key
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not objects:
        t = PrettyTable(["Key", "Value"])
        t.align = "l"
        info = stm.get_dynamic_global_properties()
        median_price = stm.get_current_median_history()
        steem_per_mvest = stm.get_steem_per_mvest()
        chain_props = stm.get_chain_properties()
        price = (Amount(median_price["base"], blockchain_instance=stm).amount / Amount(median_price["quote"], blockchain_instance=stm).amount)
        for key in info:
            if isinstance(info[key], dict) and 'amount' in info[key]:
                t.add_row([key, str(Amount(info[key], blockchain_instance=stm))])
            else:
                t.add_row([key, info[key]])
        t.add_row(["%s per mvest" % stm.token_symbol, steem_per_mvest])
        t.add_row(["internal price", price])
        t.add_row(["account_creation_fee", str(Amount(chain_props["account_creation_fee"], blockchain_instance=stm))])
        print(t.get_string(sortby="Key"))
        # Block
    for obj in objects:
        if re.match(r"^[0-9-]*$", obj) or re.match(r"^-[0-9]*$", obj) or re.match(r"^[0-9-]*:[0-9]", obj) or re.match(r"^[0-9-]*:-[0-9]", obj):
            tran_nr = ''
            if re.match(r"^[0-9-]*:[0-9-]", obj):
                obj, tran_nr = obj.split(":")
            if int(obj) < 1:
                b = Blockchain(blockchain_instance=stm)
                block_number = b.get_current_block_num() + int(obj) - 1
            else:
                block_number = obj
            block = Block(block_number, blockchain_instance=stm)
            if block:
                t = PrettyTable(["Key", "Value"])
                t.align = "l"
                block_json = block.json()
                for key in sorted(block_json):
                    value = block_json[key]
                    if key == "transactions" and not bool(tran_nr):
                        t.add_row(["Nr. of transactions", len(value)])
                    elif key == "transactions" and bool(tran_nr):
                        if int(tran_nr) < 0:
                            tran_nr = len(value) + int(tran_nr)
                        else:
                            tran_nr = int(tran_nr)
                        if len(value) > tran_nr - 1 and tran_nr > -1:
                            t_value = json.dumps(value[tran_nr], indent=4)
                            t.add_row(["transaction %d/%d" % (tran_nr, len(value)), t_value])
                    elif key == "transaction_ids" and not bool(tran_nr):
                        t.add_row(["Nr. of transaction_ids", len(value)])
                    elif key == "transaction_ids" and bool(tran_nr):
                        if int(tran_nr) < 0:
                            tran_nr = len(value) + int(tran_nr)
                        else:
                            tran_nr = int(tran_nr)
                        if len(value) > tran_nr - 1 and tran_nr > -1:
                            t.add_row(["transaction_id %d/%d" % (int(tran_nr), len(value)), value[tran_nr]])
                    else:
                        t.add_row([key, value])
                print(t)
            else:
                print("Block number %s unknown" % obj)
        elif re.match(r"^[a-zA-Z0-9\-\._]{2,16}$", obj):
            account = Account(obj, blockchain_instance=stm)
            t = PrettyTable(["Key", "Value"])
            t.align = "l"
            account_json = account.json()
            for key in sorted(account_json):
                value = account_json[key]
                if key == "json_metadata":
                    value = json.dumps(json.loads(value or "{}"), indent=4)
                elif key in ["posting", "witness_votes", "active", "owner"]:
                    value = json.dumps(value, indent=4)
                elif key == "reputation" and int(value) > 0:
                    value = int(value)
                    rep = account.rep
                    value = "{:.2f} ({:d})".format(rep, value)
                elif isinstance(value, dict) and "asset" in value:
                    value = str(account[key])
                t.add_row([key, value])
            print(t)

            # witness available?
            try:
                witness = Witness(obj, blockchain_instance=stm)
                witness_json = witness.json()
                t = PrettyTable(["Key", "Value"])
                t.align = "l"
                for key in sorted(witness_json):
                    value = witness_json[key]
                    if key in ["props", "sbd_exchange_rate"]:
                        value = json.dumps(value, indent=4)
                    t.add_row([key, value])
                print(t)
            except exceptions.WitnessDoesNotExistsException as e:
                print(str(e))
        # Public Key
        elif re.match(r"^" + stm.prefix + ".{48,55}$", obj):
            account = stm.wallet.getAccountFromPublicKey(obj)
            if account:
                account = Account(account, blockchain_instance=stm)
                key_type = stm.wallet.getKeyType(account, obj)
                t = PrettyTable(["Account", "Key_type"])
                t.align = "l"
                t.add_row([account["name"], key_type])
                print(t)
            else:
                print("Public Key %s not known" % obj)
        # Post identifier
        elif re.match(r".*@.{3,16}/.*$", obj):
            post = Comment(obj, blockchain_instance=stm)
            post_json = post.json()
            if post_json:
                t = PrettyTable(["Key", "Value"])
                t.align = "l"
                for key in sorted(post_json):
                    if key in ["body", "active_votes"]:
                        value = "not shown"
                    else:
                        value = post_json[key]
                    if (key in ["json_metadata"]):
                        value = json.loads(value)
                        value = json.dumps(value, indent=4)
                    elif (key in ["tags", "active_votes"]):
                        value = json.dumps(value, indent=4)
                    t.add_row([key, value])
                print(t)
            else:
                print("Post now known" % obj)
        else:
            print("Couldn't identify object to read")


@cli.command()
@click.argument('account', nargs=1, required=False)
@click.option('--signing-account', '-s', help='Signing account, when empty account is used.')
def userdata(account, signing_account):
    """ Get the account's email address and phone number.

        The request has to be signed by the requested account or an admin account.
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not unlock_wallet(stm):
        return
    if not account:
        if "default_account" in stm.config:
            account = stm.config["default_account"]
    account = Account(account, blockchain_instance=stm)
    if signing_account is not None:
        signing_account = Account(signing_account, blockchain_instance=stm)
    c = Conveyor(blockchain_instance=stm)
    user_data = c.get_user_data(account, signing_account=signing_account)
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    for key in user_data:
        # hide internal config data
        t.add_row([key, user_data[key]])
    print(t)


@cli.command()
@click.argument('account', nargs=1, required=False)
@click.option('--signing-account', '-s', help='Signing account, when empty account is used.')
def featureflags(account, signing_account):
    """ Get the account's feature flags.

        The request has to be signed by the requested account or an admin account.
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not unlock_wallet(stm):
        return
    if not account:
        if "default_account" in stm.config:
            account = stm.config["default_account"]
    account = Account(account, blockchain_instance=stm)
    if signing_account is not None:
        signing_account = Account(signing_account, blockchain_instance=stm)
    c = Conveyor(blockchain_instance=stm)
    user_data = c.get_feature_flags(account, signing_account=signing_account)
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    for key in user_data:
        # hide internal config data
        t.add_row([key, user_data[key]])
    print(t)


@cli.command()
@click.option('--block', '-b', help='Select a block number, when skipped the latest block is used.', default=None)
@click.option('--trx-id', '-t', help='Select a trx-id, When skipped, the latest one is used.', default=None)
@click.option('--draws', '-d', help='Number of draws (default = 1)', default=1)
@click.option('--participants', '-p', help='Number of participants or file name including participants (one participant per line), (default = 100)', default="100")
@click.option('--hashtype', '-h', help='Can be md5, sha256, sha512 (default = sha256)', default="sha256")
@click.option('--separator', '-s', help='Is used for sha256 and sha512 to seperate the draw number from the seed (default = ,)', default=",")
@click.option('--account', '-a', help='The account which broadcasts the reply')
@click.option('--reply', '-r', help='Parent post/comment authorperm. When set, the results will be broadcasted as reply to this authorperm.', default=None)
@click.option('--without-replacement', '-w', help='When set, numbers are drawed without replacement.', is_flag=True, default=False)
@click.option('--markdown', '-m', help='When set, results are returned in markdown format', is_flag=True, default=False)
def draw(block, trx_id, draws, participants, hashtype, separator, account, reply, without_replacement, markdown):
    """ Generate pseudo-random numbers based on trx id, block id and previous block id.

    When using --reply, the result is directly broadcasted as comment
    """    
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]    
    if reply is not None:
        if not unlock_wallet(stm):
            return
        reply_comment = Comment(reply, blockchain_instance=stm)
    if block is not None and block != "":
        block = Block(int(block), blockchain_instance=stm)
    else:
        blockchain = Blockchain(blockchain_instance=stm)
        block = blockchain.get_current_block()
    data = None
    
    for trx in block.transactions:
        if trx["transaction_id"] == trx_id:
            data = trx
        elif trx_id is None:
            trx_id = trx["transaction_id"]
            data = trx
    if trx_id is None:
        trx_id = "0"
    
    if os.path.exists(participants):
        with open(participants) as f:
            content = f.read()
        if content.find(",") > 0:
            participants_list = content.split(",")
        else:
            participants_list = content.split("\n")
        if participants_list[-1] == "":
            participants_list = participants_list[:-1]
        participants = len(participants_list)
    else:
        participants = int(participants)
        participants_list = []

    if without_replacement:
        assert draws <= participants
    trx = data["operations"][0]["value"]
    if hashtype == "md5":
        seed = hashlib.md5((trx_id + block["block_id"] + block["previous"]).encode()).hexdigest()
    elif hashtype == "sha256":
        seed = hashlib.sha256((trx_id + block["block_id"] + block["previous"]).encode()).hexdigest()
    elif hashtype == "sha512":
        seed = hashlib.sha512((trx_id + block["block_id"] + block["previous"]).encode()).hexdigest()
    random.seed(a=seed, version=2)
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    t.add_row(["block number", block["id"]])
    t.add_row(["trx id", trx_id])
    t.add_row(["block id", block["block_id"]])
    t.add_row(["previous", block["previous"]])
    t.add_row(["hash type", hashtype])
    t.add_row(["draws", draws])
    t.add_row(["participants", participants])
    draw_list = [x + 1 for x in range(participants)]
    results = []
    for i in range(int(draws)):
        if hashtype == "md5":
            number = int(random.random() * len(draw_list))
        elif hashtype == "sha256":
            seed = hashlib.sha256((trx_id + block["block_id"] + block["previous"] + separator +str(i + 1)).encode()).digest()
            bigRand = int.from_bytes(seed, 'big')
            number = bigRand % (len(draw_list))
        elif hashtype == "sha512":
            seed = hashlib.sha512((trx_id + block["block_id"] + block["previous"] + separator +str(i + 1)).encode()).digest()
            bigRand = int.from_bytes(seed, 'big')
            number = bigRand % (len(draw_list))
        results.append(draw_list[number])
        if len(participants_list) > 0:
            t.add_row(["%d. draw" % (i + 1), "%d - %s" % (draw_list[number], participants_list[draw_list[number] - 1])])
        else:
            t.add_row(["%d. draw" % (i + 1), draw_list[number]])
        if without_replacement:
            draw_list.pop(number)

    body = "The following results can be checked with:\n"
    body += "```\n"
    if without_replacement:
        body += "beempy draw -d %d -p %d -b %d -t %s -h %s -s '%s' -w\n" % (draws, participants, block["id"], trx_id, hashtype, separator)
    else:
        body += "beempy draw -d %d -p %d -b %d -t %s -h %s -s '%s'\n" % (draws, participants, block["id"], trx_id, hashtype, separator)
    body += "```\n\n"
    body += "| key | value |\n"
    body += "| --- | --- |\n"
    body += "| block number | [%d](https://hiveblocks.com/b/%d#%s) |\n" % (block["id"], block["id"], trx_id)
    body += "| trx id | [%s](https://hiveblocks.com/tx/%s) |\n" % (trx_id, trx_id)
    body += "| block id | %s |\n" % block["block_id"]
    body += "| previous id | %s |\n" % block["previous"]
    body += "| hash type | %s |\n" % hashtype
    body += "| draws | %d |\n" % draws
    body += "| participants | %d |\n" % participants
    i = 0
    for result in results:
        i += 1
        if len(participants_list) > 0:
            body += "| %d. draw | %d - %s |\n" % (i, result, participants_list[result - 1])
        else:
            body += "| %d. draw | %d |\n" % (i, result)
    if markdown:
        print(body)
    else:
        print(t)
    if reply:
        reply_comment.reply(body, author=account)


if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        os.environ['SSL_CERT_FILE'] = os.path.join(sys._MEIPASS, 'lib', 'cert.pem')
        cli(sys.argv[1:])
    else:
        cli()
