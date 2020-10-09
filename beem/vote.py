# -*- coding: utf-8 -*-
import json
import math
import pytz
import logging
from prettytable import PrettyTable
from datetime import datetime, date
from beemgraphenebase.py23 import integer_types, string_types, text_type
from .instance import shared_blockchain_instance
from .account import Account
from .exceptions import VoteDoesNotExistsException
from .utils import resolve_authorperm, resolve_authorpermvoter, construct_authorpermvoter, construct_authorperm, formatTimeString, addTzInfo, reputation_to_score
from .blockchainobject import BlockchainObject
from .comment import Comment
from beemapi.exceptions import UnkownKey

log = logging.getLogger(__name__)


class Vote(BlockchainObject):
    """ Read data about a Vote in the chain

        :param str authorperm: perm link to post/comment
        :param Steem steem_instance: Steem() instance to use when accesing a RPC

        .. code-block:: python

           >>> from beem.vote import Vote
           >>> from beem import Steem
           >>> stm = Steem()
           >>> v = Vote("@gtg/steem-pressure-4-need-for-speed|gandalf", steem_instance=stm)

    """
    type_id = 11

    def __init__(
        self,
        voter,
        authorperm=None,
        full=False,
        lazy=False,
        blockchain_instance=None,
        **kwargs
    ):
        self.full = full
        self.lazy = lazy
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
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
            authorpermvoter = self._parse_json_data(authorpermvoter)
        elif isinstance(voter, dict) and "authorperm" in voter and authorperm is not None:
            [author, permlink] = resolve_authorperm(voter["authorperm"])
            authorpermvoter = voter
            authorpermvoter["voter"] = authorperm
            authorpermvoter["author"] = author
            authorpermvoter["permlink"] = permlink
            authorpermvoter["authorpermvoter"] = construct_authorpermvoter(author, permlink, authorperm)
            authorpermvoter = self._parse_json_data(authorpermvoter)
        elif isinstance(voter, dict) and "voter" in voter and authorperm is not None:
            [author, permlink] = resolve_authorperm(authorperm)
            authorpermvoter = voter
            authorpermvoter["author"] = author
            authorpermvoter["permlink"] = permlink
            authorpermvoter["authorpermvoter"] = construct_authorpermvoter(author, permlink, voter["voter"])
            authorpermvoter = self._parse_json_data(authorpermvoter)
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
            blockchain_instance=blockchain_instance
        )

    def refresh(self):
        if self.identifier is None:
            return
        if not self.blockchain.is_connected():
            return
        [author, permlink, voter] = resolve_authorpermvoter(self.identifier)
        try:
            self.blockchain.rpc.set_next_node_on_empty_reply(True)
            if self.blockchain.rpc.get_use_appbase():
                try:
                    votes = self.blockchain.rpc.get_active_votes({'author': author, 'permlink': permlink}, api="tags")['votes']
                except:
                    from beemapi.exceptions import InvalidParameters
                    try:
                        votes = self.blockchain.rpc.get_active_votes(author, permlink, api="database_api")
                    except InvalidParameters:
                        raise VoteDoesNotExistsException(self.identifier)
            else:
                votes = self.blockchain.rpc.get_active_votes(author, permlink, api="database_api")
        except UnkownKey:
            raise VoteDoesNotExistsException(self.identifier)

        vote = None
        if votes is not None:
            for x in votes:
                if x["voter"] == voter:
                    vote = x
        if not vote:
            raise VoteDoesNotExistsException(self.identifier)
        vote = self._parse_json_data(vote)
        vote["authorpermvoter"] = construct_authorpermvoter(author, permlink, voter)
        super(Vote, self).__init__(vote, id_item="authorpermvoter", lazy=self.lazy, full=self.full, blockchain_instance=self.blockchain)

    def _parse_json_data(self, vote):
        parse_int = [
            "rshares", "reputation",
        ]
        for p in parse_int:
            if p in vote and isinstance(vote.get(p), string_types):
                vote[p] = int(vote.get(p, "0"))

        if "time" in vote and isinstance(vote.get("time"), string_types) and vote.get("time") != '':
            vote["time"] = formatTimeString(vote.get("time", "1970-01-01T00:00:00"))
        elif "timestamp" in vote and isinstance(vote.get("timestamp"), string_types) and vote.get("timestamp") != '':
            vote["time"] = formatTimeString(vote.get("timestamp", "1970-01-01T00:00:00"))
        elif "last_update" in vote and isinstance(vote.get("last_update"), string_types) and vote.get("last_update") != '':
            vote["last_update"] = formatTimeString(vote.get("last_update", "1970-01-01T00:00:00"))        
        else:
            vote["time"] = formatTimeString("1970-01-01T00:00:00")
        return vote

    def json(self):
        output = self.copy()
        if "author" in output:
            output.pop("author")
        if "permlink" in output:
            output.pop("permlink")
        parse_times = [
            "time"
        ]
        for p in parse_times:
            if p in output:
                p_date = output.get(p, datetime(1970, 1, 1, 0, 0))
                if isinstance(p_date, (datetime, date)):
                    output[p] = formatTimeString(p_date)
                else:
                    output[p] = p_date
        parse_int = [
            "rshares", "reputation",
        ]
        for p in parse_int:
            if p in output and isinstance(output[p], integer_types):
                output[p] = str(output[p])
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
        return self.blockchain.rshares_to_sbd(int(self.get("rshares", 0)))

    @property
    def hbd(self):
        return self.blockchain.rshares_to_hbd(int(self.get("rshares", 0)))

    @property
    def token_backed_dollar(self):
        from beem import Hive
        if isinstance(self.blockchain, Hive):
            return self.blockchain.rshares_to_hbd(int(self.get("rshares", 0)))
        else:
            return self.blockchain.rshares_to_sbd(int(self.get("rshares", 0)))

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
        return reputation_to_score(int(self.reputation))

    @property
    def time(self):
        return self["time"]


