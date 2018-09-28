# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import json
from .instance import shared_steem_instance
from beem.account import Account
from beem.constants import state_object_size_info
import hashlib
from binascii import hexlify, unhexlify
import os
from pprint import pprint
from beem.amount import Amount
from beembase import operations
from beembase.objects import Operation
from beembase.signedtransactions import Signed_Transaction
from beemgraphenebase.py23 import py23_bytes, bytes_types


class RC(object):
    def __init__(
        self,
        steem_instance=None,
    ):
        self.steem = steem_instance or shared_steem_instance()

    def get_tx_size(self, op):
        """Returns the tx size of an operation"""
        ops = [Operation(op)]
        prefix = u"STEEM"
        wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
        ref_block_num = 34294
        ref_block_prefix = 3707022213
        expiration = "2016-04-06T08:29:27"
        tx = Signed_Transaction(ref_block_num=ref_block_num,
                                ref_block_prefix=ref_block_prefix,
                                expiration=expiration,
                                operations=ops)
        tx = tx.sign([wif], chain=prefix)
        txWire = hexlify(py23_bytes(tx)).decode("ascii")
        tx_size = len(txWire)
        return tx_size

    def get_resource_count(self, tx_size, state_bytes_count=0, new_account_op_count=0, market_op_count=0):
        """Creates the resource_count dictionary based on tx_size, state_bytes_count, new_account_op_count and market_op_count"""
        resource_count = {"resource_history_bytes": tx_size}
        resource_count["resource_state_bytes"] = state_object_size_info["transaction_object_base_size"]
        resource_count["resource_state_bytes"] += state_object_size_info["transaction_object_byte_size"] * tx_size
        resource_count["resource_state_bytes"] += state_bytes_count
        resource_count["resource_new_accounts"] = new_account_op_count
        if market_op_count > 0:
            resource_count["resource_market_bytes"] = market_op_count
        return resource_count

    def comment(self, comment_dict):
        """Calc RC costs for a comment

        Example for calculating RC costs

        .. code-block:: python

            from beem.rc import RC
            comment_dict = {
                            "permlink": "test", "author": "holger80",
                            "body": "test", "parent_permlink": "",
                            "parent_author": "", "title": "test",
                            "json_metadata": {"foo": "bar"}
                           }

            rc = RC()
            print(rc.comment(comment_dict))

        """
        state_bytes_count = state_object_size_info["comment_object_base_size"]
        state_bytes_count += state_object_size_info["comment_object_permlink_char_size"] * len(comment_dict["permlink"])
        state_bytes_count += state_object_size_info["comment_object_parent_permlink_char_size"] * len(comment_dict["parent_permlink"])
        op = operations.Comment(**comment_dict)
        tx_size = self.get_tx_size(op)
        resource_count = self.get_resource_count(tx_size, state_bytes_count)

        return self.steem.get_rc_cost(resource_count)

    def vote(self, vote_dict):
        """Calc RC costs for a vote

        Example for calculating RC costs

        .. code-block:: python

            from beem.rc import RC
            vote_dict = {
                         "voter": "foobara", "author": "foobarc",
                         "permlink": "foobard", "weight": 1000
                        }

            rc = RC()
            print(rc.comment(vote_dict))

        """
        op = operations.Vote(**vote_dict)
        tx_size = self.get_tx_size(op)
        state_bytes_count = state_object_size_info["comment_vote_object_base_size"]
        resource_count = self.get_resource_count(tx_size, state_bytes_count)
        return self.steem.get_rc_cost(resource_count)

    def transfer(self, transfer_dict):
        """Calc RC costs for a transfer

        Example for calculating RC costs

        .. code-block:: python

            from beem.rc import RC
            from beem.amount import Amount
            transfer_dict = {
                             "from": "foo", "to": "baar",
                             "amount": Amount("111.110 STEEM"),
                             "memo": "Fooo"
                            }

            rc = RC()
            print(rc.comment(transfer_dict))

        """
        market_op_count = 1
        op = operations.Transfer(**transfer_dict)
        tx_size = self.get_tx_size(op)
        resource_count = self.get_resource_count(tx_size, market_op_count=market_op_count)
        return self.steem.get_rc_cost(resource_count)

    def custom_json(self, custom_json_dict):
        """Calc RC costs for a custom_json

        Example for calculating RC costs

        .. code-block:: python

            from beem.rc import RC
             custom_json_dict = {
                                 "json": [
                                          "reblog", OrderedDict([("account", "xeroc"), ("author", "chainsquad"),
                                                                 ("permlink", "streemian-com-to-open-its-doors-and-offer-a-20-discount")
                                                                ])
                                         ],
                                 "required_auths": [],
                                 "required_posting_auths": ["xeroc"],
                                 "id": "follow"
                                }

            rc = RC()
            print(rc.comment(custom_json_dict))

        """
        op = operations.Custom_json(**custom_json_dict)
        tx_size = self.get_tx_size(op)
        resource_count = self.get_resource_count(tx_size)
        return self.steem.get_rc_cost(resource_count)

    def account_update(self, account_update_dict):
        """Calc RC costs for account update"""
        op = operations.Account_update(**account_update_dict)
        tx_size = self.get_tx_size(op)
        resource_count = self.get_resource_count(tx_size)
        return self.steem.get_rc_cost(resource_count)
