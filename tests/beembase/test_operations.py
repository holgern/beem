# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes
from builtins import chr
from builtins import range
import unittest
import hashlib
from binascii import hexlify, unhexlify
import os
import json
from pprint import pprint
from beembase.operations import Transfer


class Testcases(unittest.TestCase):

    def test_Transfer(self):
        transferJson = {'from': 'test', 'to': 'test1', 'amount': '1.000 SBD', 'memo': 'foobar'}
        t = Transfer(transferJson)
        self.assertEqual(transferJson, json.loads(str(t)))
        self.assertEqual(transferJson, t.json())
        self.assertEqual(transferJson, t.toJson())
        self.assertEqual(transferJson, t.__json__())
