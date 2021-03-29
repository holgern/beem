# -*- coding: utf-8 -*-
import json
try:
    from urllib.parse import urlparse, urlencode, urljoin
except ImportError:
    from urlparse import urlparse, urljoin
    from urllib import urlencode
import requests
import logging
from six import PY2
from beem.instance import shared_blockchain_instance
from beem.amount import Amount
from beem.exceptions import (
    MissingKeyError,
    WalletExists
)
from beemstorage.exceptions import KeyAlreadyInStoreException, WalletLocked

log = logging.getLogger(__name__)


class HiveSigner(object):
    """ HiveSigner

        :param str scope: comma separated string with scopes
            login,offline,vote,comment,delete_comment,comment_options,custom_json,claim_reward_balance


        .. code-block:: python

            # Run the login_app in examples and login with a account
            from beem import Steem
            from beem.HiveSigner import HiveSigner
            from beem.comment import Comment
            hs = HiveSigner(client_id="beem.app")
            steem = Steem(HiveSigner=hs)
            steem.wallet.unlock("supersecret-passphrase")
            post = Comment("author/permlink", blockchain_instance=steem)
            post.upvote(voter="test")  # replace "test" with your account

        Examples for creating HiveSigner urls for broadcasting in browser:

        .. testoutput::

            from beem import Steem
            from beem.account import Account
            from beem.HiveSigner import HiveSigner
            from pprint import pprint
            steem = Steem(nobroadcast=True, unsigned=True)
            hs = HiveSigner(blockchain_instance=steem)
            acc = Account("test", blockchain_instance=steem)
            pprint(hs.url_from_tx(acc.transfer("test1", 1, "HIVE", "test")))

        .. testcode::

            'https://hivesigner.com/sign/transfer?from=test&to=test1&amount=1.000+HIVE&memo=test'

        .. testoutput::

            from beem import Steem
            from beem.transactionbuilder import TransactionBuilder
            from beembase import operations
            from beem.HiveSigner import HiveSigner
            from pprint import pprint
            stm = Steem(nobroadcast=True, unsigned=True)
            hs = HiveSigner(blockchain_instance=stm)
            tx = TransactionBuilder(blockchain_instance=stm)
            op = operations.Transfer(**{"from": 'test',
                                        "to": 'test1',
                                        "amount": '1.000 HIVE',
                                        "memo": 'test'})
            tx.appendOps(op)
            pprint(hs.url_from_tx(tx.json()))

        .. testcode::

            'https://hivesigner.com/sign/transfer?from=test&to=test1&amount=1.000+HIVE&memo=test'

    """

    def __init__(self, blockchain_instance=None, *args, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        self.access_token = None
        config = self.blockchain.config
        self.get_refresh_token = kwargs.get("get_refresh_token", False)
        self.hot_sign_redirect_uri = kwargs.get("hot_sign_redirect_uri", config["hot_sign_redirect_uri"])
        if self.hot_sign_redirect_uri == "":
            self.hot_sign_redirect_uri = None
        self.client_id = kwargs.get("client_id", config["hs_client_id"])
        self.scope = kwargs.get("scope", "login")
        self.hs_oauth_base_url = kwargs.get("hs_oauth_base_url", config["hs_oauth_base_url"])
        self.hs_api_url = kwargs.get("hs_api_url", config["hs_api_url"])

        if "token" in kwargs and len(kwargs["token"]) > 0:
            from beemstorage import InRamPlainTokenStore
            self.store = InRamPlainTokenStore()
            token = kwargs["token"]
            self.set_access_token(token)
            name = self.me()["user"]
            self.setToken({name: token})
        else:
            """ If no keys are provided manually we load the SQLite
                keyStorage
            """
            from beemstorage import SqliteEncryptedTokenStore
            self.store = kwargs.get(
                "token_store",
                SqliteEncryptedTokenStore(config=config, **kwargs),
            )

    @property
    def headers(self):
        return {'Authorization': self.access_token}

    def setToken(self, loadtoken):
        """ This method is strictly only for in memory token that are
            passed to Wallet/Steem with the ``token`` argument
        """
        log.debug(
            "Force setting of private token. Not using the wallet database!")
        if not isinstance(loadtoken, (dict)):
            raise ValueError("token must be a dict variable!")
        for name in loadtoken:
            self.store.add(loadtoken[name], name)

    def is_encrypted(self):
        """ Is the key store encrypted?
        """
        return self.store.is_encrypted()

    def unlock(self, pwd):
        """ Unlock the wallet database
        """
        unlock_ok = None
        if self.store.is_encrypted():
            unlock_ok = self.store.unlock(pwd)
        return unlock_ok

    def lock(self):
        """ Lock the wallet database
        """
        lock_ok = False
        if self.store.is_encrypted():
            lock_ok =  self.store.lock()       
        return lock_ok

    def unlocked(self):
        """ Is the wallet database unlocked?
        """
        unlocked = True
        if self.store.is_encrypted():
            unlocked = not self.store.locked()   
        return unlocked

    def locked(self):
        """ Is the wallet database locked?
        """
        if self.store.is_encrypted():
            return self.store.locked()
        else:
            return False

    def changePassphrase(self, new_pwd):
        """ Change the passphrase for the wallet database
        """
        self.store.change_password(new_pwd)

    def created(self):
        """ Do we have a wallet database already?
        """
        if len(self.store.getPublicKeys()):
            # Already keys installed
            return True
        else:
            return False

    def create(self, pwd):
        """ Alias for :func:`newWallet`

            :param str pwd: Passphrase for the created wallet
        """
        self.newWallet(pwd)

    def newWallet(self, pwd):
        """ Create a new wallet database

            :param str pwd: Passphrase for the created wallet
        """
        if self.created():
            raise WalletExists("You already have created a wallet!")
        self.store.unlock(pwd)

    def addToken(self, name, token):
        if str(name) in self.store:
            raise KeyAlreadyInStoreException("Token already in the store")
        self.store.add(str(token), str(name))

    def getTokenForAccountName(self, name):
        """ Obtain the private token for a given public name

            :param str name: Public name
        """      
        if str(name) not in self.store:
            raise MissingKeyError
        return self.store.getPrivateKeyForPublicKey(str(name))

    def removeTokenFromPublicName(self, name):
        """ Remove a token from the wallet database

            :param str name: token to be removed
        """
        self.store.delete(str(name))

    def getPublicNames(self):
        """ Return all installed public token
        """
        if self.store is None:
            return
        return self.store.getPublicNames()

    def get_login_url(self, redirect_uri, **kwargs):
        """ Returns a login url for receiving token from HiveSigner
        """
        client_id = kwargs.get("client_id", self.client_id)
        scope = kwargs.get("scope", self.scope)
        get_refresh_token = kwargs.get("get_refresh_token", self.get_refresh_token)
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
        }
        if get_refresh_token:
            params.update({
                "response_type": "code",
            })
        if PY2:
            return urljoin(
                self.hs_oauth_base_url,
                "authorize?" + urlencode(params).replace('%2C', ','))
        else:
            return urljoin(
                self.hs_oauth_base_url,
                "authorize?" + urlencode(params, safe=","))

    def get_access_token(self, code):
        post_data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.getTokenForAccountName(self.client_id),
        }

        r = requests.post(
            urljoin(self.hs_api_url, "oauth2/token/"),
            data=post_data
        )

        return r.json()

    def me(self, username=None):
        """ Calls the me function from HiveSigner

        .. code-block:: python

            from beem.HiveSigner import HiveSigner
            hs = HiveSigner()
            hs.steem.wallet.unlock("supersecret-passphrase")
            hs.me(username="test")

        """
        if username:
            self.set_username(username)
        url = urljoin(self.hs_api_url, "me/")
        r = requests.post(url, headers=self.headers)
        return r.json()

    def set_access_token(self, access_token):
        """ Is needed for :func:`broadcast` and :func:`me`
        """
        self.access_token = access_token

    def set_username(self, username, permission="posting"):
        """ Set a username for the next :func:`broadcast` or :func:`me` operation.
            The necessary token is fetched from the wallet
        """
        if permission != "posting":
            self.access_token = None
            return
        self.access_token = self.getTokenForAccountName(username)

    def broadcast(self, operations, username=None):
        """ Broadcast an operation

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
        url = urljoin(self.hs_api_url, "broadcast/")
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
            "client_secret": self.getTokenForAccountName(self.client_id),
            "scope": scope,
        }

        r = requests.post(
            urljoin(self.hs_api_url, "oauth2/token/"),
            data=post_data,
        )

        return r.json()

    def revoke_token(self, access_token):
        post_data = {
            "access_token": access_token,
        }

        r = requests.post(
            urljoin(self.hs_api_url, "oauth2/token/revoke"),
            data=post_data
        )

        return r.json()

    def update_user_metadata(self, metadata):
        put_data = {
            "user_metadata": metadata,
        }
        r = requests.put(
            urljoin(self.hs_api_url, "me/"),
            data=put_data, headers=self.headers)

        return r.json()

    def url_from_tx(self, tx, redirect_uri=None):
        """ Creates a link for broadcasting an operation

            :param dict tx: includes the operation, which should be broadcast
            :param str redirect_uri: Redirects to this uri, when set
        """
        if not isinstance(tx, dict):
            tx = tx.json()
        if "operations" not in tx or not tx["operations"]:
            return ''
        urls = []
        operations = tx["operations"]
        for op in operations:
            operation = op[0]
            params = op[1]
            for key in params:
                value = params[key]
                if isinstance(value, list) and len(value) == 3:
                    try:
                        amount = Amount(value, blockchain_instance=self.blockchain)
                        params[key] = str(amount)
                    except:
                        amount = None
                elif isinstance(value, bool):
                    if value:
                        params[key] = 1
                    else:
                        params[key] = 0
            urls.append(self.create_hot_sign_url(operation, params, redirect_uri=redirect_uri))
        if len(urls) == 1:
            return urls[0]
        else:
            return urls

    def create_hot_sign_url(self, operation, params, redirect_uri=None):
        """ Creates a link for broadcasting an operation

            :param str operation: operation name (e.g.: vote)
            :param dict params: operation dict params
            :param str redirect_uri: Redirects to this uri, when set
        """

        if not isinstance(operation, str) or not isinstance(params, dict):
            raise ValueError("Invalid Request.")

        base_url = self.hs_api_url.replace("https://api.", "https://").replace("/api", "")
        if redirect_uri == "":
            redirect_uri = None

        if redirect_uri is None and self.hot_sign_redirect_uri is not None:
            redirect_uri = self.hot_sign_redirect_uri
        if redirect_uri is not None:
            params.update({"redirect_uri": redirect_uri})

        for key in params:
            if isinstance(params[key], list):
                params[key] = json.dumps(params[key])
        params = urlencode(params)
        url = urljoin(base_url, "sign/%s" % operation)
        url += "?" + params

        return url
