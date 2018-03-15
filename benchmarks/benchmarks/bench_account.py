# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from beemgraphenebase.base58 import Base58
from beemgraphenebase.account import BrainKey, Address, PublicKey, PrivateKey, PasswordKey


class Benchmark(object):
    goal_time = 1


class Account(Benchmark):
    def setup(self):
        self.b = BrainKey("COLORER BICORN KASBEKE FAERIE LOCHIA GOMUTI SOVKHOZ Y GERMAL AUNTIE PERFUMY TIME FEATURE GANGAN CELEMIN MATZO")

    def time_B85hexgetb58_btc(self):
        format(Base58("02b52e04a0acfe611a4b6963462aca94b6ae02b24e321eda86507661901adb49"), "WIF")

    def time_B85hexgetb58(self):
        format(Base58("02b52e04a0acfe611a4b6963462aca94b6ae02b24e321eda86507661901adb49"), "BTS")

    def time_Address(self):
        format(Address("BTSFN9r6VYzBK8EKtMewfNbfiGCr56pHDBFi", prefix="BTS"), "BTS")

    def time_PubKey(self):
        format(PublicKey("BTS6UtYWWs3rkZGV8JA86qrgkG6tyFksgECefKE1MiH4HkLD8PFGL", prefix="BTS").address, "BTS")

    def time_btsprivkey(self):
        format(PrivateKey("5HqUkGuo62BfcJU5vNhTXKJRXuUi9QSE6jp8C3uBJ2BVHtB8WSd").address, "BTS")

    def time_btcprivkey(self):
        format(PrivateKey("5HvVz6XMx84aC5KaaBbwYrRLvWE46cH6zVnv4827SBPLorg76oq").uncompressed.address, "BTC")

    def time_PublicKey(self):
        str(PublicKey("BTS6UtYWWs3rkZGV8JA86qrgkG6tyFksgECefKE1MiH4HkLD8PFGL", prefix="BTS"))

    def time_Privatekey(self):
        str(PrivateKey("5HvVz6XMx84aC5KaaBbwYrRLvWE46cH6zVnv4827SBPLorg76oq"))

    def time_BrainKey(self):
        str(BrainKey("COLORER BICORN KASBEKE FAERIE LOCHIA GOMUTI SOVKHOZ Y GERMAL AUNTIE PERFUMY TIME FEATURE GANGAN CELEMIN MATZO").get_private())

    def time_BrainKey_normalize(self):
        BrainKey("COLORER BICORN KASBEKE FAERIE LOCHIA GOMUTI SOVKHOZ Y GERMAL AUNTIE PERFUMY TIME FEATURE GANGAN CELEMIN MATZO").get_brainkey()

    def time_BrainKey_sequences(self):
        p = self.b.next_sequence().get_private()

    def time_PasswordKey(self):
        pwd = "Aang7foN3oz1Ungai2qua5toh3map8ladei1eem2ohsh2shuo8aeji9Thoseo7ah"
        format(PasswordKey("xeroc", pwd, "posting").get_public(), "STM")
    