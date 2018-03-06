from __future__ import print_function
import sys
from datetime import timedelta
import time
import io
from beem.blockchain import Blockchain
from beem.utils import parse_time
import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DemoBot(object):
    def comment(self, comment_event):
        print('Comment by {} on post {} by {}:'.format(comment_event['author'],
                                                       comment_event['parent_permlink'],
                                                       comment_event['parent_author']))
        print(comment_event['body'])
        print()


if __name__ == "__main__":
    tb = DemoBot()
    blockchain = Blockchain()
    for vote in blockchain.stream(opNames=["comment"]):
        tb.comment(vote)
