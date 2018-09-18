from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import sys
from datetime import datetime, timedelta
import time
import io
import logging

from beem.blockchain import Blockchain
from beem.block import Block
from beem.account import Account
from beem.amount import Amount
from beemgraphenebase.account import PasswordKey, PrivateKey, PublicKey
from beem.steem import Steem
from beem.utils import parse_time, formatTimedelta
from beemapi.exceptions import NumRetriesReached
from beem.nodelist import NodeList
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    # stm = Steem(node="https://testnet.timcliff.com/")
    # stm = Steem(node="https://testnet.steemitdev.com")
    stm = Steem(node="https://api.steemit.com")
    stm.wallet.unlock(pwd="pwd123")

    account = Account("beembot", steem_instance=stm)
    print(account.get_voting_power())

    account.transfer("holger80", 0.001, "SBD", "test")
