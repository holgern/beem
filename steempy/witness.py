from steempy.instance import shared_steem_instance
from .account import Account
from .exceptions import WitnessDoesNotExistsException
from .blockchainobject import BlockchainObject


class Witness(BlockchainObject):
    """ Read data about a witness in the chain

        :param str account_name: Name of the witness
        :param steem steem_instance: BitShares() instance to use when
               accesing a RPC

    """
    type_ids = [6, 2]

    def refresh(self):

        witness = self.steem.rpc.get_witness_by_account(self.identifier)
        if not witness:
            raise WitnessDoesNotExistsException
        super(Witness, self).__init__(witness, steem_instance=self.steem)

    @property
    def account(self):
        return Account(self["owner"], steem_instance=self.steem)


class Witnesses(list):
    """ Obtain a list of **active** witnesses and the current schedule

        :param steem steem_instance: BitShares() instance to use when
            accesing a RPC
    """
    def __init__(self, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        self.active_witnessess = self.steem.rpc.get_active_witnesses()
        self.schedule = self.steem.rpc.get_witness_schedule()
        self.witness_count = self.steem.rpc.get_witness_count()

        super(Witnesses, self).__init__(
            [
                Witness(x, lazy=True, steem_instance=self.steem)
                for x in self.active_witnessess
            ]
        )
