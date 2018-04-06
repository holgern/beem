from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from builtins import super
import unittest
import mock
import click
from click.testing import CliRunner
from pprint import pprint
from beem import Steem, exceptions
from beem.account import Account
from beem.amount import Amount
from beem.cli import cli, balance
from beem.instance import set_shared_steem_instance
from beembase.operationids import getOperationNameForId
from beem.utils import get_node_list

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bts = Steem(
            node=get_node_list(appbase=False),
            nobroadcast=True,
            bundle=False,
            # Overwrite wallet to use this list of wifs only
            wif={"active": wif},
            num_retries=10
        )
        self.bts.set_default_account("test")
        set_shared_steem_instance(self.bts)

    def test_balance(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['balance', '-atest'])
        self.assertEqual(result.exit_code, 0)

    def test_config(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['config'])
        self.assertEqual(result.exit_code, 0)

    def test_listkeys(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['addkey', '--password test', '--key ' + wif])
        self.assertEqual(result.exit_code, 2)

    def test_addkeys(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['listkeys'])
        self.assertEqual(result.exit_code, 0)

    def test_listaccounts(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['listaccounts'])
        self.assertEqual(result.exit_code, 0)

    def test_info(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['info'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['info', 'test'])
        self.assertEqual(result.exit_code, 0)

    def test_changepassword(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['changewalletpassphrase', '--password test'])
        self.assertEqual(result.exit_code, 2)

    def test_walletinfo(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['walletinfo'])
        self.assertEqual(result.exit_code, 0)

    def test_createwallet(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['createwallet', '--password test', '--wipe True'])
        self.assertEqual(result.exit_code, 2)

    def test_set(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['set', '-w 100'])
        self.assertEqual(result.exit_code, 0)
