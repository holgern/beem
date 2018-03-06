# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from beemgraphenebase.py23 import integer_types, string_types, text_type
from .instance import shared_steem_instance
from .account import Account
from .exceptions import VoteDoesNotExistsException
from .utils import resolve_authorperm, resolve_authorpermvoter, construct_authorpermvoter, construct_authorperm, formatTimeString
from .blockchainobject import BlockchainObject
from .comment import Comment
from datetime import datetime
import json
import math
import pytz
import logging
log = logging.getLogger(__name__)


class Vote(BlockchainObject):
    """ Read data about a Vote in the chain

        :param str authorperm: perm link to post/comment
        :param steem steem_instance: Steem() instance to use when accesing a RPC

        .. code-block:: python

           from beem.vote import Vote
           v = Vote("theaussiegame/cryptokittie-giveaway-number-2|")

    """
    type_id = 11

    def __init__(
        self,
        voter,
        authorperm=None,
        full=False,
        lazy=False,
        steem_instance=None
    ):
        self.full = full
        if isinstance(voter, string_types) and authorperm is not None:
            [author, permlink] = resolve_authorperm(authorperm)
            self["voter"] = voter
            self["author"] = author
            self["permlink"] = permlink
            authorpermvoter = construct_authorpermvoter(author, permlink, voter)
            self["authorpermvoter"] = authorpermvoter
        elif isinstance(voter, dict) and "author" in voter and "permlink" in voter and "voter" in voter:
            self["author"] = voter["author"]
            self["permlink"] = voter["permlink"]
            authorpermvoter = construct_authorpermvoter(voter["author"], voter["permlink"], voter["voter"])
            self["authorpermvoter"] = authorpermvoter
        elif isinstance(voter, dict) and "authorperm" in voter and authorperm is not None:
            [author, permlink] = resolve_authorperm(voter["authorperm"])
            self["voter"] = authorperm
            self["author"] = author
            self["permlink"] = permlink
            authorpermvoter = construct_authorpermvoter(author, permlink, authorperm)
            self["authorpermvoter"] = authorpermvoter
        elif isinstance(voter, dict) and "voter" in voter and authorperm is not None:
            [author, permlink] = resolve_authorperm(authorperm)
            self["author"] = author
            self["permlink"] = permlink
            authorpermvoter = construct_authorpermvoter(author, permlink, voter["voter"])
            self["authorpermvoter"] = authorpermvoter
        else:
            authorpermvoter = voter
        super(Vote, self).__init__(
            authorpermvoter,
            id_item="authorpermvoter",
            lazy=lazy,
            full=full,
            steem_instance=steem_instance
        )

    def refresh(self):
        if self.identifier is None:
            return
        [author, permlink, voter] = resolve_authorpermvoter(self.identifier)
        if self.steem.rpc.get_use_appbase():
            votes = self.steem.rpc.get_active_votes({'author': author, 'permlink': permlink}, api="tags")['votes']
        else:
            votes = self.steem.rpc.get_active_votes(author, permlink)
        if not votes:
            self["voter"] = voter
            return
        vote = None
        for x in votes:
            if x["voter"] == voter:
                vote = x
        if not vote:
            raise VoteDoesNotExistsException
        super(Vote, self).__init__(vote, id_item="authorpermvoter", steem_instance=self.steem)

        self.identifier = construct_authorpermvoter(author, permlink, voter)

    def json(self):
        output = self.copy()
        if "author" in output:
            output.pop("author")
        if "permlink" in output:
            output.pop("permlink")
        return json.loads(str(json.dumps(output)))

    @property
    def voter(self):
        return self["voter"]

    @property
    def weight(self):
        return self["weight"]

    @property
    def sbd(self):
        return self.steem.rshares_to_sbd(self["rshares"])

    @property
    def rshares(self):
        return self["rshares"]

    @property
    def percent(self):
        return self["percent"]

    @property
    def reputation(self):
        return self["reputation"]

    @property
    def rep(self):
        rep = int(self['reputation'])
        if rep == 0:
            return 25.
        score = max([math.log10(abs(rep)) - 9, 0])
        if rep < 0:
            score *= -1
        score = (score * 9.) + 25.
        return score

    @property
    def time(self):
        return self["time"]


