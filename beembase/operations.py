# -*- coding: utf-8 -*-
from beemgraphenebase.py23 import bytes_types, integer_types, string_types, text_type
from collections import OrderedDict
import json
from binascii import hexlify, unhexlify
import re
from beemgraphenebase.types import (
    Uint8, Int16, Uint16, Uint32, Uint64,
    Varint32, Int64, String, Bytes, Void,
    Array, PointInTime, Signature, Bool,
    Set, Fixed_array, Optional, Static_variant,
    Map, Id, HexString
)
from .objects import GrapheneObject, isArgsThisClass
from beemgraphenebase.account import PublicKey
from beemgraphenebase.py23 import PY2, PY3
from .objects import (
    Operation,
    Memo,
    Amount,
    Extension,
    Price,
    WitnessProps,
    Permission,
    ExchangeRate,
    Beneficiaries,
    Beneficiary,
    CommentOptionExtensions,
    UpdateProposalExtensions
)

default_prefix = "STM"


def check_for_class(self, args):
    if isArgsThisClass(self, args):
        self.data = args[0].data
        return True
    else:
        return False


class Transfer(GrapheneObject):
    def __init__(self, *args, **kwargs):
        # Allow for overwrite of prefix
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        if "memo" not in kwargs:
            kwargs["memo"] = ""
        if isinstance(kwargs["memo"], dict):
            kwargs["memo"]["prefix"] = prefix
            memo = Optional(Memo(**kwargs["memo"]))
        elif isinstance(kwargs["memo"], string_types):
            memo = (String(kwargs["memo"]))
        else:
            memo = Optional(Memo(kwargs["memo"]))

        super(Transfer, self).__init__(OrderedDict([
            ('from', String(kwargs["from"])),
            ('to', String(kwargs["to"])),
            ('amount', Amount(kwargs["amount"], prefix=prefix, json_str=json_str)),
            ('memo', memo),
        ]))


