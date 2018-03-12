"""graphennewsrpc."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import next
from builtins import object
from itertools import cycle
import json
import logging
import ssl
import sys
import threading
import time
import warnings
from .rpcutils import (
    is_network_appbase_ready, sleep_and_check_retries,
    get_api_name, get_query, UnauthorizedError,
    RPCConnection, RPCError, NumRetriesReached
)

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
        REQUEST_MODULE = "requests"
    except ImportError:
        REQUEST_MODULE = None


log = logging.getLogger(__name__)


class GrapheneRPC(object):
    """
    This class allows to call API methods synchronously, without callbacks.

    It logs in and registers to the APIs:

    * database
    * history

    :param str urls: Either a single Websocket/Http URL, or a list of URLs
    :param str user: Username for Authentication
    :param str password: Password for Authentication
    :param Array apis: List of APIs to register to (default: ["database", "network_broadcast"])
    :param int num_retries: Try x times to num_retries to a node on disconnect, -1 for indefinitely

    Available APIs

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

        ws = GrapheneRPC("https://api.steemitstage.com","","")
        print(ws.get_account_count())

    .. note:: This class allows to call methods available via
              websocket. If you want to use the notification
              subsystem, please use ``GrapheneWebsocket`` instead.

    """

    def __init__(self, urls, user="", password="", **kwargs):
        """Init."""
        self.api_id = {}
        self.rpc_methods = {'offline': -1, 'ws': 0, 'jsonrpc': 1, 'appbase': 2, 'wsappbase': 3}
        self.current_rpc = self.rpc_methods["ws"]
        self._request_id = 0
        if isinstance(urls, list):
            self.urls = cycle(urls)
        elif urls is not None:
            self.urls = cycle([urls])
        else:
            self.urls = None
            self.current_rpc = self.rpc_methods["offline"]
        self.user = user
        self.password = password
        self.ws = None
        self.rpc_queue = []
        self.num_retries = kwargs.get("num_retries", -1)

        self.rpcconnect()
        self.register_apis()

    def get_request_id(self):
        """Get request id."""
        self._request_id += 1
        return self._request_id

    def is_appbase_ready(self):
        """Check if node is appbase ready"""
        return self.current_rpc >= 2

    def rpcconnect(self, next_url=True):
        """Connect to next url in a loop."""
        cnt = 0
        if self.urls is None:
            return
        while True:
            cnt += 1 
            if next_url:                
                self.url = next(self.urls)
                log.debug("Trying to connect to node %s" % self.url)
                if self.url[:3] == "wss":
                    if WEBSOCKET_MODULE is None:
                        raise Exception()
                    sslopt_ca_certs = {'cert_reqs': ssl.CERT_NONE}
                    self.ws = websocket.WebSocket(sslopt=sslopt_ca_certs, enable_multithread=True)
                    self.current_rpc = self.rpc_methods["ws"]
                elif self.url[:3] == "ws":
                    if WEBSOCKET_MODULE is None:
                        raise Exception()
                    self.ws = websocket.WebSocket(enable_multithread=True)
                    self.current_rpc = self.rpc_methods["ws"]
                else:
                    if REQUEST_MODULE is None:
                        raise Exception()
                    self.ws = None
                    self.current_rpc = self.rpc_methods["jsonrpc"]
                    self.headers = {'User-Agent': 'beem v0.19.14',
                                    'content-type': 'application/json'}

            try:
                if not self.ws:
                    break
                else:
                    self.ws.connect(self.url)
                    break
            except KeyboardInterrupt:
                raise
            except Exception as e:
                log.critical("Error: {}\n".format(str(e)))
                sleep_and_check_retries(self.num_retries, cnt, self.url)
                next_url = True
        try:
            props = self.get_config(api="database")
        except:
            if self.ws:
                self.current_rpc = self.rpc_methods["wsappbase"]
            else:
                self.current_rpc = self.rpc_methods["appbase"]
            props = self.get_config(api="database")
        if is_network_appbase_ready(props):
            if self.ws:
                self.current_rpc = self.rpc_methods["wsappbase"]
            else:
                self.current_rpc = self.rpc_methods["appbase"]
        self.rpclogin(self.user, self.password)

    def rpclogin(self, user, password):
        """Login into Websocket"""
        if self.ws and self.current_rpc == 0:
            self.login(user, password, api_id=1)

    def rpcclose(self):
        """Close Websocket"""
        if self.ws:
            self.ws.close()

    def register_apis(self):
        """Register apis."""
        if self.current_rpc >= 0 and self.current_rpc < 2:
            self.api_id["database"] = self.get_api_by_name("database_api", api_id=1)
            self.api_id["network_broadcast"] = self.get_api_by_name("network_broadcast_api", api_id=1)

    def request_send(self, payload):
        response = requests.post(self.url,
                                 data=payload,
                                 headers=self.headers,
                                 auth=(self.user, self.password))
        if response.status_code == 401:
            raise UnauthorizedError
        return response.text

    def ws_send(self, payload):
        self.ws.send(payload)
        reply = self.ws.recv()
        return reply

    def rpcexec(self, payload):
        """
        Execute a call by sending the payload.

        :param json payload: Payload data
        :raises ValueError: if the server does not respond in proper JSON format
        :raises RPCError: if the server returns an error
        """
        log.debug(json.dumps(payload))
        cnt = 0
        reply = {}
        while True:
            cnt += 1

            try:
                if self.current_rpc == 0 or self.current_rpc == 3:
                    reply = self.ws_send(json.dumps(payload, ensure_ascii=False).encode('utf8'))
                else:
                    reply = self.request_send(json.dumps(payload, ensure_ascii=False).encode('utf8'))
                break
            except KeyboardInterrupt:
                raise
            except WebSocketConnectionClosedException:
                self.rpcconnect(next_url=False)
                self.register_apis()                
            except Exception as e:
                log.critical("Error: {}\n".format(str(e)))
                sleep_and_check_retries(self.num_retries, cnt, self.url)
                # retry
                self.rpcconnect()
                self.register_apis()

        ret = {}
        try:
            ret = json.loads(reply, strict=False)
        except ValueError:
            raise ValueError("Client returned invalid format. Expected JSON!")

        log.debug(json.dumps(reply))

        if 'error' in ret:
            if 'detail' in ret['error']:
                raise RPCError(ret['error']['detail'])
            else:
                raise RPCError(ret['error']['message'])
        else:
            if isinstance(ret, list):
                ret_list = []
                for r in ret:
                    if 'error' in ret:
                        if 'detail' in ret['error']:
                            raise RPCError(ret['error']['detail'])
                        else:
                            raise RPCError(ret['error']['message'])
                    else:
                        ret_list.append(r["result"])
                return ret_list
            else:
                return ret["result"]

    # End of Deprecated methods
    ####################################################################
    def __getattr__(self, name):
        """Map all methods to RPC calls and pass through the arguments."""
        def method(*args, **kwargs):

            api_name = get_api_name(self.is_appbase_ready(), *args, **kwargs)

            # let's be able to define the num_retries per query
            self.num_retries = kwargs.get("num_retries", self.num_retries)
            add_to_queue = kwargs.get("add_to_queue", False)
            query = get_query(self.is_appbase_ready(), self.get_request_id(), api_name, name, args)
            if add_to_queue:
                self.rpc_queue.append(query)
                return None
            elif len(self.rpc_queue) > 0:
                self.rpc_queue.append(query)
                query = self.rpc_queue
                self.rpc_queue = []
            if isinstance(query, list):
                self._request_id += len(query) - 1
            r = self.rpcexec(query)
            return r
        return method
