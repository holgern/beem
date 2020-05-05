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

    def test_vector2(self):
        seed = unhexlify("fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542")
        key = BIP32Key.fromEntropy(seed)     
        self.assertEqual(key.ExtendedKey(), "xprv9s21ZrQH143K31xYSDQpPDxsXRTUcvj2iNHm5NUtrGiGG5e2DtALGdso3pGz6ssrdK4PFmM8NSpSBHNqPqm55Qn3LqFtT2emdEXVYsCzC2U")
        self.assertEqual(key.ExtendedKey(private=False), "xpub661MyMwAqRbcFW31YEwpkMuc5THy2PSt5bDMsktWQcFF8syAmRUapSCGu8ED9W6oDMSgv6Zz8idoc4a6mr8BDzTJY47LJhkJ8UB7WEGuduB")
        
        path = "m/0"
        m = key
        for n in parse_path(path):
            m = m.ChildKey(n)
        self.assertEqual(m.ExtendedKey(), "xprv9vHkqa6EV4sPZHYqZznhT2NPtPCjKuDKGY38FBWLvgaDx45zo9WQRUT3dKYnjwih2yJD9mkrocEZXo1ex8G81dwSM1fwqWpWkeS3v86pgKt")
        self.assertEqual(m.ExtendedKey(private=False, encoded=True), "xpub69H7F5d8KSRgmmdJg2KhpAK8SR3DjMwAdkxj3ZuxV27CprR9LgpeyGmXUbC6wb7ERfvrnKZjXoUmmDznezpbZb7ap6r1D3tgFxHmwMkQTPH")

        path = "m/0/2147483647'"
        m = key
        for n in parse_path(path):
            m = m.ChildKey(n)
        self.assertEqual(m.ExtendedKey(), "xprv9wSp6B7kry3Vj9m1zSnLvN3xH8RdsPP1Mh7fAaR7aRLcQMKTR2vidYEeEg2mUCTAwCd6vnxVrcjfy2kRgVsFawNzmjuHc2YmYRmagcEPdU9")
        self.assertEqual(m.ExtendedKey(private=False, encoded=True), "xpub6ASAVgeehLbnwdqV6UKMHVzgqAG8Gr6riv3Fxxpj8ksbH9ebxaEyBLZ85ySDhKiLDBrQSARLq1uNRts8RuJiHjaDMBU4Zn9h8LZNnBC5y4a")
        path = "m/0/2147483647'/1"
        m = key
        for n in parse_path(path):
            m = m.ChildKey(n)
        self.assertEqual(m.ExtendedKey(), "xprv9zFnWC6h2cLgpmSA46vutJzBcfJ8yaJGg8cX1e5StJh45BBciYTRXSd25UEPVuesF9yog62tGAQtHjXajPPdbRCHuWS6T8XA2ECKADdw4Ef")
        self.assertEqual(m.ExtendedKey(private=False, encoded=True), "xpub6DF8uhdarytz3FWdA8TvFSvvAh8dP3283MY7p2V4SeE2wyWmG5mg5EwVvmdMVCQcoNJxGoWaU9DCWh89LojfZ537wTfunKau47EL2dhHKon")
        path = "m/0/2147483647'/1/2147483646'"
        m = key
        for n in parse_path(path):
            m = m.ChildKey(n)
        self.assertEqual(m.ExtendedKey(), "xprvA1RpRA33e1JQ7ifknakTFpgNXPmW2YvmhqLQYMmrj4xJXXWYpDPS3xz7iAxn8L39njGVyuoseXzU6rcxFLJ8HFsTjSyQbLYnMpCqE2VbFWc")
        self.assertEqual(m.ExtendedKey(private=False, encoded=True), "xpub6ERApfZwUNrhLCkDtcHTcxd75RbzS1ed54G1LkBUHQVHQKqhMkhgbmJbZRkrgZw4koxb5JaHWkY4ALHY2grBGRjaDMzQLcgJvLJuZZvRcEL")
        path = "m/0/2147483647'/1/2147483646'/2"
        m = key
        for n in parse_path(path):
            m = m.ChildKey(n)
        self.assertEqual(m.ExtendedKey(), "xprvA2nrNbFZABcdryreWet9Ea4LvTJcGsqrMzxHx98MMrotbir7yrKCEXw7nadnHM8Dq38EGfSh6dqA9QWTyefMLEcBYJUuekgW4BYPJcr9E7j")
        self.assertEqual(m.ExtendedKey(private=False, encoded=True), "xpub6FnCn6nSzZAw5Tw7cgR9bi15UV96gLZhjDstkXXxvCLsUXBGXPdSnLFbdpq8p9HmGsApME5hQTZ3emM2rnY5agb9rXpVGyy3bdW6EEgAtqt")

    def test_vector3(self):
        seed = unhexlify("4b381541583be4423346c643850da4b320e46a87ae3d2a4e6da11eba819cd4acba45d239319ac14f863b8d5ab5a0d0c64d2e8a1e7d1457df2e5a3c51c73235be")
        key = BIP32Key.fromEntropy(seed)     
        self.assertEqual(key.ExtendedKey(), "xprv9s21ZrQH143K25QhxbucbDDuQ4naNntJRi4KUfWT7xo4EKsHt2QJDu7KXp1A3u7Bi1j8ph3EGsZ9Xvz9dGuVrtHHs7pXeTzjuxBrCmmhgC6")
        self.assertEqual(key.ExtendedKey(private=False), "xpub661MyMwAqRbcEZVB4dScxMAdx6d4nFc9nvyvH3v4gJL378CSRZiYmhRoP7mBy6gSPSCYk6SzXPTf3ND1cZAceL7SfJ1Z3GC8vBgp2epUt13")
        
        path = "m/0'"
        m = key
        for n in parse_path(path):
            m = m.ChildKey(n)
        self.assertEqual(m.ExtendedKey(), "xprv9uPDJpEQgRQfDcW7BkF7eTya6RPxXeJCqCJGHuCJ4GiRVLzkTXBAJMu2qaMWPrS7AANYqdq6vcBcBUdJCVVFceUvJFjaPdGZ2y9WACViL4L")
        self.assertEqual(m.ExtendedKey(private=False, encoded=True), "xpub68NZiKmJWnxxS6aaHmn81bvJeTESw724CRDs6HbuccFQN9Ku14VQrADWgqbhhTHBaohPX4CjNLf9fq9MYo6oDaPPLPxSb7gwQN3ih19Zm4Y")

if __name__ == '__main__':
    unittest.main()
