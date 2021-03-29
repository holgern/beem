# -*- coding: utf-8 -*-
from beemgraphenebase.unsignedtransactions import Unsigned_Transaction as GrapheneUnsigned_Transaction
from .operations import Operation
from beemgraphenebase.chains import known_chains
from beemgraphenebase.py23 import py23_bytes
from beemgraphenebase.account import PublicKey
from beemgraphenebase.types import (
    Array,
    Signature,
)
from binascii import hexlify
import logging
log = logging.getLogger(__name__)


class Ledger_Transaction(GrapheneUnsigned_Transaction):
    """ Create an unsigned transaction and offer method to send it to a ledger device for signing

        :param num ref_block_num:
        :param num ref_block_prefix:
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
        super(Ledger_Transaction, self).__init__(*args, **kwargs)

    def add_custom_chains(self, custom_chain):
        if len(custom_chain) > 0:
            for c in custom_chain:
                if c not in self.known_chains:
                    self.known_chains[c] = custom_chain[c]

    def getOperationKlass(self):
        return Operation

    def getKnownChains(self):
        return self.known_chains

    def sign(self, path="48'/13'/0'/0'/0'", chain=u"STEEM"):
        from ledgerblue.comm import getDongle
        dongle = getDongle(True)
        apdu_list = self.build_apdu(path, chain)
        for apdu in apdu_list:
            result = dongle.exchange(py23_bytes(apdu))
        dongle.close()
        sigs = []
        signature = result
        sigs.append(Signature(signature))
        self.data["signatures"] = Array(sigs)
        return self

    def get_pubkey(self, path="48'/13'/0'/0'/0'", request_screen_approval=False, prefix="STM"):
        from ledgerblue.comm import getDongle
        dongle = getDongle(True)
        apdu = self.build_apdu_pubkey(path, request_screen_approval)
        result = dongle.exchange(py23_bytes(apdu))
        dongle.close()
        offset = 1 + result[0]
        address = result[offset + 1: offset + 1 + result[offset]]
        # public_key = result[1: 1 + result[0]]
        return PublicKey(address.decode(), prefix=prefix)
