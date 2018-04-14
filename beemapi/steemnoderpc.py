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
    :param str urls: Either a single Websocket/Http URL, or a list of URLs
    :param str user: Username for Authentication
    :param str password: Password for Authentication
    :param int num_retries: Try x times to num_retries to a node on disconnect, -1 for indefinitely
    :param int num_retries_call: Repeat num_retries_call times a rpc call on node error (default is 5)
    :param int timeout: Timeout setting for https nodes (default is 60)
    """

    def __init__(self, *args, **kwargs):
        super(SteemNodeRPC, self).__init__(*args, **kwargs)
        self.appbase = kwargs.get("appbase", False)
        self.next_node_on_empty_reply = False
        self.chain_params = self.get_network()

    def get_use_appbase(self):
        """Returns True if appbase ready and appbase calls are set"""
        return self.appbase and self.is_appbase_ready()

    def set_next_node_on_empty_reply(self, next_node_on_empty_reply=True):
        """Switch to next node on empty reply for the next rpc call"""
        self.next_node_on_empty_reply = next_node_on_empty_reply

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
                reply = super(SteemNodeRPC, self).rpcexec(payload)
                if self.next_node_on_empty_reply and not bool(reply) and self.n_urls > 1:
                    sleep_and_check_retries(self.num_retries_call, cnt, self.url, str("Empty reply"), sleep=False, call_retry=True)
                    self.error_cnt[self.url] += 1
                    self.next()
                    cnt = 0
                    self.error_cnt_call = 0
                    doRetry = True
                    self.next_node_on_empty_reply = True
                else:
                    self.next_node_on_empty_reply = False
                    return reply
            except exceptions.RPCErrorDoRetry as e:
                msg = exceptions.decodeRPCErrorMsg(e).strip()
                sleep_and_check_retries(self.num_retries_call, cnt, self.url, str(msg), call_retry=True)
                doRetry = True
            except exceptions.RPCError as e:
                doRetry = self._check_error_message(e, cnt)
            except Exception as e:
                raise e
            if doRetry:
                if self.error_cnt_call == 0:
                    cnt += 1
                else:
                    cnt = self.error_cnt_call + 1

    def _check_error_message(self, e, cnt):
        """Check error message and decide what to do"""
        doRetry = False
        msg = exceptions.decodeRPCErrorMsg(e).strip()
        if re.search("missing required active authority", msg):
            raise exceptions.MissingRequiredActiveAuthority
        elif re.search("missing required active authority", msg):
            raise exceptions.MissingRequiredActiveAuthority
        elif re.match("^no method with name.*", msg):
            raise exceptions.NoMethodWithName(msg)
        elif re.search("Could not find method", msg):
            raise exceptions.NoMethodWithName(msg)
        elif re.search("Could not find API", msg):
            if self._check_api_name(msg):
                raise exceptions.ApiNotSupported(msg)
            else:
                raise exceptions.NoApiWithName(msg)
        elif re.search("irrelevant signature included", msg):
            raise exceptions.UnnecessarySignatureDetected(msg)
        elif re.search("WinError", msg):
            raise exceptions.RPCError(msg)
        elif re.search("Unable to acquire database lock", msg):
            sleep_and_check_retries(self.num_retries_call, cnt, self.url, str(msg), call_retry=True)
            doRetry = True
        elif re.search("Internal Error", msg):
            sleep_and_check_retries(self.num_retries_call, cnt, self.url, str(msg), call_retry=True)
            doRetry = True
        elif re.search("!check_max_block_age", str(e)):
            if self.n_urls == 1:
                raise exceptions.UnhandledRPCError(msg)
            self.error_cnt[self.url] += 1
            sleep_and_check_retries(self.num_retries, self.error_cnt[self.url], self.url, str(msg), sleep=False)
            self.next()
            doRetry = True
        elif re.search("out_of_rangeEEEE: unknown key", msg) or re.search("unknown key:unknown key", msg):
            raise exceptions.UnkownKey(msg)
        elif msg:
            raise exceptions.UnhandledRPCError(msg)
        else:
            raise e
        return doRetry

    def _check_api_name(self, msg):
        error_start = "Could not find API "
        if re.search(error_start + "account_history_api", msg):
            return True
        elif re.search(error_start + "tags_api", msg):
            return True
        elif re.search(error_start + "database_api", msg):
            return True
        elif re.search(error_start + "market_history_api", msg):
            return True
        elif re.search(error_start + "block_api", msg):
            return True
        elif re.search(error_start + "account_by_key_api", msg):
            return True
        elif re.search(error_start + "chain_api", msg):
            return True
        elif re.search(error_start + "follow_api", msg):
            return True
        elif re.search(error_start + "condenser_api", msg):
            return True
        elif re.search(error_start + "debug_node_api", msg):
            return True
        elif re.search(error_start + "witness_api", msg):
            return True
        elif re.search(error_start + "test_api", msg):
            return True
        elif re.search(error_start + "network_broadcast_api", msg):
            return True
        else:
            return False

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
