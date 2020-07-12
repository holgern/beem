# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes, int, str
import pytz
import json
from datetime import datetime, timedelta, date, time
import math
import random
import logging
from prettytable import PrettyTable
from beem.instance import shared_blockchain_instance
from .exceptions import AccountDoesNotExistsException, OfflineHasNoRPCException
from beemapi.exceptions import ApiNotSupported, MissingRequiredActiveAuthority
from .blockchainobject import BlockchainObject
from .blockchain import Blockchain
from .utils import formatTimeString, formatTimedelta, remove_from_dict, reputation_to_score, addTzInfo
from beem.amount import Amount
from beembase import operations
from beem.rc import RC
from beemgraphenebase.account import PrivateKey, PublicKey, PasswordKey
from beemgraphenebase.py23 import bytes_types, integer_types, string_types, text_type
from beem.constants import STEEM_VOTE_REGENERATION_SECONDS, STEEM_1_PERCENT, STEEM_100_PERCENT, STEEM_VOTING_MANA_REGENERATION_SECONDS
log = logging.getLogger(__name__)


class Community(BlockchainObject):
    """ This class allows to easily access Community data

        :param str account: Name of the account
        :param Steem/Hive blockchain_instance: Hive or Steem
               instance
        :param bool lazy: Use lazy loading
        :param bool full: Obtain all account data including orders, positions,
               etc.
        :param Hive hive_instance: Hive instance
        :param Steem steem_instance: Steem instance
        :returns: Account data
        :rtype: dictionary
        :raises beem.exceptions.AccountDoesNotExistsException: if account
                does not exist

        Instances of this class are dictionaries that come with additional
        methods (see below) that allow dealing with an community and its
        corresponding functions.

        .. code-block:: python

            >>> from beem.community import Community
            >>> from beem import Hive
            >>> from beem.nodelist import NodeList
            >>> nodelist = NodeList()
            >>> nodelist.update_nodes()
            >>> stm = Hive(node=nodelist.get_hive_nodes())
            >>> community = Community("hive-10836", blockchain_instance=stm)
            >>> print(community)
            <Community hive-10836>
            >>> print(community.balances) # doctest: +SKIP

        .. note:: This class comes with its own caching function to reduce the
                  load on the API server. Instances of this class can be
                  refreshed with ``Community.refresh()``. The cache can be
                  cleared with ``Community.clear_cache()``

    """

    type_id = 2

    def __init__(
        self,
        community,
        observer="",
        full=True,
        lazy=False,
        blockchain_instance=None,
        **kwargs
    ):
        """Initialize an community

        :param str community: Name of the community
        :param Hive/Steem blockchain_instance: Hive/Steem
               instance
        :param bool lazy: Use lazy loading
        :param bool full: Obtain all community data including orders, positions,
               etc.
        """
        self.full = full
        self.lazy = lazy
        self.observer = observer
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        if isinstance(community, dict):
            community = self._parse_json_data(community)
        super(Community, self).__init__(
            community,
            lazy=lazy,
            full=full,
            id_item="name",
            blockchain_instance=blockchain_instance
        )

    def refresh(self):
        """ Refresh/Obtain an community's data from the API server
        """
        if not self.blockchain.is_connected():
            return
        self.blockchain.rpc.set_next_node_on_empty_reply(True)
        community = self.blockchain.rpc.get_community({'name': self.identifier, 'observer': self.observer}, api="bridge")

        if not community:
            raise AccountDoesNotExistsException(self.identifier)
        community = self._parse_json_data(community)
        self.identifier = community["name"]
        # self.blockchain.refresh_data()

        super(Community, self).__init__(community, id_item="name", lazy=self.lazy, full=self.full, blockchain_instance=self.blockchain)

    def _parse_json_data(self, community):
        parse_int = [
            "sum_pending", "subscribers", "num_pending", "num_authors",
        ]
        for p in parse_int:
            if p in community and isinstance(community.get(p), string_types):
                community[p] = int(community.get(p, 0))
        parse_times = [
            "created_at"            
        ]
        for p in parse_times:
            if p in community and isinstance(community.get(p), string_types):
                community[p] = addTzInfo(datetime.strptime(community.get(p, "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S"))
        return community

    def json(self):
        output = self.copy()
        parse_int = [
            "sum_pending", "subscribers", "num_pending", "num_authors",
        ]
        parse_int_without_zero = [

        ]
        for p in parse_int:
            if p in output and isinstance(output[p], integer_types):
                output[p] = str(output[p])
        for p in parse_int_without_zero:
            if p in output and isinstance(output[p], integer_types) and output[p] != 0:
                output[p] = str(output[p])

        parse_times = [
            "created_at",        
        ]
        for p in parse_times:
            if p in output:
                p_date = output.get(p, datetime(1970, 1, 1, 0, 0))
                if isinstance(p_date, (datetime, date, time)):
                    output[p] = formatTimeString(p_date).replace("T", " ")
                else:
                    output[p] = p_date
        return json.loads(str(json.dumps(output)))

    def get_community_roles(self):
        """ Lists community roles
        """
        community = self["name"]
        if not self.blockchain.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.blockchain.rpc.set_next_node_on_empty_reply(False)        
        return self.blockchain.rpc.list_community_roles({"community": community}, api="bridge")

    def get_subscribers(self):
        """  Returns subscribers
        """
        community = self["name"]
        if not self.blockchain.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.blockchain.rpc.set_next_node_on_empty_reply(False)        
        return self.blockchain.rpc.list_subscribers({"community": community}, api="bridge")

    def get_activities(self, limit=100, last_id=None):
        """ Returns community activity
        """
        community = self["name"]
        if not self.blockchain.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        self.blockchain.rpc.set_next_node_on_empty_reply(False)        
        return self.blockchain.rpc.account_notifications({"account": community, "limit": limit, "last_id": last_id}, api="bridge")

    def set_role(self, account, role, mod_account):
        """ Set role for a given account

            :param str account: Set role of this account
            :param str role: Can be member, mod, admin, owner, guest
            :param str mod_account: Account who broadcast this, (mods or higher)

        """
        community = self["name"]
        if not self.blockchain.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        json_body = [
            'setRole', {
                'community': community,
                'account': account,
                'role': role,
            }
        ]
        return self.blockchain.custom_json(
            "community", json_body, required_posting_auths=[mod_account])

    def set_user_title(self, account, title, mod_account):
        """ Set title for a given account

            :param str account: Set role of this account
            :param str title: Title
            :param str mod_account: Account who broadcast this, (mods or higher)

        """
        community = self["name"]
        if not self.blockchain.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        json_body = [
            'setUserTitle', {
                'community': community,
                'account': account,
                'title': title,
            }
        ]
        return self.blockchain.custom_json(
            "community", json_body, required_posting_auths=[mod_account])

    def mute_post(self, account, permlink, notes, mod_account):
        """ Mutes a post

            :param str account: Set role of this account
            :param str permlink: permlink
            :param str notes: permlink
            :param str mod_account: Account who broadcast this, (mods or higher)

        """
        community = self["name"]
        if not self.blockchain.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        json_body = [
            'mutePost', {
                'community': community,
                'account': account,
                'permlink': permlink,
                "notes": notes
            }
        ]
        return self.blockchain.custom_json(
            "community", json_body, required_posting_auths=[mod_account])


    def unmute_post(self, account, permlink, notes, mod_account):
        """ Unmute a post

            :param str account: post author
            :param str permlink: permlink
            :param str notes: notes
            :param str mod_account: Account who broadcast this, (mods or higher)

        """
        community = self["name"]
        if not self.blockchain.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        json_body = [
            'unmutePost', {
                'community': community,
                'account': account,
                'permlink': permlink,
                "notes": notes
            }
        ]
        return self.blockchain.custom_json(
            "community", json_body, required_posting_auths=[mod_account])

    def update_props(self, title, about, is_nsfw, description, flag_text, admin_account):
        """ Updates the community properties

            :param str title: Community title
            :param str about: about
            :param bool is_nsfw: is_nsfw
            :param str description: description
            :param str flag_text: flag_text            
            :param str admin_account: Account who broadcast this, (admin or higher)

        """
        community = self["name"]
        if not self.blockchain.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        json_body = [
            'updateProps', {
                'community': community,
                'props': {
                    "title": title,
                    "about": about,
                    "is_nsfw": is_nsfw,
                    "description": description,
                    "flag_text": flag_text
                }
            }
        ]
        return self.blockchain.custom_json(
            "community", json_body, required_posting_auths=[admin_account])

    def subscribe(self, account):
        """ subscribe to a community

            :param str account: account who suscribe to the community (is also broadcasting the custom_json)

        """
        community = self["name"]
        if not self.blockchain.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        json_body = [
            'subscribe', {
                'community': community,
            }
        ]
        return self.blockchain.custom_json(
            "community", json_body, required_posting_auths=[account])

    def pin_post(self, account, permlink, mod_account):
        """ Stickes a post to the top of a community

            :param str account: post author
            :param str permlink: permlink
            :param str mod_account: Account who broadcast this, (mods or higher)

        """
        community = self["name"]
        if not self.blockchain.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        json_body = [
            'pinPost', {
                'community': community,
                'account': account,
                'permlink': permlink,
            }
        ]
        return self.blockchain.custom_json(
            "community", json_body, required_posting_auths=[mod_account])

    def unsubscribe(self, account):
        """ unsubscribe a community

            :param str account: account who unsuscribe to the community (is also broadcasting the custom_json)

        """
        community = self["name"]
        if not self.blockchain.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        json_body = [
            'unsubscribe', {
                'community': community,
            }
        ]
        return self.blockchain.custom_json(
            "community", json_body, required_posting_auths=[account])

    def unpin_post(self, account, permlink, mod_account):
        """ Removes a post from the top of a community

            :param str account: post author
            :param str permlink: permlink
            :param str mod_account: Account who broadcast this, (mods or higher)

        """
        community = self["name"]
        if not self.blockchain.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        json_body = [
            'unpinPost', {
                'community': community,
                'account': account,
                'permlink': permlink,
            }
        ]
        return self.blockchain.custom_json(
            "community", json_body, required_posting_auths=[mod_account])    

    def flag_post(self, account, permlink, notes, reporter):
        """ Suggest a post for the review queue

            :param str account: post author
            :param str permlink: permlink
            :param str notes: notes
            :param str reporter: Account who broadcast this
        """
        community = self["name"]
        if not self.blockchain.is_connected():
            raise OfflineHasNoRPCException("No RPC available in offline mode!")
        json_body = [
            'flagPost', {
                'community': community,
                'account': account,
                'permlink': permlink,
                'notes': notes
            }
        ]
        return self.blockchain.custom_json(
            "community", json_body, required_posting_auths=[reporter])        


class CommunityObject(list):
    def printAsTable(self):
        t = PrettyTable(["Name", "Title", "lang", "subscribers", "sum_pending", "num_pending", "num_authors"])
        t.align = "l"
        for community in self:
            t.add_row([community['name'], community["title"], community["lang"], community["subscribers"], community["sum_pending"],
                       community["num_pending"], community["num_authors"]])
        print(t)


class Communities(CommunityObject):
    """ Obtain a list of communities

        :param list name_list: list of accounts to fetch
        :param int batch_limit: (optional) maximum number of accounts
            to fetch per call, defaults to 100
        :param Steem/Hive blockchain_instance: Steem() or Hive() instance to use when
            accessing a RPCcreator = Account(creator, blockchain_instance=self)
    """
    def __init__(self, sort="rank", observer=None, last=None, limit=100, lazy=False, full=True, blockchain_instance=None, **kwargs):
        
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]
        self.blockchain = blockchain_instance or shared_blockchain_instance()

        if not self.blockchain.is_connected():
            return
        communities = []
        community_cnt = 0
        batch_limit = 100
        if batch_limit > limit:
            batch_limit = limit

        while community_cnt < limit:
            self.blockchain.rpc.set_next_node_on_empty_reply(False)
            communities += self.blockchain.rpc.list_communities({'sort': sort, 'observer': observer, "last": last, "limit": batch_limit}, api="bridge")
            community_cnt += batch_limit
            last = communities[-1]["name"]

        super(Communities, self).__init__(
            [
                Community(x, lazy=lazy, full=full, blockchain_instance=self.blockchain)
                for x in communities
            ]
        )

    def search_title(self, title):
        """ Returns all communites which have a title similar to title"""
        ret = CommunityObject()
        for community in self:
            if title.lower() in community["title"].lower():
                ret.append(community)
        return ret