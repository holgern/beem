# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from .instance import shared_steem_instance
from .account import Account
from .comment import Comment
from .utils import resolve_authorperm
import logging
log = logging.getLogger(__name__)


class Query(dict):
    """
    :param int limit
    :param str tag
    :param int truncate_body
    :param array filter_tags
    :param array select_authors
    :param array select_tags
    :param str start_author
    :param str start_permlink
    :param str parent_author
    :param str parent_permlink
    """
    def __init__(self, limit=0, tag="", truncate_body=0,
                 filter_tags=[""], select_authors=[""], select_tags=[""],
                 start_author=None, start_permlink=None, parent_author=None, parent_permlink=None):
        self["limit"] = limit
        self["truncate_body"] = truncate_body
        self["tag"] = tag
        self["filter_tags"] = filter_tags
        self["select_authors"] = select_authors
        self["select_tags"] = select_tags
        self["start_author"] = start_author
        self["start_permlink"] = start_permlink
        self["parent_author"] = parent_author
        self["parent_permlink"] = parent_permlink


class Discussions_by_trending(list):
    """ get_discussions_by_trending

        :param str discussion_query
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, discussion_query, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        posts = self.steem.rpc.get_discussions_by_trending(discussion_query)
        super(Discussions_by_trending, self).__init__(
            [
                Comment(x)
                for x in posts
            ]
        )


class Comment_discussions_by_payout(list):
    """ get_comment_discussions_by_payout

        :param str discussion_query
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, discussion_query, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        posts = self.steem.rpc.get_comment_discussions_by_payout(discussion_query)
        super(Comment_discussions_by_payout, self).__init__(
            [
                Comment(x)
                for x in posts
            ]
        )


class Post_discussions_by_payout(list):
    """ get_post_discussions_by_payout

        :param str discussion_query
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, discussion_query, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        posts = self.steem.rpc.get_post_discussions_by_payout(discussion_query)
        super(Post_discussions_by_payout, self).__init__(
            [
                Comment(x)
                for x in posts
            ]
        )


class Discussions_by_created(list):
    """ get_discussions_by_created

        :param str discussion_query
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, discussion_query, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        posts = self.steem.rpc.get_discussions_by_created(discussion_query)
        super(Discussions_by_created, self).__init__(
            [
                Comment(x)
                for x in posts
            ]
        )


class Discussions_by_active(list):
    """ get_discussions_by_active

        :param str discussion_query
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, discussion_query, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        posts = self.steem.rpc.get_discussions_by_active(discussion_query)
        super(Discussions_by_active, self).__init__(
            [
                Comment(x)
                for x in posts
            ]
        )


class Discussions_by_cashout(list):
    """ get_discussions_by_cashout. This query seems to be broken at the moment.
        The output is always empty.

        :param str discussion_query
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, discussion_query, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        posts = self.steem.rpc.get_discussions_by_cashout(discussion_query)
        super(Discussions_by_cashout, self).__init__(
            [
                Comment(x)
                for x in posts
            ]
        )


class Discussions_by_payout(list):
    """ get_discussions_by_payout

        :param str discussion_query
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, discussion_query, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        posts = self.steem.rpc.get_discussions_by_payout(discussion_query)
        super(Discussions_by_payout, self).__init__(
            [
                Comment(x)
                for x in posts
            ]
        )


class Discussions_by_votes(list):
    """ get_discussions_by_votes

        :param str discussion_query
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, discussion_query, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        posts = self.steem.rpc.get_discussions_by_votes(discussion_query)
        super(Discussions_by_votes, self).__init__(
            [
                Comment(x)
                for x in posts
            ]
        )


class Discussions_by_children(list):
    """ get_discussions_by_children

        :param str discussion_query
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, discussion_query, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        posts = self.steem.rpc.get_discussions_by_children(discussion_query)
        super(Discussions_by_children, self).__init__(
            [
                Comment(x)
                for x in posts
            ]
        )


class Discussions_by_hot(list):
    """ get_discussions_by_hot

        :param str discussion_query
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, discussion_query, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        posts = self.steem.rpc.get_discussions_by_hot(discussion_query)
        super(Discussions_by_hot, self).__init__(
            [
                Comment(x)
                for x in posts
            ]
        )


class Discussions_by_feed(list):
    """ get_discussions_by_feed

        :param str discussion_query, tag musst be set to a username
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, discussion_query, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()

        self.steem.register_apis(["follow"])
        limit = discussion_query["limit"]
        account = discussion_query["tag"]
        entryId = 0
        posts = self.steem.rpc.get_feed(account, entryId, limit, api='follow')
        # posts = self.steem.rpc.get_discussions_by_feed(discussion_query, api='follow')
        super(Discussions_by_feed, self).__init__(
            [
                Comment(x["comment"])
                for x in posts
            ]
        )


class Discussions_by_blog(list):
    """ get_discussions_by_blog

        :param str discussion_query, tag musst be set to a username
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, discussion_query, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        self.steem.register_apis(["follow"])
        limit = discussion_query["limit"]
        account = discussion_query["tag"]
        entryId = 0
        posts = self.steem.rpc.get_feed(account, entryId, limit, api='follow')
        # posts = self.steem.rpc.get_discussions_by_blog(discussion_query)
        super(Discussions_by_blog, self).__init__(
            [
                Comment(x["comment"])
                for x in posts
            ]
        )


class Discussions_by_comments(list):
    """ get_discussions_by_comments

        :param str discussion_query
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, discussion_query, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        posts = self.steem.rpc.get_discussions_by_comments(discussion_query)
        super(Discussions_by_comments, self).__init__(
            [
                Comment(x)
                for x in posts
            ]
        )


class Discussions_by_promoted(list):
    """ get_discussions_by_promoted

        :param str discussion_query
        :param steem steem_instance: Steem() instance to use when accesing a RPC
    """
    def __init__(self, discussion_query, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        posts = self.steem.rpc.get_discussions_by_promoted(discussion_query)
        super(Discussions_by_promoted, self).__init__(
            [
                Comment(x)
                for x in posts
            ]
        )
