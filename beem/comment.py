# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from .instance import shared_steem_instance
from .account import Account
from .amount import Amount
from .utils import resolve_authorperm, construct_authorperm, derive_permlink, remove_from_dict, make_patch, formatTimeString
from .blockchainobject import BlockchainObject
from .exceptions import ContentDoesNotExistsException, VotingInvalidOnArchivedPost
from beembase import operations
from beemgraphenebase.py23 import py23_bytes, bytes_types, integer_types, string_types, text_type
import json
import re
import logging
from datetime import datetime
log = logging.getLogger(__name__)


class Comment(BlockchainObject):
    """ Read data about a Comment/Post in the chain

        :param str authorperm: perm link to post/comment
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    type_id = 8

    def __init__(
        self,
        authorperm,
        full=False,
        lazy=False,
        steem_instance=None
    ):
        self.full = full
        if isinstance(authorperm, string_types) and authorperm != "":
            [author, permlink] = resolve_authorperm(authorperm)
            self["id"] = 0
            self["author"] = author
            self["permlink"] = permlink
        elif isinstance(authorperm, dict) and "author" in authorperm and "permlink" in authorperm:
            authorperm["authorperm"] = construct_authorperm(authorperm["author"], authorperm["permlink"])
        super(Comment, self).__init__(
            authorperm,
            id_item="authorperm",
            lazy=lazy,
            full=full,
            steem_instance=steem_instance
        )
        if "author" in self and "permlink" in self:
            self.identifier = construct_authorperm(self["author"], self["permlink"])
        parse_times = [
            "active", "cashout_time", "created", "last_payout", "last_update",
            "max_cashout_time"
        ]
        for p in parse_times:
            if p in self and isinstance(self.get(p), str):
                self[p] = formatTimeString(self.get(p, "1970-01-01T00:00:00"))
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
            if p in self and isinstance(self.get(p), string_types):
                self[p] = Amount(self.get(p, "0.000 SBD"), steem_instance=self.steem)

        # turn json_metadata into python dict
        self._metadata_to_dict()
        self["tags"] = []
        self['community'] = ''
        if isinstance(self['json_metadata'], dict):
            if "tags" in self['json_metadata']:
                self["tags"] = self['json_metadata']["tags"]
            if 'community' in self['json_metadata']:
                self['community'] = self['json_metadata']['community']

    def _metadata_to_dict(self):
        """turn json_metadata into python dict"""
        meta_str = self.get("json_metadata", "{}")
        if meta_str == "{}":
            self['json_metadata'] = meta_str
        if isinstance(meta_str, (string_types, bytes_types, bytearray)):
            try:
                self['json_metadata'] = json.loads(meta_str)
            except:
                self['json_metadata'] = {}

    def refresh(self):
        if self.identifier == "":
            return
        if self.steem.offline:
            return
        [author, permlink] = resolve_authorperm(self.identifier)
        self.steem.rpc.set_next_node_on_empty_reply(True)
        if self.steem.rpc.get_use_appbase():
            content = self.steem.rpc.get_discussion({'author': author, 'permlink': permlink}, api="tags")
        else:
            content = self.steem.rpc.get_content(author, permlink)
        if not content or not content['author'] or not content['permlink']:
            raise ContentDoesNotExistsException(self.identifier)
        super(Comment, self).__init__(content, id_item="authorperm", steem_instance=self.steem)
        self["authorperm"] = construct_authorperm(self["author"], self["permlink"])
        self.identifier = self["authorperm"]
        parse_times = [
            "active", "cashout_time", "created", "last_payout", "last_update",
            "max_cashout_time"
        ]
        for p in parse_times:
            if p in self and isinstance(self.get(p), string_types):
                self[p] = formatTimeString(self.get(p, "1970-01-01T00:00:00"))
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
            if p in self and isinstance(self.get(p), string_types):
                self[p] = Amount(self.get(p, "0.000 SBD"), steem_instance=self.steem)
        # turn json_metadata into python dict
        self._metadata_to_dict()
        self["tags"] = []
        self['community'] = ''
        if isinstance(self['json_metadata'], dict):
            if "tags" in self['json_metadata']:
                self["tags"] = self['json_metadata']["tags"]
            if 'community' in self['json_metadata']:
                if p in self:
                    self['community'] = self['json_metadata']['community']

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
                date = output.get(p, datetime(1970, 1, 1, 0, 0))
                if isinstance(date, datetime):
                    output[p] = formatTimeString(date)
                else:
                    output[p] = date
        sbd_amounts = [
            "total_payout_value",
            "max_accepted_payout",
            "pending_payout_value",
            "curator_payout_value",
            "total_pending_payout_value",
            "promoted",
        ]
        for p in sbd_amounts:
            if p in output:
                if self.steem.rpc.get_use_appbase():
                    output[p] = (output.get(p, Amount("0.000 SBD", steem_instance=self.steem)))
                else:
                    output[p] = str(output.get(p, Amount("0.000 SBD", steem_instance=self.steem)))
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
        return self["category"]

    @property
    def parent_author(self):
        return self["parent_author"]

    @property
    def parent_permlink(self):
        return self["parent_permlink"]

    @property
    def title(self):
        return self["title"]

    @property
    def body(self):
        return self["body"]

    @property
    def json_metadata(self):
        return self["json_metadata"]

    def is_main_post(self):
        """ Retuns True if main post, and False if this is a comment (reply).
        """
        return self['depth'] == 0

    def is_comment(self):
        """ Retuns True if post is a comment
        """
        return self['depth'] > 0

    def get_reblogged_by(self, identifier=None):
        if not identifier:
            post_author = self["author"]
            post_permlink = self["permlink"]
        else:
            [post_author, post_permlink] = resolve_authorperm(identifier)
        if self.steem.rpc.get_use_appbase():
            return self.steem.rpc.get_reblogged_by({'author': post_author, 'permlink': post_permlink}, api="follow")['accounts']
        else:
            return self.steem.rpc.get_reblogged_by(post_author, post_permlink, api="follow")

    def get_votes(self):
        from .vote import ActiveVotes
        return ActiveVotes(self, steem_instance=self.steem)

    def upvote(self, weight=+100, voter=None):
        """ Upvote the post
            :param float weight: (optional) Weight for posting (-100.0 -
            +100.0) defaults to +100.0
            :param str voter: (optional) Voting account
        """
        if self.get('net_rshares', None) is None:
            raise VotingInvalidOnArchivedPost
        return self.vote(weight, voter=voter)

    def downvote(self, weight=-100, voter=None):
        """ Downvote the post
            :param float weight: (optional) Weight for posting (-100.0 -
            +100.0) defaults to -100.0
            :param str voter: (optional) Voting account
        """
        if self.get('net_rshares', None) is None:
            raise VotingInvalidOnArchivedPost
        return self.vote(weight, voter=voter)

    def vote(self, weight, account=None, identifier=None, **kwargs):
        """ Vote for a post
            :param str identifier: Identifier for the post to upvote Takes
                                   the form ``@author/permlink``
            :param float weight: Voting weight. Range: -100.0 - +100.0. May
                                 not be 0.0
            :param str account: Voter to use for voting. (Optional)
            If ``voter`` is not defines, the ``default_account`` will be taken
            or a ValueError will be raised
        """
        if not account:
            if "default_account" in self.steem.config:
                account = self.steem.config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self.steem)
        if not identifier:
            post_author = self["author"]
            post_permlink = self["permlink"]
        else:
            [post_author, post_permlink] = resolve_authorperm(identifier)

        STEEMIT_100_PERCENT = 10000
        STEEMIT_1_PERCENT = (STEEMIT_100_PERCENT / 100)
        vote_weight = int(weight * STEEMIT_1_PERCENT)
        if vote_weight > STEEMIT_100_PERCENT:
            vote_weight = STEEMIT_100_PERCENT
        if vote_weight < STEEMIT_100_PERCENT:
            vote_weight = -STEEMIT_100_PERCENT

        op = operations.Vote(
            **{
                "voter": account["name"],
                "author": post_author,
                "permlink": post_permlink,
                "weight": vote_weight
            })

        return self.steem.finalizeOp(op, account, "posting", **kwargs)

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
        if meta:
            if original_post["json_metadata"]:
                new_meta = original_post["json_metadata"].update(meta)
            else:
                new_meta = meta

        return self.steem.post(
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
        return self.steem.post(
            title,
            body,
            json_metadata=meta,
            author=author,
            reply_identifier=self.identifier)

    def delete(self, account=None, identifier=None):
        """ Delete an existing post/comment
            :param str identifier: Identifier for the post to upvote Takes
                                   the form ``@author/permlink``
            :param str account: Voter to use for voting. (Optional)
            If ``voter`` is not defines, the ``default_account`` will be taken
            or a ValueError will be raised
        """
        if not account:
            if "default_account" in self.steem.config:
                account = self.steem.config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self.steem)
        if not identifier:
            post_author = self["author"]
            post_permlink = self["permlink"]
        else:
            [post_author, post_permlink] = resolve_authorperm(identifier)
        op = operations.Delete_comment(
            **{"author": post_author,
               "permlink": post_permlink})
        return self.steem.finalizeOp(op, account, "posting")

    def resteem(self, identifier=None, account=None):
        """ Resteem a post
            :param str identifier: post identifier (@<account>/<permlink>)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        if not account:
            account = self.steem.configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self.steem)
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
        return self.steem.custom_json(
            id="follow", json_data=json_body, required_posting_auths=[account["name"]])


class RecentReplies(list):
    """ Obtain a list of recent replies

        :param str author: author
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, author, skip_own=True, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        self.steem.rpc.set_next_node_on_empty_reply(True)
        state = self.steem.rpc.get_state("/@%s/recent-replies" % author)
        replies = state["accounts"][author].get("recent_replies", [])
        comments = []
        for reply in replies:
            post = state["content"][reply]
            if skip_own and post["author"] == author:
                continue
            comments.append(Comment(post, lazy=True, steem_instance=self.steem))
        super(RecentReplies, self).__init__(comments)


class RecentByPath(list):
    """ Obtain a list of votes for an account

        :param str account: Account name
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, path="promoted", category=None, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        self.steem.rpc.set_next_node_on_empty_reply(True)
        state = self.steem.rpc.get_state("/" + path)
        replies = state["discussion_idx"][''].get(path, [])
        comments = []
        for reply in replies:
            post = state["content"][reply]
            if category is None or (category is not None and post["category"] != category):
                comments.append(Comment(post, lazy=True, steem_instance=self.steem))
        super(RecentByPath, self).__init__(comments)
