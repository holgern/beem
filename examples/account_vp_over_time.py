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
        # print("ERROR: command line parameter mismatch!")
        # print("usage: %s [account]" % (sys.argv[0]))
        account = "holger80"
    else:
        account = sys.argv[1]
    acc_snapshot = AccountSnapshot(account)
    acc_snapshot.get_account_history()
    acc_snapshot.build(enable_out_votes=True)
    acc_snapshot.build_vp_arrays()
    timestamps = acc_snapshot.vp_timestamp
    vp = acc_snapshot.vp
    plt.figure(figsize=(12, 6))
    opts = {'linestyle': '-', 'marker': '.'}
    plt.plot_date(timestamps, vp, label="Voting power", **opts)
    plt.grid()
    plt.legend()
    plt.title("Voting power over time - @%s" % (account))
    plt.xlabel("Date")
    plt.ylabel("Voting power over time")
    # plt.show()
    plt.savefig("voting-power-%s.png" % (account))
    print("last voting power %d" % (vp[-1]))
