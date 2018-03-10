from __future__ import print_function
import sys
from datetime import datetime, timedelta
import time
import io
from beem.blockchain import Blockchain
from beem.comment import Comment
from beem.account import Account
from beem.utils import parse_time, construct_authorperm
import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class WatchingTheWatchers:
    def __init__(self):
        self.dvcount = 0
        self.account_type = dict()
        self.account_relations = dict()
        self.by_voter = dict()
        self.by_target = dict()
        self.by_pair = dict()

    def update(self, downvoter, downvoted, dvpower, flagpower):
        pair = downvoter + "/" + downvoted
        if downvoter not in self.by_voter:
            self.by_voter[downvoter] = [0.0, 0.0]
        if downvoted not in self.by_target:
            self.by_target[downvoted] = [0.0, 0.0]
        if pair not in self.by_pair:
            self.by_pair[pair] = [0.0, 0.0]
        self.by_voter[downvoter][0] = self.by_voter[downvoter][0] + dvpower
        self.by_voter[downvoter][1] = self.by_voter[downvoter][1] + flagpower
        self.by_target[downvoted][0] = self.by_target[downvoted][0] + dvpower
        self.by_target[downvoted][1] = self.by_target[downvoted][1] + flagpower
        self.by_pair[pair][0] = self.by_pair[pair][0] + dvpower
        self.by_pair[pair][1] = self.by_pair[pair][1] + flagpower
        self.dvcount = self.dvcount + 1
        if self.dvcount % 100 == 0:
            print(self.dvcount, "downvotes so far.")

    def set_account_info(self, account, fish, related):
        self.account_type[account] = fish
        if len(related) > 0:
            self.account_relations[account] = related

    def report(self):
        print("[REPORT]")
        print(" * account_type :", self.account_type)
        print()
        print(" * account_relations :", self.account_relations)
        print()
        print(" * by voter :", self.by_voter)
        print()
        print(" * by target :", self.by_target)
        print()
        print(" * by pair :", self.by_pair)
        print()
        self.dvcount = 0
        self.account_type = dict()
        self.account_relations = dict()
        self.by_voter = dict()
        self.by_target = dict()
        self.by_pair = dict()


class WatchingTheWatchersBot:
    def __init__(self, wtw):
        self.stopped = None
        self.wtw = wtw
        self.looked_up = set()

    def vote(self, vote_event):
        def process_vote_content(event):
            start_rshares = 0.0
            for vote in event["active_votes"]:
                if vote["voter"] == vote_event["voter"] and float(vote["rshares"]) < 0:
                    if start_rshares + float(vote["rshares"]) < 0:
                        flag_power = 0 - start_rshares - float(vote["rshares"])
                    else:
                        flag_power = 0
                    downvote_power = 0 - vote["rshares"] - flag_power
                    self.wtw.update(vote["voter"], vote_event["author"], downvote_power, flag_power)

        def lookup_accounts(acclist):
            def user_info(accounts):
                if len(acclist) != len(accounts):
                    print("OOPS:", len(acclist), len(accounts), acclist)
                for index in range(0, len(accounts)):
                    a = accounts[index]
                    account = acclist[index]
                    vp = (a["vesting_shares"].amount +
                          a["received_vesting_shares"].amount -
                          a["delegated_vesting_shares"].amount) / 1000000.0
                    fish = "redfish"
                    if vp >= 1.0:
                        fish = "minnow"
                    if vp >= 10.0:
                        fish = "dolphin"
                    if vp >= 100:
                        fish = "orca"
                    if vp > 1000:
                        fish = "whale"
                    racc = None
                    proxy = None
                    related = list()
                    if a["recovery_account"] != "steem" and a["recovery_account"] != "":
                        related.append(a["recovery_account"])
                    if a["proxy"] != "":
                        related.append(a["proxy"])
                    self.wtw.set_account_info(account, fish, related)
                    accl2 = list()
                    if racc is not None and racc not in self.looked_up:
                        accl2.append(racc)
                    if proxy is not None and proxy not in self.looked_up:
                        accl2.append(proxy)
                    if len(accl2) > 0:
                        lookup_accounts(accl2)
            accounts = []
            for a in acclist:
                accounts.append(Account(a))
            user_info(accounts)
        if vote_event["weight"] < 0:
            authorperm = construct_authorperm(vote_event["author"], vote_event["permlink"])
            # print(authorperm)
            process_vote_content(Comment(authorperm))
            al = list()
            if not vote_event["voter"] in self.looked_up:
                al.append(vote_event["voter"])
                self.looked_up.add(vote_event["voter"])
            if not vote_event["author"] in self.looked_up:
                al.append(vote_event["author"])
                self.looked_up.add(vote_event["author"])
            if len(al) > 0:
                lookup_accounts(al)


if __name__ == "__main__":
    wtw = WatchingTheWatchers()
    tb = WatchingTheWatchersBot(wtw)
    blockchain = Blockchain()
    threading = True
    thread_num = 16    
    cur_block = blockchain.get_current_block()
    stop = cur_block.identifier
    startdate = cur_block.time() - timedelta(days=1)
    start = blockchain.get_estimated_block_num(startdate, accurate=True)
    for vote in blockchain.stream(opNames=["vote"], start=start, stop=stop, threading=threading, thread_num=thread_num):
        tb.vote(vote)
    wtw.report()
