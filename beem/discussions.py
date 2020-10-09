# -*- coding: utf-8 -*-
from .instance import shared_blockchain_instance
from .account import Account
from .comment import Comment
from .utils import resolve_authorperm
import logging
log = logging.getLogger(__name__)


class Query(dict):
    """ Query to be used for all discussion queries

        :param int limit: limits the number of posts
        :param str tag: tag query
        :param int truncate_body:
        :param array filter_tags:
        :param array select_authors:
        :param array select_tags:
        :param str start_author:
        :param str start_permlink:
        :param str start_tag:
        :param str parent_author:
        :param str parent_permlink:
        :param str start_parent_author:
        :param str before_date:
        :param str author: Author (see Discussions_by_author_before_date)

        .. testcode::

            from beem.discussions import Query
            query = Query(limit=10, tag="steemit")

    """
    def __init__(self, limit=0, tag="", truncate_body=0,
                 filter_tags=[], select_authors=[], select_tags=[],
                 start_author=None, start_permlink=None,
                 start_tag=None, parent_author=None,
                 parent_permlink=None, start_parent_author=None,
                 before_date=None, author=None):
        self["limit"] = limit
        self["truncate_body"] = truncate_body
        self["tag"] = tag
        self["filter_tags"] = filter_tags
        self["select_authors"] = select_authors
        self["select_tags"] = select_tags
        self["start_author"] = start_author
        self["start_permlink"] = start_permlink
        self["start_tag"] = start_tag
        self["parent_author"] = parent_author
        self["parent_permlink"] = parent_permlink
        self["start_parent_author"] = start_parent_author
        self["before_date"] = before_date
        self["author"] = author


