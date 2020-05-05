from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from builtins import super
import unittest
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
        nodelist.update_nodes()
        nodelist.update_nodes(steem_instance=Steem(node=nodelist.get_nodes(hive=True), num_retries=10))
        cls.node_list = nodelist.get_nodes(hive=True)
       
        # stm = shared_steem_instance()
        # stm.config.refreshBackup()
        runner = CliRunner()
        result = runner.invoke(cli, ['-o', 'set', 'default_vote_weight', '100'])
        if result.exit_code != 0:
            raise AssertionError(str(result))
        result = runner.invoke(cli, ['-o', 'set', 'default_account', 'beem'])
        if result.exit_code != 0:
            raise AssertionError(str(result))
        result = runner.invoke(cli, ['-o', 'set', 'nodes', str(cls.node_list)])
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
        runner = CliRunner()
        result = runner.invoke(cli, ['updatenodes', '--hive'])

    def test_balance(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['balance', 'beembot', 'beempy'])
        self.assertEqual(result.exit_code, 0)

    def test_interest(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'interest', 'beembot', 'beempy'])
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

    def test_changerecovery(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'changerecovery', '-a', 'beembot', 'holger80'], input=wif + "\nexit\n")
        self.assertEqual(result.exit_code, 0)

    def test_delkey(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['delkey', '--confirm', pub_key], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['addkey'], input="test\n" + posting_key + "\n")
        # self.assertEqual(result.exit_code, 0)

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
        result = runner.invoke(cli, ['info', 'beembot'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['info', '100'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['info', '--', '-1'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['info', pub_key])
        self.assertEqual(result.exit_code, 0)

    def test_info2(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['info', '--', '42725832:-1'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['info', '--', '42725832:1'])
        self.assertEqual(result.exit_code, 0)        
        result = runner.invoke(cli, ['info', 'gtg'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['info', "@gtg/witness-gtg-log"])
        self.assertEqual(result.exit_code, 0)

    def test_changepassword(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['changewalletpassphrase'], input="test\ntest\ntest\n")
        self.assertEqual(result.exit_code, 0)

    def test_walletinfo(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['walletinfo'])
        self.assertEqual(result.exit_code, 0)

    def test_keygen(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['keygen'])
        self.assertEqual(result.exit_code, 0)

    def test_set(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-o', 'set', 'set_default_vote_weight', '100'])
        self.assertEqual(result.exit_code, 0)

    def test_upvote(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'upvote', '@steemit/firstpost'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-dt', 'upvote', '--weight', '100', '@steemit/firstpost'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_downvote(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'downvote', '--weight', '100', '@steemit/firstpost'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_download(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'download', '-a', 'steemit', 'firstpost'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-dt', 'download', '@steemit/firstpost'])
        self.assertEqual(result.exit_code, 0)

    def test_transfer(self):
        stm = shared_steem_instance()
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'transfer', 'beembot', '1', stm.sbd_symbol, 'test'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_powerdownroute(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'powerdownroute', 'beembot'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_convert(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'convert', '1'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_powerup(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'powerup', '1'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_powerdown(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'powerdown', '1e3'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-dt', 'powerdown', '0'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_updatememokey(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'updatememokey'], input="test\ntest\ntest\n")
        self.assertEqual(result.exit_code, 0)

    def test_permissions(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['permissions', 'beembot'])
        self.assertEqual(result.exit_code, 0)

    def test_follower(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['follower', 'beembot'])
        self.assertEqual(result.exit_code, 0)

    def test_following(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['following', 'beembot'])
        self.assertEqual(result.exit_code, 0)

    def test_muter(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['muter', 'beembot'])
        self.assertEqual(result.exit_code, 0)

    def test_about(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['about'])
        self.assertEqual(result.exit_code, 0)

    def test_muting(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['muting', 'beem'])
        self.assertEqual(result.exit_code, 0)

    def test_allow_disallow(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'allow', '--account', 'beembot', '--permission', 'posting', 'beempy'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-dt', 'disallow', '--account', 'holger80', '--permission', 'posting', 'rewarding'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_witnesses(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['witnesses'])
        self.assertEqual(result.exit_code, 0)

    def test_votes(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['votes', '--direction', 'out', 'fullnodeupdate'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['votes', '--direction', 'in', 'fullnodeupdate'])
        self.assertEqual(result.exit_code, 0)

    def test_approvewitness(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'approvewitness', '-a', 'beempy', 'holger80'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_disapprovewitness(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'disapprovewitness',  '-a', 'beempy', 'holger80'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_addproxy(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'setproxy', '-a', 'beempy', 'holger80'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_delproxy(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'delproxy',  '-a', 'fullnodeupdate'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_newaccount(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'newaccount', 'beem3'], input="test\ntest\ntest\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-dt', 'newaccount', '--owner', 'STM7mLs2hns87f7kbf3o2HBqNoEaXiTeeU89eVF6iUCrMQJFzBsPo',
                                     '--active', 'STM7rUmnpnCp9oZqMQeRKDB7GvXTM9KFvhzbA3AKcabgTBfQZgHZp',
                                     '--posting', 'STM6qGWHsCpmHbphnQbS2yfhvhJXDUVDwnsbnrMZkTqfnkNEZRoLP',
                                     '--memo', 'STM8Wvi74GYzBKgnUmiLvptzvxmPtXfjGPJL8QY3rebecXaxGGQyV', 'beem3'], input="test\ntest\n")
        self.assertEqual(result.exit_code, 0)                            

    def test_changekeys(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dx', 'changekeys', '--owner', 'STM7mLs2hns87f7kbf3o2HBqNoEaXiTeeU89eVF6iUCrMQJFzBsPo',
                                     '--active', 'STM7rUmnpnCp9oZqMQeRKDB7GvXTM9KFvhzbA3AKcabgTBfQZgHZp',
                                     '--posting', 'STM6qGWHsCpmHbphnQbS2yfhvhJXDUVDwnsbnrMZkTqfnkNEZRoLP',
                                     '--memo', 'STM8Wvi74GYzBKgnUmiLvptzvxmPtXfjGPJL8QY3rebecXaxGGQyV', 'beem'], input="test\ntest\n")
        self.assertEqual(result.exit_code, 0)     

    @unittest.skip
    def test_importaccount(self):
        runner = CliRunner()
        runner.invoke(cli, ['-o', 'set', 'nodes', str(self.node_list)])
        result = runner.invoke(cli, ['importaccount', '--roles', '["owner", "active", "posting", "memo"]', 'beem2'], input="test\numybjvCafrt8LdoCjEimQiQ4\n")
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
        result = runner.invoke(cli, ['orderbook'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['orderbook', '--show-date'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['orderbook', '--chart'])
        self.assertEqual(result.exit_code, 0)

    def test_buy(self):
        stm = shared_steem_instance()
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', '-x', 'buy', '1', stm.steem_symbol, '2.2'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-dt', '-x', 'buy', '1', stm.steem_symbol], input="y\ntest\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-dt', '-x', 'buy', '1', stm.sbd_symbol, '2.2'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-dt', '-x', 'buy', '1', stm.sbd_symbol], input="y\ntest\n")
        self.assertEqual(result.exit_code, 0)

    def test_sell(self):
        stm = shared_steem_instance()
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', '-x', 'sell', '1', stm.steem_symbol, '2.2'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-dt', '-x', 'sell', '1', stm.sbd_symbol, '2.2'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-dt', '-x', 'sell', '1', stm.steem_symbol], input="y\ntest\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-dt', '-x', 'sell', '1', stm.sbd_symbol], input="y\ntest\n")
        self.assertEqual(result.exit_code, 0)

    def test_cancel(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'cancel', '5'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_openorders(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['openorders'])
        self.assertEqual(result.exit_code, 0)

    def test_reblog(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dto', 'reblog', '@steemit/firstpost'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_follow_unfollow(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dto', 'follow', 'beempy'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-dto', 'unfollow', 'beempy'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_mute_unmute(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dto', 'mute', 'beempy'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-dto', 'unfollow', 'beempy'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_witnesscreate(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'witnesscreate', 'beem', pub_key], input="test\n")

    def test_witnessupdate(self):
        runner = CliRunner()
        runner.invoke(cli, ['-dt', 'witnessupdate', 'gtg', '--maximum_block_size', 65000, '--account_creation_fee', 0.1, '--sbd_interest_rate', 0, '--url', 'https://google.de', '--signing_key', wif])

    def test_profile(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'setprofile', 'url', 'https://google.de'], input="test\n")
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['-dt', 'delprofile', 'url'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_claimreward(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['-dt', 'claimreward'], input="test\n")
        result = runner.invoke(cli, ['-dt', 'claimreward', '--claim_all_steem'], input="test\n")
        result = runner.invoke(cli, ['-dt', 'claimreward', '--claim_all_sbd'], input="test\n")
        result = runner.invoke(cli, ['-dt', 'claimreward', '--claim_all_vests'], input="test\n")
        self.assertEqual(result.exit_code, 0)

    def test_power(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['power', 'holger80'])
        self.assertEqual(result.exit_code, 0)

    def test_nextnode(self):
        runner = CliRunner()
        runner.invoke(cli, ['-o', 'set', 'nodes', self.node_list])
        result = runner.invoke(cli, ['-o', 'nextnode'])
        self.assertEqual(result.exit_code, 0)
        runner.invoke(cli, ['-o', 'set', 'nodes', str(self.node_list)])

    def test_pingnode(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['pingnode'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['pingnode', '--raw'])
        self.assertEqual(result.exit_code, 0)

    def test_updatenodes(self):
        runner = CliRunner()
        runner.invoke(cli, ['-o', 'set', 'nodes', self.node_list])
        result = runner.invoke(cli, ['updatenodes', '--hive', '--test'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['updatenodes', '--steem'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['updatenodes'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['updatenodes', '--hive'])
        self.assertEqual(result.exit_code, 0)        
        result = runner.invoke(cli, ['updatenodes'])
        self.assertEqual(result.exit_code, 0)        
        runner.invoke(cli, ['-o', 'set', 'nodes', str(self.node_list)])

    def test_currentnode(self):
        runner = CliRunner()
        runner.invoke(cli, ['-o', 'set', 'nodes', self.node_list])
        result = runner.invoke(cli, ['currentnode'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['currentnode', '--url'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['currentnode', '--version'])
        self.assertEqual(result.exit_code, 0)
        runner.invoke(cli, ['-o', 'set', 'nodes', str(self.node_list)])

    def test_ticker(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['ticker'])
        self.assertEqual(result.exit_code, 0)

    def test_pricehistory(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['pricehistory'])
        self.assertEqual(result.exit_code, 0)

    def test_pending(self):
        runner = CliRunner()
        account_name = "fullnodeupdate"
        result = runner.invoke(cli, ['pending', account_name])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['pending', '--post', '--comment', account_name])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['pending', '--curation', '--permlink', '--days', '1', account_name])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['pending', '--post', '--comment', '--author', '--permlink', '--length', '30', '--days', '1', account_name])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['pending', '--post', '--author', '--title', '--days', '1', account_name])
        self.assertEqual(result.exit_code, 0)

    def test_rewards(self):
        runner = CliRunner()
        account_name = "fullnodeupdate"
        result = runner.invoke(cli, ['rewards', account_name])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['rewards', '--post', '--comment', '--curation', account_name])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['rewards', '--post', '--comment', '--curation', '--permlink', account_name])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['rewards', '--post', '--comment', '--curation', '--author', account_name])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['rewards', '--post', '--comment', '--author', '--title', account_name])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['rewards', '--post', '--comment', '--author', '--permlink', '--length', '30', account_name])
        self.assertEqual(result.exit_code, 0)

    def test_curation(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['curation', "@gtg/witness-gtg-log"])
        self.assertEqual(result.exit_code, 0)

    def test_verify(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['verify', '--trx', '3', '25304468'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['verify', '--trx', '5', '25304468'])
        self.assertEqual(result.exit_code, 0)
        result = runner.invoke(cli, ['verify', '--trx', '0'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.exit_code, 0)

    def test_tradehistory(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['tradehistory'])
        self.assertEqual(result.exit_code, 0)
