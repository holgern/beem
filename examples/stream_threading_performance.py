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
    for op in b.stream(start=23483000, stop=23483200, threading=threading, thread_num=thread_num,
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
    node_list_wss = nodes.get_nodes(https=False)[:5]
    node_list_https = nodes.get_nodes(wss=False)[:5]

    vote_result = []
    duration = []
    stm_wss = Steem(node=node_list_wss, timeout=timeout)
    stm_https = Steem(node=node_list_https, timeout=timeout)
    print("Without threading wss")
    opcount_wot_wss, total_duration_wot_wss = stream_votes(stm_wss, False, 8)
    print("Without threading https")
    opcount_wot_https, total_duration_wot_https = stream_votes(stm_https, False, 8)
    if threading:
        print("\n Threading with %d threads is activated now." % thread_num)

    stm = Steem(node=node_list_wss, timeout=timeout)
    opcount_wss, total_duration_wss = stream_votes(stm, threading, thread_num)
    opcount_https, total_duration_https = stream_votes(stm, threading, thread_num)
    print("Finished!")

    print("Results:")
    print("No Threads with wss duration: %.2f s - votes: %d" % (total_duration_wot_wss, opcount_wot_wss))
    print("No Threads with https duration: %.2f s - votes: %d" % (total_duration_wot_https, opcount_wot_https))
    print("%d Threads with wss duration: %.2f s - votes: %d" % (thread_num, total_duration_wss, opcount_wss))
    print("%d Threads with https duration: %.2f s - votes: %d" % (thread_num, total_duration_https, opcount_https))
