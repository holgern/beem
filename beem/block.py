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

        .. code-block:: python

            from beem.block import Block
            block = Block(1)
            print(block["block"])
            print(block["id])

        .. note:: This class comes with its own caching function to reduce the
                  load on the API server. Instances of this class can be
                  refreshed with ``Account.refresh()``.

    """

    def refresh(self):
        """ Even though blocks never change, you freshly obtain its contents
            from an API with this method
        """
        if self.steem.rpc.get_use_appbase():
            block = self.steem.rpc.get_block({"block_num": self.identifier}, api="block")
        else:
            block = {'block': self.steem.rpc.get_block(self.identifier), 'id': str(self.identifier)}

        if not block or not block['block']:
            raise BlockDoesNotExistsException
        super(Block, self).__init__(block, steem_instance=self.steem)

    @property
    def block(self):
        """ Returns the block data
        """
        return self["block"]

    @property
    def id(self):
        """ Returns the block id
        """
        return int(self["id"])

    def time(self):
        """ Return a datatime instance for the timestamp of this block
        """
        return parse_time(self['block']['timestamp'])

    def ops(self):
        ops = []
        trxs = self["block"]["transactions"]
        for tx in trxs:
            for op in tx["operations"]:
                # Replace opid by op name
                # op[0] = getOperationNameForId(op[0])
                ops.append(op)
        return ops

    def ops_statistics(self, add_to_ops_stat=None):
        if add_to_ops_stat is None:
            import beembase.operationids
            ops_stat = beembase.operationids.operations.copy()
            for key in ops_stat:
                ops_stat[key] = 0
        else:
            ops_stat = add_to_ops_stat.copy()
        trxs = self["block"]["transactions"]
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
        else:
            block = {'header': self.steem.rpc.get_block_header(self.identifier), 'id': str(self.identifier)}
        if not block or not block['header']:
            raise BlockDoesNotExistsException
        super(BlockHeader, self).__init__(
            block,
            steem_instance=self.steem
        )

    def time(self):
        """ Return a datatime instance for the timestamp of this block
        """
        return parse_time(self['header']['timestamp'])

    @property
    def header(self):
        """ Returns the block header
        """
        return self["header"]

    @property
    def id(self):
        """ Returns the block id
        """
        return int(self["id"])
