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
from .block import Block
from .blockchainobject import BlockchainObject
from beem.instance import shared_steem_instance
from beembase.operationids import getOperationNameForId
from .amount import Amount
from datetime import datetime
import math


@python_2_unicode_compatible
class Blockchain(object):
    """ This class allows to access the blockchain and read data
        from it

        :param beem.steem.Steem steem_instance: Steem
                 instance
        :param str mode: (default) Irreversible block (``irreversible``) or
                 actual head block (``head``)

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
        data_refresh_time_seconds=900,
    ):
        self.steem = steem_instance or shared_steem_instance()

        if mode == "irreversible":
            self.mode = 'last_irreversible_block_num'
        elif mode == "head":
            self.mode = "head_block_number"
        else:
            raise ValueError("invalid value for 'mode'!")

    def get_current_block_num(self):
        """ This call returns the current block number

            .. note:: The block number returned depends on the ``mode`` used
                      when instanciating from this class.
        """
        return self.steem.get_dynamic_global_properties(False).get(self.mode)

    def get_current_block(self):
        """ This call returns the current block

            .. note:: The block number returned depends on the ``mode`` used
                      when instanciating from this class.
        """
        return Block(
            self.get_current_block_num(),
            steem_instance=self.steem
        )

    def get_estimated_block_num(self, date, estimateForwards=False):
        """ This call estimates the block number based on a given date

            :param datetime date: block time for which a block number is estimated

            .. note:: The block number returned depends on the ``mode`` used
                      when instanciating from this class.
        """
        block_time_seconds = 3
        if estimateForwards:
            block_offset = 10
            first_block = Block(block_offset, steem_instance=self.steem)
            time_diff = date - first_block.time()
            return math.floor(time_diff.total_seconds() / block_time_seconds + block_offset.identifier)
        else:
            last_block = self.get_current_block()
            time_diff = last_block.time() - date
            block_number = math.floor(last_block.identifier - time_diff.total_seconds() / block_time_seconds)
            return block_number

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
        return int(Block(
            block_num,
            steem_instance=self.steem
        ).time().timestamp())

    def blocks(self, start=None, stop=None):
        """ Yields blocks starting from ``start``.

            :param int start: Starting block
            :param int stop: Stop at this block
            :param str mode: We here have the choice between
             "head" (the last block) and "irreversible" (the block that is
             confirmed by 2/3 of all block producers and is thus irreversible)
        """
        # Let's find out how often blocks are generated!
        block_interval = self.steem.get_config().get("STEEMIT_BLOCK_INTERVAL")

        if not start:
            start = self.get_current_block_num()

        # We are going to loop indefinitely
        while True:

            # Get chain properies to identify the
            if stop:
                head_block = stop
            else:
                head_block = self.get_current_block_num()

            # Blocks from start until head block
            for blocknum in range(start, head_block + 1):
                # Get full block
                block = self.steem.rpc.get_block(blocknum)
                block.update({"block_num": blocknum})
                yield block
            # Set new start
            start = head_block + 1

            if stop and start > stop:
                # raise StopIteration
                return

            # Sleep for one block
            time.sleep(block_interval)

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
                        "block_num": block["block_num"],
                        "op": op,
                        "timestamp": block["timestamp"]
                    }

    def ops_statistics(self, start, stop=None, add_to_ops_stat=None, verbose=True):
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
                print(str(block["block_num"]) + " " + block["timestamp"])
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

    def get_all_accounts(self, start='', stop='', steps=1e3, **kwargs):
        """ Yields account names between start and stop.

            :param str start: Start at this account name
            :param str stop: Stop at this account name
            :param int steps: Obtain ``steps`` ret with a single call from RPC
        """
        lastname = start
        while True:
            ret = self.steem.rpc.lookup_accounts(lastname, steps)
            for account in ret:
                yield account
                if account == stop:
                    raise StopIteration
            if lastname == ret[-1]:
                raise StopIteration
            lastname = ret[-1]
            if len(ret) < steps:
                raise StopIteration
