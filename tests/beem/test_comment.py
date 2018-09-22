from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super, str
import unittest
from parameterized import parameterized
from pprint import pprint
from beem import Steem, exceptions
from beem.comment import Comment, RecentReplies, RecentByPath
from beem.vote import Vote
from beem.account import Account
from beem.instance import set_shared_steem_instance
from beem.utils import resolve_authorperm
from beem.nodelist import NodeList

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodelist = NodeList()
        nodelist.update_nodes(steem_instance=Steem(node=nodelist.get_nodes(normal=True, appbase=True), num_retries=10))
        cls.bts = Steem(
            node=nodelist.get_nodes(),
            use_condenser=True,
            nobroadcast=True,
            unsigned=True,
            keys={"active": wif},
            num_retries=10
        )
        cls.testnet = Steem(
            node="https://testnet.steemitdev.com",
            nobroadcast=True,
            unsigned=True,
            keys={"active": wif},
            num_retries=10
        )
        acc = Account("holger80", steem_instance=cls.bts)
        comment = acc.get_feed(limit=20)[-1]
        cls.authorperm = comment.authorperm
        [author, permlink] = resolve_authorperm(cls.authorperm)
        cls.author = author
        cls.permlink = permlink
        cls.category = comment.category
        cls.title = comment.title
        # from getpass import getpass
        # self.bts.wallet.unlock(getpass())
        # set_shared_steem_instance(cls.bts)
        # cls.bts.set_default_account("test")

    def test_comment(self):
        bts = self.bts
        with self.assertRaises(
            exceptions.ContentDoesNotExistsException
        ):
            Comment("@abcdef/abcdef", steem_instance=bts)
        title = ''
        cnt = 0
        while title == '' and cnt < 5:
            c = Comment(self.authorperm, steem_instance=bts)
            title = c.title
            cnt += 1
            if title == '':
                c.steem.rpc.next()
                c.refresh()
                title = c.title
        self.assertTrue(isinstance(c.id, int))
        self.assertTrue(c.id > 0)
        self.assertEqual(c.author, self.author)
        self.assertEqual(c.permlink, self.permlink)
        self.assertEqual(c.authorperm, self.authorperm)
        self.assertEqual(c.category, self.category)
        self.assertEqual(c.parent_author, '')
        self.assertEqual(c.parent_permlink, self.category)
        self.assertEqual(c.title, self.title)
        self.assertTrue(len(c.body) > 0)
        self.assertTrue(isinstance(c.json_metadata, dict))
        self.assertTrue(c.is_main_post())
        self.assertFalse(c.is_comment())
        if c.is_pending():
            self.assertFalse((c.time_elapsed().total_seconds() / 60 / 60 / 24) > 7.0)
        else:
            self.assertTrue((c.time_elapsed().total_seconds() / 60 / 60 / 24) > 7.0)
        self.assertTrue(isinstance(c.get_reblogged_by(), list))
        self.assertTrue(len(c.get_reblogged_by()) > 0)
        self.assertTrue(isinstance(c.get_votes(), list))
        self.assertTrue(len(c.get_votes()) > 0)
        self.assertTrue(isinstance(c.get_votes()[0], Vote))

    def test_comment_dict(self):
        bts = self.bts
        title = ''
        cnt = 0
        while title == '' and cnt < 5:
            c = Comment({'author': self.author, 'permlink': self.permlink}, steem_instance=bts)
            c.refresh()
            title = c.title
            cnt += 1
            if title == '':
                c.steem.rpc.next()
                c.refresh()
                title = c.title

        self.assertEqual(c.author, self.author)
        self.assertEqual(c.permlink, self.permlink)
        self.assertEqual(c.authorperm, self.authorperm)
        self.assertEqual(c.category, self.category)
        self.assertEqual(c.parent_author, '')
        self.assertEqual(c.parent_permlink, self.category)
        self.assertEqual(c.title, self.title)

    def test_vote(self):
        bts = self.bts
        c = Comment(self.authorperm, steem_instance=bts)
        bts.txbuffer.clear()
        tx = c.vote(100, account="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "vote"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["voter"])
        c.steem.txbuffer.clear()
        tx = c.upvote(weight=150, voter="test")
        op = tx["operations"][0][1]
        self.assertEqual(op["weight"], 10000)
        c.steem.txbuffer.clear()
        tx = c.upvote(weight=99.9, voter="test")
        op = tx["operations"][0][1]
        self.assertEqual(op["weight"], 9990)
        c.steem.txbuffer.clear()
        tx = c.downvote(weight=-150, voter="test")
        op = tx["operations"][0][1]
        self.assertEqual(op["weight"], -10000)
        c.steem.txbuffer.clear()
        tx = c.downvote(weight=-99.9, voter="test")
        op = tx["operations"][0][1]
        self.assertEqual(op["weight"], -9990)

    def test_export(self):
        bts = self.bts

        if bts.rpc.get_use_appbase():
            content = bts.rpc.get_discussion({'author': self.author, 'permlink': self.permlink}, api="tags")
        else:
            content = bts.rpc.get_content(self.author, self.permlink)

        c = Comment(self.authorperm, steem_instance=bts)
        keys = list(content.keys())
        json_content = c.json()
        exclude_list = ["json_metadata", "reputation", "active_votes"]
        for k in keys:
            if k not in exclude_list:
                if isinstance(content[k], dict) and isinstance(json_content[k], list):
                    self.assertEqual(list(content[k].values()), json_content[k])
                elif isinstance(content[k], str) and isinstance(json_content[k], str):
                    self.assertEqual(content[k].encode('utf-8'), json_content[k].encode('utf-8'))
                else:
                    self.assertEqual(content[k], json_content[k])

    def test_resteem(self):
        bts = self.bts
        bts.txbuffer.clear()
        c = Comment(self.authorperm, steem_instance=bts)
        tx = c.resteem(account="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "custom_json"
        )

    def test_reply(self):
        bts = self.bts
        bts.txbuffer.clear()
        c = Comment(self.authorperm, steem_instance=bts)
        tx = c.reply(body="Good post!", author="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "comment"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test",
            op["author"])

    def test_delete(self):
        bts = self.bts
        bts.txbuffer.clear()
        c = Comment(self.authorperm, steem_instance=bts)
        tx = c.delete(account="test")
        self.assertEqual(
            (tx["operations"][0][0]),
            "delete_comment"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            self.author,
            op["author"])

    def test_edit(self):
        bts = self.bts
        bts.txbuffer.clear()
        c = Comment(self.authorperm, steem_instance=bts)
        c.edit(c.body, replace=False)
        body = c.body + "test"
        tx = c.edit(body, replace=False)
        self.assertEqual(
            (tx["operations"][0][0]),
            "comment"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            self.author,
            op["author"])

    def test_edit_replace(self):
        bts = self.bts
        bts.txbuffer.clear()
        c = Comment(self.authorperm, steem_instance=bts)
        body = c.body + "test"
        tx = c.edit(body, meta=c["json_metadata"], replace=True)
        self.assertEqual(
            (tx["operations"][0][0]),
            "comment"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            self.author,
            op["author"])
        self.assertEqual(body, op["body"])

    def test_recent_replies(self):
        bts = self.bts
        r = RecentReplies(self.author, skip_own=True, steem_instance=bts)
        self.assertTrue(len(r) > 0)
        self.assertTrue(r[0] is not None)

    def test_recent_by_path(self):
        bts = self.bts
        r = RecentByPath(path="hot", steem_instance=bts)
        self.assertTrue(len(r) > 0)
        self.assertTrue(r[0] is not None)
