# -*- coding: utf-8 -*-
import re
import json
import logging
from binascii import hexlify, unhexlify
from datetime import datetime
from beemgraphenebase.ecdsasig import verify_message, sign_message
from beemgraphenebase.account import PublicKey
from beem.instance import shared_blockchain_instance
from beem.account import Account
from .exceptions import InvalidMessageSignature, WrongMemoKey, AccountDoesNotExistsException, InvalidMemoKeyException


log = logging.getLogger(__name__)


class MessageV1(object):
    """ Allow to sign and verify Messages that are sigend with a private key
    """

    MESSAGE_SPLIT = (
        "-----BEGIN HIVE SIGNED MESSAGE-----",
        "-----BEGIN META-----",
        "-----BEGIN SIGNATURE-----",
        "-----END HIVE SIGNED MESSAGE-----",
    )

    # This is the message that is actually signed
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
{MESSAGE_SPLIT[3]}"""

    def __init__(self, message, blockchain_instance=None, *args, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        self.message = message.replace("\r\n", "\n")
        self.signed_by_account = None
        self.signed_by_name = None
        self.meta = None
        self.plain_message = None

    def sign(self, account=None, **kwargs):
        """ Sign a message with an account's memo key
            :param str account: (optional) the account that owns the bet
                (defaults to ``default_account``)
            :raises ValueError: If not account for signing is provided
            :returns: the signed message encapsulated in a known format
        """
        if not account:
            if "default_account" in self.blockchain.config:
                account = self.blockchain.config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        # Data for message
        account = Account(account, blockchain_instance=self.blockchain)
        info = self.blockchain.info()
        meta = dict(
            timestamp=info["time"],
            block=info["head_block_number"],
            memokey=account["memo_key"],
            account=account["name"],
        )

        # wif key
        wif = self.blockchain.wallet.getPrivateKeyForPublicKey(
            account["memo_key"]
        )

        # We strip the message here so we know for sure there are no trailing
        # whitespaces or returns
        message = self.message.strip()

        enc_message = self.SIGNED_MESSAGE_META.format(**locals())

        # signature
        signature = hexlify(sign_message(enc_message, wif)).decode("ascii")

        self.signed_by_account = account
        self.signed_by_name = account["name"]
        self.meta = meta
        self.plain_message = message

        return self.SIGNED_MESSAGE_ENCAPSULATED.format(
            MESSAGE_SPLIT=self.MESSAGE_SPLIT, **locals()
        )

    def verify(self, **kwargs):
        """ Verify a message with an account's memo key
            :param str account: (optional) the account that owns the bet
                (defaults to ``default_account``)
            :returns: True if the message is verified successfully
            :raises InvalidMessageSignature if the signature is not ok
        """
        # Split message into its parts
        parts = re.split("|".join(self.MESSAGE_SPLIT), self.message)
        parts = [x for x in parts if x.strip()]

        assert len(parts) > 2, "Incorrect number of message parts"

        # Strip away all whitespaces before and after the message
        message = parts[0].strip()
        signature = parts[2].strip()
        # Parse the meta data
        meta = dict(re.findall(r"(\S+)=(.*)", parts[1]))

        log.info("Message is: {}".format(message))
        log.info("Meta is: {}".format(json.dumps(meta)))
        log.info("Signature is: {}".format(signature))

        # Ensure we have all the data in meta
        assert "account" in meta, "No 'account' could be found in meta data"
        assert "memokey" in meta, "No 'memokey' could be found in meta data"
        assert "block" in meta, "No 'block' could be found in meta data"
        assert "timestamp" in meta, "No 'timestamp' could be found in meta data"

        account_name = meta.get("account").strip()
        memo_key = meta["memokey"].strip()

        try:
            PublicKey(memo_key, prefix=self.blockchain.prefix)
        except Exception:
            raise InvalidMemoKeyException("The memo key in the message is invalid")

        # Load account from blockchain
        try:
            account = Account(
                account_name, blockchain_instance=self.blockchain
            )
        except AccountDoesNotExistsException:
            raise AccountDoesNotExistsException(
                "Could not find account {}. Are you connected to the right chain?".format(
                    account_name
                )
            )

        # Test if memo key is the same as on the blockchain
        if not account["memo_key"] == memo_key:
            raise WrongMemoKey(
                "Memo Key of account {} on the Blockchain ".format(account["name"])
                + "differs from memo key in the message: {} != {}".format(
                    account["memo_key"], memo_key
                )
            )

        # Reformat message
        enc_message = self.SIGNED_MESSAGE_META.format(**locals())

        # Verify Signature
        pubkey = verify_message(enc_message, unhexlify(signature))

        # Verify pubky
        pk = PublicKey(
            hexlify(pubkey).decode("ascii"), prefix=self.blockchain.prefix
        )
        if format(pk, self.blockchain.prefix) != memo_key:
            raise InvalidMessageSignature("The signature doesn't match the memo key")

        self.signed_by_account = account
        self.signed_by_name = account["name"]
        self.meta = meta
        self.plain_message = message

        return True


class MessageV2(object):
    """ Allow to sign and verify Messages that are sigend with a private key
    """

    def __init__(self, message, blockchain_instance=None, *args, **kwargs):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]
        self.blockchain = blockchain_instance or shared_blockchain_instance()

        self.message = message
        self.signed_by_account = None
        self.signed_by_name = None
        self.meta = None
        self.plain_message = None

    def sign(self, account=None, **kwargs):
        """ Sign a message with an account's memo key
            :param str account: (optional) the account that owns the bet
                (defaults to ``default_account``)
            :raises ValueError: If not account for signing is provided
            :returns: the signed message encapsulated in a known format
        """
        if not account:
            if "default_account" in self.blockchain.config:
                account = self.blockchain.config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        # Data for message
        account = Account(account, blockchain_instance=self.blockchain)

        # wif key
        wif = self.blockchain.wallet.getPrivateKeyForPublicKey(
            account["memo_key"]
        )

        payload = [
            "from",
            account["name"],
            "key",
            account["memo_key"],
            "time",
            str(datetime.utcnow()),
            "text",
            self.message,
        ]
        enc_message = json.dumps(payload, separators=(",", ":"))

        # signature
        signature = hexlify(sign_message(enc_message, wif)).decode("ascii")

        return dict(signed=enc_message, payload=payload, signature=signature)

    def verify(self, **kwargs):
        """ Verify a message with an account's memo key
            :param str account: (optional) the account that owns the bet
                (defaults to ``default_account``)
            :returns: True if the message is verified successfully
            :raises InvalidMessageSignature if the signature is not ok
        """
        if not isinstance(self.message, dict):
            try:
                self.message = json.loads(self.message)
            except Exception:
                raise ValueError("Message must be valid JSON")

        payload = self.message.get("payload")
        assert payload, "Missing payload"
        payload_dict = {k[0]: k[1] for k in zip(payload[::2], payload[1::2])}
        signature = self.message.get("signature")

        account_name = payload_dict.get("from").strip()
        memo_key = payload_dict.get("key").strip()

        assert account_name, "Missing account name 'from'"
        assert memo_key, "missing 'key'"

        try:
            Account(memo_key, prefix=self.blockchain.prefix)
        except Exception:
            raise InvalidMemoKeyException("The memo key in the message is invalid")

        # Load account from blockchain
        try:
            account = Account(
                account_name, blockchain_instance=self.blockchain
            )
        except AccountDoesNotExistsException:
            raise AccountDoesNotExistsException(
                "Could not find account {}. Are you connected to the right chain?".format(
                    account_name
                )
            )

        # Test if memo key is the same as on the blockchain
        if not account["memo_key"] == memo_key:
            raise WrongMemoKey(
                "Memo Key of account {} on the Blockchain ".format(account["name"])
                + "differs from memo key in the message: {} != {}".format(
                    account["memo_key"], memo_key
                )
            )

        # Ensure payload and signed match
        signed_target = json.dumps(self.message.get("payload"), separators=(",", ":"))
        signed_actual = self.message.get("signed")
        assert (
            signed_target == signed_actual
        ), "payload doesn't match signed message: \n{}\n{}".format(
            signed_target, signed_actual
        )

        # Reformat message
        enc_message = self.message.get("signed")

        # Verify Signature
        pubkey = verify_message(enc_message, unhexlify(signature))

        # Verify pubky
        pk = PublicKey(
            hexlify(pubkey).decode("ascii"), prefix=self.blockchain.prefix
        )
        if format(pk, self.blockchain.prefix) != memo_key:
            raise InvalidMessageSignature("The signature doesn't match the memo key")

        self.signed_by_account = account
        self.signed_by_name = account["name"]
        self.plain_message = payload_dict.get("text")

        return True


class Message(MessageV1, MessageV2):
    supported_formats = (MessageV1, MessageV2)
    valid_exceptions = (
        AccountDoesNotExistsException,
        InvalidMessageSignature,
        WrongMemoKey,
        InvalidMemoKeyException,
    )

    def __init__(self, *args, **kwargs):
        for _format in self.supported_formats:
            try:
                _format.__init__(self, *args, **kwargs)
                return
            except self.valid_exceptions as e:
                raise e
            except Exception as e:
                log.warning(
                    "{}: Couldn't init: {}: {}".format(
                        _format.__name__, e.__class__.__name__, str(e)
                    )
                )

    def verify(self, **kwargs):
        for _format in self.supported_formats:
            try:
                return _format.verify(self, **kwargs)
            except self.valid_exceptions as e:
                raise e
            except Exception as e:
                log.warning(
                    "{}: Couldn't verify: {}: {}".format(
                        _format.__name__, e.__class__.__name__, str(e)
                    )
                )
        raise ValueError("No Decoder accepted the message")

    def sign(self, *args, **kwargs):
        for _format in self.supported_formats:
            try:
                return _format.sign(self, *args, **kwargs)
            except self.valid_exceptions as e:
                raise e
            except Exception as e:
                log.warning(
                    "{}: Couldn't sign: {}: {}".format(
                        _format.__name__, e.__class__.__name__, str(e)
                    )
                )
        raise ValueError("No Decoder accepted the message")