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
import pytz
import math
import random
import logging
import click
import re
from beem.instance import set_shared_steem_instance, shared_steem_instance
from beem.amount import Amount
from beem.price import Price
from beem.account import Account
from beem.steem import Steem
from beem.comment import Comment
from beem.market import Market
from beem.block import Block
from beem.profile import Profile
from beem.wallet import Wallet
from beem.asset import Asset
from beem.witness import Witness, WitnessesRankedByVote, WitnessesVotedByAccount
from beem.blockchain import Blockchain
from beem.utils import formatTimeString, construct_authorperm
from beem.vote import AccountVotes, ActiveVotes
from beem import exceptions
from beem.version import version as __version__
from beem.asciichart import AsciiChart
from beem.transactionbuilder import TransactionBuilder
from timeit import default_timer as timer
from beembase import operations
from beemgraphenebase.account import PrivateKey, PublicKey
from beemgraphenebase.base58 import Base58


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

FUTURES_MODULE = None
if not FUTURES_MODULE:
    try:
        from concurrent.futures import ThreadPoolExecutor, wait, as_completed
        FUTURES_MODULE = "futures"
    except ImportError:
        FUTURES_MODULE = None


availableConfigurationKeys = [
    "default_account",
    "default_vote_weight",
    "nodes",
    "password_storage"
]


def prompt_callback(ctx, param, value):
    if value in ["yes", "y", "ye"]:
        value = True
    else:
        print("Please write yes, ye or y to confirm!")
        ctx.abort()


def asset_callback(ctx, param, value):
    if value not in ["STEEM", "SBD"]:
        print("Please STEEM or SBD as asset!")
        ctx.abort()
    else:
        return value


def prompt_flag_callback(ctx, param, value):
    if not value:
        ctx.abort()


def unlock_wallet(stm, password=None):
    password_storage = stm.config["password_storage"]
    if not password and KEYRING_AVAILABLE and password_storage == "keyring":
        password = keyring.get_password("beem", "wallet")
    if not password and password_storage == "environment" and "UNLOCK" in os.environ:
        password = os.environ.get("UNLOCK")
    if bool(password):
        stm.wallet.unlock(password)
    else:
        password = click.prompt("Password to unlock wallet", confirmation_prompt=False, hide_input=True)
        stm.wallet.unlock(password)

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


def node_answer_time(node):
    try:
        stm_local = Steem(node=node, num_retries=2, num_retries_call=2, timeout=10)
        start = timer()
        stm_local.get_config(use_stored_data=False)
        stop = timer()
        rpc_answer_time = stop - start
    except KeyboardInterrupt:
        rpc_answer_time = float("inf")
        raise KeyboardInterrupt()
    except:
        rpc_answer_time = float("inf")
    return rpc_answer_time


@click.group(chain=True)
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
    '--expires', '-e', default=30,
    help='Delay in seconds until transactions are supposed to expire(defaults to 60)')
@click.option(
    '--verbose', '-v', default=3, help='Verbosity')
@click.version_option(version=__version__)
def cli(node, offline, no_broadcast, no_wallet, unsigned, expires, verbose):

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

    debug = verbose > 0
    stm = Steem(
        node=node,
        nobroadcast=no_broadcast,
        offline=offline,
        nowallet=no_wallet,
        unsigned=unsigned,
        expiration=expires,
        debug=debug,
        num_retries=10,
        num_retries_call=3,
        timeout=15,
        autoconnect=False
    )
    set_shared_steem_instance(stm)

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
    stm = shared_steem_instance()
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
            print("The wallet password can be stored in the UNLOCK invironment variable to skip password prompt!")
    else:
        print("wrong key")


@cli.command()
@click.option('--results', is_flag=True, default=False, help="Shows result of changing the node.")
def nextnode(results):
    """ Uses the next node in list
    """
    stm = shared_steem_instance()
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
    else:
        t.add_row(["Version", "steempy is in offline mode..."])
    print(t)


@cli.command()
@click.option(
    '--raw', is_flag=True, default=False,
    help="Returns only the raw value")
@click.option(
    '--sort', is_flag=True, default=False,
    help="Sort all nodes by ping value")
@click.option(
    '--remove', is_flag=True, default=False,
    help="Remove node with errors from list")
@click.option(
    '--threading', is_flag=True, default=False,
    help="Use a thread for each node")
def pingnode(raw, sort, remove, threading):
    """ Returns the answer time in milliseconds
    """
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    nodes = stm.get_default_nodes()
    if not raw:
        t = PrettyTable(["Node", "Answer time [ms]"])
        t.align = "l"
    if sort:
        ping_times = []
        for node in nodes:
            ping_times.append(1000.)
        if threading and FUTURES_MODULE:
            pool = ThreadPoolExecutor(max_workers=len(nodes) + 1)
            futures = []
        for i in range(len(nodes)):
            try:
                if not threading or not FUTURES_MODULE:
                    ping_times[i] = node_answer_time(nodes[i])
                else:
                    futures.append(pool.submit(node_answer_time, nodes[i]))
                if not threading or not FUTURES_MODULE:
                    print("node %s results in %.2f" % (nodes[i], ping_times[i]))
            except KeyboardInterrupt:
                ping_times[i] = float("inf")
                break
        if threading and FUTURES_MODULE:
            ping_times = [r.result() for r in as_completed(futures)]
        sorted_arg = sorted(range(len(ping_times)), key=ping_times.__getitem__)
        sorted_nodes = []
        for i in sorted_arg:
            if not remove or ping_times[i] != float("inf"):
                sorted_nodes.append(nodes[i])
        stm.set_default_nodes(sorted_nodes)
        if not raw:
            for i in sorted_arg:
                t.add_row([nodes[i], "%.2f" % (ping_times[i] * 1000)])
            print(t)
        else:
            print(ping_times[sorted_arg])
    else:
        node = stm.rpc.url
        rpc_answer_time = node_answer_time(node)
        rpc_time_str = "%.2f" % (rpc_answer_time * 1000)
        if raw:
            print(rpc_time_str)
            return
        t.add_row([node, rpc_time_str])
        print(t)


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
    stm = shared_steem_instance()
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
    else:
        t.add_row(["Version", "steempy is in offline mode..."])
    print(t)


