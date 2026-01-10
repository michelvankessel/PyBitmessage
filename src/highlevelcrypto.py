"""
High level cryptographic functions based on OpenSSL/cryptography.

.. note::
  Upstream pyelliptic was upgraded from SHA1 to SHA256 for signing. We must
  upgrade PyBitmessage gracefully.
"""

import hashlib
import logging
import os
from binascii import hexlify

from Crypto.Hash import RIPEMD160 as RIPEMD160Hash
import arithmetic as a

logger = logging.getLogger('default')


try:
    from cryptography.hazmat.primitives import hashes, hmac, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


__all__ = [
    "calculateInventoryHash",
    "decodeWalletImportFormat",
    "deterministic_keys",
    "decrypt",
    "decryptFast",
    "double_sha512",
    "encodeWalletImportFormat",
    "encrypt",
    "hexToPubkey",
    "makeCryptor",
    "makePubCryptor",
    "pointMult",
    "random_keys",
    "randomBytes",
    "sign",
    "to_ripe",
    "verify",
    "HAS_CRYPTOGRAPHY",
]


# WIF (uses arithmetic):


def decodeWalletImportFormat(WIFstring):
    """
    Decodes WIF string. Returns the raw private key bytes.
    """
    if isinstance(WIFstring, bytes):
        WIFstring = WIFstring.decode('ascii')
    try:
        privkey_bin = a.b58check_to_bin(WIFstring, 128)
    except Exception:
        # Maybe it's not b58check?
        privkey_bin = a.changebase(WIFstring, 58, 256)
    if len(privkey_bin) == 33 and privkey_bin[-1] == 1:
        # compressed
        return privkey_bin[:-1]
    return privkey_bin


def encodeWalletImportFormat(privkey):
    """
    Encodes hex private key into WIF.
    """
    if len(privkey) == 32:
        return a.bin_to_b58check(privkey, 128)
    return a.bin_to_b58check(a.changebase(privkey, 16, 256, minlen=32), 128)


# Keys


def random_keys():
    """Generates random keys. Returns (privkey, pubkey) in binary"""
    if not HAS_CRYPTOGRAPHY:
        raise ImportError("cryptography library is required")
    priv = ec.generate_private_key(ec.SECP256K1(), default_backend())
    pub = priv.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    # Bitmessage expects privkey in secret bytes format
    priv_bytes = priv.private_numbers().private_value.to_bytes(32, 'big')
    return priv_bytes, pub


def deterministic_keys(seed, nonce):
    """Generates deterministic keys from seed and nonce"""
    payload = seed + a.encode(int.from_bytes(nonce, 'big'), 256)
    privkey = hashlib.sha512(payload).digest()[:32]
    return privkey, pointMult(privkey)


def randomBytes(n):
    """Get n random bytes"""
    return os.urandom(n)


# Hashes


def double_sha512(data):
    """Double SHA512 hash"""
    return hashlib.sha512(hashlib.sha512(data).digest()).digest()


def calculateInventoryHash(data):
    """Calculate Bitmessage inventory hash (double SHA512, then first 32 bytes)"""
    return double_sha512(data)[:32]


def _bm160(data):
    """Bitmessage 160-bit hash: RIPEMD160(SHA512(data))"""
    h = hashlib.sha512(data).digest()
    return RIPEMD160Hash.new(h).digest()


def to_ripe(signing_key, encryption_key):
    """Converts a pair of public keys into a RIPE hash"""
    return _bm160(signing_key + encryption_key)


def hexToPubkey(pubkey):
    """Converts hex public key into binary pyelliptic high-level format"""
    pubkey_raw = a.changebase(pubkey[2:], 16, 256, minlen=64)
    return b"\x02\xca\x00 " + pubkey_raw[:32] + b"\x00 " + pubkey_raw[32:]


def privToPub(privkey):
    """Converts hex private key into hex public key"""
    private_key = a.changebase(privkey, 16, 256, minlen=32)
    public_key = pointMult(private_key)
    return hexlify(public_key)


