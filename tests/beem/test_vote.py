from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from parameterized import parameterized
from pprint import pprint
from beem import Steem
from beem.comment import Comment
from beem.vote import Vote, ActiveVotes, AccountVotes
from beem.instance import set_shared_steem_instance
from beem.utils import get_node_list, construct_authorperm, resolve_authorperm, resolve_authorpermvoter

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bts = Steem(
            node=get_node_list(appbase=False),
            nobroadcast=True,
            keys={"active": wif},
            num_retries=10
        )
        self.appbase = Steem(
            node=get_node_list(appbase=True),
            nobroadcast=True,
            keys={"active": wif},
            num_retries=10
        )
        # from getpass import getpass
        # self.bts.wallet.unlock(getpass())
        set_shared_steem_instance(self.bts)
        self.bts.set_default_account("test")
        self.authorpermvoter = u"@gtg/ffdhu-gtg-witness-log|gandalf"
        [author, permlink, voter] = resolve_authorpermvoter(self.authorpermvoter)
        self.author = author
        self.permlink = permlink
        self.voter = voter
        self.authorperm = construct_authorperm(author, permlink)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_vote(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        vote = Vote(self.authorpermvoter, steem_instance=bts)
        self.assertEqual(self.voter, vote["voter"])
        self.assertEqual(self.author, vote["author"])
        self.assertEqual(self.permlink, vote["permlink"])

        vote = Vote(self.voter, authorperm=self.authorperm, steem_instance=bts)
        self.assertEqual(self.voter, vote["voter"])
        self.assertEqual(self.author, vote["author"])
        self.assertEqual(self.permlink, vote["permlink"])
        vote_json = vote.json()
        self.assertEqual(self.voter, vote_json["voter"])
        self.assertEqual(self.voter, vote.voter)
        self.assertTrue(vote.weight >= 0)
        self.assertTrue(vote.sbd >= 0)
        self.assertTrue(vote.rshares >= 0)
        self.assertTrue(vote.percent >= 0)
        self.assertTrue(vote.reputation is not None)
        self.assertTrue(vote.rep is not None)
        self.assertTrue(vote.time is not None)
        vote.refresh()
        self.assertEqual(self.voter, vote["voter"])
        self.assertEqual(self.author, vote["author"])
        self.assertEqual(self.permlink, vote["permlink"])
        vote_json = vote.json()
        self.assertEqual(self.voter, vote_json["voter"])
        self.assertEqual(self.voter, vote.voter)
        self.assertTrue(vote.weight >= 0)
        self.assertTrue(vote.sbd >= 0)
        self.assertTrue(vote.rshares >= 0)
        self.assertTrue(vote.percent >= 0)
        self.assertTrue(vote.reputation is not None)
        self.assertTrue(vote.rep is not None)
        self.assertTrue(vote.time is not None)

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_activevotes(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        votes = ActiveVotes(self.authorperm, steem_instance=bts)
        votes.printAsTable()

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_accountvotes(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        votes = AccountVotes(self.author, steem_instance=bts)
        self.assertTrue(len(votes) > 0)
        self.assertTrue(isinstance(votes[0], Vote))
