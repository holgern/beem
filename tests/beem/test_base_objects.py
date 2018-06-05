from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
from beem import Steem, exceptions
from beem.instance import set_shared_steem_instance
from beem.account import Account
from beem.witness import Witness
from beem.nodelist import NodeList


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodelist = NodeList()
        nodelist.update_nodes(steem_instance=Steem(node=nodelist.get_nodes(normal=True, appbase=True), num_retries=10))
        cls.bts = Steem(
            node=nodelist.get_nodes(appbase=False),
            nobroadcast=True,
            num_retries=10
        )
        set_shared_steem_instance(cls.bts)

    def test_Account(self):
        with self.assertRaises(
            exceptions.AccountDoesNotExistsException
        ):
            Account("FOObarNonExisting")

        c = Account("test")
        self.assertEqual(c["name"], "test")
        self.assertIsInstance(c, Account)

    def test_Witness(self):
        with self.assertRaises(
            exceptions.WitnessDoesNotExistsException
        ):
            Witness("FOObarNonExisting")

        c = Witness("jesta")
        self.assertEqual(c["owner"], "jesta")
        self.assertIsInstance(c.account, Account)
