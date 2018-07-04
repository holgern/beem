from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
default_prefix = "STM"
known_chains = {
    "STEEMAPPBASE": {
        "chain_id": "0" * int(256 / 4),
        "min_version": '0.19.10',
        "prefix": "STM",
        "chain_assets": [
            {"asset": "@@000000013", "symbol": "SBD", "precision": 3, "id": 0},
            {"asset": "@@000000021", "symbol": "STEEM", "precision": 3, "id": 1},
            {"asset": "@@000000037", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },
    "STEEM": {
        "chain_id": "0" * int(256 / 4),
        "min_version": '0.19.5',
        "prefix": "STM",
        "chain_assets": [
            {"asset": "SBD", "symbol": "SBD", "precision": 3, "id": 0},
            {"asset": "STEEM", "symbol": "STEEM", "precision": 3, "id": 1},
            {"asset": "VESTS", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },
    "TESTNET": {
        "chain_id": "79276aea5d4877d9a25892eaa01b0adf019d3e5cb12a97478df3298ccdd01673",
        "min_version": '0.0.0',
        "prefix": "STX",
        "chain_assets": [
            {"asset": "SBD", "symbol": "SBD", "precision": 3, "id": 0},
            {"asset": "STEEM", "symbol": "STEEM", "precision": 3, "id": 1},
            {"asset": "VESTS", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },
    "TEST": {
        "chain_id":
        "9afbce9f2416520733bacb370315d32b6b2c43d6097576df1c1222859d91eecc",
        "min_version": '0.0.0',
        "prefix": "TST",
        "chain_assets": [
            {"asset": "SBD", "symbol": "TBD", "precision": 3, "id": 0},
            {"asset": "STEEM", "symbol": "TESTS", "precision": 3, "id": 1},
            {"asset": "VESTS", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },
    "GOLOS": {
        "chain_id": "782a3039b478c839e4cb0c941ff4eaeb7df40bdd68bd441afd444b9da763de12",
        "min_version": '0.0.0',
        "prefix": "GLS",
        "chain_assets": [
            {"asset": "SBD", "symbol": "GBG", "precision": 3, "id": 0},
            {"asset": "STEEM", "symbol": "GOLOS", "precision": 3, "id": 1},
            {"asset": "VESTS", "symbol": "GESTS", "precision": 6, "id": 2}
        ],
    },
    "VIT": {
        "chain_id": "73f14dd4b7b07a8663be9d84300de0f65ef2ee7e27aae32bbe911c548c08f000",
        "min_version": "0.0.0",
        "prefix": "VIT",
        "chain_assets": [
            {"asset": "SBD", "symbol": "VBD", "precision": 3, "id": 0},
            {"asset": "STEEM", "symbol": "VIT", "precision": 3, "id": 1},
            {"asset": "VESTS", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    }
}
