# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.utils import python_2_unicode_compatible
from builtins import str
from builtins import range
from builtins import object
import time
import hashlib
import json
import math
from datetime import datetime, timedelta
from .block import Block
from .blockchainobject import BlockchainObject
from beemgraphenebase.py23 import py23_bytes
from beem.instance import shared_steem_instance
from .amount import Amount
FUTURES_MODULE = None
if not FUTURES_MODULE:
    try:
        from concurrent.futures import ThreadPoolExecutor, wait, as_completed
        FUTURES_MODULE = "futures"
    except ImportError:
        FUTURES_MODULE = None


@python_2_unicode_compatible
class Blockchain(object):
    """ This class allows to access the blockchain and read data
        from it

        :param beem.steem.Steem steem_instance: Steem instance
        :param str mode: (default) Irreversible block (``irreversible``) or
            actual head block (``head``)
        :param int max_block_wait_repetition: (default) 3 maximum wait time for next block
            is max_block_wait_repetition * block_interval

        This class let's you deal with blockchain related data and methods.
        Read blockchain related data:
        .. code-block:: python

            from beem.blockchain import Blockchain
            chain = Blockchain()

        Read current block and blockchain info
        .. code-block:: python
            print(chain.get_current_block())
            print(chain.steem.info())

        Monitor for new blocks ..
        .. code-block:: python
            for block in chain.blocks():
                print(block)

        or each operation individually:
        .. code-block:: python
            for operations in chain.ops():
                print(operations)

    """
    def __init__(
        self,
        steem_instance=None,
        mode="irreversible",
        max_block_wait_repetition=None,
        data_refresh_time_seconds=900,
    ):
        self.steem = steem_instance or shared_steem_instance()

        if mode == "irreversible":
            self.mode = 'last_irreversible_block_num'
        elif mode == "head":
            self.mode = "head_block_number"
        else:
            raise ValueError("invalid value for 'mode'!")
        if max_block_wait_repetition:
            self.max_block_wait_repetition = max_block_wait_repetition
        else:
            self.max_block_wait_repetition = 3

    def is_irreversible_mode(self):
        return self.mode == 'last_irreversible_block_num'

    def get_current_block_num(self):
        """ This call returns the current block number

            .. note:: The block number returned depends on the ``mode`` used
                      when instanciating from this class.
        """
        props = self.steem.get_dynamic_global_properties(False)
        return int(props.get(self.mode))

    def get_current_block(self):
        """ This call returns the current block

            .. note:: The block number returned depends on the ``mode`` used
                      when instanciating from this class.
        """
        return Block(
            self.get_current_block_num(),
            steem_instance=self.steem
        )

    def get_estimated_block_num(self, date, estimateForwards=False, accurate=True):
        """ This call estimates the block number based on a given date

            :param datetime date: block time for which a block number is estimated

            .. note:: The block number returned depends on the ``mode`` used
                      when instanciating from this class.
        """
        block_time_seconds = self.steem.get_block_interval()
        last_block = self.get_current_block()
        if estimateForwards:
            block_offset = 10
            first_block = Block(block_offset, steem_instance=self.steem)
            time_diff = date - first_block.time()
            block_number = math.floor(time_diff.total_seconds() / block_time_seconds + block_offset)
        else:
            time_diff = last_block.time() - date
            block_number = math.floor(last_block.identifier - time_diff.total_seconds() / block_time_seconds)

        if accurate:
            if block_number > last_block.identifier:
                block_number = last_block.identifier
            block_time_diff = timedelta(seconds=10)
            while block_time_diff.total_seconds() > block_time_seconds or block_time_diff.total_seconds() < -block_time_seconds:
                block = Block(block_number, steem_instance=self.steem)
                block_time_diff = date - block.time()
                delta = block_time_diff.total_seconds() // block_time_seconds
                if delta == 0 and block_time_diff.total_seconds() < 0:
                    delta = -1
                elif delta == 0 and block_time_diff.total_seconds() > 0:
                    delta = 1
                block_number += delta
                if block_number > last_block.identifier:
                    break

        return int(block_number)

    def block_time(self, block_num):
        """ Returns a datetime of the block with the given block
            number.

            :param int block_num: Block number
        """
        return Block(
            block_num,
            steem_instance=self.steem
        ).time()

    def block_timestamp(self, block_num):
        """ Returns the timestamp of the block with the given block
            number.

            :param int block_num: Block number
        """
        block_time = Block(
            block_num,
            steem_instance=self.steem
        ).time()
        return int(time.mktime(block_time.timetuple()))

    def blocks(self, start=None, stop=None, max_batch_size=None, threading=False, thread_num=8):
        """ Yields blocks starting from ``start``.

            :param int start: Starting block
            :param int stop: Stop at this block
            :param str mode: We here have the choice between
             "head" (the last block) and "irreversible" (the block that is
             confirmed by 2/3 of all block producers and is thus irreversible)
        """
        # Let's find out how often blocks are generated!
        self.block_interval = self.steem.get_block_interval()
        current_block_num = self.get_current_block_num()
        if not start:
            start = current_block_num

        # We are going to loop indefinitely
        while True:

            # Get chain properies to identify the
            if stop:
                head_block = stop
            else:
                current_block_num = self.get_current_block_num()
                head_block = current_block_num
            if threading and FUTURES_MODULE:
                pool = ThreadPoolExecutor(max_workers=thread_num + 1)
                latest_block = 0
                for blocknum in range(start, head_block + 1, thread_num):
                    futures = []
                    i = blocknum
                    while i < blocknum + thread_num and i <= head_block:
                        futures.append(pool.submit(Block, i, steem_instance=self.steem))
                        i += 1
                    results = [r.result() for r in as_completed(futures)]
                    block_nums = []
                    for b in results:
                        block_nums.append(int(b.identifier))
                        if latest_block < int(b.identifier):
                            latest_block = int(b.identifier)
                    from operator import itemgetter
                    blocks = sorted(results, key=itemgetter('id'))
                    for b in blocks:
                        yield b
                if latest_block < head_block:
                    for blocknum in range(latest_block, head_block + 1):
                        block = Block(blocknum, steem_instance=self.steem)
                        yield block
            elif max_batch_size is not None and (head_block - start) >= max_batch_size:
                latest_block = start - 1
                batches = max_batch_size
                for blocknumblock in range(start, head_block + 1, batches):
                    # Get full block
                    if (head_block - blocknumblock) < batches:
                        batches = head_block - blocknumblock + 1
                    for blocknum in range(blocknumblock, blocknumblock + batches - 1):
                        if self.steem.rpc.get_use_appbase():
                            self.steem.rpc.get_block({"block_num": blocknum}, api="block", add_to_queue=True)
                        else:
                            self.steem.rpc.get_block(blocknum, add_to_queue=True)
                        latest_block = blocknum
                    if batches > 1:
                        latest_block += 1
                    if latest_block <= head_block:
                        if self.steem.rpc.get_use_appbase():
                            block_batch = self.steem.rpc.get_block({"block_num": latest_block}, api="block", add_to_queue=False)
                        else:
                            block_batch = self.steem.rpc.get_block(latest_block, add_to_queue=False)
                        blocknum = latest_block - len(block_batch) + 1
                        if not isinstance(block_batch, list):
                            block_batch = [block_batch]
                        for block in block_batch:
                            if self.steem.rpc.get_use_appbase():
                                block = block["block"]
                            block["id"] = blocknum
                            yield Block(block, steem_instance=self.steem)
                            blocknum += 1
            else:
                # Blocks from start until head block
                for blocknum in range(start, head_block + 1):
                    # Get full block
                    block = self.wait_for_and_get_block(blocknum, last_fetched_block_num=current_block_num)
                    yield block
            # Set new start
            start = head_block + 1

            if stop and start > stop:
                # raise StopIteration
                return

            # Sleep for one block
            time.sleep(self.block_interval)

    def wait_for_and_get_block(self, block_number, blocks_waiting_for=None, last_fetched_block_num=None):
        """ Get the desired block from the chain, if the current head block is smaller (for both head and irreversible)
            then we wait, but a maxmimum of blocks_waiting_for * max_block_wait_repetition time before failure.
            :param int block_number: desired block number
            :param int blocks_waiting_for: (default) difference between block_number and current head
                                           how many blocks we are willing to wait, positive int
        """
        if last_fetched_block_num is None or (last_fetched_block_num is not None and block_number > last_fetched_block_num):
            if not blocks_waiting_for:
                blocks_waiting_for = max(1, block_number - self.get_current_block_num())

            repetition = 0
            # can't return the block before the chain has reached it (support future block_num)
            while self.get_current_block_num() < block_number:
                repetition += 1
                time.sleep(self.block_interval)
                if repetition > blocks_waiting_for * self.max_block_wait_repetition:
                    raise Exception("Wait time for new block exceeded, aborting")
        # block has to be returned properly
        block = Block(block_number, steem_instance=self.steem)
        repetition = 0
        while not block:
            repetition += 1
            time.sleep(self.block_interval)
            if repetition > self.max_block_wait_repetition:
                raise Exception("Wait time for new block exceeded, aborting")
            block = Block(block_number, steem_instance=self.steem)
        return block

    def ops(self, start=None, stop=None, **kwargs):
        """ Yields all operations (including virtual operations) starting from
            ``start``.

            :param int start: Starting block
            :param int stop: Stop at this block
            :param str mode: We here have the choice between
             "head" (the last block) and "irreversible" (the block that is
             confirmed by 2/3 of all block producers and is thus irreversible)
            :param bool only_virtual_ops: Only yield virtual operations

            This call returns a list that only carries one operation and
            its type!
        """

        for block in self.blocks(start=start, stop=stop, **kwargs):
            for tx in block["transactions"]:
                for op in tx["operations"]:
                    # Replace opid by op name
                    # op[0] = getOperationNameForId(op[0])
                    yield {
                        "block_num": block.identifier,
                        "op": op,
                        "timestamp": block["timestamp"]
                    }

    def ops_statistics(self, start, stop=None, add_to_ops_stat=None, verbose=False):
        """ Generates a statistics for all operations (including virtual operations) starting from
            ``start``.

            :param int start: Starting block
            :param int stop: Stop at this block, if set to None, the current_block_num is taken
            :param dict add_to_ops_stat, if set, the result is added to add_to_ops_stat
            :param bool verbose, if True, the current block number and timestamp is printed
            This call returns a dict with all possible operations and their occurence.
        """
        if add_to_ops_stat is None:
            import beembase.operationids
            ops_stat = beembase.operationids.operations.copy()
            for key in ops_stat:
                ops_stat[key] = 0
        else:
            ops_stat = add_to_ops_stat.copy()
        current_block = self.get_current_block_num()
        if start > current_block:
            return
        if stop is None:
            stop = current_block
        for block in self.blocks(start=start, stop=stop):
            if verbose:
                print(block.identifier + " " + block["timestamp"])
            for tx in block["transactions"]:
                for op in tx["operations"]:
                    ops_stat[op[0]] += 1
        return ops_stat

    def stream(self, opNames=[], *args, **kwargs):
        """ Yield specific operations (e.g. comments) only

            :param array opNames: List of operations to filter for
            :param int start: Start at this block
            :param int stop: Stop at this block
            :param str mode: We here have the choice between
             "head" (the last block) and "irreversible" (the block that is
             confirmed by 2/3 of all block producers and is thus irreversible)

            The dict output is formated such that ``type`` caries the
            operation type, timestamp and block_num are taken from the
            block the operation was stored in and the other key depend
            on the actualy operation.
        """
        for op in self.ops(**kwargs):
            if not opNames or op["op"][0] in opNames:
                r = {
                    "type": op["op"][0],
                    "timestamp": op.get("timestamp"),
                    "block_num": op.get("block_num"),
                }
                r.update(op["op"][1])
                yield r

    def awaitTxConfirmation(self, transaction, limit=10):
        """ Returns the transaction as seen by the blockchain after being
            included into a block

            .. note:: If you want instant confirmation, you need to instantiate
                      class:`beem.blockchain.Blockchain` with
                      ``mode="head"``, otherwise, the call will wait until
                      confirmed in an irreversible block.

            .. note:: This method returns once the blockchain has included a
                      transaction with the **same signature**. Even though the
                      signature is not usually used to identify a transaction,
                      it still cannot be forfeited and is derived from the
                      transaction contented and thus identifies a transaction
                      uniquely.
        """
        counter = 10
        for block in self.blocks():
            counter += 1
            for tx in block["transactions"]:
                if sorted(
                    tx["signatures"]
                ) == sorted(transaction["signatures"]):
                    return tx
            if counter > limit:
                raise Exception(
                    "The operation has not been added after 10 blocks!")

    @staticmethod
    def hash_op(event):
        """ This method generates a hash of blockchain operation. """
        data = json.dumps(event, sort_keys=True)
        return hashlib.sha1(py23_bytes(data, 'utf-8')).hexdigest()

    def get_all_accounts(self, start='', stop='', steps=1e3, limit=-1, **kwargs):
        """ Yields account names between start and stop.

            :param str start: Start at this account name
            :param str stop: Stop at this account name
            :param int steps: Obtain ``steps`` ret with a single call from RPC
        """
        lastname = start
        cnt = 1
        while True:
            if self.steem.rpc.get_use_appbase():
                ret = self.steem.rpc.list_accounts({'start': lastname, 'limit': steps, 'order': 'by_name'}, api="database")["accounts"]
            else:
                ret = self.steem.rpc.lookup_accounts(lastname, steps)
            for account in ret:
                yield account
                cnt += 1
                if account == stop or (limit > 0 and cnt > limit):
                    raise StopIteration
            if lastname == ret[-1]:
                raise StopIteration
            lastname = ret[-1]
            if len(ret) < steps:
                raise StopIteration
