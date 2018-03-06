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

WEBSOCKET_MODULE = None
if not WEBSOCKET_MODULE:
    try:
        import websocket
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


class UnauthorizedError(Exception):
    """UnauthorizedError Exception."""

    pass


class RPCConnection(Exception):
    """RPCConnection Exception."""

    pass


class RPCError(Exception):
    """RPCError Exception."""

    pass


class NumRetriesReached(Exception):
    """NumRetriesReached Exception."""

    pass


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
        self.rpc_methods = {'ws': 0, 'jsonrpc': 1, 'appbase': 2, 'wsappbase': 3}
        self.current_rpc = self.rpc_methods["ws"]
        self._request_id = 0
        if isinstance(urls, list):
            self.urls = cycle(urls)
        else:
            self.urls = cycle([urls])
        self.user = user
        self.password = password
        self.ws = None
        self.num_retries = kwargs.get("num_retries", -1)

        self.rpcconnect()
        self.register_apis()

    def get_request_id(self):
        """Get request id."""
        self._request_id += 1
        return self._request_id

    def rpcconnect(self):
        """Connect to next url in a loop."""
        cnt = 0
        while True:
            cnt += 1
            self.url = next(self.urls)
            log.debug("Trying to connect to node %s" % self.url)
            if self.url[:3] == "wss":
                if WEBSOCKET_MODULE is None:
                    raise Exception()
                sslopt_ca_certs = {'cert_reqs': ssl.CERT_NONE}
                self.ws = websocket.WebSocket(sslopt=sslopt_ca_certs)
                self.current_rpc = self.rpc_methods["ws"]
            elif self.url[:3] == "ws":
                if WEBSOCKET_MODULE is None:
                    raise Exception()
                self.ws = websocket.WebSocket()
                self.current_rpc = self.rpc_methods["ws"]
            else:
                if REQUEST_MODULE is None:
                    raise Exception()
                self.ws = None
                self.current_rpc = self.rpc_methods["jsonrpc"]
                self.headers = {'User-Agent': 'beem v0.19.11',
                                'content-type': 'application/json'}

            try:
                if not self.ws:
                    break
                else:
                    self.ws.connect(self.url)
                    break
            except KeyboardInterrupt:
                raise
            except Exception:
                if (self.num_retries >= 0 and cnt > self.num_retries):
                    raise NumRetriesReached()

                sleeptime = (cnt - 1) * 2 if cnt < 10 else 10
                if sleeptime:
                    log.warning(
                        "Lost connection to node during wsconnect(): %s (%d/%d) "
                        % (self.url, cnt, self.num_retries) +
                        "Retrying in %d seconds" % sleeptime
                    )
                    time.sleep(sleeptime)
        try:
            props = self.get_config(api="database")
        except:
            if self.ws:
                self.current_rpc = self.rpc_methods["wsappbase"]
            else:
                self.current_rpc = self.rpc_methods["appbase"]
            props = self.get_config(api="database")
        if "STEEMIT_CHAIN_ID" in props:
            network_version = props['STEEMIT_BLOCKCHAIN_VERSION']
        elif "STEEM_CHAIN_ID" in props:
            network_version = props['STEEM_BLOCKCHAIN_VERSION']
        if self.ws and network_version >= '0.19.4':
            self.current_rpc = self.rpc_methods["wsappbase"]
        elif not self.ws and network_version >= '0.19.4':
            self.current_rpc = self.rpc_methods["appbase"]
        if self.ws and self.current_rpc == 0:
            self.login(self.user, self.password, api_id=1)

    def rpcclose(self):
        if self.ws:
            self.ws.close()

    def register_apis(self):
        """Register apis."""
        if self.current_rpc < 2:
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

    def get_query(self, api_name, name, args):
        if self.current_rpc < 2:
            query = {"method": "call",
                     "params": [api_name, name, list(args)],
                     "jsonrpc": "2.0",
                     "id": self.get_request_id()}
        else:
            args = json.loads(json.dumps(args))
            # print(args)
            if len(args) == 1 and isinstance(args[0], dict):
                query = {"method": api_name + "." + name,
                         "params": args[0],
                         "jsonrpc": "2.0",
                         "id": self.get_request_id()}
            elif args:
                query = {"method": "call",
                         "params": [api_name, name, list(args)],
                         "jsonrpc": "2.0",
                         "id": self.get_request_id()}
            elif api_name == "condenser_api":
                query = {"method": api_name + "." + name,
                         "jsonrpc": "2.0",
                         "params": [],
                         "id": self.get_request_id()}
            else:
                query = {"method": api_name + "." + name,
                         "jsonrpc": "2.0",
                         "params": {},
                         "id": self.get_request_id()}
        return query

    def get_api_name(self, *args, **kwargs):
        if self.current_rpc < 2:
            # Sepcify the api to talk to
            if "api_id" not in kwargs:
                if ("api" in kwargs):
                    api_name = kwargs["api"].replace("_api", "") + "_api"
                else:
                    api_id = 0
                    api_name = None
            else:
                api_id = kwargs["api_id"]
                api_name = api_id
        else:
            # Sepcify the api to talk to
            if "api_id" not in kwargs:
                if ("api" in kwargs):
                    if kwargs["api"] != "jsonrpc":
                        api_name = kwargs["api"].replace("_api", "") + "_api"
                    else:
                        api_name = kwargs["api"]
                else:
                    api_name = "condenser_api"
            else:
                api_name = "condenser_api"
        return api_name

    def rpcexec(self, payload):
        """
        Execute a call by sending the payload.

        :param json payload: Payload data
        :raises ValueError: if the server does not respond in proper JSON format
        :raises RPCError: if the server returns an error
        """
        log.debug(json.dumps(payload))
        cnt = 0
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
            except Exception:
                if (self.num_retries > -1 and
                        cnt > self.num_retries):
                    raise NumRetriesReached()
                sleeptime = (cnt - 1) * 2 if cnt < 10 else 10
                if sleeptime:
                    log.warning(
                        "Lost connection to node during rpcexec(): %s (%d/%d) "
                        % (self.url, cnt, self.num_retries) +
                        "Retrying in %d seconds" % sleeptime
                    )
                    time.sleep(sleeptime)

                # retry
                try:
                    self.rpcclose()
                    time.sleep(sleeptime)
                    self.rpcconnect()
                    self.register_apis()
                except Exception:
                    pass

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
            return ret["result"]

    # End of Deprecated methods
    ####################################################################
    def __getattr__(self, name):
        """Map all methods to RPC calls and pass through the arguments."""
        def method(*args, **kwargs):

            api_name = self.get_api_name(*args, **kwargs)

            # let's be able to define the num_retries per query
            self.num_retries = kwargs.get("num_retries", self.num_retries)
            query = self.get_query(api_name, name, args)
            r = self.rpcexec(query)
            return r
        return method
