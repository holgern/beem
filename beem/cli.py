# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes, int, str
from beem.instance import set_shared_steem_instance, shared_steem_instance
from beem.amount import Amount
from beem.account import Account
from beem.steem import Steem
from beem.comment import Comment
from beem.block import Block
from beem.witness import Witness
from beem.blockchain import Blockchain
from beem import exceptions
from beem.version import version as __version__
from datetime import datetime, timedelta
import pytz
from beembase import operations

from beemgraphenebase.account import PrivateKey, PublicKey
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


def unlock_wallet(stm, password):
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
    '--blocking', is_flag=True, default=False,
    help="Wait for broadcasted transactions to be included in a block and return full transaction")
@click.option(
    '--bundle', is_flag=True, default=False,
    help="Do not broadcast transactions right away, but allow to bundle operations ")
@click.option(
    '--expires', '-e', default=30,
    help='Delay in seconds until transactions are supposed to expire(defaults to 60)')
@click.option(
    '--verbose', '-v', default=3, help='Verbosity')
@click.version_option(version=__version__)
def cli(node, offline, no_broadcast, no_wallet, unsigned, blocking, bundle, expires, verbose):

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
        blocking=blocking,
        bundle=bundle,
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
    # t.add_row(["getAccounts", str(stm.wallet.getAccounts())])
    # t.add_row(["getPublicKeys", str(stm.wallet.getPublicKeys())])
    print(t)


@cli.command()
@click.option('--password', prompt=True, hide_input=True,
              confirmation_prompt=False, help='Password to unlock wallet')
@click.option('--unsafe-import-key', prompt='Enter private key', hide_input=False,
              confirmation_prompt=False, help='Private key to import to wallet (unsafe, unless shell history is deleted afterwards)')
def addkey(password, unsafe_import_key):
    """ Add key to wallet

        When no [OPTION] is given, a password prompt for unlocking the wallet
        and a prompt for entering the private key are shown.
    """
    stm = shared_steem_instance()
    if not unlock_wallet(stm, password):
        return
    stm.wallet.addPrivateKey(unsafe_import_key)
    set_shared_steem_instance(stm)


@cli.command()
@click.option('--confirm',
              prompt='Are your sure? This is IRREVERSIBLE! If you dont have a backup you may lose access to your account!',
              hide_input=False, callback=prompt_flag_callback, is_flag=True,
              confirmation_prompt=False, help='Please confirm!')
@click.option('--password', prompt=True, hide_input=True,
              confirmation_prompt=False, help='Password to unlock wallet')
@click.argument('pub')
def delkey(confirm, password, pub):
    """ Delete key from the wallet

        PUB is the public key from the private key
        which will be deleted from the wallet
    """
    stm = shared_steem_instance()
    if not unlock_wallet(stm, password):
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
@click.option('--password', prompt=True, hide_input=True,
              confirmation_prompt=False, help='Password to unlock wallet')
def upvote(post, vote_weight, account, weight, password):
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
    if not unlock_wallet(stm, password):
        return
    try:
        post = Comment(post, steem_instance=stm)
        post.upvote(weight, voter=account)
    except Exception as e:
        log.error(str(e))


@cli.command()
@click.argument('post', nargs=1)
@click.argument('vote_weight', nargs=1, required=False)
@click.option('--account', '-a', help='Voter account name')
@click.option('--weight', '-w', default=100.0, help='Vote weight (from 0.1 to 100.0)')
@click.option('--password', prompt=True, hide_input=True,
              confirmation_prompt=False, help='Password to unlock wallet')
def downvote(post, vote_weight, account, weight, password):
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
    if not unlock_wallet(stm, password):
        return
    try:
        post = Comment(post)
    except Exception as e:
        log.error(str(e))
        return
    post.downvote(weight, voter=account)


@cli.command()
@click.argument('to', nargs=1)
@click.argument('amount', nargs=1)
@click.argument('asset', nargs=1, callback=asset_callback)
@click.argument('memo', nargs=1, required=False)
@click.option('--password', prompt=True, hide_input=True, default='',
              confirmation_prompt=False, help='Password to unlock wallet')
@click.option('--account', '-a', help='Transfer from this account')
def transfer(to, amount, asset, memo, password, account):
    """Transfer SBD/STEEM"""
    stm = shared_steem_instance()
    if not account:
        account = stm.config["default_account"]
    if not bool(memo):
        memo = ''
    if not unlock_wallet(stm, password):
        return
    acc = Account(account, steem_instance=stm)
    tx = acc.transfer(to, amount, asset, memo)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1)
@click.option('--password', prompt=True, hide_input=True,
              confirmation_prompt=False, help='Password to unlock wallet')
@click.option('--account', '-a', help='Powerup from this account')
@click.option('--to', help='Powerup this account', default=None)
def powerup(amount, password, account, to):
    """Power up (vest STEEM as STEEM POWER)"""
    stm = shared_steem_instance()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm, password):
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
@click.option('--password', prompt=True, hide_input=True,
              confirmation_prompt=False, help='Password to unlock wallet')
@click.option('--account', '-a', help='Powerup from this account')
def powerdown(amount, password, account):
    """Power down (start withdrawing VESTS from Steem POWER)

        amount is in VESTS
    """
    stm = shared_steem_instance()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm, password):
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
@click.option('--password', prompt=True, hide_input=True,
              confirmation_prompt=False, help='Password to unlock wallet')
@click.option('--account', '-a', help='Powerup from this account')
@click.option('--auto_vest', help='Set to true if the from account should receive the VESTS as'
              'VESTS, or false if it should receive them as STEEM.', is_flag=True)
def powerdownroute(to, percentage, password, account, auto_vest):
    """Setup a powerdown route"""
    stm = shared_steem_instance()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm, password):
        return
    acc = Account(account, steem_instance=stm)
    tx = acc.set_withdraw_vesting_route(to, percentage, auto_vest=auto_vest)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1)
@click.option('--password', prompt=True, hide_input=True,
              confirmation_prompt=False, help='Password to unlock wallet')
@click.option('--account', '-a', help='Powerup from this account')
def convert(amount, password, account):
    """Convert STEEMDollars to Steem (takes a week to settle)"""
    stm = shared_steem_instance()
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm, password):
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
        price = (Amount(median_price["base"]).amount / Amount(
            median_price["quote"]).amount)
        for key in info:
            t.add_row([key, info[key]])
        t.add_row(["steem per mvest", steem_per_mvest])
        t.add_row(["internal price", price])
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
                        if len(value) > tran_nr and tran_nr > -1:
                            t_value = json.dumps(value[tran_nr], indent=4)
                            t.add_row(["transaction %d/%d" % (tran_nr, len(value)), t_value])
                    elif key == "transaction_ids" and bool(tran_nr):
                        if int(tran_nr) < 0:
                            tran_nr = len(value) + int(tran_nr)
                        else:
                            tran_nr = int(tran_nr)
                        if len(value) > int(tran_nr) and int(tran_nr) > -1:
                            t.add_row(["transaction_id %d/%d" % (int(tran_nr), len(value)), value[int(tran_nr)]])
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
        elif re.match("^STM.{48,55}$", obj):
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
