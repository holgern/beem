from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import sys
from datetime import datetime, timedelta
import time
import io
import logging
from prettytable import PrettyTable
from beem.blockchain import Blockchain
from beem.account import Account
from beem.block import Block
from beem.steem import Steem
from beem.utils import parse_time, formatTimedelta, get_node_list
from beemgrapheneapi.rpcutils import NumRetriesReached
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    how_many_minutes = 10
    how_many_virtual_op = 10000
    max_batch_size = None
    threading = False
    thread_num = 16
    nodes = get_node_list(appbase=True)
    nodes.append(get_node_list(appbase=False))
    t = PrettyTable(["node", "10 blockchain minutes", "10000 virtual account op", "version"])
    t.align = "l"
    for node in nodes:
        print("Current node:", node)
        try:
            stm = Steem(node=node, num_retries=3)
            blockchain = Blockchain(steem_instance=stm)
            account = Account("gtg", steem_instance=stm)
            virtual_op_count = account.virtual_op_count()
            blockchain_version = stm.get_blockchain_version()

            last_block_id = 19273700
            last_block = Block(last_block_id, steem_instance=stm)
            startTime = datetime.now()

            stopTime = last_block.time() + timedelta(seconds=how_many_minutes * 60)
            ltime = time.time()
            cnt = 0
            total_transaction = 0

            start_time = time.time()
            last_node = blockchain.steem.rpc.url

            for entry in blockchain.blocks(start=last_block_id, max_batch_size=max_batch_size, threading=threading, thread_num=thread_num):
                block_no = entry.identifier
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
                    total_duration = formatTimedelta(datetime.now() - startTime)
                    last_block_id = block_no
                    avtran = total_transaction / (last_block_id - 19273700)
                    break
            start_time = time.time()

            stopOP = virtual_op_count - how_many_virtual_op + 1
            i = 0
            for acc_op in account.history_reverse(stop=stopOP):
                i += 1
            total_duration_acc = formatTimedelta(datetime.now() - startTime)

            print("* Processed %d blockchain minutes in %s" % (how_many_minutes, total_duration))
            print("* Processed %d account ops in %s" % (i, total_duration_acc))
            print("* blockchain version: %s" % (blockchain_version))
            t.add_row([
                node,
                total_duration,
                total_duration_acc,
                blockchain_version
            ])
        except NumRetriesReached:
            print("NumRetriesReached")
            continue
        except Exception as e:
            print("Error: " + str(e))
            continue
    print(t)
