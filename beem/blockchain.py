# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.utils import python_2_unicode_compatible
from builtins import str
from builtins import range
from builtins import object
import sys
import time
import hashlib
import json
import math
from threading import Thread, Event
from time import sleep
import logging
from datetime import datetime, timedelta
from .utils import formatTimeString, addTzInfo
from .block import Block
from .exceptions import BatchedCallsNotSupported, BlockDoesNotExistsException, BlockWaitTimeExceeded, OfflineHasNoRPCException
from beemapi.exceptions import NumRetriesReached
from beemgraphenebase.py23 import py23_bytes
from beem.instance import shared_steem_instance
from .amount import Amount
log = logging.getLogger(__name__)
if sys.version_info < (3, 0):
    from Queue import Queue
else:
    from queue import Queue


# default exception handler. if you want to take some action on failed tasks
# maybe add the task back into the queue, then make your own handler and pass it in
def default_handler(name, exception, *args, **kwargs):
    print('%s raised %s with args %s and kwargs %s' % (name, str(exception), repr(args), repr(kwargs)))
    pass


class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, name, queue, results, abort, idle, exception_handler):
        Thread.__init__(self)
        self.name = name
        self.queue = queue
        self.results = results
        self.abort = abort
        self.idle = idle
        self.exception_handler = exception_handler
        self.daemon = True
        self.start()

    def run(self):
        """Thread work loop calling the function with the params"""
        # keep running until told to abort
        while not self.abort.is_set():
            try:
                # get a task and raise immediately if none available
                func, args, kwargs = self.queue.get(False)
                self.idle.clear()
            except:
                # no work to do
                # if not self.idle.is_set():
                #  print >> stdout, '%s is idle' % self.name
                self.idle.set()
                continue

            try:
                # the function may raise
                result = func(*args, **kwargs)
                # print(result)
                if(result is not None):
                    self.results.put(result)
            except Exception as e:
                # so we move on and handle it in whatever way the caller wanted
                self.exception_handler(self.name, e, args, kwargs)
            finally:
                # task complete no matter what happened
                self.queue.task_done()


