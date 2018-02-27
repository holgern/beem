# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from builtins import super
from .instance import shared_steem_instance
from .account import Account
from .amount import Amount
from .utils import resolve_authorperm, construct_authorperm, derive_permlink, keep_in_dict, make_patch, formatTimeString
from .blockchainobject import BlockchainObject
from .exceptions import ContentDoesNotExistsException, VotingInvalidOnArchivedPost
from beembase import operations
import json
import re
import logging
import difflib
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
        if isinstance(authorperm, str) and authorperm != "":
            [author, permlink] = resolve_authorperm(authorperm)
            self["id"] = 0
            self["author"] = author
            self["permlink"] = permlink
            self["authorperm"] = construct_authorperm(author, permlink)
        elif isinstance(authorperm, dict) and "author" in authorperm and "permlink" in authorperm:
            # self["author"] = authorperm["author"]
            # self["permlink"] = authorperm["permlink"]
            self["authorperm"] = construct_authorperm(authorperm["author"], authorperm["permlink"])
        super().__init__(
            authorperm,
            id_item="authorperm",
            lazy=lazy,
            full=full,
            steem_instance=steem_instance
        )
        self.identifier = self["authorperm"]
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
            if p in self and isinstance(self.get(p), str):
                self[p] = Amount(self.get(p, "0.000 SBD"))

        # turn json_metadata into python dict
        meta_str = self.get("json_metadata", "{}")
        if isinstance(meta_str, (str, bytes, bytearray)):
            self['json_metadata'] = json.loads(meta_str)
        self["tags"] = []
        if "tags" in self['json_metadata']:
            self["tags"] = self['json_metadata']["tags"]
        self['community'] = ''
        if 'community' in self['json_metadata']:
            self['community'] = self['json_metadata']['community']

    def refresh(self):
        [author, permlink] = resolve_authorperm(self.identifier)
        content = self.steem.rpc.get_content(author, permlink)
        if not content:
            raise ContentDoesNotExistsException
        super(Comment, self).__init__(content, id_item="authorperm", steem_instance=self.steem)
        self["authorperm"] = construct_authorperm(self["author"], self["permlink"])
        self.identifier = self["authorperm"]
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
            if p in self and isinstance(self.get(p), str):
                self[p] = Amount(self.get(p, "0.000 SBD"))
        # turn json_metadata into python dict

        meta_str = self.get("json_metadata", "{}")
        if isinstance(meta_str, (str, bytes, bytearray)):
            self['json_metadata'] = json.loads(meta_str)
        self["tags"] = []
        if "tags" in self['json_metadata']:
            self["tags"] = self['json_metadata']["tags"]
        self['community'] = ''
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
                output[p] = str(output.get(p, Amount("0.000 SBD")))
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
        self.steem.register_apis(["follow"])
        return self.steem.rpc.get_reblogged_by(post_author, post_permlink, api="follow")

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
                "weight": int(weight * STEEMIT_1_PERCENT)
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
                import json
                new_meta = original_post["json_metadata"].update(meta)
            else:
                new_meta = meta

        return self.post(
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
        return self.post(
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

    def post(self,
             title=None,
             body=None,
             author=None,
             permlink=None,
             reply_identifier=None,
             json_metadata=None,
             comment_options=None,
             community=None,
             tags=None,
             beneficiaries=None,
             self_vote=False):
        """ Create a new post.
        If this post is intended as a reply/comment, `reply_identifier` needs
        to be set with the identifier of the parent post/comment (eg.
        `@author/permlink`).
        Optionally you can also set json_metadata, comment_options and upvote
        the newly created post as an author.
        Setting category, tags or community will override the values provided
        in json_metadata and/or comment_options where appropriate.
        Args:
        title (str): Title of the post
        body (str): Body of the post/comment
        author (str): Account are you posting from
        permlink (str): Manually set the permlink (defaults to None).
            If left empty, it will be derived from title automatically.
        reply_identifier (str): Identifier of the parent post/comment (only
            if this post is a reply/comment).
        json_metadata (str, dict): JSON meta object that can be attached to
            the post.
        comment_options (str, dict): JSON options object that can be
            attached to the post.
        Example::
            comment_options = {
                'max_accepted_payout': '1000000.000 SBD',
                'percent_steem_dollars': 10000,
                'allow_votes': True,
                'allow_curation_rewards': True,
                'extensions': [[0, {
                    'beneficiaries': [
                        {'account': 'account1', 'weight': 5000},
                        {'account': 'account2', 'weight': 5000},
                    ]}
                ]]
            }
        community (str): (Optional) Name of the community we are posting
            into. This will also override the community specified in
            `json_metadata`.
        tags (str, list): (Optional) A list of tags (5 max) to go with the
            post. This will also override the tags specified in
            `json_metadata`. The first tag will be used as a 'category'. If
            provided as a string, it should be space separated.
        beneficiaries (list of dicts): (Optional) A list of beneficiaries
            for posting reward distribution. This argument overrides
            beneficiaries as specified in `comment_options`.
        For example, if we would like to split rewards between account1 and
        account2::
            beneficiaries = [
                {'account': 'account1', 'weight': 5000},
                {'account': 'account2', 'weight': 5000}
            ]
        self_vote (bool): (Optional) Upvote the post as author, right after
            posting.
        """

        # prepare json_metadata
        json_metadata = json_metadata or {}
        if isinstance(json_metadata, str):
            json_metadata = json.loads(json_metadata)

        # override the community
        if community:
            json_metadata.update({'community': community})

        if title is None:
            title = self["title"]
        if body is None:
            body = self["body"]
        if author is None and permlink is None:
            [author, permlink] = resolve_authorperm(self.identifier)
        else:
            if author is None:
                author = self["author"]
            if permlink is None:
                permlink = self["permlink"]
        account = Account(author, steem_instance=self.steem)
        # deal with the category and tags
        if isinstance(tags, str):
            tags = list(set([_f for _f in (re.split("[\W_]", tags)) if _f]))

        category = None
        tags = tags or json_metadata.get('tags', [])
        if tags:
            if len(tags) > 5:
                raise ValueError('Can only specify up to 5 tags per post.')

            # first tag should be a category
            category = tags[0]
            json_metadata.update({"tags": tags})

        # can't provide a category while replying to a post
        if reply_identifier and category:
            category = None

        # deal with replies/categories
        if reply_identifier:
            parent_author, parent_permlink = resolve_authorperm(
                reply_identifier)
            if not permlink:
                permlink = derive_permlink(title, parent_permlink)
        elif category:
            parent_permlink = derive_permlink(category)
            parent_author = ""
            if not permlink:
                permlink = derive_permlink(title)
        else:
            parent_author = ""
            parent_permlink = ""
            if not permlink:
                permlink = derive_permlink(title)

        post_op = operations.Comment(
            **{
                "parent_author": parent_author,
                "parent_permlink": parent_permlink,
                "author": author,
                "permlink": permlink,
                "title": title,
                "body": body,
                "json_metadata": json_metadata
            })
        ops = [post_op]

        # if comment_options are used, add a new op to the transaction
        if comment_options or beneficiaries:
            options = keep_in_dict(comment_options or {}, [
                'max_accepted_payout', 'percent_steem_dollars', 'allow_votes',
                'allow_curation_rewards', 'extensions'
            ])
            # override beneficiaries extension
            if beneficiaries:
                # validate schema
                # or just simply vo.Schema([{'account': str, 'weight': int}])

                for b in beneficiaries:
                    if 'account' not in b:
                        raise ValueError(
                            "beneficiaries need an account field!"
                        )
                    if 'weight' not in b:
                        b['weight'] = 10000
                    if len(b['account']) > 16:
                        raise ValueError(
                            "beneficiaries error, account name length >16!"
                        )
                    if b['weight'] < 1 or b['weight'] > 10000:
                        raise ValueError(
                            "beneficiaries error, 1<=weight<=10000!"
                        )

                options['beneficiaries'] = beneficiaries

            default_max_payout = "1000000.000 SBD"
            comment_op = operations.Comment_options(
                **{
                    "author":
                    author,
                    "permlink":
                    permlink,
                    "max_accepted_payout":
                    options.get("max_accepted_payout", default_max_payout),
                    "percent_steem_dollars":
                    int(options.get("percent_steem_dollars", 10000)),
                    "allow_votes":
                    options.get("allow_votes", True),
                    "allow_curation_rewards":
                    options.get("allow_curation_rewards", True),
                    "extensions":
                    options.get("extensions", []),
                    "beneficiaries":
                    options.get("beneficiaries"),
                })
            ops.append(comment_op)

        if self_vote:
            vote_op = operations.Vote(
                **{
                    'voter': author,
                    'author': author,
                    'permlink': permlink,
                    'weight': 10000,
                })
            ops.append(vote_op)

        return self.steem.finalizeOp(ops, account, "posting")

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

    def comment_options(self, options, identifier=None, account=None):
        """ Set the comment options
            :param str identifier: Post identifier
            :param dict options: The options to define.
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
            For the options, you have these defaults:::
                    {
                        "author": "",
                        "permlink": "",
                        "max_accepted_payout": "1000000.000 SBD",
                        "percent_steem_dollars": 10000,
                        "allow_votes": True,
                        "allow_curation_rewards": True,
                    }
        """
        if not account:
            account = self.steem.configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self.steem)
        if identifier is None:
            identifier = self.identifier
        author, permlink = resolve_authorperm(identifier)
        default_max_payout = "1000000.000 SBD"
        STEEMIT_100_PERCENT = 10000
        STEEMIT_1_PERCENT = (STEEMIT_100_PERCENT / 100)
        op = operations.Comment_options(
            **{
                "author":
                author,
                "permlink":
                permlink,
                "max_accepted_payout":
                options.get("max_accepted_payout", default_max_payout),
                "percent_steem_dollars":
                options.get("percent_steem_dollars", 100) * STEEMIT_1_PERCENT,
                "allow_votes":
                options.get("allow_votes", True),
                "allow_curation_rewards":
                options.get("allow_curation_rewards", True),
            })
        return self.commit.finalizeOp(op, account, "posting")


class RecentReplies(list):
    """ Obtain a list of recent replies

        :param str author: author
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, author, skip_own=True, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
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

        state = self.steem.rpc.get_state("/" + path)
        replies = state["discussion_idx"][''].get(path, [])
        comments = []
        for reply in replies:
            post = state["content"][reply]
            if category is not None and post["category"] != category:
                continue
            comments.append(Comment(post, lazy=True, steem_instance=self.steem))
        super(RecentByPath, self).__init__(comments)
