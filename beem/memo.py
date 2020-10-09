# -*- coding: utf-8 -*-
from beem.instance import shared_blockchain_instance
import random
import os
import struct
from binascii import hexlify, unhexlify
from beemgraphenebase.base58 import base58encode, base58decode
from beem.version import version as __version__
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
            m = Memo("holger80", "beempy")
            m.unlock_wallet("secret")
            enc = (m.encrypt("test"))
            print(enc)
            >> {'message': '#DTpKcbxWqsETCRfjYGk9feERFa5nVBF8FaHfWPwUjyHBTgNhXGh4mN5TTG41nLhUcHtXfu7Hy3AwLrtWvo1ERUyAZaJjaEZNhHyoeDnrHdWChrzbccbANQmazgwjyxzEL', 'from': 'STM6MQBLaX9Q15CK3prXoWK4C6EqtsL7C4rqq1h6BQjxvfk9tuT3N', 'to': 'STM6sRudsxWpTZWxnpRkCDVD51RteiJnvJYCt5LiZAbVLfM1hJCQC'}
            print(m.decrypt(enc))
            >> foobar

        To decrypt a memo, simply use

        .. code-block:: python

            from beem.memo import Memo
            m = Memo()
            m.unlock_wallet("secret")
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

        if to_account and len(to_account) < 51:
            self.to_account = Account(to_account, blockchain_instance=self.blockchain)
        elif to_account and len(to_account) >= 51:
            self.to_account = PublicKey(to_account)
        else:
            self.to_account = None
        if from_account and len(from_account) < 51:
            self.from_account = Account(from_account, blockchain_instance=self.blockchain)
        elif from_account and len(from_account) >= 51:
            self.from_account = PrivateKey(from_account)
        else:
            self.from_account = None

    def unlock_wallet(self, *args, **kwargs):
        """ Unlock the library internal wallet
        """
        self.blockchain.wallet.unlock(*args, **kwargs)

    def encrypt(self, memo, bts_encrypt=False, return_enc_memo_only=False, nonce=None):
        """ Encrypt a memo

            :param str memo: clear text memo message
            :param bool return_enc_memo_only: When True, only the encoded memo is returned
            :param str nonce: when not set, a random string is generated and used
            :returns: encrypted memo
            :rtype: dict
        """
        if not memo:
            return None
        if nonce is None:
            nonce = str(random.getrandbits(64))
        if isinstance(self.from_account, Account):
            memo_wif = self.blockchain.wallet.getPrivateKeyForPublicKey(
                self.from_account["memo_key"]
            )
            memo_wif = PrivateKey(memo_wif)
        else:
            memo_wif = self.from_account
        if isinstance(self.to_account, Account):
            pubkey = self.to_account["memo_key"]
        else:
            pubkey = self.to_account
        if not memo_wif:
            raise MissingKeyError("Memo key for %s missing!" % self.from_account["name"])

        if not hasattr(self, 'chain_prefix'):
            self.chain_prefix = self.blockchain.prefix

        if bts_encrypt:
            enc = BtsMemo.encode_memo_bts(
                PrivateKey(memo_wif),
                PublicKey(
                    pubkey,
                    prefix=self.chain_prefix
                ),
                nonce,
                memo
            )

            return {
                "message": enc,
                "nonce": nonce,
                "from": str(PrivateKey(memo_wif).pubkey),
                "to": str(pubkey)
            }
        else:
            enc = BtsMemo.encode_memo(
                PrivateKey(memo_wif),
                PublicKey(
                    pubkey,
                    prefix=self.chain_prefix
                ),
                nonce,
                memo,
                prefix=self.chain_prefix
            )
            if return_enc_memo_only:
                return enc
            return {
                "message": enc,
                "from": str(PrivateKey(memo_wif).pubkey),
                "to": str(pubkey)
            }

    def encrypt_binary(self, infile, outfile, buffer_size=2048, nonce=None):
        """ Encrypt a binary file

            :param str infile: input file name
            :param str outfile: output file name
            :param int buffer_size: write buffer size
            :param str nonce: when not set, a random string is generated and used
        """
        if not os.path.exists(infile):
            raise ValueError("%s does not exists!" % infile)

        if nonce is None:
            nonce = str(random.getrandbits(64))
        if isinstance(self.from_account, Account):
            memo_wif = self.blockchain.wallet.getPrivateKeyForPublicKey(
                self.from_account["memo_key"]
            )
        else:
            memo_wif = self.from_account
        if isinstance(self.to_account, Account):
            pubkey = self.to_account["memo_key"]
        else:
            pubkey = self.to_account        
        if not memo_wif:
            raise MissingKeyError("Memo key for %s missing!" % self.from_account["name"])

        if not hasattr(self, 'chain_prefix'):
            self.chain_prefix = self.blockchain.prefix

        file_size = os.path.getsize(infile)
        priv = PrivateKey(memo_wif)
        pub = PublicKey(
                pubkey,
                prefix=self.chain_prefix
            )
        enc = BtsMemo.encode_memo(
            priv,
            pub,
            nonce,
            "beem/%s" % __version__,
            prefix=self.chain_prefix
        )
        enc = unhexlify(base58decode(enc[1:]))
        shared_secret = BtsMemo.get_shared_secret(priv, pub)
        aes, check = BtsMemo.init_aes(shared_secret, nonce)
        with open(outfile, 'wb') as fout:
            fout.write(struct.pack('<Q', len(enc)))
            fout.write(enc)
            fout.write(struct.pack('<Q', file_size))
            with open(infile, 'rb') as fin:
                while True:
                    data = fin.read(buffer_size)
                    n = len(data)
                    if n == 0:
                        break
                    elif n % 16 != 0:
                        data += b' ' * (16 - n % 16) # <- padded with spaces
                    encd = aes.encrypt(data)
                    fout.write(encd)

    def extract_decrypt_memo_data(self, memo):
        """ Returns information about an encrypted memo
        """
        from_key, to_key, nonce, check, cipher = BtsMemo.extract_memo_data(memo)
        return from_key, to_key, nonce

    def decrypt(self, memo):
        """ Decrypt a memo

            :param str memo: encrypted memo message
            :returns: encrypted memo
            :rtype: str
        """
        if not memo:
            return None
        memo_wif = None
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
        
        if memo_to is None or memo_from is None:
            from_key, to_key, nonce, check, cipher = BtsMemo.extract_memo_data(message)
            try:
                memo_wif = self.blockchain.wallet.getPrivateKeyForPublicKey(
                    str(to_key)
                )
                pubkey = from_key
            except MissingKeyError:
                try:
                    # if that failed, we assume that we have sent the memo
                    memo_wif = self.blockchain.wallet.getPrivateKeyForPublicKey(
                        str(from_key)
                    )
                    pubkey = to_key
                except MissingKeyError:
                    # if all fails, raise exception
                    raise MissingKeyError(
                        "Non of the required memo keys are installed!"
                        "Need any of {}".format(
                        [str(to_key), str(from_key)]))
        elif memo_to is not None and memo_from is not None and isinstance(memo_from, PrivateKey):
            memo_wif = memo_from
            pubkey = memo_to
        elif memo_to is not None and memo_from is not None and isinstance(memo_to, PrivateKey):
            memo_wif = memo_to
            pubkey = memo_from           
        else:
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

        if message[0] == '#' or memo_to is None or memo_from is None:
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

    def decrypt_binary(self, infile, outfile, buffer_size=2048):
        """ Decrypt a binary file

            :param str infile: encrypted binary file
            :param str outfile: output file name
            :param int buffer_size: read buffer size
            :returns: encrypted memo information
            :rtype: dict
        """
        if not os.path.exists(infile):
            raise ValueError("%s does not exists!" % infile)
        if buffer_size % 16 != 0:
            raise ValueError("buffer_size must be dividable by 16")
        with open(infile, 'rb') as fin:
            memo_size = struct.unpack('<Q', fin.read(struct.calcsize('<Q')))[0]
            memo = fin.read(memo_size)
            orig_file_size = struct.unpack('<Q', fin.read(struct.calcsize('<Q')))[0]
        memo = '#' + base58encode(hexlify(memo).decode("ascii"))
        memo_to = self.to_account
        memo_from = self.from_account
        from_key, to_key, nonce, check, cipher = BtsMemo.extract_memo_data(memo)
        if memo_to is None and memo_from is None:
            try:
                memo_wif = self.blockchain.wallet.getPrivateKeyForPublicKey(
                    str(to_key)
                )
                pubkey = from_key
            except MissingKeyError:
                try:
                    # if that failed, we assume that we have sent the memo
                    memo_wif = self.blockchain.wallet.getPrivateKeyForPublicKey(
                        str(from_key)
                    )
                    pubkey = to_key
                except MissingKeyError:
                    # if all fails, raise exception
                    raise MissingKeyError(
                        "Non of the required memo keys are installed!"
                        "Need any of {}".format(
                        [str(to_key), str(from_key)]))
        elif memo_to is not None and memo_from is not None and isinstance(memo_from, PrivateKey):
            memo_wif = memo_from
            if isinstance(memo_to, Account):
                pubkey = memo_to["memo_key"]
            else:
                pubkey = memo_to
        elif memo_to is not None and memo_from is not None and isinstance(memo_to, PrivateKey):
            memo_wif = memo_to
            if isinstance(memo_from, Account):
                pubkey = memo_from["memo_key"]
            else:
                pubkey = memo_from           
        else:
            
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
        priv = PrivateKey(memo_wif)
        pubkey = PublicKey(pubkey, prefix=self.chain_prefix)
        beem_version = BtsMemo.decode_memo(
                priv,
                memo
            )
        shared_secret = BtsMemo.get_shared_secret(priv, pubkey)
        # Init encryption
        aes, checksum = BtsMemo.init_aes(shared_secret, nonce)
        with open(infile, 'rb') as fin:
            memo_size = struct.unpack('<Q', fin.read(struct.calcsize('<Q')))[0]
            memo = fin.read(memo_size)
            file_size = struct.unpack('<Q', fin.read(struct.calcsize('<Q')))[0]
            with open(outfile, 'wb') as fout:
                while True:
                    data = fin.read(buffer_size)
                    n = len(data)
                    if n == 0:
                        break
                    decd = aes.decrypt(data)
                    n = len(decd)
                    if file_size > n:
                        fout.write(decd)
                    else:
                        fout.write(decd[:file_size]) # <- remove padding on last block
                    file_size -= n        
        return {
            "file_size": orig_file_size,
            "from_key": str(from_key),
            "to_key": str(to_key),
            "nonce": nonce,
            "beem_version": beem_version
        }
