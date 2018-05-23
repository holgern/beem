from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import sys
from datetime import datetime, timedelta
import time
import io
from timeit import default_timer as timer
import logging
from prettytable import PrettyTable
from beem.blockchain import Blockchain
from beem.account import Account
from beem.block import Block
from beem.steem import Steem
from beem.utils import parse_time, formatTimedelta, get_node_list, construct_authorperm, resolve_authorperm, resolve_authorpermvoter, construct_authorpermvoter
from beem.comment import Comment
from beem.vote import Vote
from beemapi.exceptions import NumRetriesReached
FUTURES_MODULE = None
if not FUTURES_MODULE:
    try:
        from concurrent.futures import ThreadPoolExecutor, wait, as_completed
        FUTURES_MODULE = "futures"
    except ImportError:
        FUTURES_MODULE = None
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
quit_thread = False


def benchmark_node(node, how_many_minutes=10, how_many_seconds=30):
    block_count = 0
    history_count = 0
    access_time = 0
    follow_time = 0
    blockchain_version = u'0.0.0'
    sucessfull = False
    error_msg = None
    start_total = timer()
    max_batch_size = None
    threading = False
    thread_num = 16
    try:
        stm = Steem(node=node, num_retries=2, num_retries_call=3, timeout=10)
        blockchain = Blockchain(steem_instance=stm)
        account = Account("gtg", steem_instance=stm)
        blockchain_version = stm.get_blockchain_version()

        last_block_id = 19273700
        last_block = Block(last_block_id, steem_instance=stm)

        stopTime = last_block.time() + timedelta(seconds=how_many_minutes * 60)
        total_transaction = 0

        start = timer()
        for entry in blockchain.blocks(start=last_block_id, max_batch_size=max_batch_size, threading=threading, thread_num=thread_num):
            block_no = entry.identifier
            block_count += 1
            if "block" in entry:
                trxs = entry["block"]["transactions"]
            else:
                trxs = entry["transactions"]

            for tx in trxs:
                for op in tx["operations"]:
                    total_transaction += 1
            if "block" in entry:
                block_time = parse_time(entry["block"]["timestamp"])
            else:
                block_time = parse_time(entry["timestamp"])

            if block_time > stopTime:
                last_block_id = block_no
                break
            if timer() - start > how_many_seconds or quit_thread:
                break

        start = timer()
        for acc_op in account.history_reverse(batch_size=100):
            history_count += 1
            if timer() - start > how_many_seconds or quit_thread:
                break
        start = timer()
        Vote(authorpermvoter, steem_instance=stm)
        stop = timer()
        vote_time = stop - start
        start = timer()
        Comment(authorperm, steem_instance=stm)
        stop = timer()
        comment_time = stop - start
        start = timer()
        Account(author, steem_instance=stm)
        stop = timer()
        account_time = stop - start
        start = timer()
        account.get_followers()
        stop = timer()
        follow_time = stop - start
        access_time = (vote_time + comment_time + account_time + follow_time) / 4.0
        sucessfull = True
    except NumRetriesReached:
        error_msg = 'NumRetriesReached'
    except KeyboardInterrupt:
        error_msg = 'KeyboardInterrupt'
        # quit = True
    except Exception as e:
        error_msg = str(e)
    return {'sucessfull': sucessfull, 'node': node, 'error': error_msg,
            'total_duration': timer() - start_total, 'block_count': block_count,
            'history_count': history_count, 'access_time': access_time, 'follow_time': follow_time,
            'version': blockchain_version}


if __name__ == "__main__":
    how_many_seconds = 30
    how_many_minutes = 10
    threading = True
    set_default_nodes = True
    quit_thread = False
    benchmark_time = timer()

    authorpermvoter = u"@gtg/ffdhu-gtg-witness-log|gandalf"
    [author, permlink, voter] = resolve_authorpermvoter(authorpermvoter)
    authorperm = construct_authorperm(author, permlink)

    nodes = get_node_list(appbase=False) + get_node_list(appbase=True)
    t = PrettyTable(["node", "N blocks", "N acc hist", "dur. call in s"])
    t.align = "l"
    working_nodes = []
    results = []
    if threading and FUTURES_MODULE:
        pool = ThreadPoolExecutor(max_workers=len(nodes) + 1)
        futures = []
        for node in nodes:
            futures.append(pool.submit(benchmark_node, node, how_many_minutes, how_many_seconds))
        try:
            results = [r.result() for r in as_completed(futures)]
        except KeyboardInterrupt:
            quit_thread = True
            print("benchmark aborted.")
    else:
        for node in nodes:
            print("Current node:", node)
            result = benchmark_node(node, how_many_minutes, how_many_seconds)
            results.append(result)

    sortedList = sorted(results, key=lambda self: self["total_duration"], reverse=False)
    for result in sortedList:
        if result["sucessfull"]:
            t.add_row([
                result["node"],
                result["block_count"],
                result["history_count"],
                ("%.2f" % (result["access_time"]))
            ])
            working_nodes.append(result["node"])
    print(t)
    print("\n")
    print("Total benchmark time: %.2f s\n" % (timer() - benchmark_time))
    if set_default_nodes:
        stm = Steem(offline=True)
        stm.set_default_nodes(working_nodes)
    else:
        print("beempy set nodes " + str(working_nodes))
