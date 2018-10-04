# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import unittest
import json
from beemgraphenebase import types
from beem.amount import Amount
from beem import Steem


class Testcases(unittest.TestCase):

    def test_varint(self):
        expected = [
            None,
            b'\x01', b'\x02', b'\x03', b'\x04', b'\x05', b'\x06', b'\x07',
            b'\x08', b'\t', b'\n', b'\x0b', b'\x0c', b'\r', b'\x0e', b'\x0f',
            b'\x10', b'\x11', b'\x12', b'\x13', b'\x14', b'\x15', b'\x16',
            b'\x17', b'\x18', b'\x19', b'\x1a', b'\x1b', b'\x1c', b'\x1d',
            b'\x1e', b'\x1f', b' ', b'!', b'"', b'#', b'$', b'%', b'&', b"'",
            b'(', b')', b'*', b'+', b',', b'-', b'.', b'/', b'0', b'1', b'2',
            b'3', b'4', b'5', b'6', b'7', b'8', b'9', b':', b';', b'<', b'=',
            b'>', b'?', b'@', b'A', b'B', b'C', b'D', b'E', b'F', b'G', b'H',
            b'I', b'J', b'K', b'L', b'M', b'N', b'O', b'P', b'Q', b'R', b'S',
            b'T', b'U', b'V', b'W', b'X', b'Y', b'Z', b'[', b'\\', b']', b'^',
            b'_', b'`', b'a', b'b', b'c', b'd', b'e', b'f', b'g', b'h', b'i',
            b'j', b'k', b'l', b'm', b'n', b'o', b'p', b'q', b'r', b's', b't',
            b'u', b'v', b'w', b'x', b'y', b'z', b'{', b'|', b'}', b'~',
            b'\x7f', b'\x80\x01', b'\x81\x01', b'\x82\x01', b'\x83\x01',
            b'\x84\x01', b'\x85\x01', b'\x86\x01', b'\x87\x01', b'\x88\x01',
            b'\x89\x01', b'\x8a\x01', b'\x8b\x01', b'\x8c\x01', b'\x8d\x01',
            b'\x8e\x01', b'\x8f\x01', b'\x90\x01', b'\x91\x01', b'\x92\x01',
            b'\x93\x01', b'\x94\x01', b'\x95\x01', b'\x96\x01', b'\x97\x01',
            b'\x98\x01', b'\x99\x01', b'\x9a\x01', b'\x9b\x01', b'\x9c\x01',
            b'\x9d\x01', b'\x9e\x01', b'\x9f\x01', b'\xa0\x01', b'\xa1\x01',
            b'\xa2\x01', b'\xa3\x01', b'\xa4\x01', b'\xa5\x01', b'\xa6\x01',
            b'\xa7\x01', b'\xa8\x01', b'\xa9\x01', b'\xaa\x01', b'\xab\x01',
            b'\xac\x01', b'\xad\x01', b'\xae\x01', b'\xaf\x01', b'\xb0\x01',
            b'\xb1\x01', b'\xb2\x01', b'\xb3\x01', b'\xb4\x01', b'\xb5\x01',
            b'\xb6\x01', b'\xb7\x01', b'\xb8\x01', b'\xb9\x01', b'\xba\x01',
            b'\xbb\x01', b'\xbc\x01', b'\xbd\x01', b'\xbe\x01', b'\xbf\x01',
            b'\xc0\x01', b'\xc1\x01', b'\xc2\x01', b'\xc3\x01', b'\xc4\x01',
            b'\xc5\x01', b'\xc6\x01', b'\xc7\x01']
        for i in range(1, 200):
            self.assertEqual(types.varint(i), expected[i])
            self.assertEqual(types.varintdecode(expected[i]), i)

    def test_variable_buffer(self):
        self.assertEqual(
            types.variable_buffer(b"Hello"),
            b"\x05Hello"
        )

    def test_JsonObj(self):
        j = types.JsonObj(json.dumps(dict(foo="bar")))
        self.assertIn("foo", j)
        self.assertEqual(j["foo"], "bar")

    def test_uint8(self):
        u = types.Uint8(10)
        self.assertEqual(bytes(u), b"\n")
        self.assertEqual(str(u), "10")

    def test_uint16(self):
        u = types.Uint16(2**16 - 1)
        self.assertEqual(bytes(u), b"\xff\xff")
        self.assertEqual(str(u), str(2**16 - 1))

    def test_uint32(self):
        u = types.Uint32(2**32 - 1)
        self.assertEqual(bytes(u), b"\xff\xff\xff\xff")
        self.assertEqual(str(u), str(2**32 - 1))

    def test_uint64(self):
        u = types.Uint64(2**64 - 1)
        self.assertEqual(bytes(u), b"\xff\xff\xff\xff\xff\xff\xff\xff")
        self.assertEqual(str(u), str(2**64 - 1))

    def test_int64(self):
        u = types.Int64(2**63 - 1)
        self.assertEqual(bytes(u), b"\xff\xff\xff\xff\xff\xff\xff\x7f")
        self.assertEqual(str(u), str(9223372036854775807))

    def test_int16(self):
        u = types.Int16(2**15 - 1)
        self.assertEqual(bytes(u), b"\xff\x7f")
        self.assertEqual(str(u), str(2**15 - 1))

    def test_varint32(self):
        u = types.Varint32(2**32 - 1)
        self.assertEqual(bytes(u), b"\xff\xff\xff\xff\x0f")
        self.assertEqual(str(u), str(4294967295))
        u = types.Id(2**32 - 1)
        self.assertEqual(bytes(u), b"\xff\xff\xff\xff\x0f")
        self.assertEqual(str(u), str(4294967295))

    def test_string(self):
        u = types.String("HelloFoobar")
        self.assertEqual(bytes(u), b"\x0bHelloFoobar")
        self.assertEqual(str(u), "HelloFoobar")

        u = types.String("\x07\x08\x09\x0a\x0b\x0c\x0d\x0e")
        self.assertEqual(bytes(u), b"\x14u0007b\t\nu000bf\ru000e")
        self.assertEqual(str(u), "\x07\x08\x09\x0a\x0b\x0c\x0d\x0e")

    def test_void(self):
        u = types.Void()
        self.assertEqual(bytes(u), b"")
        self.assertEqual(str(u), "")

    def test_array(self):
        u = types.Array([types.Uint8(10) for x in range(2)] + [11])
        self.assertEqual(bytes(u), b'\x03\n\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        self.assertEqual(str(u), "[10, 10, 11]")
        u = types.Set([types.Uint16(10) for x in range(10)])
        self.assertEqual(bytes(u), b"\n\n\x00\n\x00\n\x00\n\x00\n\x00\n\x00\n\x00\n\x00\n\x00\n\x00")
        self.assertEqual(str(u), "[10, 10, 10, 10, 10, 10, 10, 10, 10, 10]")
        u = types.Array(["Foobar"])
        # We do not support bytes of Array containing String only!
        # self.assertEqual(bytes(u), b'')
        self.assertEqual(str(u), '["Foobar"]')

    def test_PointInTime(self):
        u = types.PointInTime("2018-07-06T22:10:00")
        self.assertEqual(bytes(u), b"\xb8\xe8?[")
        self.assertEqual(str(u), "2018-07-06T22:10:00")

    def test_Signature(self):
        u = types.Signature(b"\x00" * 33)
        self.assertEqual(bytes(u), b"\x00" * 33)
        self.assertEqual(str(u), '"000000000000000000000000000000000000000000000000000000000000000000"')

    def test_Bytes(self):
        u = types.Bytes("00" * 5)
        self.assertEqual(bytes(u), b'\x05\x00\x00\x00\x00\x00')
        self.assertEqual(str(u), "00" * 5)

    def test_Bool(self):
        u = types.Bool(True)
        self.assertEqual(bytes(u), b"\x01")
        self.assertEqual(str(u), 'true')
        u = types.Bool(False)
        self.assertEqual(bytes(u), b"\x00")
        self.assertEqual(str(u), 'false')

    def test_Optional(self):
        u = types.Optional(types.Uint16(10))
        self.assertEqual(bytes(u), b"\x01\n\x00")
        self.assertEqual(str(u), '10')
        self.assertFalse(u.isempty())
        u = types.Optional(None)
        self.assertEqual(bytes(u), b"\x00")
        self.assertEqual(str(u), 'None')
        self.assertTrue(u.isempty())

    def test_Static_variant(self):
        class Tmp(types.Uint16):
            def json(self):
                return "Foobar"

        u = types.Static_variant(Tmp(10), 10)
        self.assertEqual(bytes(u), b"\n\n\x00")
        self.assertEqual(str(u), '[10, "Foobar"]')

    def test_Map(self):
        u = types.Map([[types.Uint16(10), types.Uint16(11)]])
        self.assertEqual(bytes(u), b"\x01\n\x00\x0b\x00")
        self.assertEqual(str(u), '[["10", "11"]]')
