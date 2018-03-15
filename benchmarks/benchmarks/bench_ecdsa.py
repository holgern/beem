# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import hashlib
import ecdsa
from binascii import hexlify, unhexlify
from beemgraphenebase.account import PrivateKey, PublicKey, Address
import beemgraphenebase.ecdsasig as ecda
from beemgraphenebase.py23 import py23_bytes


class Benchmark(object):
    goal_time = 10


class ECDSA(Benchmark):
    def setup(self):
        ecda.SECP256K1_MODULE = "ecdsa"

    def time_sign(self):
        wif = "5J4KCbg1G3my9b9hCaQXnHSm6vrwW9xQTJS6ZciW2Kek7cCkCEk"
        message = '576b2c99564392ed50e36c80654224953fdf8b5259528a1a4342c19be2da9b133c44429ac2be4d5dd588ec28e97015c34db80b7e8d8915e023c2501acd3eafe0'
        signature = ecda.sign_message(message, wif)
        message = 'foo'
        signature = ecda.sign_message(message, wif)
        message = 'This is a short Message'
        signature = ecda.sign_message(message, wif)
        message = '1234567890'
        signature = ecda.sign_message(message, wif)              
        

    def time_verify(self):
        message = '576b2c99564392ed50e36c80654224953fdf8b5259528a1a4342c19be2da9b133c44429ac2be4d5dd588ec28e97015c34db80b7e8d8915e023c2501acd3eafe0'
        signature = b' S\xef\x14x\x06\xeb\xba\xc5\xf9\x0e\xac\x02pL\xbeLO;\x1d"$\xd7\xfc\x07\xfb\x9c\x08\xc5b^\x1e\xec\x19\xb1y\x11\np\xec(\xc9\xf3\xfd\x1f~\xe3\x99\xe8\xc98]\xd3\x951m${\x82\x0f[(\xa9\x90#'
        pubkey = ecda.verify_message(message, signature)
        signature = b' W\x83\xe5w\x8f\x07\x19EV\xba\x9d\x90\x9f\xfd \x81&\x0f\xa1L\xa00zK0\x08\xf78/\x9d\x0c\x06JFx[*Z\xfe\xd1F\x8d\x9f \x19\xad\xd9\xc9\xbf\xd3\x1br\xdd\x8e\x8ei\xf8\xd2\xf40\xad\xc6\x9c\xe5'
        message = 'foo'
        pubkey = ecda.verify_message(message, signature)
        signature = b'\x1f9\xb6_\x85\xbdr7\\\xb2N\xfb~\x82\xb7E\x80\xf1M\xa4EP=\x8elJ\x1d[t\xab%v~a\xb7\xdbS\x86;~N\xd2!\xf1k=\xb6tMm-\xf1\xd9\xfc\xf3`\xbf\xd5)\x1b\xb3N\x92u/'
        message = 'This is a short Message'
        pubkey = ecda.verify_message(message, signature)
        message = '1234567890'
        signature = b' 7\x82\xe2\xad\xdc\xdb]~\xd6\xa8J\xdc\xa5\xf4\x13<i\xb9\xc0\xdcEc\x10\xd0)t\xc7^\xecw\x05 U\x91\x0f\xa2\xce\x04\xa1\xdb\xb0\nQ\xbd\xafP`\\\x8bb\x99\xcf\xe0;\x01*\xe9D]\xad\xd9l\x1f\x05'        
        pubkey = ecda.verify_message(message, signature)        


