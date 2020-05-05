from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes
from builtins import chr
from builtins import range
from builtins import object
from future.utils import python_2_unicode_compatible
import hashlib
import sys
import re
import os
import codecs
import ecdsa
import ctypes
import binascii
import bisect
import hmac
import itertools
from binascii import hexlify, unhexlify
import unicodedata

from .base58 import ripemd160, Base58
from .bip32 import BIP32Key, parse_path
from .dictionary import words as BrainKeyDictionary
from .dictionary import words_bip39 as MnemonicDictionary
from .py23 import py23_bytes, PY2


PBKDF2_ROUNDS = 2048

# From <https://stackoverflow.com/questions/212358/binary-search-bisection-in-python/2233940#2233940>
def binary_search(a, x, lo=0, hi=None):  # can't use a to specify default for hi
    hi = hi if hi is not None else len(a)  # hi defaults to len(a)
    pos = bisect.bisect_left(a, x, lo, hi)  # find insertion position
    return pos if pos != hi and a[pos] == x else -1  # don't walk off the end


class PasswordKey(object):
    """ This class derives a private key given the account name, the
        role and a password. It leverages the technology of Brainkeys
        and allows people to have a secure private key by providing a
        passphrase only.
    """

    def __init__(self, account, password, role="active", prefix="STM"):
        self.account = account
        self.role = role
        self.password = password
        self.prefix = prefix

    def normalize(self, seed):
        """ Correct formating with single whitespace syntax and no trailing space """
        return " ".join(re.compile("[\t\n\v\f\r ]+").split(seed))

    def get_private(self):
        """ Derive private key from the account, the role and the password
        """
        if self.account is None and self.role is None:
            seed = self.password
        elif self.account == "" and self.role == "":
            seed = self.password
        else:
            seed = self.account + self.role + self.password
        seed = self.normalize(seed)
        a = py23_bytes(seed, 'utf8')
        s = hashlib.sha256(a).digest()
        return PrivateKey(hexlify(s).decode('ascii'), prefix=self.prefix)

    def get_public(self):
        return self.get_private().pubkey

    def get_private_key(self):
        return self.get_private()

    def get_public_key(self):
        return self.get_public()


@python_2_unicode_compatible
class BrainKey(object):
    """Brainkey implementation similar to the graphene-ui web-wallet.

        :param str brainkey: Brain Key
        :param int sequence: Sequence number for consecutive keys

        Keys in Graphene are derived from a seed brain key which is a string of
        16 words out of a predefined dictionary with 49744 words. It is a
        simple single-chain key derivation scheme that is not compatible with
        BIP44 but easy to use.

        Given the brain key, a private key is derived as::

            privkey = SHA256(SHA512(brainkey + " " + sequence))

        Incrementing the sequence number yields a new key that can be
        regenerated given the brain key.

    """

    def __init__(self, brainkey=None, sequence=0):
        if not brainkey:
            self.brainkey = self.suggest()
        else:
            self.brainkey = self.normalize(brainkey).strip()
        self.sequence = sequence

    def __next__(self):
        """ Get the next private key (sequence number increment) for
            iterators
        """
        return self.next_sequence()

    def next_sequence(self):
        """ Increment the sequence number by 1 """
        self.sequence += 1
        return self

    def normalize(self, brainkey):
        """ Correct formating with single whitespace syntax and no trailing space """
        return " ".join(re.compile("[\t\n\v\f\r ]+").split(brainkey))

    def get_brainkey(self):
        """ Return brain key of this instance """
        return self.normalize(self.brainkey)

    def get_private(self):
        """ Derive private key from the brain key and the current sequence
            number
        """
        encoded = "%s %d" % (self.brainkey, self.sequence)
        a = py23_bytes(encoded, 'ascii')
        s = hashlib.sha256(hashlib.sha512(a).digest()).digest()
        return PrivateKey(hexlify(s).decode('ascii'))

    def get_blind_private(self):
        """ Derive private key from the brain key (and no sequence number)
        """
        a = py23_bytes(self.brainkey, 'ascii')
        return PrivateKey(hashlib.sha256(a).hexdigest())

    def get_public(self):
        return self.get_private().pubkey

    def get_private_key(self):
        return self.get_private()

    def get_public_key(self):
        return self.get_public()

    def suggest(self, word_count=16):
        """ Suggest a new random brain key. Randomness is provided by the
            operating system using ``os.urandom()``.
        """
        brainkey = [None] * word_count
        dict_lines = BrainKeyDictionary.split(',')
        if not len(dict_lines) == 49744:
            raise AssertionError()
        for j in range(0, word_count):
            urand = os.urandom(2)
            if isinstance(urand, str):
                urand = py23_bytes(urand, 'ascii')
            if PY2:
                num = int(codecs.encode(urand[::-1], 'hex'), 16)
            else:
                num = int.from_bytes(urand, byteorder="little")
            rndMult = num / 2 ** 16  # returns float between 0..1 (inclusive)
            wIdx = int(round(len(dict_lines) * rndMult))
            brainkey[j] = dict_lines[wIdx]
        return " ".join(brainkey).upper()


