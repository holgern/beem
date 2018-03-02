from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes, int, str, chr
import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


if PY3:
    bytes_types = bytes,
    string_types = str,
    integer_types = int,
    text_type = str
    binary_type = bytes
else:
    bytes_types = bytes,
    string_types = basestring,  # noqa: F821
    integer_types = (int, long)  # noqa: F821
    text_type = unicode   # noqa: F821
    binary_type = str


def py23_bytes(item=None, encoding=None):
    if item is None:
        return b''
    if hasattr(item, '__bytes__'):
        return item.__bytes__()
    else:
        if encoding:
            return bytes(item, encoding)
        else:
            return bytes(item)


def py23_chr(item):
    if PY2:
        return chr(item)
    else:
        return bytes([item])
