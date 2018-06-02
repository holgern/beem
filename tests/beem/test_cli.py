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
from beem.instance import set_shared_steem_instance, shared_steem_instance
from beembase.operationids import getOperationNameForId
from beem.nodelist import NodeList

wif = "5Jt2wTfhUt5GkZHV1HYVfkEaJ6XnY8D2iA4qjtK9nnGXAhThM3w"
posting_key = "5Jh1Gtu2j4Yi16TfhoDmg8Qj3ULcgRi7A49JXdfUUTVPkaFaRKz"
memo_key = "5KPbCuocX26aMxN9CDPdUex4wCbfw9NoT5P7UhcqgDwxXa47bit"
pub_key = "STX52xMqKegLk4tdpNcUXU9Rw5DtdM9fxf3f12Gp55v1UjLX3ELZf"


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodelist = NodeList()
        stm = shared_steem_instance()
        stm.config.refreshBackup()
        runner = CliRunner()
        result = runner.invoke(cli, ['-o', 'set', 'default_vote_weight', '100'])
        if result.exit_code != 0:
            raise AssertionError(str(result))
        result = runner.invoke(cli, ['-o', 'set', 'default_account', 'beem'])
        if result.exit_code != 0:
            raise AssertionError(str(result))
        result = runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        if result.exit_code != 0:
            raise AssertionError(str(result))
        result = runner.invoke(cli, ['createwallet', '--wipe'], input="test\ntest\n")
        if result.exit_code != 0:
            raise AssertionError(str(result))
        result = runner.invoke(cli, ['addkey'], input="test\n" + wif + "\n")
        if result.exit_code != 0:
            raise AssertionError(str(result))
        result = runner.invoke(cli, ['addkey'], input="test\n" + posting_key + "\n")
        if result.exit_code != 0:
            raise AssertionError(str(result))
        result = runner.invoke(cli, ['addkey'], input="test\n" + memo_key + "\n")
        if result.exit_code != 0:
            raise AssertionError(str(result))

    @classmethod
    def tearDownClass(cls):
        stm = shared_steem_instance()
        stm.config.recover_with_latest_backup()

    def test_balance(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['balance', 'beem', 'beem1'])
        self.assertEqual(result.exit_code, 0)

    def test_interest(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['interest', 'beem', 'beem1'])
        self.assertEqual(result.exit_code, 0)

    def test_config(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['config'])
        self.assertEqual(result.exit_code, 0)

    def test_addkey(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['createwallet', '--wipe'], input="test\ntest\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['addkey'], input="test\n" + wif + "\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['addkey'], input="test\n" + posting_key + "\n")
        self.assertEqual(result.exit_code, 0)

    def test_parsewif(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['parsewif'], input=wif + "\nexit\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['parsewif', '--unsafe-import-key', wif])
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
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['info'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['info', 'beem'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['info', '100'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['info', '--', '-1'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['info', pub_key])
        self.assertEqual(result.exit_code, 0)

    def test_info2(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', ''])
        result = runner.invoke(cli, ['info', '--', '-1:1'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['info', 'gtg'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['info', "@gtg/witness-gtg-log"])
        self.assertEqual(result.exit_code, 0)
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])

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
        result = runner.invoke(cli, ['-o', 'set', 'set_default_vote_weight', '100'])
        self.assertEqual(result.exit_code, 0)

    def test_upvote(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-o', 'upvote', '@test/abcd'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-o', 'upvote', '@test/abcd', '100'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-o', 'upvote', '--weight', '100', '@test/abcd'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_downvote(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-o', 'downvote', '@test/abcd'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-o', 'downvote', '@test/abcd', '100'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-o', 'downvote', '--weight', '100', '@test/abcd'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_transfer(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['transfer', 'beem1', '1', 'SBD', 'test'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_powerdownroute(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['powerdownroute', 'beem1'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_convert(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['convert', '1'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_powerup(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['powerup', '1'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_powerdown(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['powerdown', '1e3'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['powerdown', '0'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_updatememokey(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['-d', 'updatememokey'], input="test\ntest\ntest\n")
        self.assertEqual(result.exit_code, 0)

    def test_permissions(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['permissions', 'test'])
        self.assertEqual(result.exit_code, 0)

    def test_follower(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['follower', 'beem2'])
        self.assertEqual(result.exit_code, 0)

    def test_following(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['following', 'beem'])
        self.assertEqual(result.exit_code, 0)

    def test_muter(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['muter', 'beem2'])
        self.assertEqual(result.exit_code, 0)

    def test_muting(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['muting', 'beem'])
        self.assertEqual(result.exit_code, 0)

    def test_allow_disallow(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['-d', 'allow', '--account', 'beem', '--permission', 'posting', 'beem1'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-d', 'disallow', '--account', 'beem', '--permission', 'posting', 'beem1'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_witnesses(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['witnesses'])
        self.assertEqual(result.exit_code, 0)

    def test_votes(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', ''])
        result = runner.invoke(cli, ['votes', '--direction', 'out', 'test'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['votes', '--direction', 'in', 'test'])
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        self.assertEqual(result.exit_code, 0)

    def test_approvewitness(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['-o', 'approvewitness', 'beem1'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_disapprovewitness(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['-o', 'disapprovewitness', 'beem1'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_newaccount(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['-d', 'newaccount', 'beem3'], input="test\ntest\ntest\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-d', 'newaccount', '--fee', '6 STEEM', 'beem3'], input="test\ntest\ntest\n")
        self.assertEqual(result.exit_code, 0)

    def test_importaccount(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['importaccount', '--roles', '["owner", "active", "posting", "memo"]', 'beem2'], input="test\ntest\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['delkey', '--confirm', 'STX7mLs2hns87f7kbf3o2HBqNoEaXiTeeU89eVF6iUCrMQJFzBsPo'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['delkey', '--confirm', 'STX7rUmnpnCp9oZqMQeRKDB7GvXTM9KFvhzbA3AKcabgTBfQZgHZp'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['delkey', '--confirm', 'STX6qGWHsCpmHbphnQbS2yfhvhJXDUVDwnsbnrMZkTqfnkNEZRoLP'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['delkey', '--confirm', 'STX8Wvi74GYzBKgnUmiLvptzvxmPtXfjGPJL8QY3rebecXaxGGQyV'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_orderbook(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', ''])
        result = runner.invoke(cli, ['orderbook'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['orderbook', '--show-date'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['orderbook', '--chart'])
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        self.assertEqual(result.exit_code, 0)

    def test_buy(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-d', 'buy', '1', 'STEEM', '2.2'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-d', 'buy', '1', 'STEEM'], input="y\ntest\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-d', 'buy', '1', 'SBD', '2.2'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-d', 'buy', '1', 'SBD'], input="y\ntest\n")
        self.assertEqual(result.exit_code, 0)

    def test_sell(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-d', 'sell', '1', 'STEEM', '2.2'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-d', 'sell', '1', 'SBD', '2.2'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-d', 'sell', '1', 'STEEM'], input="y\ntest\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-d', 'sell', '1', 'SBD'], input="y\ntest\n")
        self.assertEqual(result.exit_code, 0)

    def test_cancel(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-d', 'cancel', '5'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_openorders(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['openorders'])
        self.assertEqual(result.exit_code, 0)

    def test_resteem(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-o', 'resteem', '@test/abcde'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_follow_unfollow(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['follow', 'beem1'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['unfollow', 'beem1'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_mute_unmute(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['mute', 'beem1'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['unfollow', 'beem1'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_witnesscreate(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        result = runner.invoke(cli, ['-d', 'witnesscreate', 'beem', pub_key], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_witnessupdate(self):
        runner = CliRunner()
        runner.invoke(cli, ['-o', 'set', 'nodes', ''])
        result = runner.invoke(cli, ['-o', 'nextnode'])
        runner.invoke(cli, ['-o', 'witnessupdate', 'gtg', '--maximum_block_size', 65000, '--account_creation_fee', 0.1, '--sbd_interest_rate', 0, '--url', 'https://google.de', '--signing_key', wif])
        self.assertEqual(result.exit_code, 0)

    def test_profile(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['setprofile', 'url', 'https://google.de'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['delprofile', 'url'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_claimreward(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-d', 'claimreward'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_power(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['power'])
        self.assertEqual(result.exit_code, 0)

    def test_nextnode(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', ''])
        result = runner.invoke(cli, ['-o', 'nextnode'])
        self.assertEqual(result.exit_code, 0)
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])

    def test_pingnode(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['pingnode'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['pingnode', '--raw'])
        self.assertEqual(result.exit_code, 0)

    def test_currentnode(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', ''])
        result = runner.invoke(cli, ['currentnode'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['currentnode', '--url'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['currentnode', '--version'])
        self.assertEqual(result.exit_code, 0)
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])

    def test_ticker(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', ''])
        result = runner.invoke(cli, ['ticker'])
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        self.assertEqual(result.exit_code, 0)

    def test_pricehistory(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', ''])
        result = runner.invoke(cli, ['pricehistory'])
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        self.assertEqual(result.exit_code, 0)

    def test_pending(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', ''])
        result = runner.invoke(cli, ['pending', 'test'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['pending', '--post', '--comment', '--curation', 'test'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['pending', '--post', '--comment', '--curation', '--permlink', 'test'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['pending', '--post', '--comment', '--curation', '--author', 'test'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['pending', '--post', '--comment', '--curation', '--author', '--title', 'test'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['pending', '--post', '--comment', '--curation', '--author', '--permlink', '--length', '30', 'test'])
        self.assertEqual(result.exit_code, 0)
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])

    def test_rewards(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', ''])
        result = runner.invoke(cli, ['rewards', 'test'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['rewards', '--post', '--comment', '--curation', 'test'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['rewards', '--post', '--comment', '--curation', '--permlink', 'test'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['rewards', '--post', '--comment', '--curation', '--author', 'test'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['rewards', '--post', '--comment', '--curation', '--author', '--title', 'test'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['rewards', '--post', '--comment', '--curation', '--author', '--permlink', '--length', '30', 'test'])
        self.assertEqual(result.exit_code, 0)
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])

    def test_curation(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', ''])
        result = runner.invoke(cli, ['curation', "@gtg/witness-gtg-log"])
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        self.assertEqual(result.exit_code, 0)

    def test_verify(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', ''])
        result = runner.invoke(cli, ['verify', '--trx', '0'])
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        self.assertEqual(result.exit_code, 0)

    def test_tradehistory(self):
        runner = CliRunner()
        nodelist = NodeList()
        runner.invoke(cli, ['-o', 'set', 'nodes', ''])
        result = runner.invoke(cli, ['tradehistory'])
        runner.invoke(cli, ['-o', 'set', 'nodes', str(nodelist.get_testnet())])
        self.assertEqual(result.exit_code, 0)
