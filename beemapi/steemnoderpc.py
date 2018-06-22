from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes, int, str
import re
import sys
from .graphenerpc import GrapheneRPC
from beemgraphenebase.chains import known_chains
from . import exceptions
import logging
log = logging.getLogger(__name__)


class SteemNodeRPC(GrapheneRPC):
    """ This class allows to call API methods exposed by the witness node via
        websockets / rpc-json.

        :param str urls: Either a single Websocket/Http URL, or a list of URLs
        :param str user: Username for Authentication
        :param str password: Password for Authentication
        :param int num_retries: Try x times to num_retries to a node on disconnect, -1 for indefinitely
        :param int num_retries_call: Repeat num_retries_call times a rpc call on node error (default is 5)
        :param int timeout: Timeout setting for https nodes (default is 60)
        :param bool use_condenser: Use the old condenser_api rpc protocol on nodes with version
            0.19.4 or higher. The settings has no effect on nodes with version of 0.19.3 or lower.

    """

    def __init__(self, *args, **kwargs):
        """ Init SteemNodeRPC

            :param str urls: Either a single Websocket/Http URL, or a list of URLs
            :param str user: Username for Authentication
            :param str password: Password for Authentication
            :param int num_retries: Try x times to num_retries to a node on disconnect, -1 for indefinitely
            :param int num_retries_call: Repeat num_retries_call times a rpc call on node error (default is 5)
            :param int timeout: Timeout setting for https nodes (default is 60)

        """
        super(SteemNodeRPC, self).__init__(*args, **kwargs)
        self.next_node_on_empty_reply = False

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
        if self.url is None:
            raise exceptions.RPCConnection("RPC is not connected!")
        doRetry = True
        maxRetryCountReached = False
        while doRetry and not maxRetryCountReached:
            doRetry = False
            try:
                # Forward call to GrapheneWebsocketRPC and catch+evaluate errors
                reply = super(SteemNodeRPC, self).rpcexec(payload)
                if self.next_node_on_empty_reply and not bool(reply) and self.nodes.working_nodes_count > 1:
                    self._retry_on_next_node("Empty Reply")
                    doRetry = True
                    self.next_node_on_empty_reply = True
                else:
                    self.next_node_on_empty_reply = False
                    return reply
            except exceptions.RPCErrorDoRetry as e:
                msg = exceptions.decodeRPCErrorMsg(e).strip()
                try:
                    self.nodes.sleep_and_check_retries(str(msg), call_retry=True)
                    doRetry = True
                except exceptions.CallRetriesReached:
                    if self.nodes.working_nodes_count > 1:
                        self._retry_on_next_node(msg)
                        doRetry = True
                    else:
                        self.next_node_on_empty_reply = False
                        raise exceptions.CallRetriesReached
            except exceptions.RPCError as e:
                try:
                    doRetry = self._check_error_message(e, self.error_cnt_call)
                except exceptions.CallRetriesReached:
                    msg = exceptions.decodeRPCErrorMsg(e).strip()
                    if self.nodes.working_nodes_count > 1:
                        self._retry_on_next_node(msg)
                        doRetry = True
                    else:
                        self.next_node_on_empty_reply = False
                        raise exceptions.CallRetriesReached
            except Exception as e:
                self.next_node_on_empty_reply = False
                raise e
            maxRetryCountReached = self.nodes.num_retries_call_reached
        self.next_node_on_empty_reply = False

    def _retry_on_next_node(self, error_msg):
        self.nodes.increase_error_cnt()
        self.nodes.sleep_and_check_retries(error_msg, sleep=False, call_retry=False)
        self.next()

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
                # self._switch_to_next_node(msg, "ApiNotSupported")
                raise exceptions.ApiNotSupported(msg)
            else:
                raise exceptions.NoApiWithName(msg)
        elif re.search("irrelevant signature included", msg):
            raise exceptions.UnnecessarySignatureDetected(msg)
        elif re.search("WinError", msg):
            raise exceptions.RPCError(msg)
        elif re.search("Unable to acquire database lock", msg):
            self.nodes.sleep_and_check_retries(str(msg), call_retry=True)
            doRetry = True
        elif re.search("Request Timeout", msg):
            self.nodes.sleep_and_check_retries(str(msg), call_retry=True)
            doRetry = True
        elif re.search("Internal Error", msg) or re.search("Unknown exception", msg):
            self.nodes.sleep_and_check_retries(str(msg), call_retry=True)
            doRetry = True
        elif re.search("!check_max_block_age", str(e)):
            self._switch_to_next_node(str(e))
            doRetry = True
        elif re.search("out_of_rangeEEEE: unknown key", msg) or re.search("unknown key:unknown key", msg):
            raise exceptions.UnkownKey(msg)
        elif re.search("Assert Exception:v.is_object(): Input data have to treated as object", msg):
            raise exceptions.UnhandledRPCError("Use Operation(op, appbase=True) to prevent error: " + msg)
        elif re.search("Client returned invalid format. Expected JSON!", msg):
            self._switch_to_next_node(msg)
            doRetry = True
        elif msg:
            raise exceptions.UnhandledRPCError(msg)
        else:
            raise e
        return doRetry

    def _switch_to_next_node(self, msg, error_type="UnhandledRPCError"):
        if self.nodes.working_nodes_count == 1:
            if error_type == "UnhandledRPCError":
                raise exceptions.UnhandledRPCError(msg)
            elif error_type == "ApiNotSupported":
                raise exceptions.ApiNotSupported(msg)
        self.nodes.increase_error_cnt()
        self.nodes.sleep_and_check_retries(str(msg), sleep=False)
        self.next()

    def _check_api_name(self, msg):
        error_start = "Could not find API"
        known_apis = ['account_history_api', 'tags_api',
                      'database_api', 'market_history_api',
                      'block_api', 'account_by_key_api', 'chain_api',
                      'follow_api', 'condenser_api', 'debug_node_api',
                      'witness_api', 'test_api',
                      'network_broadcast_api']
        for api in known_apis:
            if re.search(error_start + " " + api, msg):
                return True
        if msg[-18:] == error_start:
            return True
        return False

    def get_account(self, name, **kwargs):
        """ Get full account details from account name

            :param str name: Account name
        """
        if isinstance(name, str):
            return self.get_accounts([name], **kwargs)
