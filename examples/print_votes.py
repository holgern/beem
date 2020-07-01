from __future__ import print_function
import sys
from datetime import timedelta
import time
import io
from beem.blockchain import Blockchain
from beem.instance import shared_blockchain_instance
from beem.utils import parse_time
import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DemoBot(object):
    def vote(self, vote_event):
        w = vote_event["weight"]
        if w > 0:
            print("Vote by", vote_event["voter"], "for", vote_event["author"])
        else:
            if w < 0:
                print("Downvote by", vote_event["voter"], "for", vote_event["author"])
            else:
                print("(Down)vote by", vote_event["voter"], "for", vote_event["author"], "CANCELED")


if __name__ == "__main__":
    tb = DemoBot()
    blockchain = Blockchain()
    print("Starting on %s network" % shared_blockchain_instance().get_blockchain_name())
    for vote in blockchain.stream(opNames=["vote"]):
        tb.vote(vote)
