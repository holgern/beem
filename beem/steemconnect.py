# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import json
import urllib.parse
import requests
from .storage import configStorage as config
from beem.instance import shared_steem_instance


class SteemConnect(object):
    """ SteemConnect v2

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
            post = Comment("author/permlink", steem_instance=stm)
            post.upvote(voter="test")  # replace "test" with your account

    """

    def __init__(self, steem_instance=None, *args, **kwargs):
        self.steem = steem_instance or shared_steem_instance()
        self.access_token = None
        self.get_refresh_token = kwargs.get("get_refresh_token", False)
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

        return urllib.parse.urljoin(
            self.oauth_base_url,
            "authorize?" + urllib.parse.urlencode(params, safe=","))

    def get_access_token(self, code):
        post_data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.steem.wallet.getTokenForAccountName(self.client_id),
        }

        r = requests.post(
            urllib.parse.urljoin(self.sc2_api_url, "oauth2/token/"),
            data=post_data
        )

        return r.json()

    def me(self, username=None):
        if username:
            self.set_username(username)
        url = urllib.parse.urljoin(self.sc2_api_url, "me/")
        r = requests.post(url, headers=self.headers)
        return r.json()

    def set_access_token(self, access_token):
        """ Is needed for broadcast() and me()
        """
        self.access_token = access_token

    def set_username(self, username):
        """ Set a username for the next broadcast() or me operation()
            The necessary token is fetched from the wallet
        """
        self.access_token = self.steem.wallet.getTokenForAccountName(username)

    def broadcast(self, operations, username=None):
        """ Broadcast a operations

            Sample operations:

            .. code-block:: js

                [
                    [
                        'vote', {
                                    'voter': 'holger.random',
                                    'author': 'holger80',
                                    'permlink': 'does-the-steem-blockchain-comply-with-the-gdpr-and-european-privacy-laws',
                                    'weight': 10000
                                }
                    ]
                ]

        """
        url = urllib.parse.urljoin(self.sc2_api_url, "broadcast/")
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
            urllib.parse.urljoin(self.sc2_api_url, "oauth2/token/"),
            data=post_data,
        )

        return r.json()

    def revoke_token(self, access_token):
        post_data = {
            "access_token": access_token,
        }

        r = requests.post(
            urllib.parse.urljoin(self.sc2_api_url, "oauth2/token/revoke"),
            data=post_data
        )

        return r.json()

    def update_user_metadata(self, metadata):
        put_data = {
            "user_metadata": metadata,
        }
        r = requests.put(
            urllib.parse.urljoin(self.sc2_api_url, "me/"),
            data=put_data, headers=self.headers)

        return r.json()

    def hot_sign(self, operation, params, redirect_uri=None):
        """ Creates a link for broadcasting a operation

            :param str operation: operation name (e.g.: vote)
            :param dict params: operation dict params
        """

        if not isinstance(operation, str) or not isinstance(params, dict):
            raise ValueError("Invalid Request.")

        base_url = self.sc2_api_url.replace("/api", "")

        if redirect_uri:
            params.update({"redirect_uri": redirect_uri})

        params = urllib.parse.urlencode(params)
        url = urllib.parse.urljoin(base_url, "sign/%s" % operation)
        url += "?" + params

        return url
