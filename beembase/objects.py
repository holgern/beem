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
    Map, Id
)
from beemgraphenebase.objects import GrapheneObject, isArgsThisClass
from .objecttypes import object_type
from beemgraphenebase.account import PublicKey
from beemgraphenebase.objects import Operation as GPHOperation
from beemgraphenebase.chains import known_chains
from .operationids import operations, operations_wls
import struct
default_prefix = "STM"


@python_2_unicode_compatible
class Amount(object):
    def __init__(self, d, prefix=default_prefix):
        if isinstance(d, string_types):
            self.amount, self.symbol = d.strip().split(" ")
            self.precision = None
            for c in known_chains:
                if self.precision is not None:
                    continue
                if known_chains[c]["prefix"] != prefix:
                    continue
                for asset in known_chains[c]["chain_assets"]:
                    if self.precision is not None:
                        continue
                    if asset["symbol"] == self.symbol:
                        self.precision = asset["precision"]
                        self.asset = asset["asset"]
                    elif asset["asset"] == self.symbol:
                        self.precision = asset["precision"]
                        self.asset = asset["asset"]
            if self.precision is None:
                raise Exception("Asset unknown")
            self.amount = round(float(self.amount) * 10 ** self.precision)

            self.str_repr = '{:.{}f} {}'.format((float(self.amount) / 10 ** self.precision), self.precision, self.symbol)
        elif isinstance(d, list):
            self.amount = d[0]
            self.asset = d[2]
            self.precision = d[1]
            self.symbol = None
            for c in known_chains:
                if known_chains[c]["prefix"] != prefix:
                    continue
                for asset in known_chains[c]["chain_assets"]:
                    if asset["asset"] == self.asset:
                        self.symbol = asset["symbol"]
            if self.symbol is None:
                raise ValueError("Unknown NAI, cannot resolve symbol")
            a = Array([String(d[0]), d[1], d[2]])
            self.str_repr = str(a.__str__())
        elif isinstance(d, dict) and "nai" in d:
            self.asset = d["nai"]
            self.symbol = None
            for c in known_chains:
                if known_chains[c]["prefix"] != prefix:
                    continue
                for asset in known_chains[c]["chain_assets"]:
                    if asset["asset"] == d["nai"]:
                        self.symbol = asset["symbol"]
            if self.symbol is None:
                raise ValueError("Unknown NAI, cannot resolve symbol")
            self.amount = d["amount"]
            self.precision = d["precision"]
            self.str_repr = json.dumps(d)
        else:
            self.amount = d.amount
            self.symbol = d.symbol
            # Workaround to allow transfers in HIVE
            if self.symbol == "HBD":
                self.symbol = "SBD"
            elif self.symbol == "HIVE":
                self.symbol = "STEEM"              
            self.asset = d.asset["asset"]
            self.precision = d.asset["precision"]
            self.amount = round(float(self.amount) * 10 ** self.precision)
            self.str_repr = str(d)
            # self.str_repr = json.dumps((d.json()))
            # self.str_repr = '{:.{}f} {}'.format((float(self.amount) / 10 ** self.precision), self.precision, self.asset)

    def __bytes__(self):
        # padding
        # Workaround to allow transfers in HIVE
        if self.symbol == "HBD":
            self.symbol = "SBD"
        elif self.symbol == "HIVE":
            self.symbol = "STEEM"        
        symbol = self.symbol + "\x00" * (7 - len(self.symbol))
        return (struct.pack("<q", int(self.amount)) + struct.pack("<b", self.precision) +
                py23_bytes(symbol, "ascii"))

    def __str__(self):
        # return json.dumps({"amount": self.amount, "precision": self.precision, "nai": self.asset})
        return self.str_repr


@python_2_unicode_compatible
class Operation(GPHOperation):
    def __init__(self, *args, **kwargs):
        self.appbase = kwargs.pop("appbase", False)
        self.prefix = kwargs.pop("prefix", default_prefix)
        super(Operation, self).__init__(*args, **kwargs)

    def _getklass(self, name):
        module = __import__("beembase.operations", fromlist=["operations"])
        class_ = getattr(module, name)
        return class_

    def operations(self):
        if self.prefix == "WLS":
            return operations_wls
        return operations

    def getOperationNameForId(self, i):
        """ Convert an operation id into the corresponding string
        """
        for key in self.operations():
            if int(self.operations()[key]) is int(i):
                return key
        return "Unknown Operation ID %d" % i

    def json(self):
        return json.loads(str(self))
        # return json.loads(str(json.dumps([self.name, self.op.toJson()])))

    def __bytes__(self):
        return py23_bytes(Id(self.opId)) + py23_bytes(self.op)

    def __str__(self):
        if self.appbase:
            return json.dumps({'type': self.name.lower() + '_operation', 'value': self.op.toJson()})
        else:
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
            prefix = kwargs.get("prefix", default_prefix)
            if "sbd_interest_rate" in kwargs:
                super(WitnessProps, self).__init__(OrderedDict([
                    ('account_creation_fee', Amount(kwargs["account_creation_fee"], prefix=prefix)),
                    ('maximum_block_size', Uint32(kwargs["maximum_block_size"])),
                    ('sbd_interest_rate', Uint16(kwargs["sbd_interest_rate"])),
                ]))
            else:
                super(WitnessProps, self).__init__(OrderedDict([
                    ('account_creation_fee', Amount(kwargs["account_creation_fee"], prefix=prefix)),
                    ('maximum_block_size', Uint32(kwargs["maximum_block_size"])),
                ]))


