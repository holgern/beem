from .instance import shared_steem_instance
from .account import Account
from .utils import resolve_authorperm, construct_authorperm
from .blockchainobject import BlockchainObject
from .exceptions import ContentDoesNotExistsException
import json
import logging
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
        if isinstance(authorperm, str):
            [author, permlink] = resolve_authorperm(authorperm)
            self["author"] = author
            self["permlink"] = permlink
            self["authorperm"] = construct_authorperm(author, permlink)
        elif isinstance(authorperm, dict) and "author" in authorperm and "permlink" in authorperm:
            self["author"] = authorperm["author"]
            self["permlink"] = authorperm["permlink"]
            self["authorperm"] = construct_authorperm(authorperm)
        super().__init__(
            authorperm,
            id_item="authorperm",
            lazy=lazy,
            full=full,
            steem_instance=steem_instance
        )

    def refresh(self):
        [author, permlink] = resolve_authorperm(self.identifier)
        content = self.steem.rpc.get_content(author, permlink)
        if not content:
            raise ContentDoesNotExistsException
        super(Comment, self).__init__(content, id_item="authorperm", steem_instance=self.steem)

        self.identifier = self.authorperm

    def json(self):
        output = self
        output.pop("authorperm")
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
