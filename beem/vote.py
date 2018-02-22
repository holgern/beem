from .instance import shared_steem_instance
from .account import Account
from .exceptions import VoteDoesNotExistsException
from .utils import resolve_authorperm, resolve_authorpermvoter, construct_authorpermvoter, construct_authorperm
from .blockchainobject import BlockchainObject
from .comment import Comment
import json
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
        if isinstance(voter, str) and authorperm is not None:
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
        elif isinstance(voter, dict) and "authorperm" in voter and "voter" in voter:
            [author, permlink] = resolve_authorperm(voter["authorperm"])
            self["author"] = author
            self["permlink"] = permlink
            authorpermvoter = construct_authorpermvoter(voter["author"], voter["permlink"], voter["voter"])
            self["authorpermvoter"] = authorpermvoter
        elif isinstance(voter, dict) and "voter" in voter and authorperm is not None:
            [author, permlink] = resolve_authorperm(authorperm)
            self["author"] = author
            self["permlink"] = permlink
            authorpermvoter = construct_authorpermvoter(author, permlink, voter)
            self["authorpermvoter"] = authorpermvoter
        else:
            authorpermvoter = voter
        super().__init__(
            authorpermvoter,
            id_item="authorpermvoter",
            lazy=lazy,
            full=full,
            steem_instance=steem_instance
        )

    def refresh(self):
        [author, permlink, voter] = resolve_authorpermvoter(self.identifier)
        votes = self.steem.rpc.get_active_votes(author, permlink)
        vote = None
        for x in votes:
            if x["voter"] == voter:
                vote = x
        if not vote:
            raise VoteDoesNotExistsException
        super(Vote, self).__init__(vote, id_item="authorpermvoter", steem_instance=self.steem)

        self.identifier = self.authorpermvoter

    def json(self):
        output = self
        output.pop("authorpermvoter")
        return json.loads(str(json.dumps(output)))

    @property
    def voter(self):
        return self["voter"]

    @property
    def authorpermvoter(self):
        return self["authorpermvoter"]

    @property
    def weight(self):
        return self["weight"]

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
    def time(self):
        return self["time"]


class ActiveVotes(list):
    """ Obtain a list of votes for a post

        :param str authorperm: authorperm link
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, authorperm, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        votes = None
        if isinstance(authorperm, str):
            [author, permlink] = resolve_authorperm(authorperm)
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


class AccountVotes(list):
    """ Obtain a list of votes for an account

        :param str account: Account name
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, account, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()

        account = Account(account, steem_instance=self.steem)
        votes = self.steem.rpc.get_account_votes(account.name)

        super(AccountVotes, self).__init__(
            [
                Vote(x, voter=account.name)
                for x in votes
            ]
        )