@cli.command()
def config():
    """ Shows local configuration
    """
    stm = shared_steem_instance()
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    for key in stm.config:
        # hide internal config data
        if key in availableConfigurationKeys and key != "nodes" and key != "node":
            t.add_row([key, stm.config[key]])
    node = stm.get_default_nodes()
    nodes = json.dumps(node, indent=4)
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
    stm = shared_steem_instance()
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
        print("The new wallet password can be stored in the UNLOCK invironment variable to skip password prompt!")
    stm.wallet.create(password)
    set_shared_steem_instance(stm)


@cli.command()
@click.option('--test-unlock', is_flag=True, default=False, help='test if unlock is sucessful')
def walletinfo(test_unlock):
    """ Show info about wallet
    """
    stm = shared_steem_instance()
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    t.add_row(["created", stm.wallet.created()])
    t.add_row(["locked", stm.wallet.locked()])
    t.add_row(["Number of stored keys", len(stm.wallet.getPublicKeys())])
    t.add_row(["sql-file", stm.wallet.keyStorage.sqlDataBaseFile])
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
    if test_unlock:
        if unlock_wallet(stm):
            t.add_row(["Wallet unlock", "sucessful"])
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
    stm = shared_steem_instance()
    if unsafe_import_key:
        for key in unsafe_import_key:
            try:
                print(PrivateKey(key, prefix=stm.prefix).pubkey)
            except Exception as e:
                print(str(e))
    else:
        while True:
            wifkey = click.prompt("Enter private key", confirmation_prompt=False, hide_input=True)
            if not wifkey or wifkey == "quit" or wifkey == "exit":
                break
            try:
                print(PrivateKey(wifkey, prefix=stm.prefix).pubkey)
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
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not unlock_wallet(stm):
        return
    if not unsafe_import_key:
        unsafe_import_key = click.prompt("Enter private key", confirmation_prompt=False, hide_input=True)
    stm.wallet.addPrivateKey(unsafe_import_key)
    set_shared_steem_instance(stm)


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
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not unlock_wallet(stm):
        return
    stm.wallet.removePrivateKeyFromPublicKey(pub)
    set_shared_steem_instance(stm)


@cli.command()
def listkeys():
    """ Show stored keys
    """
    stm = shared_steem_instance()
    t = PrettyTable(["Available Key"])
    t.align = "l"
    for key in stm.wallet.getPublicKeys():
        t.add_row([key])
    print(t)


@cli.command()
def listaccounts():
    """Show stored accounts"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
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
@click.argument('vote_weight', nargs=1, required=False)
@click.option('--weight', '-w', help='Vote weight (from 0.1 to 100.0)')
@click.option('--account', '-a', help='Voter account name')
def upvote(post, vote_weight, account, weight):
    """Upvote a post/comment

        POST is @author/permlink
    """
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not weight and vote_weight:
        weight = vote_weight
    elif not weight and not vote_weight:
        weight = stm.config["default_vote_weight"]
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    try:
        post = Comment(post, steem_instance=stm)
        tx = post.upvote(weight, voter=account)
    except exceptions.VotingInvalidOnArchivedPost:
        print("Post/Comment is older than 7 days! Did not upvote.")
        tx = {}
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('post', nargs=1)
@click.argument('vote_weight', nargs=1, required=False)
@click.option('--account', '-a', help='Voter account name')
@click.option('--weight', '-w', default=100.0, help='Vote weight (from 0.1 to 100.0)')
def downvote(post, vote_weight, account, weight):
    """Downvote a post/comment

        POST is @author/permlink
    """
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not weight and vote_weight:
        weight = vote_weight
    elif not weight and not vote_weight:
        weight = stm.config["default_vote_weight"]
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    try:
        post = Comment(post, steem_instance=stm)
        tx = post.downvote(weight, voter=account)
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
    """Transfer SBD/STEEM"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not bool(memo):
        memo = ''
    if not unlock_wallet(stm):
        return
    acc = Account(account, steem_instance=stm)
    tx = acc.transfer(to, amount, asset, memo)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1)
