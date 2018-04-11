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
from beemgrapheneapi.rpcutils import NumRetriesReached
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    how_many_seconds = 15
    how_many_minutes = 10
    max_batch_size = None
    threading = False
    thread_num = 16

    authorpermvoter = u"@gtg/ffdhu-gtg-witness-log|gandalf"
    [author, permlink, voter] = resolve_authorpermvoter(authorpermvoter)
    authorperm = construct_authorperm(author, permlink)

    nodes = get_node_list(appbase=False) + get_node_list(appbase=True)

    t = PrettyTable(["node", "N blocks", "N acc hist", "dur. call in s", "version"])
    t.align = "l"

    for node in nodes:
        print("Current node:", node)
        try:
            stm = Steem(node=node, num_retries=2, num_retries_call=3, timeout=5)
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

            last_node = blockchain.steem.rpc.url
            start = timer()
            block_count = 0
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
                    total_duration = formatTimedelta(datetime.now() - startTime)
                    last_block_id = block_no
                    avtran = total_transaction / (last_block_id - 19273700)
                    break
                if timer() - start > how_many_seconds:
                    break

            start = timer()
            history_count = 0
            for acc_op in account.history_reverse():
                history_count += 1
                if timer() - start > how_many_seconds:
                    break
            start = timer()
            if stm.rpc.get_use_appbase():
                votes = stm.rpc.get_active_votes({'author': author, 'permlink': permlink}, api="tags")['votes']
            else:
                votes = stm.rpc.get_active_votes(author, permlink, api="database_api")
            stop = timer()
            vote_time = stop - start
            print("votes: %d in %.2f s" % (len(votes), vote_time))
            start = timer()
            if stm.rpc.get_use_appbase():
                content = stm.rpc.get_discussion({'author': author, 'permlink': permlink}, api="tags")
            else:
                content = stm.rpc.get_content(author, permlink)
            stop = timer()
            comment_time = stop - start
            print("content: %s, %s, votes: %d in %.2f s" %
                  (content["author"], content["permlink"], len(content["active_votes"]), comment_time))
            start = timer()
            if stm.rpc.get_use_appbase():
                acc = stm.rpc.find_accounts({'accounts': [author]}, api="database")["accounts"][0]
            else:
                acc = stm.rpc.get_accounts([author])[0]
            stop = timer()
            account_time = stop - start
            print("account: %s in %.2f s" % (acc["active"]["key_auths"][0][0], account_time))

            print("* Processed %d blocks in %.2f seconds" % (block_count, how_many_seconds))
            print("* Processed %d account ops in %.2f seconds" % (history_count, how_many_seconds))
            print("* blockchain version: %s" % (blockchain_version))
            t.add_row([
                node,
                block_count,
                history_count,
                ("%.2f" % ((vote_time + comment_time + account_time) / 3.0)),
                blockchain_version
            ])
        except NumRetriesReached:
            print("NumRetriesReached")
            continue
        except Exception as e:
            print("Error: " + str(e))
            continue
    print(t)
