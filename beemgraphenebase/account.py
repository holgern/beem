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
from binascii import hexlify, unhexlify

from .base58 import ripemd160, Base58
from .dictionary import words as BrainKeyDictionary
from .py23 import py23_bytes, PY2


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

    def get_private(self):
        """ Derive private key from the brain key and the current sequence
            number
        """
        a = py23_bytes(self.account + self.role + self.password, 'utf8')
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

    def suggest(self):
        """ Suggest a new random brain key. Randomness is provided by the
            operating system using ``os.urandom()``.
        """
        word_count = 16
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
