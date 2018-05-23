from __future__ import print_function
from memory_profiler import profile
import sys
from beem.steem import Steem
from beem.account import Account
from beem.blockchain import Blockchain
from beem.instance import set_shared_steem_instance, clear_cache
from beem.storage import configStorage as config
from beemapi.graphenerpc import GrapheneRPC
import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@profile
def profiling(node, name_list, shared_instance=True, clear_acc_cache=False, clear_all_cache=True):
    print("shared_instance %d clear_acc_cache %d clear_all_cache %d" %
          (shared_instance, clear_acc_cache, clear_all_cache))
    if not shared_instance:
        stm = Steem(node=node)
        print(str(stm))
    else:
        stm = None
    acc_dict = {}
    for name in name_list:
        acc = Account(name, steem_instance=stm)
        acc_dict[name] = acc
        if clear_acc_cache:
            acc.clear_cache()
        acc_dict = {}
    if clear_all_cache:
        clear_cache()
    if not shared_instance:
        del stm.rpc


if __name__ == "__main__":
    stm = Steem()
    print("Shared instance: " + str(stm))
    set_shared_steem_instance(stm)
    b = Blockchain()
    account_list = []
    for a in b.get_all_accounts(limit=500):
        account_list.append(a)
    shared_instance = False
    clear_acc_cache = False
    clear_all_cache = False
    node = "https://api.steemit.com"
    n = 3
    for i in range(1, n + 1):
        print("%d of %d" % (i, n))
        profiling(node, account_list, shared_instance=shared_instance, clear_acc_cache=clear_acc_cache, clear_all_cache=clear_all_cache)
