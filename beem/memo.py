# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from builtins import object
from beem.instance import shared_blockchain_instance
import random
from beembase import memo as BtsMemo
from beemgraphenebase.account import PrivateKey, PublicKey
from .account import Account
from .exceptions import MissingKeyError


class Memo(object):
    """ Deals with Memos that are attached to a transfer

        :param Account from_account: Account that has sent the memo
        :param Account to_account: Account that has received the memo
        :param Steem blockchain_instance: Steem instance

        A memo is encrypted with a shared secret derived from a private key of
        the sender and a public key of the receiver. Due to the underlying
        mathematics, the same shared secret can be derived by the private key
        of the receiver and the public key of the sender. The encrypted message
        is perturbed by a nonce that is part of the transmitted message.

        .. code-block:: python

            from beem.memo import Memo
            m = Memo("steemeu", "wallet.xeroc")
            m.steem.wallet.unlock("secret")
            enc = (m.encrypt("foobar"))
            print(enc)
            >> {'nonce': '17329630356955254641', 'message': '8563e2bb2976e0217806d642901a2855'}
            print(m.decrypt(enc))
            >> foobar

        To decrypt a memo, simply use

        .. code-block:: python

            from beem.memo import Memo
            m = Memo()
            m.steem.wallet.unlock("secret")
            print(m.decrypt(op_data["memo"]))

        if ``op_data`` being the payload of a transfer operation.

        Memo Keys

        In Steem, memos are AES-256 encrypted with a shared secret between sender and
        receiver. It is derived from the memo private key of the sender and the memo
        public key of the receiver.

        In order for the receiver to decode the memo, the shared secret has to be
        derived from the receiver's private key and the senders public key.

        The memo public key is part of the account and can be retrieved with the
        `get_account` call:

        .. code-block:: js

            get_account <accountname>
            {
              [...]
              "options": {
                "memo_key": "GPH5TPTziKkLexhVKsQKtSpo4bAv5RnB8oXcG4sMHEwCcTf3r7dqE",
                [...]
              },
              [...]
            }

        while the memo private key can be dumped with `dump_private_keys`

        Memo Message

        The take the following form:

        .. code-block:: js

                {
                  "from": "GPH5mgup8evDqMnT86L7scVebRYDC2fwAWmygPEUL43LjstQegYCC",
                  "to": "GPH5Ar4j53kFWuEZQ9XhxbAja4YXMPJ2EnUg5QcrdeMFYUNMMNJbe",
                  "nonce": "13043867485137706821",
                  "message": "d55524c37320920844ca83bb20c8d008"
                }

        The fields `from` and `to` contain the memo public key of sender and receiver.
        The `nonce` is a random integer that is used for the seed of the AES encryption
        of the message.

        Encrypting a memo

        The high level memo class makes use of the beem wallet to obtain keys
        for the corresponding accounts.

        .. code-block:: python

            from beem.memo import Memo
            from beem.account import Account

            memoObj = Memo(
                from_account=Account(from_account),
                to_account=Account(to_account)
            )
            encrypted_memo = memoObj.encrypt(memo)

        Decoding of a received memo

        .. code-block:: python

            from getpass import getpass
            from beem.block import Block
            from beem.memo import Memo

            # Obtain a transfer from the blockchain
            block = Block(23755086)                   # block
            transaction = block["transactions"][3]    # transactions
            op = transaction["operations"][0]         # operation
            op_id = op[0]                             # operation type
            op_data = op[1]                           # operation payload

            # Instantiate Memo for decoding
            memo = Memo()

            # Unlock wallet
            memo.unlock_wallet(getpass())

            # Decode memo
            # Raises exception if required keys not available in the wallet
            print(memo.decrypt(op_data["transfer"]))

    """
    def __init__(
        self,
        from_account=None,
        to_account=None,
        blockchain_instance=None,
        **kwargs
    ):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]
        self.blockchain = blockchain_instance or shared_blockchain_instance()

        if to_account:
            self.to_account = Account(to_account, blockchain_instance=self.blockchain)
        if from_account:
            self.from_account = Account(from_account, blockchain_instance=self.blockchain)

    def unlock_wallet(self, *args, **kwargs):
        """ Unlock the library internal wallet
        """
        self.blockchain.wallet.unlock(*args, **kwargs)
        return self

    def encrypt(self, memo, bts_encrypt=False):
        """ Encrypt a memo

            :param str memo: clear text memo message
            :returns: encrypted memo
            :rtype: str
        """
        if not memo:
            return None

        nonce = str(random.getrandbits(64))
        memo_wif = self.blockchain.wallet.getPrivateKeyForPublicKey(
            self.from_account["memo_key"]
        )
        if not memo_wif:
            raise MissingKeyError("Memo key for %s missing!" % self.from_account["name"])

        if not hasattr(self, 'chain_prefix'):
            self.chain_prefix = self.blockchain.prefix

        if bts_encrypt:
            enc = BtsMemo.encode_memo_bts(
                PrivateKey(memo_wif),
                PublicKey(
                    self.to_account["memo_key"],
                    prefix=self.chain_prefix
                ),
                nonce,
                memo
            )

            return {
                "message": enc,
                "nonce": nonce,
                "from": self.from_account["memo_key"],
                "to": self.to_account["memo_key"]
            }
        else:
            enc = BtsMemo.encode_memo(
                PrivateKey(memo_wif),
                PublicKey(
                    self.to_account["memo_key"],
                    prefix=self.chain_prefix
                ),
                nonce,
                memo,
                prefix=self.chain_prefix
            )

            return {
                "message": enc,
                "from": self.from_account["memo_key"],
                "to": self.to_account["memo_key"]
            }

    def decrypt(self, memo):
        """ Decrypt a memo

            :param str memo: encrypted memo message
            :returns: encrypted memo
            :rtype: str
        """
        if not memo:
            return None

        # We first try to decode assuming we received the memo
        if isinstance(memo, dict) and "to" in memo and "from" in memo and "memo" in memo:
            memo_to = Account(memo["to"], blockchain_instance=self.blockchain)
            memo_from = Account(memo["from"], blockchain_instance=self.blockchain)
            message = memo["memo"]
        else:
            memo_to = self.to_account
            memo_from = self.from_account
            message = memo
        if isinstance(memo, dict) and "nonce" in memo:
            nonce = memo.get("nonce")
        else:
            nonce = ""

        try:
            memo_wif = self.blockchain.wallet.getPrivateKeyForPublicKey(
                memo_to["memo_key"]
            )
            pubkey = memo_from["memo_key"]
        except MissingKeyError:
            try:
                # if that failed, we assume that we have sent the memo
                memo_wif = self.blockchain.wallet.getPrivateKeyForPublicKey(
                    memo_from["memo_key"]
                )
                pubkey = memo_to["memo_key"]
            except MissingKeyError:
                # if all fails, raise exception
                raise MissingKeyError(
                    "Non of the required memo keys are installed!"
                    "Need any of {}".format(
                    [memo_to["name"], memo_from["name"]]))

        if not hasattr(self, 'chain_prefix'):
            self.chain_prefix = self.blockchain.prefix

        if message[0] == '#':
            return BtsMemo.decode_memo(
                PrivateKey(memo_wif),
                message
            )
        else:
            return BtsMemo.decode_memo_bts(
                PrivateKey(memo_wif),
                PublicKey(pubkey, prefix=self.chain_prefix),
                nonce,
                message
            )
