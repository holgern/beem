# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import pytest
from parameterized import parameterized
import unittest
import hashlib
import ecdsa
from binascii import hexlify, unhexlify
from beemgraphenebase.account import PrivateKey, PublicKey, Address
import beemgraphenebase.ecdsasig as ecda
from beemgraphenebase.py23 import py23_bytes


wif = "5J4KCbg1G3my9b9hCaQXnHSm6vrwW9xQTJS6ZciW2Kek7cCkCEk"


class Testcases(unittest.TestCase):

    # Ignore warning:
    # https://www.reddit.com/r/joinmarket/comments/5crhfh/userwarning_implicit_cast_from_char_to_a/
    # @pytest.mark.filterwarnings()
    @parameterized.expand([
        ("cryptography"),
        ("secp256k1"),
        ("ecdsa")
    ])
    def test_sign_message(self, module):
        if module == "cryptography":
            try:
                from cryptography.hazmat.backends import default_backend
                from cryptography.hazmat.primitives import hashes
                from cryptography.hazmat.primitives.asymmetric import ec
                from cryptography.hazmat.primitives.asymmetric.utils \
                    import decode_dss_signature, encode_dss_signature
                from cryptography.exceptions import InvalidSignature
                ecda.SECP256K1_MODULE = "cryptography"
            except ImportError:
                return
        elif module == "secp256k1":
            try:
                import secp256k1
                ecda.SECP256K1_MODULE = "secp256k1"
            except ImportError:
                return
        else:
            ecda.SECP256K1_MODULE = module
        pub_key = py23_bytes(repr(PrivateKey(wif).pubkey), "latin")
        signature = ecda.sign_message("Foobar", wif)
        pub_key_sig = ecda.verify_message("Foobar", signature)
        self.assertEqual(hexlify(pub_key_sig), pub_key)

    @parameterized.expand([
        ("cryptography"),
        ("secp256k1"),
    ])
    def test_sign_message_cross(self, module):
        if module == "cryptography":
            try:
                from cryptography.hazmat.backends import default_backend
                from cryptography.hazmat.primitives import hashes
                from cryptography.hazmat.primitives.asymmetric import ec
                from cryptography.hazmat.primitives.asymmetric.utils \
                    import decode_dss_signature, encode_dss_signature
                from cryptography.exceptions import InvalidSignature
                ecda.SECP256K1_MODULE = "cryptography"
            except ImportError:
                return
        elif module == "secp256k1":
            try:
                import secp256k1
                ecda.SECP256K1_MODULE = "secp256k1"
            except ImportError:
                return
        pub_key = py23_bytes(repr(PrivateKey(wif).pubkey), "latin")
        signature = ecda.sign_message("Foobar", wif)
        ecda.SECP256K1_MODULE = "ecdsa"
        pub_key_sig = ecda.verify_message("Foobar", signature)
        self.assertEqual(hexlify(pub_key_sig), pub_key)
        signature = ecda.sign_message("Foobar", wif)
        ecda.SECP256K1_MODULE = module
        pub_key_sig = ecda.verify_message("Foobar", signature)
        self.assertEqual(hexlify(pub_key_sig), pub_key)

    @parameterized.expand([
        ("cryptography"),
        ("secp256k1"),
        ("ecdsa"),
    ])
    def test_wrong_signature(self, module):
        if module == "cryptography":
            try:
                from cryptography.hazmat.backends import default_backend
                from cryptography.hazmat.primitives import hashes
                from cryptography.hazmat.primitives.asymmetric import ec
                from cryptography.hazmat.primitives.asymmetric.utils \
                    import decode_dss_signature, encode_dss_signature
                from cryptography.exceptions import InvalidSignature
                ecda.SECP256K1_MODULE = "cryptography"
            except ImportError:
                return
        elif module == "secp256k1":
            try:
                import secp256k1
                ecda.SECP256K1_MODULE = "secp256k1"
            except ImportError:
                return
        pub_key = py23_bytes(repr(PrivateKey(wif).pubkey), "latin")
        ecda.SECP256K1_MODULE = module
        signature = ecda.sign_message("Foobar", wif)
        pub_key_sig = ecda.verify_message("Foobar", signature)
        self.assertEqual(hexlify(pub_key_sig), pub_key)
        pub_key_sig2 = ecda.verify_message("Foobar2", signature)
        self.assertTrue(hexlify(pub_key_sig2) != pub_key)


if __name__ == '__main__':
    unittest.main()
