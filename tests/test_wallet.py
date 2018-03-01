from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
import unittest
import mock
from pprint import pprint
from beem import Steem, exceptions
from beem.account import Account
from beem.amount import Amount
from beem.asset import Asset
from beem.wallet import Wallet
from beem.instance import set_shared_steem_instance
from beembase.operationids import getOperationNameForId

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://node.steem.ws", "wss://steemd.steemgigs.org", "wss://steemd.steemit.com",
         "wss://steemd.minnowsupportproject.org"]


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.stm = Steem(
            node=nodes,
            nobroadcast=True,
            # We want to bundle many operations into a single transaction
            bundle=True,
            # Overwrite wallet to use this list of wifs only
        )
        self.stm.set_default_account("test")
        set_shared_steem_instance(self.stm)
        # self.stm.newWallet("TestingOneTwoThree")
        self.wallet = Wallet(rpc=self.stm.rpc)
        self.wallet.purgeWallet()
        self.wallet.newWallet(pwd="TestingOneTwoThree")
        self.wallet.unlock(pwd="TestingOneTwoThree")
        self.wallet.addPrivateKey(wif)

    def test_wallet_lock(self):
        self.wallet.unlock(pwd="TestingOneTwoThree")
        self.assertTrue(self.wallet.unlocked())
        self.assertFalse(self.wallet.locked())
        self.wallet.lock()
        self.assertTrue(self.wallet.locked())

    def test_change_masterpassword(self):
        self.wallet.unlock(pwd="TestingOneTwoThree")
        self.assertTrue(self.wallet.unlocked())
        self.wallet.changePassphrase("newPass")
        self.wallet.lock()
        self.assertTrue(self.wallet.locked())
        self.wallet.unlock(pwd="newPass")
        self.assertTrue(self.wallet.unlocked())
        self.wallet.changePassphrase("TestingOneTwoThree")
        self.wallet.lock()

    def test_Keys(self):
        self.wallet.unlock(pwd="TestingOneTwoThree")
        keys = self.wallet.getPublicKeys()
        self.assertTrue(len(keys) > 0)
        pub = self.wallet.getPublicKeys()[0]
        private = self.wallet.getPrivateKeyForPublicKey(pub)
        self.assertEqual(private, wif)

    def test_account_by_pub(self):
        self.wallet.unlock(pwd="TestingOneTwoThree")
        acc = Account("steemit")
        pub = acc["owner"]["key_auths"][0][0]
        acc_by_pub = self.wallet.getAccount(pub)
        self.assertEqual("steemit", acc_by_pub["name"])

    def test_pub_lookup(self):
        self.wallet.unlock(pwd="TestingOneTwoThree")
        with self.assertRaises(
            exceptions.KeyNotFound
        ):
            self.wallet.getOwnerKeyForAccount("test")
        with self.assertRaises(
            exceptions.KeyNotFound
        ):
            self.wallet.getMemoKeyForAccount("test")
        with self.assertRaises(
            exceptions.KeyNotFound
        ):
            self.wallet.getActiveKeyForAccount("test")
        with self.assertRaises(
            exceptions.KeyNotFound
        ):
            self.wallet.getPostingKeyForAccount("test")

    def test_encrypt(self):
        self.wallet.unlock(pwd="TestingOneTwoThree")
        self.wallet.masterpassword = "TestingOneTwoThree"
        self.assertEqual([self.wallet.encrypt_wif("5HqUkGuo62BfcJU5vNhTXKJRXuUi9QSE6jp8C3uBJ2BVHtB8WSd"),
                          self.wallet.encrypt_wif("5KN7MzqK5wt2TP1fQCYyHBtDrXdJuXbUzm4A9rKAteGu3Qi5CVR")],
                         ["6PRN5mjUTtud6fUXbJXezfn6oABoSr6GSLjMbrGXRZxSUcxThxsUW8epQi",
                          "6PRVWUbkzzsbcVac2qwfssoUJAN1Xhrg6bNk8J7Nzm5H7kxEbn2Nh2ZoGg"])
        self.wallet.masterpassword = "Satoshi"
        self.assertEqual([self.wallet.encrypt_wif("5HtasZ6ofTHP6HCwTqTkLDuLQisYPah7aUnSKfC7h4hMUVw2gi5")],
                         ["6PRNFFkZc2NZ6dJqFfhRoFNMR9Lnyj7dYGrzdgXXVMXcxoKTePPX1dWByq"])
        self.wallet.masterpassword = "TestingOneTwoThree"

    def test_deencrypt(self):
        self.wallet.unlock(pwd="TestingOneTwoThree")
        self.wallet.masterpassword = "TestingOneTwoThree"
        self.assertEqual([self.wallet.decrypt_wif("6PRN5mjUTtud6fUXbJXezfn6oABoSr6GSLjMbrGXRZxSUcxThxsUW8epQi"),
                          self.wallet.decrypt_wif("6PRVWUbkzzsbcVac2qwfssoUJAN1Xhrg6bNk8J7Nzm5H7kxEbn2Nh2ZoGg")],
                         ["5HqUkGuo62BfcJU5vNhTXKJRXuUi9QSE6jp8C3uBJ2BVHtB8WSd",
                          "5KN7MzqK5wt2TP1fQCYyHBtDrXdJuXbUzm4A9rKAteGu3Qi5CVR"])
        self.wallet.masterpassword = "Satoshi"
        self.assertEqual([self.wallet.decrypt_wif("6PRNFFkZc2NZ6dJqFfhRoFNMR9Lnyj7dYGrzdgXXVMXcxoKTePPX1dWByq")],
                         ["5HtasZ6ofTHP6HCwTqTkLDuLQisYPah7aUnSKfC7h4hMUVw2gi5"])
        self.wallet.masterpassword = "TestingOneTwoThree"
