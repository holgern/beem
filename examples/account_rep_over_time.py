#!/usr/bin/python
import sys
import datetime as dt
from beem.amount import Amount
from beem.utils import parse_time, formatTimeString, addTzInfo
from beem.instance import set_shared_steem_instance
from beem import Steem
from beem.snapshot import AccountSnapshot
import matplotlib as mpl
# mpl.use('Agg')
# mpl.use('TkAgg')
import matplotlib.pyplot as plt


if __name__ == "__main__":
    if len(sys.argv) != 2:
        # print("ERROR: command line paramter mismatch!")
        # print("usage: %s [account]" % (sys.argv[0]))
        account = "holger80"
    else:
        account = sys.argv[1]
    acc_snapshot = AccountSnapshot(account)
    acc_snapshot.get_account_history()
    acc_snapshot.build(enable_in_votes=True)
    acc_snapshot.build_rep_arrays()
    timestamps = acc_snapshot.rep_timestamp
    rep = acc_snapshot.rep
    plt.figure(figsize=(12, 6))
    opts = {'linestyle': '-', 'marker': '.'}
    plt.plot_date(timestamps, rep, label="Reputation", **opts)
    plt.grid()
    plt.legend()
    plt.title("Reputation over time - @%s" % (account))
    plt.xlabel("Date")
    plt.ylabel("Reputation over time")
    # plt.show()
    plt.savefig("reputation-%s.png" % (account))
    print("last reputation %f" % (rep[-1]))