class Price(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.get("prefix", default_prefix)
            super(Price, self).__init__(OrderedDict([
                ('base', Amount(kwargs["base"], prefix=prefix)),
                ('quote', Amount(kwargs["quote"], prefix=prefix))
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

            prefix = kwargs.get("prefix", default_prefix)
            super(ExchangeRate, self).__init__(
                OrderedDict([
                    ('base', Amount(kwargs["base"], prefix=prefix)),
                    ('quote', Amount(kwargs["quote"], prefix=prefix)),
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

        :param list beneficiaries: A static_variant containing beneficiaries.

        Example::

            [0,
                {'beneficiaries': [
                    {'account': 'furion', 'weight': 10000}
                ]}
            ]

    """
    def __init__(self, o):
        if type(o) == dict and 'type' in o and 'value' in o:
            if o['type'] == "comment_payout_beneficiaries":
                type_id = 0
            else:
                type_id = ~0
            data = o['value']
        else:
            type_id, data = o
        if type_id == 0:
            data = (Beneficiaries(data))
        else:
            raise Exception("Unknown CommentOptionExtension")
        super(CommentOptionExtensions, self).__init__(data, type_id)

        
class SocialActionCommentCreate(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            meta = ""
            if "json_metadata" in kwargs and kwargs["json_metadata"]:
                if (isinstance(kwargs["json_metadata"], dict)
                        or isinstance(kwargs["json_metadata"], list)):
                    meta = json.dumps(kwargs["json_metadata"])
                else:
                    meta = kwargs["json_metadata"]

            pod = String(kwargs["pod"]) if "pod" in kwargs else None
            max_accepted_payout = Amount(kwargs["max_accepted_payout"]) if "max_accepted_payout" in kwargs else None
            allow_replies = Bool(kwargs["allow_replies"]) if "allow_replies" in kwargs else None
            allow_votes = Bool(kwargs["allow_votes"]) if "allow_votes" in kwargs else None
            allow_curation_rewards = Bool(kwargs["allow_curation_rewards"]) if "allow_curation_rewards" in kwargs else None
            allow_friends = Bool(kwargs["allow_friends"]) if "allow_friends" in kwargs else None

            super(SocialActionCommentCreate, self).__init__(
                OrderedDict([
                    ('permlink', String(kwargs["permlink"])),
                    ('parent_author', String(kwargs["parent_author"])),
                    ('parent_permlink', String(kwargs["parent_permlink"])),
                    ('pod', Optional(pod)),
                    ('max_accepted_payout', Optional(max_accepted_payout)),
                    ('allow_replies', Optional(allow_replies)),
                    ('allow_votes', Optional(allow_votes)),
                    ('allow_curation_rewards', Optional(allow_curation_rewards)),
                    ('allow_friends', Optional(allow_friends)),
                    ('title', String(kwargs["title"])),
                    ('body', String(kwargs["body"])),
                    ('json_metadata', String(meta)),
                ]))

class SocialActionCommentUpdate(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            meta = Optional(None)
            if "json_metadata" in kwargs and kwargs["json_metadata"]:
                if (isinstance(kwargs["json_metadata"], dict)
                        or isinstance(kwargs["json_metadata"], list)):
                    meta = json.dumps(kwargs["json_metadata"])
                else:
                    if "json_metadata" in kwargs:
                        meta = kwargs["json_metadata"]

            title = kwargs["title"] if "title" in kwargs else None
            body = kwargs["body"] if "body" in kwargs else None

            super(SocialActionCommentUpdate, self).__init__(
                OrderedDict([
                    ('permlink', String(kwargs["permlink"])),
                    ('title', Optional(String(kwargs["title"]))),
                    ('body', Optional(String(kwargs["body"]))),
                    ('json_metadata', meta),
                ]))

class SocialActionCommentDelete(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            super(SocialActionCommentDelete, self).__init__(
                OrderedDict([
                    ('permlink', String(kwargs["permlink"]))
                ]))

class SocialActionVariant(Static_variant):
    def __init__(self, o):
        type_id, data = o
        if type_id == 0:
            data = SocialActionCommentCreate(data)
        else:
            if type_id == 1:
                data = SocialActionCommentUpdate(data)
            else:
                if type_id == 2:
                    data = SocialActionCommentDelete(data)
                else:
                    raise Exception("Unknown SocialAction")
        Static_variant.__init__(self, data, type_id)