class VotesObject(list):
    def get_sorted_list(self, sort_key="time", reverse=True):
        utc = pytz.timezone('UTC')

        if sort_key == 'sbd' or sort_key == "hbd":
            sortedList = sorted(self, key=lambda self: self.rshares, reverse=reverse)
        elif sort_key == 'time':
            sortedList = sorted(self, key=lambda self: (utc.localize(datetime.utcnow()) - self.time).total_seconds(), reverse=reverse)
        elif sort_key == 'votee':
            sortedList = sorted(self, key=lambda self: self.votee, reverse=reverse)
        elif sort_key in ['voter', 'rshares', 'percent', 'weight']:
            sortedList = sorted(self, key=lambda self: self[sort_key], reverse=reverse)
        else:
            sortedList = self
        return sortedList

    def printAsTable(self, voter=None, votee=None, start=None, stop=None, start_percent=None, stop_percent=None, sort_key="time", reverse=True, allow_refresh=True, return_str=False, **kwargs):
        utc = pytz.timezone('UTC')
        table_header = ["Voter", "Votee", "SBD/HBD", "Time", "Rshares", "Percent", "Weight"]
        t = PrettyTable(table_header)
        t.align = "l"
        start = addTzInfo(start)
        stop = addTzInfo(stop)
        for vote in self.get_sorted_list(sort_key=sort_key, reverse=reverse):
            if not allow_refresh:
                vote.cached = True

            d_time = vote.time
            if d_time != formatTimeString("1970-01-01T00:00:00"):
                td = utc.localize(datetime.utcnow()) - d_time
                timestr = str(td.days) + " days " + str(td.seconds // 3600) + ":" + str((td.seconds // 60) % 60)
            else:
                start = None
                stop = None
                timestr = ''

            percent = vote.get('percent', '')
            if percent == '':
                start_percent = None
                stop_percent = None
            if (start is None or d_time >= start) and (stop is None or d_time <= stop) and\
                (start_percent is None or percent >= start_percent) and (stop_percent is None or percent <= stop_percent) and\
                (voter is None or vote["voter"] == voter) and (votee is None or vote.votee == votee):
                percent = vote.get('percent', '')
                if percent == '':
                    percent = vote.get('vote_percent', '')
                t.add_row([vote['voter'],
                           vote.votee,
                           str(round(vote.token_backed_dollar, 2)).ljust(5) + "$",
                           timestr,
                           vote.get("rshares", ""),
                           str(percent),
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
            d_time = vote.time
            if d_time != formatTimeString("1970-01-01T00:00:00"):
                start = None
                stop = None
            percent = vote.get('percent', '')
            if percent == '':
                percent = vote.get('vote_percent', '') 
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
                elif var == "sbd" or var == "hbd":
                    v = vote.token_backed_dollar
                elif var == "time":
                    v = d_time
                elif var == "rshares":
                    v = vote.get("rshares", 0)
                elif var == "percent":
                    v = percent
                elif var == "weight":
                    v = vote['weight']
                vote_list.append(v)
        return vote_list

    def print_stats(self, return_str=False, **kwargs):
        # utc = pytz.timezone('UTC')
        table_header = ["voter", "votee", "sbd/hbd", "time", "rshares", "percent", "weight"]
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
        :param Steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, authorperm, lazy=False, full=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        votes = None
        if not self.blockchain.is_connected():
            return None
        self.blockchain.rpc.set_next_node_on_empty_reply(False)

        if isinstance(authorperm, Comment):
            # if 'active_votes' in authorperm and len(authorperm["active_votes"]) > 0:
            #    votes = authorperm["active_votes"]
            if self.blockchain.rpc.get_use_appbase():
                self.blockchain.rpc.set_next_node_on_empty_reply(False)
                from beemapi.exceptions import InvalidParameters
                try:
                    votes = self.blockchain.rpc.get_active_votes(authorperm["author"], authorperm["permlink"], api="condenser")
                except InvalidParameters:
                    raise VoteDoesNotExistsException(construct_authorperm(authorperm["author"], authorperm["permlink"]))
                except:
                    votes = self.blockchain.rpc.get_active_votes({'author': authorperm["author"],
                                                             'permlink': authorperm["permlink"]},
                                                            api="tags")['votes']
            else:
                votes = self.blockchain.rpc.get_active_votes(authorperm["author"], authorperm["permlink"])
            authorperm = authorperm["authorperm"]
        elif isinstance(authorperm, string_types):
            [author, permlink] = resolve_authorperm(authorperm)
            if self.blockchain.rpc.get_use_appbase():
                self.blockchain.rpc.set_next_node_on_empty_reply(False)
                from beemapi.exceptions import InvalidParameters
                try:
                    votes = self.blockchain.rpc.get_active_votes(author, permlink, api="condenser")
                except InvalidParameters:
                    raise VoteDoesNotExistsException(construct_authorperm(author, permlink))                    
                except:
                    votes = self.blockchain.rpc.get_active_votes({'author': author,
                                                             'permlink': permlink},
                                                            api="tags")['votes']
            else:
                votes = self.blockchain.rpc.get_active_votes(author, permlink)
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
                Vote(x, authorperm=authorperm, lazy=lazy, full=full, blockchain_instance=self.blockchain)
                for x in votes
            ]
        )


class AccountVotes(VotesObject):
    """ Obtain a list of votes for an account
        Lists the last 100+ votes on the given account.

        :param str account: Account name
        :param Steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, account, start=None, stop=None, raw_data=False, lazy=False, full=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        start = addTzInfo(start)
        stop = addTzInfo(stop)
        account = Account(account, blockchain_instance=self.blockchain)
        votes = account.get_account_votes()
        self.identifier = account["name"]
        vote_list = []
        if votes is None:
            votes = []
        for x in votes:
            time = x.get("time", "")
            if time == "":
                time = x.get("last_update", "")
                if time != "":
                    x["time"] = time
            if time != "" and isinstance(time, string_types):
                d_time = formatTimeString(time)
            elif isinstance(time, datetime):
                d_time = time
            else:
                d_time = addTzInfo(datetime(1970, 1, 1, 0, 0, 0))
            if (start is None or d_time >= start) and (stop is None or d_time <= stop):
                if not raw_data:
                    vote_list.append(Vote(x, authorperm=account["name"], lazy=lazy, full=full, blockchain_instance=self.blockchain))
                else:
                    vote_list.append(x)

        super(AccountVotes, self).__init__(vote_list)