class Discussions(object):
    """ Get Discussions

        :param Steem blockchain_instance: Steem instance

    """
    def __init__(self, lazy=False, use_appbase=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        self.lazy = lazy
        self.use_appbase = use_appbase

    def get_discussions(self, discussion_type, discussion_query, limit=1000, raw_data=False):
        """ Get Discussions

            :param str discussion_type: Defines the used discussion query
            :param Query discussion_query: Defines the parameter for
                   searching posts
            :param bool raw_data: returns list of comments when False, default is False

            .. testcode::

                from beem.discussions import Query, Discussions
                query = Query(limit=51, tag="steemit")
                discussions = Discussions()
                count = 0
                for d in discussions.get_discussions("tags", query, limit=200):
                    print(("%d. " % (count + 1)) + str(d))
                    count += 1

        """
        if limit >= 100 and discussion_query["limit"] == 0:
            discussion_query["limit"] = 100
        elif limit < 100 and discussion_query["limit"] == 0:
            discussion_query["limit"] = limit
        query_count = 0
        found_more_than_start_entry = True
        if "start_author" in discussion_query:
            start_author = discussion_query["start_author"]
        else:
            start_author = None
        if "start_permlink" in discussion_query:
            start_permlink = discussion_query["start_permlink"]
        else:
            start_permlink = None
        if "start_tag" in discussion_query:
            start_tag = discussion_query["start_tag"]
        else:
            start_tag = None
        if "start_parent_author" in discussion_query:
            start_parent_author = discussion_query["start_parent_author"]
        else:
            start_parent_author = None
        if not discussion_query["before_date"]:
            discussion_query["before_date"] = "1970-01-01T00:00:00"
        while (query_count < limit and found_more_than_start_entry):
            rpc_query_count = 0
            dd = None
            discussion_query["start_author"] = start_author
            discussion_query["start_permlink"] = start_permlink
            discussion_query["start_tag"] = start_tag
            discussion_query["start_parent_author"] = start_parent_author
            if discussion_type == "trending":
                dd = Discussions_by_trending(discussion_query, blockchain_instance=self.blockchain, lazy=self.lazy)
            elif discussion_type == "author_before_date":
                dd = Discussions_by_author_before_date(author=discussion_query["author"],
                                                       start_permlink=discussion_query["start_permlink"],
                                                       before_date=discussion_query["before_date"],
                                                       limit=discussion_query["limit"],
                                                       blockchain_instance=self.blockchain, lazy=self.lazy)
            elif discussion_type == "payout":
                dd = Comment_discussions_by_payout(discussion_query, blockchain_instance=self.blockchain, lazy=self.lazy, use_appbase=self.use_appbase, raw_data=raw_data)
            elif discussion_type == "post_payout":
                dd = Post_discussions_by_payout(discussion_query, blockchain_instance=self.blockchain, lazy=self.lazy, use_appbase=self.use_appbase, raw_data=raw_data)
            elif discussion_type == "created":
                dd = Discussions_by_created(discussion_query, blockchain_instance=self.blockchain, lazy=self.lazy, use_appbase=self.use_appbase, raw_data=raw_data)
            elif discussion_type == "active":
                dd = Discussions_by_active(discussion_query, blockchain_instance=self.blockchain, lazy=self.lazy, use_appbase=self.use_appbase, raw_data=raw_data)
            elif discussion_type == "cashout":
                dd = Discussions_by_cashout(discussion_query, blockchain_instance=self.blockchain, lazy=self.lazy, use_appbase=self.use_appbase, raw_data=raw_data)
            elif discussion_type == "votes":
                dd = Discussions_by_votes(discussion_query, blockchain_instance=self.blockchain, lazy=self.lazy, use_appbase=self.use_appbase, raw_data=raw_data)
            elif discussion_type == "children":
                dd = Discussions_by_children(discussion_query, blockchain_instance=self.blockchain, lazy=self.lazy, use_appbase=self.use_appbase, raw_data=raw_data)
            elif discussion_type == "hot":
                dd = Discussions_by_hot(discussion_query, blockchain_instance=self.blockchain, lazy=self.lazy, use_appbase=self.use_appbase, raw_data=raw_data)
            elif discussion_type == "feed":
                dd = Discussions_by_feed(discussion_query, blockchain_instance=self.blockchain, lazy=self.lazy, use_appbase=self.use_appbase, raw_data=raw_data)
            elif discussion_type == "blog":
                dd = Discussions_by_blog(discussion_query, blockchain_instance=self.blockchain, lazy=self.lazy, use_appbase=self.use_appbase, raw_data=raw_data)
            elif discussion_type == "comments":
                dd = Discussions_by_comments(discussion_query, blockchain_instance=self.blockchain, lazy=self.lazy, use_appbase=self.use_appbase, raw_data=raw_data)
            elif discussion_type == "promoted":
                dd = Discussions_by_promoted(discussion_query, blockchain_instance=self.blockchain, lazy=self.lazy, use_appbase=self.use_appbase, raw_data=raw_data)
            elif discussion_type == "replies":
                dd = Replies_by_last_update(discussion_query, blockchain_instance=self.blockchain, lazy=self.lazy, use_appbase=self.use_appbase, raw_data=raw_data)
            elif discussion_type == "tags":
                dd = Trending_tags(discussion_query, blockchain_instance=self.blockchain, lazy=self.lazy, use_appbase=self.use_appbase)
            else:
                raise ValueError("Wrong discussion_type")
            if not dd:
                return

            for d in dd:
                double_result = False
                if discussion_type == "tags":
                    if query_count != 0 and rpc_query_count == 0 and (d["name"] == start_tag):
                        double_result = True
                        if len(dd) == 1:
                            found_more_than_start_entry = False
                    start_tag = d["name"]
                elif discussion_type == "replies":
                    if query_count != 0 and rpc_query_count == 0 and (d["author"] == start_parent_author and d["permlink"] == start_permlink):
                        double_result = True
                        if len(dd) == 1:
                            found_more_than_start_entry = False
                    start_parent_author = d["author"]
                    start_permlink = d["permlink"]
                else:
                    if query_count != 0 and rpc_query_count == 0 and (d["author"] == start_author and d["permlink"] == start_permlink):
                        double_result = True
                        if len(dd) == 1:
                            found_more_than_start_entry = False
                    start_author = d["author"]
                    start_permlink = d["permlink"]
                rpc_query_count += 1
                if not double_result:
                    query_count += 1
                    if query_count <= limit:
                        yield d


class Discussions_by_trending(list):
    """ Get Discussions by trending

        :param Query discussion_query: Defines the parameter for
            searching posts
        :param Steem blockchain_instance: Steem instance
        :param bool raw_data: returns list of comments when False, default is False

        .. testcode::

            from beem.discussions import Query, Discussions_by_trending
            q = Query(limit=10, tag="steem")
            for h in Discussions_by_trending(q):
                print(h)

    """
    def __init__(self, discussion_query, lazy=False, use_appbase=False, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        reduced_query = {}
        for key in ["tag", "limit", "filter_tags", "select_authors", "select_tags", "truncate_body",
                    "start_author", "start_permlink"]:
            if key in discussion_query:
                reduced_query[key] = discussion_query[key]
        self.blockchain.rpc.set_next_node_on_empty_reply(self.blockchain.rpc.get_use_appbase() and use_appbase)
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            posts = self.blockchain.rpc.get_discussions_by_trending(reduced_query, api="tags")['discussions']
        if len(posts) == 0:
            posts = self.blockchain.rpc.get_discussions_by_trending(reduced_query)
        if raw_data:
            super(Discussions_by_trending, self).__init__(
                [
                    x
                    for x in posts
                ]
            )
        else:
            super(Discussions_by_trending, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )


class Discussions_by_author_before_date(list):
    """ Get Discussions by author before date

        .. note:: To retrieve discussions before date, the time of creation
                  of the discussion @author/start_permlink must be older than
                  the specified before_date parameter.

        :param str author: Defines the author *(required)*
        :param str start_permlink: Defines the permlink of a starting discussion
        :param str before_date: Defines the before date for query
        :param int limit: Defines the limit of discussions
        :param bool use_appbase: use condenser call when set to False, default is False
        :param bool raw_data: returns list of comments when False, default is False
        :param Steem blockchain_instance: Steem instance

        .. testcode::

            from beem.discussions import Query, Discussions_by_author_before_date
            for h in Discussions_by_author_before_date(limit=10, author="gtg"):
                print(h)

    """
    def __init__(self, author="", start_permlink="", before_date="1970-01-01T00:00:00", limit=100, lazy=False, use_appbase=False, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        self.blockchain.rpc.set_next_node_on_empty_reply(self.blockchain.rpc.get_use_appbase() and use_appbase)
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            discussion_query = {"author": author, "start_permlink": start_permlink, "before_date": before_date, "limit": limit}
            posts = self.blockchain.rpc.get_discussions_by_author_before_date(discussion_query, api="tags")['discussions']
        if len(posts) == 0:
            posts = self.blockchain.rpc.get_discussions_by_author_before_date(author, start_permlink, before_date, limit)
        if raw_data:
            super(Discussions_by_author_before_date, self).__init__(
                [
                    x
                    for x in posts
                ]
            )
        else:
            super(Discussions_by_author_before_date, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )


class Comment_discussions_by_payout(list):
    """ Get comment_discussions_by_payout

        :param Query discussion_query: Defines the parameter for
            searching posts
        :param bool use_appbase: use condenser call when set to False, default is False
        :param bool raw_data: returns list of comments when False, default is False
        :param Steem blockchain_instance: Steem instance

        .. testcode::

            from beem.discussions import Query, Comment_discussions_by_payout
            q = Query(limit=10)
            for h in Comment_discussions_by_payout(q):
                print(h)

    """
    def __init__(self, discussion_query, lazy=False, use_appbase=False, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        reduced_query = {}
        for key in ["tag", "limit", "filter_tags", "select_authors", "select_tags", "truncate_body",
                    "start_author", "start_permlink"]:
            if key in discussion_query:
                reduced_query[key] = discussion_query[key]
        self.blockchain.rpc.set_next_node_on_empty_reply(self.blockchain.rpc.get_use_appbase() and use_appbase)
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            posts = self.blockchain.rpc.get_comment_discussions_by_payout(reduced_query, api="tags")['discussions']
        if len(posts) == 0:
            posts = self.blockchain.rpc.get_comment_discussions_by_payout(reduced_query)
        if raw_data:
            super(Comment_discussions_by_payout, self).__init__(
                [
                    x
                    for x in posts
                ]
            )
        else:
            super(Comment_discussions_by_payout, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )


class Post_discussions_by_payout(list):
    """ Get post_discussions_by_payout

        :param Query discussion_query: Defines the parameter for
            searching posts
        :param bool use_appbase: use condenser call when set to False, default is False
        :param bool raw_data: returns list of comments when False, default is False
        :param Steem blockchain_instance: Steem instance

        .. testcode::

            from beem.discussions import Query, Post_discussions_by_payout
            q = Query(limit=10)
            for h in Post_discussions_by_payout(q):
                print(h)

    """
    def __init__(self, discussion_query, lazy=False, use_appbase=False, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        reduced_query = {}
        for key in ["tag", "limit", "filter_tags", "select_authors", "select_tags", "truncate_body",
                    "start_author", "start_permlink"]:
            if key in discussion_query:
                reduced_query[key] = discussion_query[key]        
        self.blockchain.rpc.set_next_node_on_empty_reply(self.blockchain.rpc.get_use_appbase() and use_appbase)
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            posts = self.blockchain.rpc.get_post_discussions_by_payout(reduced_query, api="tags")['discussions']
        if len(posts) == 0:
            posts = self.blockchain.rpc.get_post_discussions_by_payout(reduced_query)
        if raw_data:
            super(Post_discussions_by_payout, self).__init__(
                [
                    x
                    for x in posts
                ]
            )
        else:
            super(Post_discussions_by_payout, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )


class Discussions_by_created(list):
    """ Get discussions_by_created

        :param Query discussion_query: Defines the parameter for
            searching posts
        :param bool use_appbase: use condenser call when set to False, default is False
        :param bool raw_data: returns list of comments when False, default is False
        :param Steem blockchain_instance: Steem instance

        .. testcode::

            from beem.discussions import Query, Discussions_by_created
            q = Query(limit=10)
            for h in Discussions_by_created(q):
                print(h)

    """
    def __init__(self, discussion_query, lazy=False, use_appbase=False, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        reduced_query = {}
        for key in ["tag", "limit", "filter_tags", "select_authors", "select_tags", "truncate_body",
                    "start_author", "start_permlink"]:
            if key in discussion_query:
                reduced_query[key] = discussion_query[key]        
        self.blockchain.rpc.set_next_node_on_empty_reply(self.blockchain.rpc.get_use_appbase() and use_appbase)
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            posts = self.blockchain.rpc.get_discussions_by_created(reduced_query, api="tags")['discussions']
        if len(posts) == 0:
            posts = self.blockchain.rpc.get_discussions_by_created(reduced_query)
        if raw_data:
            super(Discussions_by_created, self).__init__(
                [
                    x
                    for x in posts
                ]
            )
        else:
            super(Discussions_by_created, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )


class Discussions_by_active(list):
    """ get_discussions_by_active

        :param Query discussion_query: Defines the parameter
            searching posts
        :param bool use_appbase: use condenser call when set to False, default is False
        :param bool raw_data: returns list of comments when False, default is False
        :param Steem blockchain_instance: Steem() instance to use when accesing a RPC

        .. testcode::

            from beem.discussions import Query, Discussions_by_active
            q = Query(limit=10)
            for h in Discussions_by_active(q):
                print(h)

    """
    def __init__(self, discussion_query, lazy=False, use_appbase=False, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        reduced_query = {}
        for key in ["tag", "limit", "filter_tags", "select_authors", "select_tags", "truncate_body",
                    "start_author", "start_permlink"]:
            if key in discussion_query:
                reduced_query[key] = discussion_query[key]        
        self.blockchain.rpc.set_next_node_on_empty_reply(self.blockchain.rpc.get_use_appbase() and use_appbase)
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            posts = self.blockchain.rpc.get_discussions_by_active(reduced_query, api="tags")['discussions']
        if len(posts) == 0:
            posts = self.blockchain.rpc.get_discussions_by_active(reduced_query)
        if raw_data:
            super(Discussions_by_active, self).__init__(
                [
                    x
                    for x in posts
                ]
            )
        else:
            super(Discussions_by_active, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )


class Discussions_by_cashout(list):
    """ Get discussions_by_cashout. This query seems to be broken at the moment.
        The output is always empty.

        :param Query discussion_query: Defines the parameter
            searching posts
        :param bool use_appbase: use condenser call when set to False, default is False
        :param bool raw_data: returns list of comments when False, default is False
        :param Steem blockchain_instance: Steem instance

        .. testcode::

            from beem.discussions import Query, Discussions_by_cashout
            q = Query(limit=10)
            for h in Discussions_by_cashout(q):
                print(h)

    """
    def __init__(self, discussion_query, lazy=False, use_appbase=False, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        reduced_query = {}
        for key in ["tag", "limit", "filter_tags", "select_authors", "select_tags", "truncate_body",
                    "start_author", "start_permlink"]:
            if key in discussion_query:
                reduced_query[key] = discussion_query[key]        
        self.blockchain.rpc.set_next_node_on_empty_reply(self.blockchain.rpc.get_use_appbase() and use_appbase)
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            posts = self.blockchain.rpc.get_discussions_by_cashout(reduced_query, api="tags")['discussions']
        if len(posts) == 0:
            posts = self.blockchain.rpc.get_discussions_by_cashout(reduced_query)
        if raw_data:
            super(Discussions_by_cashout, self).__init__(
                [
                    x
                    for x in posts
                ]
            )
        else:
            super(Discussions_by_cashout, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )


class Discussions_by_votes(list):
    """ Get discussions_by_votes

        :param Query discussion_query: Defines the parameter
            searching posts
        :param bool use_appbase: use condenser call when set to False, default is False
        :param bool raw_data: returns list of comments when False, default is False
        :param Steem blockchain_instance: Steem instance

        .. testcode::

            from beem.discussions import Query, Discussions_by_votes
            q = Query(limit=10)
            for h in Discussions_by_votes(q):
                print(h)

    """
    def __init__(self, discussion_query, lazy=False, use_appbase=False, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        reduced_query = {}
        for key in ["tag", "limit", "filter_tags", "select_authors", "select_tags", "truncate_body",
                    "start_author", "start_permlink"]:
            if key in discussion_query:
                reduced_query[key] = discussion_query[key]        
        self.blockchain.rpc.set_next_node_on_empty_reply(self.blockchain.rpc.get_use_appbase() and use_appbase)
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            posts = self.blockchain.rpc.get_discussions_by_votes(reduced_query, api="tags")['discussions']
        if len(posts) == 0:
            posts = self.blockchain.rpc.get_discussions_by_votes(reduced_query)
        if raw_data:
            super(Discussions_by_votes, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )
        else:
            super(Discussions_by_votes, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )


class Discussions_by_children(list):
    """ Get discussions by children

        :param Query discussion_query: Defines the parameter
            searching posts
        :param bool use_appbase: use condenser call when set to False, default is False
        :param bool raw_data: returns list of comments when False, default is False
        :param Steem blockchain_instance: Steem instance

        .. testcode::

            from beem.discussions import Query, Discussions_by_children
            q = Query(limit=10)
            for h in Discussions_by_children(q):
                print(h)

    """
    def __init__(self, discussion_query, lazy=False, use_appbase=False, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        reduced_query = {}
        for key in ["tag", "limit", "filter_tags", "select_authors", "select_tags", "truncate_body",
                    "start_author", "start_permlink"]:
            if key in discussion_query:
                reduced_query[key] = discussion_query[key]         
        self.blockchain.rpc.set_next_node_on_empty_reply(self.blockchain.rpc.get_use_appbase() and use_appbase)
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            posts = self.blockchain.rpc.get_discussions_by_children(reduced_query, api="tags")['discussions']
        if len(posts) == 0:
            posts = self.blockchain.rpc.get_discussions_by_children(reduced_query)
        if raw_data:
            super(Discussions_by_votes, self).__init__(
                [
                    x
                    for x in posts
                ]
            )
        else:
            super(Discussions_by_children, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )


class Discussions_by_hot(list):
    """ Get discussions by hot

        :param Query discussion_query: Defines the parameter
            searching posts
        :param bool use_appbase: use condenser call when set to False, default is False
        :param bool raw_data: returns list of comments when False, default is False
        :param Steem blockchain_instance: Steem instance

        .. testcode::

            from beem.discussions import Query, Discussions_by_hot
            q = Query(limit=10, tag="steem")
            for h in Discussions_by_hot(q):
                print(h)

    """
    def __init__(self, discussion_query, lazy=False, use_appbase=False, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        reduced_query = {}
        for key in ["tag", "limit", "filter_tags", "select_authors", "select_tags", "truncate_body",
                    "start_author", "start_permlink"]:
            if key in discussion_query:
                reduced_query[key] = discussion_query[key]        
        self.blockchain.rpc.set_next_node_on_empty_reply(self.blockchain.rpc.get_use_appbase() and use_appbase)
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            posts = self.blockchain.rpc.get_discussions_by_hot(reduced_query, api="tags")['discussions']
        if len(posts) == 0:
            posts = self.blockchain.rpc.get_discussions_by_hot(reduced_query)
        if raw_data:
            super(Discussions_by_hot, self).__init__(
                [
                    x
                    for x in posts
                ]
            )
        else:
            super(Discussions_by_hot, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )


class Discussions_by_feed(list):
    """ Get discussions by feed

        :param Query discussion_query: Defines the parameter
            searching posts, tag musst be set to a username
        :param bool use_appbase: use condenser call when set to False, default is False
        :param bool raw_data: returns list of comments when False, default is False
        :param Steem blockchain_instance: Steem instance

        .. testcode::

            from beem.discussions import Query, Discussions_by_feed
            q = Query(limit=10, tag="steem")
            for h in Discussions_by_feed(q):
                print(h)

    """
    def __init__(self, discussion_query, lazy=False, use_appbase=False, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        self.blockchain.rpc.set_next_node_on_empty_reply(self.blockchain.rpc.get_use_appbase() and use_appbase)
        reduced_query = {}
        for key in ["tag", "limit", "filter_tags", "select_authors", "select_tags", "truncate_body",
                    "start_author", "start_permlink"]:
            if key in discussion_query:
                reduced_query[key] = discussion_query[key]
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            posts = self.blockchain.rpc.get_discussions_by_feed(reduced_query, api="tags")['discussions']
        if len(posts) == 0:
            # limit = discussion_query["limit"]
            # account = discussion_query["tag"]
            # entryId = 0
            # posts = self.blockchain.rpc.get_feed(account, entryId, limit, api='follow')["comment"]
            posts = self.blockchain.rpc.get_discussions_by_feed(reduced_query)
        if raw_data:
            super(Discussions_by_feed, self).__init__(
                [
                    x
                    for x in posts
                ]
            )            
        else:
            super(Discussions_by_feed, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )


class Discussions_by_blog(list):
    """ Get discussions by blog

        :param Query discussion_query: Defines the parameter
            searching posts, tag musst be set to a username
        :param bool use_appbase: use condenser call when set to False, default is False
        :param bool raw_data: returns list of comments when False, default is False
        :param Steem blockchain_instance: Steem instance

        .. testcode::

            from beem.discussions import Query, Discussions_by_blog
            q = Query(limit=10)
            for h in Discussions_by_blog(q):
                print(h)

    """
    def __init__(self, discussion_query, lazy=False, use_appbase=False, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        reduced_query = {}
        for key in ["tag", "limit", "filter_tags", "select_authors", "select_tags", "truncate_body",
                    "start_author", "start_permlink"]:
            if key in discussion_query:
                reduced_query[key] = discussion_query[key]     
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            self.blockchain.rpc.set_next_node_on_empty_reply(True)
            posts = self.blockchain.rpc.get_discussions_by_blog(reduced_query, api="tags")
            if 'discussions' in posts:
                posts = posts['discussions']  # inconsistent format across node types
        if len(posts) == 0:
            self.blockchain.rpc.set_next_node_on_empty_reply(False)
            # limit = discussion_query["limit"]
            # account = discussion_query["tag"]
            # entryId = 0
            # posts = self.blockchain.rpc.get_feed(account, entryId, limit, api='follow')
            posts = self.blockchain.rpc.get_discussions_by_blog(reduced_query)
        if raw_data:
            super(Discussions_by_blog, self).__init__(
                [
                    x
                    for x in posts
                ]
            )
        else:
            super(Discussions_by_blog, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )


class Discussions_by_comments(list):
    """ Get discussions by comments

        :param Query discussion_query: Defines the parameter
            searching posts, start_author and start_permlink must be set.
        :param bool use_appbase: use condenser call when set to False, default is False
        :param bool raw_data: returns list of comments when False, default is False
        :param Steem blockchain_instance: Steem instance

        .. testcode::

            from beem.discussions import Query, Discussions_by_comments
            q = Query(limit=10, start_author="steemit", start_permlink="firstpost")
            for h in Discussions_by_comments(q):
                print(h)

    """
    def __init__(self, discussion_query, lazy=False, use_appbase=False, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        reduced_query = {}
        for key in ["start_author", "start_permlink", "limit"]:
            if key in discussion_query:
                reduced_query[key] = discussion_query[key]         
        self.blockchain.rpc.set_next_node_on_empty_reply(self.blockchain.rpc.get_use_appbase() and use_appbase)
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            posts = self.blockchain.rpc.get_discussions_by_comments(reduced_query, api="tags")
            if 'discussions' in posts:
                posts = posts['discussions']  # inconsistent format across node types
        if len(posts) == 0:
            posts = self.blockchain.rpc.get_discussions_by_comments(reduced_query)
        if raw_data:
            super(Discussions_by_comments, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )            
        else:
            super(Discussions_by_comments, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )


class Discussions_by_promoted(list):
    """ Get discussions by promoted

        :param Query discussion_query: Defines the parameter
            searching posts
        :param bool use_appbase: use condenser call when set to False, default is False
        :param bool raw_data: returns list of comments when False, default is False
        :param Steem blockchain_instance: Steem instance

        .. testcode::

            from beem.discussions import Query, Discussions_by_promoted
            q = Query(limit=10, tag="steem")
            for h in Discussions_by_promoted(q):
                print(h)

    """
    def __init__(self, discussion_query, lazy=False, use_appbase=False, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        reduced_query = {}
        for key in ["tag", "limit", "filter_tags", "select_authors", "select_tags", "truncate_body",
                    "start_author", "start_permlink"]:
            if key in discussion_query:
                reduced_query[key] = discussion_query[key]        
        self.blockchain.rpc.set_next_node_on_empty_reply(self.blockchain.rpc.get_use_appbase() and use_appbase)
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            posts = self.blockchain.rpc.get_discussions_by_promoted(reduced_query, api="tags")['discussions']
        if len(posts) == 0:
            posts = self.blockchain.rpc.get_discussions_by_promoted(reduced_query)
        if raw_data:
            super(Discussions_by_promoted, self).__init__(
                [
                    x
                    for x in posts
                ]
            )
        else:
            super(Discussions_by_promoted, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )


class Replies_by_last_update(list):
    """ Returns a list of replies by last update

        :param Query discussion_query: Defines the parameter
            searching posts start_parent_author and start_permlink must be set.
        :param bool use_appbase: use condenser call when set to False, default is False
        :param bool raw_data: returns list of comments when False, default is False
        :param Steem blockchain_instance: Steem instance

        .. testcode::

            from beem.discussions import Query, Replies_by_last_update
            q = Query(limit=10, start_parent_author="steemit", start_permlink="firstpost")
            for h in Replies_by_last_update(q):
                print(h)

    """
    def __init__(self, discussion_query, lazy=False, use_appbase=False, raw_data=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        self.blockchain.rpc.set_next_node_on_empty_reply(self.blockchain.rpc.get_use_appbase() and use_appbase)
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            try:
                posts = self.blockchain.rpc.get_replies_by_last_update(discussion_query, api="tags")
                if 'discussions' in posts:
                    posts = posts['discussions']
            except:
                posts = self.blockchain.rpc.get_replies_by_last_update(discussion_query["start_author"], discussion_query["start_permlink"], discussion_query["limit"])
        if len(posts) == 0:
            posts = self.blockchain.rpc.get_replies_by_last_update(discussion_query["start_author"], discussion_query["start_permlink"], discussion_query["limit"])
        if posts is None:
            posts = []
        if raw_data:
            super(Replies_by_last_update, self).__init__(
                [
                    x
                    for x in posts
                ]
            )
        else:
            super(Replies_by_last_update, self).__init__(
                [
                    Comment(x, lazy=lazy, blockchain_instance=self.blockchain)
                    for x in posts
                ]
            )


class Trending_tags(list):
    """ Returns the list of trending tags.

        :param Query discussion_query: Defines the parameter
            searching posts, start_tag can be set.
            :param bool use_appbase: use condenser call when set to False, default is False
        :param Steem blockchain_instance: Steem instance

        .. testcode::

            from beem.discussions import Query, Trending_tags
            q = Query(limit=10, start_tag="")
            for h in Trending_tags(q):
                print(h)

    """
    def __init__(self, discussion_query, lazy=False, use_appbase=False, blockchain_instance=None, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        self.blockchain.rpc.set_next_node_on_empty_reply(self.blockchain.rpc.get_use_appbase() and use_appbase)
        posts = []
        if self.blockchain.rpc.get_use_appbase() and use_appbase:
            tags = self.blockchain.rpc.get_trending_tags(discussion_query, api="tags")['tags']
        if len(posts) == 0:
            tags = self.blockchain.rpc.get_trending_tags(discussion_query["start_tag"], discussion_query["limit"], api="tags")
        super(Trending_tags, self).__init__(
            [
                x
                for x in tags
            ]
        )
