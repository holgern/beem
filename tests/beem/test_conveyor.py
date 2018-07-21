from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import unittest
from beem import Steem
from beem.conveyor import Conveyor
from beem.instance import set_shared_steem_instance
from beem.nodelist import NodeList

wif = '5Jh1Gtu2j4Yi16TfhoDmg8Qj3ULcgRi7A49JXdfUUTVPkaFaRKz'


class Testcases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        nodelist = NodeList()
        stm = Steem(node=nodelist.get_testnet(), nobroadcast=True,
                    num_retries=10, expiration=120, keys=wif)
        set_shared_steem_instance(stm)

    def test_healthcheck(self):
        health = Conveyor().healthcheck()
        self.assertTrue('version' in health)
        self.assertTrue('ok' in health)
        self.assertTrue('date' in health)

    def test_get_user_data(self):
        c = Conveyor()
        userdata = c.get_user_data('beem')
        self.assertTrue('jsonrpc' in userdata)
        self.assertTrue('error' in userdata)
        self.assertTrue('code' in userdata['error'])
        # error 401 -> unauthorized, but proper format
        self.assertTrue(userdata['error']['code'] == 401)


if __name__ == "__main__":
    unittest.main()
