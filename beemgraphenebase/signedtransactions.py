# -*- coding: utf-8 -*-
from beemgraphenebase.py23 import py23_bytes, bytes_types
import ecdsa
import hashlib
from binascii import hexlify, unhexlify
from collections import OrderedDict

from .account import PublicKey
from .types import (
    Array,
    Set,
    Signature,
    PointInTime,
    Uint16,
    Uint32,
)
from .objects import GrapheneObject, isArgsThisClass
from .operations import Operation
from .chains import known_chains
from .ecdsasig import sign_message, verify_message
import logging
log = logging.getLogger(__name__)


class Signed_Transaction(GrapheneObject):
    """ Create a signed transaction and offer method to create the
        signature

        :param num ref_block_num: reference block number
        :param num ref_block_prefix: 
        :param str expiration: expiration date
        :param array operations:  array of operations
    """
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", "STM")
            if "extensions" not in kwargs:
                kwargs["extensions"] = Set([])
            elif not kwargs.get("extensions"):
                kwargs["extensions"] = Set([])
            if "signatures" not in kwargs:
                kwargs["signatures"] = Array([])
            else:
                kwargs["signatures"] = Array([Signature(unhexlify(a)) for a in kwargs["signatures"]])

            if "operations" in kwargs:
                opklass = self.getOperationKlass()
                if all([not isinstance(a, opklass) for a in kwargs["operations"]]):
                    kwargs['operations'] = Array([opklass(a, prefix=prefix) for a in kwargs["operations"]])
                else:
                    kwargs['operations'] = Array(kwargs["operations"])

            super(Signed_Transaction, self).__init__(OrderedDict([
                ('ref_block_num', Uint16(kwargs['ref_block_num'])),
                ('ref_block_prefix', Uint32(kwargs['ref_block_prefix'])),
                ('expiration', PointInTime(kwargs['expiration'])),
                ('operations', kwargs['operations']),
                ('extensions', kwargs['extensions']),
                ('signatures', kwargs['signatures']),
            ]))

    @property
    def id(self):
        """ The transaction id of this transaction
        """
        # Store signatures temporarily since they are not part of
        # transaction id
        sigs = self.data["signatures"]
        self.data.pop("signatures", None)

        # Generage Hash of the seriliazed version
        h = hashlib.sha256(py23_bytes(self)).digest()

        # recover signatures
        self.data["signatures"] = sigs

        # Return properly truncated tx hash
        return hexlify(h[:20]).decode("ascii")

    def getOperationKlass(self):
        return Operation

    def derSigToHexSig(self, s):
        """ Format DER to HEX signature
        """
        s, junk = ecdsa.der.remove_sequence(unhexlify(s))
        if junk:
            log.debug('JUNK: %s', hexlify(junk).decode('ascii'))
        if not (junk == b''):
            raise AssertionError()
        x, s = ecdsa.der.remove_integer(s)
        y, s = ecdsa.der.remove_integer(s)
        return '%064x%064x' % (x, y)

    def getKnownChains(self):
        return known_chains

    def getChainParams(self, chain):
        # Which network are we on:
        chains = self.getKnownChains()
        if isinstance(chain, str) and chain in chains:
            chain_params = chains[chain]
        elif isinstance(chain, dict):
            chain_params = chain
        else:
            raise Exception("sign() only takes a string or a dict as chain!")
        if "chain_id" not in chain_params:
            raise Exception("sign() needs a 'chain_id' in chain params!")
        return chain_params

    def deriveDigest(self, chain):
        chain_params = self.getChainParams(chain)
        # Chain ID
        self.chainid = chain_params["chain_id"]

        # Do not serialize signatures
        sigs = self.data["signatures"]
        self.data["signatures"] = []

        # Get message to sign
        #   bytes(self) will give the wire formated data according to
        #   GrapheneObject and the data given in __init__()
        self.message = unhexlify(self.chainid) + py23_bytes(self)
        self.digest = hashlib.sha256(self.message).digest()

        # restore signatures
        self.data["signatures"] = sigs

    def verify(self, pubkeys=[], chain=None, recover_parameter=False):
        """Returned pubkeys have to be checked if they are existing"""
        if not chain:
            raise
        chain_params = self.getChainParams(chain)
        self.deriveDigest(chain)
        signatures = self.data["signatures"].data
        pubKeysFound = []

        for signature in signatures:
            if recover_parameter:
                p = verify_message(
                    self.message,
                    py23_bytes(signature)
                )
            else:
                p = None
            if p is None:
                for i in range(4):
                    try:
                        p = verify_message(
                            self.message,
                            py23_bytes(signature),
                            recover_parameter=i
                        )
                        phex = hexlify(p).decode('ascii')
                        pubKeysFound.append(phex)
                    except Exception:
                        p = None
            else:
                phex = hexlify(p).decode('ascii')
                pubKeysFound.append(phex)

        for pubkey in pubkeys:
            if not isinstance(pubkey, PublicKey):
                raise Exception("Pubkeys must be array of 'PublicKey'")

            k = pubkey.unCompressed()[2:]
            if k not in pubKeysFound and repr(pubkey) not in pubKeysFound:
                k = PublicKey(PublicKey(k).compressed())
                f = format(k, chain_params["prefix"])
                raise Exception("Signature for %s missing!" % f)
        return pubKeysFound

    def sign(self, wifkeys, chain=None):
        """ Sign the transaction with the provided private keys.

            :param array wifkeys: Array of wif keys
            :param str chain: identifier for the chain

        """
        if not chain:
            raise Exception("Chain needs to be provided!")
        self.deriveDigest(chain)

        # Get Unique private keys
        self.privkeys = []
        [self.privkeys.append(item) for item in wifkeys if item not in self.privkeys]

        # Sign the message with every private key given!
        sigs = []
        for wif in self.privkeys:
            signature = sign_message(self.message, wif)
            sigs.append(Signature(signature))

        self.data["signatures"] = Array(sigs)
        return self
