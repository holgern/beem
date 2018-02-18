from .instance import shared_steem_instance
from .account import Account
from .utils import resolve_authorperm
import logging
log = logging.getLogger(__name__)


class VoteObject(dict):
    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__, str(self.voter))


class Vote(VoteObject):
    """ Read data about a Vote in the chain

        :param str authorperm: perm link to post/comment
        :param steem steem_instance: Steem() instance to use when accesing a RPC

    """
    type_id = 11

    def refresh(self, authorperm=None, voter=None):
        vote = self.identifier
        if authorperm is not None:
            vote["authorperm"] = authorperm
        if voter is not None:
            vote["voter"] = voter
        super(Vote, self).__init__(vote)

    @property
    def voter(self):
        return self["voter"]

    @property
    def authorperm(self):
        return self["authorperm"]

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
    """ Obtain a list of pending proposals for a post

        :param str authorperm: authorperm link
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, authorperm, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        [author, permlink] = resolve_authorperm(authorperm)
        votes = self.steem.rpc.get_active_votes(author, permlink)

        super(ActiveVotes, self).__init__(
            [
                Vote(x, authorperm=authorperm)
                for x in votes
            ]
        )


class AccountVotes(list):
    """ Obtain a list of pending proposals for an account

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
