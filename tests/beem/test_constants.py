from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from builtins import super
import unittest
import mock
import pytz
from datetime import datetime, timedelta
from parameterized import parameterized
from pprint import pprint
from beem import Steem, exceptions, constants
from beem.nodelist import NodeList

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"


class Testcases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        nodelist = NodeList()
        nodelist.update_nodes(steem_instance=Steem(node=nodelist.get_nodes(normal=True, appbase=True), num_retries=10))
        cls.appbase = Steem(
            node=nodelist.get_nodes(appbase=True, dev=True),
            nobroadcast=True,
            bundle=False,
            # Overwrite wallet to use this list of wifs only
            keys={"active": wif},
            num_retries=10
        )

    def test_constants(self):
        stm = self.appbase
        steem_conf = stm.get_config()
        if "STEEM_100_PERCENT" in steem_conf:
            STEEM_100_PERCENT = steem_conf['STEEM_100_PERCENT']
        else:
            STEEM_100_PERCENT = steem_conf['STEEMIT_100_PERCENT']
        self.assertEqual(constants.STEEM_100_PERCENT, STEEM_100_PERCENT)

        if "STEEM_1_PERCENT" in steem_conf:
            STEEM_1_PERCENT = steem_conf['STEEM_1_PERCENT']
        else:
            STEEM_1_PERCENT = steem_conf['STEEMIT_1_PERCENT']
        self.assertEqual(constants.STEEM_1_PERCENT, STEEM_1_PERCENT)

        if "STEEM_REVERSE_AUCTION_WINDOW_SECONDS" in steem_conf:
            STEEM_REVERSE_AUCTION_WINDOW_SECONDS = steem_conf['STEEM_REVERSE_AUCTION_WINDOW_SECONDS']
        elif "STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF6" in steem_conf:
            STEEM_REVERSE_AUCTION_WINDOW_SECONDS = steem_conf['STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF6']
        else:
            STEEM_REVERSE_AUCTION_WINDOW_SECONDS = steem_conf['STEEMIT_REVERSE_AUCTION_WINDOW_SECONDS']
        self.assertEqual(constants.STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF6, STEEM_REVERSE_AUCTION_WINDOW_SECONDS)

        if "STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF20" in steem_conf:
            self.assertEqual(constants.STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF20, steem_conf["STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF20"])

        if "STEEM_VOTE_DUST_THRESHOLD" in steem_conf:
            self.assertEqual(constants.STEEM_VOTE_DUST_THRESHOLD, steem_conf["STEEM_VOTE_DUST_THRESHOLD"])

        if "STEEM_VOTE_REGENERATION_SECONDS" in steem_conf:
            STEEM_VOTE_REGENERATION_SECONDS = steem_conf['STEEM_VOTE_REGENERATION_SECONDS']
            self.assertEqual(constants.STEEM_VOTE_REGENERATION_SECONDS, STEEM_VOTE_REGENERATION_SECONDS)
        elif "STEEM_VOTING_MANA_REGENERATION_SECONDS" in steem_conf:
            STEEM_VOTING_MANA_REGENERATION_SECONDS = steem_conf["STEEM_VOTING_MANA_REGENERATION_SECONDS"]
            self.assertEqual(constants.STEEM_VOTING_MANA_REGENERATION_SECONDS, STEEM_VOTING_MANA_REGENERATION_SECONDS)
        else:
            STEEM_VOTE_REGENERATION_SECONDS = steem_conf['STEEMIT_VOTE_REGENERATION_SECONDS']
            self.assertEqual(constants.STEEM_VOTE_REGENERATION_SECONDS, STEEM_VOTE_REGENERATION_SECONDS)

        if "STEEM_ROOT_POST_PARENT" in steem_conf:
            STEEM_ROOT_POST_PARENT = steem_conf['STEEM_ROOT_POST_PARENT']
        else:
            STEEM_ROOT_POST_PARENT = steem_conf['STEEMIT_ROOT_POST_PARENT']
        self.assertEqual(constants.STEEM_ROOT_POST_PARENT, STEEM_ROOT_POST_PARENT)
