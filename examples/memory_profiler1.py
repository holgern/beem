from __future__ import print_function
from memory_profiler import profile
import sys
from datetime import datetime, timedelta
import time
import io
from beem.steem import Steem
from beem.account import Account
from beem.amount import Amount
from beem.blockchain import Blockchain
from beem.utils import parse_time
from beem.instance import set_shared_steem_instance
import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@profile
def profiling(name_list):
    stm = Steem()
    set_shared_steem_instance(stm)
    del stm
    print("start")
    for name in name_list:
        print("account: %s" % (name))
        acc = Account(name)
        max_index = acc.virtual_op_count()
        print(max_index)
        stopTime = datetime(2018, 4, 22, 0, 0, 0)
        hist_elem = None
        for h in acc.history_reverse(stop=stopTime):
            hist_elem = h
        print(hist_elem)
    print("blockchain")
    blockchain_object = Blockchain()
    current_num = blockchain_object.get_current_block_num()
    startBlockNumber = current_num - 20
    endBlockNumber = current_num
    block_elem = None
    for o in blockchain_object.stream(start=startBlockNumber, stop=endBlockNumber):
        print("block %d" % (o["block_num"]))
        block_elem = o
    print(block_elem)


if __name__ == "__main__":

    account_list = ["utopian-io", "busy.org", "minnowsupport", "qurator", "thesteemengine", "ethandsmith", "make-a-whale", "feedyourminnows", "steembasicincome",
                    "sbi2", "sbi3", "sbi4", "sbi5", "sbi6", "steemdunk", "thehumanbot", "resteemable", "kobusu", "mariachan", "qustodian", "randowhale",
                    "bumper", "minnowbooster", "smartsteem", "steemlike", "parosai", "koinbot", "steemfunding"]
    profiling(account_list)
