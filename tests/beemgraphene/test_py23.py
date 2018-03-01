# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import pytest
import unittest
from beemgraphenebase.py23 import (
    py23_bytes,
    bytes_types,
    integer_types,
    string_types,
    text_type,
    PY2,
    PY3
)


TEST_UNICODE_STR = u'ℝεα∂@ßʟ℮ ☂ℯṧт υηḯ¢☺ḓ℮'
# Tk icon as a .gif:
TEST_BYTE_STR = b'GIF89a\x0e\x00\x0b\x00\x80\xff\x00\xff\x00\x00\xc0\xc0\xc0!\xf9\x04\x01\x00\x00\x01\x00,\x00\x00\x00\x00\x0e\x00\x0b\x00@\x02\x1f\x0c\x8e\x10\xbb\xcan\x90\x99\xaf&\xd8\x1a\xce\x9ar\x06F\xd7\xf1\x90\xa1c\x9e\xe8\x84\x99\x89\x97\xa2J\x01\x00;\x1a\x14\x00;;\xba\nD\x14\x00\x00;;'


class Testcases(unittest.TestCase):
    def test_bytes_encoding_arg(self):
        """
        The bytes class has changed in Python 3 to accept an
        additional argument in the constructor: encoding.
        It would be nice to support this without breaking the
        isinstance(..., bytes) test below.
        """
        u = u'Unicode string: \u5b54\u5b50'
        b = py23_bytes(u, encoding='utf-8')
        self.assertEqual(b, u.encode('utf-8'))

    def test_bytes_encoding_arg_non_kwarg(self):
        """
        As above, but with a positional argument
        """
        u = u'Unicode string: \u5b54\u5b50'
        b = py23_bytes(u, 'utf-8')
        self.assertEqual(b, u.encode('utf-8'))

    def test_bytes_int(self):
        """
        In Py3, bytes(int) -> bytes object of size given by the parameter initialized with null
        """
        self.assertEqual(py23_bytes(5), b'\x00\x00\x00\x00\x00')
        # Test using newint:
        self.assertEqual(py23_bytes(int(5)), b'\x00\x00\x00\x00\x00')
        self.assertTrue(isinstance(py23_bytes(int(5)), bytes_types))

    def test_bytes_iterable_of_ints(self):
        self.assertEqual(py23_bytes([65, 66, 67]), b'ABC')
        self.assertEqual(py23_bytes([int(120), int(121), int(122)]), b'xyz')

    def test_bytes_bytes(self):
        self.assertEqual(py23_bytes(b'ABC'), b'ABC')

    def test_bytes_is_bytes(self):
        b = py23_bytes(b'ABC')
        self.assertTrue(py23_bytes(b) is b)
        self.assertEqual(repr(py23_bytes(b)), "b'ABC'")

    def test_isinstance_bytes(self):
        self.assertTrue(isinstance(py23_bytes(b'blah'), bytes_types))

    def test_isinstance_bytes_subclass(self):
        """
        Issue #89
        """
        value = py23_bytes(b'abc')

        class Magic():
            def __bytes__(self):
                return py23_bytes(b'abc')

        self.assertEqual(value, py23_bytes(Magic()))

    def test_isinstance_oldbytestrings_bytes(self):
        """
        Watch out for this. Byte-strings produced in various places in Py2
        are of type 'str'. With 'from future.builtins import bytes', 'bytes'
        is redefined to be a subclass of 'str', not just an alias for 'str'.
        """
        self.assertTrue(isinstance(b'blah', bytes_types))   # not with the redefined bytes obj
        self.assertTrue(isinstance(u'blah'.encode('utf-8'), bytes_types))   # not with the redefined bytes obj

    def test_bytes_getitem(self):
        b = py23_bytes(b'ABCD')
        self.assertEqual(b[0], 65)
        self.assertEqual(b[-1], 68)
        self.assertEqual(b[0:1], b'A')
        self.assertEqual(b[:], b'ABCD')

    def test_integer_types(self):
        a = int(5)
        if PY2:
            b = long(10)  # noqa: F821
        else:
            b = int(10)
        self.assertTrue(isinstance(a, integer_types))
        self.assertTrue(isinstance(b, integer_types))

    def test_string_types(self):
        a = 'abc'
        b = u'abc'
        c = b'abc'
        self.assertTrue(isinstance(a, string_types))
        self.assertTrue(isinstance(b, string_types))
        self.assertTrue(isinstance(c, string_types))


if __name__ == '__main__':
    unittest.main()
