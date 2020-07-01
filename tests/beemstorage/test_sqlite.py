from builtins import chr
from builtins import range
from builtins import str
import unittest
import hashlib
from binascii import hexlify, unhexlify
import os
import json
from pprint import pprint
from beemstorage.sqlite import SQLiteStore

class MyStore(SQLiteStore):
    __tablename__ = "testing"
    __key__ = "key"
    __value__ = "value"

    defaults = {"default": "value"}


class Testcases(unittest.TestCase):
    def test_init(self):
        store = MyStore()
        self.assertEqual(store.storageDatabase, "beem.sqlite")
        store = MyStore(profile="testing")
        self.assertEqual(store.storageDatabase, "testing.sqlite")

        directory = "/tmp/temporaryFolder"
        expected = os.path.join(directory, "testing.sqlite")

        store = MyStore(profile="testing", data_dir=directory)
        self.assertEqual(store.sqlite_file, expected)

    def test_initialdata(self):
        store = MyStore()
        store["foobar"] = "banana"
        self.assertEqual(store["foobar"], "banana")

        self.assertIsNone(store["empty"])

        self.assertEqual(store["default"], "value")
        self.assertEqual(len(store), 1)