from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
known_chains = {
    "STEEM": {
        "chain_id": "0" * int(256 / 4),
        "prefix": "STM",
        "steem_symbol": "STEEM",
        "sbd_symbol": "SBD",
        "vests_symbol": "VESTS",
    },
    "TESTNET": {
        "chain_id": "79276aea5d4877d9a25892eaa01b0adf019d3e5cb12a97478df3298ccdd01673",
        "prefix": "STM",
        "steem_symbol": "STEEM",
        "sbd_symbol": "SBD",
        "vests_symbol": "VESTS",
    },
    "TEST": {
        "chain_id":
        "9afbce9f2416520733bacb370315d32b6b2c43d6097576df1c1222859d91eecc",
        "prefix":
        "TST",
        "steem_symbol":
        "TESTS",
        "sbd_symbol":
        "TBD",
        "vests_symbol":
        "VESTS",
    },
}
