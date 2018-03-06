from __future__ import print_function
import sys
from datetime import timedelta
import time
import io
from beem.notify import Notify
from beem.utils import parse_time
import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TestBot:
    def __init__(self):
        self.notify = None
        self.blocks = 0
        self.hourcount = 0
        self.start = time.time()
        self.last = time.time()
        self.total_transaction = 0

    def new_block(self, block):
        if "block" in block:
            trxs = block["block"]["transactions"]
        else:
            trxs = block["transactions"]
        for tx in trxs:
            for op in tx["operations"]:
                self.total_transaction += 1
                if op[0] == 'vote':
                    self.vote(op[1])
        chunk = 100
        self.blocks = self.blocks + 1
        if self.blocks % chunk == 0:
            now = time.time()
            duration = now - self.last
            total_duration = now - self.start
            speed = int(chunk * 1000.0 / duration) * 1.0 / 1000
            avspeed = int(self.blocks * 1000 / total_duration) * 1.0 / 1000
            avtran = self.total_transaction / self.blocks
            self.last = now
            print("* 100 blocks processed in %.2f seconds. Speed %.2f. Avg: %.2f. Avg.Trans:"
                  "%.2f Count: %d Block minutes: %d" % (duration, speed, avspeed, avtran, self.blocks, self.blocks * 3 / 60))
        if self.blocks % 1200 == 0:
            self.hour()

    def vote(self, vote_event):
        w = vote_event["weight"]
        if w > 0:
            print("Vote by", vote_event["voter"], "for", vote_event["author"])
        else:
            if w < 0:
                print("Downvote by", vote_event["voter"], "for", vote_event["author"])
            else:
                print("(Down)vote by", vote_event["voter"], "for", vote_event["author"], "CANCELED")

    def hour(self):
        self.hourcount = self.hourcount + 1
        now = time.time()
        total_duration = str(timedelta(seconds=now - self.start))
        print("* HOUR mark: Processed " + str(self.hourcount) + " blockchain hours in " + total_duration)
        if self.hourcount == 1 * 24:
            print("Ending eventloop")
            self.notify.close()


if __name__ == "__main__":
    tb = TestBot()
    notify = Notify(on_block=tb.new_block)
    tb.notify = notify
    notify.listen()
