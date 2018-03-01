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
from beem.storage import configStorage
from beem.version import version as __version__
from datetime import datetime, timedelta
import pytz
from beembase import operations
from beembase.account import PrivateKey, PublicKey
import json
from prettytable import PrettyTable
import math
import random
import logging
import click
log = logging.getLogger(__name__)


@click.group(chain=True)
@click.option(
    '--node', '-n', default="", help="URL for public Steem API")
@click.option(
    '--offline', is_flag=True, default=False, help="Prevent connecting to network")
@click.option(
    '--nobroadcast', '-d', is_flag=True, default=False, help="Do not broadcast")
@click.option(
    '--unsigned', is_flag=True, default=False, help="Nothing will be signed")
@click.option(
    '--blocking', is_flag=True, default=False,
    help="Wait for broadcasted transactions to be included in a block and return full transaction")
@click.option(
    '--bundle', is_flag=True, default=False,
    help="Do not broadcast transactions right away, but allow to bundle operations ")
@click.option(
    '--expiration', '-e', default=30,
    help='Delay in seconds until transactions are supposed to expire(defaults to 60)')
@click.option(
    '--debug', is_flag=True, default=False, help='Enables Debug output')
@click.version_option(version=__version__)
def cli(node, offline, nobroadcast, unsigned, blocking, bundle, expiration, debug):
    stm = Steem(
        node=node,
        nobroadcast=nobroadcast,
        unsigned=unsigned,
        blocking=blocking,
        bundle=bundle,
        expiration=expiration,
        debug=debug
    )
    set_shared_steem_instance(stm)
    pass


@cli.command()
@click.option(
    '--account', '-a', multiple=True)
def balance(account):
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
@click.option(
    '--account', '-a', multiple=True)
def info(account):
    stm = shared_steem_instance()
    for name in account:
        a = Account(name, steem_instance=stm)
        a.print_info()
        print("\n")


if __name__ == "__main__":
    cli()
