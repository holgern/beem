from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import range
from builtins import super
import mock
import string
import unittest
import random
from pprint import pprint
from beem import Steem
from beem.amount import Amount
from beem.witness import Witness
from beem.account import Account
from beem.instance import set_shared_steem_instance, shared_steem_instance
from beem.blockchain import Blockchain
from beem.block import Block
from beem.transactionbuilder import TransactionBuilder
from beembase.operations import Transfer
from beemgraphenebase.account import PasswordKey, PrivateKey, PublicKey
from beem.utils import parse_time, formatTimedelta
from beemapi.rpcutils import NumRetriesReached
from beem.nodelist import NodeList

# Py3 compatibility
import sys

core_unit = "STX"


class Testcases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodelist = NodeList()
        stm = shared_steem_instance()
        stm.config.refreshBackup()
        cls.bts = Steem(
            node=nodelist.get_testnet(),
            nobroadcast=True,
            num_retries=10,
            expiration=120,
        )
        # from getpass import getpass
        # self.bts.wallet.unlock(getpass())
        cls.bts.set_default_account("beem")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        stm = self.bts
        stm.nobroadcast = True
        stm.wallet.wipe(True)
        stm.wallet.create("123")
        stm.wallet.unlock("123")
        # Test account "beem"
        self.active_key = "5Jt2wTfhUt5GkZHV1HYVfkEaJ6XnY8D2iA4qjtK9nnGXAhThM3w"
        self.posting_key = "5Jh1Gtu2j4Yi16TfhoDmg8Qj3ULcgRi7A49JXdfUUTVPkaFaRKz"
        self.memo_key = "5KPbCuocX26aMxN9CDPdUex4wCbfw9NoT5P7UhcqgDwxXa47bit"

        stm.wallet.addPrivateKey(self.active_key)
        stm.wallet.addPrivateKey(self.memo_key)
        stm.wallet.addPrivateKey(self.posting_key)

        # Test account "beem1"
        self.active_key1 = "5Jo9SinzpdAiCDLDJVwuN7K5JcusKmzFnHpEAtPoBHaC1B5RDUd"
        self.posting_key1 = "5JGNhDXuDLusTR3nbmpWAw4dcmE8WfSM8odzqcQ6mDhJHP8YkQo"
        self.memo_key1 = "5KA2ddfAffjfRFoe1UhQjJtKnGsBn9xcsdPQTfMt1fQuErDAkWr"

        stm.wallet.addPrivateKey(self.active_key1)
        stm.wallet.addPrivateKey(self.memo_key1)
        stm.wallet.addPrivateKey(self.posting_key1)

        self.active_private_key_of_steemfiles = '5HvwMUj7phRn6JeWi8HNHC9FuNEhaATt3PHWZoKPXouvb4wBmz1'
        self.active_private_key_of_elf = '5JeUg6eXYLKqESf2dyP8bshK3YZGKo4UCsvZAP4GW9yDrxzySSK'
        stm.wallet.addPrivateKey(self.active_private_key_of_steemfiles)
        stm.wallet.addPrivateKey(self.active_private_key_of_elf)

    @classmethod
    def tearDownClass(cls):
        stm = shared_steem_instance()
        stm.config.recover_with_latest_backup()

    def test_wallet_keys(self):
        stm = self.bts
        stm.wallet.unlock("123")
        priv_key = stm.wallet.getPrivateKeyForPublicKey(str(PrivateKey(self.posting_key, prefix=stm.prefix).pubkey))
        self.assertEqual(str(priv_key), self.posting_key)
        priv_key = stm.wallet.getKeyForAccount("beem", "active")
        self.assertEqual(str(priv_key), self.active_key)
        priv_key = stm.wallet.getKeyForAccount("beem1", "posting")
        self.assertEqual(str(priv_key), self.posting_key1)

        priv_key = stm.wallet.getPrivateKeyForPublicKey(str(PrivateKey(self.active_private_key_of_steemfiles, prefix=stm.prefix).pubkey))
        self.assertEqual(str(priv_key), self.active_private_key_of_steemfiles)
        priv_key = stm.wallet.getKeyForAccount("steemfiles", "active")
        self.assertEqual(str(priv_key), self.active_private_key_of_steemfiles)

        priv_key = stm.wallet.getPrivateKeyForPublicKey(str(PrivateKey(self.active_private_key_of_elf, prefix=stm.prefix).pubkey))
        self.assertEqual(str(priv_key), self.active_private_key_of_elf)
        priv_key = stm.wallet.getKeyForAccount("elf", "active")
        self.assertEqual(str(priv_key), self.active_private_key_of_elf)

    def test_transfer(self):
        bts = self.bts
        bts.nobroadcast = False
        bts.wallet.unlock("123")
        # bts.prefix ="STX"
        acc = Account("beem", steem_instance=bts)
        tx = acc.transfer(
            "test1", 1.33, "SBD", memo="Foobar")
        self.assertEqual(
            tx["operations"][0][0],
            "transfer"
        )
        self.assertEqual(len(tx['signatures']), 1)
        op = tx["operations"][0][1]
        self.assertIn("memo", op)
        self.assertEqual(op["from"], "beem")
        self.assertEqual(op["to"], "test1")
        amount = Amount(op["amount"], steem_instance=bts)
        self.assertEqual(float(amount), 1.33)
        bts.nobroadcast = True

    def test_transfer_1of1(self):
        steem = self.bts
        steem.nobroadcast = False
        tx = TransactionBuilder(steem_instance=steem)
        tx.appendOps(Transfer(**{"from": 'beem',
                                 "to": 'leprechaun',
                                 "amount": '0.01 SBD',
                                 "memo": '1 of 1 transaction'}))
        self.assertEqual(
            tx["operations"][0][0],
            "transfer"
        )
        tx.appendWif(self.active_key)
        tx.sign()
        tx.sign()
        self.assertEqual(len(tx['signatures']), 1)
        tx.broadcast()
        steem.nobroadcast = True

    def test_transfer_2of2_simple(self):
        # Send a 2 of 2 transaction from elf which needs steemfiles's cosign to send funds
        steem = self.bts
        steem.nobroadcast = False
        tx = TransactionBuilder(steem_instance=steem)
        tx.appendOps(Transfer(**{"from": 'elf',
                                 "to": 'leprechaun',
                                 "amount": '0.01 SBD',
                                 "memo": '2 of 2 simple transaction'}))

        tx.appendWif(self.active_private_key_of_elf)
        tx.sign()
        tx.clearWifs()
        tx.appendWif(self.active_private_key_of_steemfiles)
        tx.sign(reconstruct_tx=False)
        self.assertEqual(len(tx['signatures']), 2)
        tx.broadcast()
        steem.nobroadcast = True

    def test_transfer_2of2_wallet(self):
        # Send a 2 of 2 transaction from elf which needs steemfiles's cosign to send
        # priv key of elf and steemfiles are stored in the wallet
        # appendSigner fetches both keys and signs automatically with both keys.
        steem = self.bts
        steem.nobroadcast = False
        steem.wallet.unlock("123")

        tx = TransactionBuilder(steem_instance=steem)
        tx.appendOps(Transfer(**{"from": 'elf',
                                 "to": 'leprechaun',
                                 "amount": '0.01 SBD',
                                 "memo": '2 of 2 serialized/deserialized transaction'}))

        tx.appendSigner("elf", "active")
        tx.sign()
        self.assertEqual(len(tx['signatures']), 2)
        tx.broadcast()
        steem.nobroadcast = True

    def test_transfer_2of2_serialized_deserialized(self):
        # Send a 2 of 2 transaction from elf which needs steemfiles's cosign to send
        # funds but sign the transaction with elf's key and then serialize the transaction
        # and deserialize the transaction.  After that, sign with steemfiles's key.
        steem = self.bts
        steem.nobroadcast = False
        steem.wallet.unlock("123")
        steem.wallet.removeAccount("steemfiles")

        tx = TransactionBuilder(steem_instance=steem)
        tx.appendOps(Transfer(**{"from": 'elf',
                                 "to": 'leprechaun',
                                 "amount": '0.01 SBD',
                                 "memo": '2 of 2 serialized/deserialized transaction'}))

        tx.appendSigner("elf", "active")
        tx.addSigningInformation("elf", "active")
        tx.sign()
        tx.clearWifs()
        self.assertEqual(len(tx['signatures']), 1)
        steem.wallet.removeAccount("elf")
        tx_json = tx.json()
        del tx
        new_tx = TransactionBuilder(tx=tx_json, steem_instance=steem)
        self.assertEqual(len(new_tx['signatures']), 1)
        steem.wallet.addPrivateKey(self.active_private_key_of_steemfiles)
        new_tx.appendMissingSignatures()
        new_tx.sign(reconstruct_tx=False)
        self.assertEqual(len(new_tx['signatures']), 2)
        new_tx.broadcast()
        steem.nobroadcast = True

    def test_transfer_2of2_offline(self):
        # Send a 2 of 2 transaction from elf which needs steemfiles's cosign to send
        # funds but sign the transaction with elf's key and then serialize the transaction
        # and deserialize the transaction.  After that, sign with steemfiles's key.
        steem = self.bts
        steem.nobroadcast = False
        steem.wallet.unlock("123")
        steem.wallet.removeAccount("steemfiles")

        tx = TransactionBuilder(steem_instance=steem)
        tx.appendOps(Transfer(**{"from": 'elf',
                                 "to": 'leprechaun',
                                 "amount": '0.01 SBD',
                                 "memo": '2 of 2 serialized/deserialized transaction'}))

        tx.appendSigner("elf", "active")
        tx.addSigningInformation("elf", "active")
        tx.sign()
        tx.clearWifs()
        self.assertEqual(len(tx['signatures']), 1)
        steem.wallet.removeAccount("elf")
        steem.wallet.addPrivateKey(self.active_private_key_of_steemfiles)
        tx.appendMissingSignatures()
        tx.sign(reconstruct_tx=False)
        self.assertEqual(len(tx['signatures']), 2)
        tx.broadcast()
        steem.nobroadcast = True
        steem.wallet.addPrivateKey(self.active_private_key_of_elf)

    def test_transfer_2of2_wif(self):
        nodelist = NodeList()
        # Send a 2 of 2 transaction from elf which needs steemfiles's cosign to send
        # funds but sign the transaction with elf's key and then serialize the transaction
        # and deserialize the transaction.  After that, sign with steemfiles's key.
        steem = Steem(
            node=nodelist.get_testnet(),
            num_retries=10,
            keys=[self.active_private_key_of_elf],
            expiration=120,
        )

        tx = TransactionBuilder(steem_instance=steem)
        tx.appendOps(Transfer(**{"from": 'elf',
                                 "to": 'leprechaun',
                                 "amount": '0.01 SBD',
                                 "memo": '2 of 2 serialized/deserialized transaction'}))

        tx.appendSigner("elf", "active")
        tx.addSigningInformation("elf", "active")
        tx.sign()
        tx.clearWifs()
        self.assertEqual(len(tx['signatures']), 1)
        tx_json = tx.json()
        del steem
        del tx

        steem = Steem(
            node=nodelist.get_testnet(),
            num_retries=10,
            keys=[self.active_private_key_of_steemfiles],
            expiration=120,
        )
        new_tx = TransactionBuilder(tx=tx_json, steem_instance=steem)
        new_tx.appendMissingSignatures()
        new_tx.sign(reconstruct_tx=False)
        self.assertEqual(len(new_tx['signatures']), 2)
        new_tx.broadcast()

    def test_verifyAuthority(self):
        stm = self.bts
        stm.wallet.unlock("123")
        tx = TransactionBuilder(steem_instance=stm)
        tx.appendOps(Transfer(**{"from": "beem",
                                 "to": "test1",
                                 "amount": "1.33 STEEM",
                                 "memo": "Foobar"}))
        account = Account("beem", steem_instance=stm)
        tx.appendSigner(account, "active")
        self.assertTrue(len(tx.wifs) > 0)
        tx.sign()
        tx.verify_authority()
        self.assertTrue(len(tx["signatures"]) > 0)

    def test_create_account(self):
        bts = self.bts
        name = ''.join(random.choice(string.ascii_lowercase) for _ in range(12))
        key1 = PrivateKey()
        key2 = PrivateKey()
        key3 = PrivateKey()
        key4 = PrivateKey()
        key5 = PrivateKey()
        tx = bts.create_account(
            name,
            creator="beem",
            owner_key=format(key1.pubkey, core_unit),
            active_key=format(key2.pubkey, core_unit),
            posting_key=format(key3.pubkey, core_unit),
            memo_key=format(key4.pubkey, core_unit),
            additional_owner_keys=[format(key5.pubkey, core_unit)],
            additional_active_keys=[format(key5.pubkey, core_unit)],
            additional_owner_accounts=["test1"],  # 1.2.0
            additional_active_accounts=["test1"],
            storekeys=False
        )
        self.assertEqual(
            tx["operations"][0][0],
            "account_create"
        )
        op = tx["operations"][0][1]
        role = "active"
        self.assertIn(
            format(key5.pubkey, core_unit),
            [x[0] for x in op[role]["key_auths"]])
        self.assertIn(
            format(key5.pubkey, core_unit),
            [x[0] for x in op[role]["key_auths"]])
        self.assertIn(
            "test1",
            [x[0] for x in op[role]["account_auths"]])
        role = "owner"
        self.assertIn(
            format(key5.pubkey, core_unit),
            [x[0] for x in op[role]["key_auths"]])
        self.assertIn(
            format(key5.pubkey, core_unit),
            [x[0] for x in op[role]["key_auths"]])
        self.assertIn(
            "test1",
            [x[0] for x in op[role]["account_auths"]])
        self.assertEqual(
            op["creator"],
            "beem")

    def test_connect(self):
        nodelist = NodeList()
        self.bts.connect(node=nodelist.get_testnet())
        bts = self.bts
        self.assertEqual(bts.prefix, "STX")

    def test_set_default_account(self):
        self.bts.set_default_account("beem")

    def test_info(self):
        info = self.bts.info()
        for key in ['current_witness',
                    'head_block_id',
                    'head_block_number',
                    'id',
                    'last_irreversible_block_num',
                    'current_witness',
                    'total_pow',
                    'time']:
            self.assertTrue(key in info)

    def test_finalizeOps(self):
        bts = self.bts
        tx1 = bts.new_tx()
        tx2 = bts.new_tx()

        acc = Account("beem", steem_instance=bts)
        acc.transfer("test1", 1, "STEEM", append_to=tx1)
        acc.transfer("test1", 2, "STEEM", append_to=tx2)
        acc.transfer("test1", 3, "STEEM", append_to=tx1)
        tx1 = tx1.json()
        tx2 = tx2.json()
        ops1 = tx1["operations"]
        ops2 = tx2["operations"]
        self.assertEqual(len(ops1), 2)
        self.assertEqual(len(ops2), 1)

    def test_weight_threshold(self):
        bts = self.bts
        auth = {'account_auths': [['test', 1]],
                'extensions': [],
                'key_auths': [
                    ['STX55VCzsb47NZwWe5F3qyQKedX9iHBHMVVFSc96PDvV7wuj7W86n', 1],
                    ['STX7GM9YXcsoAJAgKbqW2oVj7bnNXFNL4pk9NugqKWPmuhoEDbkDv', 1]],
                'weight_threshold': 3}  # threshold fine
        bts._test_weights_treshold(auth)
        auth = {'account_auths': [['test', 1]],
                'extensions': [],
                'key_auths': [
                    ['STX55VCzsb47NZwWe5F3qyQKedX9iHBHMVVFSc96PDvV7wuj7W86n', 1],
                    ['STX7GM9YXcsoAJAgKbqW2oVj7bnNXFNL4pk9NugqKWPmuhoEDbkDv', 1]],
                'weight_threshold': 4}  # too high

        with self.assertRaises(ValueError):
            bts._test_weights_treshold(auth)

    def test_allow(self):
        bts = self.bts
        self.assertIn(bts.prefix, "STX")
        acc = Account("beem", steem_instance=bts)
        self.assertIn(acc.steem.prefix, "STX")
        tx = acc.allow(
            "STX55VCzsb47NZwWe5F3qyQKedX9iHBHMVVFSc96PDvV7wuj7W86n",
            account="beem",
            weight=1,
            threshold=1,
            permission="active",
        )
        self.assertEqual(
            (tx["operations"][0][0]),
            "account_update"
        )
        op = tx["operations"][0][1]
        self.assertIn("active", op)
        self.assertIn(
            ["STX55VCzsb47NZwWe5F3qyQKedX9iHBHMVVFSc96PDvV7wuj7W86n", '1'],
            op["active"]["key_auths"])
        self.assertEqual(op["active"]["weight_threshold"], 1)

    def test_disallow(self):
        bts = self.bts
        acc = Account("beem", steem_instance=bts)
        if sys.version > '3':
            _assertRaisesRegex = self.assertRaisesRegex
        else:
            _assertRaisesRegex = self.assertRaisesRegexp
        with _assertRaisesRegex(ValueError, ".*Changes nothing.*"):
            acc.disallow(
                "STX55VCzsb47NZwWe5F3qyQKedX9iHBHMVVFSc96PDvV7wuj7W86n",
                weight=1,
                threshold=1,
                permission="active"
            )
        with _assertRaisesRegex(ValueError, ".*Changes nothing!.*"):
            acc.disallow(
                "STX6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV",
                weight=1,
                threshold=1,
                permission="active"
            )

    def test_update_memo_key(self):
        bts = self.bts
        bts.wallet.unlock("123")
        self.assertEqual(bts.prefix, "STX")
        acc = Account("beem", steem_instance=bts)
        tx = acc.update_memo_key("STX55VCzsb47NZwWe5F3qyQKedX9iHBHMVVFSc96PDvV7wuj7W86n")
        self.assertEqual(
            (tx["operations"][0][0]),
            "account_update"
        )
        op = tx["operations"][0][1]
        self.assertEqual(
            op["memo_key"],
            "STX55VCzsb47NZwWe5F3qyQKedX9iHBHMVVFSc96PDvV7wuj7W86n")

    def test_approvewitness(self):
        bts = self.bts
        w = Account("beem", steem_instance=bts)
        tx = w.approvewitness("test1")
        self.assertEqual(
            (tx["operations"][0][0]),
            "account_witness_vote"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test1",
            op["witness"])
