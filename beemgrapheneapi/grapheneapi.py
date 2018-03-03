"""graphenapi."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import object
import json
import logging
import sys
log = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    raise ImportError("Missing dependency: python-requests")


class UnauthorizedError(Exception):
    """UnauthorizedError Exception."""

    pass


class RPCError(Exception):
    """RPCError Exception."""

    pass


class RPCConnection(Exception):
    """RPCConnection Exception."""

    pass


class GrapheneAPI(object):
    """
    Graphene JSON-HTTP-RPC API.

    This class serves as an abstraction layer for easy use of the
    Grapehene API.

    :param str host: Host of the API server
    :param int port: Port to connect to
    :param str username: Username for Authentication (if required,
                         defaults to "")
    :param str password: Password for Authentication (if required,
                         defaults to "")

    All RPC commands of the Graphene client are exposed as methods
    in the class ``grapheneapi``. Once an instance of GrapheneAPI is
    created with host, port, username, and password, e.g.,

    .. code-block:: python

        from grapheneapi import GrapheneAPI
        rpc = GrapheneAPI("localhost", 8092, "", "")

    any call available to that port can be issued using the instance
    via the syntax rpc.*command*(*parameters*). Example:

    .. code-block:: python

        rpc.info()

    .. note:: A distinction has to be made whether the connection is
              made to a **witness/full node** which handles the
              blockchain and P2P network, or a **cli-wallet** that
              handles wallet related actions! The available commands
              differ drastically!

    If you are connected to a wallet, you can simply initiate a transfer with:

    .. code-block:: python

        res = client.transfer("sender","receiver","5", "USD", "memo", True);

    Again, the witness node does not offer access to construct any transactions,
    and hence the calls available to the witness-rpc can be seen as read-only for
    the blockchain.
    """

    def __init__(self, host, port, username="", password=""):
        """init."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.headers = {'content-type': 'application/json'}

    def rpcexec(self, payload):
        """
        Manual execute a command on API (internally used).

        param str payload: The payload containing the request
        return: Servers answer to the query
        rtype: json
        raises RPCConnection: if no connction can be made
        raises UnauthorizedError: if the user is not authorized
        raise ValueError: if the API returns a non-JSON formated answer

        It is not recommended to use this method directly, unless
        you know what you are doing. All calls available to the API
        will be wrapped to methods directly::

            info -> grapheneapi.info()
        """
        try:
            response = requests.post("http://{}:{}/rpc".format(self.host,
                                                               self.port),
                                     data=json.dumps(payload, ensure_ascii=False).encode('utf8'),
                                     headers=self.headers,
                                     auth=(self.username, self.password))
            if response.status_code == 401:
                raise UnauthorizedError
            ret = json.loads(response.text)
            if 'error' in ret:
                if 'detail' in ret['error']:
                    raise RPCError(ret['error']['detail'])
                else:
                    raise RPCError(ret['error']['message'])
        except requests.exceptions.RequestException:
            raise RPCConnection("Error connecting to Client!")
        except UnauthorizedError:
            raise UnauthorizedError("Invalid login credentials!")
        except ValueError:
            raise ValueError("Client returned invalid format. Expected JSON!")
        except RPCError as err:
            raise err
        else:
            return ret["result"]

    def __getattr__(self, name):
        """Map all methods to RPC calls and pass through the arguments."""
        def method(*args):
            query = {"method": name,
                     "params": args,
                     "jsonrpc": "2.0",
                     "id": 0}
            r = self.rpcexec(query)
            return r
        return method
