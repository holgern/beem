from __future__ import print_function
import sys
from datetime import timedelta
import time
import io
from beem import Steem
from beem.account import Account
from beem.amount import Amount
from beem.utils import parse_time
from steem.account import Account as steemAccount
from steem.post import Post as steemPost
from steem import Steem as steemSteem
import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    stm = Steem("https://api.steemit.com")
    beem_acc = Account("holger80", steem_instance=stm)
    stm2 = steemSteem(nodes=["https://api.steemit.com"])
    steem_acc = steemAccount("holger80", steemd_instance=stm2)

    # profile
    print("beem_acc.profile  {}".format(beem_acc.profile))
    print("steem_acc.profile {}".format(steem_acc.profile))
    # sp
    print("beem_acc.sp  {}".format(beem_acc.sp))
    print("steem_acc.sp {}".format(steem_acc.sp))
    # rep
    print("beem_acc.rep  {}".format(beem_acc.rep))
    print("steem_acc.rep {}".format(steem_acc.rep))
    # balances
    print("beem_acc.balances  {}".format(beem_acc.balances))
    print("steem_acc.balances {}".format(steem_acc.balances))
    # get_balances()
    print("beem_acc.get_balances()  {}".format(beem_acc.get_balances()))
    print("steem_acc.get_balances() {}".format(steem_acc.get_balances()))
    # reputation()
    print("beem_acc.get_reputation()  {}".format(beem_acc.get_reputation()))
    print("steem_acc.reputation() {}".format(steem_acc.reputation()))
    # voting_power()
    print("beem_acc.get_voting_power()  {}".format(beem_acc.get_voting_power()))
    print("steem_acc.voting_power() {}".format(steem_acc.voting_power()))
    # get_followers()
    print("beem_acc.get_followers()  {}".format(beem_acc.get_followers()))
    print("steem_acc.get_followers() {}".format(steem_acc.get_followers()))
    # get_following()
    print("beem_acc.get_following()  {}".format(beem_acc.get_following()))
    print("steem_acc.get_following() {}".format(steem_acc.get_following()))
    # has_voted()
    print("beem_acc.has_voted()  {}".format(beem_acc.has_voted("@holger80/api-methods-list-for-appbase")))
    print("steem_acc.has_voted() {}".format(steem_acc.has_voted(steemPost("@holger80/api-methods-list-for-appbase"))))
    # curation_stats()
    print("beem_acc.curation_stats()  {}".format(beem_acc.curation_stats()))
    print("steem_acc.curation_stats() {}".format(steem_acc.curation_stats()))
    # virtual_op_count
    print("beem_acc.virtual_op_count()  {}".format(beem_acc.virtual_op_count()))
    print("steem_acc.virtual_op_count() {}".format(steem_acc.virtual_op_count()))
    # get_account_votes
    print("beem_acc.get_account_votes()  {}".format(beem_acc.get_account_votes()))
    print("steem_acc.get_account_votes() {}".format(steem_acc.get_account_votes()))
    # get_withdraw_routes
    print("beem_acc.get_withdraw_routes()  {}".format(beem_acc.get_withdraw_routes()))
    print("steem_acc.get_withdraw_routes() {}".format(steem_acc.get_withdraw_routes()))
    # get_conversion_requests
    print("beem_acc.get_conversion_requests()  {}".format(beem_acc.get_conversion_requests()))
    print("steem_acc.get_conversion_requests() {}".format(steem_acc.get_conversion_requests()))
    # export
    # history
    beem_hist = []
    for h in beem_acc.history(only_ops=["transfer"]):
        beem_hist.append(h)
        if len(beem_hist) >= 10:
            break
    steem_hist = []
    for h in steem_acc.history(filter_by="transfer", start=0):
        steem_hist.append(h)
        if len(steem_hist) >= 10:
            break
    print("beem_acc.history()  {}".format(beem_hist))
    print("steem_acc.history() {}".format(steem_hist))
    # history_reverse
    beem_hist = []
    for h in beem_acc.history_reverse(only_ops=["transfer"]):
        beem_hist.append(h)
        if len(beem_hist) >= 10:
            break
    steem_hist = []
    for h in steem_acc.history_reverse(filter_by="transfer"):
        steem_hist.append(h)
        if len(steem_hist) >= 10:
            break
    print("beem_acc.history_reverse()  {}".format(beem_hist))
    print("steem_acc.history_reverse() {}".format(steem_hist))
