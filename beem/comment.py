# -*- coding: utf-8 -*-
import json
import re
import logging
import pytz
import math
import warnings
from datetime import datetime, date, time
from .instance import shared_blockchain_instance
from .account import Account
from .amount import Amount
from .price import Price
from .utils import resolve_authorperm, construct_authorperm, construct_authorpermvoter, derive_permlink, remove_from_dict, make_patch, formatTimeString, formatToTimeStamp
from .blockchainobject import BlockchainObject
from .exceptions import ContentDoesNotExistsException, VotingInvalidOnArchivedPost
from beembase import operations
from beemgraphenebase.py23 import py23_bytes, bytes_types, integer_types, string_types, text_type
from beem.constants import STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF6, STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF20, STEEM_100_PERCENT, STEEM_1_PERCENT, STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF21
log = logging.getLogger(__name__)


class Comment(BlockchainObject):
    """ Read data about a Comment/Post in the chain

        :param str authorperm: identifier to post/comment in the form of
            ``@author/permlink``
        :param str tags: defines which api is used. Can be bridge, tags, condenser or database (default = bridge)
        :param Hive blockchain_instance: :class:`beem.hive.Steem` instance to use when accessing a RPC


        .. code-block:: python

        >>> from beem.comment import Comment
        >>> from beem.account import Account
        >>> from beem import Steem
        >>> stm = Steem()
        >>> acc = Account("gtg", blockchain_instance=stm)
        >>> authorperm = acc.get_blog(limit=1)[0]["authorperm"]
        >>> c = Comment(authorperm)
        >>> postdate = c["created"]
        >>> postdate_str = c.json()["created"]

    """
    type_id = 8

    def __init__(
        self,
        authorperm,
        api="bridge",
        observer="",
        full=True,
        lazy=False,
        blockchain_instance=None,
        **kwargs
    ):
        self.full = full
        self.lazy = lazy
        self.api = api
        self.observer = observer
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        if isinstance(authorperm, string_types) and authorperm != "":
            [author, permlink] = resolve_authorperm(authorperm)
            self["id"] = 0
            self["author"] = author
            self["permlink"] = permlink
            self["authorperm"] = authorperm
        elif isinstance(authorperm, dict) and "author" in authorperm and "permlink" in authorperm:
            authorperm["authorperm"] = construct_authorperm(authorperm["author"], authorperm["permlink"])
            authorperm = self._parse_json_data(authorperm)
        super(Comment, self).__init__(
            authorperm,
            id_item="authorperm",
            lazy=lazy,
            full=full,
            blockchain_instance=blockchain_instance
        )

    def _parse_json_data(self, comment):
        parse_times = [
            "active", "cashout_time", "created", "last_payout", "last_update",
            "max_cashout_time"
        ]
        for p in parse_times:
            if p in comment and isinstance(comment.get(p), string_types):
                comment[p] = formatTimeString(comment.get(p, "1970-01-01T00:00:00"))
        # Parse Amounts
        sbd_amounts = [
            "total_payout_value",
            "max_accepted_payout",
            "pending_payout_value",
            "curator_payout_value",
            "total_pending_payout_value",
            "promoted",
        ]
        for p in sbd_amounts:
            if p in comment and isinstance(comment.get(p), (string_types, list, dict)):
                value = comment.get(p, "0.000 %s" % (self.blockchain.backed_token_symbol))
                if isinstance(value, str) and value.split(" ")[1] !=self.blockchain.backed_token_symbol:
                    value = value.split(" ")[0] + " " + self.blockchain.backed_token_symbol
                comment[p] = Amount(value, blockchain_instance=self.blockchain)

        # turn json_metadata into python dict
        meta_str = comment.get("json_metadata", "{}")
        if meta_str == "{}":
            comment['json_metadata'] = meta_str
        if isinstance(meta_str, (string_types, bytes_types, bytearray)):
            try:
                comment['json_metadata'] = json.loads(meta_str)
            except:
                comment['json_metadata'] = {}

        comment["tags"] = []
        comment['community'] = ''
        if isinstance(comment['json_metadata'], dict):
            if "tags" in comment['json_metadata']:
                comment["tags"] = comment['json_metadata']["tags"]
            if 'community' in comment['json_metadata']:
                comment['community'] = comment['json_metadata']['community']

        parse_int = [
            "author_reputation",
            "net_rshares",
        ]
        for p in parse_int:
            if p in comment and isinstance(comment.get(p), string_types):
                comment[p] = int(comment.get(p, "0"))

        if "active_votes" in comment:
            new_active_votes = []
            for vote in comment["active_votes"]:
                if 'time' in vote and isinstance(vote.get('time'), string_types):
                    vote['time'] = formatTimeString(vote.get('time', "1970-01-01T00:00:00"))
                parse_int = [
                    "rshares", "reputation",
                ]
                for p in parse_int:
                    if p in vote and isinstance(vote.get(p), string_types):
                        try:
                            vote[p] = int(vote.get(p, "0"))
                        except:
                            vote[p] = int(0)
                new_active_votes.append(vote)
            comment["active_votes"] = new_active_votes
        return comment

    def refresh(self):
        if self.identifier == "":
            return
        if not self.blockchain.is_connected():
            return
        [author, permlink] = resolve_authorperm(self.identifier)
        self.blockchain.rpc.set_next_node_on_empty_reply(True)
        if self.blockchain.rpc.get_use_appbase():
            from beemapi.exceptions import InvalidParameters
            try:
                if self.api == "tags":
                    content = self.blockchain.rpc.get_discussion({'author': author, 'permlink': permlink}, api="tags")
                elif self.api == "database":
                    content =self.blockchain.rpc.list_comments({"start": [author, permlink], "limit": 1, "order": "by_permlink"}, api="database")
                elif self.api == "bridge":
                    content = self.blockchain.rpc.get_post({"author": author, "permlink": permlink, "observer": self.observer}, api="bridge")
                elif self.api == "condenser":
                    content = self.blockchain.rpc.get_content(author, permlink, api="condenser")
                else:
                    raise ValueError("api must be: tags, database, bridge or condenser")
                if content is not None and "comments" in content:
                    content =content["comments"]
                if isinstance(content, list) and len(content) >0:
                    content =content[0]
            except InvalidParameters:
                raise ContentDoesNotExistsException(self.identifier)
        else:
            from beemapi.exceptions import InvalidParameters
            try:            
                content = self.blockchain.rpc.get_content(author, permlink)
            except InvalidParameters:
                raise ContentDoesNotExistsException(self.identifier)                
        if not content or not content['author'] or not content['permlink']:
            raise ContentDoesNotExistsException(self.identifier)
        content = self._parse_json_data(content)
        content["authorperm"] = construct_authorperm(content['author'], content['permlink'])
        super(Comment, self).__init__(content, id_item="authorperm", lazy=self.lazy, full=self.full, blockchain_instance=self.blockchain)

    def json(self):
        output = self.copy()
        if "authorperm" in output:
            output.pop("authorperm")
        if 'json_metadata' in output:
            output["json_metadata"] = json.dumps(output["json_metadata"], separators=[',', ':'])
        if "tags" in output:
            output.pop("tags")
        if "community" in output:
            output.pop("community")
        parse_times = [
            "active", "cashout_time", "created", "last_payout", "last_update",
            "max_cashout_time"
        ]
        for p in parse_times:
            if p in output:
                p_date = output.get(p, datetime(1970, 1, 1, 0, 0))
                if isinstance(p_date, (datetime, date)):
                    output[p] = formatTimeString(p_date)
                else:
                    output[p] = p_date
        sbd_amounts = [
            "total_payout_value",
            "max_accepted_payout",
            "pending_payout_value",
            "curator_payout_value",
            "total_pending_payout_value",
            "promoted",
        ]
        for p in sbd_amounts:
            if p in output and isinstance(output[p], Amount):
                output[p] = output[p].json()
        parse_int = [
            "author_reputation",
            "net_rshares",
        ]
        for p in parse_int:
            if p in output and isinstance(output[p], integer_types):
                output[p] = str(output[p])
        if "active_votes" in output:
            new_active_votes = []
            for vote in output["active_votes"]:
                if 'time' in vote:
                    p_date = vote.get('time', datetime(1970, 1, 1, 0, 0))
                    if isinstance(p_date, (datetime, date)):
                        vote['time'] = formatTimeString(p_date)
                    else:
                        vote['time'] = p_date
                parse_int = [
                    "rshares", "reputation",
                ]
                for p in parse_int:
                    if p in vote and isinstance(vote[p], integer_types):
                        vote[p] = str(vote[p])
                new_active_votes.append(vote)
            output["active_votes"] = new_active_votes
        return json.loads(str(json.dumps(output)))

    @property
    def id(self):
        return self["id"]

    @property
    def author(self):
        return self["author"]

    @property
    def permlink(self):
        return self["permlink"]

    @property
    def authorperm(self):
        return construct_authorperm(self["author"], self["permlink"])

    @property
    def category(self):
        if "category" in self:
            return self["category"]
        else:
            return ""

    @property
    def parent_author(self):
        return self["parent_author"]

    @property
    def parent_permlink(self):
        return self["parent_permlink"]

    @property
    def depth(self):
        return self["depth"]

    @property
    def title(self):
        if "title" in self:
            return self["title"]
        else:
            return ""

    @property
    def body(self):
        if "body" in self:
            return self["body"]
        else:
            return ""

    @property
    def json_metadata(self):
        if "json_metadata" in self:
            return self["json_metadata"]
        else:
            return {}

    def is_main_post(self):
        """ Returns True if main post, and False if this is a comment (reply).
        """
        if 'depth' in self:
            return self['depth'] == 0
        else:
            return self["parent_author"] == ''

    def is_comment(self):
        """ Returns True if post is a comment
        """
        if 'depth' in self:
            return self['depth'] > 0
        else:
            return self["parent_author"] != ''

    @property
    def reward(self):
        """ Return the estimated total SBD reward.
        """
        a_zero = Amount(0, self.blockchain.backed_token_symbol, blockchain_instance=self.blockchain)
        author = Amount(self.get("total_payout_value", a_zero), blockchain_instance=self.blockchain)
        curator = Amount(self.get("curator_payout_value", a_zero), blockchain_instance=self.blockchain)
        pending = Amount(self.get("pending_payout_value", a_zero), blockchain_instance=self.blockchain)
        return author + curator + pending

    def is_pending(self):
        """ Returns if the payout is pending (the post/comment
            is younger than 7 days)
        """
        a_zero = Amount(0, self.blockchain.backed_token_symbol, blockchain_instance=self.blockchain)
        total = Amount(self.get("total_payout_value", a_zero), blockchain_instance=self.blockchain)
        post_age_days = self.time_elapsed().total_seconds() / 60 / 60 / 24
        return post_age_days < 7.0 and float(total) == 0

    def time_elapsed(self):
        """Returns a timedelta on how old the post is.
        """
        utc = pytz.timezone('UTC')
        return utc.localize(datetime.utcnow()) - self['created']

    def curation_penalty_compensation_SBD(self):
        """ Returns The required post payout amount after 15 minutes
            which will compentsate the curation penalty, if voting earlier than 15 minutes
        """
        self.refresh()
        if self.blockchain.hardfork >= 21:
            reverse_auction_window_seconds = STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF21
        elif self.blockchain.hardfork >= 20:
            reverse_auction_window_seconds = STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF20
        else:
            reverse_auction_window_seconds = STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF6
        return self.reward * reverse_auction_window_seconds / ((self.time_elapsed()).total_seconds() / 60) ** 2

    def estimate_curation_SBD(self, vote_value_SBD, estimated_value_SBD=None):
        """ Estimates curation reward

            :param float vote_value_SBD: The vote value in SBD for which the curation
                should be calculated
            :param float estimated_value_SBD: When set, this value is used for calculate
                the curation. When not set, the current post value is used.
        """
        self.refresh()
        if estimated_value_SBD is None:
            estimated_value_SBD = float(self.reward)
        t = 1.0 - self.get_curation_penalty()
        k = vote_value_SBD / (vote_value_SBD + float(self.reward))
        K = (1 - math.sqrt(1 - k)) / 4 / k
        return K * vote_value_SBD * t * math.sqrt(estimated_value_SBD)

    def get_curation_penalty(self, vote_time=None):
        """ If post is less than 5 minutes old, it will incur a curation
            reward penalty.

            :param datetime vote_time: A vote time can be given and the curation
                penalty is calculated regarding the given time (default is None)
                When set to None, the current date is used.
            :returns: Float number between 0 and 1 (0.0 -> no penalty, 1.0 -> 100 % curation penalty)
            :rtype: float

        """
        if vote_time is None:
            elapsed_seconds = self.time_elapsed().total_seconds()
        elif isinstance(vote_time, str):
            elapsed_seconds = (formatTimeString(vote_time) - self["created"]).total_seconds()
        elif isinstance(vote_time, (datetime, date)):
            elapsed_seconds = (vote_time - self["created"]).total_seconds()
        else:
            raise ValueError("vote_time must be a string or a datetime")
        if self.blockchain.hardfork >= 21:
            reward = (elapsed_seconds / STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF21)
        elif self.blockchain.hardfork >= 20:
            reward = (elapsed_seconds / STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF20)
        else:
            reward = (elapsed_seconds / STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF6)
        if reward > 1:
            reward = 1.0
        return 1.0 - reward

    def get_vote_with_curation(self, voter=None, raw_data=False, pending_payout_value=None):
        """ Returns vote for voter. Returns None, if the voter cannot be found in `active_votes`.

            :param str voter: Voter for which the vote should be returned
            :param bool raw_data: If True, the raw data are returned
            :param pending_payout_SBD: When not None this value instead of the current
                value is used for calculating the rewards
            :type pending_payout_SBD: float, str
        """
        specific_vote = None
        if voter is None:
            voter = Account(self["author"], blockchain_instance=self.blockchain)
        else:
            voter = Account(voter, blockchain_instance=self.blockchain)
        if "active_votes" in self:
            for vote in self["active_votes"]:
                if voter["name"] == vote["voter"]:
                    specific_vote = vote
        else:
            active_votes = self.get_votes()
            for vote in active_votes:
                if voter["name"] == vote["voter"]:
                    specific_vote = vote 
        if specific_vote is not None and (raw_data or not self.is_pending()):
            return specific_vote
        elif specific_vote is not None:
            curation_reward = self.get_curation_rewards(pending_payout_SBD=True, pending_payout_value=pending_payout_value)
            specific_vote["curation_reward"] = curation_reward["active_votes"][voter["name"]]
            specific_vote["ROI"] = float(curation_reward["active_votes"][voter["name"]]) / float(voter.get_voting_value_SBD(voting_weight=specific_vote["percent"] / 100)) * 100
            return specific_vote
        else:
            return None

    def get_beneficiaries_pct(self):
        """ Returns the sum of all post beneficiaries in percentage
        """
        beneficiaries = self["beneficiaries"]
        weight = 0
        for b in beneficiaries:
            weight += b["weight"]
        return weight / 100.

    def get_rewards(self):
        """ Returns the total_payout, author_payout and the curator payout in SBD.
            When the payout is still pending, the estimated payout is given out.

            .. note:: Potential beneficiary rewards were already deducted from the
                      `author_payout` and the `total_payout`

            Example:::

                {
                    'total_payout': 9.956 SBD,
                    'author_payout': 7.166 SBD,
                    'curator_payout': 2.790 SBD
                }

        """
        if self.is_pending():
            total_payout = Amount(self["pending_payout_value"], blockchain_instance=self.blockchain)
            author_payout = self.get_author_rewards()["total_payout_SBD"]
            curator_payout = total_payout - author_payout
        else:
            author_payout = Amount(self["total_payout_value"], blockchain_instance=self.blockchain)
            curator_payout = Amount(self["curator_payout_value"], blockchain_instance=self.blockchain)
            total_payout = author_payout + curator_payout
        return {"total_payout": total_payout, "author_payout": author_payout, "curator_payout": curator_payout}

    def get_author_rewards(self):
        """ Returns the author rewards.

            
            
            Example::

                {
                    'pending_rewards': True,
                    'payout_SP': 0.912 STEEM,
                    'payout_SBD': 3.583 SBD,
                    'total_payout_SBD': 7.166 SBD
                }

        """
        if not self.is_pending():
            return {'pending_rewards': False,
                    "payout_SP": Amount(0, self.blockchain.token_symbol, blockchain_instance=self.blockchain),
                    "payout_SBD": Amount(0, self.blockchain.backed_token_symbol, blockchain_instance=self.blockchain),
                    "total_payout_SBD": Amount(self["total_payout_value"], blockchain_instance=self.blockchain)}
        author_reward_factor = 0.5
        median_hist = self.blockchain.get_current_median_history()
        if median_hist is not None:
            median_price = Price(median_hist, blockchain_instance=self.blockchain)
        beneficiaries_pct = self.get_beneficiaries_pct()
        curation_tokens = self.reward * author_reward_factor
        author_tokens = self.reward - curation_tokens
        curation_rewards = self.get_curation_rewards()
        if self.blockchain.hardfork >= 20 and median_hist is not None:
            author_tokens += median_price * curation_rewards['unclaimed_rewards']

        benefactor_tokens = author_tokens * beneficiaries_pct / 100.
        author_tokens -= benefactor_tokens

        if median_hist is not None and "percent_steem_dollars" in self:
            sbd_steem = author_tokens * self["percent_steem_dollars"] / 20000.
            vesting_steem = median_price.as_base(self.blockchain.token_symbol) * (author_tokens - sbd_steem)
            return {'pending_rewards': True, "payout_SP": vesting_steem, "payout_SBD": sbd_steem, "total_payout_SBD": author_tokens}
        elif median_hist is not None and "percent_hbd" in self:
            sbd_steem = author_tokens * self["percent_hbd"] / 20000.
            vesting_steem = median_price.as_base(self.blockchain.token_symbol) * (author_tokens - sbd_steem)
            return {'pending_rewards': True, "payout_SP": vesting_steem, "payout_SBD": sbd_steem, "total_payout_SBD": author_tokens}        
        else:
            return {'pending_rewards': True, "total_payout": author_tokens, "payout_SBD": None, "total_payout_SBD": None}

    def get_curation_rewards(self, pending_payout_SBD=False, pending_payout_value=None):
        """ Returns the curation rewards. The split between creator/curator is currently 50%/50%.

            :param bool pending_payout_SBD: If True, the rewards are returned in SBD and not in STEEM (default is False)
            :param pending_payout_value: When not None this value instead of the current
                value is used for calculating the rewards
            :type pending_payout_value: float, str

            `pending_rewards` is True when
            the post is younger than 7 days. `unclaimed_rewards` is the
            amount of curation_rewards that goes to the author (self-vote or votes within
            the first 30 minutes). `active_votes` contains all voter with their curation reward.

            Example::

                {
                    'pending_rewards': True, 'unclaimed_rewards': 0.245 STEEM,
                    'active_votes': {
                        'leprechaun': 0.006 STEEM, 'timcliff': 0.186 STEEM,
                        'st3llar': 0.000 STEEM, 'crokkon': 0.015 STEEM, 'feedyourminnows': 0.003 STEEM,
                        'isnochys': 0.003 STEEM, 'loshcat': 0.001 STEEM, 'greenorange': 0.000 STEEM,
                        'qustodian': 0.123 STEEM, 'jpphotography': 0.002 STEEM, 'thinkingmind': 0.001 STEEM,
                        'oups': 0.006 STEEM, 'mattockfs': 0.001 STEEM, 'holger80': 0.003 STEEM, 'michaelizer': 0.004 STEEM,
                        'flugschwein': 0.010 STEEM, 'ulisessabeque': 0.000 STEEM, 'hakancelik': 0.002 STEEM, 'sbi2': 0.008 STEEM,
                        'zcool': 0.000 STEEM, 'steemhq': 0.002 STEEM, 'rowdiya': 0.000 STEEM, 'qurator-tier-1-2': 0.012 STEEM
                    }
                }

        """
        median_hist = self.blockchain.get_current_median_history()
        if median_hist is not None:
            median_price = Price(median_hist, blockchain_instance=self.blockchain)
        pending_rewards = False
        active_votes_list = self.get_votes()
        curator_reward_factor = 0.5
        
        if "total_vote_weight" in self:
            total_vote_weight = self["total_vote_weight"]
        active_votes_json_list = []
        for vote in active_votes_list:
            if "weight" not in vote:
                vote.refresh()
                active_votes_json_list.append(vote.json())
            else:
                active_votes_json_list.append(vote.json())
        
        total_vote_weight = 0
        for vote in active_votes_json_list:
            total_vote_weight += vote["weight"]
            
        if not self.is_pending():
            if pending_payout_SBD or median_hist is None:
                max_rewards = Amount(self["curator_payout_value"], blockchain_instance=self.blockchain)
            else:
                max_rewards = median_price.as_base(self.blockchain.token_symbol) * Amount(self["curator_payout_value"], blockchain_instance=self.blockchain)
            unclaimed_rewards = Amount(0, self.blockchain.token_symbol, blockchain_instance=self.blockchain)
        else:
            if pending_payout_value is None and "pending_payout_value" in self:
                pending_payout_value = Amount(self["pending_payout_value"], blockchain_instance=self.blockchain)
            elif pending_payout_value is None:
                pending_payout_value = 0
            elif isinstance(pending_payout_value, (float, integer_types)):
                pending_payout_value = Amount(pending_payout_value, self.blockchain.backed_token_symbol, blockchain_instance=self.blockchain)
            elif isinstance(pending_payout_value, str):
                pending_payout_value = Amount(pending_payout_value, blockchain_instance=self.blockchain)
            if pending_payout_SBD or median_hist is None:
                max_rewards = (pending_payout_value * curator_reward_factor)
            else:
                max_rewards = median_price.as_base(self.blockchain.token_symbol) * (pending_payout_value * curator_reward_factor)
            unclaimed_rewards = max_rewards.copy()
            pending_rewards = True

        active_votes = {}

        for vote in active_votes_json_list:
            if total_vote_weight > 0:
                claim = max_rewards * int(vote["weight"]) / total_vote_weight
            else:
                claim = 0
            if claim > 0 and pending_rewards:
                unclaimed_rewards -= claim
            if claim > 0:
                active_votes[vote["voter"]] = claim
            else:
                active_votes[vote["voter"]] = 0

        return {'pending_rewards': pending_rewards, 'unclaimed_rewards': unclaimed_rewards, "active_votes": active_votes}

    def get_reblogged_by(self, identifier=None):
        """Shows in which blogs this post appears"""
        if not identifier:
            post_author = self["author"]
            post_permlink = self["permlink"]
        else:
            [post_author, post_permlink] = resolve_authorperm(identifier)
        if not self.blockchain.is_connected():
            return None
        self.blockchain.rpc.set_next_node_on_empty_reply(False)
        if self.blockchain.rpc.get_use_appbase():
            return self.blockchain.rpc.get_reblogged_by({'author': post_author, 'permlink': post_permlink}, api="follow")['accounts']
        else:
            return self.blockchain.rpc.get_reblogged_by(post_author, post_permlink, api="follow")

    def get_replies(self, raw_data=False, identifier=None):
        """ Returns content replies

            :param bool raw_data: When set to False, the replies will be returned as Comment class objects
        """
        if not identifier:
            post_author = self["author"]
            post_permlink = self["permlink"]
        else:
            [post_author, post_permlink] = resolve_authorperm(identifier)
        if not self.blockchain.is_connected():
            return None
        self.blockchain.rpc.set_next_node_on_empty_reply(False)
        if self.blockchain.rpc.get_use_appbase():
            content_replies = self.blockchain.rpc.get_content_replies({'author': post_author, 'permlink': post_permlink}, api="tags")
            if 'discussions' in content_replies:
                content_replies = content_replies['discussions']
        else:
            content_replies = self.blockchain.rpc.get_content_replies(post_author, post_permlink, api="tags")
        if raw_data:
            return content_replies
        return [Comment(c, blockchain_instance=self.blockchain) for c in content_replies]

    def get_all_replies(self, parent=None):
        """ Returns all content replies
        """
        if parent is None:
            parent = self
        if parent["children"] > 0:
            children = parent.get_replies()
            if children is None:
                return []
            for cc in children[:]:
                children.extend(self.get_all_replies(parent=cc))
            return children
        return []

    def get_parent(self, children=None):
        """ Returns the parent post with depth == 0"""
        if children is None:
            children = self
        while children["depth"] > 0:
            children = Comment(construct_authorperm(children["parent_author"], children["parent_permlink"]), blockchain_instance=self.blockchain)
        return children

    def get_votes(self, raw_data=False):
        """Returns all votes as ActiveVotes object"""
        if raw_data and "active_votes" in self:
            return self["active_votes"]
        from .vote import ActiveVotes
        authorperm = construct_authorperm(self["author"], self["permlink"])
        return ActiveVotes(authorperm, lazy=False, blockchain_instance=self.blockchain)

    def upvote(self, weight=+100, voter=None):
        """ Upvote the post

            :param float weight: (optional) Weight for posting (-100.0 -
                +100.0) defaults to +100.0
            :param str voter: (optional) Voting account

        """
        if weight < 0:
            raise ValueError("Weight must be >= 0.")
        last_payout = self.get('last_payout', None)
        if last_payout is not None:
            if formatToTimeStamp(last_payout) > 0:
                raise VotingInvalidOnArchivedPost
        return self.vote(weight, account=voter)

    def downvote(self, weight=100, voter=None):
        """ Downvote the post

            :param float weight: (optional) Weight for posting (-100.0 -
                +100.0) defaults to -100.0
            :param str voter: (optional) Voting account

        """
        if weight < 0:
            raise ValueError("Weight must be >= 0.")        
        last_payout = self.get('last_payout', None)
        if last_payout is not None:
            if formatToTimeStamp(last_payout) > 0:
                raise VotingInvalidOnArchivedPost
        return self.vote(-weight, account=voter)

    def vote(self, weight, account=None, identifier=None, **kwargs):
        """ Vote for a post

            :param float weight: Voting weight. Range: -100.0 - +100.0.
            :param str account: (optional) Account to use for voting. If
                ``account`` is not defined, the ``default_account`` will be used
                or a ValueError will be raised
            :param str identifier: Identifier for the post to vote. Takes the
                form ``@author/permlink``.

        """
        if not identifier:
            identifier = construct_authorperm(self["author"], self["permlink"])

        return self.blockchain.vote(weight, identifier, account=account)

    def edit(self, body, meta=None, replace=False):
        """ Edit an existing post

            :param str body: Body of the reply
            :param json meta: JSON meta object that can be attached to the
                post. (optional)
            :param bool replace: Instead of calculating a *diff*, replace
                the post entirely (defaults to ``False``)

        """
        if not meta:
            meta = {}
        original_post = self

        if replace:
            newbody = body
        else:
            newbody = make_patch(original_post["body"], body)
            if not newbody:
                log.info("No changes made! Skipping ...")
                return

        reply_identifier = construct_authorperm(
            original_post["parent_author"], original_post["parent_permlink"])

        new_meta = {}
        if meta is not None:
            if bool(original_post["json_metadata"]):
                new_meta = original_post["json_metadata"]
                for key in meta:
                    new_meta[key] = meta[key]
            else:
                new_meta = meta

        return self.blockchain.post(
            original_post["title"],
            newbody,
            reply_identifier=reply_identifier,
            author=original_post["author"],
            permlink=original_post["permlink"],
            json_metadata=new_meta,
        )

    def reply(self, body, title="", author="", meta=None):
        """ Reply to an existing post

            :param str body: Body of the reply
            :param str title: Title of the reply post
            :param str author: Author of reply (optional) if not provided
                ``default_user`` will be used, if present, else
                a ``ValueError`` will be raised.
            :param json meta: JSON meta object that can be attached to the
                post. (optional)

        """
        return self.blockchain.post(
            title,
            body,
            json_metadata=meta,
            author=author,
            reply_identifier=self.identifier)

    def delete(self, account=None, identifier=None):
        """ Delete an existing post/comment

            :param str account: (optional) Account to use for deletion. If
                ``account`` is not defined, the ``default_account`` will be
                taken or a ValueError will be raised.

            :param str identifier: (optional) Identifier for the post to delete.
                Takes the form ``@author/permlink``. By default the current post
                will be used.

            .. note:: A post/comment can only be deleted as long as it has no
                      replies and no positive rshares on it.

        """
        if not account:
            if "default_account" in self.blockchain.config:
                account = self.blockchain.config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, blockchain_instance=self.blockchain)
        if not identifier:
            post_author = self["author"]
            post_permlink = self["permlink"]
        else:
            [post_author, post_permlink] = resolve_authorperm(identifier)
        op = operations.Delete_comment(
            **{"author": post_author,
               "permlink": post_permlink})
        return self.blockchain.finalizeOp(op, account, "posting")

    def resteem(self, identifier=None, account=None):
        """ Resteem a post

            :param str identifier: post identifier (@<account>/<permlink>)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)

        """
        if not account:
            account = self.blockchain.configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, blockchain_instance=self.blockchain)
        if identifier is None:
            identifier = self.identifier
        author, permlink = resolve_authorperm(identifier)
        json_body = [
            "reblog", {
                "account": account["name"],
                "author": author,
                "permlink": permlink
            }
        ]
        return self.blockchain.custom_json(
            id="follow", json_data=json_body, required_posting_auths=[account["name"]])


