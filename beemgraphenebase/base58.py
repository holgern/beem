# -*- coding: utf-8 -*-
from binascii import hexlify, unhexlify
from .py23 import py23_bytes, py23_chr, bytes_types, integer_types, string_types, text_type
from .prefix import Prefix
import hashlib
import string
import logging
log = logging.getLogger(__name__)


class Base58(Prefix):
    """Base58 base class

    This class serves as an abstraction layer to deal with base58 encoded
    strings and their corresponding hex and binary representation throughout the
    library.

    :param data: Data to initialize object, e.g. pubkey data, address data, ...
    :type data: hex, wif, bip38 encrypted wif, base58 string
    :param str prefix: Prefix to use for Address/PubKey strings (defaults to ``GPH``)
    :return: Base58 object initialized with ``data``
    :rtype: Base58
    :raises ValueError: if data cannot be decoded

    * ``bytes(Base58)``: Returns the raw data
    * ``str(Base58)``:   Returns the readable ``Base58CheckEncoded`` data.
    * ``repr(Base58)``:  Gives the hex representation of the data.
    * ``format(Base58,_format)``: Formats the instance according to ``_format``

        * ``"btc"``: prefixed with ``0x80``. Yields a valid btc address
        * ``"wif"``: prefixed with ``0x00``. Yields a valid wif key
        * ``"bts"``: prefixed with ``BTS``
        * etc.

    """
    def __init__(self, data, prefix=None):
        self.set_prefix(prefix)
        if isinstance(data, Base58):
            data = repr(data)
        if all(c in string.hexdigits for c in data):
            self._hex = data
        elif data[0] == "5" or data[0] == "6":
            self._hex = base58CheckDecode(data)
        elif data[0] == "K" or data[0] == "L":
            self._hex = base58CheckDecode(data)[:-2]
        elif data[:len(self.prefix)] == self.prefix:
            self._hex = gphBase58CheckDecode(data[len(self.prefix):])
        else:
            raise ValueError("Error loading Base58 object")

    def __format__(self, _format):
        """ Format output according to argument _format (wif,btc,...)

            :param str _format: Format to use
            :return: formatted data according to _format
            :rtype: str

        """
        if _format.upper() == "WIF":
            return base58CheckEncode(0x80, self._hex)
        elif _format.upper() == "ENCWIF":
            return base58encode(self._hex)
        elif _format.upper() == "BTC":
            return base58CheckEncode(0x00, self._hex)
        else:
            return _format.upper() + str(self)

    def __repr__(self):
        """ Returns hex value of object

            :return: Hex string of instance's data
            :rtype: hex string
        """
        return self._hex

    def __str__(self):
        """ Return graphene-base58CheckEncoded string of data

            :return: Base58 encoded data
            :rtype: str
        """
        return gphBase58CheckEncode(self._hex)

    def __bytes__(self):
        """ Return raw bytes

            :return: Raw bytes of instance
            :rtype: bytes

        """
        return unhexlify(self._hex)


# https://github.com/tochev/python3-cryptocoins/raw/master/cryptocoins/base58.py
BASE58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def base58decode(base58_str):
    base58_text = py23_bytes(base58_str, "ascii")
    n = 0
    leading_zeroes_count = 0
    for b in base58_text:
        if isinstance(b, integer_types):
            n = n * 58 + BASE58_ALPHABET.find(py23_chr(b))
        else:
            n = n * 58 + BASE58_ALPHABET.find(b)
        if n == 0:
            leading_zeroes_count += 1
    res = bytearray()
    while n >= 256:
        div, mod = divmod(n, 256)
        res.insert(0, mod)
        n = div
    else:
        res.insert(0, n)
    return hexlify(bytearray(1) * leading_zeroes_count + res).decode('ascii')


def base58encode(hexstring):
    byteseq = py23_bytes(unhexlify(py23_bytes(hexstring, 'ascii')))
    n = 0
    leading_zeroes_count = 0
    for c in byteseq:
        n = n * 256 + c
        if n == 0:
            leading_zeroes_count += 1
    res = bytearray()
    while n >= 58:
        div, mod = divmod(n, 58)
        res.insert(0, BASE58_ALPHABET[mod])
        n = div
    else:
        res.insert(0, BASE58_ALPHABET[n])
    return (BASE58_ALPHABET[0:1] * leading_zeroes_count + res).decode('ascii')


def ripemd160(s):
    try:
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(unhexlify(s))
        return ripemd160.digest()
    except BaseException:
        # ripemd160 is not guaranteed to be available in hashlib on all platforms.
        # Historically, our Android builds had hashlib/openssl which did not have it.
        # see https://github.com/spesmilo/electrum/issues/7093
        # We bundle a pure python implementation as fallback that gets used now:
        from beem import ripemd
        md = ripemd.new(unhexlify(s))
        return md.digest()

def doublesha256(s):
    return hashlib.sha256(hashlib.sha256(unhexlify(s)).digest()).digest()


def b58encode(v):
    return base58encode(v)


def b58decode(v):
    return base58decode(v)


def base58CheckEncode(version, payload):
    if isinstance(version, string_types):
        s = version + payload
    else:
        s = ('%.2x' % version) + payload
    checksum = doublesha256(s)[:4]
    result = s + hexlify(checksum).decode('ascii')
    return base58encode(result)


def base58CheckDecode(s, skip_first_bytes=True):
    s = unhexlify(base58decode(s))
    dec = hexlify(s[:-4]).decode('ascii')
    checksum = doublesha256(dec)[:4]
    if not (s[-4:] == checksum):
        raise AssertionError()
    if skip_first_bytes:
        return dec[2:]
    else:
        return dec


def gphBase58CheckEncode(s):
    checksum = ripemd160(s)[:4]
    result = s + hexlify(checksum).decode('ascii')
    return base58encode(result)


def gphBase58CheckDecode(s):
    s = unhexlify(base58decode(s))
    dec = hexlify(s[:-4]).decode('ascii')
    checksum = ripemd160(dec)[:4]
    if not (s[-4:] == checksum):
        raise AssertionError()
    return dec
