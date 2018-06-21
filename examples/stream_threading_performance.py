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
    nodes.update_nodes()
    node_list = nodes.get_nodes()

    vote_result = []
    duration = []
    stm = Steem(node=node_list, timeout=timeout)
    print("Without threading")
    stream_votes(stm, False, 8)
    if threading:
        print("\n Threading with %d threads is activated now." % thread_num)

    for n in range(len(node_list)):
        print("\n Round %d / %d" % (n, len(node_list)))
        stm = Steem(node=node_list, timeout=timeout)
        print(stm)
        opcount, total_duration = stream_votes(stm, threading, thread_num)
        vote_result.append(opcount)
        duration.append(total_duration)
        node_list = node_list[1:] + [node_list[0]]
    print("Finished!")

    for n in range(len(node_list)):
        print(" votes: %d, time %.2f" % (vote_result[n], duration[n]))