def pointMult(secret):
    """
    Does an EC point multiplication; turns a private key into a public key.
    """
    if not HAS_CRYPTOGRAPHY:
        raise ImportError("cryptography library is required")

    priv = ec.derive_private_key(
        int.from_bytes(secret, 'big'), ec.SECP256K1(), default_backend()
    )
    # cryptography's public_bytes for uncompressed point (0x04 prefix)
    return priv.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )


class CryptographyECC:
    """A compatibility layer for pyelliptic.ECC using the cryptography library"""
    def __init__(self, pubkey=None, raw_privkey=None, curve="secp256k1"):
        if curve != "secp256k1":
            raise ValueError("Only secp256k1 is supported currently")
        self.curve = ec.SECP256K1()
        self.private_key = None
        self.public_key = None
        if raw_privkey:
            self.private_key = ec.derive_private_key(
                int.from_bytes(raw_privkey, 'big'), self.curve, default_backend()
            )
            self.public_key = self.private_key.public_key()
        if pubkey:
            # pubkey can be in multiple formats
            if len(pubkey) == 70 and pubkey.startswith(b"\x02\xca\x00 "):
                # pyelliptic high-level format
                x = pubkey[4:36]
                y = pubkey[38:70]
                self.public_key = ec.EllipticCurvePublicNumbers(
                    int.from_bytes(x, 'big'),
                    int.from_bytes(y, 'big'),
                    self.curve
                ).public_key(default_backend())
            else:
                # assume raw X9.62 format (0x04 + x + y)
                self.public_key = ec.EllipticCurvePublicKey.from_encoded_point(
                    self.curve, pubkey
                )

    def encrypt(self, data, pubkey_bin):
        # pyelliptic style ECIES
        # 1. Ephemeral key
        ephem_priv = ec.generate_private_key(self.curve, default_backend())
        ephem_pub = ephem_priv.public_key()

        # 2. Recipient public key
        if len(pubkey_bin) == 70 and pubkey_bin.startswith(b"\x02\xca\x00 "):
            x = pubkey_bin[4:36]
            y = pubkey_bin[38:70]
            recipient_pub = ec.EllipticCurvePublicNumbers(
                int.from_bytes(x, 'big'),
                int.from_bytes(y, 'big'),
                self.curve
            ).public_key(default_backend())
        else:
            recipient_pub = ec.EllipticCurvePublicKey.from_encoded_point(
                self.curve, pubkey_bin
            )

        # 3. ECDH
        shared_secret = ephem_priv.exchange(ec.ECDH(), recipient_pub)

        # 4. KDF (SHA512)
        digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
        digest.update(shared_secret)
        key_material = digest.finalize()
        key_e, key_m = key_material[:32], key_material[32:]

        # 5. IV
        iv = os.urandom(16)

        # 6. AES-256-CBC Encrypt
        cipher = Cipher(algorithms.AES(key_e), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        from cryptography.hazmat.primitives import padding
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        # 7. Construct Result
        # Ephemeral pubkey in pyelliptic format
        pub_numbers = ephem_pub.public_numbers()
        x_bytes = pub_numbers.x.to_bytes(32, 'big')
        y_bytes = pub_numbers.y.to_bytes(32, 'big')
        ephem_pub_bin = b"\x02\xca\x00 " + x_bytes + b"\x00 " + y_bytes

        payload = iv + ephem_pub_bin + ciphertext

        # 8. HMAC-SHA256
        h = hmac.HMAC(key_m, hashes.SHA256(), backend=default_backend())
        h.update(payload)
        mac = h.finalize()

        return payload + mac

    def decrypt(self, data, hmac_prefix=b""):
        if not self.private_key:
            raise ValueError("Private key required for decryption")

        if len(data) < 70:
            # Minimal length check to prevent "Invalid EC key" on short/symmetric messages
            return b""

        # 1. Extract parts
        # pyelliptic format: iv(16) + pubkey(70) + ciphertext + mac(32)
        iv = data[:16]
        # 2. Decode Ephemeral Pubkey
        ephem_pub = None
        pub_len = 0
        is_legacy = False

        # Check for PyElliptic Legacy (02 CA ...) vs SEC (02/03/04 ...)
        # PyElliptic: 02 CA (2 bytes header for X)
        if len(data) > 17 and data[16] == 0x02 and data[17] == 0xCA:
            is_legacy = True

        if not is_legacy:
            try:
                # Try to use modern cryptography method
                # This handles 04 (uncompressed), 02/03 (compressed), and validates points
                header_byte = data[16]
                if header_byte == 0x04:
                    length = 65
                elif header_byte in (0x02, 0x03):
                    length = 33
                else:
                    length = 0

                if length > 0:
                    ephem_bytes = data[16:16 + length]
                    # This method was added in cryptography 2.5
                    ephem_pub = ec.EllipticCurvePublicKey.from_encoded_point(self.curve, ephem_bytes)
                    pub_len = length  # Only set pub_len if parsing succeeds
            except (ValueError, AttributeError):
                # Fallback if invalid point or method missing
                is_legacy = True

        if is_legacy or not ephem_pub:
            # PyElliptic / Bitmessage legacy: 02 CA 00 20 + X(32) + 00 20 + Y(32) = 70 bytes
            pub_len = 70
            ephem_pub_bin = data[16:86]
            x = ephem_pub_bin[4:36]
            y = ephem_pub_bin[38:70]
            ephem_pub = ec.EllipticCurvePublicNumbers(
                int.from_bytes(x, 'big'),
                int.from_bytes(y, 'big'),
                self.curve
            ).public_key(default_backend())

        ciphertext = data[16 + pub_len:-32]
        mac = data[-32:]

        # 3. ECDH
        try:
            shared_secret = self.private_key.exchange(ec.ECDH(), ephem_pub)
        except ValueError:
            return b""

        # 4. KDF (SHA512)
        digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
        digest.update(shared_secret)
        key_material = digest.finalize()
        key_e, key_m = key_material[:32], key_material[32:]

        # 5. Verify MAC
        # Standard scope: IV + EphemPub + Ciphertext
        h_data = data[:-32]

        verified = False
        # Attempt 1: Standard
        h = hmac.HMAC(key_m, hashes.SHA256(), backend=default_backend())
        h.update(h_data)
        try:
            h.verify(mac)
            verified = True
        except Exception:
            # Attempt 2: Full Header (hmac_prefix + data)
            if hmac_prefix:
                h = hmac.HMAC(key_m, hashes.SHA256(), backend=default_backend())
                h.update(hmac_prefix)
                h.update(h_data)
                try:
                    h.verify(mac)
                    verified = True
                    print("DEBUG_DECRYPT: HMAC Verified via FALLBACK (Object Header inclusive).")
                except Exception:
                    pass
            # Attempt 3: Object Header Only (First 20 bytes)
            if hmac_prefix and len(hmac_prefix) > 20:
                h = hmac.HMAC(key_m, hashes.SHA256(), backend=default_backend())
                h.update(hmac_prefix[:20])  # Nonce, Time, Type only
                h.update(h_data)
                try:
                    h.verify(mac)
                    verified = True
                    print("DEBUG_DECRYPT: HMAC Verified via SECOND FALLBACK (Object Header only).")
                except Exception:
                    pass

        if not verified:
            # HMAC verification failed - return empty to allow trying other keys
            return b""

        # 6. AES-256-CBC Decrypt
        cipher = Cipher(algorithms.AES(key_e), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        # 7. Unpad
        from cryptography.hazmat.primitives import padding
        unpadder = padding.PKCS7(128).unpadder()
        try:
            result = unpadder.update(padded_data) + unpadder.finalize()
        except Exception:
            return padded_data

        return result

    def sign(self, data, digest_alg=None):
        if not self.private_key:
            raise ValueError("Private key required for signing")
        if digest_alg == hashes.SHA256:
            alg = hashes.SHA256()
        else:
            alg = hashes.SHA1()
        return self.private_key.sign(data, ec.ECDSA(alg))

    def verify(self, signature, data, digest_alg=None):
        if not self.public_key:
            raise ValueError("Public key required for verification")
        if digest_alg == hashes.SHA256:
            alg = hashes.SHA256()
        else:
            alg = hashes.SHA1()
        try:
            self.public_key.verify(signature, data, ec.ECDSA(alg))
            return True
        except Exception:
            return False


# Encryption


def makeCryptor(privkey, curve="secp256k1"):
    """Return a private CryptographyECC instance"""
    if not HAS_CRYPTOGRAPHY:
        raise ImportError("cryptography library is required")
    # privkey can be:
    # 1. bytes from hexlify() - 64 bytes hex string as bytes
    # 2. str hex - 64 char hex string
    # 3. str WIF - starts with '5', 'K', or 'L'
    if isinstance(privkey, bytes):
        # Hex bytes from shared.py (hexlify returns bytes in Python 3)
        private_key = a.changebase(privkey.decode(), 16, 256, minlen=32)
    elif isinstance(privkey, str) and len(privkey) == 64:
        # Hex string (64 chars = 32 bytes)
        private_key = a.changebase(privkey, 16, 256, minlen=32)
    elif isinstance(privkey, str) and privkey[0] in ('5', 'K', 'L'):
        # WIF format
        private_key = decodeWalletImportFormat(privkey)
    else:
        # Fallback to hex interpretation
        private_key = a.changebase(privkey, 16, 256, minlen=32)
    return CryptographyECC(raw_privkey=private_key, curve=curve)


def makePubCryptor(pubkey):
    """Return a public CryptographyECC instance"""
    if not HAS_CRYPTOGRAPHY:
        raise ImportError("cryptography library is required")
    pubkey_bin = hexToPubkey(pubkey)
    return CryptographyECC(pubkey=pubkey_bin, curve="secp256k1")


def makeSymCryptor(key):
    """Return a SymmetricCryptor instance"""
    if not HAS_CRYPTOGRAPHY:
        raise ImportError("cryptography library is required")
    # key is passed as hex string
    from binascii import unhexlify
    key_bin = unhexlify(key)
    return SymmetricCryptor(key_bin)


class SymmetricCryptor:
    """Handles Symmetric Encryption (AES-CBC + HMAC) using a known secret"""
    def __init__(self, key):
        self.key = key

    def decrypt(self, data, hmac_prefix=b""):
        # Data format: IV + PubKey + Ciphertext + MAC
        # Note: For Symmetric/Tag encryption, there is no Ephemeral Pubkey.
        # But 'data' structure usually includes it?
        # Specification for V4 Pubkey: "IV + EncryptedData".
        # EncryptedData includes MAC?
        # Let's assume standard Bitmessage encryption format (IV + ... + MAC).
        # But WITHOUT Ephemeral Pubkey?
        # My 'CryptographyECC.decrypt' parses IV (16) + EphemPub (Length).
        # If we use `makeSymCryptor` in `class_singleWorker`, we use it for PubKeys.
        # PubKey Payload: IV (16) + ...
        # There is NO Ephemeral Pubkey.
        # So we should validly parse IV at 0-16.
        # And Key Derivation uses SHA512(self.key).
        if not HAS_CRYPTOGRAPHY:
            raise ImportError("cryptography library is required")

        # 1. Parse IV
        iv = data[:16]

        # 2. Key Derivation (SHA512)
        from cryptography.hazmat.primitives import hashes, hmac
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
        digest.update(self.key)
        key_material = digest.finalize()
        key_e, key_m = key_material[:32], key_material[32:]

        # 3. Verify MAC
        # MAC is last 32 bytes
        mac = data[-32:]
        ciphertext = data[16:-32]  # Everything between IV and MAC

        verified = False
        # Attempt 1: Standard
        h = hmac.HMAC(key_m, hashes.SHA256(), backend=default_backend())
        # MAC covers IV + Ciphertext (No Ephem Pubkey)
        h.update(data[:-32])
        try:
            h.verify(mac)
            verified = True
        except Exception:
            # Attempt 2: Full Header (hmac_prefix + data)
            if hmac_prefix:
                h = hmac.HMAC(key_m, hashes.SHA256(), backend=default_backend())
                h.update(hmac_prefix)
                h.update(data[:-32])
                try:
                    h.verify(mac)
                    verified = True
                    logger.info("HMAC Verified (Symmetric) via FALLBACK (Object Header inclusive).")
                except Exception:
                    pass
            # Attempt 3: Object Header Only (First 20 bytes)
            if hmac_prefix and len(hmac_prefix) > 20:
                h = hmac.HMAC(key_m, hashes.SHA256(), backend=default_backend())
                h.update(hmac_prefix[:20])  # Nonce, Time, Type only
                h.update(data[:-32])
                try:
                    h.verify(mac)
                    verified = True
                    print("DEBUG_DECRYPT: HMAC Verified (Symmetric) via SECOND FALLBACK (Object Header only).")
                except Exception:
                    pass

        if not verified:
            print(f"DEBUG_DECRYPT: HMAC Verification FAILED (Symmetric). Prefix: {hexlify(hmac_prefix).decode() if hmac_prefix else 'None'}")
            print("DEBUG_DECRYPT: Strict HMAC Enforcement: Aborting (Bypass Inactive).")
            raise RuntimeError("Fail to verify data (Symmetric)")

        # 4. AES-256-CBC Decrypt
        cipher = Cipher(algorithms.AES(key_e), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        # 5. Unpad
        from cryptography.hazmat.primitives import padding
        unpadder = padding.PKCS7(128).unpadder()
        try:
            result = unpadder.update(padded_data) + unpadder.finalize()
        except Exception:
            return padded_data

        return result


def encrypt(msg, hexPubkey):
    """Encrypts message with hex public key"""
    if not HAS_CRYPTOGRAPHY:
        raise ImportError("cryptography library is required")
    return CryptographyECC(curve="secp256k1").encrypt(msg, hexToPubkey(hexPubkey))


def decrypt(msg, hexPrivkey, hmac_prefix=b""):
    """Decrypts message with hex private key"""
    return makeCryptor(hexPrivkey).decrypt(msg, hmac_prefix=hmac_prefix)


def decryptFast(msg, cryptor, hmac_prefix=b""):
    """Decrypts message with an existing CryptographyECC object"""
    return cryptor.decrypt(msg, hmac_prefix=hmac_prefix)


# Signatures


def _choose_digest_alg(name):
    """Choose digest constant by name"""
    if name not in ("sha1", "sha256"):
        raise ValueError("Unknown digest algorithm %s" % name)
    if not HAS_CRYPTOGRAPHY:
        raise ImportError("cryptography library is required")
    return hashes.SHA256 if name == "sha256" else hashes.SHA1


def sign(msg, hexPrivkey, digestAlg="sha256"):
    """Signs with hex private key"""
    return makeCryptor(hexPrivkey).sign(msg, digest_alg=_choose_digest_alg(digestAlg))


def verify(msg, sig, hexPubkey, digestAlg=None):
    """Verifies with hex public key"""
    if digestAlg is None:
        if verify(msg, sig, hexPubkey, "sha1"):
            return True
        return verify(msg, sig, hexPubkey, "sha256")

    try:
        return makePubCryptor(hexPubkey).verify(
            sig, msg, digest_alg=_choose_digest_alg(digestAlg)
        )
    except Exception:
        return False
