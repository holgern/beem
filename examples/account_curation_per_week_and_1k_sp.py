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
    acc_snapshot.build(enable_rewards=True)
    acc_snapshot.build_curation_arrays()
    timestamps = acc_snapshot.curation_per_1000_SP_timestamp
    curation_per_1000_SP = acc_snapshot.curation_per_1000_SP

    plt.figure(figsize=(12, 6))
    opts = {'linestyle': '-', 'marker': '.'}
    plt.plot_date(timestamps, curation_per_1000_SP, label="Curation reward per week and 1k SP", **opts)
    plt.grid()
    plt.legend()
    plt.title("Curation over time - @%s" % (account))
    plt.xlabel("Date")
    plt.ylabel("Curation rewards (SP / (week * 1k SP))")
    plt.show()
    # plt.savefig("curation_per_week-%s.png" % (account))
    print("last curation reward per week and 1k sp %.2f SP" % (curation_per_1000_SP[-1]))
