# -*- coding: utf-8 -*-
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
from .nodes import get_hive_nodes, get_steem_nodes

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bts = Steem(
            node=get_hive_nodes(),
            nobroadcast=True,
            keys={"active": wif},
            num_retries=10
        )
        # from getpass import getpass
        # self.bts.wallet.unlock(getpass())
        set_shared_steem_instance(cls.bts)
        cls.bts.set_default_account("test")

        acc = Account("fullnodeupdate", steem_instance=cls.bts)
        n_votes = 0
        index = 0
        entries = acc.get_blog_entries(limit=30)[::-1]
        while n_votes == 0:
            comment = Comment(entries[index], steem_instance=cls.bts)
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

    def test_vote(self):
        bts = self.bts
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

    def test_keyerror(self):
        bts = self.bts
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

    def test_activevotes(self):
        bts = self.bts
        votes = ActiveVotes(self.authorperm, steem_instance=bts)
        votes.printAsTable()
        vote_list = votes.get_list()
        self.assertTrue(isinstance(vote_list, list))

    @unittest.skip
    def test_accountvotes(self):
        bts = self.bts
        utc = pytz.timezone('UTC')
        limit_time = utc.localize(datetime.utcnow()) - timedelta(days=7)
        votes = AccountVotes(self.voter, start=limit_time, steem_instance=bts)
        self.assertTrue(len(votes) > 0)
        self.assertTrue(isinstance(votes[0], Vote))
