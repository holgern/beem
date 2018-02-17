import json
from collections import OrderedDict
from graphenebase.types import (
    Uint8, Int16, Uint16, Uint32, Uint64,
    Varint32, Int64, String, Bytes, Void,
    Array, PointInTime, Signature, Bool,
    Set, Fixed_array, Optional, Static_variant,
    Map, Id, VoteId,
    ObjectId as GPHObjectId
)
from graphenebase.objects import GrapheneObject, isArgsThisClass
from .objecttypes import object_type
from .account import PublicKey
from graphenebase.objects import Operation as GPHOperation
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


class Amount():
    def __init__(self, d):
        if isinstance(d, str):
            self.amount, self.asset = d.strip().split(" ")
            self.amount = float(self.amount)

            if self.asset in asset_precision:
                self.precision = asset_precision[self.asset]
            else:
                raise Exception("Asset unknown")
        else:
            self.amount = d.amount
            self.asset = d.symbol
            self.precision = d.asset.precision

    def __bytes__(self):
        # padding
        asset = self.asset + "\x00" * (7 - len(self.asset))
        amount = round(float(self.amount) * 10**self.precision)
        return (struct.pack("<q", amount) + struct.pack("<b", self.precision) +
                bytes(asset, "ascii"))

    def __str__(self):
        return '{:.{}f} {}'.format(self.amount, self.precision, self.asset)


class Operation(GPHOperation):
    def __init__(self, *args, **kwargs):
        super(Operation, self).__init__(*args, **kwargs)

    def _getklass(self, name):
        module = __import__("steempybase.operations", fromlist=["operations"])
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
        return bytes(Id(self.opId)) + bytes(self.op)

    def __str__(self):
        return json.dumps([self.name.lower(), self.op.toJson()])


class Transfer(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('from', String(kwargs["from"])),
                ('to', String(kwargs["to"])),
                ('amount', Amount(kwargs["amount"])),
                ('memo', String(kwargs["memo"])),
            ]))


class Memo(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", default_prefix)
            if "message" in kwargs and kwargs["message"]:
                super().__init__(OrderedDict([
                    ('from', PublicKey(kwargs["from"], prefix=prefix)),
                    ('to', PublicKey(kwargs["to"], prefix=prefix)),
                    ('nonce', Uint64(int(kwargs["nonce"]))),
                    ('message', Bytes(kwargs["message"]))
                ]))
            else:
                super().__init__(None)


class WitnessProps(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
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
            super().__init__(OrderedDict([
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
                key=lambda x: repr(PublicKey(x[0], prefix=prefix).address),
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
            super().__init__(OrderedDict([
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
            super().__init__(OrderedDict([
                ('memo_key', PublicKey(kwargs["memo_key"], prefix=prefix)),
                ('voting_account', ObjectId(kwargs["voting_account"], "account")),
                ('num_witness', Uint16(kwargs["num_witness"])),
                ('num_committee', Uint16(kwargs["num_committee"])),
                ('votes', Array([VoteId(o) for o in kwargs["votes"]])),
            ]))


class SpecialAuthority(Static_variant):
    def __init__(self, o):

        class No_special_authority(GrapheneObject):
            def __init__(self, kwargs):
                super().__init__(OrderedDict([]))

        class Top_holders_special_authority(GrapheneObject):
            def __init__(self, kwargs):
                super().__init__(OrderedDict([
                    ('asset', ObjectId(kwargs["asset"], "asset")),
                    ('num_top_holders', Uint8(kwargs["num_top_holders"])),
                ]))

        id = o[0]
        if id == 0:
            data = No_special_authority(o[1])
        elif id == 1:
            data = Top_holders_special_authority(o[1])
        else:
            raise Exception("Unknown SpecialAuthority")
        super().__init__(data, id)


class Extension(Array):
    def __str__(self):
        """ We overload the __str__ function because the json
            representation is different for extensions
        """
        return json.dumps(self.json)


class AccountCreateExtensions(Extension):
    def __init__(self, *args, **kwargs):
        # Extensions #################################
        class Null_ext(GrapheneObject):
            def __init__(self, kwargs):
                super().__init__(OrderedDict([]))

        class Owner_special_authority(SpecialAuthority):
            def __init__(self, kwargs):
                super().__init__(kwargs)

        class Active_special_authority(SpecialAuthority):
            def __init__(self, kwargs):
                super().__init__(kwargs)

        class Buyback_options(GrapheneObject):
            def __init__(self, kwargs):
                if isArgsThisClass(self, args):
                        self.data = args[0].data
                else:
                    if len(args) == 1 and len(kwargs) == 0:
                        kwargs = args[0]
#                    assert "1.3.0" in kwargs["markets"], "CORE asset must be in 'markets' to pay fees"
                    super().__init__(OrderedDict([
                        ('asset_to_buy', ObjectId(kwargs["asset_to_buy"], "asset")),
                        ('asset_to_buy_issuer', ObjectId(kwargs["asset_to_buy_issuer"], "account")),
                        ('markets', Array([
                            ObjectId(x, "asset") for x in kwargs["markets"]
                        ])),
                    ]))
        # End of Extensions definition ################
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

        self.json = dict()
        a = []
        sorted_options = [
            "null_ext",
            "owner_special_authority",
            "active_special_authority",
            "buyback_options"
        ]
        sorting = sorted(kwargs.items(), key=lambda x: sorted_options.index(x[0]))
        for key, value in sorting:
            self.json.update({key: value})
            if key == "null_ext":
                a.append(Static_variant(
                    Null_ext({key: value}),
                    sorted_options.index(key))
                )
            elif key == "owner_special_authority":
                a.append(Static_variant(
                    Owner_special_authority(value),
                    sorted_options.index(key))
                )
            elif key == "active_special_authority":
                a.append(Static_variant(
                    Active_special_authority(value),
                    sorted_options.index(key))
                )
            elif key == "buyback_options":
                a.append(Static_variant(
                    Buyback_options(value),
                    sorted_options.index(key))
                )
            else:
                raise NotImplementedError("Extension {} is unknown".format(key))

        super().__init__(a)
