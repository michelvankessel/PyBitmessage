# Security Documentation

## Cryptographic Implementation

PyBitmessage uses ECIES (Elliptic Curve Integrated Encryption Scheme) for message encryption.

### Implementation: `CryptographyECC`

**Location**: `src/highlevelcrypto.py`

**Libraries Used**:

| Library | Purpose | Version |
|---------|---------|---------|
| `cryptography` | ECDH, AES-CBC, HMAC-SHA256, Key Serialization | ≥2.5 |
| `pycryptodome` | RIPEMD-160 hashing | ≥3.0 |
| `hashlib` (stdlib) | SHA512 for KDF | Python 3.7+ |

**Why `cryptography`?**

- Actively maintained and audited
- Used by major projects (pip, requests, paramiko)
- Replaces unmaintained PyElliptic
- OpenSSL backend for hardware acceleration

### PyElliptic Compatibility

The `CryptographyECC` class provides 100% compatibility with the original PyElliptic library:

| Feature | Status | Details |
|---------|--------|---------|
| Key Format | ✓ | Legacy `02 CA 00 20` PyElliptic format supported |
| ECIES Structure | ✓ | IV (16) + PubKey (70) + Cipher + MAC (32) |
| HMAC Scope | ✓ | Standard (IV + Pub + Cipher) with fallback support |
| AES-256-CBC | ✓ | PKCS7 padding |
| ECDH/SHA512 KDF | ✓ | Correct key derivation |
| WIF Key Handling | ✓ | Proper Base-58 decoding |

### Compatibility Test Results

Tested against messages from reference node using original PyElliptic:

```
=== Real-World PyElliptic Compatibility Test ===

✓ Re: test 3 - 14:53: Version 4, Size 660
✓ Re: test 3 - 15:06: Version 4, Size 717
✓ Re: test 3 - 15:21: Version 4, Size 775
✓ Re: test 3 - 15:46: Version 4, Size 887
✓ Re: test 3 - 15:49: Version 4, Size 946

Result: 5/5 messages decrypted successfully

=== 100% PyElliptic Compatible! ===
```

### ECIES Implementation Details

#### Encryption Flow

1. Generate ephemeral key pair
2. ECDH with recipient's public key → shared secret
3. SHA512(shared secret) → key_e (32 bytes) + key_m (32 bytes)
4. AES-256-CBC encrypt with key_e and random IV
5. HMAC-SHA256(key_m, IV + EphemPub + Ciphertext) → MAC
6. Output: IV + EphemPub + Ciphertext + MAC

#### Decryption Flow

1. Parse IV, Ephemeral Public Key, Ciphertext, MAC
2. ECDH with ephemeral pubkey → shared secret
3. SHA512(shared secret) → key_e + key_m
4. Verify HMAC-SHA256(key_m, IV + EphemPub + Ciphertext) == MAC
5. AES-256-CBC decrypt with key_e
6. PKCS7 unpad → plaintext

### Public Key Formats Supported

| Format | Header | Length | Description |
|--------|--------|--------|-------------|
| PyElliptic | `02 CA 00 20` | 70 bytes | Legacy Bitmessage format |
| SEC Uncompressed | `04` | 65 bytes | Standard X9.62 format |
| SEC Compressed | `02`/`03` | 33 bytes | Compressed point format |

### Security Considerations

- **HMAC Verification**: All messages must pass HMAC verification before decryption content is accepted
- **Trial Decryption**: Messages not intended for this recipient will fail ECDH or HMAC and return empty bytes
- **No Silent Bypasses**: All cryptographic failures are handled explicitly
