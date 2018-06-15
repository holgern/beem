"""types."""
# encoding=utf8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import bytes
from builtins import str
from builtins import object
from builtins import int
import json
import struct
import sys
import time
from calendar import timegm
from binascii import hexlify, unhexlify
from datetime import datetime
from collections import OrderedDict
from .objecttypes import object_type

from future.utils import python_2_unicode_compatible
from .py23 import py23_bytes

timeformat = '%Y-%m-%dT%H:%M:%S%Z'


def varint(n):
    """Varint encoding."""
    data = b''
    while n >= 0x80:
        data += bytes([(n & 0x7f) | 0x80])
        n >>= 7
    data += bytes([n])
    return data


def varintdecode(data):
    """Varint decoding."""
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
    """Encodes variable length buffer."""
    return varint(len(s)) + s


def JsonObj(data):
    """Returns json object from data."""
    return json.loads(str(data))


@python_2_unicode_compatible
class Uint8(object):
    """Uint8."""

    def __init__(self, d):
        """init."""
        self.data = int(d)

    def __bytes__(self):
        """Returns bytes."""
        return struct.pack("<B", self.data)

    def __str__(self):
        """Returns str"""
        return '%d' % self.data


@python_2_unicode_compatible
class Int16(object):
    """Int16."""

    def __init__(self, d):
        """init."""
        self.data = int(d)

    def __bytes__(self):
        """Returns bytes."""
        return struct.pack("<h", int(self.data))

    def __str__(self):
        return '%d' % self.data


@python_2_unicode_compatible
class Uint16(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        """Returns bytes."""
        return struct.pack("<H", self.data)

    def __str__(self):
        return '%d' % self.data


@python_2_unicode_compatible
class Uint32(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        """Returns bytes."""
        return struct.pack("<I", self.data)

    def __str__(self):
        """Returns data as string."""
        return '%d' % self.data


@python_2_unicode_compatible
class Uint64(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        """Returns bytes."""
        return struct.pack("<Q", self.data)

    def __str__(self):
        """Returns data as string."""
        return '%d' % self.data


@python_2_unicode_compatible
class Varint32(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        """Returns bytes."""
        return varint(self.data)

    def __str__(self):
        """Returns data as string."""
        return '%d' % self.data


@python_2_unicode_compatible
class Int64(object):
    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        """Returns bytes."""
        return struct.pack("<q", self.data)

    def __str__(self):
        """Returns data as string."""
        return '%d' % self.data


@python_2_unicode_compatible
class String(object):
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        """Returns bytes representation."""
        d = self.unicodify()
        return varint(len(d)) + d

    def __str__(self):
        """Returns data as string."""
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


@python_2_unicode_compatible
class Bytes(object):
    def __init__(self, d, length=None):
        self.data = d
        if length:
            self.length = length
        else:
            self.length = len(self.data)

    def __bytes__(self):
        """Returns data as bytes."""
        # FIXME constraint data to self.length
        d = unhexlify(bytes(self.data, 'utf-8'))
        return varint(len(d)) + d

    def __str__(self):
        """Returns data as string."""
        return str(self.data)


@python_2_unicode_compatible
class Void(object):
    def __init__(self):
        pass

    def __bytes__(self):
        """Returns bytes representation."""
        return b''

    def __str__(self):
        """Returns data as string."""
        return ""


@python_2_unicode_compatible
class Array(object):
    def __init__(self, d):
        self.data = d
        self.length = Varint32(len(self.data))

    def __bytes__(self):
        """Returns bytes representation."""
        return py23_bytes(self.length) + b"".join([py23_bytes(a) for a in self.data])

    def __str__(self):
        """Returns data as string."""
        r = []
        for a in self.data:
            try:
                if isinstance(a, String):
                    r.append(str(a))
                else:
                    r.append(JsonObj(a))
            except Exception:
                r.append(str(a))
        return json.dumps(r)


@python_2_unicode_compatible
class PointInTime(object):
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        """Returns bytes representation."""
        if isinstance(self.data, datetime):
            unixtime = timegm(self.data.timetuple())
        elif sys.version > '3':
            unixtime = timegm(time.strptime((self.data + "UTC"), timeformat))
        else:
            unixtime = timegm(time.strptime((self.data + "UTC"), timeformat.encode("utf-8")))
        if unixtime < 0:
            return struct.pack("<i", unixtime)
        return struct.pack("<I", unixtime)

    def __str__(self):
        """Returns data as string."""
        return self.data


@python_2_unicode_compatible
class Signature(object):
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        """Returns bytes representation."""
        return self.data

    def __str__(self):
        """Returns data as string."""
        return json.dumps(hexlify(self.data).decode('ascii'))


@python_2_unicode_compatible
class Bool(Uint8):  # Bool = Uint8
    def __init__(self, d):
        super(Bool, self).__init__(d)

    def __str__(self):
        """Returns data as string."""
        return json.dumps(True) if self.data else json.dumps(False)


class Set(Array):  # Set = Array
    def __init__(self, d):
        super(Set, self).__init__(d)


@python_2_unicode_compatible
class Fixed_array(object):
    def __init__(self, d):
        raise NotImplementedError

    def __bytes__(self):
        """Returns bytes representation."""
        raise NotImplementedError

    def __str__(self):
        """Returns data as string."""
        raise NotImplementedError


@python_2_unicode_compatible
class Optional(object):
    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        """Returns data as bytes."""
        if not self.data:
            return py23_bytes(Bool(0))
        else:
            return py23_bytes(Bool(1)) + py23_bytes(self.data) if py23_bytes(self.data) else py23_bytes(Bool(0))

    def __str__(self):
        """Returns data as string."""
        return str(self.data)

    def isempty(self):
        if not self.data:
            return True
        return not bool(py23_bytes(self.data))


@python_2_unicode_compatible
class Static_variant(object):
    def __init__(self, d, type_id):
        self.data = d
        self.type_id = type_id

    def __bytes__(self):
        """Returns bytes representation."""
        return varint(self.type_id) + py23_bytes(self.data)

    def __str__(self):
        """Returns data as string."""
        return json.dumps([self.type_id, self.data.json()])


@python_2_unicode_compatible
class Map(object):
    def __init__(self, data):
        self.data = data

    def __bytes__(self):
        """Returns bytes representation."""
        b = b""
        b += varint(len(self.data))
        for e in self.data:
            b += py23_bytes(e[0]) + py23_bytes(e[1])
        return b

    def __str__(self):
        """Returns data as string."""
        r = []
        for e in self.data:
            r.append([str(e[0]), str(e[1])])
        return json.dumps(r)


@python_2_unicode_compatible
class Id(object):
    def __init__(self, d):
        self.data = Varint32(d)

    def __bytes__(self):
        """Returns bytes representation."""
        return py23_bytes(self.data)

    def __str__(self):
        """Returns data as string."""
        return str(self.data)


@python_2_unicode_compatible
class Enum8(Uint8):
    def __init__(self, selection):
        if selection not in self.options and \
                not (isinstance(selection, int) and len(self.options) < selection):
            raise AssertionError("Options are %s. Given '%s'" % (
                self.options, selection))
        if selection in self.options:
            super(Enum8, self).__init__(self.options.index(selection))
        else:
            super(Enum8, self).__init__(selection)

    def __str__(self):
        """Returns data as string."""
        return str(self.options[self.data])
