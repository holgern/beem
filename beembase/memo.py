# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes, int, str
from beemgraphenebase.py23 import py23_bytes, bytes_types
from beemgraphenebase.base58 import base58encode, base58decode
import sys
import hashlib
from binascii import hexlify, unhexlify
try:
    from Cryptodome.Cipher import AES
except ImportError:
    try:
        from Crypto.Cipher import AES
    except ImportError:
        raise ImportError("Missing dependency: pyCryptodome")
from .account import PrivateKey, PublicKey
from .objects import Memo
import struct
default_prefix = "STM"


def get_shared_secret(priv, pub):
    """ Derive the share secret between ``priv`` and ``pub``

        :param `Base58` priv: Private Key
        :param `Base58` pub: Public Key
        :return: Shared secret
        :rtype: hex

        The shared secret is generated such that::

            Pub(Alice) * Priv(Bob) = Pub(Bob) * Priv(Alice)

    """
    pub_point = pub.point()
    priv_point = int(repr(priv), 16)
    res = pub_point * priv_point
    res_hex = '%032x' % res.x()
    # Zero padding
    res_hex = '0' * (64 - len(res_hex)) + res_hex
    return res_hex


def init_aes_bts(shared_secret, nonce):
    """ Initialize AES instance

        :param hex shared_secret: Shared Secret to use as encryption key
        :param int nonce: Random nonce
        :return: AES instance
        :rtype: AES

    """
    # Shared Secret
    ss = hashlib.sha512(unhexlify(shared_secret)).digest()
    # Seed
    seed = py23_bytes(str(nonce), 'ascii') + hexlify(ss)
    seed_digest = hexlify(hashlib.sha512(seed).digest()).decode('ascii')
    # Check'sum'
    check = hashlib.sha256(unhexlify(seed_digest)).digest()
    check = struct.unpack_from("<I", check[:4])[0]
    # AES
    key = unhexlify(seed_digest[0:64])
    iv = unhexlify(seed_digest[64:96])
    return AES.new(key, AES.MODE_CBC, iv)


def init_aes(shared_secret, nonce):
    """ Initialize AES instance
        :param hex shared_secret: Shared Secret to use as encryption key
        :param int nonce: Random nonce
        :return: AES instance and checksum of the encryption key
        :rtype: length 2 tuple
    """
    shared_secret = hashlib.sha512(unhexlify(shared_secret)).hexdigest()
    # Seed
    ss = unhexlify(shared_secret)
    n = struct.pack("<Q", int(nonce))
    encryption_key = hashlib.sha512(n + ss).hexdigest()
    # Check'sum'
    check = hashlib.sha256(unhexlify(encryption_key)).digest()
    check = struct.unpack_from("<I", check[:4])[0]
    # AES
    key = unhexlify(encryption_key[0:64])
    iv = unhexlify(encryption_key[64:96])
    return AES.new(key, AES.MODE_CBC, iv), check


def _pad(s, BS):
    numBytes = (BS - len(s) % BS)
    return s + numBytes * struct.pack('B', numBytes)


def _unpad(s, BS):
    count = int(struct.unpack('B', py23_bytes(s[-1], 'ascii'))[0])
    if py23_bytes(s[-count::], 'ascii') == count * struct.pack('B', count):
        return s[:-count]
    return s


def encode_memo_bts(priv, pub, nonce, message):
    """ Encode a message with a shared secret between Alice and Bob

        :param PrivateKey priv: Private Key (of Alice)
        :param PublicKey pub: Public Key (of Bob)
        :param int nonce: Random nonce
        :param str message: Memo message
        :return: Encrypted message
        :rtype: hex

    """
    shared_secret = get_shared_secret(priv, pub)
    aes = init_aes_bts(shared_secret, nonce)
    # Checksum
    raw = py23_bytes(message, 'utf8')
    checksum = hashlib.sha256(raw).digest()
    raw = (checksum[0:4] + raw)
    # Padding
    BS = 16
    # FIXME: this adds 16 bytes even if not required
    if len(raw) % BS:
        raw = _pad(raw, BS)
    # Encryption
    return hexlify(aes.encrypt(raw)).decode('ascii')


def decode_memo_bts(priv, pub, nonce, message):
    """ Decode a message with a shared secret between Alice and Bob

        :param PrivateKey priv: Private Key (of Bob)
        :param PublicKey pub: Public Key (of Alice)
        :param int nonce: Nonce used for Encryption
        :param bytes message: Encrypted Memo message
        :return: Decrypted message
        :rtype: str
        :raise ValueError: if message cannot be decoded as valid UTF-8
               string

    """
    shared_secret = get_shared_secret(priv, pub)
    aes = init_aes_bts(shared_secret, nonce)
    # Encryption
    raw = py23_bytes(message, 'ascii')
    cleartext = aes.decrypt(unhexlify(raw))
    # TODO, verify checksum
    message = cleartext[4:]
    try:
        return _unpad(message.decode('utf8'), 16)
    except Exception:
        raise ValueError(message)


def encode_memo(priv, pub, nonce, message, **kwargs):
    """ Encode a message with a shared secret between Alice and Bob
        :param PrivateKey priv: Private Key (of Alice)
        :param PublicKey pub: Public Key (of Bob)
        :param int nonce: Random nonce
        :param str message: Memo message
        :return: Encrypted message
        :rtype: hex
    """
    shared_secret = get_shared_secret(priv, pub)

    aes, check = init_aes(shared_secret, nonce)
    raw = py23_bytes(message, 'utf8')
    # Padding
    BS = 16
    if len(raw) % BS:
        raw = _pad(raw, BS)
    # Encryption
    cipher = hexlify(aes.encrypt(raw)).decode('ascii')
    prefix = kwargs.pop("prefix", default_prefix)
    s = {
        "from": format(priv.pubkey, prefix),
        "to": format(pub, prefix),
        "nonce": nonce,
        "check": check,
        "encrypted": cipher,
        "prefix": prefix
    }
    tx = Memo(**s)
    return "#" + base58encode(hexlify(py23_bytes(tx)).decode("ascii"))


def decode_memo(priv, message):
    """ Decode a message with a shared secret between Alice and Bob
        :param PrivateKey priv: Private Key (of Bob)
        :param base58encoded message: Encrypted Memo message
        :return: Decrypted message
        :rtype: str
        :raise ValueError: if message cannot be decoded as valid UTF-8
               string
    """
    # decode structure
    raw = base58decode(message[1:])
    from_key = PublicKey(raw[:66])
    raw = raw[66:]
    to_key = PublicKey(raw[:66])
    raw = raw[66:]
    nonce = str(struct.unpack_from("<Q", unhexlify(raw[:16]))[0])
    raw = raw[16:]
    check = struct.unpack_from("<I", unhexlify(raw[:8]))[0]
    raw = raw[8:]
    cipher = raw

    if repr(to_key) == repr(priv.pubkey):
        shared_secret = get_shared_secret(priv, from_key)
    elif repr(from_key) == repr(priv.pubkey):
        shared_secret = get_shared_secret(priv, to_key)
    else:
        raise ValueError("Incorrect PrivateKey")

    # Init encryption
    aes, checksum = init_aes(shared_secret, nonce)

    # Check
    if not check == checksum:
        raise AssertionError("Checksum failure")

    # Encryption
    # remove the varint prefix (FIXME, long messages!)
    message = cipher[2:]
    message = aes.decrypt(unhexlify(py23_bytes(message, 'ascii')))
    try:
        return _unpad(message.decode('utf8'), 16)
    except:  # noqa FIXME(sneak)
        raise ValueError(message)
