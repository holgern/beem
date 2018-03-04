from __future__ import print_function
import sys
sys.path.append('../')
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
    def new_block(self,block):
        print(block["timestamp"])
        timestamp = parse_time(block["timestamp"])
        chunk = 10
        self.blocks = self.blocks + 1
        if self.blocks % chunk == 0:
            self.notify.close()
            now = time.time()
            duration = now - self.last
            total_duration = now - self.start
            speed = int(chunk*1000.0/duration)*1.0/1000
            avspeed = int(self.blocks*1000/total_duration)*1.0/1000
            self.last = now
    def hour(self):
        self.hourcount = self.hourcount + 1
        now = time.time()
        total_duration = str(timedelta(seconds=now-self.start))
        print("* HOUR mark: Processed "+str(self.hourcount)+ " blockchain hours in "+ total_duration)
        if self.hourcount == 1*24:
            print("Ending eventloop")
            self.notify.close()

if __name__ == "__main__":
    tb = TestBot()
    notify = Notify(on_block=tb.new_block)
    tb.notify = notify
    notify.listen()