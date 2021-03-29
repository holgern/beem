# -*- coding: utf-8 -*-
from beemgraphenebase.signedtransactions import Signed_Transaction as GrapheneSigned_Transaction
from .operations import Operation
from beemgraphenebase.chains import known_chains
import logging
log = logging.getLogger(__name__)


class Signed_Transaction(GrapheneSigned_Transaction):
    """ Create a signed transaction and offer method to create the
        signature

        :param num refNum: parameter ref_block_num (see :func:`beembase.transactions.getBlockParams`)
        :param num refPrefix: parameter ref_block_prefix (see :func:`beembase.transactions.getBlockParams`)
        :param str expiration: expiration date
        :param array operations:  array of operations
        :param dict custom_chains: custom chain which should be added to the known chains
    """
    def __init__(self, *args, **kwargs):
        self.known_chains = known_chains
        custom_chain = kwargs.get("custom_chains", {})
        if len(custom_chain) > 0:
            for c in custom_chain:
                if c not in self.known_chains:
                    self.known_chains[c] = custom_chain[c]
        super(Signed_Transaction, self).__init__(*args, **kwargs)

    def add_custom_chains(self, custom_chain):
        if len(custom_chain) > 0:
            for c in custom_chain:
                if c not in self.known_chains:
                    self.known_chains[c] = custom_chain[c]

    def sign(self, wifkeys, chain=u"STEEM"):
        return super(Signed_Transaction, self).sign(wifkeys, chain)

    def verify(self, pubkeys=[], chain=u"STEEM", recover_parameter=False):
        return super(Signed_Transaction, self).verify(pubkeys, chain, recover_parameter)

    def getOperationKlass(self):
        return Operation

    def getKnownChains(self):
        return self.known_chains