@click.option('--account', '-a', help='Powerup from this account')
@click.option('--to', help='Powerup this account', default=None)
def powerup(amount, account, to):
    """Power up (vest STEEM as STEEM POWER)"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, steem_instance=stm)
    try:
        amount = float(amount)
    except:
        amount = str(amount)
    tx = acc.transfer_to_vesting(amount, to=to)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1)
@click.option('--account', '-a', help='Powerup from this account')
def powerdown(amount, account):
    """Power down (start withdrawing VESTS from Steem POWER)

        amount is in VESTS
    """
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, steem_instance=stm)
    try:
        amount = float(amount)
    except:
        amount = str(amount)
    tx = acc.withdraw_vesting(amount)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('to', nargs=1)
@click.option('--percentage', default=100, help='The percent of the withdraw to go to the "to" account')
@click.option('--account', '-a', help='Powerup from this account')
@click.option('--auto_vest', help='Set to true if the from account should receive the VESTS as'
              'VESTS, or false if it should receive them as STEEM.', is_flag=True)
def powerdownroute(to, percentage, account, auto_vest):
    """Setup a powerdown route"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, steem_instance=stm)
    tx = acc.set_withdraw_vesting_route(to, percentage, auto_vest=auto_vest)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1)
@click.option('--account', '-a', help='Powerup from this account')
def convert(amount, account):
    """Convert STEEMDollars to Steem (takes a week to settle)"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, steem_instance=stm)
    try:
        amount = float(amount)
    except:
        amount = str(amount)
    tx = acc.convert(amount)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
def changewalletpassphrase():
    """ Change wallet password
    """
    stm = shared_steem_instance()
    if not unlock_wallet(stm):
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
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if len(account) == 0:
        if "default_account" in stm.config:
            account = [stm.config["default_account"]]
    for name in account:
        a = Account(name, steem_instance=stm)
        print("\n@%s" % a.name)
        a.print_info(use_table=True)


@cli.command()
@click.argument('account', nargs=-1)
def balance(account):
    """ Shows balance
    """
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if len(account) == 0:
        if "default_account" in stm.config:
            account = [stm.config["default_account"]]
    for name in account:
        a = Account(name, steem_instance=stm)
        print("\n@%s" % a.name)
        t = PrettyTable(["Account", "STEEM", "SBD", "VESTS"])
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
    stm = shared_steem_instance()
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
        a = Account(a, steem_instance=stm)
        i = a.interest()
        t.add_row([
            a["name"],
            i["last_payment"],
            "in %s" % (i["next_payment_duration"]),
            "%.1f%%" % i["interest_rate"],
            "%.3f %s" % (i["interest"], "SBD"),
        ])
    print(t)


@cli.command()
@click.argument('account', nargs=-1, required=False)
def follower(account):
    """ Get information about followers
    """
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        if "default_account" in stm.config:
            account = [stm.config["default_account"]]
    for a in account:
        a = Account(a, steem_instance=stm)
        print("\nFollowers statistics for @%s (please wait...)" % a.name)
        followers = a.get_followers(False)
        followers.print_summarize_table(tag_type="Followers")


@cli.command()
@click.argument('account', nargs=-1, required=False)
def following(account):
    """ Get information about following
    """
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        if "default_account" in stm.config:
            account = [stm.config["default_account"]]
    for a in account:
        a = Account(a, steem_instance=stm)
        print("\nFollowing statistics for @%s (please wait...)" % a.name)
        following = a.get_following(False)
        following.print_summarize_table(tag_type="Following")


@cli.command()
@click.argument('account', nargs=-1, required=False)
def muter(account):
    """ Get information about muter
    """
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        if "default_account" in stm.config:
            account = [stm.config["default_account"]]
    for a in account:
        a = Account(a, steem_instance=stm)
        print("\nMuters statistics for @%s (please wait...)" % a.name)
        muters = a.get_muters(False)
        muters.print_summarize_table(tag_type="Muters")


@cli.command()
@click.argument('account', nargs=-1, required=False)
def muting(account):
    """ Get information about muting
    """
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        if "default_account" in stm.config:
            account = [stm.config["default_account"]]
    for a in account:
        a = Account(a, steem_instance=stm)
        print("\nMuting statistics for @%s (please wait...)" % a.name)
        muting = a.get_mutings(False)
        muting.print_summarize_table(tag_type="Muting")


@cli.command()
@click.argument('account', nargs=1, required=False)
def permissions(account):
    """ Show permissions of an account
    """
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        if "default_account" in stm.config:
            account = stm.config["default_account"]
    account = Account(account, steem_instance=stm)
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
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    if permission not in ["posting", "active", "owner"]:
        print("Wrong permission, please use: posting, active or owner!")
        return
    acc = Account(account, steem_instance=stm)
    if not foreign_account:
        from beemgraphenebase.account import PasswordKey
        pwd = click.prompt("Password for Key Derivation", confirmation_prompt=True, hide_input=True)
        foreign_account = format(PasswordKey(account, pwd, permission).get_public(), stm.prefix)
    tx = acc.allow(foreign_account, weight=weight, permission=permission, threshold=threshold)
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
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    if permission not in ["posting", "active", "owner"]:
        print("Wrong permission, please use: posting, active or owner!")
        return
    acc = Account(account, steem_instance=stm)
    if not foreign_account:
        from beemgraphenebase.account import PasswordKey
        pwd = click.prompt("Password for Key Derivation", confirmation_prompt=True)
        foreign_account = [format(PasswordKey(account, pwd, permission).get_public(), stm.prefix)]
    tx = acc.disallow(foreign_account, permission=permission, threshold=threshold)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('accountname', nargs=1, required=True)
@click.option('--account', '-a', help='Account that pays the fee')
@click.option('--fee', help='Base Fee to pay. Delegate the rest.', default='0 STEEM')
def newaccount(accountname, account, fee):
    """Create a new account"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, steem_instance=stm)
    password = click.prompt("New Account Passphrase", confirmation_prompt=True, hide_input=True)
    if not password:
        print("You cannot chose an empty password")
        return
    tx = stm.create_account(accountname, creator=acc, password=password, delegation_fee_steem=fee)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('variable', nargs=1, required=False)
