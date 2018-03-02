from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes, int, str
from builtins import object
from future.utils import python_2_unicode_compatible
import json
from beemgraphenebase.py23 import py23_bytes, bytes_types, integer_types, string_types, text_type
from collections import OrderedDict
from beemgraphenebase.types import (
    Uint8, Int16, Uint16, Uint32, Uint64,
    Varint32, Int64, String, Bytes, Void,
    Array, PointInTime, Signature, Bool,
    Set, Fixed_array, Optional, Static_variant,
    Map, Id, VoteId,
    ObjectId as GPHObjectId
)
from beemgraphenebase.objects import GrapheneObject, isArgsThisClass
from .objecttypes import object_type
from .account import PublicKey
from beemgraphenebase.objects import Operation as GPHOperation
from .operationids import operations
import struct
default_prefix = "STM"

asset_precision = {
    "STEEM": 3,
    "VESTS": 6,
    "SBD": 3,
}


def AssetId(asset):
    return ObjectId(asset, "asset")


def AccountId(asset):
    return ObjectId(asset, "account")


class ObjectId(GPHObjectId):
    """ Encodes object/protocol ids
    """
    def __init__(self, object_str, type_verify=None):
        if len(object_str.split(".")) == 3:
            space, type, id = object_str.split(".")
            self.space = int(space)
            self.type = int(type)
            self.instance = Id(int(id))
            self.Id = object_str
            if type_verify:
                assert object_type[type_verify] == int(type),\
                    "Object id does not match object type! " +\
                    "Excpected %d, got %d" %\
                    (object_type[type_verify], int(type))
        else:
            raise Exception("Object id is invalid")


@python_2_unicode_compatible
class Amount(object):
    def __init__(self, d):
        if isinstance(d, string_types):
            self.amount, self.asset = d.strip().split(" ")
            self.amount = float(self.amount)

            if self.asset in asset_precision:
                self.precision = asset_precision[self.asset]
            else:
                raise Exception("Asset unknown")
        else:
            self.amount = d.amount
            self.asset = d.symbol
            self.precision = d.asset["precision"]

    def __bytes__(self):
        # padding
        asset = self.asset + "\x00" * (7 - len(self.asset))
        amount = round(float(self.amount) * 10**self.precision)
        return (struct.pack("<q", amount) + struct.pack("<b", self.precision) +
                py23_bytes(asset, "ascii"))

    def __str__(self):
        return '{:.{}f} {}'.format(self.amount, self.precision, self.asset)


@python_2_unicode_compatible
class Operation(GPHOperation):
    def __init__(self, *args, **kwargs):
        super(Operation, self).__init__(*args, **kwargs)

    def _getklass(self, name):
        module = __import__("beembase.operations", fromlist=["operations"])
        class_ = getattr(module, name)
        return class_

    def operations(self):
        return operations

    def getOperationNameForId(self, i):
        """ Convert an operation id into the corresponding string
        """
        for key in operations:
            if int(operations[key]) is int(i):
                return key
        return "Unknown Operation ID %d" % i

    def json(self):
        return json.loads(str(self))
        # return json.loads(str(json.dumps([self.name, self.op.toJson()])))

    def __bytes__(self):
        return py23_bytes(Id(self.opId)) + py23_bytes(self.op)

    def __str__(self):
        return json.dumps([self.name.lower(), self.op.toJson()])


