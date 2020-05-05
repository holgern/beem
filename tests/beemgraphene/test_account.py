# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import unittest
from beemgraphenebase.base58 import Base58, base58encode
from beemgraphenebase.bip32 import BIP32Key
from beemgraphenebase.account import BrainKey, Address, PublicKey, PrivateKey, PasswordKey, Mnemonic, MnemonicKey
from binascii import hexlify, unhexlify
import sys
import hashlib
import random


class Testcases(unittest.TestCase):
    def test_B85hexgetb58_btc(self):
        self.assertEqual(["5HqUkGuo62BfcJU5vNhTXKJRXuUi9QSE6jp8C3uBJ2BVHtB8WSd",
                          "5JWcdkhL3w4RkVPcZMdJsjos22yB5cSkPExerktvKnRNZR5gx1S",
                          "5HvVz6XMx84aC5KaaBbwYrRLvWE46cH6zVnv4827SBPLorg76oq",
                          "5Jete5oFNjjk3aUMkKuxgAXsp7ZyhgJbYNiNjHLvq5xzXkiqw7R",
                          "5KDT58ksNsVKjYShG4Ls5ZtredybSxzmKec8juj7CojZj6LPRF7",
                          "02b52e04a0acfe611a4b6963462aca94b6ae02b24e321eda86507661901adb49",
                          "5b921f7051be5e13e177a0253229903c40493df410ae04f4a450c85568f19131",
                          "0e1bfc9024d1f55a7855dc690e45b2e089d2d825a4671a3c3c7e4ea4e74ec00e",
                          "6e5cc4653d46e690c709ed9e0570a2c75a286ad7c1bc69a648aae6855d919d3e",
                          ],
                         [format(Base58("02b52e04a0acfe611a4b6963462aca94b6ae02b24e321eda86507661901adb49"), "WIF"),
                          format(Base58("5b921f7051be5e13e177a0253229903c40493df410ae04f4a450c85568f19131"), "WIF"),
                          format(Base58("0e1bfc9024d1f55a7855dc690e45b2e089d2d825a4671a3c3c7e4ea4e74ec00e"), "WIF"),
                          format(Base58("6e5cc4653d46e690c709ed9e0570a2c75a286ad7c1bc69a648aae6855d919d3e"), "WIF"),
                          format(Base58("b84abd64d66ee1dd614230ebbe9d9c6d66d78d93927c395196666762e9ad69d8"), "WIF"),
                          repr(Base58("5HqUkGuo62BfcJU5vNhTXKJRXuUi9QSE6jp8C3uBJ2BVHtB8WSd")),
                          repr(Base58("5JWcdkhL3w4RkVPcZMdJsjos22yB5cSkPExerktvKnRNZR5gx1S")),
                          repr(Base58("5HvVz6XMx84aC5KaaBbwYrRLvWE46cH6zVnv4827SBPLorg76oq")),
                          repr(Base58("5Jete5oFNjjk3aUMkKuxgAXsp7ZyhgJbYNiNjHLvq5xzXkiqw7R")),
                          ])

    def test_B85hexgetb58(self):
        self.assertEqual(['BTS2CAbTi1ZcgMJ5otBFZSGZJKJenwGa9NvkLxsrS49Kr8JsiSGc',
                          'BTShL45FEyUVSVV1LXABQnh4joS9FsUaffRtsdarB5uZjPsrwMZF',
                          'BTS7DQR5GsfVaw4wJXzA3TogDhuQ8tUR2Ggj8pwyNCJXheHehL4Q',
                          'BTSqc4QMAJHAkna65i8U4b7nkbWk4VYSWpZebW7JBbD7MN8FB5sc',
                          'BTS2QAVTJnJQvLUY4RDrtxzX9jS39gEq8gbqYMWjgMxvsvZTJxDSu'
                          ],
                         [format(Base58("02b52e04a0acfe611a4b6963462aca94b6ae02b24e321eda86507661901adb49"), "BTS"),
                          format(Base58("5b921f7051be5e13e177a0253229903c40493df410ae04f4a450c85568f19131"), "BTS"),
                          format(Base58("0e1bfc9024d1f55a7855dc690e45b2e089d2d825a4671a3c3c7e4ea4e74ec00e"), "BTS"),
                          format(Base58("6e5cc4653d46e690c709ed9e0570a2c75a286ad7c1bc69a648aae6855d919d3e"), "BTS"),
                          format(Base58("b84abd64d66ee1dd614230ebbe9d9c6d66d78d93927c395196666762e9ad69d8"), "BTS")])

    def test_Address(self):
        self.assertEqual([format(Address("BTSFN9r6VYzBK8EKtMewfNbfiGCr56pHDBFi", prefix="BTS"), "BTS"),
                          format(Address("BTSdXrrTXimLb6TEt3nHnePwFmBT6Cck112", prefix="BTS"), "BTS"),
                          format(Address("BTSJQUAt4gz4civ8gSs5srTK4r82F7HvpChk", prefix="BTS"), "BTS"),
                          format(Address("BTSFPXXHXXGbyTBwdKoJaAPXRnhFNtTRS4EL", prefix="BTS"), "BTS"),
                          format(Address("BTS3qXyZnjJneeAddgNDYNYXbF7ARZrRv5dr", prefix="BTS"), "BTS"),
                          ],
                         ["BTSFN9r6VYzBK8EKtMewfNbfiGCr56pHDBFi",
                          "BTSdXrrTXimLb6TEt3nHnePwFmBT6Cck112",
                          "BTSJQUAt4gz4civ8gSs5srTK4r82F7HvpChk",
                          "BTSFPXXHXXGbyTBwdKoJaAPXRnhFNtTRS4EL",
                          "BTS3qXyZnjJneeAddgNDYNYXbF7ARZrRv5dr",
                          ])

    def test_PubKey(self):
        self.assertEqual([format(PublicKey("BTS6UtYWWs3rkZGV8JA86qrgkG6tyFksgECefKE1MiH4HkLD8PFGL", prefix="BTS").address, "BTS"),
                          format(PublicKey("BTS8YAMLtNcnqGNd3fx28NP3WoyuqNtzxXpwXTkZjbfe9scBmSyGT", prefix="BTS").address, "BTS"),
                          format(PublicKey("BTS7HUo6bm7Gfoi3RqAtzwZ83BFCwiCZ4tp37oZjtWxGEBJVzVVGw", prefix="BTS").address, "BTS"),
                          format(PublicKey("BTS6676cZ9qmqPnWMrm4McjCuHcnt6QW5d8oRJ4t8EDH8DdCjvh4V", prefix="BTS").address, "BTS"),
                          format(PublicKey("BTS7u8m6zUNuzPNK1tPPLtnipxgqV9mVmTzrFNJ9GvovvSTCkVUra", prefix="BTS").address, "BTS")
                          ],
                         ["BTS66FCjYKzMwLbE3a59YpmFqA9bwporT4L3",
                          "BTSKNpRuPX8KhTBsJoFp1JXd7eQEsnCpRw3k",
                          "BTS838ENJargbUrxXWuE2xD9HKjQaS17GdCd",
                          "BTSNsrLFWTziSZASnNJjWafFtGBfSu8VG8KU",
                          "BTSDjAGuXzk3WXabBEgKKc8NsuQM412boBdR"
                          ])

    def test_btsprivkey(self):
        self.assertEqual([format(PrivateKey("5HqUkGuo62BfcJU5vNhTXKJRXuUi9QSE6jp8C3uBJ2BVHtB8WSd").address, "BTS"),
                          format(PrivateKey("5JWcdkhL3w4RkVPcZMdJsjos22yB5cSkPExerktvKnRNZR5gx1S").address, "BTS"),
                          format(PrivateKey("5HvVz6XMx84aC5KaaBbwYrRLvWE46cH6zVnv4827SBPLorg76oq").address, "BTS"),
                          format(PrivateKey("5Jete5oFNjjk3aUMkKuxgAXsp7ZyhgJbYNiNjHLvq5xzXkiqw7R").address, "BTS"),
                          format(PrivateKey("5KDT58ksNsVKjYShG4Ls5ZtredybSxzmKec8juj7CojZj6LPRF7").address, "BTS")
                          ],
                         ["BTSFN9r6VYzBK8EKtMewfNbfiGCr56pHDBFi",
                          "BTSdXrrTXimLb6TEt3nHnePwFmBT6Cck112",
                          "BTSJQUAt4gz4civ8gSs5srTK4r82F7HvpChk",
                          "BTSFPXXHXXGbyTBwdKoJaAPXRnhFNtTRS4EL",
                          "BTS3qXyZnjJneeAddgNDYNYXbF7ARZrRv5dr",
                          ])

    def test_btcprivkey(self):
        self.assertEqual([format(PrivateKey("5HvVz6XMx84aC5KaaBbwYrRLvWE46cH6zVnv4827SBPLorg76oq").uncompressed.address, "BTC"),
                          format(PrivateKey("5Jete5oFNjjk3aUMkKuxgAXsp7ZyhgJbYNiNjHLvq5xzXkiqw7R").uncompressed.address, "BTC"),
                          format(PrivateKey("5KDT58ksNsVKjYShG4Ls5ZtredybSxzmKec8juj7CojZj6LPRF7").uncompressed.address, "BTC"),
                          ],
                         ["1G7qw8FiVfHEFrSt3tDi6YgfAdrDrEM44Z",
                          "12c7KAAZfpREaQZuvjC5EhpoN6si9vekqK",
                          "1Gu5191CVHmaoU3Zz3prept87jjnpFDrXL",
                          ])

    def test_PublicKey(self):
        self.assertEqual([str(PublicKey("BTS6UtYWWs3rkZGV8JA86qrgkG6tyFksgECefKE1MiH4HkLD8PFGL", prefix="BTS")),
                          str(PublicKey("BTS8YAMLtNcnqGNd3fx28NP3WoyuqNtzxXpwXTkZjbfe9scBmSyGT", prefix="BTS")),
                          str(PublicKey("BTS7HUo6bm7Gfoi3RqAtzwZ83BFCwiCZ4tp37oZjtWxGEBJVzVVGw", prefix="BTS")),
                          str(PublicKey("BTS6676cZ9qmqPnWMrm4McjCuHcnt6QW5d8oRJ4t8EDH8DdCjvh4V", prefix="BTS")),
                          str(PublicKey("BTS7u8m6zUNuzPNK1tPPLtnipxgqV9mVmTzrFNJ9GvovvSTCkVUra", prefix="BTS"))
                          ],
                         ["BTS6UtYWWs3rkZGV8JA86qrgkG6tyFksgECefKE1MiH4HkLD8PFGL",
                          "BTS8YAMLtNcnqGNd3fx28NP3WoyuqNtzxXpwXTkZjbfe9scBmSyGT",
                          "BTS7HUo6bm7Gfoi3RqAtzwZ83BFCwiCZ4tp37oZjtWxGEBJVzVVGw",
                          "BTS6676cZ9qmqPnWMrm4McjCuHcnt6QW5d8oRJ4t8EDH8DdCjvh4V",
                          "BTS7u8m6zUNuzPNK1tPPLtnipxgqV9mVmTzrFNJ9GvovvSTCkVUra"
                          ])

    def test_Privatekey(self):
        self.assertEqual([str(PrivateKey("5HvVz6XMx84aC5KaaBbwYrRLvWE46cH6zVnv4827SBPLorg76oq")),
                          str(PrivateKey("5Jete5oFNjjk3aUMkKuxgAXsp7ZyhgJbYNiNjHLvq5xzXkiqw7R")),
                          str(PrivateKey("5KDT58ksNsVKjYShG4Ls5ZtredybSxzmKec8juj7CojZj6LPRF7")),
                          repr(PrivateKey("5HvVz6XMx84aC5KaaBbwYrRLvWE46cH6zVnv4827SBPLorg76oq")),
                          repr(PrivateKey("5Jete5oFNjjk3aUMkKuxgAXsp7ZyhgJbYNiNjHLvq5xzXkiqw7R")),
                          repr(PrivateKey("5KDT58ksNsVKjYShG4Ls5ZtredybSxzmKec8juj7CojZj6LPRF7")),
                          ],
                         ["5HvVz6XMx84aC5KaaBbwYrRLvWE46cH6zVnv4827SBPLorg76oq",
                          "5Jete5oFNjjk3aUMkKuxgAXsp7ZyhgJbYNiNjHLvq5xzXkiqw7R",
                          "5KDT58ksNsVKjYShG4Ls5ZtredybSxzmKec8juj7CojZj6LPRF7",
                          '0e1bfc9024d1f55a7855dc690e45b2e089d2d825a4671a3c3c7e4ea4e74ec00e',
                          '6e5cc4653d46e690c709ed9e0570a2c75a286ad7c1bc69a648aae6855d919d3e',
                          'b84abd64d66ee1dd614230ebbe9d9c6d66d78d93927c395196666762e9ad69d8'
                          ])

    def test_BrainKey(self):
        self.assertEqual([str(BrainKey("COLORER BICORN KASBEKE FAERIE LOCHIA GOMUTI SOVKHOZ Y GERMAL AUNTIE PERFUMY TIME FEATURE GANGAN CELEMIN MATZO").get_private()),
                          str(BrainKey("NAK TILTING MOOTING TAVERT SCREENY MAGIC BARDIE UPBORNE CONOID MAUVE CARBON NOTAEUM BITUMEN HOOEY KURUMA COWFISH").get_private()),
                          str(BrainKey("CORKITE CORDAGE FONDISH UNDER FORGET BEFLEA OUTBUD ZOOGAMY BERLINE ACANTHA STYLO YINCE TROPISM TUNKET FALCULA TOMENT").get_private()),
                          str(BrainKey("MURZA PREDRAW FIT LARIGOT CRYOGEN SEVENTH LISP UNTAWED AMBER CRETIN KOVIL TEATED OUTGRIN POTTAGY KLAFTER DABB").get_private()),
                          str(BrainKey("VERDICT REPOUR SUNRAY WAMBLY UNFILM UNCOUS COWMAN REBUOY MIURUS KEACORN BENZOLE BEMAUL SAXTIE DOLENT CHABUK BOUGHED").get_private()),
                          str(BrainKey("HOUGH TRUMPH SUCKEN EXODY MAMMATE PIGGIN CRIME TEPEE URETHAN TOLUATE BLINDLY CACOEPY SPINOSE COMMIE GRIECE FUNDAL").get_private()),
                          str(BrainKey("OERSTED ETHERIN TESTIS PEGGLE ONCOST POMME SUBAH FLOODER OLIGIST ACCUSE UNPLAT OATLIKE DEWTRY CYCLIZE PIMLICO CHICOT").get_private()),
                          ],
                         ["5JfwDztjHYDDdKnCpjY6cwUQfM4hbtYmSJLjGd9KTpk9J4H2jDZ",
                          "5JcdQEQjBS92rKqwzQnpBndqieKAMQSiXLhU7SFZoCja5c1JyKM",
                          "5JsmdqfNXegnM1eA8HyL6uimHp6pS9ba4kwoiWjjvqFC1fY5AeV",
                          "5J2KeFptc73WTZPoT1Sd59prFep6SobGobCYm7T5ZnBKtuW9RL9",
                          "5HryThsy6ySbkaiGK12r8kQ21vNdH81T5iifFEZNTe59wfPFvU9",
                          "5Ji4N7LSSv3MAVkM3Gw2kq8GT5uxZYNaZ3d3y2C4Ex1m7vshjBN",
                          "5HqSHfckRKmZLqqWW7p2iU18BYvyjxQs2sksRWhXMWXsNEtxPZU",
                          ])

    def test_BrainKey_normalize(self):
        b = "COLORER BICORN KASBEKE FAERIE LOCHIA GOMUTI SOVKHOZ Y GERMAL AUNTIE PERFUMY TIME FEATURE GANGAN CELEMIN MATZO"
        self.assertEqual([BrainKey(b + "").get_brainkey(),
                          BrainKey(b + " ").get_brainkey(),
                          BrainKey(b + "  ").get_brainkey(),
                          BrainKey(b + "\t").get_brainkey(),
                          BrainKey(b + "\t\t").get_brainkey(),
                          BrainKey(b.replace(" ", "\t")).get_brainkey(),
                          BrainKey(b.replace(" ", "  ")).get_brainkey(),
                          ],
                         [b, b, b, b, b, b, b])

    def test_BrainKey_suggest(self):
        b = BrainKey()
        self.assertTrue(len(b.suggest()) > 0)

    def test_BrainKey_sequences(self):
        b = BrainKey("COLORER BICORN KASBEKE FAERIE LOCHIA GOMUTI SOVKHOZ Y GERMAL AUNTIE PERFUMY TIME FEATURE GANGAN CELEMIN MATZO")
        keys = ["5Hsbn6kXio4bb7eW5bX7kTp2sdkmbzP8kGWoau46Cf7en7T1RRE",
                "5K9MHEyiSye5iFL2srZu3ZVjzAZjcQxUgUvuttcVrymovFbU4cc",
                "5JBXhzDWQdYPAzRxxuGtzqM7ULLKPK7GZmktHTyF9foGGfbtDLT",
                "5Kbbfbs6DmJFNddWiP1XZfDKwhm5dkn9KX5AENQfQke2RYBBDcz",
                "5JUqLwgxn8f7myNz4gDwo5e77HZgopHMDHv4icNVww9Rxu1GDG5",
                "5JNBVj5QVh86N8MUUwY3EVUmsZwChZftxnuJx22DzEtHWC4rmvK",
                "5JdvczYtxPPjQdXMki1tpNvuSbvPMxJG5y4ndEAuQsC5RYMQXuC",
                "5HsUSesU2YB4EA3dmpGtHh8aPAwEdkdhidG8hcU2Nd2tETKk85t",
                "5JpveiQd1mt91APyQwvsCdAXWJ7uag3JmhtSxpGienic8vv1k2W",
                "5KDGhQUqQmwcGQ9tegimSyyT4vmH8h2fMzoNe1MT9bEGvRvR6kD"]
        for i in keys:
            p = b.next_sequence().get_private()
            self.assertEqual(str(p), i)

    def test_PasswordKey(self):
        a = ["Aang7foN3oz1Ungai2qua5toh3map8ladei1eem2ohsh2shuo8aeji9Thoseo7ah",
             "iep1Mees9eghiifahwei5iidi0Sazae9aigaeT7itho3quoo2dah5zuvobaelau5",
             "ohBeuyoothae5aer9odaegh5Eeloh1fi7obei9ahSh0haeYuas1sheehaiv5LaiX",
             "geiQuoo9NeeLoaZee0ain3Ku1biedohsesien4uHo1eib1ahzaesh5shae3iena7",
             "jahzeice6Ix8ohBo3eik9pohjahgeegoh9sahthai1aeMahs8ki7Iub1oojeeSuo",
             "eiVahHoh2hi4fazah9Tha8loxeeNgequaquuYee6Shoopo3EiWoosheeX6yohg2o",
             "PheeCh3ar8xoofoiphoo4aisahjiiPah4vah0eeceiJ2iyeem9wahyupeithah9T",
             "IuyiibahNgieshei2eeFu8aic1IeMae9ooXi9jaiwaht4Wiengieghahnguang0U",
             "Ipee1quee7sheughemae4eir8pheix3quac3ei0Aquo9ohieLaeseeh8AhGeM2ew",
             "Tech5iir0aP6waiMeiHoph3iwoch4iijoogh0zoh9aSh6Ueb2Dee5dang1aa8IiP"
             ]
        b = ["STM5NyCrrXHmdikC6QPRAPoDjSHVQJe3WC5bMZuF6YhqhSsfYfjhN",
             "STM8gyvJtYyv5ZbT2ZxbAtgufQ5ovV2bq6EQp4YDTzQuSwyg7Ckry",
             "STM7yE71iVPSpaq8Ae2AmsKfyFxA8pwYv5zgQtCnX7xMwRUQMVoGf",
             "STM5jRgWA2kswPaXsQNtD2MMjs92XfJ1TYob6tjHtsECg2AusF5Wo",
             "STM6XHwVxcP6zP5NV1jUbG6Kso9m8ZG9g2CjDiPcZpAxHngx6ATPB",
             "STM59X1S4ofTAeHd1iNHDGxim5GkLo2AdcznksUsSYGU687ywB5WV",
             "STM6BPPL4iSRbFVVN8v3BEEEyDsC1STRK7Ba9ewQ4Lqvszn5J8VAe",
             "STM7cdK927wj95ptUrCk6HKWVeF74LG5cTjDTV22Z3yJ4Xw8xc9qp",
             "STM7VNFRjrE1hs1CKpEAP9NAabdFpwvzYXRKvkrVBBv2kTQCbNHz7",
             "STM7ZZFhEBjujcKjkmY31i1spPMx6xDSRhkursZLigi2HKLuALe5t",
             ]
        for i, pwd in enumerate(a):
            p = format(PasswordKey("xeroc", pwd, "posting").get_public(), "STM")
            self.assertEqual(p, b[i])

    def test_Privatekey_pubkey(self):
        self.assertEqual([format(PrivateKey("5HvVz6XMx84aC5KaaBbwYrRLvWE46cH6zVnv4827SBPLorg76oq").pubkey, "STX"),
                          str(PrivateKey("5HvVz6XMx84aC5KaaBbwYrRLvWE46cH6zVnv4827SBPLorg76oq", prefix="STX").pubkey)],
                         ["STX7W5qsanXHgRAZPijbrLMDwX6VmHqUdL2s8PZiYKD5h1R7JaqRJ",
                          "STX7W5qsanXHgRAZPijbrLMDwX6VmHqUdL2s8PZiYKD5h1R7JaqRJ"])

    def test_Privatekey_derive(self):
        p1 = PrivateKey("5HvVz6XMx84aC5KaaBbwYrRLvWE46cH6zVnv4827SBPLorg76oq")
        p2 = PrivateKey("5Jete5oFNjjk3aUMkKuxgAXsp7ZyhgJbYNiNjHLvq5xzXkiqw7R")
        self.assertEqual([format(p1.child(p2.get_secret()), "STM"),
                          format(p2.child(p1.get_secret()), "STM"),
                          format(p1.derive_private_key(0), "STM"),
                          format(p2.derive_private_key(56), "STM")],
                         ["STMZiwJpC7MUmc9gn3vii3XS36nUceYEfKvFC1NLSrjB7ZRQJ7gt",
                          "STM24hzNSDZYgm9C85yxJqyk32DwjXg8pCgkGVzB77hvP2XxGDdvr",
                          "STM2e99iqVQUFij7Dk2nWVNC1dL8M86q37Nj4KwPHKBu1Yy49HkwA",
                          "STMgqaH9RdvUtVk7NFnx4BZJRrNS7Lj35qaueAeYJ3tKEqPaLwa4"])

    def test_utf8_nfkd(self):
        # The same sentence in various UTF-8 forms
        words_nfkd = u"Pr\u030ci\u0301s\u030cerne\u030c z\u030clut\u030couc\u030cky\u0301 ku\u030an\u030c u\u0301pe\u030cl d\u030ca\u0301belske\u0301 o\u0301dy za\u0301ker\u030cny\u0301 uc\u030cen\u030c be\u030cz\u030ci\u0301 pode\u0301l zo\u0301ny u\u0301lu\u030a"
        words_nfc = u"P\u0159\xed\u0161ern\u011b \u017elu\u0165ou\u010dk\xfd k\u016f\u0148 \xfap\u011bl \u010f\xe1belsk\xe9 \xf3dy z\xe1ke\u0159n\xfd u\u010de\u0148 b\u011b\u017e\xed pod\xe9l z\xf3ny \xfal\u016f"
        words_nfkc = u"P\u0159\xed\u0161ern\u011b \u017elu\u0165ou\u010dk\xfd k\u016f\u0148 \xfap\u011bl \u010f\xe1belsk\xe9 \xf3dy z\xe1ke\u0159n\xfd u\u010de\u0148 b\u011b\u017e\xed pod\xe9l z\xf3ny \xfal\u016f"
        words_nfd = u"Pr\u030ci\u0301s\u030cerne\u030c z\u030clut\u030couc\u030cky\u0301 ku\u030an\u030c u\u0301pe\u030cl d\u030ca\u0301belske\u0301 o\u0301dy za\u0301ker\u030cny\u0301 uc\u030cen\u030c be\u030cz\u030ci\u0301 pode\u0301l zo\u0301ny u\u0301lu\u030a"

        passphrase_nfkd = (
            u"Neuve\u030cr\u030citelne\u030c bezpec\u030cne\u0301 hesli\u0301c\u030cko"
        )
        passphrase_nfc = (
            u"Neuv\u011b\u0159iteln\u011b bezpe\u010dn\xe9 hesl\xed\u010dko"
        )
        passphrase_nfkc = (
            u"Neuv\u011b\u0159iteln\u011b bezpe\u010dn\xe9 hesl\xed\u010dko"
        )
        passphrase_nfd = (
            u"Neuve\u030cr\u030citelne\u030c bezpec\u030cne\u0301 hesli\u0301c\u030cko"
        )

        seed_nfkd = Mnemonic.to_seed(words_nfkd, passphrase_nfkd)
        seed_nfc = Mnemonic.to_seed(words_nfc, passphrase_nfc)
        seed_nfkc = Mnemonic.to_seed(words_nfkc, passphrase_nfkc)
        seed_nfd = Mnemonic.to_seed(words_nfd, passphrase_nfd)

        self.assertEqual(seed_nfkd, seed_nfc)
        self.assertEqual(seed_nfkd, seed_nfkc)
        self.assertEqual(seed_nfkd, seed_nfd)

    def test_expand(self):
        m = Mnemonic()
        self.assertEqual("access", m.expand("access"))
        self.assertEqual(
            "access access acb acc act action", m.expand("access acce acb acc act acti")
        )

    def test_expand_word(self):
        m = Mnemonic()
        self.assertEqual("", m.expand_word(""))
        self.assertEqual(" ", m.expand_word(" "))
        self.assertEqual("access", m.expand_word("access"))  # word in list
        self.assertEqual(
            "access", m.expand_word("acce")
        )  # unique prefix expanded to word in list
        self.assertEqual("acb", m.expand_word("acb"))  # not found at all
        self.assertEqual("acc", m.expand_word("acc"))  # multi-prefix match
        self.assertEqual("act", m.expand_word("act"))  # exact three letter match
        self.assertEqual(
            "action", m.expand_word("acti")
        )  # unique prefix expanded to word in list

    def test_failed_checksum(self):
        code = (
            "bless cloud wheel regular tiny venue bird web grief security dignity zoo"
        )
        mnemo = Mnemonic()
        self.assertFalse(mnemo.check(code))

    def test_mnemonic(self):
        v = [[
            "00000000000000000000000000000000",
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
            "c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e53495531f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04",
            "xprv9s21ZrQH143K3h3fDYiay8mocZ3afhfULfb5GX8kCBdno77K4HiA15Tg23wpbeF1pLfs1c5SPmYHrEpTuuRhxMwvKDwqdKiGJS9XFKzUsAF"
        ],
        [
            "7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f",
            "legal winner thank year wave sausage worth useful legal winner thank yellow",
            "2e8905819b8723fe2c1d161860e5ee1830318dbf49a83bd451cfb8440c28bd6fa457fe1296106559a3c80937a1c1069be3a3a5bd381ee6260e8d9739fce1f607",
            "xprv9s21ZrQH143K2gA81bYFHqU68xz1cX2APaSq5tt6MFSLeXnCKV1RVUJt9FWNTbrrryem4ZckN8k4Ls1H6nwdvDTvnV7zEXs2HgPezuVccsq"
        ],
        [
            "80808080808080808080808080808080",
            "letter advice cage absurd amount doctor acoustic avoid letter advice cage above",
            "d71de856f81a8acc65e6fc851a38d4d7ec216fd0796d0a6827a3ad6ed5511a30fa280f12eb2e47ed2ac03b5c462a0358d18d69fe4f985ec81778c1b370b652a8",
            "xprv9s21ZrQH143K2shfP28KM3nr5Ap1SXjz8gc2rAqqMEynmjt6o1qboCDpxckqXavCwdnYds6yBHZGKHv7ef2eTXy461PXUjBFQg6PrwY4Gzq"
        ],
        [
            "ffffffffffffffffffffffffffffffff",
            "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong",
            "ac27495480225222079d7be181583751e86f571027b0497b5b5d11218e0a8a13332572917f0f8e5a589620c6f15b11c61dee327651a14c34e18231052e48c069",
            "xprv9s21ZrQH143K2V4oox4M8Zmhi2Fjx5XK4Lf7GKRvPSgydU3mjZuKGCTg7UPiBUD7ydVPvSLtg9hjp7MQTYsW67rZHAXeccqYqrsx8LcXnyd"
        ],
        [
            "000000000000000000000000000000000000000000000000",
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon agent",
            "035895f2f481b1b0f01fcf8c289c794660b289981a78f8106447707fdd9666ca06da5a9a565181599b79f53b844d8a71dd9f439c52a3d7b3e8a79c906ac845fa",
            "xprv9s21ZrQH143K3mEDrypcZ2usWqFgzKB6jBBx9B6GfC7fu26X6hPRzVjzkqkPvDqp6g5eypdk6cyhGnBngbjeHTe4LsuLG1cCmKJka5SMkmU"
        ],
        [
            "7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f",
            "legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal will",
            "f2b94508732bcbacbcc020faefecfc89feafa6649a5491b8c952cede496c214a0c7b3c392d168748f2d4a612bada0753b52a1c7ac53c1e93abd5c6320b9e95dd",
            "xprv9s21ZrQH143K3Lv9MZLj16np5GzLe7tDKQfVusBni7toqJGcnKRtHSxUwbKUyUWiwpK55g1DUSsw76TF1T93VT4gz4wt5RM23pkaQLnvBh7"
        ],
        [
            "808080808080808080808080808080808080808080808080",
            "letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter always",
            "107d7c02a5aa6f38c58083ff74f04c607c2d2c0ecc55501dadd72d025b751bc27fe913ffb796f841c49b1d33b610cf0e91d3aa239027f5e99fe4ce9e5088cd65",
            "xprv9s21ZrQH143K3VPCbxbUtpkh9pRG371UCLDz3BjceqP1jz7XZsQ5EnNkYAEkfeZp62cDNj13ZTEVG1TEro9sZ9grfRmcYWLBhCocViKEJae"
        ],
        [
            "ffffffffffffffffffffffffffffffffffffffffffffffff",
            "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo when",
            "0cd6e5d827bb62eb8fc1e262254223817fd068a74b5b449cc2f667c3f1f985a76379b43348d952e2265b4cd129090758b3e3c2c49103b5051aac2eaeb890a528",
            "xprv9s21ZrQH143K36Ao5jHRVhFGDbLP6FCx8BEEmpru77ef3bmA928BxsqvVM27WnvvyfWywiFN8K6yToqMaGYfzS6Db1EHAXT5TuyCLBXUfdm"
        ],
        [
            "0000000000000000000000000000000000000000000000000000000000000000",
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art",
            "bda85446c68413707090a52022edd26a1c9462295029f2e60cd7c4f2bbd3097170af7a4d73245cafa9c3cca8d561a7c3de6f5d4a10be8ed2a5e608d68f92fcc8",
            "xprv9s21ZrQH143K32qBagUJAMU2LsHg3ka7jqMcV98Y7gVeVyNStwYS3U7yVVoDZ4btbRNf4h6ibWpY22iRmXq35qgLs79f312g2kj5539ebPM"
        ],
        [
            "7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f",
            "legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth title",
            "bc09fca1804f7e69da93c2f2028eb238c227f2e9dda30cd63699232578480a4021b146ad717fbb7e451ce9eb835f43620bf5c514db0f8add49f5d121449d3e87",
            "xprv9s21ZrQH143K3Y1sd2XVu9wtqxJRvybCfAetjUrMMco6r3v9qZTBeXiBZkS8JxWbcGJZyio8TrZtm6pkbzG8SYt1sxwNLh3Wx7to5pgiVFU"
        ],
        [
            "8080808080808080808080808080808080808080808080808080808080808080",
            "letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic bless",
            "c0c519bd0e91a2ed54357d9d1ebef6f5af218a153624cf4f2da911a0ed8f7a09e2ef61af0aca007096df430022f7a2b6fb91661a9589097069720d015e4e982f",
            "xprv9s21ZrQH143K3CSnQNYC3MqAAqHwxeTLhDbhF43A4ss4ciWNmCY9zQGvAKUSqVUf2vPHBTSE1rB2pg4avopqSiLVzXEU8KziNnVPauTqLRo"
        ],
        [
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo vote",
            "dd48c104698c30cfe2b6142103248622fb7bb0ff692eebb00089b32d22484e1613912f0a5b694407be899ffd31ed3992c456cdf60f5d4564b8ba3f05a69890ad",
            "xprv9s21ZrQH143K2WFF16X85T2QCpndrGwx6GueB72Zf3AHwHJaknRXNF37ZmDrtHrrLSHvbuRejXcnYxoZKvRquTPyp2JiNG3XcjQyzSEgqCB"
        ],
        [
            "9e885d952ad362caeb4efe34a8e91bd2",
            "ozone drill grab fiber curtain grace pudding thank cruise elder eight picnic",
            "274ddc525802f7c828d8ef7ddbcdc5304e87ac3535913611fbbfa986d0c9e5476c91689f9c8a54fd55bd38606aa6a8595ad213d4c9c9f9aca3fb217069a41028",
            "xprv9s21ZrQH143K2oZ9stBYpoaZ2ktHj7jLz7iMqpgg1En8kKFTXJHsjxry1JbKH19YrDTicVwKPehFKTbmaxgVEc5TpHdS1aYhB2s9aFJBeJH"
        ],
        [
            "6610b25967cdcca9d59875f5cb50b0ea75433311869e930b",
            "gravity machine north sort system female filter attitude volume fold club stay feature office ecology stable narrow fog",
            "628c3827a8823298ee685db84f55caa34b5cc195a778e52d45f59bcf75aba68e4d7590e101dc414bc1bbd5737666fbbef35d1f1903953b66624f910feef245ac",
            "xprv9s21ZrQH143K3uT8eQowUjsxrmsA9YUuQQK1RLqFufzybxD6DH6gPY7NjJ5G3EPHjsWDrs9iivSbmvjc9DQJbJGatfa9pv4MZ3wjr8qWPAK"
        ],
        [
            "68a79eaca2324873eacc50cb9c6eca8cc68ea5d936f98787c60c7ebc74e6ce7c",
            "hamster diagram private dutch cause delay private meat slide toddler razor book happy fancy gospel tennis maple dilemma loan word shrug inflict delay length",
            "64c87cde7e12ecf6704ab95bb1408bef047c22db4cc7491c4271d170a1b213d20b385bc1588d9c7b38f1b39d415665b8a9030c9ec653d75e65f847d8fc1fc440",
            "xprv9s21ZrQH143K2XTAhys3pMNcGn261Fi5Ta2Pw8PwaVPhg3D8DWkzWQwjTJfskj8ofb81i9NP2cUNKxwjueJHHMQAnxtivTA75uUFqPFeWzk"
        ],
        [
            "c0ba5a8e914111210f2bd131f3d5e08d",
            "scheme spot photo card baby mountain device kick cradle pact join borrow",
            "ea725895aaae8d4c1cf682c1bfd2d358d52ed9f0f0591131b559e2724bb234fca05aa9c02c57407e04ee9dc3b454aa63fbff483a8b11de949624b9f1831a9612",
            "xprv9s21ZrQH143K3FperxDp8vFsFycKCRcJGAFmcV7umQmcnMZaLtZRt13QJDsoS5F6oYT6BB4sS6zmTmyQAEkJKxJ7yByDNtRe5asP2jFGhT6"
        ],
        [
            "6d9be1ee6ebd27a258115aad99b7317b9c8d28b6d76431c3",
            "horn tenant knee talent sponsor spell gate clip pulse soap slush warm silver nephew swap uncle crack brave",
            "fd579828af3da1d32544ce4db5c73d53fc8acc4ddb1e3b251a31179cdb71e853c56d2fcb11aed39898ce6c34b10b5382772db8796e52837b54468aeb312cfc3d",
            "xprv9s21ZrQH143K3R1SfVZZLtVbXEB9ryVxmVtVMsMwmEyEvgXN6Q84LKkLRmf4ST6QrLeBm3jQsb9gx1uo23TS7vo3vAkZGZz71uuLCcywUkt"
        ],
        [
            "9f6a2878b2520799a44ef18bc7df394e7061a224d2c33cd015b157d746869863",
            "panda eyebrow bullet gorilla call smoke muffin taste mesh discover soft ostrich alcohol speed nation flash devote level hobby quick inner drive ghost inside",
            "72be8e052fc4919d2adf28d5306b5474b0069df35b02303de8c1729c9538dbb6fc2d731d5f832193cd9fb6aeecbc469594a70e3dd50811b5067f3b88b28c3e8d",
            "xprv9s21ZrQH143K2WNnKmssvZYM96VAr47iHUQUTUyUXH3sAGNjhJANddnhw3i3y3pBbRAVk5M5qUGFr4rHbEWwXgX4qrvrceifCYQJbbFDems"
        ],
        [
            "23db8160a31d3e0dca3688ed941adbf3",
            "cat swing flag economy stadium alone churn speed unique patch report train",
            "deb5f45449e615feff5640f2e49f933ff51895de3b4381832b3139941c57b59205a42480c52175b6efcffaa58a2503887c1e8b363a707256bdd2b587b46541f5",
            "xprv9s21ZrQH143K4G28omGMogEoYgDQuigBo8AFHAGDaJdqQ99QKMQ5J6fYTMfANTJy6xBmhvsNZ1CJzRZ64PWbnTFUn6CDV2FxoMDLXdk95DQ"
        ],
        [
            "8197a4a47f0425faeaa69deebc05ca29c0a5b5cc76ceacc0",
            "light rule cinnamon wrap drastic word pride squirrel upgrade then income fatal apart sustain crack supply proud access",
            "4cbdff1ca2db800fd61cae72a57475fdc6bab03e441fd63f96dabd1f183ef5b782925f00105f318309a7e9c3ea6967c7801e46c8a58082674c860a37b93eda02",
            "xprv9s21ZrQH143K3wtsvY8L2aZyxkiWULZH4vyQE5XkHTXkmx8gHo6RUEfH3Jyr6NwkJhvano7Xb2o6UqFKWHVo5scE31SGDCAUsgVhiUuUDyh"
        ],
        [
            "066dca1a2bb7e8a1db2832148ce9933eea0f3ac9548d793112d9a95c9407efad",
            "all hour make first leader extend hole alien behind guard gospel lava path output census museum junior mass reopen famous sing advance salt reform",
            "26e975ec644423f4a4c4f4215ef09b4bd7ef924e85d1d17c4cf3f136c2863cf6df0a475045652c57eb5fb41513ca2a2d67722b77e954b4b3fc11f7590449191d",
            "xprv9s21ZrQH143K3rEfqSM4QZRVmiMuSWY9wugscmaCjYja3SbUD3KPEB1a7QXJoajyR2T1SiXU7rFVRXMV9XdYVSZe7JoUXdP4SRHTxsT1nzm"
        ],
        [
            "f30f8c1da665478f49b001d94c5fc452",
            "vessel ladder alter error federal sibling chat ability sun glass valve picture",
            "2aaa9242daafcee6aa9d7269f17d4efe271e1b9a529178d7dc139cd18747090bf9d60295d0ce74309a78852a9caadf0af48aae1c6253839624076224374bc63f",
            "xprv9s21ZrQH143K2QWV9Wn8Vvs6jbqfF1YbTCdURQW9dLFKDovpKaKrqS3SEWsXCu6ZNky9PSAENg6c9AQYHcg4PjopRGGKmdD313ZHszymnps"
        ],
        [
            "c10ec20dc3cd9f652c7fac2f1230f7a3c828389a14392f05",
            "scissors invite lock maple supreme raw rapid void congress muscle digital elegant little brisk hair mango congress clump",
            "7b4a10be9d98e6cba265566db7f136718e1398c71cb581e1b2f464cac1ceedf4f3e274dc270003c670ad8d02c4558b2f8e39edea2775c9e232c7cb798b069e88",
            "xprv9s21ZrQH143K4aERa2bq7559eMCCEs2QmmqVjUuzfy5eAeDX4mqZffkYwpzGQRE2YEEeLVRoH4CSHxianrFaVnMN2RYaPUZJhJx8S5j6puX"
        ],
        [
            "f585c11aec520db57dd353c69554b21a89b20fb0650966fa0a9d6f74fd989d8f",
            "void come effort suffer camp survey warrior heavy shoot primary clutch crush open amazing screen patrol group space point ten exist slush involve unfold",
            "01f5bced59dec48e362f2c45b5de68b9fd6c92c6634f44d6d40aab69056506f0e35524a518034ddc1192e1dacd32c1ed3eaa3c3b131c88ed8e7e54c49a5d0998",
            "xprv9s21ZrQH143K39rnQJknpH1WEPFJrzmAqqasiDcVrNuk926oizzJDDQkdiTvNPr2FYDYzWgiMiC63YmfPAa2oPyNB23r2g7d1yiK6WpqaQS"
        ]
        ]
        mnemo = Mnemonic()
        for i in range(len(v)):
            code = mnemo.to_mnemonic(unhexlify(v[i][0]))
            seed = Mnemonic.to_seed(code, passphrase="TREZOR")
            key = BIP32Key.fromEntropy(seed)
            if sys.version >= "3":
                seed = hexlify(seed).decode("utf8")
            self.assertIs(mnemo.check(v[i][1]), True)
            self.assertEqual(v[i][1], code)
            self.assertEqual(v[i][2], seed)
            xprv = key.ExtendedKey(private=True, encoded=True)
            self.assertEqual(v[i][3], xprv)

    def test_to_entropy(self):
        data = [
            bytearray((random.getrandbits(8) for _ in range(32))) for _ in range(1024)
        ]
        data.append(b"Lorem ipsum dolor sit amet amet.")
        m = Mnemonic()
        for d in data:
            self.assertEqual(m.to_entropy(m.to_mnemonic(d).split()), d)

    def test_mnemorickey(self):
        word_list = "news clever spot drama infant detail sword cover color throw foot primary when slender rhythm clog autumn ecology enough bronze math you modify excuse"
        mk = MnemonicKey(word_list, role="owner")
        self.assertEqual(str(mk.get_private_key()), str(PrivateKey("L2cgypn75kre1s7JUkTK6H7Y656GwDbNnSNZKWSQ2Rnnx6qM11KD")))
        self.assertEqual(str(mk.get_public_key()), str(PublicKey("02821aa2d26c4fd9b735dd1fed148b96fec978eae1440adf79a4bf95e118b2d8f1")))
        
        mk = MnemonicKey(word_list, role="owner", key_sequence=5)
        self.assertEqual(str(mk.get_private_key()), str(PrivateKey("L5cJSZPcBMBtmuRaK9C48yyXK5JpaH15BsjKLZkmamEWKKx25Kx7")))
        self.assertEqual(str(mk.get_public_key()), str(PublicKey("0309a45aa9add2c7421e0553e23b1800e51d95e525fa4eae1bcc5fb58186e07ed5")))

        mk = MnemonicKey(word_list, role="owner", account_sequence=2)
        self.assertEqual(str(mk.get_private_key()), str(PrivateKey("L4A95nfp1kyJtUtaTqzMyLQkz6NYSfk4R8pejcgKXQSUtPysiFgv")))
        self.assertEqual(str(mk.get_public_key()), str(PublicKey("02b164dc8819830cd50fca4217ad35fa7371cf29db1bc6a07456cc0090ca8ea8fe")))

        mk = MnemonicKey(word_list, role="active")
        self.assertEqual(str(mk.get_private_key()), str(PrivateKey("KygWePihetfhKYCHahcHjMebNSy53HtcXkccYuTn6R8QLydyPUWt")))
        self.assertEqual(str(mk.get_public_key()), str(PublicKey("035c679454155c4c41e8956ecb8e514d37d2d28da91db81c3a22f216a09af94605")))

        mk = MnemonicKey(word_list, role="posting")
        self.assertEqual(str(mk.get_private_key()), str(PrivateKey("L53K986B756VbqatsCi3jjPLHCq8Y38AZyXf19w6CcxuGH84Rrhs")))
        self.assertEqual(str(mk.get_public_key()), str(PublicKey("0200e7d987dfd5aaecf822420475ddcbadc8503a99893d50d06f87da48e85a8206")))

        mk = MnemonicKey(word_list, role="memo")
        self.assertEqual(str(mk.get_private_key()), str(PrivateKey("L5GrFqdRsroM1Ym4aMdALQBL7xN9kNMru9JTgtwbHVZ4iGvx1184")))
        self.assertEqual(str(mk.get_public_key()), str(PublicKey("02fa2cdf5a007b01b1911615a4fba9c2a864a1c1ed079d222e5d549d207412c601")))
