# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from .exceptions import BlockDoesNotExistsException
from .utils import parse_time
from .blockchainobject import BlockchainObject


class Block(BlockchainObject):
    """ Read a single block from the chain

        :param int block: block number
        :param beem.steem.Steem steem_instance: Steem
            instance
        :param bool lazy: Use lazy loading

        Instances of this class are dictionaries that come with additional
        methods (see below) that allow dealing with a block and it's
        corresponding functions.

        Additionally to the block data, the block number is stored as self["id"] or self.identifier.

        .. code-block:: python

            >>> from beem.block import Block
            >>> block = Block(1)
            >>> print(block)
            <Block 1>

        .. note:: This class comes with its own caching function to reduce the
                  load on the API server. Instances of this class can be
                  refreshed with ``Account.refresh()``.

    """

    def refresh(self):
        """ Even though blocks never change, you freshly obtain its contents
            from an API with this method
        """
        if not isinstance(self.identifier, int):
            self.identifier = int(self.identifier)
        if self.steem.rpc.get_use_appbase():
            block = self.steem.rpc.get_block({"block_num": self.identifier}, api="block")
            if block and "block" in block:
                block = block["block"]
        else:
            block = self.steem.rpc.get_block(self.identifier)
        if not block:
            raise BlockDoesNotExistsException(str(self.identifier))
        super(Block, self).__init__(block, steem_instance=self.steem)

    @property
    def block_num(self):
        """Returns the block number"""
        return self.identifier

    def time(self):
        """Return a datatime instance for the timestamp of this block"""
        return parse_time(self['timestamp'])

    def ops(self):
        """Returns all block operations"""
        ops = []
        trxs = self["transactions"]
        for tx in trxs:
            for op in tx["operations"]:
                # Replace opid by op name
                # op[0] = getOperationNameForId(op[0])
                ops.append(op)
        return ops

    def ops_statistics(self, add_to_ops_stat=None):
        """Retuns a statistic with the occurance of the different operation types"""
        if add_to_ops_stat is None:
            import beembase.operationids
            ops_stat = beembase.operationids.operations.copy()
            for key in ops_stat:
                ops_stat[key] = 0
        else:
            ops_stat = add_to_ops_stat.copy()
        trxs = self["transactions"]
        for tx in trxs:
            for op in tx["operations"]:
                ops_stat[op[0]] += 1
        return ops_stat


class BlockHeader(BlockchainObject):
    def refresh(self):
        """ Even though blocks never change, you freshly obtain its contents
            from an API with this method
        """
        if self.steem.rpc.get_use_appbase():
            block = self.steem.rpc.get_block_header({"block_num": self.identifier}, api="block")
            if "header" in block:
                block = block["header"]
        else:
            block = self.steem.rpc.get_block_header(self.identifier)
        if not block:
            raise BlockDoesNotExistsException(str(self.identifier))
        super(BlockHeader, self).__init__(
            block,
            steem_instance=self.steem
        )

    def time(self):
        """ Return a datatime instance for the timestamp of this block
        """
        return parse_time(self['timestamp'])

    @property
    def block_num(self):
        """Retuns the block number"""
        return self.identifier
