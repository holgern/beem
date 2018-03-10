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
from beemgrapheneapi.rpcutils import NumRetriesReached
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://node.steem.ws", "wss://steemd.steemgigs.org", "wss://steemd.steemit.com",
         "wss://steemd.minnowsupportproject.org", "https://api.steemitstage.com", "https://api.steemit.com","https://rpc.buildteam.io",
         "https://steemd.minnowsupportproject.org", "https://steemd.pevo.science", "https://rpc.steemviz.com", "https://seed.bitcoiner.me",
         "https://rpc.steemliberator.com", "https://api.steemit.com", "https://steemd.privex.io"]

if __name__ == "__main__":
    how_many_minutes = 10

    
    max_batch_size = None
    threading = False
    thread_num = 16
    for node in nodes:
        print("Current node:", node)
        try:
            stm = Steem(node=node, num_retries=2)
            blockchain = Blockchain(steem_instance=stm)
            
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
                    print("* Processed %d blockchain minutes in %s" % (how_many_minutes, total_duration))
                    break
        except NumRetriesReached:
            print("NumRetriesReached")
            continue
        except Exception as e:
            print("Error: " + str(e))
            continue


