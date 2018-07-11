from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from parameterized import parameterized
import pytz
from datetime import datetime, timedelta
from pprint import pprint
from beem import Steem, exceptions
from beem.comment import Comment
from beem.account import Account
from beem.vote import Vote, ActiveVotes, AccountVotes
from beem.instance import set_shared_steem_instance
from beem.utils import construct_authorperm, resolve_authorperm, resolve_authorpermvoter, construct_authorpermvoter
from beem.nodelist import NodeList

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodelist = NodeList()
        nodelist.update_nodes(steem_instance=Steem(node=nodelist.get_nodes(normal=True, appbase=True), num_retries=10))
        cls.bts = Steem(
            node=nodelist.get_nodes(appbase=False),
            nobroadcast=True,
            keys={"active": wif},
            num_retries=10
        )
        cls.appbase = Steem(
            node=nodelist.get_nodes(normal=False, appbase=True),
            nobroadcast=True,
            keys={"active": wif},
            num_retries=10
        )
        # from getpass import getpass
        # self.bts.wallet.unlock(getpass())
        set_shared_steem_instance(cls.bts)
        cls.bts.set_default_account("test")

        acc = Account("holger80", steem_instance=cls.bts)
        n_votes = 0
        index = 0
        while n_votes == 0:
            comment = acc.get_feed(limit=30)[::-1][index]
            votes = comment.get_votes()
            n_votes = len(votes)
            index += 1

        last_vote = votes[0]

        cls.authorpermvoter = construct_authorpermvoter(last_vote['author'], last_vote['permlink'], last_vote["voter"])
        [author, permlink, voter] = resolve_authorpermvoter(cls.authorpermvoter)
        cls.author = author
        cls.permlink = permlink
        cls.voter = voter
        cls.authorperm = construct_authorperm(author, permlink)

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
    def test_keyerror(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        with self.assertRaises(
            exceptions.VoteDoesNotExistsException
        ):
            Vote(construct_authorpermvoter(self.author, self.permlink, "asdfsldfjlasd"), steem_instance=bts)

        with self.assertRaises(
            exceptions.VoteDoesNotExistsException
        ):
            Vote(construct_authorpermvoter(self.author, "sdlfjd", "asdfsldfjlasd"), steem_instance=bts)

        with self.assertRaises(
            exceptions.VoteDoesNotExistsException
        ):
            Vote(construct_authorpermvoter("sdalfj", "dsfa", "asdfsldfjlasd"), steem_instance=bts)

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
        vote_list = votes.get_list()
        self.assertTrue(isinstance(vote_list, list))

    @parameterized.expand([
        ("non_appbase"),
        ("appbase"),
    ])
    def test_accountvotes(self, node_param):
        if node_param == "non_appbase":
            bts = self.bts
        else:
            bts = self.appbase
        utc = pytz.timezone('UTC')
        limit_time = utc.localize(datetime.utcnow()) - timedelta(days=7)
        votes = AccountVotes(self.author, start=limit_time, steem_instance=bts)
        self.assertTrue(len(votes) > 0)
        self.assertTrue(isinstance(votes[0], Vote))
