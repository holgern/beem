# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes, int, str
from beem.instance import set_shared_steem_instance, shared_steem_instance
from beem.amount import Amount
from beem.price import Price
from beem.account import Account
from beem.steem import Steem
from beem.comment import Comment
from beem.market import Market
from beem.block import Block
from beem.profile import Profile
from beem.witness import Witness, WitnessesRankedByVote, WitnessesVotedByAccount
from beem.blockchain import Blockchain
from beem.utils import formatTimeString
from beem.vote import AccountVotes, ActiveVotes
from beem import exceptions
from beem.version import version as __version__
from datetime import datetime, timedelta
import pytz
from beembase import operations

from beemgraphenebase.account import PrivateKey, PublicKey
import os
import ast
import json
from prettytable import PrettyTable
import math
import random
import logging
import click
import re
click.disable_unicode_literals_warning = True
log = logging.getLogger(__name__)


availableConfigurationKeys = [
    "default_account",
    "default_vote_weight",
    "nodes",
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
    if not password:
        password = os.environ.get("UNLOCK")
    if bool(password):
        stm.wallet.unlock(password)
    else:
        password = click.prompt("Password to unlock wallet", confirmation_prompt=False, hide_input=True)
        stm.wallet.unlock(password)

    if stm.wallet.locked():
        print("Wallet could not be unlocked!")
        return False
    else:
        print("Wallet Unlocked!")
        return True


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
        debug=debug
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
        stm.set_default_account(value)
    elif key == "default_vote_weight":
        stm.set_default_vote_weight(value)
    elif key == "nodes" or key == "node":
        if bool(value) or value != "default":
            stm.set_default_nodes(value)
        else:
            stm.set_default_nodes("")
    else:
        print("wrong key")


@cli.command()
def config():
    """ Shows local configuration
    """
    stm = shared_steem_instance()
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    for key in stm.config:
        # hide internal config data
        if key in availableConfigurationKeys:
            t.add_row([key, stm.config[key]])
    if "default_nodes" in stm.config and bool(stm.config["default_nodes"]):
        node = stm.config["default_nodes"]
    elif "node" in stm.config:
        node = stm.config["node"]
    nodes = json.dumps(node, indent=4)
    t.add_row(["nodes", nodes])
    t.add_row(["data_dir", stm.config.data_dir])
    print(t)


@cli.command()
@click.option(
    '--wipe', is_flag=True, default=False,
    prompt='Do you want to wipe your wallet? Are your sure? This is IRREVERSIBLE! If you dont have a backup you may lose access to your account!',
    help="Delete old wallet. All wallet data are deleted!")
@click.option('--password', prompt=True, hide_input=True,
              confirmation_prompt=True)
def createwallet(wipe, password):
    """ Create new wallet with password
    """
    stm = shared_steem_instance()
    if wipe:
        stm.wallet.wipe(True)
    stm.wallet.create(password)
    set_shared_steem_instance(stm)


@cli.command()
def walletinfo():
    """ Show info about wallet
    """
    stm = shared_steem_instance()
    t = PrettyTable(["Key", "Value"])
    t.align = "l"
    t.add_row(["created", stm.wallet.created()])
    t.add_row(["locked", stm.wallet.locked()])
    t.add_row(["Number of stored keys", len(stm.wallet.getPublicKeys())])
    t.add_row(["sql-file", stm.wallet.keyStorage.sqlDataBaseFile])
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
@click.option('--oldpassword', prompt=True, hide_input=True,
              confirmation_prompt=False, help='Password to unlock wallet')
@click.option('--newpassword', prompt=True, hide_input=True,
              confirmation_prompt=True, help='Set new password to unlock wallet')
def changewalletpassphrase(oldpassword, newpassword):
    """ Change wallet password
    """
    stm = shared_steem_instance()
    if not unlock_wallet(stm, oldpassword):
        return
    stm.wallet.changePassphrase(newpassword)


@cli.command()
@click.argument('account', nargs=-1)
def balance(account):
    """ Shows balance
    """
    stm = shared_steem_instance()
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
        foreign_account = format(PasswordKey(account, pwd, permission).get_public(), stm.prefix)
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
@click.option('--chart', help='Enable charting (requires matplotlib)', is_flag=True)
def orderbook(chart):
    """Obtain orderbook of the internal market"""
    stm = shared_steem_instance()
    market = Market(steem_instance=stm)
    orderbook = market.orderbook(limit=25, raw_data=False)
    t = PrettyTable(["asks-date", "asks", "bids-date", "bids"], hrules=0)
    t.align = "r"
    asks = []
    bids = []
    asks_date = []
    bids_date = []
    n = 0
    for order in orderbook["asks"]:
        asks.append(order)
    if n < len(asks):
        n = len(asks)
    for order in orderbook["bids"]:
        bids.append(order)
    if n < len(bids):
        n = len(bids)
    for order in orderbook["asks_date"]:
        asks_date.append(order)
    if n < len(asks_date):
        n = len(asks_date)
    for order in orderbook["bids_date"]:
        bids_date.append(order)
    if n < len(bids_date):
        n = len(bids_date)
    for i in range(n):
        row = []
        if len(asks_date) > i:
            row.append(formatTimeString(asks_date[i]))
        else:
            row.append([""])
        if len(asks) > i:
            row.append(str(asks[i]))
        else:
            row.append([""])
        if len(bids_date) > i:
            row.append(formatTimeString(bids_date[i]))
        else:
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
    market = Market(steem_instance=stm)
    if not account:
        account = stm.config["default_account"]
    if not price:
        orderbook = market.orderbook(limit=1, raw_data=False)
        if asset == "STEEM" and len(orderbook["bids"]) > 0:
            p = Price(orderbook["bids"][0]["base"], orderbook["bids"][0]["quote"], steem_instance=stm).invert()
        else:
            p = Price(orderbook["asks"][0]["base"], orderbook["asks"][0]["quote"], steem_instance=stm).invert()
        price_ok = click.prompt("Is the following Price ok: %s [y/n]" % (str(p)))
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
    market = Market(steem_instance=stm)
    if not account:
        account = stm.config["default_account"]
    if not price:
        orderbook = market.orderbook(limit=1, raw_data=False)
        if asset == "SBD" and len(orderbook["bids"]) > 0:
            p = Price(orderbook["bids"][0]["base"], orderbook["bids"][0]["quote"], steem_instance=stm).invert()
        else:
            p = Price(orderbook["asks"][0]["base"], orderbook["asks"][0]["quote"], steem_instance=stm).invert()
        price_ok = click.prompt("Is the following Price ok: %s [y/n]" % (str(p)))
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
    market = Market(steem_instance=stm)
    if not account:
        account = stm.config["default_account"]
    acc = Account(account, steem_instance=stm)
    openorders = market.accountopenorders(account=acc)
    t = PrettyTable(["orderid", "created", "order", "account"], hrules=0)
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
    if account:
        witnesses = WitnessesVotedByAccount(account, steem_instance=stm)
    else:
        witnesses = WitnessesRankedByVote(limit=limit, steem_instance=stm)
    witnesses.printAsTable()


@cli.command()
@click.argument('account', nargs=1, required=False)
@click.option('--direction', default="in", help="in or out (default: in)")
@click.option('--days', default=2, help="Limit shown vote history by this amount of days (default: 2)")
def votes(account, direction, days):
    """ List outgoing/incoming account votes
    """
    stm = shared_steem_instance()
    if not account:
        account = stm.config["default_account"]
    utc = pytz.timezone('UTC')
    limit_time = utc.localize(datetime.utcnow()) - timedelta(days=days)
    if direction == "out":
        votes = AccountVotes(account, steem_instance=stm)
        votes.printAsTable(start=limit_time)
    else:
        account = Account(account, steem_instance=stm)
        votes_list = []
        for v in account.history(start=limit_time, only_ops=["vote"]):
            votes_list.append(v)
        votes = ActiveVotes(votes_list, steem_instance=stm)
        votes.printAsTable(votee=account["name"])


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
@click.argument('objects', nargs=-1)
def info(objects):
    """ Show basic blockchain info

        General information about the blockchain, a block, an account,
        a post/comment and a public key
    """
    stm = shared_steem_instance()
    if not objects:
        t = PrettyTable(["Key", "Value"])
        t.align = "l"
        info = stm.get_dynamic_global_properties()
        median_price = stm.get_current_median_history()
        steem_per_mvest = stm.get_steem_per_mvest()
        chain_props = stm.get_chain_properties()
        price = (Amount(median_price["base"]).amount / Amount(
            median_price["quote"]).amount)
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
                b = Blockchain()
                block_number = b.get_current_block_num() + int(obj) - 1
            else:
                block_number = obj
            block = Block(block_number)
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
                            t_value = json.dumps(value[tran_nr - 1], indent=4)
                            t.add_row(["transaction %d/%d" % (tran_nr, len(value)), t_value])
                    elif key == "transaction_ids" and not bool(tran_nr):
                        t.add_row(["Nr. of transaction_ids", len(value)])
                    elif key == "transaction_ids" and bool(tran_nr):
                        if int(tran_nr) < 0:
                            tran_nr = len(value) + int(tran_nr)
                        else:
                            tran_nr = int(tran_nr)
                        if len(value) > tran_nr - 1 and tran_nr > -1:
                            t.add_row(["transaction_id %d/%d" % (int(tran_nr), len(value)), value[tran_nr - 1]])
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
                witness = Witness(obj)
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
            post = Comment(obj)
            post_json = post.json()
            if post_json:
                t = PrettyTable(["Key", "Value"])
                t.align = "l"
                for key in sorted(post_json):
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
    cli()