class VotesObject(list):
    def printAsTable(self, sort_key="sbd", reverse=True):
        utc = pytz.timezone('UTC')
        if sort_key == 'sbd':
            sortedList = sorted(self, key=lambda self: self['rshares'], reverse=reverse)
        elif sort_key == 'voter':
            sortedList = sorted(self, key=lambda self: self[sort_key], reverse=reverse)
        elif sort_key == 'time':
            sortedList = sorted(self, key=lambda self: (utc.localize(datetime.now()) - formatTimeString(self['time'])).total_seconds(), reverse=reverse)
        elif sort_key == 'rshares':
            sortedList = sorted(self, key=lambda self: self[sort_key], reverse=reverse)
        elif sort_key == 'percent':
            sortedList = sorted(self, key=lambda self: self[sort_key], reverse=reverse)
        elif sort_key == 'weight':
            sortedList = sorted(self, key=lambda self: self[sort_key], reverse=reverse)
        elif sort_key == 'reputation':
            sortedList = sorted(self, key=lambda self: int(self[sort_key]), reverse=reverse)
        else:
            sortedList = sorted(self, key=lambda self: self[sort_key], reverse=reverse)
        for vote in sortedList:
            outstr = ''
            outstr += vote['voter'][:15].ljust(15) + " (" + str(round(vote.rep, 2)) + ")\t " + str(round(vote.sbd, 2)).ljust(5) + " $ - "
            outstr += str(vote['percent']).ljust(5) + " % - weight:" + str(vote['weight'])
            td = utc.localize(datetime.now()) - formatTimeString(vote['time'])
            outstr += " " + str(td.days) + " days " + str(td.seconds // 3600) + ":" + str((td.seconds // 60) % 60) + " \t "
            print(outstr)


class ActiveVotes(VotesObject):
    """ Obtain a list of votes for a post

        :param str authorperm: authorperm link
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, authorperm, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        votes = None
        if isinstance(authorperm, Comment) and 'active_votes' not in authorperm:
            if self.steem.rpc.get_use_appbase():
                votes = self.steem.rpc.get_active_votes({'author': authorperm["author"],
                                                         'permlink': authorperm["permlink"]},
                                                        api="tags")['votes']
            else:
                votes = self.steem.rpc.get_active_votes(authorperm["author"], authorperm["permlink"])
            authorperm = authorperm["authorperm"]
        elif isinstance(authorperm, string_types):
            [author, permlink] = resolve_authorperm(authorperm)
            if self.steem.rpc.get_use_appbase():
                votes = self.steem.rpc.get_active_votes({'author': author,
                                                         'permlink': permlink},
                                                        api="tags")['votes']
            else:
                votes = self.steem.rpc.get_active_votes(author, permlink)
        elif isinstance(authorperm, list):
            votes = authorperm
            authorperm = None
        elif isinstance(authorperm, Comment):
            votes = authorperm["active_votes"]
            authorperm = authorperm["authorperm"]
        elif isinstance(authorperm, dict):
            votes = authorperm["active_votes"]
            authorperm = authorperm["authorperm"]
        if votes is None:
            return

        super(ActiveVotes, self).__init__(
            [
                Vote(x, authorperm=authorperm)
                for x in votes
            ]
        )


class AccountVotes(VotesObject):
    """ Obtain a list of votes for an account
        Lists the last 100+ votes on the given account.

        :param str account: Account name
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, account, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()

        account = Account(account, steem_instance=self.steem)
        if self.steem.rpc.get_use_appbase():
            votes = self.steem.rpc.find_votes({'author': account["name"], 'permlink': ''}, api="database")['votes']
        else:
            votes = self.steem.rpc.get_account_votes(account["name"])

        super(AccountVotes, self).__init__(
            [
                Vote(x, authorperm=account["name"])
                for x in votes
            ]
        )
