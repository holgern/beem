from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes, int, str
import re
import sys
from itertools import cycle
from beemgrapheneapi.graphenerpc import GrapheneRPC
from beemgrapheneapi.rpcutils import sleep_and_check_retries
from beembase.chains import known_chains
from . import exceptions
import logging
log = logging.getLogger(__name__)


class SteemNodeRPC(GrapheneRPC):
    """This class allows to call API methods exposed by the witness node via
       websockets / rpc-json.

    """

    def __init__(self, *args, **kwargs):
        super(SteemNodeRPC, self).__init__(*args, **kwargs)
        self.appbase = kwargs.get("appbase", False)
        self.chain_params = self.get_network()

    def get_use_appbase(self):
        """Returns True if appbase ready and appbase calls are set"""
        return self.appbase and self.is_appbase_ready()

    def rpcexec(self, payload):
        """ Execute a call by sending the payload.
            It makes use of the GrapheneRPC library.
            In here, we mostly deal with Steem specific error handling

            :param json payload: Payload data
            :raises ValueError: if the server does not respond in proper JSON format
            :raises RPCError: if the server returns an error
        """
        doRetry = True
        cnt = 0
        while doRetry and cnt < self.num_retries_call:
            doRetry = False
            try:
                # Forward call to GrapheneWebsocketRPC and catch+evaluate errors
                self.error_cnt_call = cnt
                return super(SteemNodeRPC, self).rpcexec(payload)
            except exceptions.RPCError as e:
                msg = exceptions.decodeRPCErrorMsg(e).strip()
                if msg == "missing required active authority":
                    raise exceptions.MissingRequiredActiveAuthority
                elif re.search("missing required active authority", msg):
                    raise exceptions.MissingRequiredActiveAuthority
                elif re.match("^no method with name.*", msg):
                    raise exceptions.NoMethodWithName(msg)
                elif re.search("Could not find method", msg):
                    raise exceptions.NoMethodWithName(msg)
                elif re.search("Could not find API", msg):
                    raise exceptions.NoApiWithName(msg)
                elif re.search("Unable to acquire database lock", msg):
                    sleep_and_check_retries(self.num_retries_call, cnt, self.url, str(msg))
                    doRetry = True
                elif re.search("Internal Error", msg):
                    sleep_and_check_retries(self.num_retries_call, cnt, self.url, str(msg))
                    doRetry = True
                elif re.search("Service Temporarily Unavailable", msg):
                    sleep_and_check_retries(self.num_retries_call, cnt, self.url, str(msg))
                    doRetry = True
                elif re.search("Bad Gateway", msg):
                    sleep_and_check_retries(self.num_retries_call, cnt, self.url, str(msg))
                    doRetry = True
                elif msg:
                    raise exceptions.UnhandledRPCError(msg)
                else:
                    raise e
                if doRetry:
                    if self.error_cnt_call == 0:
                        cnt += 1
                    else:
                        cnt = self.error_cnt_call + 1
            except Exception as e:
                raise e

    def get_account(self, name, **kwargs):
        """ Get full account details from account name

            :param str name: Account name
        """
        if isinstance(name, str):
            return self.get_accounts([name], **kwargs)

    def get_network(self):
        """ Identify the connected network. This call returns a
            dictionary with keys chain_id, core_symbol and prefix
        """
        props = self.get_config(api="database")
        if "STEEMIT_CHAIN_ID" in props:
            chain_id = props["STEEMIT_CHAIN_ID"]
            network_version = props['STEEMIT_BLOCKCHAIN_VERSION']
        elif "STEEM_CHAIN_ID" in props:
            chain_id = props["STEEM_CHAIN_ID"]
            network_version = props['STEEM_BLOCKCHAIN_VERSION']
        else:
            raise("Connecting to unknown network!")
        highest_version_chain = None
        for k, v in list(known_chains.items()):
            if v["chain_id"] == chain_id and v["min_version"] <= network_version:
                if highest_version_chain is None:
                    highest_version_chain = v
                elif v["min_version"] > highest_version_chain["min_version"]:
                    highest_version_chain = v
        if highest_version_chain is None:
            raise("Connecting to unknown network!")
        else:
            return highest_version_chain
