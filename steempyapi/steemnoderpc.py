import re
import sys
import threading
import websocket
import ssl
import json
import time
from itertools import cycle
from grapheneapi.graphenewsrpc import GrapheneWebsocketRPC
from steempybase.chains import known_chains
from . import exceptions
import logging
log = logging.getLogger(__name__)


class NumRetriesReached(Exception):
    pass


class SteemNodeRPC(GrapheneWebsocketRPC):

    def __init__(self, *args, **kwargs):
        super(SteemNodeRPC, self).__init__(*args, **kwargs)
        self.chain_params = self.get_network()

    def register_apis(self):
        return
        # self.api_id["database"] = self.database(api_id=1)
        # self.api_id["market_history"] = self.market_history(api_id=1)
        # self.api_id["network_broadcast"] = self.network_broadcast(api_id=1)
        # self.api_id["follow"] = self.follow(api_id=1)

    def rpcexec(self, payload):
        """ Execute a call by sending the payload.
            It makes use of the GrapheneRPC library.
            In here, we mostly deal with Steem specific error handling

            :param json payload: Payload data
            :raises ValueError: if the server does not respond in proper JSON format
            :raises RPCError: if the server returns an error
        """
        try:
            # Forward call to GrapheneWebsocketRPC and catch+evaluate errors
            return super(SteemNodeRPC, self).rpcexec(payload)
        except exceptions.RPCError as e:
            msg = exceptions.decodeRPCErrorMsg(e).strip()
            if msg == "missing required active authority":
                raise exceptions.MissingRequiredActiveAuthority
            elif re.match("^no method with name.*", msg):
                raise exceptions.NoMethodWithName(msg)
            elif msg:
                raise exceptions.UnhandledRPCError(msg)
            else:
                raise e
        except Exception as e:
            raise e

    def get_account(self, name, **kwargs):
        """ Get full account details from account name or id

            :param str name: Account name or account id
        """
        if isinstance(name, str):
            return self.get_accounts([name], **kwargs)
        elif isinstance(name, int):
            return self.get_account_references(name, **kwargs)

    def get_network(self):
        """ Identify the connected network. This call returns a
            dictionary with keys chain_id, core_symbol and prefix
        """
        props = self.get_config()
        chain_id = props["STEEMIT_CHAIN_ID"]
        for k, v in known_chains.items():
            if v["chain_id"] == chain_id:
                return v
        raise("Connecting to unknown network!")