# From https://github.com/trezor/python-mnemonic/blob/master/mnemonic/mnemonic.py
# 
# Copyright (c) 2013 Pavol Rusnak
# Copyright (c) 2017 mruddy
@python_2_unicode_compatible
class Mnemonic(object):
    """BIP39 mnemoric implementation"""
    def __init__(self):
        self.wordlist = MnemonicDictionary.split(',')
        self.radix = 2048

    def generate(self, strength=128):
        """ Generates a word list based on the given strength

        :param int strength: initial entropy strength, must be one of [128, 160, 192, 224, 256]

        """
        if strength not in [128, 160, 192, 224, 256]:
            raise ValueError(
                "Strength should be one of the following [128, 160, 192, 224, 256], but it is not (%d)."
                % strength
            )
        return self.to_mnemonic(os.urandom(strength // 8))

    # Adapted from <http://tinyurl.com/oxmn476>
    def to_entropy(self, words):
        if not isinstance(words, list):
            words = words.split(" ")
        if len(words) not in [12, 15, 18, 21, 24]:
            raise ValueError(
                "Number of words must be one of the following: [12, 15, 18, 21, 24], but it is not (%d)."
                % len(words)
            )
        # Look up all the words in the list and construct the
        # concatenation of the original entropy and the checksum.
        concatLenBits = len(words) * 11
        concatBits = [False] * concatLenBits
        wordindex = 0
        use_binary_search = True
        for word in words:
            # Find the words index in the wordlist
            ndx = (
                binary_search(self.wordlist, word)
                if use_binary_search
                else self.wordlist.index(word)
            )
            if ndx < 0:
                raise LookupError('Unable to find "%s" in word list.' % word)
            # Set the next 11 bits to the value of the index.
            for ii in range(11):
                concatBits[(wordindex * 11) + ii] = (ndx & (1 << (10 - ii))) != 0
            wordindex += 1
        checksumLengthBits = concatLenBits // 33
        entropyLengthBits = concatLenBits - checksumLengthBits
        # Extract original entropy as bytes.
        entropy = bytearray(entropyLengthBits // 8)
        for ii in range(len(entropy)):
            for jj in range(8):
                if concatBits[(ii * 8) + jj]:
                    entropy[ii] |= 1 << (7 - jj)
        # Take the digest of the entropy.
        hashBytes = hashlib.sha256(entropy).digest()
        if sys.version < "3":
            hashBits = list(
                itertools.chain.from_iterable(
                    (
                        [ord(c) & (1 << (7 - i)) != 0 for i in range(8)]
                        for c in hashBytes
                    )
                )
            )
        else:
            hashBits = list(
                itertools.chain.from_iterable(
                    ([c & (1 << (7 - i)) != 0 for i in range(8)] for c in hashBytes)
                )
            )
        # Check all the checksum bits.
        for i in range(checksumLengthBits):
            if concatBits[entropyLengthBits + i] != hashBits[i]:
                raise ValueError("Failed checksum.")
        return entropy

    def to_mnemonic(self, data):
        if len(data) not in [16, 20, 24, 28, 32]:
            raise ValueError(
                "Data length should be one of the following: [16, 20, 24, 28, 32], but it is not (%d)."
                % len(data)
            )
        h = hashlib.sha256(data).hexdigest()
        b = (
            bin(int(binascii.hexlify(data), 16))[2:].zfill(len(data) * 8)
            + bin(int(h, 16))[2:].zfill(256)[: len(data) * 8 // 32]
        )
        result = []
        for i in range(len(b) // 11):
            idx = int(b[i * 11 : (i + 1) * 11], 2)
            result.append(self.wordlist[idx])

        result_phrase = " ".join(result)
        return result_phrase

    def check(self, mnemonic):
        """ Checks the mnemonic word list is valid
        :param list mnemonic: mnemonic word list with lenght of 12, 15, 18, 21, 24
        :returns: True, when valid
        """
        mnemonic = self.normalize_string(mnemonic).split(" ")
        # list of valid mnemonic lengths
        if len(mnemonic) not in [12, 15, 18, 21, 24]:
            return False
        try:
            idx = map(lambda x: bin(self.wordlist.index(x))[2:].zfill(11), mnemonic)
            b = "".join(idx)
        except ValueError:
            return False
        l = len(b)  # noqa: E741
        d = b[: l // 33 * 32]
        h = b[-l // 33 :]
        nd = binascii.unhexlify(hex(int(d, 2))[2:].rstrip("L").zfill(l // 33 * 8))
        nh = bin(int(hashlib.sha256(nd).hexdigest(), 16))[2:].zfill(256)[: l // 33]
        return h == nh

    def check_word(self, word):
        return word in self.wordlist

    def expand_word(self, prefix):
        """Expands a word when sufficient chars are given

        :param str prefix: first chars of a valid dict word

        """
        if prefix in self.wordlist:
            return prefix
        else:
            matches = [word for word in self.wordlist if word.startswith(prefix)]
            if len(matches) == 1:  # matched exactly one word in the wordlist
                return matches[0]
            else:
                # exact match not found.
                # this is not a validation routine, just return the input
                return prefix

    def expand(self, mnemonic):
        """Expands all words given in a list"""
        return " ".join(map(self.expand_word, mnemonic.split(" ")))

    @classmethod
    def normalize_string(cls, txt):
        """Normalizes strings"""
        if isinstance(txt, str if sys.version < "3" else bytes):
            utxt = txt.decode("utf8")
        elif isinstance(txt, unicode if sys.version < "3" else str):  # noqa: F821
            utxt = txt
        else:
            raise TypeError("String value expected")

        return unicodedata.normalize("NFKD", utxt)

    @classmethod
    def to_seed(cls, mnemonic, passphrase=""):
        """Returns a seed based on bip39

        :param str mnemonic: string containing a valid mnemonic word list
        :param str passphrase: optional, passphrase can be set to modify the returned seed.
        
        """
        mnemonic = cls.normalize_string(mnemonic)
        passphrase = cls.normalize_string(passphrase)
        passphrase = "mnemonic" + passphrase
        mnemonic = mnemonic.encode("utf-8")
        passphrase = passphrase.encode("utf-8")
        stretched = hashlib.pbkdf2_hmac("sha512", mnemonic, passphrase, PBKDF2_ROUNDS)
        return stretched[:64]




class MnemonicKey(object):
    """ This class derives a private key from a BIP39 mnemoric implementation
    """

    def __init__(self, word_list=None, passphrase="", network_index=13, role="owner", account_sequence=0, key_sequence=0, prefix="STM"):
        if word_list is not None:
            self.set_mnemonic(word_list, passphrase=passphrase)
        else:
            self.seed = None
        self.network_index = network_index
        self.role = role
        self.account_sequence = account_sequence
        self.key_sequence = key_sequence
        self.prefix = prefix
        self.path_prefix = "m/48'"

    def set_mnemonic(self, word_list, passphrase=""):
        mnemonic = Mnemonic()
        if not mnemonic.check(word_list):
            raise ValueError("Word list is not valid!")
        self.seed = mnemonic.to_seed(word_list, passphrase=passphrase)   

    def generate_mnemonic(self, passphrase="", strength=256):
        mnemonic = Mnemonic()
        word_list = mnemonic.generate(strength=strength)
        self.seed = mnemonic.to_seed(word_list, passphrase=passphrase)
        return word_list

    def set_path(self, network_index=13, role="owner", account_sequence=0, key_sequence=0):
        if account_sequence < 0:
            raise ValueError("account_sequence must be >= 0")
        if key_sequence < 0:
            raise ValueError("key_sequence must be >= 0")
        if network_index < 0:
            raise ValueError("network_index must be >= 0")
        if isinstance(role, str) and role not in ["owner", "active", "posting", "memo"]:
            raise ValueError("Wrong role!")
        elif isinstance(role, int) and role < 0:
            raise ValueError("role must be >= 0")
        self.role = role
        self.account_sequence = account_sequence
        self.key_sequence = key_sequence
        self.network_index = network_index

    def next_account_sequence(self):
        """ Increment the account sequence number by 1 """
        self.account_sequence += 1
        return self

    def next_sequence(self):
        """ Increment the key sequence number by 1 """
        self.key_sequence += 1
        return self  

    def get_path(self):
        if self.account_sequence < 0:
            raise ValueError("account_sequence must be >= 0")
        if self.key_sequence < 0:
            raise ValueError("key_sequence must be >= 0")
        if self.network_index < 0:
            raise ValueError("network_index must be >= 0")
        if isinstance(self.role, str) and self.role not in ["owner", "active", "posting", "memo"]:
            raise ValueError("Wrong role!")
        elif isinstance(self.role, int) and self.role < 0:
            raise ValueError("role must be >= 0")    
        if self.role == "owner":
            role = 0
        elif self.role == "active":
            role = 1
        elif self.role == "posting":
            role = 4
        elif self.role == "memo":
            role = 3
        else:
            role = self.role
        return "%s/%d'/%d'/%d'/%d'" % (self.path_prefix, self.network_index, role, self.account_sequence, self.key_sequence)

    def get_private(self):
        """ Derive private key from the account_sequence, the role and the key_sequence
        """
        if self.seed is None:
            raise ValueError("seed is None, set or generate a mnemnoric first")
        key = BIP32Key.fromEntropy(self.seed)
        for n in parse_path(self.get_path()):
            key = key.ChildKey(n)
        return PrivateKey(key.WalletImportFormat(), prefix=self.prefix)

    def get_public(self):
        return self.get_private().pubkey

    def get_private_key(self):
        return self.get_private()

    def get_public_key(self):
        return self.get_public()


@python_2_unicode_compatible
class Address(object):
    """ Address class

        This class serves as an address representation for Public Keys.

        :param str address: Base58 encoded address (defaults to ``None``)
        :param str pubkey: Base58 encoded pubkey (defaults to ``None``)
        :param str prefix: Network prefix (defaults to ``STM``)

        Example::

           Address("STMFN9r6VYzBK8EKtMewfNbfiGCr56pHDBFi")

    """
    def __init__(self, address=None, pubkey=None, prefix="STM"):
        self.prefix = prefix
        if pubkey is not None:
            self._pubkey = Base58(pubkey, prefix=prefix)
            self._address = None
        elif address is not None:
            self._pubkey = None
            self._address = Base58(address, prefix=prefix)
        else:
            raise Exception("Address has to be initialized by either the " +
                            "pubkey or the address.")

    def get_public_key(self):
        """Returns the pubkey"""
        return self._pubkey

    def derivesha256address(self):
        """ Derive address using ``RIPEMD160(SHA256(x))`` """
        pubkey = self.get_public_key()
        if pubkey is None:
            return None
        pkbin = unhexlify(repr(pubkey))
        addressbin = ripemd160(hexlify(hashlib.sha256(pkbin).digest()))
        return Base58(hexlify(addressbin).decode('ascii'))

    def derive256address_with_version(self, version=56):
        """ Derive address using ``RIPEMD160(SHA256(x))``
            and adding version + checksum
        """
        pubkey = self.get_public_key()
        if pubkey is None:
            return None
        pkbin = unhexlify(repr(pubkey))
        addressbin = ripemd160(hexlify(hashlib.sha256(pkbin).digest()))
        addr = py23_bytes(bytearray(ctypes.c_uint8(version & 0xFF))) + addressbin
        check = hashlib.sha256(addr).digest()
        check = hashlib.sha256(check).digest()
        buffer = addr + check[0:4]
        return Base58(hexlify(ripemd160(hexlify(buffer))).decode('ascii'))

    def derivesha512address(self):
        """ Derive address using ``RIPEMD160(SHA512(x))`` """
        pubkey = self.get_public_key()
        if pubkey is None:
            return None
        pkbin = unhexlify(repr(pubkey))
        addressbin = ripemd160(hexlify(hashlib.sha512(pkbin).digest()))
        return Base58(hexlify(addressbin).decode('ascii'))

    def __repr__(self):
        """ Gives the hex representation of the ``GrapheneBase58CheckEncoded``
            Graphene address.
        """
        if self._address is None:
            return repr(self.derivesha512address())
        else:
            return repr(self._address)

    def __str__(self):
        """ Returns the readable Graphene address. This call is equivalent to
            ``format(Address, "STM")``
        """
        return format(self, self.prefix)

    def __format__(self, _format):
        """  May be issued to get valid "MUSE", "PLAY" or any other Graphene compatible
            address with corresponding prefix.
        """
        if self._address is None:
            if _format.lower() == "btc":
                return format(self.derivesha256address(), _format)
            else:
                return format(self.derivesha512address(), _format)
        else:
            return format(self._address, _format)

    def __bytes__(self):
        """ Returns the raw content of the ``Base58CheckEncoded`` address """
        if self._address is None:
            return py23_bytes(self.derivesha512address())
        else:
            return py23_bytes(self._address)


@python_2_unicode_compatible
class PublicKey(Address):
    """ This class deals with Public Keys and inherits ``Address``.

        :param str pk: Base58 encoded public key
        :param str prefix: Network prefix (defaults to ``STM``)

        Example::

           PublicKey("STM6UtYWWs3rkZGV8JA86qrgkG6tyFksgECefKE1MiH4HkLD8PFGL")

        .. note:: By default, graphene-based networks deal with **compressed**
                  public keys. If an **uncompressed** key is required, the
                  method :func:`unCompressed` can be used::

                      PublicKey("xxxxx").unCompressed()

    """
    def __init__(self, pk, prefix="STM"):
        """Init PublicKey
            :param str pk: Base58 encoded public key
            :param str prefix: Network prefix (defaults to ``STM``)
        """
        self.prefix = prefix
        self._pk = Base58(pk, prefix=prefix)
        self.address = Address(pubkey=pk, prefix=prefix)
        self.pubkey = self._pk

    def get_public_key(self):
        """Returns the pubkey"""
        return self.pubkey

    def _derive_y_from_x(self, x, is_even):
        """ Derive y point from x point """
        curve = ecdsa.SECP256k1.curve
        # The curve equation over F_p is:
        #   y^2 = x^3 + ax + b
        a, b, p = curve.a(), curve.b(), curve.p()
        alpha = (pow(x, 3, p) + a * x + b) % p
        beta = ecdsa.numbertheory.square_root_mod_prime(alpha, p)
        if (beta % 2) == is_even:
            beta = p - beta
        return beta

    def compressed(self):
        """ Derive compressed public key """
        order = ecdsa.SECP256k1.generator.order()
        p = ecdsa.VerifyingKey.from_string(py23_bytes(self), curve=ecdsa.SECP256k1).pubkey.point
        x_str = ecdsa.util.number_to_string(p.x(), order)
        # y_str = ecdsa.util.number_to_string(p.y(), order)
        compressed = hexlify(py23_bytes(chr(2 + (p.y() & 1)), 'ascii') + x_str).decode('ascii')
        return(compressed)

    def unCompressed(self):
        """ Derive uncompressed key """
        public_key = repr(self._pk)
        prefix = public_key[0:2]
        if prefix == "04":
            return public_key
        if not (prefix == "02" or prefix == "03"):
            raise AssertionError()
        x = int(public_key[2:], 16)
        y = self._derive_y_from_x(x, (prefix == "02"))
        key = '04' + '%064x' % x + '%064x' % y
        return key

    def point(self):
        """ Return the point for the public key """
        string = unhexlify(self.unCompressed())
        return ecdsa.VerifyingKey.from_string(string[1:], curve=ecdsa.SECP256k1).pubkey.point

    def __repr__(self):
        """ Gives the hex representation of the Graphene public key. """
        return repr(self._pk)

    def __str__(self):
        """ Returns the readable Graphene public key. This call is equivalent to
            ``format(PublicKey, "STM")``
        """
        return format(self._pk, self.prefix)

    def __format__(self, _format):
        """ Formats the instance of:doc:`Base58 <base58>` according to ``_format`` """
        return format(self._pk, _format)

    def __bytes__(self):
        """ Returns the raw public key (has length 33)"""
        return py23_bytes(self._pk)


@python_2_unicode_compatible
class PrivateKey(PublicKey):
    """ Derives the compressed and uncompressed public keys and
        constructs two instances of :class:`PublicKey`:

        :param str wif: Base58check-encoded wif key
        :param str prefix: Network prefix (defaults to ``STM``)

        Example::

            PrivateKey("5HqUkGuo62BfcJU5vNhTXKJRXuUi9QSE6jp8C3uBJ2BVHtB8WSd")

        Compressed vs. Uncompressed:

        * ``PrivateKey("w-i-f").pubkey``:
            Instance of :class:`PublicKey` using compressed key.
        * ``PrivateKey("w-i-f").pubkey.address``:
            Instance of :class:`Address` using compressed key.
        * ``PrivateKey("w-i-f").uncompressed``:
            Instance of :class:`PublicKey` using uncompressed key.
        * ``PrivateKey("w-i-f").uncompressed.address``:
            Instance of :class:`Address` using uncompressed key.

    """
    def __init__(self, wif=None, prefix="STM"):
        if wif is None:
            self._wif = Base58(hexlify(os.urandom(32)).decode('ascii'), prefix=prefix)
        elif isinstance(wif, Base58):
            self._wif = wif
        else:
            self._wif = Base58(wif, prefix=prefix)
        # compress pubkeys only
        self._pubkeyhex, self._pubkeyuncompressedhex = self.compressedpubkey()
        self.pubkey = PublicKey(self._pubkeyhex, prefix=prefix)
        self.uncompressed = PublicKey(self._pubkeyuncompressedhex, prefix=prefix)
        self.uncompressed.address = Address(pubkey=self._pubkeyuncompressedhex, prefix=prefix)
        self.address = Address(pubkey=self._pubkeyhex, prefix=prefix)

    def get_public_key(self):
        """Returns the pubkey"""
        return self.pubkey

    def compressedpubkey(self):
        """ Derive uncompressed public key """
        secret = unhexlify(repr(self._wif))
        if not len(secret) == ecdsa.SECP256k1.baselen:
            raise ValueError("{} != {}".format(len(secret), ecdsa.SECP256k1.baselen))
        order = ecdsa.SigningKey.from_string(secret, curve=ecdsa.SECP256k1).curve.generator.order()
        p = ecdsa.SigningKey.from_string(secret, curve=ecdsa.SECP256k1).verifying_key.pubkey.point
        x_str = ecdsa.util.number_to_string(p.x(), order)
        y_str = ecdsa.util.number_to_string(p.y(), order)
        compressed = hexlify(py23_bytes(chr(2 + (p.y() & 1)), 'ascii') + x_str).decode('ascii')
        uncompressed = hexlify(py23_bytes(chr(4), 'ascii') + x_str + y_str).decode('ascii')
        return([compressed, uncompressed])

    def get_secret(self):
        """ Get sha256 digest of the wif key.
        """
        return hashlib.sha256(py23_bytes(self)).digest()

    def derive_private_key(self, sequence):
        """ Derive new private key from this private key and an arbitrary
            sequence number
        """
        encoded = "%s %d" % (str(self), sequence)
        a = py23_bytes(encoded, 'ascii')
        s = hashlib.sha256(hashlib.sha512(a).digest()).digest()
        return PrivateKey(hexlify(s).decode('ascii'), prefix=self.pubkey.prefix)

    def child(self, offset256):
        """ Derive new private key from this key and a sha256 "offset"
        """
        pubkey = self.get_public_key()
        a = py23_bytes(pubkey) + offset256
        s = hashlib.sha256(a).digest()
        return self.derive_from_seed(s)

    def derive_from_seed(self, offset):
        """ Derive private key using "generate_from_seed" method.
            Here, the key itself serves as a `seed`, and `offset`
            is expected to be a sha256 digest.
        """
        seed = int(hexlify(py23_bytes(self)).decode('ascii'), 16)
        z = int(hexlify(offset).decode('ascii'), 16)
        order = ecdsa.SECP256k1.order

        secexp = (seed + z) % order

        secret = "%0x" % secexp
        return PrivateKey(secret, prefix=self.pubkey.prefix)

    def __format__(self, _format):
        """ Formats the instance of:doc:`Base58 <base58>` according to
            ``_format``
        """
        return format(self._wif, _format)

    def __repr__(self):
        """ Gives the hex representation of the Graphene private key."""
        return repr(self._wif)

    def __str__(self):
        """ Returns the readable (uncompressed wif format) Graphene private key. This
            call is equivalent to ``format(PrivateKey, "WIF")``
        """
        return format(self._wif, "WIF")

    def __bytes__(self):
        """ Returns the raw private key """
        return py23_bytes(self._wif)
