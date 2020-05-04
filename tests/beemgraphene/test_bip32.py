# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import unittest
import binascii
from binascii import hexlify, unhexlify
from beemgraphenebase.account import Mnemonic
from beemgraphenebase.bip32 import BIP32Key, BIP32_HARDEN, parse_path

words = 'news clever spot drama infant detail sword cover color throw foot primary when slender rhythm clog autumn ecology enough bronze math you modify excuse'


class Testcases(unittest.TestCase):
    def test_btc_privkey(self):
        mobj = Mnemonic()
        mnemonic_words = "aware report movie exile buyer drum poverty supreme gym oppose float elegant"
        seed = mobj.to_seed(mnemonic_words)
    
        bip32_root_key_obj = BIP32Key.fromEntropy(seed)
        bip32_child_key_obj = bip32_root_key_obj.ChildKey(
            44 + BIP32_HARDEN
        ).ChildKey(
            0 + BIP32_HARDEN
        ).ChildKey(
            0 + BIP32_HARDEN
        ).ChildKey(0).ChildKey(0)
        self.assertEqual(bip32_child_key_obj.Address(), '1A9vZ4oPLb29szfRWVFe1VoEe7a2qEMjvJ')
        self.assertEqual(binascii.hexlify(bip32_child_key_obj.PublicKey()).decode(), '029dc2912196f2ad7a830747c2490287e4ff3ea52c417598681a955dcdf473b6c0')
        self.assertEqual(bip32_child_key_obj.WalletImportFormat(), 'L3g3hhYabnBFbGqd7qReebwCrRkGhAzaX4cBpYSv5S667sWJAn5A')

    def test_with_sec(self):
        path = "m/44'/0'/0'/0'/0"
        m = Mnemonic()
        seed = m.to_seed(words)
        key = BIP32Key.fromEntropy(seed)
        self.assertEqual(key.ExtendedKey(), "xprv9s21ZrQH143K3EGRfjQYhZ6fA3HPPiw6rxopHKXfWTrB66evM4fDRiUScJy5RCCGz98nBaCCtwpwFCTDiFG5tx3mdnyyL1MbHmQQ19BWemo")
        m = key
        for n in parse_path(path):
            m = m.ChildKey(n)
        self.assertEqual(m.ExtendedKey(), "xprvA3Fu8ZNFZDn3S24jWzHCLGsX9eSUcpvFY2FFKLzessSEkk1KQLhHpyG7rnfYtx7txBupUY546PT5tjb4kwXghpd1rRw1Xw8nAqS19EZuPSu")
        self.assertEqual(m.ExtendedKey(private=False), "xpub6GFFY4u9PbLLeW9Cd1pChQpFhgGy2He6uFAr7jQGSCyDdYLTwt1YNmabi4aRfHRxwiEEhwu2Bjm3ypHaWHXbmr48QP4Fd8PXcw1o9qpdLSQ")

        m = key.ChildKey(
            44 + BIP32_HARDEN
        ).ChildKey(
            0 + BIP32_HARDEN
        ).ChildKey(
            0 + BIP32_HARDEN
        ).ChildKey(0 + BIP32_HARDEN).ChildKey(0)      
        self.assertEqual(m.ExtendedKey(), "xprvA3Fu8ZNFZDn3S24jWzHCLGsX9eSUcpvFY2FFKLzessSEkk1KQLhHpyG7rnfYtx7txBupUY546PT5tjb4kwXghpd1rRw1Xw8nAqS19EZuPSu")
        self.assertEqual(m.ExtendedKey(private=False), "xpub6GFFY4u9PbLLeW9Cd1pChQpFhgGy2He6uFAr7jQGSCyDdYLTwt1YNmabi4aRfHRxwiEEhwu2Bjm3ypHaWHXbmr48QP4Fd8PXcw1o9qpdLSQ")


    def test_with_pub(self):
        path = "m/0/0/0"
        m = Mnemonic()
        seed = m.to_seed(words)
        key = BIP32Key.fromEntropy(seed)
        m = key
        for n in parse_path(path):
            m = m.ChildKey(n)
        self.assertEqual(m.ExtendedKey(), "xprv9yK7bXqEnmCpHMV4NM7FKj1vsiXQ14h6W8Bn5jkAHHBqrm2CSy82Wpb3FXHaG39v6zt3YCKiqNz4ydx3BNtgvDmU2bxXz1RJ9TXL7N91bTL")
        self.assertEqual(m.ExtendedKey(private=False, encoded=True), "xpub6CJU13N8d8m7VqZXUNeFgrxfRkMtQXQwsM7Nt89mqcipjZMLzWSH4cuX6mWj3XohyuCBRK7cpkAq59XBLRqqjQJGieg2qHaEeRS8dBrGgZu")

        path = "m/0/0/0"
        key2 = BIP32Key.fromExtendedKey(key.ExtendedKey(encoded=True))
        m = key2
        for n in parse_path(path):
            m = m.ChildKey(n)
        self.assertEqual(m.ExtendedKey(), "xprv9yK7bXqEnmCpHMV4NM7FKj1vsiXQ14h6W8Bn5jkAHHBqrm2CSy82Wpb3FXHaG39v6zt3YCKiqNz4ydx3BNtgvDmU2bxXz1RJ9TXL7N91bTL")
        self.assertEqual(m.ExtendedKey(private=False, encoded=True), "xpub6CJU13N8d8m7VqZXUNeFgrxfRkMtQXQwsM7Nt89mqcipjZMLzWSH4cuX6mWj3XohyuCBRK7cpkAq59XBLRqqjQJGieg2qHaEeRS8dBrGgZu")

    def test_vector1(self):
        seed = unhexlify("000102030405060708090a0b0c0d0e0f")
        key = BIP32Key.fromEntropy(seed)     
        self.assertEqual(key.ExtendedKey(), "xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi")
        self.assertEqual(key.ExtendedKey(private=False), "xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8")
        
        path = "m/0'"
        m = key
        for n in parse_path(path):
            m = m.ChildKey(n)
        self.assertEqual(m.ExtendedKey(), "xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7")
        self.assertEqual(m.ExtendedKey(private=False, encoded=True), "xpub68Gmy5EdvgibQVfPdqkBBCHxA5htiqg55crXYuXoQRKfDBFA1WEjWgP6LHhwBZeNK1VTsfTFUHCdrfp1bgwQ9xv5ski8PX9rL2dZXvgGDnw")

        path = "m/0'/1"
        m = key
        for n in parse_path(path):
            m = m.ChildKey(n)
        self.assertEqual(m.ExtendedKey(), "xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H2EU4pWcQDnRnrVA1xe8fs")
        self.assertEqual(m.ExtendedKey(private=False, encoded=True), "xpub6ASuArnXKPbfEwhqN6e3mwBcDTgzisQN1wXN9BJcM47sSikHjJf3UFHKkNAWbWMiGj7Wf5uMash7SyYq527Hqck2AxYysAA7xmALppuCkwQ")
            
        path = "m/0'/1/2'"
        m = key
        for n in parse_path(path):
            m = m.ChildKey(n)
        self.assertEqual(m.ExtendedKey(), "xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjANTtpgP4mLTj34bhnZX7UiM")
        self.assertEqual(m.ExtendedKey(private=False, encoded=True), "xpub6D4BDPcP2GT577Vvch3R8wDkScZWzQzMMUm3PWbmWvVJrZwQY4VUNgqFJPMM3No2dFDFGTsxxpG5uJh7n7epu4trkrX7x7DogT5Uv6fcLW5")

        path = "m/0'/1/2'/2"
        m = key
        for n in parse_path(path):
            m = m.ChildKey(n)
        self.assertEqual(m.ExtendedKey(), "xprvA2JDeKCSNNZky6uBCviVfJSKyQ1mDYahRjijr5idH2WwLsEd4Hsb2Tyh8RfQMuPh7f7RtyzTtdrbdqqsunu5Mm3wDvUAKRHSC34sJ7in334")
        self.assertEqual(m.ExtendedKey(private=False, encoded=True), "xpub6FHa3pjLCk84BayeJxFW2SP4XRrFd1JYnxeLeU8EqN3vDfZmbqBqaGJAyiLjTAwm6ZLRQUMv1ZACTj37sR62cfN7fe5JnJ7dh8zL4fiyLHV")

        path = "m/0'/1/2'/2/1000000000"
        m = key
        for n in parse_path(path):
            m = m.ChildKey(n)
        self.assertEqual(m.ExtendedKey(), "xprvA41z7zogVVwxVSgdKUHDy1SKmdb533PjDz7J6N6mV6uS3ze1ai8FHa8kmHScGpWmj4WggLyQjgPie1rFSruoUihUZREPSL39UNdE3BBDu76")
        self.assertEqual(m.ExtendedKey(private=False, encoded=True), "xpub6H1LXWLaKsWFhvm6RVpEL9P4KfRZSW7abD2ttkWP3SSQvnyA8FSVqNTEcYFgJS2UaFcxupHiYkro49S8yGasTvXEYBVPamhGW6cFJodrTHy")


if __name__ == '__main__':
    unittest.main()
