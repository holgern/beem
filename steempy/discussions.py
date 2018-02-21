from .instance import shared_steem_instance
from .account import Account
from .comment import Comment
from .utils import resolve_authorperm
import logging
log = logging.getLogger(__name__)


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
