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
from beemgraphenebase.account import PrivateKey
from beem.cli import cli, balance
from beem.instance import set_shared_steem_instance
from beembase.operationids import getOperationNameForId
from beem.utils import get_node_list

wif = "5Jt2wTfhUt5GkZHV1HYVfkEaJ6XnY8D2iA4qjtK9nnGXAhThM3w"


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        runner = CliRunner()
        runner.invoke(cli, ['set', 'default_vote_weight', '100'])
        runner.invoke(cli, ['set', 'default_account', 'beem'])
        runner.invoke(cli, ['set', 'nodes', 'wss://testnet.steem.vc'])
        runner.invoke(cli, ['createwallet', '--wipe', '--password test'], input='y\n')
        runner.invoke(cli, ['addkey', '--password test', '--unsafe-import-key ' + wif])
        # runner.invoke(cli, ['changewalletpassphrase', '--password test'])

    def test_balance(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['balance', '-atest'])
        self.assertEqual(result.exit_code, 0)

    def test_config(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['config'])
        self.assertEqual(result.exit_code, 0)

    def test_addkey(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['createwallet', '--wipe', '--password test'], input='y\n')
        self.assertEqual(result.exit_code, 2)
        result = runner.invoke(cli, ['addkey', '--password test', '--unsafe-import-key ' + wif])
        self.assertEqual(result.exit_code, 2)

    def test_delkey(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['delkey', '--password test', wif])
        self.assertEqual(result.exit_code, 2)
        result = runner.invoke(cli, ['addkey', '--password test', '--unsafe-import-key ' + wif])
        self.assertEqual(result.exit_code, 2)

    def test_listkeys(self):
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
        result = runner.invoke(cli, ['info', 'beem'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['info', '100'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['info', '--', '-1'])
        self.assertEqual(result.exit_code, 0)

    def test_changepassword(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['changewalletpassphrase', '--password test'])
        self.assertEqual(result.exit_code, 2)

    def test_walletinfo(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['walletinfo'])
        self.assertEqual(result.exit_code, 0)

    def test_set(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['set', 'set_default_vote_weight', '100'])
        self.assertEqual(result.exit_code, 0)

    def test_upvote(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['upvote', '@test/abcd', '--weight 100'], input='test\n')
        self.assertEqual(result.exit_code, 0)

    def test_downvote(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['downvote', '@test/abcd', '--weight 100'], input='test\n')
        self.assertEqual(result.exit_code, 0)

    def test_transfer(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['transfer', 'beem1', '1', 'SBD', 'test'], input='test\n')
        self.assertEqual(result.exit_code, 0)
