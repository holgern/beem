# -*- coding: utf-8 -*-
import json
from .types import (
    Uint8, Int16, Uint16, Uint32, Uint64,
    Varint32, Int64, String, Bytes, Void,
    Array, PointInTime, Signature, Bool,
    Set, Fixed_array, Optional, Static_variant,
    Map, Id,
)
from .objects import GrapheneObject, isArgsThisClass
from .account import PublicKey
from .chains import default_prefix
from .objects import Operation
from .operationids import operations


class Demooepration(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
                self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Demooepration, self).__init__(OrderedDict([
                ('string', String(kwargs["string"], "account")),
                ('extensions', Set([])),
            ]))
