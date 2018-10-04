# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes
from builtins import chr
from builtins import range
from builtins import str
import unittest
import hashlib
from binascii import hexlify, unhexlify
import os
import json
from pprint import pprint
from beem.amount import Amount
from beembase.operations import Transfer
from beembase.objects import Operation
from beembase.signedtransactions import Signed_Transaction

wif = "5J4KCbg1G3my9b9hCaQXnHSm6vrwW9xQTJS6ZciW2Kek7cCkCEk"


class Testcases(unittest.TestCase):
    def test_Transfer(self):
        transferJson = {'from': 'test', 'to': 'test1', 'amount': "1.000 STEEM", 'memo': 'foobar'}
        t = Transfer(transferJson)
        self.assertEqual(transferJson, json.loads(str(t)))
        self.assertEqual(transferJson, t.json())
        self.assertEqual(transferJson, t.toJson())
        self.assertEqual(transferJson, t.__json__())

        transferJson = {'from': 'test', 'to': 'test1', 'amount': ['3000', 3, '@@000000037'], 'memo': 'foobar'}
        t = Transfer(transferJson)
        self.assertEqual(transferJson, json.loads(str(t)))
        self.assertEqual(transferJson, t.json())
        self.assertEqual(transferJson, t.toJson())
        self.assertEqual(transferJson, t.__json__())

        o = Operation(Transfer(transferJson))
        self.assertEqual(o.json()[1], transferJson)
        tx = {'ref_block_num': 0, 'ref_block_prefix': 0, 'expiration': '2018-04-07T09:30:53', 'operations': [o], 'extensions': [], 'signatures': []}
        s = Signed_Transaction(tx)
        s.sign(wifkeys=[wif], chain="STEEMAPPBASE")
        self.assertEqual(s.json()["operations"][0][1], transferJson)
