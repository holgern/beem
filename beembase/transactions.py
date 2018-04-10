from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from binascii import hexlify, unhexlify
import struct
from beemgraphenebase.account import PublicKey
from .chains import known_chains
from .signedtransactions import Signed_Transaction
from .operations import (
    Op_wrapper,
    Account_create,
)


def getBlockParams(ws):
    """ Auxiliary method to obtain ``ref_block_num`` and
        ``ref_block_prefix``. Requires a websocket connection to a
        witness node!
    """
    dynBCParams = ws.get_dynamic_global_properties()
    ref_block_num = dynBCParams["head_block_number"] & 0xFFFF
    ref_block_prefix = struct.unpack_from("<I", unhexlify(dynBCParams["head_block_id"]), 4)[0]
    return ref_block_num, ref_block_prefix