@click.argument('value', nargs=1, required=False)
@click.option('--account', '-a', help='setprofile as this user')
@click.option('--pair', '-p', help='"Key=Value" pairs', multiple=True)
def setprofile(variable, value, account, pair):
    """Set a variable in an account\'s profile"""
    stm = shared_steem_instance()
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
    acc = Account(account, steem_instance=stm)

    acc["json_metadata"] = Profile(acc["json_metadata"]
                                   if acc["json_metadata"] else {})
    acc["json_metadata"].update(profile)
    tx = acc.update_account_profile(acc["json_metadata"])
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('variable', nargs=-1, required=True)
@click.option('--account', '-a', help='delprofile as this user')
def delprofile(variable, account):
    """Delete a variable in an account\'s profile"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()

    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, steem_instance=stm)
    acc["json_metadata"] = Profile(acc["json_metadata"])

    for var in variable:
        acc["json_metadata"].remove(var)

    tx = acc.update_account_profile(acc["json_metadata"])
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('account', nargs=1, required=True)
@click.option('--roles', help='Import specified keys (owner, active, posting, memo).', default=["active", "posting", "memo"])
def importaccount(account, roles):
    """Import an account using a passphrase"""
    from beemgraphenebase.account import PasswordKey
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not unlock_wallet(stm):
        return
    account = Account(account, steem_instance=stm)
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
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, steem_instance=stm)
    if not key:
        from beemgraphenebase.account import PasswordKey
        pwd = click.prompt("Password for Memo Key Derivation", confirmation_prompt=True, hide_input=True)
        memo_key = PasswordKey(account, pwd, "memo")
        key = format(memo_key.get_public_key(), stm.prefix)
        memo_privkey = memo_key.get_private_key()
        if not stm.nobroadcast:
            stm.wallet.addPrivateKey(memo_privkey)
    tx = acc.update_memo_key(key)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('witness', nargs=1)
@click.option('--account', '-a', help='Your account')
def approvewitness(witness, account):
    """Approve a witnesses"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, steem_instance=stm)
    tx = acc.approvewitness(witness, approve=True)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('witness', nargs=1)
@click.option('--account', '-a', help='Your account')
def disapprovewitness(witness, account):
    """Disapprove a witnesses"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, steem_instance=stm)
    tx = acc.disapprovewitness(witness)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.option('--file', help='Load transaction from file. If "-", read from stdin (defaults to "-")')
def sign(file):
    """Sign a provided transaction with available and required keys"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if file and file != "-":
        if not os.path.isfile(file):
            raise Exception("File %s does not exist!" % file)
        with open(file) as fp:
            tx = fp.read()
    else:
        tx = click.get_text_stream('stdin')
    tx = ast.literal_eval(tx)
    tx = stm.sign(tx)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.option('--file', help='Load transaction from file. If "-", read from stdin (defaults to "-")')
