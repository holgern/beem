# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import object
import re
import logging
from binascii import hexlify, unhexlify
from beemgraphenebase.ecdsasig import verify_message, sign_message
from beemgraphenebase.account import PublicKey
from beem.instance import shared_steem_instance
from beem.account import Account
from .exceptions import InvalidMessageSignature
from .storage import get_default_config_storage


log = logging.getLogger(__name__)

MESSAGE_SPLIT = (
    "-----BEGIN STEEM SIGNED MESSAGE-----",
    "-----BEGIN META-----",
    "-----BEGIN SIGNATURE-----",
    "-----END STEEM SIGNED MESSAGE-----"
)

SIGNED_MESSAGE_META = """{message}
account={meta[account]}
memokey={meta[memokey]}
block={meta[block]}
timestamp={meta[timestamp]}"""

SIGNED_MESSAGE_ENCAPSULATED = """
{MESSAGE_SPLIT[0]}
{message}
{MESSAGE_SPLIT[1]}
account={meta[account]}
memokey={meta[memokey]}
block={meta[block]}
timestamp={meta[timestamp]}
{MESSAGE_SPLIT[2]}
{signature}
{MESSAGE_SPLIT[3]}
"""


class Message(object):

    def __init__(self, message, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        self.message = message

    def sign(self, account=None, **kwargs):
        """ Sign a message with an account's memo key

            :param str account: (optional) the account that owns the bet
                (defaults to ``default_account``)

            :returns: the signed message encapsulated in a known format

        """
        config = get_default_config_storage()
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        # Data for message
        account = Account(account, steem_instance=self.steem)
        info = self.steem.info()
        meta = dict(
            timestamp=info["time"],
            block=info["head_block_number"],
            memokey=account["memo_key"],
            account=account["name"])

        # wif key
        wif = self.steem.wallet.getPrivateKeyForPublicKey(
            account["memo_key"]
        )

        # signature
        message = self.message.strip()
        signature = hexlify(sign_message(
            SIGNED_MESSAGE_META.format(**locals()),
            wif
        )).decode("ascii")

        message = self.message
        return SIGNED_MESSAGE_ENCAPSULATED.format(
            MESSAGE_SPLIT=MESSAGE_SPLIT,
            **locals()
        )

    def verify(self, **kwargs):
        """ Verify a message with an account's memo key

            :param str account: (optional) the account that owns the bet
                (defaults to ``default_account``)

            :returns: True if the message is verified successfully

            :raises InvalidMessageSignature: if the signature is not ok

        """
        # Split message into its parts
        parts = re.split("|".join(MESSAGE_SPLIT), self.message)
        parts = [x for x in parts if x.strip()]

        if not len(parts) > 2:
            raise AssertionError("Incorrect number of message parts")

        message = parts[0].strip()
        signature = parts[2].strip()
        # Parse the meta data
        meta = dict(re.findall(r'(\S+)=(.*)', parts[1]))

        # Ensure we have all the data in meta
        if "account" not in meta:
            raise AssertionError()
        if "memokey" not in meta:
            raise AssertionError()
        if "block" not in meta:
            raise AssertionError()
        if "timestamp" not in meta:
            raise AssertionError()

        # Load account from blockchain
        account = Account(
            meta.get("account"),
            steem_instance=self.steem)

        # Test if memo key is the same as on the blockchain
        if not account["memo_key"] == meta["memokey"]:
            log.error(
                "Memo Key of account {} on the Blockchain".format(
                    account["name"]) +
                "differs from memo key in the message: {} != {}".format(
                    account["memo_key"], meta["memokey"]
                )
            )

        # Reformat message
        message = SIGNED_MESSAGE_META.format(**locals())

        # Verify Signature
        pubkey = verify_message(message, unhexlify(signature))

        # Verify pubky
        pk = PublicKey(hexlify(pubkey).decode("ascii"))
        if format(pk, self.steem.prefix) != meta["memokey"]:
            raise InvalidMessageSignature

        return True
