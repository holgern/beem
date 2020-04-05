"""graphennewsrpc."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import next
from builtins import str
from builtins import object
from itertools import cycle
import threading
import sys
import json
import signal
import logging
import ssl
import re
import time
import warnings
import six
from .exceptions import (
    UnauthorizedError, RPCConnection, RPCError, RPCErrorDoRetry, NumRetriesReached, CallRetriesReached, WorkingNodeMissing, TimeoutException
)
from .rpcutils import (
    is_network_appbase_ready,
    get_api_name, get_query
)
from .node import Nodes
from beemgraphenebase.version import version as beem_version
from beemgraphenebase.chains import known_chains
if sys.version_info[0] < 3:
    from thread import interrupt_main
else:
    from _thread import interrupt_main
WEBSOCKET_MODULE = None
if not WEBSOCKET_MODULE:
    try:
        import websocket
        from websocket._exceptions import WebSocketConnectionClosedException, WebSocketTimeoutException
        WEBSOCKET_MODULE = "websocket"
    except ImportError:
        WEBSOCKET_MODULE = None
REQUEST_MODULE = None
if not REQUEST_MODULE:
    try:
        import requests
        from requests.adapters import HTTPAdapter
        from requests.packages.urllib3.util.retry import Retry
        from requests.exceptions import ConnectionError
        REQUEST_MODULE = "requests"
    except ImportError:
        REQUEST_MODULE = None

log = logging.getLogger(__name__)


class SessionInstance(object):
    """Singelton for the Session Instance"""
    instance = None


def set_session_instance(instance):
    """Set session instance"""
    SessionInstance.instance = instance


def shared_session_instance():
    """Get session instance"""
    if REQUEST_MODULE is None:
        raise Exception()
    if not SessionInstance.instance:
        SessionInstance.instance = requests.Session()
    return SessionInstance.instance


def create_ws_instance(use_ssl=True, enable_multithread=True):
    """Get websocket instance"""
    if WEBSOCKET_MODULE is None:
        raise Exception()
    if use_ssl:
        ssl_defaults = ssl.get_default_verify_paths()
        sslopt_ca_certs = {'ca_certs': ssl_defaults.cafile}
        return websocket.WebSocket(sslopt=sslopt_ca_certs, enable_multithread=enable_multithread)
    else:
        return websocket.WebSocket(enable_multithread=enable_multithread)


class GrapheneRPC(object):
    """
    This class allows to call API methods synchronously, without callbacks.

    It logs warnings and errors.

    :param str urls: Either a single Websocket/Http URL, or a list of URLs
    :param str user: Username for Authentication
    :param str password: Password for Authentication
    :param int num_retries: Try x times to num_retries to a node on disconnect, -1 for indefinitely (default is 100)
    :param int num_retries_call: Repeat num_retries_call times a rpc call on node error (default is 5)
    :param int timeout: Timeout setting for https nodes (default is 60)
    :param bool autoconnect: When set to false, connection is performed on the first rpc call (default is True)
    :param bool use_condenser: Use the old condenser_api rpc protocol on nodes with version
        0.19.4 or higher. The settings has no effect on nodes with version of 0.19.3 or lower.
    :param dict custom_chains: custom chain which should be added to the known chains

    Available APIs:

          * database
          * network_node
          * network_broadcast

    Usage:

        .. code-block:: python

            from beemapi.graphenerpc import GrapheneRPC
            ws = GrapheneRPC("wss://steemd.pevo.science","","")
            print(ws.get_account_count())

            ws = GrapheneRPC("https://api.steemit.com","","")
            print(ws.get_account_count())

    .. note:: This class allows to call methods available via
              websocket. If you want to use the notification
              subsystem, please use ``GrapheneWebsocket`` instead.

    """

    def __init__(self, urls, user=None, password=None, **kwargs):
        """Init."""
        self.rpc_methods = {'offline': -1, 'ws': 0, 'jsonrpc': 1, 'wsappbase': 2, 'appbase': 3}
        self.current_rpc = self.rpc_methods["ws"]
        self._request_id = 0
        self.timeout = kwargs.get('timeout', 60)
        num_retries = kwargs.get("num_retries", 100)
        num_retries_call = kwargs.get("num_retries_call", 5)
        self.use_condenser = kwargs.get("use_condenser", False)
        self.disable_chain_detection = kwargs.get("disable_chain_detection", False)
        self.known_chains = known_chains
        custom_chain = kwargs.get("custom_chains", {})
        if len(custom_chain) > 0:
            for c in custom_chain:
                if c not in self.known_chains:
                    self.known_chains[c] = custom_chain[c]

        self.nodes = Nodes(urls, num_retries, num_retries_call)
        if self.nodes.working_nodes_count == 0:
            self.current_rpc = self.rpc_methods["offline"]

        self.user = user
        self.password = password
        self.ws = None
        self.url = None
        self.session = None
        self.rpc_queue = []
        if kwargs.get("autoconnect", True):
            self.rpcconnect()

    @property
    def num_retries(self):
        return self.nodes.num_retries

    @property
    def num_retries_call(self):
        return self.nodes.num_retries_call

    @property
    def error_cnt_call(self):
        return self.nodes.error_cnt_call

    @property
    def error_cnt(self):
        return self.nodes.error_cnt

    def get_request_id(self):
        """Get request id."""
        self._request_id += 1
        return self._request_id

    def next(self):
        """Switches to the next node url"""
        if self.ws:
            try:
                self.rpcclose()
            except Exception as e:
                log.warning(str(e))
        self.rpcconnect()

    def is_appbase_ready(self):
        """Check if node is appbase ready"""
        return self.current_rpc in [self.rpc_methods['wsappbase'], self.rpc_methods['appbase']]

    def get_use_appbase(self):
        """Returns True if appbase ready and appbase calls are set"""
        return not self.use_condenser and self.is_appbase_ready()

    def rpcconnect(self, next_url=True):
        """Connect to next url in a loop."""
        if self.nodes.working_nodes_count == 0:
            return
        while True:
            if next_url:
                self.url = next(self.nodes)
                self.nodes.reset_error_cnt_call()
                log.debug("Trying to connect to node %s" % self.url)
                if self.url[:3] == "wss":
                    self.ws = create_ws_instance(use_ssl=True)
                    self.ws.settimeout(self.timeout)
                    self.current_rpc = self.rpc_methods["ws"]
                elif self.url[:2] == "ws":
                    self.ws = create_ws_instance(use_ssl=False)
                    self.ws.settimeout(self.timeout)
                    self.current_rpc = self.rpc_methods["ws"]
                else:
                    self.ws = None
                    self.session = shared_session_instance()
                    self.current_rpc = self.rpc_methods["jsonrpc"]
                    self.headers = {'User-Agent': 'beem v%s' % (beem_version),
                                    'content-type': 'application/json; charset=utf-8'}
            try:
                if self.ws:
                    self.ws.connect(self.url)
                    self.rpclogin(self.user, self.password)
                if self.disable_chain_detection:
                    # Set to appbase rpc format
                    if self.current_rpc == self.rpc_methods['ws']:
                        self.current_rpc = self.rpc_methods['wsappbase']
                    else:
                        self.current_rpc = self.rpc_methods['appbase']
                    break
                try:
                    props = None
                    if not self.use_condenser:
                        props = self.get_config(api="database")
                    else:
                        props = self.get_config()
                except Exception as e:
                    if re.search("Bad Cast:Invalid cast from type", str(e)):
                        # retry with appbase
                        if self.current_rpc == self.rpc_methods['ws']:
                            self.current_rpc = self.rpc_methods['wsappbase']
                        else:
                            self.current_rpc = self.rpc_methods['appbase']
                        props = self.get_config(api="database")
                if props is None:
                    raise RPCError("Could not receive answer for get_config")
                if is_network_appbase_ready(props):
                    if self.ws:
                        self.current_rpc = self.rpc_methods["wsappbase"]
                    else:
                        self.current_rpc = self.rpc_methods["appbase"]
                break
            except KeyboardInterrupt:
                raise
            except Exception as e:
                self.nodes.increase_error_cnt()
                do_sleep = not next_url or (next_url and self.nodes.working_nodes_count == 1)
                self.nodes.sleep_and_check_retries(str(e), sleep=do_sleep)
                next_url = True

    def rpclogin(self, user, password):
        """Login into Websocket"""
        if self.ws and self.current_rpc == self.rpc_methods['ws'] and user and password:
            self.login(user, password, api="login_api")

    def rpcclose(self):
        """Close Websocket"""
        if self.ws is None:
            return
        # if self.ws.connected:
        self.ws.close()

    def request_send(self, payload):
        if self.user is not None and self.password is not None:
            response = self.session.post(self.url,
                                         data=payload,
                                         headers=self.headers,
                                         timeout=self.timeout,
                                         auth=(self.user, self.password))
        else:
            response = self.session.post(self.url,
                                         data=payload,
                                         headers=self.headers,
                                         timeout=self.timeout)
        if response.status_code == 401:
            raise UnauthorizedError
        return response

    def ws_send(self, payload):
        if self.ws is None:
            raise RPCConnection("No websocket available!")
        self.ws.send(payload)
        reply = self.ws.recv()
        return reply

    def version_string_to_int(self, network_version):
        version_list = network_version.split('.')
        return int(int(version_list[0]) * 1e8 + int(version_list[1]) * 1e4 + int(version_list[2]))

    def get_network(self, props=None):
        """ Identify the connected network. This call returns a
            dictionary with keys chain_id, core_symbol and prefix
        """
        if props is None:
            props = self.get_config(api="database")
        chain_id = None
        network_version = None
        is_hive = False
        for key in props:
            if key[-8:] == "CHAIN_ID":
                chain_id = props[key]
                is_hive = key[:4] == "HIVE"
            elif key[-18:] == "BLOCKCHAIN_VERSION":
                network_version = props[key]

        if chain_id is None:
            raise("Connecting to unknown network!")
        if is_hive:
            return self.known_chains["HIVE"]
        highest_version_chain = None
        for k, v in list(self.known_chains.items()):
            if v["chain_id"] == chain_id and self.version_string_to_int(v["min_version"]) <= self.version_string_to_int(network_version):
                if highest_version_chain is None:
                    highest_version_chain = v
                elif v["min_version"] == '0.19.5' and self.use_condenser:
                    highest_version_chain = v
                elif v["min_version"] == '0.0.0' and self.use_condenser:
                    highest_version_chain = v
                elif self.version_string_to_int(v["min_version"]) > self.version_string_to_int(highest_version_chain["min_version"]) and not self.use_condenser:
                    highest_version_chain = v
        if highest_version_chain is None:
            raise("Connecting to unknown network!")
        else:
            return highest_version_chain

    def _check_for_server_error(self, reply):
        """Checks for server error message in reply"""
        if re.search("Internal Server Error", reply) or re.search("500", reply):
            raise RPCErrorDoRetry("Internal Server Error")
        elif re.search("Not Implemented", reply) or re.search("501", reply):
            raise RPCError("Not Implemented")
        elif re.search("Bad Gateway", reply) or re.search("502", reply):
            raise RPCErrorDoRetry("Bad Gateway")
        elif re.search("Too Many Requests", reply) or re.search("429", reply):
            raise RPCErrorDoRetry("Too Many Requests")
        elif re.search("Service Temporarily Unavailable", reply) or re.search("Service Unavailable", reply) or re.search("503", reply):
            raise RPCErrorDoRetry("Service Temporarily Unavailable")
        elif re.search("Gateway Time-out", reply) or re.search("Gateway Timeout", reply) or re.search("504", reply):
            raise RPCErrorDoRetry("Gateway Time-out")
        elif re.search("HTTP Version not supported", reply) or re.search("505", reply):
            raise RPCError("HTTP Version not supported")
        elif re.search("Variant Also Negotiates", reply) or re.search("506", reply):
            raise RPCError("Variant Also Negotiates")
        elif re.search("Insufficient Storage", reply) or re.search("507", reply):
            raise RPCError("Insufficient Storage")
        elif re.search("Loop Detected", reply) or re.search("508", reply):
            raise RPCError("Loop Detected")
        elif re.search("Bandwidth Limit Exceeded", reply) or re.search("509", reply):
            raise RPCError("Bandwidth Limit Exceeded")
        elif re.search("Not Extended", reply) or re.search("510", reply):
            raise RPCError("Not Extended")
        elif re.search("Network Authentication Required", reply) or re.search("511", reply):
            raise RPCError("Network Authentication Required")
        else:
            raise RPCError("Client returned invalid format. Expected JSON!")

    def rpcexec(self, payload):
        """
        Execute a call by sending the payload.

        :param json payload: Payload data
        :raises ValueError: if the server does not respond in proper JSON format
        :raises RPCError: if the server returns an error
        """
        log.debug(json.dumps(payload))
        if self.nodes.working_nodes_count == 0:
            raise WorkingNodeMissing
        if self.url is None:
            raise RPCConnection("RPC is not connected!")
        reply = {}
        response = None
        while True:
            self.nodes.increase_error_cnt_call()
            try:
                if self.current_rpc == self.rpc_methods['ws'] or \
                   self.current_rpc == self.rpc_methods['wsappbase']:
                    reply = self.ws_send(json.dumps(payload, ensure_ascii=False).encode('utf8'))
                else:
                    response = self.request_send(json.dumps(payload, ensure_ascii=False).encode('utf8'))
                    reply = response.text
                if not bool(reply):
                    try:
                        self.nodes.sleep_and_check_retries("Empty Reply", call_retry=True)
                    except CallRetriesReached:
                        self.nodes.increase_error_cnt()
                        self.nodes.sleep_and_check_retries("Empty Reply", sleep=False, call_retry=False)
                        self.rpcconnect()
                else:
                    break
            except KeyboardInterrupt:
                raise
            except WebSocketConnectionClosedException as e:
                if self.nodes.num_retries_call_reached:
                    self.nodes.increase_error_cnt()
                    self.nodes.sleep_and_check_retries(str(e), sleep=False, call_retry=False)
                    self.rpcconnect()
                else:
                    # self.nodes.sleep_and_check_retries(str(e), sleep=True, call_retry=True)
                    self.rpcconnect(next_url=False)
            except ConnectionError as e:
                self.nodes.increase_error_cnt()
                self.nodes.sleep_and_check_retries(str(e), sleep=False, call_retry=False)
                self.rpcconnect()
            except WebSocketTimeoutException as e:
                self.nodes.increase_error_cnt()
                self.nodes.sleep_and_check_retries(str(e), sleep=False, call_retry=False)
                self.rpcconnect()
            except Exception as e:
                self.nodes.increase_error_cnt()
                self.nodes.sleep_and_check_retries(str(e), sleep=False, call_retry=False)
                self.rpcconnect()

        ret = {}
        try:
            if response is None:
                ret = json.loads(reply, strict=False, encoding="utf-8")
            else:
                ret = response.json()
        except ValueError:
            self._check_for_server_error(reply)

        log.debug(json.dumps(reply))

        if isinstance(ret, dict) and 'error' in ret:
            if 'detail' in ret['error']:
                raise RPCError(ret['error']['detail'])
            else:
                raise RPCError(ret['error']['message'])
        else:
            if isinstance(ret, list):
                ret_list = []
                for r in ret:
                    if isinstance(r, dict) and 'error' in r:
                        if 'detail' in r['error']:
                            raise RPCError(r['error']['detail'])
                        else:
                            raise RPCError(r['error']['message'])
                    elif isinstance(r, dict) and "result" in r:
                        ret_list.append(r["result"])
                    else:
                        ret_list.append(r)
                self.nodes.reset_error_cnt_call()
                return ret_list
            elif isinstance(ret, dict) and "result" in ret:
                self.nodes.reset_error_cnt_call()
                return ret["result"]
            elif isinstance(ret, int):
                raise RPCError("Client returned invalid format. Expected JSON! Output: %s" % (str(ret)))
            else:
                self.nodes.reset_error_cnt_call()
                return ret
        return ret

    # End of Deprecated methods
    ####################################################################
    def __getattr__(self, name):
        """Map all methods to RPC calls and pass through the arguments."""
        def method(*args, **kwargs):

            api_name = get_api_name(self.is_appbase_ready(), *args, **kwargs)
            if self.is_appbase_ready() and self.use_condenser and api_name != "bridge":
                api_name = "condenser_api"
            if (api_name is None):
                api_name = 'database_api'

            # let's be able to define the num_retries per query
            stored_num_retries_call = self.nodes.num_retries_call
            self.nodes.num_retries_call = kwargs.get("num_retries_call", stored_num_retries_call)
            add_to_queue = kwargs.get("add_to_queue", False)
            query = get_query(self.is_appbase_ready() and not self.use_condenser or api_name == "bridge", self.get_request_id(), api_name, name, args)
            if add_to_queue:
                self.rpc_queue.append(query)
                self.nodes.num_retries_call = stored_num_retries_call
                return None
            elif len(self.rpc_queue) > 0:
                self.rpc_queue.append(query)
                query = self.rpc_queue
                self.rpc_queue = []
            r = self.rpcexec(query)
            self.nodes.num_retries_call = stored_num_retries_call
            return r
        return method
