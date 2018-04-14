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
pub_key = "STX52xMqKegLk4tdpNcUXU9Rw5DtdM9fxf3f12Gp55v1UjLX3ELZf"


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        runner = CliRunner()
        runner.invoke(cli, ['set', 'default_vote_weight', '100'])
        runner.invoke(cli, ['set', 'default_account', 'beem'])
        runner.invoke(cli, ['set', 'nodes', 'wss://testnet.steem.vc'])
        runner.invoke(cli, ['createwallet'], input="y\ntest\ntest\n")
        runner.invoke(cli, ['addkey'], input="test\n" + wif + "\n")
        # runner.invoke(cli, ['changewalletpassphrase', '--password test'])

    def test_balance(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['balance', 'beem', 'beem1'])
        self.assertEqual(result.exit_code, 0)

    def test_interest(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['interest', 'beem', 'beem1'])
        self.assertEqual(result.exit_code, 0)

    def test_config(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['config'])
        self.assertEqual(result.exit_code, 0)

    def test_addkey(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['createwallet'], input="y\ntest\ntest\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['addkey'], input="test\n" + wif + "\n")
        self.assertEqual(result.exit_code, 0)

    def test_delkey(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['delkey', '--confirm', pub_key], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['addkey'], input="test\n" + wif + "\n")
        self.assertEqual(result.exit_code, 0)

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
        result = runner.invoke(cli, ['changewalletpassphrase'], input="test\ntest\ntest\n")
        self.assertEqual(result.exit_code, 0)

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
        result = runner.invoke(cli, ['upvote', '--weight 100', '@test/abcd'], input="test\n")
        self.assertEqual(result.exit_code, 2)

    def test_downvote(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['downvote', '--weight 100', '@test/abcd'], input="test\n")
        self.assertEqual(result.exit_code, 2)

    def test_transfer(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['transfer', 'beem1', '1', 'SBD', 'test'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_powerdownroute(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['powerdownroute', 'beem1'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_convert(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['convert', '1'], input="test\n")
        self.assertEqual(result.exit_code, 0)
