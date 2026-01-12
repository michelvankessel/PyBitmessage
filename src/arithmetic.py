"""
Arithmetic Expressions
"""

import hashlib
import re

# Try pycryptodome first for RIPEMD160 (works on all OpenSSL versions)
try:
    from Crypto.Hash import RIPEMD160 as _RIPEMD160  # nosec B413

    def _ripemd160(data: bytes) -> bytes:
        """RIPEMD160 hash using pycryptodome (works on OpenSSL 3)"""
        return _RIPEMD160.new(data).digest()

except ImportError:
    # Fallback to hashlib (may fail on OpenSSL 3)
    def _ripemd160(data: bytes) -> bytes:
        """RIPEMD160 hash using hashlib (requires OpenSSL with RIPEMD160)"""
        return hashlib.new("ripemd160", data).digest()


P = 2**256 - 2**32 - 2**9 - 2**8 - 2**7 - 2**6 - 2**4 - 1
A = 0
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
G = (Gx, Gy)


def inv(a, n):
    """Inversion"""
    lm, hm = 1, 0
    low, high = a % n, n
    while low > 1:
        r = high // low
        nm, new = hm - lm * r, high - low * r
        lm, low, hm, high = nm, new, lm, low
    return lm % n


def get_code_string(base):
    """Returns string according to base value"""
    if base == 2:
        return b"01"
    if base == 10:
        return b"0123456789"
    if base == 16:
        return b"0123456789abcdef"
    if base == 58:
        return b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    if base == 256:
        return bytes(range(256))

    raise ValueError("Invalid base!")


def encode(val, base, minlen=0):
    """Returns the encoded string"""
    code_string = get_code_string(base)
    result = b""
    while val > 0:
        val, i = divmod(val, base)
        result = code_string[i:i + 1] + result
    if len(result) < minlen:
        result = code_string[0:1] * (minlen - len(result)) + result
    return result


def decode(string, base):
    """Returns the decoded string"""
    if isinstance(string, str):
        string = string.encode("ascii")
    code_string = get_code_string(base)
    result = 0
    if base == 16:
        string = string.lower()
    for char in string:
        result *= base
        result += code_string.find(char)
    return result


def changebase(string, frm, to, minlen=0):
    """Change base of the string"""
    return encode(decode(string, frm), to, minlen)


def base10_add(a, b):
    """Adding the numbers that are of base10"""

    if a is None:
        return b[0], b[1]
    if b is None:
        return a[0], a[1]
    if a[0] == b[0]:
        if a[1] == b[1]:
            return base10_double(a[0], a[1])
        return None
    m = ((b[1] - a[1]) * inv(b[0] - a[0], P)) % P
    x = (m * m - a[0] - b[0]) % P
    y = (m * (a[0] - x) - a[1]) % P
    return (x, y)


def base10_double(a):
    """Double the numbers that are of base10"""
    if a is None:
        return None
    m = ((3 * a[0] * a[0] + A) * inv(2 * a[1], P)) % P
    x = (m * m - 2 * a[0]) % P
    y = (m * (a[0] - x) - a[1]) % P
    return (x, y)


def base10_multiply(a, n):
    """Multiply the numbers that are of base10"""
    if n == 0:
        return G
    if n == 1:
        return a
    n, m = divmod(n, 2)
    if m == 0:
        return base10_double(base10_multiply(a, n))
    if m == 1:
        return base10_add(base10_double(base10_multiply(a, n)), a)
    return None


def hex_to_point(h):
    """Converting hexadecimal to point value"""
    return (decode(h[2:66], 16), decode(h[66:], 16))


def point_to_hex(p):
    """Converting point value to hexadecimal"""
    return b"04" + encode(p[0], 16, 64) + encode(p[1], 16, 64)


def multiply(privkey, pubkey):
    """Multiplying keys"""
    return point_to_hex(base10_multiply(hex_to_point(pubkey), decode(privkey, 16)))


def privtopub(privkey):
    """Converting key from private to public"""
    return point_to_hex(base10_multiply(G, decode(privkey, 16)))


def add(p1, p2):
    """Adding two public keys"""
    if len(p1) == 32:
        return encode(decode(p1, 16) + decode(p2, 16) % P, 16, 32)
    return point_to_hex(base10_add(hex_to_point(p1), hex_to_point(p2)))


def hash_160(string):
    """Hashed version of public key"""
    intermed = hashlib.sha256(string).digest()
    return _ripemd160(intermed)


def dbl_sha256(string):
    """Double hashing (SHA256)"""
    return hashlib.sha256(hashlib.sha256(string).digest()).digest()


def bin_to_b58check(inp, magicbyte=0):
    """Convert binary to base58check"""
    if isinstance(inp, str):
        inp = inp.encode("latin1")
    inp_fmtd = bytes([magicbyte]) + inp
    leadingzbytes = len(re.match(b"^\x00*", inp_fmtd).group(0))
    checksum = dbl_sha256(inp_fmtd)[:4]
    return "1" * leadingzbytes + changebase(inp_fmtd + checksum, 256, 58).decode()


def b58check_to_bin(inp, magicbyte=None, validate_checksum=False):
    """Convert base58check to binary

    Args:
        inp: Base58check encoded string
        magicbyte: Expected magic byte (optional)
        validate_checksum: If True, validate checksum (default: False for compatibility)
    """
    if isinstance(inp, str):
        inp = inp.encode("ascii")
    leadingzbytes = 0
    for b in inp:
        if b == 49:  # ord('1')
            leadingzbytes += 1
        else:
            break
    data = b"\x00" * leadingzbytes + changebase(inp, 58, 256)
    if validate_checksum and dbl_sha256(data[:-4])[:4] != data[-4:]:
        raise ValueError("Invalid checksum")
    if magicbyte is not None and data[0] != magicbyte:
        raise ValueError("Invalid magic byte")
    return data[1:-4]


def pubkey_to_address(pubkey):
    """Convert a public key (in hex) to a Bitcoin address"""
    return bin_to_b58check(hash_160(changebase(pubkey, 16, 256)))