def broadcast(file):
    """broadcast a signed transaction"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if file and file != "-":
        if not os.path.isfile(file):
            raise Exception("File %s does not exist!" % file)
        with open(file) as fp:
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
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    market = Market(steem_instance=stm)
    ticker = market.ticker()
    for key in ticker:
        if key in ["highest_bid", "latest", "lowest_ask"] and sbd_to_steem:
            t.add_row([key, str(ticker[key].as_base("SBD"))])
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
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    feed_history = stm.get_feed_history()
    current_base = Amount(feed_history['current_median_history']["base"], steem_instance=stm)
    current_quote = Amount(feed_history['current_median_history']["quote"], steem_instance=stm)
    price_history = feed_history["price_history"]
    price = []
    for h in price_history:
        base = Amount(h["base"])
        quote = Amount(h["quote"])
        price.append(base.amount / quote.amount)
    if ascii:
        charset = u'ascii'
    else:
        charset = u'utf8'
    chart = AsciiChart(height=height, width=width, offset=4, placeholder='{:6.2f} $', charset=charset)
    print("\n            Price history for STEEM (median price %4.2f $)\n" % (float(current_base) / float(current_quote)))

    chart.adapt_on_series(price)
    chart.new_chart()
    chart.add_axis()
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
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    m = Market(steem_instance=stm)
    utc = pytz.timezone('UTC')
    stop = utc.localize(datetime.utcnow())
    start = stop - timedelta(days=days)
    intervall = timedelta(hours=hours)
    trades = m.trade_history(start=start, stop=stop, limit=limit, intervall=intervall)
    price = []
    if sbd_to_steem:
        base_str = "STEEM"
    else:
        base_str = "SBD"
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
        print("\n     Trade history %s - %s \n\nSBD/STEEM" % (formatTimeString(start), formatTimeString(stop)))
    else:
        print("\n     Trade history %s - %s \n\nSTEEM/SBD" % (formatTimeString(start), formatTimeString(stop)))
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
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    market = Market(steem_instance=stm)
    orderbook = market.orderbook(limit=limit, raw_data=False)
    if not show_date:
        header = ["Asks Sum SBD", "Sell Orders", "Bids Sum SBD", "Buy Orders"]
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
        sum_asks += float(order.as_base("SBD")["base"])
        sumsum_asks.append(sum_asks)
    if n < len(asks):
        n = len(asks)
    for order in orderbook["bids"]:
        bids.append(order)
        sum_bids += float(order.as_base("SBD")["base"])
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
    """Buy STEEM or SBD from the internal market

        Limit buy price denoted in (SBD per STEEM)
    """
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if asset == "SBD":
        market = Market(base=Asset("STEEM"), quote=Asset("SBD"), steem_instance=stm)
    else:
        market = Market(base=Asset("SBD"), quote=Asset("STEEM"), steem_instance=stm)
    if not price:
        orderbook = market.orderbook(limit=1, raw_data=False)
        if asset == "STEEM" and len(orderbook["bids"]) > 0:
            p = Price(orderbook["bids"][0]["base"], orderbook["bids"][0]["quote"], steem_instance=stm).invert()
            p_show = p
        else:
            p = Price(orderbook["asks"][0]["base"], orderbook["asks"][0]["quote"], steem_instance=stm).invert()
            p_show = p
        price_ok = click.prompt("Is the following Price ok: %s [y/n]" % (str(p_show)))
        if price_ok not in ["y", "ye", "yes"]:
            return
    else:
        p = Price(float(price), u"SBD:STEEM", steem_instance=stm)
    if not unlock_wallet(stm):
        return

    a = Amount(float(amount), asset, steem_instance=stm)
    acc = Account(account, steem_instance=stm)
    tx = market.buy(p, a, account=acc, orderid=orderid)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1)
@click.argument('asset', nargs=1)
@click.argument('price', nargs=1, required=False)
@click.option('--account', '-a', help='Sell with this account (defaults to "default_account")')
@click.option('--orderid', help='Set an orderid')
def sell(amount, asset, price, account, orderid):
    """Sell STEEM or SBD from the internal market

        Limit sell price denoted in (SBD per STEEM)
    """
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if asset == "SBD":
        market = Market(base=Asset("STEEM"), quote=Asset("SBD"), steem_instance=stm)
    else:
        market = Market(base=Asset("SBD"), quote=Asset("STEEM"), steem_instance=stm)
    if not account:
        account = stm.config["default_account"]
    if not price:
        orderbook = market.orderbook(limit=1, raw_data=False)
        if asset == "SBD" and len(orderbook["bids"]) > 0:
            p = Price(orderbook["bids"][0]["base"], orderbook["bids"][0]["quote"], steem_instance=stm).invert()
            p_show = p
        else:
            p = Price(orderbook["asks"][0]["base"], orderbook["asks"][0]["quote"], steem_instance=stm).invert()
            p_show = p
        price_ok = click.prompt("Is the following Price ok: %s [y/n]" % (str(p_show)))
        if price_ok not in ["y", "ye", "yes"]:
            return
    else:
        p = Price(float(price), u"SBD:STEEM", steem_instance=stm)
    if not unlock_wallet(stm):
        return
    a = Amount(float(amount), asset, steem_instance=stm)
    acc = Account(account, steem_instance=stm)
    tx = market.sell(p, a, account=acc, orderid=orderid)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('orderid', nargs=1)
@click.option('--account', '-a', help='Sell with this account (defaults to "default_account")')
def cancel(orderid, account):
    """Cancel order in the internal market"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    market = Market(steem_instance=stm)
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, steem_instance=stm)
    tx = market.cancel(orderid, account=acc)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('account', nargs=1, required=False)
def openorders(account):
    """Show open orders"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    market = Market(steem_instance=stm)
    if not account:
        account = stm.config["default_account"]
    acc = Account(account, steem_instance=stm)
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
@click.option('--account', '-a', help='Resteem as this user')
def resteem(identifier, account):
    """Resteem an existing post"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, steem_instance=stm)
    post = Comment(identifier, steem_instance=stm)
    tx = post.resteem(account=acc)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('follow', nargs=1)
@click.option('--account', '-a', help='Follow from this account')
@click.option('--what', help='Follow these objects (defaults to ["blog"])', default=["blog"])
def follow(follow, account, what):
    """Follow another account"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if isinstance(what, str):
        what = [what]
    if not unlock_wallet(stm):
        return
    acc = Account(account, steem_instance=stm)
    tx = acc.follow(follow, what=what)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('mute', nargs=1)
@click.option('--account', '-a', help='Mute from this account')
@click.option('--what', help='Mute these objects (defaults to ["ignore"])', default=["ignore"])
def mute(mute, account, what):
    """Mute another account"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if isinstance(what, str):
        what = [what]
    if not unlock_wallet(stm):
        return
    acc = Account(account, steem_instance=stm)
    tx = acc.follow(mute, what=what)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('unfollow', nargs=1)
@click.option('--account', '-a', help='UnFollow/UnMute from this account')
def unfollow(unfollow, account):
    """Unfollow/Unmute another account"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    acc = Account(account, steem_instance=stm)
    tx = acc.unfollow(unfollow)
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
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not witness:
        witness = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    witness = Witness(witness, steem_instance=stm)
    props = witness["props"]
    if account_creation_fee:
        props["account_creation_fee"] = str(
            Amount("%f STEEM" % account_creation_fee))
    if maximum_block_size:
        props["maximum_block_size"] = maximum_block_size
    if sbd_interest_rate:
        props["sbd_interest_rate"] = int(sbd_interest_rate * 100)
    tx = witness.update(signing_key or witness["signing_key"], url or witness["url"], props)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('witness', nargs=1)
@click.argument('signing_key', nargs=1)
@click.option('--maximum_block_size', help='Max block size', default="65536")
@click.option('--account_creation_fee', help='Account creation fee', default=30)
@click.option('--sbd_interest_rate', help='SBD interest rate in percent', default=0.0)
@click.option('--url', help='Witness URL', default="")
def witnesscreate(witness, signing_key, maximum_block_size, account_creation_fee, sbd_interest_rate, url):
    """Create a witness"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not unlock_wallet(stm):
        return
    props = {
        "account_creation_fee":
            str(Amount("%f STEEM" % account_creation_fee)),
        "maximum_block_size":
            maximum_block_size,
        "sbd_interest_rate":
            int(sbd_interest_rate * 100)
    }

    tx = stm.witness_update(signing_key, url, props, account=witness)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('account', nargs=1, required=False)