class Memo(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            prefix = kwargs.pop("prefix", default_prefix)
            if "encrypted" not in kwargs or not kwargs["encrypted"]:
                super(Memo, self).__init__(None)
            else:
                if len(args) == 1 and len(kwargs) == 0:
                    kwargs = args[0]
                if "encrypted" in kwargs and kwargs["encrypted"]:
                    super(Memo, self).__init__(OrderedDict([
                        ('from', PublicKey(kwargs["from"], prefix=prefix)),
                        ('to', PublicKey(kwargs["to"], prefix=prefix)),
                        ('nonce', Uint64(int(kwargs["nonce"]))),
                        ('check', Uint32(int(kwargs["check"]))),
                        ('encrypted', Bytes(kwargs["encrypted"]))
                    ]))


class WitnessProps(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(WitnessProps, self).__init__(OrderedDict([
                ('account_creation_fee', Amount(kwargs["account_creation_fee"])),
                ('maximum_block_size', Uint32(kwargs["maximum_block_size"])),
                ('sbd_interest_rate', Uint16(kwargs["sbd_interest_rate"])),
            ]))


class Price(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Price, self).__init__(OrderedDict([
                ('base', Amount(kwargs["base"])),
                ('quote', Amount(kwargs["quote"]))
            ]))


class Permission(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            prefix = kwargs.pop("prefix", default_prefix)

            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            # Sort keys (FIXME: ideally, the sorting is part of Public
            # Key and not located here)
            kwargs["key_auths"] = sorted(
                kwargs["key_auths"],
                key=lambda x: repr(PublicKey(x[0], prefix=prefix)),
                reverse=False,
            )
            kwargs["account_auths"] = sorted(
                kwargs["account_auths"],
                key=lambda x: x[0],
                reverse=False,
            )
            accountAuths = Map([
                [String(e[0]), Uint16(e[1])]
                for e in kwargs["account_auths"]
            ])
            keyAuths = Map([
                [PublicKey(e[0], prefix=prefix), Uint16(e[1])]
                for e in kwargs["key_auths"]
            ])
            super(Permission, self).__init__(OrderedDict([
                ('weight_threshold', Uint32(int(kwargs["weight_threshold"]))),
                ('account_auths', accountAuths),
                ('key_auths', keyAuths),
            ]))


class AccountOptions(GrapheneObject):
    def __init__(self, *args, **kwargs):
        # Allow for overwrite of prefix
        prefix = kwargs.pop("prefix", default_prefix)

        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            # remove dublicates
            kwargs["votes"] = list(set(kwargs["votes"]))
            # Sort votes
            kwargs["votes"] = sorted(
                kwargs["votes"],
                key=lambda x: float(x.split(":")[1]),
            )
            super(AccountOptions, self).__init__(OrderedDict([
                ('memo_key', PublicKey(kwargs["memo_key"], prefix=prefix)),
                ('voting_account', ObjectId(kwargs["voting_account"], "account")),
                ('num_witness', Uint16(kwargs["num_witness"])),
                ('num_committee', Uint16(kwargs["num_committee"])),
                ('votes', Array([VoteId(o) for o in kwargs["votes"]])),
            ]))


@python_2_unicode_compatible
class Extension(Array):
    def __str__(self):
        """ We overload the __str__ function because the json
            representation is different for extensions
        """
        return json.dumps(self.json)


class ExchangeRate(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            super(ExchangeRate, self).__init__(
                OrderedDict([
                    ('base', Amount(kwargs["base"])),
                    ('quote', Amount(kwargs["quote"])),
                ]))


class Beneficiary(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
        super(Beneficiary, self).__init__(
            OrderedDict([
                ('account', String(kwargs["account"])),
                ('weight', Int16(kwargs["weight"])),
            ]))


class Beneficiaries(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

        super(Beneficiaries, self).__init__(
            OrderedDict([
                ('beneficiaries',
                 Array([Beneficiary(o) for o in kwargs["beneficiaries"]])),
            ]))


class CommentOptionExtensions(Static_variant):
    """ Serialize Comment Payout Beneficiaries.
    Args:
        beneficiaries (list): A static_variant containing beneficiaries.
    Example:
        ::
            [0,
                {'beneficiaries': [
                    {'account': 'furion', 'weight': 10000}
                ]}
            ]
    """
    def __init__(self, o):
        type_id, data = o
        if type_id == 0:
            data = (Beneficiaries(data))
        else:
            raise Exception("Unknown CommentOptionExtension")
        super(CommentOptionExtensions, self).__init__(data, type_id)
