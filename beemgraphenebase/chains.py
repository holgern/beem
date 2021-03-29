# -*- coding: utf-8 -*-
default_prefix = "STM"
known_chains = {
    "HIVE": {
        "chain_id": "0" * int(256 / 4),
        "min_version": '0.23.0',
        "prefix": "STM",
        "chain_assets": [
            {"asset": "@@000000013", "symbol": "HBD", "precision": 3, "id": 0},
            {"asset": "@@000000021", "symbol": "HIVE", "precision": 3, "id": 1},
            {"asset": "@@000000037", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },
    "HIVE2": {
        "chain_id": "beeab0de00000000000000000000000000000000000000000000000000000000",
        "min_version": '0.24.0',
        "prefix": "STM",
        "chain_assets": [
            {"asset": "@@000000013", "symbol": "HBD", "precision": 3, "id": 0},
            {"asset": "@@000000021", "symbol": "HIVE", "precision": 3, "id": 1},
            {"asset": "@@000000037", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },
    "BLURT": {
        "chain_id": "cd8d90f29ae273abec3eaa7731e25934c63eb654d55080caff2ebb7f5df6381f",
        "min_version": '0.0.0',
        "prefix": "BLT",
        "chain_assets": [
            {"asset": "@@000000021", "symbol": "BLURT", "precision": 3, "id": 1},
            {"asset": "@@000000037", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },    
    "STEEM": {
        "chain_id": "0" * int(256 / 4),
        "min_version": '0.19.10',
        "prefix": "STM",
        "chain_assets": [
            {"asset": "@@000000013", "symbol": "SBD", "precision": 3, "id": 0},
            {"asset": "@@000000021", "symbol": "STEEM", "precision": 3, "id": 1},
            {"asset": "@@000000037", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },
    "TESTNET": {
        "chain_id": "79276aea5d4877d9a25892eaa01b0adf019d3e5cb12a97478df3298ccdd01673",
        "min_version": '0.20.0',
        "prefix": "STX",
        "chain_assets": [
            {"asset": "@@000000013", "symbol": "SBD", "precision": 3, "id": 0},
            {"asset": "@@000000021", "symbol": "STEEM", "precision": 3, "id": 1},
            {"asset": "@@000000037", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },
    "TESTDEV": {
        "chain_id":
        "18dcf0a285365fc58b71f18b3d3fec954aa0c141c44e4e5cb4cf777b9eab274e",
        "min_version": '0.20.0',
        "prefix": "TST",
        "chain_assets": [
            {"asset": "@@000000013", "symbol": "TBD", "precision": 3, "id": 0},
            {"asset": "@@000000021", "symbol": "TESTS", "precision": 3, "id": 1},
            {"asset": "@@000000037", "symbol": "VESTS", "precision": 6, "id": 2}
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
            {"asset": "STEEM", "symbol": "VIT", "precision": 3, "id": 1},
            {"asset": "VESTS", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },
    "VIZ": {
        "chain_id": "2040effda178d4fffff5eab7a915d4019879f5205cc5392e4bcced2b6edda0cd",
        "min_version": "2.5.0",
        "prefix": "VIZ",
        "chain_assets": [
            {"asset": "STEEM", "symbol": "VIZ", "precision": 3, "id": 1},
            {"asset": "VESTS", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },    
    "WEKU": {
        "chain_id": "b24e09256ee14bab6d58bfa3a4e47b0474a73ef4d6c47eeea007848195fa085e",
        "min_version": "0.19.3",
        "prefix": "WKA",
        "chain_assets": [
            {"asset": "SBD", "symbol": "WKD", "precision": 3, "id": 0},
            {"asset": "STEEM", "symbol": "WEKU", "precision": 3, "id": 1},
            {"asset": "VESTS", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },
    "SMOKE": {
        "chain_id": "1ce08345e61cd3bf91673a47fc507e7ed01550dab841fd9cdb0ab66ef576aaf0",
        "min_version": "0.1.0",
        "prefix": "SMK",
        "chain_assets": [
            {"asset": "STEEM", "symbol": "SMOKE", "precision": 3, "id": 1},
            {"asset": "VESTS", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },    
    "EFTGAPPBASE": {
        "chain_id": "1c15984beb16945c01cb9bc3d654b0417c650461dfe535018fe03a4fc5a36864",
        "min_version": "0.19.12",
        "prefix": "EUR",
        "chain_assets": [
            {"asset": "@@000000013", "symbol": "EUR", "precision": 3, "id": 0},
            {"asset": "@@000000021", "symbol": "EFTG", "precision": 3, "id": 1},
            {"asset": "@@000000037", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },
    "EFTG": {
        "chain_id": "1c15984beb16945c01cb9bc3d654b0417c650461dfe535018fe03a4fc5a36864",
        "min_version": "0.19.6",
        "prefix": "EUR",
        "chain_assets": [
            {"asset": "SBD", "symbol": "EUR", "precision": 3, "id": 0},
            {"asset": "STEEM", "symbol": "EFTG", "precision": 3, "id": 1},
            {"asset": "VESTS", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },
    "PULSAR": {
        "chain_id": "07c687c01f134adaf217a9b9367d1cef679c3c020167fdd25ee8c403f687528e",
        "min_version": "0.101.0",
        "prefix": "EUR",
        "chain_assets": [
            {"asset": "@@000000013", "symbol": "EUR", "precision": 3, "id": 0},
            {"asset": "@@000000021", "symbol": "PULSE", "precision": 3, "id": 1},
            {"asset": "@@000000037", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },
    "WLS": {
        "chain_id": "de999ada2ff7ed3d3d580381f229b40b5a0261aec48eb830e540080817b72866",
        "min_version": "0.0.0",
        "prefix": "WLS",
        "chain_assets": [
            {"asset": "STEEM", "symbol": "WLS", "precision": 3, "id": 1},
            {"asset": "VESTS", "symbol": "VESTS", "precision": 6, "id": 2}
        ],
    },
}