@click.option('--limit', help='How many witnesses should be shown', default=100)
def witnesses(account, limit):
    """ List witnesses
    """
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if account:
        witnesses = WitnessesVotedByAccount(account, steem_instance=stm)
    else:
        witnesses = WitnessesRankedByVote(limit=limit, steem_instance=stm)
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
    stm = shared_steem_instance()
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
        votes = AccountVotes(account, start=limit_time, steem_instance=stm)
        out_votes_str = votes.printAsTable(start=limit_time, return_str=True)
    if direction == "in" or incoming:
        account = Account(account, steem_instance=stm)
        votes_list = []
        for v in account.history(start=limit_time, only_ops=["vote"]):
            votes_list.append(v)
        votes = ActiveVotes(votes_list, steem_instance=stm)
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
@click.option('--limit', '-l', help='Show only the first minutes')
@click.option('--payout', '-p', default=None, help="Show the curation for a potential payout in SBD as float")
@click.option('--export', '-e', default=None, help="Export results to HTML-file")
def curation(authorperm, account, limit, payout, export):
    """ Lists curation rewards of all votes for authorperm

        When authorperm is empty or "all", curation rewards
        for all account votes is shown.
    """
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if authorperm == 'all' or authorperm is None:
        if not account:
            account = stm.config["default_account"]
        utc = pytz.timezone('UTC')
        limit_time = utc.localize(datetime.utcnow()) - timedelta(days=7)
        votes = AccountVotes(account, start=limit_time, steem_instance=stm)
        authorperm_list = [Comment(vote.authorperm, steem_instance=stm) for vote in votes]
    else:
        authorperm_list = [authorperm]
    if export:
        t = PrettyTable(["Author", "permlink", "Voter", "Voting time", "Vote", "Early vote loss", "Curation", "Performance"])
        t.align = "l"
    else:
        t = PrettyTable(["Voter", "Voting time", "Vote", "Early vote loss", "Curation", "Performance"])
        t.align = "l"
    for authorperm in authorperm_list:
        comment = Comment(authorperm, steem_instance=stm)
        if payout is not None and comment.is_pending():
            payout = float(payout)
        elif payout is not None:
            payout = None
        curation_rewards_SBD = comment.get_curation_rewards(pending_payout_SBD=True, pending_payout_value=payout)
        curation_rewards_SP = comment.get_curation_rewards(pending_payout_SBD=False, pending_payout_value=payout)
        rows = []
        sum_curation = [0, 0, 0, 0]
        max_curation = [0, 0, 0, 0, 0, 0]
        max_vote = [0, 0, 0, 0, 0, 0]
        for vote in comment["active_votes"]:
            vote_SBD = stm.rshares_to_sbd(int(vote["rshares"]))
            curation_SBD = curation_rewards_SBD["active_votes"][vote["voter"]]
            curation_SP = curation_rewards_SP["active_votes"][vote["voter"]]
            if vote_SBD > 0:
                penalty = ((100 - comment.get_curation_penalty(vote_time=vote["time"])) / 100 * vote_SBD)
                performance = (float(curation_SBD) / vote_SBD * 100)
            else:
                performance = 0
                penalty = 0
            vote_befor_min = ((formatTimeString(vote["time"]) - comment["created"]).total_seconds() / 60)
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
            if row[-1] > max_curation[-1]:
                max_curation = row
            if row[2] > max_vote[2]:
                max_vote = row
            rows.append(row)
        sortedList = sorted(rows, key=lambda row: (row[1]), reverse=False)
        new_row = []
        new_row2 = []
        if export:
            new_row = [comment.author, comment.permlink]
            new_row2 = ["", ""]
        for row in sortedList:
            if limit is not None and row[1] > float(limit):
                continue
            if account is None or account == row[0]:
                t.add_row(new_row + [row[0],
                                     "%.1f min" % row[1],
                                     "%.3f SBD" % float(row[2]),
                                     "%.3f SBD" % float(row[3]),
                                     "%.3f SP" % (row[4]),
                                     "%.1f %%" % (row[5])])
                if len(authorperm_list) == 1:
                    new_row = new_row2
        if export:
            t.add_row(["", "", "", "", "", "", "", ""])
        else:
            t.add_row(["", "", "", "", "", ""])
        if sum_curation[0] > 0:
            curation_sum_percentage = sum_curation[3] / sum_curation[0] * 100
        else:
            curation_sum_percentage = 0

        t.add_row(new_row2 + ["High. vote",
                              "%.1f min" % max_vote[1],
                              "%.3f SBD" % float(max_vote[2]),
                              "%.3f SBD" % float(max_vote[3]),
                              "%.3f SP" % (max_vote[4]),
                              "%.1f %%" % (max_vote[5])])
        t.add_row(new_row2 + ["High. Cur.",
                              "%.1f min" % max_curation[1],
                              "%.3f SBD" % float(max_curation[2]),
                              "%.3f SBD" % float(max_curation[3]),
                              "%.3f SP" % (max_curation[4]),
                              "%.1f %%" % (max_curation[5])])
        t.add_row(new_row2 + ["Sum",
                              "-",
                              "%.3f SBD" % (sum_curation[0]),
                              "%.3f SBD" % (sum_curation[1]),
                              "%.3f SP" % (sum_curation[2]),
                              "%.2f %%" % curation_sum_percentage])
        if export:
            t.add_row(["", "", "-", "-", "-", "-", "-", "-"])
        else:
            print("%s" % authorperm)
            print(t)
    if export:
        with open(export, 'w') as w:
            w.write(str(t.get_html_string()))


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
    stm = shared_steem_instance()
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
        account = Account(account, steem_instance=stm)
        median_price = Price(stm.get_current_median_history(), steem_instance=stm)
        m = Market(steem_instance=stm)
        latest = m.ticker()["latest"]
        if author and permlink:
            t = PrettyTable(["Author", "Permlink", "Payout", "SBD", "SP + STEEM", "Liquid USD", "Invested USD"])
        elif author and title:
                t = PrettyTable(["Author", "Title", "Payout", "SBD", "SP + STEEM", "Liquid USD", "Invested USD"])
        elif author:
            t = PrettyTable(["Author", "Payout", "SBD", "SP + STEEM", "Liquid USD", "Invested USD"])
        elif not author and permlink:
            t = PrettyTable(["Permlink", "Payout", "SBD", "SP + STEEM", "Liquid USD", "Invested USD"])
        elif not author and title:
            t = PrettyTable(["Title", "Payout", "SBD", "SP + STEEM", "Liquid USD", "Invested USD"])
        else:
            t = PrettyTable(["Received", "SBD", "SP + STEEM", "Liquid USD", "Invested USD"])
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
                    c = Comment(v, steem_instance=stm)
                    try:
                        c.refresh()
                    except exceptions.ContentDoesNotExistsException:
                        continue
                    if not post and not c.is_comment():
                        continue
                    if not comment and c.is_comment():
                        continue
                    payout_SBD = Amount(v["sbd_payout"], steem_instance=stm)
                    payout_STEEM = Amount(v["steem_payout"], steem_instance=stm)
                    sum_reward[0] += float(payout_SBD)
                    sum_reward[1] += float(payout_STEEM)
                    payout_SP = stm.vests_to_sp(Amount(v["vesting_payout"], steem_instance=stm))
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
                    reward = Amount(v["reward"], steem_instance=stm)
                    payout_SP = stm.vests_to_sp(reward)
                    liquid_USD = 0
                    invested_USD = float(payout_SP) * float(median_price)
                    sum_reward[2] += float(payout_SP)
                    sum_reward[4] += invested_USD
                    if title:
                        c = Comment(construct_authorperm(v["comment_author"], v["comment_permlink"]), steem_instance=stm)
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
                       "%.2f SBD" % (sum_reward[0]),
                       "%.2f SP" % (sum_reward[1] + sum_reward[2]),
                       "%.2f $" % (sum_reward[3]),
                       "%.2f $" % (sum_reward[4])])
        elif not author and not (permlink or title):
            t.add_row(["", "", "", "", ""])
            t.add_row(["Sum",
                       "%.2f SBD" % (sum_reward[0]),
                       "%.2f SP" % (sum_reward[1] + sum_reward[2]),
                       "%.2f $" % (sum_reward[2]),
                       "%.2f $" % (sum_reward[3])])
        else:
            t.add_row(["", "", "", "", "", ""])
            t.add_row(["Sum",
                       "-",
                       "%.2f SBD" % (sum_reward[0]),
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
def pending(accounts, only_sum, post, comment, curation, length, author, permlink, title, days):
    """ Lists pending rewards
    """
    stm = shared_steem_instance()
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

    utc = pytz.timezone('UTC')
    limit_time = utc.localize(datetime.utcnow()) - timedelta(days=days)
    for account in accounts:
        sum_reward = [0, 0, 0, 0]
        account = Account(account, steem_instance=stm)
        median_price = Price(stm.get_current_median_history(), steem_instance=stm)
        m = Market(steem_instance=stm)
        latest = m.ticker()["latest"]
        if author and permlink:
            t = PrettyTable(["Author", "Permlink", "Cashout", "SBD", "SP", "Liquid USD", "Invested USD"])
        elif author and title:
            t = PrettyTable(["Author", "Title", "Cashout", "SBD", "SP", "Liquid USD", "Invested USD"])
        elif author:
            t = PrettyTable(["Author", "Cashout", "SBD", "SP", "Liquid USD", "Invested USD"])
        elif not author and permlink:
            t = PrettyTable(["Permlink", "Cashout", "SBD", "SP", "Liquid USD", "Invested USD"])
        elif not author and title:
            t = PrettyTable(["Title", "Cashout", "SBD", "SP", "Liquid USD", "Invested USD"])
        else:
            t = PrettyTable(["Cashout", "SBD", "SP", "Liquid USD", "Invested USD"])
        t.align = "l"
        rows = []
        c_list = {}
        start_op = account.estimate_virtual_op_num(limit_time)
        if start_op > 0:
            start_op -= 1
        progress_length = (account.virtual_op_count() - start_op) / 1000
        with click.progressbar(map(Comment, account.history(start=start_op, use_block_num=False, only_ops=["comment"])), length=progress_length) as comment_hist:
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
                             ((v["created"] - limit_time).total_seconds() / 60 / 60 / 24),
                             (payout_SBD),
                             (payout_SP),
                             (liquid_USD),
                             (invested_USD)])
        if curation:
            votes = AccountVotes(account, start=limit_time, steem_instance=stm)
            for vote in votes:
                c = Comment(vote["authorperm"])
                rewards = c.get_curation_rewards()
                if not rewards["pending_rewards"]:
                    continue
                days_to_payout = ((c["created"] - limit_time).total_seconds() / 60 / 60 / 24)
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
                       "%.2f SBD" % (sum_reward[0]),
                       "%.2f SP" % (sum_reward[1]),
                       "%.2f $" % (sum_reward[2]),
                       "%.2f $" % (sum_reward[3])])
        elif not author and not (permlink or title):
            t.add_row(["", "", "", "", ""])
            t.add_row(["Sum",
                       "%.2f SBD" % (sum_reward[0]),
                       "%.2f SP" % (sum_reward[1]),
                       "%.2f $" % (sum_reward[2]),
                       "%.2f $" % (sum_reward[3])])
        else:
            t.add_row(["", "", "", "", "", ""])
            t.add_row(["Sum",
                       "-",
                       "%.2f SBD" % (sum_reward[0]),
                       "%.2f SP" % (sum_reward[1]),
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
@click.option('--reward_steem', help='Amount of STEEM you would like to claim', default="0 STEEM")
@click.option('--reward_sbd', help='Amount of SBD you would like to claim', default="0 SBD")
@click.option('--reward_vests', help='Amount of VESTS you would like to claim', default="0 VESTS")
def claimreward(account, reward_steem, reward_sbd, reward_vests):
    """Claim reward balances

        By default, this will claim ``all`` outstanding balances.
    """
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    acc = Account(account, steem_instance=stm)
    r = acc.balances["rewards"]
    if r[0].amount + r[1].amount + r[2].amount == 0:
        print("Nothing to claim.")
        return
    if not unlock_wallet(stm):
        return

    tx = acc.claim_reward_balance(reward_steem, reward_sbd, reward_vests)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('blocknumber', nargs=1, required=False)
@click.option('--trx', '-t', help='Show only one transaction number', default=None)
@click.option('--use-api', '-u', help='Uses the get_potential_signatures api call', is_flag=True, default=False)
def verify(blocknumber, trx, use_api):
    """Returns the public signing keys for a block"""
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    b = Blockchain(steem_instance=stm)
    i = 0
    if not blocknumber:
        blocknumber = b.get_current_block_num()
    try:
        int(blocknumber)
        block = Block(blocknumber, steem_instance=stm)
        if trx is not None:
            i = int(trx)
            trxs = [block.transactions[int(trx)]]
        else:
            trxs = block.transactions
    except Exception:
        trxs = [b.get_transaction(blocknumber)]
        blocknumber = trxs[0]["block_num"]
    wallet = Wallet(steem_instance=stm)
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
            tx = TransactionBuilder(tx=trx, steem_instance=stm)
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
    stm = shared_steem_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not objects:
        t = PrettyTable(["Key", "Value"])
        t.align = "l"
        info = stm.get_dynamic_global_properties()
        median_price = stm.get_current_median_history()
        steem_per_mvest = stm.get_steem_per_mvest()
        chain_props = stm.get_chain_properties()
        price = (Amount(median_price["base"], steem_instance=stm).amount / Amount(
            median_price["quote"], steem_instance=stm).amount)
        for key in info:
            t.add_row([key, info[key]])
        t.add_row(["steem per mvest", steem_per_mvest])
        t.add_row(["internal price", price])
        t.add_row(["account_creation_fee", chain_props["account_creation_fee"]])
        print(t.get_string(sortby="Key"))
        # Block
    for obj in objects:
        if re.match("^[0-9-]*$", obj) or re.match("^-[0-9]*$", obj) or re.match("^[0-9-]*:[0-9]", obj) or re.match("^[0-9-]*:-[0-9]", obj):
            tran_nr = ''
            if re.match("^[0-9-]*:[0-9-]", obj):
                obj, tran_nr = obj.split(":")
            if int(obj) < 1:
                b = Blockchain(steem_instance=stm)
                block_number = b.get_current_block_num() + int(obj) - 1
            else:
                block_number = obj
            block = Block(block_number, steem_instance=stm)
            if block:
                t = PrettyTable(["Key", "Value"])
                t.align = "l"
                for key in sorted(block):
                    value = block[key]
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
        elif re.match("^[a-zA-Z0-9\-\._]{2,16}$", obj):
            account = Account(obj, steem_instance=stm)
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
                witness = Witness(obj, steem_instance=stm)
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
        elif re.match("^" + stm.prefix + ".{48,55}$", obj):
            account = stm.wallet.getAccountFromPublicKey(obj)
            if account:
                t = PrettyTable(["Account"])
                t.align = "l"
                t.add_row([account])
                print(t)
            else:
                print("Public Key not known" % obj)
        # Post identifier
        elif re.match(".*@.{3,16}/.*$", obj):
            post = Comment(obj, steem_instance=stm)
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


if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        os.environ['SSL_CERT_FILE'] = os.path.join(sys._MEIPASS, 'lib', 'cert.pem')
        cli(sys.argv[1:])
    else:
        cli()
