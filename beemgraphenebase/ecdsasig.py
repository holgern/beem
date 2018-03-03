from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes, str
from builtins import chr
from builtins import range
import sys
import time
import ecdsa
import hashlib
import struct
import logging
from .account import PrivateKey
from .py23 import py23_bytes, bytes_types
log = logging.getLogger(__name__)

try:
    import secp256k1
    USE_SECP256K1 = True
    log.debug("Loaded secp256k1 binding.")
except Exception:
    USE_SECP256K1 = False
    log.debug("To speed up transactions signing install \n"
              "    pip install secp256k1")


def _is_canonical(sig):
    sig = bytearray(sig)
    return (not (int(sig[0]) & 0x80) and
            not (sig[0] == 0 and not (int(sig[1]) & 0x80)) and
            not (int(sig[32]) & 0x80) and
            not (sig[32] == 0 and not (int(sig[33]) & 0x80)))


def compressedPubkey(pk):
    order = pk.curve.generator.order()
    p = pk.pubkey.point
    x_str = ecdsa.util.number_to_string(p.x(), order)
    return py23_bytes(chr(2 + (p.y() & 1)), 'ascii') + x_str


def recover_public_key(digest, signature, i):
    """ Recover the public key from the the signature
    """
    # See http: //www.secg.org/download/aid-780/sec1-v2.pdf section 4.1.6 primarily
    curve = ecdsa.SECP256k1.curve
    G = ecdsa.SECP256k1.generator
    order = ecdsa.SECP256k1.order
    yp = (i % 2)
    r, s = ecdsa.util.sigdecode_string(signature, order)
    # 1.1
    x = r + (i // 2) * order
    # 1.3. This actually calculates for either effectively 02||X or 03||X depending on 'k' instead of always for 02||X as specified.
    # This substitutes for the lack of reversing R later on. -R actually is defined to be just flipping the y-coordinate in the elliptic curve.
    alpha = ((x * x * x) + (curve.a() * x) + curve.b()) % curve.p()
    beta = ecdsa.numbertheory.square_root_mod_prime(alpha, curve.p())
    y = beta if (beta - yp) % 2 == 0 else curve.p() - beta
    # 1.4 Constructor of Point is supposed to check if nR is at infinity.
    R = ecdsa.ellipticcurve.Point(curve, x, y, order)
    # 1.5 Compute e
    e = ecdsa.util.string_to_number(digest)
    # 1.6 Compute Q = r^-1(sR - eG)
    Q = ecdsa.numbertheory.inverse_mod(r, order) * (s * R + (-e % order) * G)
    # Not strictly necessary, but let's verify the message for paranoia's sake.
    if not ecdsa.VerifyingKey.from_public_point(Q, curve=ecdsa.SECP256k1).verify_digest(signature, digest, sigdecode=ecdsa.util.sigdecode_string):
        return None
    return ecdsa.VerifyingKey.from_public_point(Q, curve=ecdsa.SECP256k1)


def recoverPubkeyParameter(message, digest, signature, pubkey):
    """ Use to derive a number that allows to easily recover the
        public key from the signature
    """
    for i in range(0, 4):
        if USE_SECP256K1:
            sig = pubkey.ecdsa_recoverable_deserialize(signature, i)
            p = secp256k1.PublicKey(pubkey.ecdsa_recover(message, sig))
            if p.serialize() == pubkey.serialize():
                return i
        else:
            p = recover_public_key(digest, signature, i)
            if (p.to_string() == pubkey.to_string() or
                    compressedPubkey(p) == pubkey.to_string()):
                return i
    return None


def sign_message(message, wif, hashfn=hashlib.sha256):
    """ Sign a digest with a wif key

        :param str wif: Private key in
    """

    if not isinstance(message, bytes_types):
        message = py23_bytes(message, "utf-8")

    digest = hashfn(message).digest()
    p = py23_bytes(PrivateKey(wif))

    if USE_SECP256K1:
        ndata = secp256k1.ffi.new("const int *ndata")
        ndata[0] = 0
        while True:
            ndata[0] += 1
            privkey = secp256k1.PrivateKey(p, raw=True)
            sig = secp256k1.ffi.new('secp256k1_ecdsa_recoverable_signature *')
            signed = secp256k1.lib.secp256k1_ecdsa_sign_recoverable(
                privkey.ctx,
                sig,
                digest,
                privkey.private_key,
                secp256k1.ffi.NULL,
                ndata
            )
            if not signed == 1:
                raise AssertionError()
            signature, i = privkey.ecdsa_recoverable_serialize(sig)
            if _is_canonical(signature):
                i += 4   # compressed
                i += 27  # compact
                break
    else:
        cnt = 0
        sk = ecdsa.SigningKey.from_string(p, curve=ecdsa.SECP256k1)
        while 1:
            cnt += 1
            if not cnt % 20:
                log.info("Still searching for a canonical signature. Tried %d times already!" % cnt)

            # Deterministic k
            #
            k = ecdsa.rfc6979.generate_k(
                sk.curve.generator.order(),
                sk.privkey.secret_multiplier,
                hashlib.sha256,
                hashlib.sha256(
                    digest +
                    struct.pack("d", time.time())  # use the local time to randomize the signature
                ).digest())

            # Sign message
            #
            sigder = sk.sign_digest(
                digest,
                sigencode=ecdsa.util.sigencode_der,
                k=k)

            # Reformating of signature
            #
            r, s = ecdsa.util.sigdecode_der(sigder, sk.curve.generator.order())
            signature = ecdsa.util.sigencode_string(r, s, sk.curve.generator.order())

            # Make sure signature is canonical!
            #
            sigder = bytearray(sigder)
            lenR = sigder[3]
            lenS = sigder[5 + lenR]
            if lenR is 32 and lenS is 32:
                # Derive the recovery parameter
                #
                i = recoverPubkeyParameter(
                    message, digest, signature, sk.get_verifying_key())
                i += 4   # compressed
                i += 27  # compact
                break

    # pack signature
    #
    sigstr = struct.pack("<B", i)
    sigstr += signature

    return sigstr


def verify_message(message, signature, hashfn=hashlib.sha256):
    if not isinstance(message, bytes_types):
        message = py23_bytes(message, "utf-8")
    if not isinstance(signature, bytes_types):
        signature = py23_bytes(signature, "utf-8")
    if not isinstance(message, bytes_types):
        raise AssertionError()
    if not isinstance(signature, bytes_types):
        raise AssertionError()
    digest = hashfn(message).digest()
    sig = signature[1:]
    recoverParameter = bytearray(signature)[0] - 4 - 27  # recover parameter only

    if USE_SECP256K1:
        ALL_FLAGS = secp256k1.lib.SECP256K1_CONTEXT_VERIFY | secp256k1.lib.SECP256K1_CONTEXT_SIGN
        # Placeholder
        pub = secp256k1.PublicKey(flags=ALL_FLAGS)
        # Recover raw signature
        sig = pub.ecdsa_recoverable_deserialize(sig, recoverParameter)
        # Recover PublicKey
        verifyPub = secp256k1.PublicKey(pub.ecdsa_recover(message, sig))
        # Convert recoverable sig to normal sig
        normalSig = verifyPub.ecdsa_recoverable_convert(sig)
        # Verify
        verifyPub.ecdsa_verify(message, normalSig)
        phex = verifyPub.serialize(compressed=True)
    else:
        p = recover_public_key(digest, sig, recoverParameter)
        # Will throw an exception of not valid
        p.verify_digest(
            sig,
            digest,
            sigdecode=ecdsa.util.sigdecode_string
        )
        phex = compressedPubkey(p)

    return phex
