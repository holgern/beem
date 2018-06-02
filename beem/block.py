# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from .exceptions import BlockDoesNotExistsException
from .utils import parse_time
from .blockchainobject import BlockchainObject
from beemapi.exceptions import ApiNotSupported


class Block(BlockchainObject):
    """ Read a single block from the chain

        :param int block: block number
        :param beem.steem.Steem steem_instance: Steem
            instance
        :param bool lazy: Use lazy loading
        :param bool only_ops: Includes only operations, when set to True (default: False)
        :param bool only_virtual_ops: Includes only virtual operations (default: False)

        Instances of this class are dictionaries that come with additional
        methods (see below) that allow dealing with a block and it's
        corresponding functions.

        When only_virtual_ops is set to True, only_ops is always set to True.

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
    def __init__(
        self,
        block,
        only_ops=False,
        only_virtual_ops=False,
        full=True,
        lazy=False,
        steem_instance=None
    ):
        """ Initilize a block

            :param int block: block number
            :param beem.steem.Steem steem_instance: Steem
                instance
            :param bool lazy: Use lazy loading
            :param bool only_ops: Includes only operations, when set to True (default: False)
            :param bool only_virtual_ops: Includes only virtual operations (default: False)

        """
        self.full = full
        self.only_ops = only_ops
        self.only_virtual_ops = only_virtual_ops
        super(Block, self).__init__(
            block,
            lazy=lazy,
            full=full,
            steem_instance=steem_instance
        )

    def refresh(self):
        """ Even though blocks never change, you freshly obtain its contents
            from an API with this method
        """
        if not isinstance(self.identifier, int):
            self.identifier = int(self.identifier)
        if not self.steem.is_connected():
            return None
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.only_ops or self.only_virtual_ops:
            if self.steem.rpc.get_use_appbase():
                try:
                    ops = self.steem.rpc.get_ops_in_block({"block_num": self.identifier, 'only_virtual': self.only_virtual_ops}, api="account_history")["ops"]
                except ApiNotSupported:
                    ops = self.steem.rpc.get_ops_in_block(self.identifier, self.only_virtual_ops)
            else:
                ops = self.steem.rpc.get_ops_in_block(self.identifier, self.only_virtual_ops)
            block = {'block': ops[0]["block"],
                     'timestamp': ops[0]["timestamp"],
                     'operations': ops}
        else:
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

    @property
    def transactions(self):
        """ Returns all transactions as list"""
        if self.only_ops or self.only_virtual_ops:
            return list()
        trxs = self["transactions"]
        for i in range(len(trxs)):
            trx = trxs[i]
            trx['transaction_id'] = self['transaction_ids'][i]
            trx['block_num'] = self.block_num
            trx['transaction_num'] = i
            trxs[i] = trx
        return trxs

    @property
    def operations(self):
        """Returns all block operations as list"""
        if self.only_ops or self.only_virtual_ops:
            return self["operations"]
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
        if self.only_ops or self.only_virtual_ops:
            for op in self["operations"]:
                ops_stat[op["op"][0]] += 1
            return ops_stat
        trxs = self["transactions"]
        for tx in trxs:
            for op in tx["operations"]:
                if isinstance(op, dict) and 'type' in op:
                    op_type = op["type"]
                    if len(op_type) > 10 and op_type[len(op_type) - 10:] == "_operation":
                        op_type = op_type[:-10]
                    ops_stat[op_type] += 1
                else:
                    ops_stat[op[0]] += 1
        return ops_stat


class BlockHeader(BlockchainObject):
    def refresh(self):
        """ Even though blocks never change, you freshly obtain its contents
            from an API with this method
        """
        if not self.steem.is_connected():
            return None
        self.steem.rpc.set_next_node_on_empty_reply(False)
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
