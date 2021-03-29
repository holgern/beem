# -*- coding: utf-8 -*-
from beemgraphenebase.py23 import py23_bytes, bytes_types
import ecdsa
import hashlib
from binascii import hexlify, unhexlify
from collections import OrderedDict
from asn1crypto.core import OctetString
import struct
from collections import OrderedDict
import json

from .py23 import py23_bytes, bytes_types, integer_types, string_types, py23_chr
from .objecttypes import object_type
from .bip32 import parse_path

from .account import PublicKey
from .types import (
    Array,
    Set,
    Signature,
    PointInTime,
    Uint16,
    Uint32,
    JsonObj,
    String,
    Varint32,
    Optional
)
from .objects import GrapheneObject, isArgsThisClass
from .operations import Operation
from .chains import known_chains
from .ecdsasig import sign_message, verify_message
import logging
log = logging.getLogger(__name__)


class GrapheneObjectASN1(object):
    """ Core abstraction class

        This class is used for any JSON reflected object in Graphene.

        * ``instance.__json__()``: encodes data into json format
        * ``bytes(instance)``: encodes data into wire format
        * ``str(instances)``: dumps json object as string

    """
    def __init__(self, data=None):
        self.data = data

    def __bytes__(self):
        if self.data is None:
            return py23_bytes()
        b = b""
        output = b""
        for name, value in list(self.data.items()):
            if name == "operations":
                for operation in value:
                    if isinstance(value, string_types):
                        b = py23_bytes(operation, 'utf-8')
                    else:
                        b = py23_bytes(operation)
                    output += OctetString(b).dump()
            elif name != "signatures":
                if isinstance(value, string_types):
                    b = py23_bytes(value, 'utf-8')
                else:
                    b = py23_bytes(value)
                output += OctetString(b).dump()
        return output

    def __json__(self):
        if self.data is None:
            return {}
        d = {}  # JSON output is *not* ordered
        for name, value in list(self.data.items()):
            if isinstance(value, Optional) and value.isempty():
                continue

            if isinstance(value, String):
                d.update({name: str(value)})
            else:
                try:
                    d.update({name: JsonObj(value)})
                except Exception:
                    d.update({name: value.__str__()})
        return d

    def __str__(self):
        return json.dumps(self.__json__())

    def toJson(self):
        return self.__json__()

    def json(self):
        return self.__json__()


class Unsigned_Transaction(GrapheneObjectASN1):
    """ Create an unsigned transaction with ASN1 encoder for using it with ledger

        :param num ref_block_num:
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
            operations_count = 0
            if "operations" in kwargs:
                operations_count = len(kwargs["operations"])
                #opklass = self.getOperationKlass()
                #if all([not isinstance(a, opklass) for a in kwargs["operations"]]):
                #    kwargs['operations'] = Array([opklass(a, prefix=prefix) for a in kwargs["operations"]])
                #else:
                #    kwargs['operations'] = (kwargs["operations"])

            super(Unsigned_Transaction, self).__init__(OrderedDict([
                ('ref_block_num', Uint16(kwargs['ref_block_num'])),
                ('ref_block_prefix', Uint32(kwargs['ref_block_prefix'])),
                ('expiration', PointInTime(kwargs['expiration'])),
                ('operations_count', Varint32(operations_count)),
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
        self.message = OctetString(unhexlify(self.chainid)).dump()
        for name, value in list(self.data.items()):
            if name == "operations":
                for operation in value:
                    if isinstance(value, string_types):
                        b = py23_bytes(operation, 'utf-8')
                    else:
                        b = py23_bytes(operation)
                    self.message += OctetString(b).dump()
            elif name != "signatures":
                if isinstance(value, string_types):
                    b = py23_bytes(value, 'utf-8')
                else:
                    b = py23_bytes(value)
                self.message += OctetString(b).dump()

        self.digest = hashlib.sha256(self.message).digest()

        # restore signatures
        self.data["signatures"] = sigs

    def build_path(self, role, account_index, key_index):
        if role == "owner":
            return "48'/13'/0'/%d'/%d'" % (account_index, key_index)
        elif role == "active":
            return "48'/13'/1'/%d'/%d'" % (account_index, key_index)
        elif role == "posting":
            return "48'/13'/4'/%d'/%d'" % (account_index, key_index)
        elif role == "memo":
            return "48'/13'/3'/%d'/%d'" % (account_index, key_index)        

    def build_apdu(self, path="48'/13'/0'/0'/0'", chain=None):
        self.deriveDigest(chain)
        path = unhexlify(parse_path(path, as_bytes=True))

        message = self.message
        path_size = int(len(path) / 4)
        message_size = len(message)
        
        offset = 0
        first = True
        result = []
        while offset != message_size:
            if message_size - offset > 200:
                chunk = message[offset: offset + 200]
            else:
                chunk = message[offset:]
    
            if first:
                total_size = int(len(path)) + 1 + len(chunk)
                apdu = unhexlify("d4040000") + py23_chr(total_size) + py23_chr(path_size) + path + chunk
                first = False
            else:
                total_size = len(chunk)
                apdu = unhexlify("d4048000") + py23_chr(total_size) + chunk
            result.append(apdu)
            offset += len(chunk)
        return result

    def build_apdu_pubkey(self, path="48'/13'/0'/0'/0'", request_screen_approval=False):
        path = unhexlify(parse_path(path, as_bytes=True))
        if not request_screen_approval:
            return unhexlify("d4020001") + py23_chr(int(len(path)) + 1) + py23_chr(int(len(path) / 4)) + path
        else:
            return unhexlify("d4020101") + py23_chr(int(len(path)) + 1) + py23_chr(int(len(path) / 4)) + path
