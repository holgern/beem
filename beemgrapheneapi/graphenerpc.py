"""graphennewsrpc."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import next
from builtins import str
from builtins import object
from itertools import cycle
import json
import logging
import ssl
import sys
import threading
import re
import time
import warnings
from .exceptions import (
    UnauthorizedError, RPCConnection, RPCError, RPCErrorDoRetry, NumRetriesReached, CallRetriesReached
)
from .rpcutils import (
    is_network_appbase_ready, sleep_and_check_retries,
    get_api_name, get_query
)
from beemgraphenebase.version import version as beem_version
from beemgraphenebase.chains import known_chains

WEBSOCKET_MODULE = None
if not WEBSOCKET_MODULE:
    try:
        import websocket
        from websocket._exceptions import WebSocketConnectionClosedException
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
    :param int num_retries: Try x times to num_retries to a node on disconnect, -1 for indefinitely
    :param int num_retries_call: Repeat num_retries_call times a rpc call on node error (default is 5)
    :param int timeout: Timeout setting for https nodes (default is 60)
    :param bool autoconnect: When set to false, connection is performed on the first rpc call (default is True)

    Available APIs:

          * database
          * network_node
          * network_broadcast

    Usage:

        .. code-block:: python

            from beemgrapheneapi.graphenerpc import GrapheneRPC
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
        if isinstance(urls, str):
            url_list = re.split(r",|;", urls)
            self.n_urls = len(url_list)
            self.urls = cycle(url_list)
            if self.urls is None:
                self.n_urls = 1
                self.urls = cycle([urls])
        elif isinstance(urls, (list, tuple, set)):
            self.n_urls = len(urls)
            self.urls = cycle(urls)
        elif urls is not None:
            self.n_urls = 1
            self.urls = cycle([urls])
        else:
            self.n_urls = 0
            self.urls = None
            self.current_rpc = self.rpc_methods["offline"]
        self.user = user
        self.password = password
        self.ws = None
        self.url = None
        self.session = None
        self.rpc_queue = []
        self.timeout = kwargs.get('timeout', 60)
        self.num_retries = kwargs.get("num_retries", -1)
        self.use_condenser = kwargs.get("use_condenser", False)
        self.error_cnt = {}
        self.num_retries_call = kwargs.get("num_retries_call", 5)
        self.error_cnt_call = 0
        if kwargs.get("autoconnect", True):
            self.rpcconnect()

    def get_request_id(self):
        """Get request id."""
        self._request_id += 1
        return self._request_id

    def next(self):
        """Switches to the next node url"""
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                log.warning(str(e))
        self.rpcconnect()

    def is_appbase_ready(self):
        """Check if node is appbase ready"""
        return self.current_rpc >= 2

    def get_use_appbase(self):
        """Returns True if appbase ready and appbase calls are set"""
        return not self.use_condenser and self.is_appbase_ready()

    def rpcconnect(self, next_url=True):
        """Connect to next url in a loop."""
        if self.urls is None:
            return
        while True:
            if next_url:
                self.url = next(self.urls)
                self.error_cnt_call = 0
                if self.url not in self.error_cnt:
                    self.error_cnt[self.url] = 0
                log.debug("Trying to connect to node %s" % self.url)
                if self.url[:3] == "wss":
                    self.ws = create_ws_instance(use_ssl=True)
                    self.current_rpc = self.rpc_methods["ws"]
                elif self.url[:2] == "ws":
                    self.ws = create_ws_instance(use_ssl=False)
                    self.current_rpc = self.rpc_methods["ws"]
                else:
                    self.ws = None
                    self.session = shared_session_instance()
                    self.current_rpc = self.rpc_methods["jsonrpc"]
                    self.headers = {'User-Agent': 'beem v%s' % (beem_version),
                                    'content-type': 'application/json'}
            try:
                if self.ws:
                    self.ws.connect(self.url)
                    self.rpclogin(self.user, self.password)
                try:
                    props = None
                    if not self.use_condenser:
                        props = self.get_config(api="database")
                    else:
                        props = self.get_config()
                except Exception as e:
                    if re.search("Bad Cast:Invalid cast from type", str(e)):
                        self.current_rpc += 2
                        props = self.get_config(api="database")
                if props is None:
                    raise RPCError("Could not recieve answer for get_config")
                if is_network_appbase_ready(props):
                    if self.ws:
                        self.current_rpc = self.rpc_methods["wsappbase"]
                    else:
                        self.current_rpc = self.rpc_methods["appbase"]
                self.chain_params = self.get_network(props)
                break
            except KeyboardInterrupt:
                raise
            except Exception as e:
                self.error_cnt[self.url] += 1
                do_sleep = not next_url or (next_url and self.n_urls == 1)
                sleep_and_check_retries(self.num_retries, self.error_cnt[self.url], self.url, str(e), sleep=do_sleep)
                next_url = True

    def rpclogin(self, user, password):
        """Login into Websocket"""
        if self.ws and self.current_rpc == 0 and user and password:
            self.login(user, password, api="login_api")

    def rpcclose(self):
        """Close Websocket"""
        if self.ws:
            self.ws.close()

    def request_send(self, payload):
        response = self.session.post(self.url,
                                     data=payload,
                                     headers=self.headers,
                                     timeout=self.timeout,
                                     auth=(self.user, self.password))
        if response.status_code == 401:
            raise UnauthorizedError
        return response.text

    def ws_send(self, payload):
        self.ws.send(payload)
        reply = self.ws.recv()
        return reply

    def get_network(self, props=None):
        """ Identify the connected network. This call returns a
            dictionary with keys chain_id, core_symbol and prefix
        """
        if props is None:
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

    def _check_for_server_error(self, reply):
        """Checks for server error message in reply"""
        if re.search("Internal Server Error", reply) or re.search("500", reply):
            raise RPCErrorDoRetry("Internal Server Error")
        elif re.search("Not Implemented", reply) or re.search("501", reply):
            raise RPCError("Not Implemented")
        elif re.search("Bad Gateway", reply) or re.search("502", reply):
            raise RPCErrorDoRetry("Bad Gateway")
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
        if self.url is None:
            self.rpcconnect()
        reply = {}
        while True:
            self.error_cnt_call += 1
            try:
                if self.current_rpc == 0 or self.current_rpc == 2:
                    reply = self.ws_send(json.dumps(payload, ensure_ascii=False).encode('utf8'))
                else:
                    reply = self.request_send(json.dumps(payload, ensure_ascii=False).encode('utf8'))
                if not bool(reply):
                    try:
                        sleep_and_check_retries(self.num_retries_call, self.error_cnt_call, self.url, "Empty Reply", call_retry=True)
                    except CallRetriesReached:
                        self.error_cnt[self.url] += 1
                        sleep_and_check_retries(self.num_retries, self.error_cnt[self.url], self.url, "Empty Reply", sleep=False, call_retry=False)
                        self.rpcconnect()
                else:
                    break
            except KeyboardInterrupt:
                raise
            except WebSocketConnectionClosedException:
                # self.error_cnt[self.url] += 1
                self.rpcconnect(next_url=False)
            except ConnectionError as e:
                self.error_cnt[self.url] += 1
                sleep_and_check_retries(self.num_retries, self.error_cnt[self.url], self.url, str(e), sleep=False, call_retry=False)
                self.rpcconnect()
            except Exception as e:
                self.error_cnt[self.url] += 1
                sleep_and_check_retries(self.num_retries, self.error_cnt[self.url], self.url, str(e), sleep=False, call_retry=False)
                self.rpcconnect()

        ret = {}
        try:
            ret = json.loads(reply, strict=False)
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
                self.error_cnt_call = 0
                return ret_list
            elif isinstance(ret, dict) and "result" in ret:
                self.error_cnt_call = 0
                return ret["result"]
            elif isinstance(ret, int):
                raise RPCError("Client returned invalid format. Expected JSON! Output: %s" % (str(ret)))
            else:
                self.error_cnt_call = 0
                return ret
        return ret

    # End of Deprecated methods
    ####################################################################
    def __getattr__(self, name):
        """Map all methods to RPC calls and pass through the arguments."""
        def method(*args, **kwargs):

            api_name = get_api_name(self.is_appbase_ready(), *args, **kwargs)
            if self.is_appbase_ready() and self.use_condenser:
                api_name = "condenser_api"

            # let's be able to define the num_retries per query
            self.num_retries_call = kwargs.get("num_retries_call", self.num_retries_call)
            add_to_queue = kwargs.get("add_to_queue", False)
            query = get_query(self.is_appbase_ready() and not self.use_condenser, self.get_request_id(), api_name, name, args)
            if add_to_queue:
                self.rpc_queue.append(query)
                return None
            elif len(self.rpc_queue) > 0:
                self.rpc_queue.append(query)
                query = self.rpc_queue
                self.rpc_queue = []
            r = self.rpcexec(query)
            return r
        return method
