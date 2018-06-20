# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from datetime import datetime, timedelta, date
import json
from .exceptions import BlockDoesNotExistsException
from .utils import parse_time, formatTimeString
from .blockchainobject import BlockchainObject
from beemapi.exceptions import ApiNotSupported
from beemgraphenebase.py23 import bytes_types, integer_types, string_types, text_type


class Block(BlockchainObject):
    """ Read a single block from the chain

        :param int block: block number
        :param beem.steem.Steem steem_instance: Steem
            instance
        :param bool lazy: Use lazy loading
        :param bool only_ops: Includes only operations, when set to True (default: False)
        :param bool only_virtual_ops: Includes only virtual operations (default: False)

        Instances of this class are dictionaries that come with additional
        methods (see below) that allow dealing with a block and its
        corresponding functions.

        When only_virtual_ops is set to True, only_ops is always set to True.

        In addition to the block data, the block number is stored as self["id"] or self.identifier.

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
        self.lazy = lazy
        self.only_ops = only_ops
        self.only_virtual_ops = only_virtual_ops
        if isinstance(block, float):
            block = int(block)
        elif isinstance(block, dict):
            block = self._parse_json_data(block)
        super(Block, self).__init__(
            block,
            lazy=lazy,
            full=full,
            steem_instance=steem_instance
        )

    def _parse_json_data(self, block):
        parse_times = [
            "timestamp",
        ]
        for p in parse_times:
            if p in block and isinstance(block.get(p), string_types):
                block[p] = formatTimeString(block.get(p, "1970-01-01T00:00:00"))
        if "transactions" in block:
            for i in range(len(block["transactions"])):
                if 'expiration' in block["transactions"][i] and isinstance(block["transactions"][i]["expiration"], string_types):
                    block["transactions"][i]["expiration"] = formatTimeString(block["transactions"][i]["expiration"])
        elif "operations" in block:
            for i in range(len(block["operations"])):
                if 'timestamp' in block["operations"][i]  and isinstance(block["operations"][i]["timestamp"], string_types):
                    block["operations"][i]["timestamp"] = formatTimeString(block["operations"][i]["timestamp"])
        return block

    def json(self):
        output = self.copy()
        parse_times = [
            "timestamp",
        ]
        for p in parse_times:
            if p in output:
                p_date = output.get(p, datetime(1970, 1, 1, 0, 0))
                if isinstance(p_date, (datetime, date)):
                    output[p] = formatTimeString(p_date)
                else:
                    output[p] = p_date

        if "transactions" in output:
            for i in range(len(output["transactions"])):
                if 'expiration' in output["transactions"][i] and isinstance(output["transactions"][i]["expiration"], (datetime, date)):
                    output["transactions"][i]["expiration"] = formatTimeString(output["transactions"][i]["expiration"])
        elif "operations" in output:
            for i in range(len(output["operations"])):
                if 'timestamp' in output["operations"][i]  and isinstance(output["operations"][i]["timestamp"], (datetime, date)):
                    output["operations"][i]["timestamp"] = formatTimeString(output["operations"][i]["timestamp"])

        ret = json.loads(str(json.dumps(output)))
        output = self._parse_json_data(output)
        return ret

    def refresh(self):
        """ Even though blocks never change, you freshly obtain its contents
            from an API with this method
        """
        if self.identifier is None and "id" in self:
            self.identifier = self["id"]
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
            if bool(ops):
                block = {'block': ops[0]["block"],
                         'timestamp': ops[0]["timestamp"],
                         'operations': ops}
            else:
                block = {}
        else:
            if self.steem.rpc.get_use_appbase():
                block = self.steem.rpc.get_block({"block_num": self.identifier}, api="block")
                if block and "block" in block:
                    block = block["block"]
            else:
                block = self.steem.rpc.get_block(self.identifier)
        if not block:
            raise BlockDoesNotExistsException(str(self.identifier))
        block = self._parse_json_data(block)
        block["id"] = self.identifier
        super(Block, self).__init__(block, lazy=self.lazy, full=self.full, steem_instance=self.steem)

    @property
    def block_num(self):
        """Returns the block number"""
        return self.identifier

    def time(self):
        """Return a datatime instance for the timestamp of this block"""
        return self['timestamp']

    @property
    def transactions(self):
        """ Returns all transactions as list"""
        if self.only_ops or self.only_virtual_ops:
            return list()
        trxs = []
        i = 0
        for trx in self["transactions"]:
            trx_new = trx.copy()
            trx_new['transaction_id'] = self['transaction_ids'][i]
            trx_new['block_num'] = self.block_num
            trx_new['transaction_num'] = i
            trxs.append(trx_new)
            i += 1
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

    @property
    def json_transactions(self):
        """ Returns all transactions as list, all dates are strings."""
        if self.only_ops or self.only_virtual_ops:
            return list()
        trxs = []
        i = 0
        for trx in self["transactions"]:
            trx_new = trx.copy()
            trx_new['transaction_id'] = self['transaction_ids'][i]
            trx_new['block_num'] = self.block_num
            trx_new['transaction_num'] = i
            if 'expiration' in trx:
                p_date = trx.get('expiration', datetime(1970, 1, 1, 0, 0))
                if isinstance(p_date, (datetime, date)):
                    trx_new['expiration'] = formatTimeString(p_date)
                else:
                    trx_new['expiration'] = p_date
            trxs.append(trx_new)
            i += 1
        return trxs

    @property
    def json_operations(self):
        """Returns all block operations as list, all dates are strings."""
        if self.only_ops or self.only_virtual_ops:
            return self["operations"]
        ops = []
        for tx in self["transactions"]:
            for op in tx["operations"]:
                # Replace opid by op name
                # op[0] = getOperationNameForId(op[0])
                if 'timestamp' in op:
                    p_date = op.get('timestamp', datetime(1970, 1, 1, 0, 0))
                    if isinstance(p_date, (datetime, date)):
                        op['timestamp'] = formatTimeString(p_date)
                    else:
                        op['timestamp'] = p_date
                ops.append(op)
        return ops

    def ops_statistics(self, add_to_ops_stat=None):
        """Returns a statistic with the occurrence of the different operation types"""
        if add_to_ops_stat is None:
            import beembase.operationids
            ops_stat = beembase.operationids.operations.copy()
            for key in ops_stat:
                ops_stat[key] = 0
        else:
            ops_stat = add_to_ops_stat.copy()
        for op in self.operations:
                if isinstance(op, dict) and 'type' in op:
                    op_type = op["type"]
                    if len(op_type) > 10 and op_type[len(op_type) - 10:] == "_operation":
                        op_type = op_type[:-10]
                    ops_stat[op_type] += 1
                else:
                    if "op" in op:
                        ops_stat[op["op"][0]] += 1
                    else:
                        ops_stat[op[0]] += 1
        return ops_stat


class BlockHeader(BlockchainObject):
    """ Read a single block header from the chain

        :param int block: block number
        :param beem.steem.Steem steem_instance: Steem
            instance
        :param bool lazy: Use lazy loading

        In addition to the block data, the block number is stored as self["id"] or self.identifier.

        .. code-block:: python

            >>> from beem.block import BlockHeader
            >>> block = BlockHeader(1)
            >>> print(block)
            <BlockHeader 1>

    """
    def __init__(
        self,
        block,
        full=True,
        lazy=False,
        steem_instance=None
    ):
        """ Initilize a block

            :param int block: block number
            :param beem.steem.Steem steem_instance: Steem
                instance
            :param bool lazy: Use lazy loading

        """
        self.full = full
        self.lazy = lazy
        if isinstance(block, float):
            block = int(block)
        super(BlockHeader, self).__init__(
            block,
            lazy=lazy,
            full=full,
            steem_instance=steem_instance
        )

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
        block = self._parse_json_data(block)
        super(BlockHeader, self).__init__(
            block, lazy=self.lazy, full=self.full,
            steem_instance=self.steem
        )

    def time(self):
        """ Return a datatime instance for the timestamp of this block
        """
        return self['timestamp']

    @property
    def block_num(self):
        """Returns the block number"""
        return self.identifier

    def _parse_json_data(self, block):
        parse_times = [
            "timestamp",
        ]
        for p in parse_times:
            if p in block and isinstance(block.get(p), string_types):
                block[p] = formatTimeString(block.get(p, "1970-01-01T00:00:00"))
        return block

    def json(self):
        output = self.copy()
        parse_times = [
            "timestamp",
        ]
        for p in parse_times:
            if p in output:
                p_date = output.get(p, datetime(1970, 1, 1, 0, 0))
                if isinstance(p_date, (datetime, date)):
                    output[p] = formatTimeString(p_date)
                else:
                    output[p] = p_date
        return json.loads(str(json.dumps(output)))
