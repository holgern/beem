from .instance import shared_steem_instance
from .account import Account
from .exceptions import ProposalDoesNotExistException
from .blockchainobject import BlockchainObject
import logging
log = logging.getLogger(__name__)


class Proposal(BlockchainObject):
    """ Read data about a Proposal Balance in the chain

        :param str id: Id of the proposal
        :param steem steem_instance: Steem() instance to use when accesing a RPC

    """
    type_id = 10

    def refresh(self):
        proposal = self.steem.rpc.get_objects([self.identifier])
        if not any(proposal):
            raise ProposalDoesNotExistException
        super(Proposal, self).__init__(proposal[0], steem_instance=self.steem)

    @property
    def proposed_operations(self):
        yield from self["proposed_transaction"]["operations"]


class Proposals(list):
    """ Obtain a list of pending proposals for an account

        :param str account: Account name
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, account, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()

        account = Account(account, steem_instance=self.steem)
        proposals = self.steem.rpc.get_proposed_transactions(account["id"])

        super(Proposals, self).__init__(
            [
                Proposal(x, steem_instance=self.steem)
                for x in proposals
            ]
        )
