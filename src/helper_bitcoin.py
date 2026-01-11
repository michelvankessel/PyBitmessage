"""
Calculates bitcoin and testnet address from pubkey
"""

import hashlib

from debug import logger
import arithmetic

# Try pycryptodome first for RIPEMD160 (works on all OpenSSL versions)
try:
    from Crypto.Hash import RIPEMD160 as _RIPEMD160

    def _ripemd160(data: bytes) -> bytes:
        """RIPEMD160 hash using pycryptodome (works on OpenSSL 3)"""
        return _RIPEMD160.new(data).digest()

except ImportError:
    # Fallback to hashlib (may fail on OpenSSL 3)
    def _ripemd160(data: bytes) -> bytes:
        """RIPEMD160 hash using hashlib (requires OpenSSL with RIPEMD160)"""
        return hashlib.new("ripemd160", data).digest()


def calculateBitcoinAddressFromPubkey(pubkey):
    """Calculate bitcoin address from given pubkey (65 bytes long hex string)"""
    if len(pubkey) != 65:
        logger.error(
            "Could not calculate Bitcoin address from pubkey because"
            " function was passed a pubkey that was"
            " %i bytes long rather than 65.",
            len(pubkey),
        )
        return "error"
    sha = hashlib.new("sha256")
    sha.update(pubkey)
    ripe = _ripemd160(sha.digest())
    ripeWithProdnetPrefix = b"\x00" + ripe

    checksum = hashlib.sha256(hashlib.sha256(ripeWithProdnetPrefix).digest()).digest()[
        :4
    ]
    binaryBitcoinAddress = ripeWithProdnetPrefix + checksum
    numberOfZeroBytesOnBinaryBitcoinAddress = 0
    while binaryBitcoinAddress[0:1] == b"\x00":
        numberOfZeroBytesOnBinaryBitcoinAddress += 1
        binaryBitcoinAddress = binaryBitcoinAddress[1:]
    base58encoded = arithmetic.changebase(binaryBitcoinAddress, 256, 58)
    return "1" * numberOfZeroBytesOnBinaryBitcoinAddress + base58encoded


def calculateTestnetAddressFromPubkey(pubkey):
    """This function expects that pubkey begin with the testnet prefix"""
    if len(pubkey) != 65:
        logger.error(
            "Could not calculate Bitcoin address from pubkey because"
            " function was passed a pubkey that was"
            " %i bytes long rather than 65.",
            len(pubkey),
        )
        return "error"
    sha = hashlib.new("sha256")
    sha.update(pubkey)
    ripe = _ripemd160(sha.digest())
    ripeWithProdnetPrefix = b"\x6f" + ripe

    checksum = hashlib.sha256(hashlib.sha256(ripeWithProdnetPrefix).digest()).digest()[
        :4
    ]
    binaryBitcoinAddress = ripeWithProdnetPrefix + checksum
    numberOfZeroBytesOnBinaryBitcoinAddress = 0
    while binaryBitcoinAddress[0:1] == b"\x00":
        numberOfZeroBytesOnBinaryBitcoinAddress += 1
        binaryBitcoinAddress = binaryBitcoinAddress[1:]
    base58encoded = arithmetic.changebase(binaryBitcoinAddress, 256, 58)
    return "1" * numberOfZeroBytesOnBinaryBitcoinAddress + base58encoded
