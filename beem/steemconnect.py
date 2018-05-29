# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import json
try:
    from urllib.parse import urlparse, urlencode, urljoin
except ImportError:
    from urlparse import urlparse, urljoin
    from urllib import urlencode
import requests
from .storage import configStorage as config
from beem.instance import shared_steem_instance


class SteemConnect(object):
    """ SteemConnect

        :param str scope: comma seperate string with scopes
            login,offline,vote,comment,delete_comment,comment_options,custom_json,claim_reward_balance


        .. code-block:: python

            # Run the login_app in examples and login with a account
            from beem import Steem
            from beem.steemconnect import SteemConnect
            from beem.comment import Comment
            sc2 = SteemConnect(client_id="beem.app")
            steem = Steem(steemconnect=sc2)
            steem.wallet.unlock("supersecret-passphrase")
            post = Comment("author/permlink", steem_instance=steem)
            post.upvote(voter="test")  # replace "test" with your account

        Examples for creating steemconnect v2 urls for broadcasting in browser:
        .. testoutput::

            from beem import Steem
            from beem.account import Account
            from beem.steemconnect import SteemConnect
            from pprint import pprint
            steem = Steem(nobroadcast=True, unsigned=True)
            sc2 = SteemConnect(steem_instance=steem)
            acc = Account("test", steem_instance=steem)
            pprint(sc2.url_from_tx(acc.transfer("test1", 1, "STEEM", "test")))

        .. testcode::

            'https://v2.steemconnect.com/sign/transfer?from=test&to=test1&amount=1.000+STEEM&memo=test'

        .. testoutput::

            from beem import Steem
            from beem.transactionbuilder import TransactionBuilder
            from beembase import operations
            from beem.steemconnect import SteemConnect
            from pprint import pprint
            stm = Steem()
            tx = TransactionBuilder(steem_instance=stm)
            op = operations.Transfer(**{"from": 'test',
                                        "to": 'test1',
                                        "amount": '1.000 STEEM',
                                        "memo": 'test'})
            tx.appendOps(op)
            pprint(sc2.url_from_tx(tx)

        .. testcode::

            'https://v2.steemconnect.com/sign/transfer?from=test&to=test1&amount=1.000+STEEM&memo=test'

    """

    def __init__(self, steem_instance=None, *args, **kwargs):
        self.steem = steem_instance or shared_steem_instance()
        self.access_token = None
        self.get_refresh_token = kwargs.get("get_refresh_token", False)
        self.hot_sign = kwargs.get("hot_sign", False)
        self.hot_sign_redirect_uri = kwargs.get("hot_sign_redirect_uri", None)
        self.client_id = kwargs.get("client_id", config["sc2_client_id"])
        self.scope = kwargs.get("scope", config["sc2_scope"])
        self.oauth_base_url = kwargs.get("oauth_base_url", config["oauth_base_url"])
        self.sc2_api_url = kwargs.get("sc2_api_url", config["sc2_api_url"])

    @property
    def headers(self):
        return {'Authorization': self.access_token}

    def get_login_url(self, redirect_uri):
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": self.scope,
        }
        if self.get_refresh_token:
            params.update({
                "response_type": "code",
            })

        return urljoin(
            self.oauth_base_url,
            "authorize?" + urlencode(params, safe=","))

    def get_access_token(self, code):
        post_data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.steem.wallet.getTokenForAccountName(self.client_id),
        }

        r = requests.post(
            urljoin(self.sc2_api_url, "oauth2/token/"),
            data=post_data
        )

        return r.json()

    def me(self, username=None):
        if username:
            self.set_username(username)
        url = urljoin(self.sc2_api_url, "me/")
        r = requests.post(url, headers=self.headers)
        return r.json()

    def set_access_token(self, access_token):
        """ Is needed for broadcast() and me()
        """
        self.access_token = access_token

    def set_username(self, username, permission):
        """ Set a username for the next broadcast() or me operation()
            The necessary token is fetched from the wallet
        """
        if self.hot_sign or permission != "posting":
            self.access_token = None
            return
        self.access_token = self.steem.wallet.getTokenForAccountName(username)

    def broadcast(self, operations, username=None):
        """ Broadcast a operations

            Sample operations:

            .. code-block:: js

                [
                    [
                        'vote', {
                                    'voter': 'gandalf',
                                    'author': 'gtg',
                                    'permlink': 'steem-pressure-4-need-for-speed',
                                    'weight': 10000
                                }
                    ]
                ]

        """
        url = urljoin(self.sc2_api_url, "broadcast/")
        data = {
            "operations": operations,
        }
        if username:
            self.set_username(username)
        headers = self.headers.copy()
        headers.update({
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        })

        r = requests.post(url, headers=headers, data=json.dumps(data))
        try:
            return r.json()
        except ValueError:
            return r.content

    def refresh_access_token(self, code, scope):
        post_data = {
            "grant_type": "refresh_token",
            "refresh_token": code,
            "client_id": self.client_id,
            "client_secret": self.steem.wallet.getTokenForAccountName(self.client_id),
            "scope": scope,
        }

        r = requests.post(
            urljoin(self.sc2_api_url, "oauth2/token/"),
            data=post_data,
        )

        return r.json()

    def revoke_token(self, access_token):
        post_data = {
            "access_token": access_token,
        }

        r = requests.post(
            urljoin(self.sc2_api_url, "oauth2/token/revoke"),
            data=post_data
        )

        return r.json()

    def update_user_metadata(self, metadata):
        put_data = {
            "user_metadata": metadata,
        }
        r = requests.put(
            urljoin(self.sc2_api_url, "me/"),
            data=put_data, headers=self.headers)

        return r.json()

    def url_from_tx(self, tx, redirect_uri=None):
        """ Creates a link for broadcasting a operation

            :param dict tx: inlcudes the operation, which should be broadcast
            :param dict params: operation dict params
            :param str redirect_uri: Redirects to this uri, when set
        """
        if not isinstance(tx, dict):
            tx = tx.json()
        if "operations" not in tx or not tx["operations"]:
            return ''
        urls = []
        operations = tx["operations"]
        for op in operations:
            urls.append(self.create_hot_sign_url(op[0], op[1], redirect_uri=redirect_uri))
        if len(urls) == 1:
            return urls[0]
        else:
            return urls

    def create_hot_sign_url(self, operation, params, redirect_uri=None):
        """ Creates a link for broadcasting a operation

            :param str operation: operation name (e.g.: vote)
            :param dict params: operation dict params
            :param str redirect_uri: Redirects to this uri, when set
        """

        if not isinstance(operation, str) or not isinstance(params, dict):
            raise ValueError("Invalid Request.")

        base_url = self.sc2_api_url.replace("/api", "")

        if not redirect_uri and self.hot_sign_redirect_uri:
            redirect_uri = self.hot_sign_redirect_uri
        if redirect_uri:
            params.update({"redirect_uri": redirect_uri})

        params = urlencode(params)
        url = urljoin(base_url, "sign/%s" % operation)
        url += "?" + params

        return url


# https://steemconnect.com/authorize/@steemauto/?redirect_uri=https://steemauto.com/dash.php
# https://steemconnect.com/oauth2/authorize?client_id=steem.app&redirect_uri=https://steemauto.com/callback.php&scope=login