class Cryptography(Benchmark):
    def setup(self):
        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.hazmat.primitives.asymmetric.utils \
                import decode_dss_signature, encode_dss_signature
            from cryptography.exceptions import InvalidSignature
            ecda.SECP256K1_MODULE = "cryptography"
        except ImportError:
            raise NotImplementedError("cryptography not available")

    def time_sign(self):
        wif = "5J4KCbg1G3my9b9hCaQXnHSm6vrwW9xQTJS6ZciW2Kek7cCkCEk"
        message = '576b2c99564392ed50e36c80654224953fdf8b5259528a1a4342c19be2da9b133c44429ac2be4d5dd588ec28e97015c34db80b7e8d8915e023c2501acd3eafe0'
        signature = ecda.sign_message(message, wif)
        message = 'foo'
        signature = ecda.sign_message(message, wif)
        message = 'This is a short Message'
        signature = ecda.sign_message(message, wif)
        message = '1234567890'
        signature = ecda.sign_message(message, wif)        

    def time_verify(self):
        message = '576b2c99564392ed50e36c80654224953fdf8b5259528a1a4342c19be2da9b133c44429ac2be4d5dd588ec28e97015c34db80b7e8d8915e023c2501acd3eafe0'
        signature = b' S\xef\x14x\x06\xeb\xba\xc5\xf9\x0e\xac\x02pL\xbeLO;\x1d"$\xd7\xfc\x07\xfb\x9c\x08\xc5b^\x1e\xec\x19\xb1y\x11\np\xec(\xc9\xf3\xfd\x1f~\xe3\x99\xe8\xc98]\xd3\x951m${\x82\x0f[(\xa9\x90#'
        pubkey = ecda.verify_message(message, signature)
        signature = b' W\x83\xe5w\x8f\x07\x19EV\xba\x9d\x90\x9f\xfd \x81&\x0f\xa1L\xa00zK0\x08\xf78/\x9d\x0c\x06JFx[*Z\xfe\xd1F\x8d\x9f \x19\xad\xd9\xc9\xbf\xd3\x1br\xdd\x8e\x8ei\xf8\xd2\xf40\xad\xc6\x9c\xe5'
        message = 'foo'
        pubkey = ecda.verify_message(message, signature)
        signature = b'\x1f9\xb6_\x85\xbdr7\\\xb2N\xfb~\x82\xb7E\x80\xf1M\xa4EP=\x8elJ\x1d[t\xab%v~a\xb7\xdbS\x86;~N\xd2!\xf1k=\xb6tMm-\xf1\xd9\xfc\xf3`\xbf\xd5)\x1b\xb3N\x92u/'
        message = 'This is a short Message'
        pubkey = ecda.verify_message(message, signature)
        message = '1234567890'
        signature = b' 7\x82\xe2\xad\xdc\xdb]~\xd6\xa8J\xdc\xa5\xf4\x13<i\xb9\xc0\xdcEc\x10\xd0)t\xc7^\xecw\x05 U\x91\x0f\xa2\xce\x04\xa1\xdb\xb0\nQ\xbd\xafP`\\\x8bb\x99\xcf\xe0;\x01*\xe9D]\xad\xd9l\x1f\x05'        
        pubkey = ecda.verify_message(message, signature)


class Secp256k1(Benchmark):
    def setup(self):
        try:
            import secp256k1
            ecda.SECP256K1_MODULE = "secp256k1"
        except ImportError:
            raise NotImplementedError("secp256k1 not available")

    def time_sign(self):
        wif = "5J4KCbg1G3my9b9hCaQXnHSm6vrwW9xQTJS6ZciW2Kek7cCkCEk"
        message = '576b2c99564392ed50e36c80654224953fdf8b5259528a1a4342c19be2da9b133c44429ac2be4d5dd588ec28e97015c34db80b7e8d8915e023c2501acd3eafe0'
        signature = ecda.sign_message(message, wif)
        message = 'foo'
        signature = ecda.sign_message(message, wif)
        message = 'This is a short Message'
        signature = ecda.sign_message(message, wif)
        message = '1234567890'
        signature = ecda.sign_message(message, wif)        

    def time_verify(self):
        message = '576b2c99564392ed50e36c80654224953fdf8b5259528a1a4342c19be2da9b133c44429ac2be4d5dd588ec28e97015c34db80b7e8d8915e023c2501acd3eafe0'
        signature = b' S\xef\x14x\x06\xeb\xba\xc5\xf9\x0e\xac\x02pL\xbeLO;\x1d"$\xd7\xfc\x07\xfb\x9c\x08\xc5b^\x1e\xec\x19\xb1y\x11\np\xec(\xc9\xf3\xfd\x1f~\xe3\x99\xe8\xc98]\xd3\x951m${\x82\x0f[(\xa9\x90#'
        pubkey = ecda.verify_message(message, signature)
        signature = b' W\x83\xe5w\x8f\x07\x19EV\xba\x9d\x90\x9f\xfd \x81&\x0f\xa1L\xa00zK0\x08\xf78/\x9d\x0c\x06JFx[*Z\xfe\xd1F\x8d\x9f \x19\xad\xd9\xc9\xbf\xd3\x1br\xdd\x8e\x8ei\xf8\xd2\xf40\xad\xc6\x9c\xe5'
        message = 'foo'
        pubkey = ecda.verify_message(message, signature)
        signature = b'\x1f9\xb6_\x85\xbdr7\\\xb2N\xfb~\x82\xb7E\x80\xf1M\xa4EP=\x8elJ\x1d[t\xab%v~a\xb7\xdbS\x86;~N\xd2!\xf1k=\xb6tMm-\xf1\xd9\xfc\xf3`\xbf\xd5)\x1b\xb3N\x92u/'
        message = 'This is a short Message'
        pubkey = ecda.verify_message(message, signature)
        message = '1234567890'
        signature = b' 7\x82\xe2\xad\xdc\xdb]~\xd6\xa8J\xdc\xa5\xf4\x13<i\xb9\xc0\xdcEc\x10\xd0)t\xc7^\xecw\x05 U\x91\x0f\xa2\xce\x04\xa1\xdb\xb0\nQ\xbd\xafP`\\\x8bb\x99\xcf\xe0;\x01*\xe9D]\xad\xd9l\x1f\x05'        
        pubkey = ecda.verify_message(message, signature)

