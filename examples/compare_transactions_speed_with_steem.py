from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes
from builtins import chr
from builtins import range
from builtins import super
import random
from pprint import pprint
from binascii import hexlify
from collections import OrderedDict

from beembase import (
    transactions,
    memo,
    operations,
    objects
)
from beembase.objects import Operation
from beembase.signedtransactions import Signed_Transaction
from beemgraphenebase.account import PrivateKey
from beemgraphenebase import account
from beembase.operationids import getOperationNameForId
from beemgraphenebase.py23 import py23_bytes, bytes_types
from beem.amount import Amount
from beem.asset import Asset
from beem.steem import Steem
import time

from steem import Steem as steemSteem
from steembase.account import PrivateKey as steemPrivateKey
from steembase.transactions import SignedTransaction as steemSignedTransaction
from steembase import operations as steemOperations
from timeit import default_timer as timer


class BeemTest(object):

    def setup(self):
        self.prefix = u"STEEM"
        self.default_prefix = u"STM"
        self.wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
        self.ref_block_num = 34294
        self.ref_block_prefix = 3707022213
        self.expiration = "2016-04-06T08:29:27"
        self.stm = Steem(offline=True)

    def doit(self, printWire=False, ops=None):
        ops = [Operation(ops)]
        tx = Signed_Transaction(ref_block_num=self.ref_block_num,
                                ref_block_prefix=self.ref_block_prefix,
                                expiration=self.expiration,
                                operations=ops)
        start = timer()
        tx = tx.sign([self.wif], chain=self.prefix)
        end1 = timer()
        tx.verify([PrivateKey(self.wif, prefix=u"STM").pubkey], self.prefix)
        end2 = timer()
        return end2 - end1, end1 - start


class SteemTest(object):

    def setup(self):
        self.prefix = u"STEEM"
        self.default_prefix = u"STM"
        self.wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
        self.ref_block_num = 34294
        self.ref_block_prefix = 3707022213
        self.expiration = "2016-04-06T08:29:27"

    def doit(self, printWire=False, ops=None):
        ops = [steemOperations.Operation(ops)]
        tx = steemSignedTransaction(ref_block_num=self.ref_block_num,
                                    ref_block_prefix=self.ref_block_prefix,
                                    expiration=self.expiration,
                                    operations=ops)
        start = timer()
        tx = tx.sign([self.wif], chain=self.prefix)
        end1 = timer()
        tx.verify([steemPrivateKey(self.wif, prefix=u"STM").pubkey], self.prefix)
        end2 = timer()
        return end2 - end1, end1 - start


if __name__ == "__main__":
    steem_test = SteemTest()
    beem_test = BeemTest()
    steem_test.setup()
    beem_test.setup()
    steem_times = []
    beem_times = []
    loops = 50
    for i in range(0, loops):
        print(i)
        opSteem = steemOperations.Transfer(**{
            "from": "foo",
            "to": "baar",
            "amount": "111.110 STEEM",
            "memo": "Fooo"
        })
        opBeem = operations.Transfer(**{
            "from": "foo",
            "to": "baar",
            "amount": Amount("111.110 STEEM", steem_instance=Steem(offline=True)),
            "memo": "Fooo"
        })

        t_s, t_v = steem_test.doit(ops=opSteem)
        steem_times.append([t_s, t_v])

        t_s, t_v = beem_test.doit(ops=opBeem)
        beem_times.append([t_s, t_v])

    steem_dt = [0, 0]
    beem_dt = [0, 0]
    for i in range(0, loops):
        steem_dt[0] += steem_times[i][0]
        steem_dt[1] += steem_times[i][1]
        beem_dt[0] += beem_times[i][0]
        beem_dt[1] += beem_times[i][1]
    print("steem vs beem:\n")
    print("steem: sign: %.2f s, verification %.2f s" % (steem_dt[0] / loops, steem_dt[1] / loops))
    print("beem:  sign: %.2f s, verification %.2f s" % (beem_dt[0] / loops, beem_dt[1] / loops))
    print("------------------------------------")
    print("beem is %.2f %% (sign) and %.2f %% (verify) faster than steem" %
          (steem_dt[0] / beem_dt[0] * 100, steem_dt[1] / beem_dt[1] * 100))
