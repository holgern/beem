import unittest
from steem import Steem, exceptions
from steem.instance import set_shared_steem_instance
from steem.account import Account
from steem.witness import Witness

class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bts = Steem(
            nobroadcast=True,
        )
        set_shared_steem_instance(self.bts)

    def test_Account(self):
        with self.assertRaises(
            exceptions.AccountDoesNotExistsException
        ):
            Account("FOObarNonExisting")

        c = Account("test")
        self.assertEqual(c["name"], "test")
        self.assertIsInstance(c.account, Account)

    def test_Witness(self):
        with self.assertRaises(
            exceptions.AccountDoesNotExistsException
        ):
            Witness("FOObarNonExisting")

        c = Witness("test")
        self.assertEqual(c["name"], "test")
        self.assertIsInstance(c.account, Account)

        with self.assertRaises(
            exceptions.WitnessDoesNotExistsException
        ):
            Witness("nathan")

