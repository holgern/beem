from beem import Steem
import numpy as np
from beem.utils import reputation_to_score
from beem.amount import Amount
from beem.constants import STEEM_100_PERCENT
import matplotlib as mpl
# mpl.use('Agg')
# mpl.use('TkAgg')
import matplotlib.pyplot as plt


if __name__ == "__main__":
    stm = Steem()
    price = Amount(stm.get_current_median_history()["base"])
    reps = [0]
    for i in range(26, 91):
        reps.append(int(10**((i - 25) / 9 + 9)))
    # reps = np.logspace(9, 16, 60)
    used_power = stm._calc_resulting_vote()
    last_sp = 0
    sp_list = []
    rep_score_list = []
    for goal_rep in reps:
        score = reputation_to_score(goal_rep)
        rep_score_list.append(score)
        needed_rshares = int(goal_rep) << 6
        needed_vests = needed_rshares / used_power / 100
        needed_sp = stm.vests_to_sp(needed_vests)
        sp_list.append(needed_sp / 1000)
        # print("| %.1f | %.2f | %.2f  | " % (score, needed_sp / 1000, needed_sp / 1000 - last_sp / 1000))
        last_sp = needed_sp

    plt.figure(figsize=(12, 6))
    opts = {'linestyle': '-', 'marker': '.'}
    plt.semilogx(sp_list, rep_score_list, label="Reputation", **opts)
    plt.grid()
    plt.legend()
    plt.title("Required number of 1k SP upvotes to reach certain reputation")
    plt.xlabel("1k SP votes")
    plt.ylabel("Reputation")
    plt.show()
    # plt.savefig("rep_based_on_votes.png")
