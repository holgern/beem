# -*- coding: utf-8 -*-
import unittest
from beem import Steem
from beem.conveyor import Conveyor
from beem.instance import set_shared_steem_instance
from .nodes import get_hive_nodes, get_steem_nodes

wif = '5Jh1Gtu2j4Yi16TfhoDmg8Qj3ULcgRi7A49JXdfUUTVPkaFaRKz'


class Testcases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        stm = Steem(node=get_steem_nodes(), nobroadcast=True,
                    num_retries=10, expiration=120)
        set_shared_steem_instance(stm)

    def test_healthcheck(self):
        health = Conveyor().healthcheck()
        self.assertTrue('version' in health)
        self.assertTrue('ok' in health)
        self.assertTrue('date' in health)

if __name__ == "__main__":
    unittest.main()
