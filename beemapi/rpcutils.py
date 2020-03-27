"""graphennewsrpc."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import time
import json
import logging
from .exceptions import (
    UnauthorizedError, RPCConnection, RPCError, NumRetriesReached, CallRetriesReached
)
from .node import Nodes

log = logging.getLogger(__name__)


def is_network_appbase_ready(props):
    """Checks if the network is appbase ready"""
    if "STEEMIT_BLOCKCHAIN_VERSION" in props:
        return False
    elif "STEEM_BLOCKCHAIN_VERSION" in props:
        return True
    elif "HIVE_BLOCKCHAIN_VERSION" in props:
        return True
    else:
        return False


def get_query(appbase, request_id, api_name, name, args):
    query = []
    if not appbase or api_name == "condenser_api":
        query = {"method": "call",
                 "params": [api_name, name, list(args)],
                 "jsonrpc": "2.0",
                 "id": request_id}
    else:
        args = json.loads(json.dumps(args))
        # print(args)
        if len(args) > 0 and isinstance(args, list) and isinstance(args[0], dict):
            query = {"method": api_name + "." + name,
                     "params": args[0],
                     "jsonrpc": "2.0",
                     "id": request_id}
        elif len(args) > 0 and isinstance(args, list) and isinstance(args[0], list) and len(args[0]) > 0 and isinstance(args[0][0], dict):
            for a in args[0]:
                query.append({"method": api_name + "." + name,
                              "params": a,
                              "jsonrpc": "2.0",
                              "id": request_id})
                request_id += 1
        elif args:
            query = {"method": "call",
                     "params": [api_name, name, list(args)],
                     "jsonrpc": "2.0",
                     "id": request_id}
            request_id += 1
        elif api_name == "condenser_api":
            query = {"method": api_name + "." + name,
                     "jsonrpc": "2.0",
                     "params": [],
                     "id": request_id}
        else:
            query = {"method": api_name + "." + name,
                     "jsonrpc": "2.0",
                     "params": {},
                     "id": request_id}
    return query


def get_api_name(appbase, *args, **kwargs):
    if not appbase:
        # Sepcify the api to talk to
        if ("api" in kwargs) and len(kwargs["api"]) > 0:
            api_name = kwargs["api"].replace("_api", "") + "_api"
        else:
            api_name = None
    else:
        # Sepcify the api to talk to
        if ("api" in kwargs) and len(kwargs["api"]) > 0:
            if kwargs["api"] not in ["jsonrpc", "hive"]:
                api_name = kwargs["api"].replace("_api", "") + "_api"
            else:
                api_name = kwargs["api"]
        else:
            api_name = "condenser_api"
    return api_name