class RecentReplies(list):
    """ Obtain a list of recent replies

        :param str author: author
        :param bool skip_own: (optional) Skip replies of the author to him/herself.
            Default: True
        :param Steem blockchain_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, author, skip_own=True, start_permlink="", limit=100, lazy=False, full=True, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        if not self.blockchain.is_connected():
            return None
        self.blockchain.rpc.set_next_node_on_empty_reply(True)
        account = Account(author, blockchain_instance=self.blockchain)
        replies = account.get_account_posts(sort="replies", raw_data=True)
        comments = []
        if replies is None:
            replies = []
        for post in replies:
            if skip_own and post["author"] == author:
                continue
            comments.append(Comment(post, lazy=lazy, full=full, blockchain_instance=self.blockchain))
        super(RecentReplies, self).__init__(comments)


class RecentByPath(list):
    """ Obtain a list of posts recent by path, does the same as RankedPosts

        :param str account: Account name
        :param Steem blockchain_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, path="trending", category=None, lazy=False, full=True, blockchain_instance=None, **kwargs):
        
        super(RecentByPath, self).__init__(RankedPosts(sort=path, tag=category))


class RankedPosts(list):
    """ Obtain a list of ranked posts

        :param str sort: can be: trending, hot, muted, created
        :param str tag: tag, when used my, the community posts of the observer are shown
        :param str observer: Observer name
        :param int limit: limits the number of returns comments
        :param str start_author: start author
        :param str start_permlink: start permlink
        :param Steem blockchain_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, sort="trending", tag="", observer="", limit=21, start_author="", start_permlink="", lazy=False, full=True, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        if not self.blockchain.is_connected():
            return None
        comments = []
        api_limit = limit
        if api_limit > 100:
            api_limit = 100
        last_n = -1
        while len(comments) < limit and last_n != len(comments):
            last_n = len(comments)        
            self.blockchain.rpc.set_next_node_on_empty_reply(True)
            posts = self.blockchain.rpc.get_ranked_posts({"sort": sort, "tag": tag, "observer": observer,
                                                          "limit": api_limit, "start_author": start_author,
                                                          "start_permlink": start_permlink}, api="bridge")
            
            for post in posts:
                if len(comments) > 0 and comments[-1]["author"] == post["author"] and comments[-1]["permlink"] == post["permlink"]:
                    continue
                if len(comments) >= limit:
                    continue
                if raw_data:
                    comments.append(post)
                else:
                    comments.append(Comment(post, lazy=lazy, full=full, blockchain_instance=self.blockchain))
            start_author = comments[-1]["author"]
            start_permlink = comments[-1]["permlink"]
            if limit - len(comments) < 100:
                api_limit = limit - len(comments) + 1
        super(RankedPosts, self).__init__(comments)


class AccountPosts(list):
    """ Obtain a list of account related posts

        :param str sort: can be: comments, posts, blog, replies, feed
        :param str account: Account name
        :param str observer: Observer name
        :param int limit: limits the number of returns comments
        :param str start_author: start author
        :param str start_permlink: start permlink
        :param Hive blockchain_instance: Hive() instance to use when accesing a RPC
    """
    def __init__(self, sort, account, observer="", limit=20, start_author="", start_permlink="", lazy=False, full=True, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        if not self.blockchain.is_connected():
            return None
        comments = []
        api_limit = limit
        if api_limit > 100:
            api_limit = 100
        last_n = -1
        while len(comments) < limit and last_n != len(comments):
            last_n = len(comments)
            self.blockchain.rpc.set_next_node_on_empty_reply(True)
            posts = self.blockchain.rpc.get_account_posts({"sort": sort, "account": account, "observer": observer,
                                                          "limit": api_limit, "start_author": start_author,
                                                          "start_permlink": start_permlink}, api="bridge")
            for post in posts:
                if len(comments) > 0 and comments[-1]["author"] == post["author"] and comments[-1]["permlink"] == post["permlink"]:
                    continue
                if len(comments) >= limit:
                    continue                
                if raw_data:
                    comments.append(post)
                else:
                    comments.append(Comment(post, lazy=lazy, full=full, blockchain_instance=self.blockchain))
            start_author = comments[-1]["author"]
            start_permlink = comments[-1]["permlink"]
            if limit - len(comments) < 100:
                api_limit = limit - len(comments) + 1
        super(AccountPosts, self).__init__(comments)