# class for thread pool
class Pool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, thread_count, batch_mode=True, exception_handler=default_handler):
        # batch mode means block when adding tasks if no threads available to process
        self.queue = Queue(thread_count if batch_mode else 0)
        self.resultQueue = Queue(0)
        self.thread_count = thread_count
        self.exception_handler = exception_handler
        self.aborts = []
        self.idles = []
        self.threads = []

    def __del__(self):
        """Tell my threads to quit"""
        self.abort()

    def run(self, block=False):
        """Start the threads, or restart them if you've aborted"""
        # either wait for them to finish or return false if some arent
        if block:
            while self.alive():
                sleep(1)
        elif self.alive():
            return False

        # go start them
        self.aborts = []
        self.idles = []
        self.threads = []
        for n in range(self.thread_count):
            abort = Event()
            idle = Event()
            self.aborts.append(abort)
            self.idles.append(idle)
            self.threads.append(Worker('thread-%d' % n, self.queue, self.resultQueue, abort, idle, self.exception_handler))
        return True

    def enqueue(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.queue.put((func, args, kargs))

    def join(self):
        """Wait for completion of all the tasks in the queue"""
        self.queue.join()

    def abort(self, block=False):
        """Tell each worker that its done working"""
        # tell the threads to stop after they are done with what they are currently doing
        for a in self.aborts:
            a.set()
        # wait for them to finish if requested
        while block and self.alive():
            sleep(1)

    def alive(self):
        """Returns True if any threads are currently running"""
        return True in [t.is_alive() for t in self.threads]

    def idle(self):
        """Returns True if all threads are waiting for work"""
        return False not in [i.is_set() for i in self.idles]

    def done(self):
        """Returns True if not tasks are left to be completed"""
        return self.queue.empty()

    def results(self, sleep_time=0):
        """Get the set of results that have been processed, repeatedly call until done"""
        sleep(sleep_time)
        results = []
        try:
            while True:
                # get a result, raises empty exception immediately if none available
                results.append(self.resultQueue.get(False))
                self.resultQueue.task_done()
        except:
            return results
        return results


@python_2_unicode_compatible
class Blockchain(object):
    """ This class allows to access the blockchain and read data
        from it

        :param beem.steem.Steem steem_instance: Steem instance
        :param str mode: (default) Irreversible block (``irreversible``) or
            actual head block (``head``)
        :param int max_block_wait_repetition: maximum wait repetition for next block
            where each repetition is block_interval long (default is 3)

        This class let's you deal with blockchain related data and methods.
        Read blockchain related data:

        .. testsetup::

            from beem.blockchain import Blockchain
            chain = Blockchain()

        Read current block and blockchain info

        .. testcode::

            print(chain.get_current_block())
            print(chain.steem.info())

        Monitor for new blocks. When ``stop`` is not set, monitoring will never stop.

        .. testcode::

            blocks = []
            current_num = chain.get_current_block_num()
            for block in chain.blocks(start=current_num - 99, stop=current_num):
                blocks.append(block)
            len(blocks)

        .. testoutput::

            100

        or each operation individually:

        .. testcode::

            ops = []
            current_num = chain.get_current_block_num()
            for operation in chain.ops(start=current_num - 99, stop=current_num):
                ops.append(operation)

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
        self.block_interval = self.steem.get_block_interval()

    def is_irreversible_mode(self):
        return self.mode == 'last_irreversible_block_num'

    def get_transaction(self, transaction_id):
        """ Returns a transaction from the blockchain

            :param str transaction_id: transaction_id
        """
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            ret = self.steem.rpc.get_transaction({'id': transaction_id}, api="database")
        else:
            ret = self.steem.rpc.get_transaction(transaction_id, api="database")
        return ret

    def get_current_block_num(self):
        """ This call returns the current block number

            .. note:: The block number returned depends on the ``mode`` used
                      when instantiating from this class.
        """
        props = self.steem.get_dynamic_global_properties(False)
        if props is None:
            raise ValueError("Could not receive dynamic_global_properties!")
        if self.mode not in props:
            raise ValueError(self.mode + " is not in " + props)
        return int(props.get(self.mode))

    def get_current_block(self, only_ops=False, only_virtual_ops=False):
        """ This call returns the current block

            :param bool only_ops: Returns block with operations only, when set to True (default: False)
            :param bool only_virtual_ops: Includes only virtual operations (default: False)

            .. note:: The block number returned depends on the ``mode`` used
                      when instantiating from this class.
        """
        return Block(
            self.get_current_block_num(),
            only_ops=only_ops,
            only_virtual_ops=only_virtual_ops,
            steem_instance=self.steem
        )

    def get_estimated_block_num(self, date, estimateForwards=False, accurate=True):
        """ This call estimates the block number based on a given date

            :param datetime date: block time for which a block number is estimated

            .. note:: The block number returned depends on the ``mode`` used
                      when instantiating from this class.
        """
        last_block = self.get_current_block()
        date = addTzInfo(date)
        if estimateForwards:
            block_offset = 10
            first_block = Block(block_offset, steem_instance=self.steem)
            time_diff = date - first_block.time()
            block_number = math.floor(time_diff.total_seconds() / self.block_interval + block_offset)
        else:
            time_diff = last_block.time() - date
            block_number = math.floor(last_block.identifier - time_diff.total_seconds() / self.block_interval)
        if block_number < 1:
            block_number = 1

        if accurate:
            if block_number > last_block.identifier:
                block_number = last_block.identifier
            block_time_diff = timedelta(seconds=10)
            while block_time_diff.total_seconds() > self.block_interval or block_time_diff.total_seconds() < -self.block_interval:
                block = Block(block_number, steem_instance=self.steem)
                block_time_diff = date - block.time()
                delta = block_time_diff.total_seconds() // self.block_interval
                if delta == 0 and block_time_diff.total_seconds() < 0:
                    delta = -1
                elif delta == 0 and block_time_diff.total_seconds() > 0:
                    delta = 1
                block_number += delta
                if block_number < 1:
                    break
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
            number as integer.

            :param int block_num: Block number
        """
        block_time = Block(
            block_num,
            steem_instance=self.steem
        ).time()
        return int(time.mktime(block_time.timetuple()))

    def blocks(self, start=None, stop=None, max_batch_size=None, threading=False, thread_num=8, only_ops=False, only_virtual_ops=False):
        """ Yields blocks starting from ``start``.

            :param int start: Starting block
            :param int stop: Stop at this block
            :param int max_batch_size: only for appbase nodes. When not None, batch calls of are used.
                Cannot be combined with threading
            :param bool threading: Enables threading. Cannot be combined with batch calls
            :param int thread_num: Defines the number of threads, when `threading` is set.
            :param bool only_ops: Only yield operations (default: False).
                Cannot be combined with ``only_virtual_ops=True``.
            :param bool only_virtual_ops: Only yield virtual operations (default: False)

            .. note:: If you want instant confirmation, you need to instantiate
                      class:`beem.blockchain.Blockchain` with
                      ``mode="head"``, otherwise, the call will wait until
                      confirmed in an irreversible block.

        """
        # Let's find out how often blocks are generated!
        current_block = self.get_current_block()
        current_block_num = current_block.block_num
        if not start:
            start = current_block_num
        head_block_reached = False
        if threading:
            # pool = ThreadPoolExecutor(max_workers=thread_num + 1)
            pool = Pool(thread_num, batch_mode=True)
        # We are going to loop indefinitely
        while True:

            # Get chain properies to identify the
            if stop:
                head_block = stop
            else:
                current_block_num = self.get_current_block_num()
                head_block = current_block_num
            if threading and not head_block_reached:
                # disable autoclean
                auto_clean = current_block.get_cache_auto_clean()
                latest_block = start - 1
                result_block_nums = []
                for blocknum in range(start, head_block + 1, thread_num):
                    # futures = []
                    i = 0
                    results = []
                    block_num_list = []
                    current_block.set_cache_auto_clean(False)
                    while i < thread_num and blocknum + i <= head_block:
                        block_num_list.append(blocknum + i)
                        pool.enqueue(Block, blocknum + i, only_ops=only_ops, only_virtual_ops=only_virtual_ops, steem_instance=self.steem)
                        i += 1
                    pool.run(True)
                    pool.join()
                    for result in pool.results():
                        results.append(result)
                    pool.abort()
                    current_block.clear_cache_from_expired_items()
                    current_block.set_cache_auto_clean(auto_clean)
                    from operator import itemgetter
                    blocks = sorted(results, key=itemgetter('id'))
                    for b in blocks:
                        if latest_block < int(b.identifier):
                            latest_block = int(b.identifier)
                        yield b

                if latest_block <= head_block:
                    for blocknum in range(latest_block + 1, head_block + 1):
                        if blocknum not in result_block_nums:
                            block = Block(blocknum, only_ops=only_ops, only_virtual_ops=only_virtual_ops, steem_instance=self.steem)
                            result_block_nums.append(blocknum)
                            yield block
                current_block.set_cache_auto_clean(auto_clean)
            elif max_batch_size is not None and (head_block - start) >= max_batch_size and not head_block_reached:
                if not self.steem.is_connected():
                    raise OfflineHasNoRPCException("No RPC available in offline mode!")
                self.steem.rpc.set_next_node_on_empty_reply(False)
                latest_block = start - 1
                batches = max_batch_size
                for blocknumblock in range(start, head_block + 1, batches):
                    # Get full block
                    if (head_block - blocknumblock) < batches:
                        batches = head_block - blocknumblock + 1
                    for blocknum in range(blocknumblock, blocknumblock + batches - 1):
                        if only_virtual_ops:
                            if self.steem.rpc.get_use_appbase():
                                # self.steem.rpc.get_ops_in_block({"block_num": blocknum, 'only_virtual': only_virtual_ops}, api="account_history", add_to_queue=True)
                                self.steem.rpc.get_ops_in_block(blocknum, only_virtual_ops, add_to_queue=True)
                            else:
                                self.steem.rpc.get_ops_in_block(blocknum, only_virtual_ops, add_to_queue=True)
                        else:
                            if self.steem.rpc.get_use_appbase():
                                self.steem.rpc.get_block({"block_num": blocknum}, api="block", add_to_queue=True)
                            else:
                                self.steem.rpc.get_block(blocknum, add_to_queue=True)
                        latest_block = blocknum
                    if batches >= 1:
                        latest_block += 1
                    if latest_block <= head_block:
                        if only_virtual_ops:
                            if self.steem.rpc.get_use_appbase():
                                # self.steem.rpc.get_ops_in_block({"block_num": blocknum, 'only_virtual': only_virtual_ops}, api="account_history", add_to_queue=False)
                                block_batch = self.steem.rpc.get_ops_in_block(blocknum, only_virtual_ops, add_to_queue=False)
                            else:
                                block_batch = self.steem.rpc.get_ops_in_block(blocknum, only_virtual_ops, add_to_queue=False)
                        else:
                            if self.steem.rpc.get_use_appbase():
                                block_batch = self.steem.rpc.get_block({"block_num": latest_block}, api="block", add_to_queue=False)
                            else:
                                block_batch = self.steem.rpc.get_block(latest_block, add_to_queue=False)
                        if not bool(block_batch):
                            raise BatchedCallsNotSupported()
                        blocknum = latest_block - len(block_batch) + 1
                        if not isinstance(block_batch, list):
                            block_batch = [block_batch]
                        for block in block_batch:
                            if self.steem.rpc.get_use_appbase():
                                if only_virtual_ops:
                                    block = block["ops"]
                                else:
                                    block = block["block"]
                            block["id"] = blocknum
                            yield Block(block, only_ops=only_ops, only_virtual_ops=only_virtual_ops, steem_instance=self.steem)
                            blocknum += 1
            else:
                # Blocks from start until head block
                for blocknum in range(start, head_block + 1):
                    # Get full block
                    block = self.wait_for_and_get_block(blocknum, only_ops=only_ops, only_virtual_ops=only_virtual_ops)
                    yield block
            # Set new start
            start = head_block + 1
            head_block_reached = True

            if stop and start > stop:
                # raise StopIteration
                return

            # Sleep for one block
            time.sleep(self.block_interval)

    def wait_for_and_get_block(self, block_number, blocks_waiting_for=None, only_ops=False, only_virtual_ops=False):
        """ Get the desired block from the chain, if the current head block is smaller (for both head and irreversible)
            then we wait, but a maxmimum of blocks_waiting_for * max_block_wait_repetition time before failure.

            :param int block_number: desired block number
            :param int blocks_waiting_for: difference between block_number and current head and defines
                how many blocks we are willing to wait, positive int (default: None)
            :param bool only_ops: Returns blocks with operations only, when set to True (default: False)
            :param bool only_virtual_ops: Includes only virtual operations (default: False)

        """
        if not blocks_waiting_for:
            blocks_waiting_for = max(
                1, block_number - self.get_current_block_num())

            repetition = 0
            # can't return the block before the chain has reached it (support future block_num)
            while self.get_current_block_num() < block_number:
                repetition += 1
                time.sleep(self.block_interval)
                if repetition > blocks_waiting_for * self.max_block_wait_repetition:
                    raise BlockWaitTimeExceeded("Already waited %d s" % (blocks_waiting_for * self.max_block_wait_repetition * self.block_interval))
        # block has to be returned properly
        repetition = 0
        block = None
        while not block:
            try:
                block = Block(block_number, only_ops=only_ops, only_virtual_ops=only_virtual_ops, steem_instance=self.steem)
            except BlockDoesNotExistsException:
                block = None
                if repetition > blocks_waiting_for * self.max_block_wait_repetition:
                    raise BlockWaitTimeExceeded("Already waited %d s" % (blocks_waiting_for * self.max_block_wait_repetition * self.block_interval))
                repetition += 1
                time.sleep(self.block_interval)

        return block

    def ops(self, start=None, stop=None, only_virtual_ops=False, **kwargs):
        """ Blockchain.ops() is deprecated. Please use Blockchain.stream() instead.
        """
        raise DeprecationWarning('Blockchain.ops() is deprecated. Please use Blockchain.stream() instead.')

    def ops_statistics(self, start, stop=None, add_to_ops_stat=None, with_virtual_ops=True, verbose=False):
        """ Generates statistics for all operations (including virtual operations) starting from
            ``start``.

            :param int start: Starting block
            :param int stop: Stop at this block, if set to None, the current_block_num is taken
            :param dict add_to_ops_stat: if set, the result is added to add_to_ops_stat
            :param bool verbose: if True, the current block number and timestamp is printed

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
        for block in self.blocks(start=start, stop=stop, only_ops=False, only_virtual_ops=False):
            if verbose:
                print(block["identifier"] + " " + block["timestamp"])
            ops_stat = block.ops_statistics(add_to_ops_stat=ops_stat)
        if with_virtual_ops:
            for block in self.blocks(start=start, stop=stop, only_ops=True, only_virtual_ops=True):
                if verbose:
                    print(block["identifier"] + " " + block["timestamp"])
                ops_stat = block.ops_statistics(add_to_ops_stat=ops_stat)
        return ops_stat

    def stream(self, opNames=[], raw_ops=False, *args, **kwargs):
        """ Yield specific operations (e.g. comments) only

            :param array opNames: List of operations to filter for
            :param bool raw_ops: When set to True, it returns the unmodified operations (default: False)
            :param int start: Start at this block
            :param int stop: Stop at this block
            :param int max_batch_size: only for appbase nodes. When not None, batch calls of are used.
                Cannot be combined with threading
            :param bool threading: Enables threading. Cannot be combined with batch calls
            :param int thread_num: Defines the number of threads, when `threading` is set.
            :param bool only_ops: Only yield operations (default: False)
                Cannot be combined with ``only_virtual_ops=True``
            :param bool only_virtual_ops: Only yield virtual operations (default: False)

            The dict output is formated such that ``type`` carries the
            operation type. Timestamp and block_num are taken from the
            block the operation was stored in and the other keys depend
            on the actualy operation.

            .. note:: If you want instant confirmation, you need to instantiate
                      class:`beem.blockchain.Blockchain` with
                      ``mode="head"``, otherwise, the call will wait until
                      confirmed in an irreversible block.

            output when `raw_ops=False` is set:
            .. code-block:: js

                {
                    'type': 'transfer',
                    'from': 'johngreenfield',
                    'to': 'thundercurator',
                    'amount': '0.080 SBD',
                    'memo': 'https://steemit.com/lofi/@johngreenfield/lofi-joji-yeah-right',
                    '_id': '6d4c5f2d4d8ef1918acaee4a8dce34f9da384786',
                    'timestamp': datetime.datetime(2018, 5, 9, 11, 23, 6, tzinfo=<UTC>),
                    'block_num': 22277588, 'trx_id': 'cf11b2ac8493c71063ec121b2e8517ab1e0e6bea'
                }

            output when `raw_ops=True` is set:
            .. code-block:: js

                {
                    'block_num': 22277588,
                    'op':
                        [
                            'transfer',
                                {
                                    'from': 'johngreenfield', 'to': 'thundercurator',
                                    'amount': '0.080 SBD',
                                    'memo': 'https://steemit.com/lofi/@johngreenfield/lofi-joji-yeah-right'
                                }
                        ],
                        'timestamp': datetime.datetime(2018, 5, 9, 11, 23, 6, tzinfo=<UTC>)
                }

        """
        for block in self.blocks(**kwargs):
            if "transactions" in block:
                trx = block["transactions"]
            else:
                trx = [block]
            for trx_nr in range(len(trx)):
                for event in trx[trx_nr]["operations"]:
                    if isinstance(event, list):
                        op_type, op = event
                        trx_id = block["transaction_ids"][trx_nr]
                        block_num = block.get("id")
                        _id = self.hash_op(event)
                        timestamp = block.get("timestamp")
                    elif isinstance(event, dict) and "type" in event and "value" in event:
                        op_type = event["type"]
                        if len(op_type) > 10 and op_type[len(op_type) - 10:] == "_operation":
                            op_type = op_type[:-10]
                        op = event["value"]
                        trx_id = block["transaction_ids"][trx_nr]
                        block_num = block.get("id")
                        _id = self.hash_op(event)
                        timestamp = block.get("timestamp")
                    else:
                        op_type, op = event["op"]
                        trx_id = event.get("trx_id")
                        block_num = event.get("block")
                        _id = self.hash_op(event["op"])
                        timestamp = event.get("timestamp")
                    if not opNames or op_type in opNames:
                        if raw_ops:
                            yield {"block_num": block_num,
                                   "op": [op_type, op],
                                   "timestamp": timestamp}
                        else:
                            updated_op = {"type": op_type}
                            updated_op.update(op.copy())
                            updated_op.update({"_id": _id,
                                               "timestamp": timestamp,
                                               "block_num": block_num,
                                               "trx_id": trx_id})
                            yield updated_op

    def awaitTxConfirmation(self, transaction, limit=10):
        """ Returns the transaction as seen by the blockchain after being
            included into a block
            :param dict transaction: transaction to wait for
            :param int limit: (optional) number of blocks to wait for the transaction (default: 10)

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
        counter = 0
        for block in self.blocks():
            counter += 1
            for tx in block["transactions"]:
                if sorted(
                    tx["signatures"]
                ) == sorted(transaction["signatures"]):
                    return tx
            if counter > limit:
                raise Exception(
                    "The operation has not been added after %d blocks!" % (limit))

    @staticmethod
    def hash_op(event):
        """ This method generates a hash of blockchain operation. """
        if isinstance(event, dict) and "type" in event and "value" in event:
            op_type = event["type"]
            if len(op_type) > 10 and op_type[len(op_type) - 10:] == "_operation":
                op_type = op_type[:-10]
            op = event["value"]
            event = [op_type, op]
        data = json.dumps(event, sort_keys=True)
        return hashlib.sha1(py23_bytes(data, 'utf-8')).hexdigest()

    def get_all_accounts(self, start='', stop='', steps=1e3, limit=-1, **kwargs):
        """ Yields account names between start and stop.

            :param str start: Start at this account name
            :param str stop: Stop at this account name
            :param int steps: Obtain ``steps`` ret with a single call from RPC
        """
        cnt = 1
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        if self.steem.rpc.get_use_appbase() and start == "":
            lastname = None
        else:
            lastname = start
        self.steem.rpc.set_next_node_on_empty_reply(False)
        while True:
            if self.steem.rpc.get_use_appbase():
                ret = self.steem.rpc.list_accounts({'start': lastname, 'limit': steps, 'order': 'by_name'}, api="database")["accounts"]
            else:
                ret = self.steem.rpc.lookup_accounts(lastname, steps)
            for account in ret:
                if isinstance(account, dict):
                    account_name = account["name"]
                else:
                    account_name = account
                if account_name != lastname:
                    yield account_name
                    cnt += 1
                    if account_name == stop or (limit > 0 and cnt > limit):
                        raise StopIteration
            if lastname == account_name:
                raise StopIteration
            lastname = account_name
            if len(ret) < steps:
                raise StopIteration

    def get_account_count(self):
        """ Returns the number of accounts"""
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            ret = self.steem.rpc.get_account_count(api="condenser")
        else:
            ret = self.steem.rpc.get_account_count()
        return ret

    def get_account_reputations(self, start='', stop='', steps=1e3, limit=-1, **kwargs):
        """ Yields account reputation between start and stop.

            :param str start: Start at this account name
            :param str stop: Stop at this account name
            :param int steps: Obtain ``steps`` ret with a single call from RPC
        """
        cnt = 1
        if not self.steem.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        if self.steem.rpc.get_use_appbase() and start == "":
            lastname = None
        else:
            lastname = start
        self.steem.rpc.set_next_node_on_empty_reply(False)
        while True:
            if self.steem.rpc.get_use_appbase():
                ret = self.steem.rpc.get_account_reputations({'account_lower_bound': lastname, 'limit': steps}, api="follow")["reputations"]
            else:
                ret = self.steem.rpc.get_account_reputations(lastname, steps, api="follow")
            for account in ret:
                if isinstance(account, dict):
                    account_name = account["account"]
                else:
                    account_name = account
                if account_name != lastname:
                    yield account
                    cnt += 1
                    if account_name == stop or (limit > 0 and cnt > limit):
                        raise StopIteration
            if lastname == account_name:
                raise StopIteration
            lastname = account_name
            if len(ret) < steps:
                raise StopIteration
