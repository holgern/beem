from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
from builtins import str
from builtins import bytes
from builtins import object
import json
import struct
import time
from calendar import timegm
from datetime import datetime
from binascii import hexlify, unhexlify
from collections import OrderedDict
from .objecttypes import object_type

timeformat = '%Y-%m-%dT%H:%M:%S%Z'


def varint(n):
    """ Varint encoding
    """
    data = b''
    while n >= 0x80:
        data += bytes([(n & 0x7f) | 0x80])
        n >>= 7
    data += bytes([n])
    return data


def varintdecode(data):
    """ Varint decoding
    """
    shift = 0
    result = 0
    for c in data:
        b = ord(c)
        result |= ((b & 0x7f) << shift)
        if not (b & 0x80):
            break
        shift += 7
    return result


def variable_buffer(s):
    """ Encode variable length buffer
    """
    return varint(len(s)) + s


def JsonObj(data):
    """ Returns json object from data
    """
    return json.loads(str(data))


class Uint8(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return struct.pack("<B", self.data)

    def __str__(self):
        return '%d' % self.data


class Int16(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return struct.pack("<h", int(self.data))

    def __str__(self):
        return '%d' % self.data


class Uint16(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return struct.pack("<H", self.data)

    def __str__(self):
        return '%d' % self.data


class Uint32(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return struct.pack("<I", self.data)

    def __str__(self):
        return '%d' % self.data


class Uint64(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return struct.pack("<Q", self.data)

    def __str__(self):
        return '%d' % self.data


class Varint32(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return varint(self.data)

    def __str__(self):
        return '%d' % self.data


class Int64(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return struct.pack("<q", self.data)

    def __str__(self):
        return '%d' % self.data


class String(object):
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        d = self.unicodify()
        return varint(len(d)) + d

    def __str__(self):
        return '%s' % str(self.data)

    def unicodify(self):
        r = []
        for s in self.data:
            o = ord(s)
            if o <= 7:
                r.append("u%04x" % o)
            elif o == 8:
                r.append("b")
            elif o == 9:
                r.append("\t")
            elif o == 10:
                r.append("\n")
            elif o == 11:
                r.append("u%04x" % o)
            elif o == 12:
                r.append("f")
            elif o == 13:
                r.append("\r")
            elif o > 13 and o < 32:
                r.append("u%04x" % o)
            else:
                r.append(s)
        return bytes("".join(r), "utf-8")


class Bytes(object):
    def __init__(self, d, length=None):
        self.data = d
        if length:
            self.length = length
        else:
            self.length = len(self.data)

    def __bytes__(self):
        # FIXME constraint data to self.length
        d = unhexlify(bytes(self.data, 'utf-8'))
        return varint(len(d)) + d

    def __str__(self):
        return str(self.data)


class Void(object):
    def __init__(self):
        pass

    def __bytes__(self):
        return b''

    def __str__(self):
        return ""


class Array(object):
    def __init__(self, d):
        self.data = d
        self.length = Varint32(len(self.data))

    def __bytes__(self):
        return bytes(self.length) + b"".join([bytes(a) for a in self.data])

    def __str__(self):
        r = []
        for a in self.data:
            try:
                r.append(JsonObj(a))
            except Exception:
                r.append(str(a))
        return json.dumps(r)


class PointInTime(object):
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        return struct.pack("<I", timegm(time.strptime((self.data + "UTC"), timeformat)))

    def __str__(self):
        return self.data


class Signature(object):
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        return self.data

    def __str__(self):
        return json.dumps(hexlify(self.data).decode('ascii'))


class Bool(Uint8):  # Bool = Uint8
    def __init__(self, d):
        super().__init__(d)

    def __str__(self):
        return json.dumps(True) if self.data else json.dumps(False)


class Set(Array):  # Set = Array
    def __init__(self, d):
        super().__init__(d)


class Fixed_array(object):
    def __init__(self, d):
        raise NotImplementedError

    def __bytes__(self):
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError


class Optional(object):
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        if not self.data:
            return bytes(Bool(0))
        else:
            return bytes(Bool(1)) + bytes(self.data) if bytes(self.data) else bytes(Bool(0))

    def __str__(self):
        return str(self.data)

    def isempty(self):
        if not self.data:
            return True
        return not bool(bytes(self.data))


class Static_variant(object):
    def __init__(self, d, type_id):
        self.data = d
        self.type_id = type_id

    def __bytes__(self):
        return varint(self.type_id) + bytes(self.data)

    def __str__(self):
        return json.dumps([self.type_id, self.data.json()])


class Map(object):
    def __init__(self, data):
        self.data = data

    def __bytes__(self):
        b = b""
        b += varint(len(self.data))
        for e in self.data:
            b += bytes(e[0]) + bytes(e[1])
        return b

    def __str__(self):
        r = []
        for e in self.data:
            r.append([str(e[0]), str(e[1])])
        return json.dumps(r)


class Id(object):
    def __init__(self, d):
        self.data = Varint32(d)

    def __bytes__(self):
        return bytes(self.data)

    def __str__(self):
        return str(self.data)


class VoteId(object):
    def __init__(self, vote):
        parts = vote.split(":")
        assert len(parts) == 2
        self.type = int(parts[0])
        self.instance = int(parts[1])

    def __bytes__(self):
        binary = (self.type & 0xff) | (self.instance << 8)
        return struct.pack("<I", binary)

    def __str__(self):
        return "%d:%d" % (self.type, self.instance)


class ObjectId(object):
    """ Encodes protocol ids - serializes to the *instance* only!
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

    def __bytes__(self):
        return bytes(self.instance)  # only yield instance

    def __str__(self):
        return self.Id


class FullObjectId(object):
    """ Encodes object ids - serializes to a full object id
    """
    def __init__(self, object_str):
        if len(object_str.split(".")) == 3:
            space, type, id = object_str.split(".")
            self.space = int(space)
            self.type = int(type)
            self.id = int(id)
            self.instance = Id(int(id))
            self.Id = object_str
        else:
            raise Exception("Object id is invalid")

    def __bytes__(self):
        return (
            self.space << 56 | self.type << 48 | self.id
        ).to_bytes(8, byteorder="little", signed=False)

    def __str__(self):
        return self.Id


class Enum8(Uint8):
    def __init__(self, selection):
        assert selection in self.options or \
            isinstance(selection, int) and len(self.options) < selection, \
            "Options are %s. Given '%s'" % (
                self.options, selection)
        if selection in self.options:
            super(Enum8, self).__init__(self.options.index(selection))
        else:
            super(Enum8, self).__init__(selection)

    def __str__(self):
        return str(self.options[self.data])