class Vote(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        super(Vote, self).__init__(OrderedDict([
            ('voter', String(kwargs["voter"])),
            ('author', String(kwargs["author"])),
            ('permlink', String(kwargs["permlink"])),
            ('weight', Int16(kwargs["weight"])),
        ]))


class Transfer_to_vesting(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        super(Transfer_to_vesting, self).__init__(OrderedDict([
            ('from', String(kwargs["from"])),
            ('to', String(kwargs["to"])),
            ('amount', Amount(kwargs["amount"], prefix=prefix, json_str=json_str)),
        ]))


class Withdraw_vesting(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        super(Withdraw_vesting, self).__init__(OrderedDict([
            ('account', String(kwargs["account"])),
            ('vesting_shares', Amount(kwargs["vesting_shares"], prefix=prefix)),
        ]))


class Account_witness_vote(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        super(Account_witness_vote, self).__init__(OrderedDict([
            ('account', String(kwargs["account"])),
            ('witness', String(kwargs["witness"])),
            ('approve', Bool(bool(kwargs["approve"]))),
        ]))


class Account_witness_proxy(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        super(Account_witness_proxy, self).__init__(OrderedDict([
            ('account', String(kwargs["account"])),
            ('proxy', String(kwargs["proxy"])),
        ]))


class Custom(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        super(Custom, self).__init__(OrderedDict([
            ('required_auths',
                Array([String(o) for o in kwargs["required_auths"]])),
            ('id', Uint16(int(kwargs["id"]))),
            ('data', String(kwargs["data"])),
        ]))


class Custom_binary(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        super(Custom_binary, self).__init__(OrderedDict([
            ('id', Uint16(int(kwargs["id"]))),
            ('data', String(kwargs["data"])),
        ]))


class Op_wrapper(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        super(Op_wrapper, self).__init__(OrderedDict([
            ('op', Operation(kwargs["op"], prefix=prefix)),
        ]))


class Account_create(GrapheneObject):

    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        if not len(kwargs["new_account_name"]) <= 16:
            raise AssertionError("Account name must be at most 16 chars long")

        meta = ""
        if "json_metadata" in kwargs and kwargs["json_metadata"]:
            if isinstance(kwargs["json_metadata"], dict):
                meta = json.dumps(kwargs["json_metadata"])
            else:
                meta = kwargs["json_metadata"]

        super(Account_create, self).__init__(OrderedDict([
            ('fee', Amount(kwargs["fee"], prefix=prefix, json_str=json_str)),
            ('creator', String(kwargs["creator"])),
            ('new_account_name', String(kwargs["new_account_name"])),
            ('owner', Permission(kwargs["owner"], prefix=prefix)),
            ('active', Permission(kwargs["active"], prefix=prefix)),
            ('posting', Permission(kwargs["posting"], prefix=prefix)),
            ('memo_key', PublicKey(kwargs["memo_key"], prefix=prefix)),
            ('json_metadata', String(meta)),
        ]))


class Account_create_with_delegation(GrapheneObject):

    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        if not len(kwargs["new_account_name"]) <= 16:
            raise AssertionError("Account name must be at most 16 chars long")

        meta = ""
        if "json_metadata" in kwargs and kwargs["json_metadata"]:
            if isinstance(kwargs["json_metadata"], dict):
                meta = json.dumps(kwargs["json_metadata"])
            else:
                meta = kwargs["json_metadata"]

        super(Account_create_with_delegation, self).__init__(OrderedDict([
            ('fee', Amount(kwargs["fee"], prefix=prefix, json_str=json_str)),
            ('delegation', Amount(kwargs["delegation"], prefix=prefix, json_str=json_str)),
            ('creator', String(kwargs["creator"])),
            ('new_account_name', String(kwargs["new_account_name"])),
            ('owner', Permission(kwargs["owner"], prefix=prefix)),
            ('active', Permission(kwargs["active"], prefix=prefix)),
            ('posting', Permission(kwargs["posting"], prefix=prefix)),
            ('memo_key', PublicKey(kwargs["memo_key"], prefix=prefix)),
            ('json_metadata', String(meta)),
            ('extensions', Array([])),
        ]))


class Account_update(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)

        if "owner" in kwargs:
            owner = Optional(Permission(kwargs["owner"], prefix=prefix))
        else:
            owner = Optional(None)

        if "active" in kwargs:
            active = Optional(Permission(kwargs["active"], prefix=prefix))
        else:
            active = Optional(None)

        if "posting" in kwargs:
            posting = Optional(Permission(kwargs["posting"], prefix=prefix))
        else:
            posting = Optional(None)

        meta = ""
        if "json_metadata" in kwargs and kwargs["json_metadata"]:
            if isinstance(kwargs["json_metadata"], dict):
                meta = json.dumps(kwargs["json_metadata"])
            else:
                meta = kwargs["json_metadata"]

        super(Account_update, self).__init__(OrderedDict([
            ('account', String(kwargs["account"])),
            ('owner', owner),
            ('active', active),
            ('posting', posting),
            ('memo_key', PublicKey(kwargs["memo_key"], prefix=prefix)),
            ('json_metadata', String(meta)),
        ]))


class Account_update2(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        extensions = Array([])

        if "owner" in kwargs:
            owner = Optional(Permission(kwargs["owner"], prefix=prefix))
        else:
            owner = Optional(None)

        if "active" in kwargs:
            active = Optional(Permission(kwargs["active"], prefix=prefix))
        else:
            active = Optional(None)

        if "posting" in kwargs:
            posting = Optional(Permission(kwargs["posting"], prefix=prefix))
        else:
            posting = Optional(None)

        if "memo_key" in kwargs:
            memo_key = Optional(PublicKey(kwargs["memo_key"], prefix=prefix))
        else:
            memo_key = Optional(None)        

        meta = ""
        if "json_metadata" in kwargs and kwargs["json_metadata"]:
            if isinstance(kwargs["json_metadata"], dict):
                meta = json.dumps(kwargs["json_metadata"])
            else:
                meta = kwargs["json_metadata"]
        posting_meta = ""
        if "posting_json_metadata" in kwargs and kwargs["posting_json_metadata"]:
            if isinstance(kwargs["posting_json_metadata"], dict):
                posting_meta = json.dumps(kwargs["posting_json_metadata"])
            else:
                posting_meta = kwargs["posting_json_metadata"]        

        super(Account_update2, self).__init__(OrderedDict([
            ('account', String(kwargs["account"])),
            ('owner', owner),
            ('active', active),
            ('posting', posting),
            ('memo_key', memo_key),
            ('json_metadata', String(meta)),
            ('posting_json_metadata', String(posting_meta)),
            ('extensions', extensions)
        ]))



class Create_proposal(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        extensions = Array([])

        super(Create_proposal, self).__init__(
            OrderedDict([
                ('creator', String(kwargs["creator"])),
                ('receiver', String(kwargs["receiver"])),
                ('start_date', PointInTime(kwargs["start_date"])),
                ('end_date', PointInTime(kwargs["end_date"])),
                ('daily_pay', Amount(kwargs["daily_pay"], prefix=prefix, json_str=json_str)),
                ('subject', String(kwargs["subject"])),
                ('permlink', String(kwargs["permlink"])),
                ('extensions', extensions)
            ]))


class Update_proposal_votes(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        extensions = Array([])
        proposal_ids = []
        for e in kwargs["proposal_ids"]:
            proposal_ids.append(Uint64(e))

        super(Update_proposal_votes, self).__init__(
            OrderedDict([
                ('voter', String(kwargs["voter"])),
                ('proposal_ids', Array(proposal_ids)),          
                ('approve', Bool(kwargs["approve"])),
                ('extensions', extensions)
            ]))


class Remove_proposal(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        extensions = Array([])
        proposal_ids = []
        for e in kwargs["proposal_ids"]:
            proposal_ids.append(Uint64(e))        

        super(Remove_proposal, self).__init__(
            OrderedDict([
                ('proposal_owner', String(kwargs["proposal_owner"])),
                ('proposal_ids', Array(proposal_ids)),
                ('extensions', extensions)
            ]))

class Update_proposal(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]

        prefix = kwargs.get("prefix", default_prefix)
        extensions = Array([])
        if "extensions" in kwargs and kwargs["extensions"]:
            extensions = Array([UpdateProposalExtensions(o) for o in kwargs["extensions"]])


        super(Update_proposal, self).__init__(
            OrderedDict([
                ('proposal_id', Uint64(kwargs["proposal_id"])),
                ('creator', String(kwargs["creator"])),
                ('daily_pay', Amount(kwargs["daily_pay"], prefix = prefix)),
                ('subject', String(kwargs["subject"])),
                ('permlink', String(kwargs["permlink"])),
                ('extensions', extensions)
            ]))

class Witness_set_properties(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.pop("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        extensions = Array([])
        props = {}
        for k in kwargs["props"]:
            if "key" == k[0]:
                block_signing_key = (PublicKey(k[1], prefix=prefix))
                props["key"] = repr(block_signing_key)
            elif "new_signing_key" == k[0]:
                new_signing_key = (PublicKey(k[1], prefix=prefix))
                props["new_signing_key"] = repr(new_signing_key)
        for k in kwargs["props"]:
            if k[0] in ["key", "new_signing_key"]:
                continue
            if isinstance(k[1], str) and PY3:
                is_hex = re.fullmatch(r'[0-9a-fA-F]+', k[1] or '') is not None
            elif isinstance(k[1], str) and PY2:
                is_hex = re.match(r'[0-9a-fA-F]+', k[1] or '') is not None
            else:
                is_hex = False
            if isinstance(k[1], int) and k[0] in ["account_subsidy_budget", "account_subsidy_decay", "maximum_block_size"]:
                props[k[0]] = (hexlify(Uint32(k[1]).__bytes__())).decode()
            elif isinstance(k[1], int) and k[0] in ["sbd_interest_rate", "hbd_interest_rate"]:
                props[k[0]] = (hexlify(Uint16(k[1]).__bytes__())).decode()          
            elif not isinstance(k[1], str) and k[0] in ["account_creation_fee"]:
                props[k[0]] = (hexlify(Amount(k[1], prefix=prefix, json_str=json_str).__bytes__())).decode()
            elif not is_hex and isinstance(k[1], str) and k[0] in ["account_creation_fee"]:
                props[k[0]] = (hexlify(Amount(k[1], prefix=prefix, json_str=json_str).__bytes__())).decode()
            elif not isinstance(k[1], str) and k[0] in ["sbd_exchange_rate", "hbd_exchange_rate"]:
                if 'prefix' not in k[1]:
                    k[1]['prefix'] = prefix               
                props[k[0]] = (hexlify(ExchangeRate(k[1]).__bytes__())).decode()             
            elif not is_hex and k[0] in ["url"]:
                props[k[0]] = (hexlify(String(k[1]).__bytes__())).decode()
            else:
                props[k[0]] = (k[1])
        props_list = []
        for k in props:
            props_list.append(([String(k), HexString(props[k])]))
        props_list = sorted(
            props_list,
            key=lambda x: str(x[0]),
            reverse=False,
        )
        map_props = Map(props_list)

        super(Witness_set_properties, self).__init__(OrderedDict([
            ('owner', String(kwargs["owner"])),
            ('props', map_props),
            ('extensions', extensions),
        ]))


class Witness_update(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.pop("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        if "block_signing_key" in kwargs and kwargs["block_signing_key"]:
            block_signing_key = (PublicKey(kwargs["block_signing_key"], prefix=prefix))
        else:
            block_signing_key = PublicKey(
                prefix + "1111111111111111111111111111111114T1Anm", prefix=prefix)
        if 'prefix' not in kwargs['props']:
            kwargs['props']['prefix'] = prefix

        super(Witness_update, self).__init__(OrderedDict([
            ('owner', String(kwargs["owner"])),
            ('url', String(kwargs["url"])),
            ('block_signing_key', block_signing_key),
            ('props', WitnessProps(kwargs["props"])),
            ('fee', Amount(kwargs["fee"], prefix=prefix, json_str=json_str)),
        ]))


class Comment(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        meta = ""
        if "json_metadata" in kwargs and kwargs["json_metadata"]:
            if (isinstance(kwargs["json_metadata"], dict) or isinstance(kwargs["json_metadata"], list)):
                meta = json.dumps(kwargs["json_metadata"])
            else:
                meta = kwargs["json_metadata"]

        super(Comment, self).__init__(
            OrderedDict([
                ('parent_author', String(kwargs["parent_author"])),
                ('parent_permlink', String(kwargs["parent_permlink"])),
                ('author', String(kwargs["author"])),
                ('permlink', String(kwargs["permlink"])),
                ('title', String(kwargs["title"])),
                ('body', String(kwargs["body"])),
                ('json_metadata', String(meta)),
            ]))


class Custom_json(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        if "json" in kwargs and kwargs["json"]:
            if (isinstance(kwargs["json"], dict) or isinstance(kwargs["json"], list)):
                js = json.dumps(kwargs["json"], separators=(',',':'))
            else:
                js = kwargs["json"]

        if len(kwargs["id"]) > 32:
            raise Exception("'id' too long")

        super(Custom_json, self).__init__(
            OrderedDict([
                ('required_auths',
                 Array([String(o) for o in kwargs["required_auths"]])),
                ('required_posting_auths',
                 Array([
                     String(o) for o in kwargs["required_posting_auths"]
                 ])),
                ('id', String(kwargs["id"])),
                ('json', String(js)),
            ]))


class Comment_options(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        # handle beneficiaries
        if "beneficiaries" in kwargs and kwargs['beneficiaries']:
            kwargs['extensions'] = [[0, {'beneficiaries': kwargs['beneficiaries']}]]
        extensions = Array([])
        if "extensions" in kwargs and kwargs["extensions"]:
            extensions = Array([CommentOptionExtensions(o) for o in kwargs["extensions"]])
        if "percent_hbd" in kwargs:
            super(Comment_options, self).__init__(
                OrderedDict([
                    ('author', String(kwargs["author"])),
                    ('permlink', String(kwargs["permlink"])),
                    ('max_accepted_payout',
                     Amount(kwargs["max_accepted_payout"], prefix=prefix, json_str=json_str)),
                    ('percent_hbd',
                     Uint16(int(kwargs["percent_hbd"]))),
                    ('allow_votes', Bool(bool(kwargs["allow_votes"]))),
                    ('allow_curation_rewards',
                     Bool(bool(kwargs["allow_curation_rewards"]))),
                    ('extensions', extensions),
                ]))
        else:
            super(Comment_options, self).__init__(
                OrderedDict([
                    ('author', String(kwargs["author"])),
                    ('permlink', String(kwargs["permlink"])),
                    ('max_accepted_payout',
                     Amount(kwargs["max_accepted_payout"], prefix=prefix)),
                    ('percent_steem_dollars',
                     Uint16(int(kwargs["percent_steem_dollars"]))),
                    ('allow_votes', Bool(bool(kwargs["allow_votes"]))),
                    ('allow_curation_rewards',
                     Bool(bool(kwargs["allow_curation_rewards"]))),
                    ('extensions', extensions),
                ]))            


class Delete_comment(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        super(Delete_comment, self).__init__(
            OrderedDict([
                ('author', String(kwargs["author"])),
                ('permlink', String(kwargs["permlink"])),
            ]))


class Feed_publish(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        if 'prefix' not in kwargs['exchange_rate']:
            kwargs['exchange_rate']['prefix'] = prefix      
        super(Feed_publish, self).__init__(
            OrderedDict([
                ('publisher', String(kwargs["publisher"])),
                ('exchange_rate', ExchangeRate(kwargs["exchange_rate"])),
            ]))


class Convert(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        super(Convert, self).__init__(
            OrderedDict([
                ('owner', String(kwargs["owner"])),
                ('requestid', Uint32(kwargs["requestid"])),
                ('amount', Amount(kwargs["amount"], prefix=prefix, json_str=json_str)),
            ]))


class Set_withdraw_vesting_route(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        super(Set_withdraw_vesting_route, self).__init__(
            OrderedDict([
                ('from_account', String(kwargs["from_account"])),
                ('to_account', String(kwargs["to_account"])),
                ('percent', Uint16((kwargs["percent"]))),
                ('auto_vest', Bool(kwargs["auto_vest"])),
            ]))


class Limit_order_cancel(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        super(Limit_order_cancel, self).__init__(
            OrderedDict([
                ('owner', String(kwargs["owner"])),
                ('orderid', Uint32(kwargs["orderid"])),
            ]))


class Claim_account(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        super(Claim_account, self).__init__(
            OrderedDict([
                ('creator', String(kwargs["creator"])),
                ('fee', Amount(kwargs["fee"], prefix=prefix, json_str=json_str)),
                ('extensions', Array([])),
            ]))


class Create_claimed_account(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)

        if not len(kwargs["new_account_name"]) <= 16:
            raise AssertionError("Account name must be at most 16 chars long")

        meta = ""
        if "json_metadata" in kwargs and kwargs["json_metadata"]:
            if isinstance(kwargs["json_metadata"], dict):
                meta = json.dumps(kwargs["json_metadata"])
            else:
                meta = kwargs["json_metadata"]

        super(Create_claimed_account, self).__init__(
            OrderedDict([
                ('creator', String(kwargs["creator"])),
                ('new_account_name', String(kwargs["new_account_name"])),
                ('owner', Permission(kwargs["owner"], prefix=prefix)),
                ('active', Permission(kwargs["active"], prefix=prefix)),
                ('posting', Permission(kwargs["posting"], prefix=prefix)),
                ('memo_key', PublicKey(kwargs["memo_key"], prefix=prefix)),
                ('json_metadata', String(meta)),
                ('extensions', Array([])),
            ]))


class Delegate_vesting_shares(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        super(Delegate_vesting_shares, self).__init__(
            OrderedDict([
                ('delegator', String(kwargs["delegator"])),
                ('delegatee', String(kwargs["delegatee"])),
                ('vesting_shares', Amount(kwargs["vesting_shares"], prefix=prefix)),
            ]))


class Limit_order_create(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        super(Limit_order_create, self).__init__(
            OrderedDict([
                ('owner', String(kwargs["owner"])),
                ('orderid', Uint32(kwargs["orderid"])),
                ('amount_to_sell', Amount(kwargs["amount_to_sell"], prefix=prefix, json_str=json_str)),
                ('min_to_receive', Amount(kwargs["min_to_receive"], prefix=prefix, json_str=json_str)),
                ('fill_or_kill', Bool(kwargs["fill_or_kill"])),
                ('expiration', PointInTime(kwargs["expiration"])),
            ]))


class Limit_order_create2(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        if 'prefix' not in kwargs['exchange_rate']:
            kwargs['exchange_rate']['prefix'] = prefix     
        super(Limit_order_create2, self).__init__(
            OrderedDict([
                ('owner', String(kwargs["owner"])),
                ('orderid', Uint32(kwargs["orderid"])),
                ('amount_to_sell', Amount(kwargs["amount_to_sell"], prefix=prefix, json_str=json_str)),
                ('fill_or_kill', Bool(kwargs["fill_or_kill"])),
                ('exchange_rate', ExchangeRate(kwargs["exchange_rate"])),
                ('expiration', PointInTime(kwargs["expiration"])),
            ]))


class Change_recovery_account(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        super(Change_recovery_account, self).__init__(
            OrderedDict([
                ('account_to_recover', String(kwargs["account_to_recover"])),
                ('new_recovery_account', String(kwargs["new_recovery_account"])),
                ('extensions', Array([])),
            ]))


class Transfer_from_savings(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        if "memo" not in kwargs:
            kwargs["memo"] = ""

        super(Transfer_from_savings, self).__init__(
            OrderedDict([
                ('from', String(kwargs["from"])),
                ('request_id', Uint32(kwargs["request_id"])),
                ('to', String(kwargs["to"])),
                ('amount', Amount(kwargs["amount"], prefix=prefix, json_str=json_str)),
                ('memo', String(kwargs["memo"])),
            ]))


class Cancel_transfer_from_savings(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        super(Cancel_transfer_from_savings, self).__init__(
            OrderedDict([
                ('from', String(kwargs["from"])),
                ('request_id', Uint32(kwargs["request_id"])),
            ]))


class Claim_reward_balance(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        if "reward_sbd" in kwargs and "reward_steem" in kwargs:
            super(Claim_reward_balance, self).__init__(
                OrderedDict([
                    ('account', String(kwargs["account"])),
                    ('reward_steem', Amount(kwargs["reward_steem"], prefix=prefix, json_str=json_str)),
                    ('reward_sbd', Amount(kwargs["reward_sbd"], prefix=prefix, json_str=json_str)),
                    ('reward_vests', Amount(kwargs["reward_vests"], prefix=prefix)),
                ]))
        elif "reward_hbd" in kwargs and "reward_hive" in kwargs:
            super(Claim_reward_balance, self).__init__(
                OrderedDict([
                    ('account', String(kwargs["account"])),
                    ('reward_hive', Amount(kwargs["reward_hive"], prefix=prefix)),
                    ('reward_hbd', Amount(kwargs["reward_hbd"], prefix=prefix)),
                    ('reward_vests', Amount(kwargs["reward_vests"], prefix=prefix)),
                ]))    
        elif "reward_hive" in kwargs:
            super(Claim_reward_balance, self).__init__(
                OrderedDict([
                    ('account', String(kwargs["account"])),
                    ('reward_hive', Amount(kwargs["reward_hive"], prefix=prefix, json_str=json_str)),
                    ('reward_vests', Amount(kwargs["reward_vests"], prefix=prefix)),
                ]))
        elif "reward_blurt" in kwargs:
            super(Claim_reward_balance, self).__init__(
                OrderedDict([
                    ('account', String(kwargs["account"])),
                    ('reward_blurt', Amount(kwargs["reward_blurt"], prefix=prefix)),
                    ('reward_vests', Amount(kwargs["reward_vests"], prefix=prefix)),
                ]))
        else:
            super(Claim_reward_balance, self).__init__(
                OrderedDict([
                    ('account', String(kwargs["account"])),
                    ('reward_steem', Amount(kwargs["reward_steem"], prefix=prefix)),
                    ('reward_vests', Amount(kwargs["reward_vests"], prefix=prefix)),
                ]))            


class Transfer_to_savings(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        if "memo" not in kwargs:
            kwargs["memo"] = ""
        super(Transfer_to_savings, self).__init__(
            OrderedDict([
                ('from', String(kwargs["from"])),
                ('to', String(kwargs["to"])),
                ('amount', Amount(kwargs["amount"], prefix=prefix, json_str=json_str)),
                ('memo', String(kwargs["memo"])),
            ]))


class Request_account_recovery(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        new_owner = Permission(kwargs["new_owner_authority"], prefix=prefix)
        super(Request_account_recovery, self).__init__(
            OrderedDict([
                ('recovery_account', String(kwargs["recovery_account"])),
                ('account_to_recover', String(kwargs["account_to_recover"])),
                ('new_owner_authority', new_owner),
                ('extensions', Array([])),
            ]))


class Recover_account(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        new_owner = Permission(kwargs["new_owner_authority"], prefix=prefix)
        recent_owner = Permission(kwargs["recent_owner_authority"], prefix=prefix)
        super(Recover_account, self).__init__(
            OrderedDict([
                ('account_to_recover', String(kwargs["account_to_recover"])),
                ('new_owner_authority', new_owner),
                ('recent_owner_authority', recent_owner),
                ('extensions', Array([])),
            ]))


class Escrow_transfer(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        meta = ""
        if "json_meta" in kwargs and kwargs["json_meta"]:
            if (isinstance(kwargs["json_meta"], dict) or isinstance(kwargs["json_meta"], list)):
                meta = json.dumps(kwargs["json_meta"])
            else:
                meta = kwargs["json_meta"]
        if "hbd_amount" in kwargs and "hive_amount" in kwargs:
            super(Escrow_transfer, self).__init__(
                OrderedDict([
                    ('from', String(kwargs["from"])),
                    ('to', String(kwargs["to"])),
                    ('agent', String(kwargs["agent"])),
                    ('escrow_id', Uint32(kwargs["escrow_id"])),
                    ('hbd_amount', Amount(kwargs["hbd_amount"], prefix=prefix, json_str=json_str)),
                    ('hive_amount', Amount(kwargs["hive_amount"], prefix=prefix, json_str=json_str)),
                    ('fee', Amount(kwargs["fee"], prefix=prefix, json_str=json_str)),
                    ('ratification_deadline', PointInTime(kwargs["ratification_deadline"])),
                    ('escrow_expiration', PointInTime(kwargs["escrow_expiration"])),
                    ('json_meta', String(meta)),
                ]))
        else:
            super(Escrow_transfer, self).__init__(
                OrderedDict([
                    ('from', String(kwargs["from"])),
                    ('to', String(kwargs["to"])),
                    ('agent', String(kwargs["agent"])),
                    ('escrow_id', Uint32(kwargs["escrow_id"])),
                    ('sbd_amount', Amount(kwargs["sbd_amount"], prefix=prefix)),
                    ('steem_amount', Amount(kwargs["steem_amount"], prefix=prefix)),
                    ('fee', Amount(kwargs["fee"], prefix=prefix)),
                    ('ratification_deadline', PointInTime(kwargs["ratification_deadline"])),
                    ('escrow_expiration', PointInTime(kwargs["escrow_expiration"])),
                    ('json_meta', String(meta)),
                ]))            


class Escrow_dispute(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        super(Escrow_dispute, self).__init__(
            OrderedDict([
                ('from', String(kwargs["from"])),
                ('to', String(kwargs["to"])),
                ('who', String(kwargs["who"])),
                ('escrow_id', Uint32(kwargs["escrow_id"])),
            ]))


class Escrow_release(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        prefix = kwargs.get("prefix", default_prefix)
        json_str = kwargs.get("json_str", False)
        if "hive_amount" in kwargs and "hbd_amount" in kwargs:
            super(Escrow_release, self).__init__(
                OrderedDict([
                    ('from', String(kwargs["from"])),
                    ('to', String(kwargs["to"])),
                    ('who', String(kwargs["who"])),
                    ('escrow_id', Uint32(kwargs["escrow_id"])),
                    ('hbd_amount', Amount(kwargs["hbd_amount"], prefix=prefix, json_str=json_str)),
                    ('hive_amount', Amount(kwargs["hive_amount"], prefix=prefix, json_str=json_str)),
                ]))
        else:
            super(Escrow_release, self).__init__(
                OrderedDict([
                    ('from', String(kwargs["from"])),
                    ('to', String(kwargs["to"])),
                    ('who', String(kwargs["who"])),
                    ('escrow_id', Uint32(kwargs["escrow_id"])),
                    ('sbd_amount', Amount(kwargs["sbd_amount"], prefix=prefix)),
                    ('steem_amount', Amount(kwargs["steem_amount"], prefix=prefix)),
                ]))            


class Escrow_approve(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        super(Escrow_approve, self).__init__(
            OrderedDict([
                ('from', String(kwargs["from"])),
                ('to', String(kwargs["to"])),
                ('agent', String(kwargs["agent"])),
                ('who', String(kwargs["who"])),
                ('escrow_id', Uint32(kwargs["escrow_id"])),
                ('approve', Bool(kwargs["approve"])),
            ]))


class Decline_voting_rights(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if check_for_class(self, args):
            return
        if len(args) == 1 and len(kwargs) == 0:
            kwargs = args[0]
        super(Decline_voting_rights, self).__init__(
            OrderedDict([
                ('account', String(kwargs["account"])),
                ('decline', Bool(kwargs["decline"])),
            ]))
