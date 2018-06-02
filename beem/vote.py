# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import json
import math
import pytz
import logging
from prettytable import PrettyTable
from datetime import datetime
from beemgraphenebase.py23 import integer_types, string_types, text_type
from .instance import shared_steem_instance
from .account import Account
from .exceptions import VoteDoesNotExistsException
from .utils import resolve_authorperm, resolve_authorpermvoter, construct_authorpermvoter, construct_authorperm, formatTimeString, addTzInfo
from .blockchainobject import BlockchainObject
from .comment import Comment
from beemapi.exceptions import UnkownKey

log = logging.getLogger(__name__)


class Vote(BlockchainObject):
    """ Read data about a Vote in the chain

        :param str authorperm: perm link to post/comment
        :param steem steem_instance: Steem() instance to use when accesing a RPC

        .. code-block:: python

           >>> from beem.vote import Vote
           >>> v = Vote("@gtg/steem-pressure-4-need-for-speed|gandalf")

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
            authorpermvoter = voter
            authorpermvoter["authorpermvoter"] = construct_authorpermvoter(voter["author"], voter["permlink"], voter["voter"])
        elif isinstance(voter, dict) and "authorperm" in voter and authorperm is not None:
            [author, permlink] = resolve_authorperm(voter["authorperm"])
            authorpermvoter = voter
            authorpermvoter["voter"] = authorperm
            authorpermvoter["author"] = author
            authorpermvoter["permlink"] = permlink
            authorpermvoter["authorpermvoter"] = construct_authorpermvoter(author, permlink, authorperm)
        elif isinstance(voter, dict) and "voter" in voter and authorperm is not None:
            [author, permlink] = resolve_authorperm(authorperm)
            authorpermvoter = voter
            authorpermvoter["author"] = author
            authorpermvoter["permlink"] = permlink
            authorpermvoter["authorpermvoter"] = construct_authorpermvoter(author, permlink, voter["voter"])
        else:
            authorpermvoter = voter
            [author, permlink, voter] = resolve_authorpermvoter(authorpermvoter)
            self["author"] = author
            self["permlink"] = permlink

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
        if self.steem.offline:
            return
        [author, permlink, voter] = resolve_authorpermvoter(self.identifier)
        try:
            self.steem.rpc.set_next_node_on_empty_reply(True)
            if self.steem.rpc.get_use_appbase():
                votes = self.steem.rpc.get_active_votes({'author': author, 'permlink': permlink}, api="tags")['votes']
            else:
                votes = self.steem.rpc.get_active_votes(author, permlink, api="database_api")
        except UnkownKey:
            raise VoteDoesNotExistsException(self.identifier)

        vote = None
        for x in votes:
            if x["voter"] == voter:
                vote = x
        if not vote:
            raise VoteDoesNotExistsException(self.identifier)
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
    def authorperm(self):
        if "authorperm" in self:
            return self["authorperm"]
        elif "authorpermvoter" in self:
            [author, permlink, voter] = resolve_authorpermvoter(self["authorpermvoter"])
            return construct_authorperm(author, permlink)
        elif "author" in self and "permlink" in self:
            return construct_authorperm(self["author"], self["permlink"])
        else:
            return ""

    @property
    def votee(self):
        votee = ''
        authorperm = self.get("authorperm", "")
        authorpermvoter = self.get("authorpermvoter", "")
        if authorperm != "":
            votee = resolve_authorperm(authorperm)[0]
        elif authorpermvoter != "":
            votee = resolve_authorpermvoter(authorpermvoter)[0]
        return votee

    @property
    def weight(self):
        return self["weight"]

    @property
    def sbd(self):
        return self.steem.rshares_to_sbd(int(self.get("rshares", 0)))

    @property
    def rshares(self):
        return int(self.get("rshares", 0))

    @property
    def percent(self):
        return self.get("percent", 0)

    @property
    def reputation(self):
        return self.get("reputation", 0)

    @property
    def rep(self):
        rep = int(self.reputation)
        if rep == 0:
            return 25.
        score = max([math.log10(abs(rep)) - 9, 0])
        if rep < 0:
            score *= -1
        score = (score * 9.) + 25.
        return score

    @property
    def time(self):
        t = self.get("time", '')
        if t == '':
            t = self.get("timestamp", '')
        return t


class VotesObject(list):
    def get_sorted_list(self, sort_key="time", reverse=True):
        utc = pytz.timezone('UTC')

        if sort_key == 'sbd':
            sortedList = sorted(self, key=lambda self: self.rshares, reverse=reverse)
        elif sort_key == 'voter':
            sortedList = sorted(self, key=lambda self: self[sort_key], reverse=reverse)
        elif sort_key == 'time':
            sortedList = sorted(self, key=lambda self: (utc.localize(datetime.utcnow()) - formatTimeString(self.time)).total_seconds(), reverse=reverse)
        elif sort_key == 'rshares':
            sortedList = sorted(self, key=lambda self: self[sort_key], reverse=reverse)
        elif sort_key == 'percent':
            sortedList = sorted(self, key=lambda self: self[sort_key], reverse=reverse)
        elif sort_key == 'weight':
            sortedList = sorted(self, key=lambda self: self[sort_key], reverse=reverse)
        elif sort_key == 'votee':
            sortedList = sorted(self, key=lambda self: self.votee, reverse=reverse)
        else:
            sortedList = self
        return sortedList

    def printAsTable(self, voter=None, votee=None, start=None, stop=None, start_percent=None, stop_percent=None, sort_key="time", reverse=True, allow_refresh=True, return_str=False, **kwargs):
        utc = pytz.timezone('UTC')
        table_header = ["Voter", "Votee", "SBD", "Time", "Rshares", "Percent", "Weight"]
        t = PrettyTable(table_header)
        t.align = "l"
        start = addTzInfo(start)
        stop = addTzInfo(stop)
        for vote in self.get_sorted_list(sort_key=sort_key, reverse=reverse):
            if not allow_refresh:
                vote.cached = True
            time = vote.time
            if time != '':
                d_time = formatTimeString(time)
                td = utc.localize(datetime.utcnow()) - d_time
                timestr = str(td.days) + " days " + str(td.seconds // 3600) + ":" + str((td.seconds // 60) % 60)
            else:
                start = None
                stop = None
                timestr = ""
            percent = vote.get('percent', '')
            if percent == '':
                start_percent = None
                stop_percent = None
            if (start is None or d_time >= start) and (stop is None or d_time <= stop) and\
                (start_percent is None or percent >= start_percent) and (stop_percent is None or percent <= stop_percent) and\
                (voter is None or vote["voter"] == voter) and (votee is None or vote.votee == votee):
                t.add_row([vote['voter'],
                           vote.votee,
                           str(round(vote.sbd, 2)).ljust(5) + "$",
                           timestr,
                           vote.get("rshares", ""),
                           str(vote.get('percent', '')),
                           str(vote['weight'])])

        if return_str:
            return t.get_string(**kwargs)
        else:
            print(t.get_string(**kwargs))

    def get_list(self, var="voter", voter=None, votee=None, start=None, stop=None, start_percent=None, stop_percent=None, sort_key="time", reverse=True):
        vote_list = []
        start = addTzInfo(start)
        stop = addTzInfo(stop)
        for vote in self.get_sorted_list(sort_key=sort_key, reverse=reverse):
            time = vote.time
            if time != '':
                d_time = formatTimeString(time)
            else:
                start = None
                stop = None
            percent = vote.get('percent', '')
            if percent == '':
                start_percent = None
                stop_percent = None
            if (start is None or d_time >= start) and (stop is None or d_time <= stop) and\
                (start_percent is None or percent >= start_percent) and (stop_percent is None or percent <= stop_percent) and\
                (voter is None or vote["voter"] == voter) and (votee is None or vote.votee == votee):
                v = ''
                if var == "voter":
                    v = vote["voter"]
                elif var == "votee":
                    v = vote.votee
                elif var == "sbd":
                    v = vote.sbd
                elif var == "time":
                    v = d_time
                elif var == "rshares":
                    v = vote.get("rshares", "")
                elif var == "percent":
                    v = percent
                elif var == "weight":
                    v = vote['weight']
                vote_list.append(v)
        return vote_list

    def print_stats(self, return_str=False, **kwargs):
        # utc = pytz.timezone('UTC')
        table_header = ["voter", "votee", "sbd", "time", "rshares", "percent", "weight"]
        t = PrettyTable(table_header)
        t.align = "l"

    def __contains__(self, item):
        if isinstance(item, Account):
            name = item["name"]
            authorperm = ""
        elif isinstance(item, Comment):
            authorperm = item.authorperm
            name = ""
        else:
            name = item
            authorperm = item

        return (
            any([name == x.voter for x in self]) or
            any([name == x.votee for x in self]) or
            any([authorperm == x.authorperm for x in self])
        )

    def __str__(self):
        return self.printAsTable(return_str=True)

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__, str(self.identifier))


class ActiveVotes(VotesObject):
    """ Obtain a list of votes for a post

        :param str authorperm: authorperm link
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, authorperm, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        votes = None
        if self.steem.offline:
            return None
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if isinstance(authorperm, Comment):
            if 'active_votes' in authorperm and len(authorperm["active_votes"]) > 0:
                votes = authorperm["active_votes"]
            elif self.steem.rpc.get_use_appbase():
                self.steem.rpc.set_next_node_on_empty_reply(True)
                votes = self.steem.rpc.get_active_votes({'author': authorperm["author"],
                                                         'permlink': authorperm["permlink"]},
                                                        api="tags")['votes']
            else:
                votes = self.steem.rpc.get_active_votes(authorperm["author"], authorperm["permlink"])
            authorperm = authorperm["authorperm"]
        elif isinstance(authorperm, string_types):
            [author, permlink] = resolve_authorperm(authorperm)
            if self.steem.rpc.get_use_appbase():
                self.steem.rpc.set_next_node_on_empty_reply(True)
                votes = self.steem.rpc.get_active_votes({'author': author,
                                                         'permlink': permlink},
                                                        api="tags")['votes']
            else:
                votes = self.steem.rpc.get_active_votes(author, permlink)
        elif isinstance(authorperm, list):
            votes = authorperm
            authorperm = None
        elif isinstance(authorperm, dict):
            votes = authorperm["active_votes"]
            authorperm = authorperm["authorperm"]
        if votes is None:
            return
        self.identifier = authorperm
        super(ActiveVotes, self).__init__(
            [
                Vote(x, authorperm=authorperm, lazy=True, steem_instance=self.steem)
                for x in votes
            ]
        )


class AccountVotes(VotesObject):
    """ Obtain a list of votes for an account
        Lists the last 100+ votes on the given account.

        :param str account: Account name
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, account, start=None, stop=None, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        start = addTzInfo(start)
        stop = addTzInfo(stop)
        account = Account(account, steem_instance=self.steem)
        votes = account.get_account_votes()
        self.identifier = account["name"]
        vote_list = []
        for x in votes:
            time = x.get("time", "")
            if time != "":
                d_time = formatTimeString(time)
            else:
                d_time = addTzInfo(datetime(1970, 1, 1, 0, 0, 0))
            if (start is None or d_time >= start) and (stop is None or d_time <= stop):
                vote_list.append(Vote(x, authorperm=account["name"], steem_instance=self.steem))

        super(AccountVotes, self).__init__(vote_list)
