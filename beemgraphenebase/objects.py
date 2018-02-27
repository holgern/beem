from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
from builtins import bytes
from builtins import str
from builtins import object
from collections import OrderedDict
import six
import json
from beemgraphenebase.types import (
    Uint8, Int16, Uint16, Uint32, Uint64,
    Varint32, Int64, String, Bytes, Void,
    Array, PointInTime, Signature, Bool,
    Set, Fixed_array, Optional, Static_variant,
    Map, Id, VoteId, ObjectId,
    JsonObj
)
from .chains import known_chains
from .objecttypes import object_type
from .account import PublicKey
from .chains import default_prefix
from .operationids import operations


class Operation(object):
    def __init__(self, op):
        if isinstance(op, list) and len(op) == 2:
            if isinstance(op[0], six.integer_types):
                self.opId = op[0]
                name = self.getOperationNameForId(self.opId)
            else:
                self.opId = self.operations().get(op[0], None)
                name = op[0]
                if self.opId is None:
                    raise ValueError("Unknown operation")
            self.name = name[0].upper() + name[1:]  # klassname
            try:
                klass = self._getklass(self.name)
            except Exception:
                raise NotImplementedError("Unimplemented Operation %s" % self.name)
            self.op = klass(op[1])
        else:
            self.op = op
            self.name = type(self.op).__name__.lower()  # also store name
            self.opId = self.operations()[self.name]

    def operations(self):
        return operations

    def getOperationNameForId(self, i):
        """ Convert an operation id into the corresponding string
        """
        for key in operations:
            if int(operations[key]) is int(i):
                return key
        return "Unknown Operation ID %d" % i

    def _getklass(self, name):
        module = __import__("graphenebase.operations", fromlist=["operations"])
        class_ = getattr(module, name)
        return class_

    def to_bytes(self):
        return (Id(self.opId).to_bytes()) + (self.op.to_bytes())

    def __str__(self):
        return json.dumps([self.opId, self.op.toJson()])


class GrapheneObject(object):
    """ Core abstraction class

        This class is used for any JSON reflected object in Graphene.

        * ``instance.__json__()``: encodes data into json format
        * ``bytes(instance)``: encodes data into wire format
        * ``str(instances)``: dumps json object as string

    """
    def __init__(self, data=None):
        self.data = data

    def to_bytes(self):
        if self.data is None:
            return bytes()
        b = b""
        for name, value in list(self.data.items()):
            if isinstance(value, six.string_types):
                b += bytes(value, 'utf-8')
            elif isinstance(value, (list, dict)):
                b += bytes(value)
            else:
                b += (value.to_bytes())
        return b

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


def isArgsThisClass(self, args):
    return (len(args) == 1 and type(args[0]).__name__ == type(self).__name__)
