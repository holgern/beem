from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import sys
from datetime import datetime, timedelta
import time
import io
import logging

from beem.blockchain import Blockchain
from beem.block import Block
from beem.steem import Steem
from beem.utils import parse_time, formatTimedelta
from beem.nodelist import NodeList
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def stream_votes(stm, threading, thread_num):
    b = Blockchain(steem_instance=stm)
    opcount = 0
    start_time = time.time()
    for op in b.stream(start=23483000, stop=23485000, threading=threading, thread_num=thread_num,
                       opNames=['vote']):
        sys.stdout.write("\r%s" % op['block_num'])
        opcount += 1
    now = time.time()
    total_duration = now - start_time
    print(" votes: %d, time %.2f" % (opcount, total_duration))
    return opcount, total_duration


if __name__ == "__main__":
    node_setup = 1
    threading = True
    thread_num = 8
    timeout = 10
    nodes = NodeList()
    nodes.update_nodes(weights={"block": 1})
    node_list = nodes.get_nodes()[:5]

    vote_result = []
    duration = []

    stm = Steem(node=node_list, timeout=timeout)
    b = Blockchain(steem_instance=stm)
    block = b.get_current_block()
    block.set_cache_auto_clean(False)
    opcount, total_duration = stream_votes(stm, threading, thread_num)
    print("Finished!")
    block.set_cache_auto_clean(True)
    cache_len = len(list(block._cache))
    start_time = time.time()
    block.clear_cache_from_expired_items()
    clear_duration = time.time() - start_time
    time.sleep(5)
    cache_len_after = len(list(block._cache))
    start_time = time.time()
    print(str(block._cache))
    clear_duration2 = time.time() - start_time
    print("Results:")
    print("%d Threads with https duration: %.2f s - votes: %d" % (thread_num, total_duration, opcount))
    print("Clear %d items in %.3f s (%.3f s) (%d remaining)" % (cache_len, clear_duration, clear_duration2, cache_len_after))
