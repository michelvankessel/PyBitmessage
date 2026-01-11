# PyBitmessage Test Modernization Plan

**Created:** 2026-01-11 | **Status:** In Progress | **Updated:** 2026-01-11

---

## Executive Summary

This document outlines the plan to modernize PyBitmessage's test suite **and production code** to be fully native to:
- **Python 3.13+**
- **PyQt6**
- **Modern cryptography** (no deprecated dependencies)

## Critical Update: pycrypto → pycryptodome

**IMPORTANT:** This is a **production code change**, not just a test fix. The `pycrypto` library is used in production for RIPEMD160.

### What Was Changed

| File | Status | Change |
|------|--------|--------|
| `setup.py` | ✅ Added | Added `pycryptodome` to `install_requires` |
| `helper_bitcoin.py` | ✅ Added | Added `_ripemd160()` helper function |
| `arithmetic.py` | ✅ Added | Added `_ripemd160()` helper function |
| `highlevelcrypto.py` | ✅ No change | Uses `from Crypto.Hash import RIPEMD160` (works with pycryptodome) |
| `depends.py` | ✅ No change | Uses `from Crypto.Hash import RIPEMD160` (works with pycryptodome) |
| `tests/test_crypto.py` | ✅ No change | Uses `from Crypto.Hash import RIPEMD160` (works with pycryptodome) |

### Why This Matters

1. **Security:** `pycrypto` is abandoned since 2013 with no security updates
2. **Python 3.13:** `pycrypto` doesn't support Python 3.13, `pycryptodome` does
3. **OpenSSL 3:** `hashlib.new('ripemd160')` fails on OpenSSL 3; pycryptodome works everywhere
4. **Cross-platform:** Same code works on macOS, Linux (all versions), Windows

### How It Works

```python
# Try pycryptodome first (works everywhere)
try:
    from Crypto.Hash import RIPEMD160 as _RIPEMD160
    def _ripemd160(data: bytes) -> bytes:
        return _RIPEMD160.new(data).digest()
except ImportError:
    # Fallback to hashlib (may fail on OpenSSL 3)
    def _ripemd160(data: bytes) -> bytes:
        return hashlib.new("ripemd160", data).digest()
```

---

## Current Test Status

### Fully Native Tests ✅

| Test File | Status | Notes |
|-----------|--------|-------|
| `test_addresses.py` | ✅ Pass | |
| `test_addressgenerator.py` | ✅ Pass | |
| `test_api_thread.py` | ✅ Pass | |
| `test_config_address.py` | ✅ Pass | |
| `test_config_process.py` | ✅ Pass | |
| `test_helper_inbox.py` | ✅ Pass | |
| `test_helper_sent.py` | ✅ Pass | |
| `test_identicon.py` | ✅ Pass | |
| `test_inventory.py` | ✅ Pass | |
| `test_l10n.py` | ✅ Pass | |
| `test_log.py` | ✅ Pass | |
| `test_logger.py` | ✅ Pass | |
| `test_msg.py` | ✅ Pass | |
| `test_multiqueue.py` | ✅ Pass | |
| `test_network.py` | ✅ Pass | |
| `test_packets.py` | ✅ Pass | |
| `test_process.py` | ✅ Pass | |
| `test_protocol.py` | ✅ Pass | |
| `test_randomtrackingdict.py` | ✅ Pass | |
| `test_shared.py` | ✅ Pass | |
| `test_config.py` | ✅ Pass | |
| `test_helper_sql.py` | ✅ Pass | |
| `test_proofofwork.py::TestProofofworkBase` | ✅ Pass | Basic tests |
| `test_proofofwork.py::TestProofofwork` | ⚠️ Skip | Requires `BITMESSAGE_TEST_POW=1` |
| `test_addressgenerator.py` | ✅ Pass | |
| `test_api.py` | ✅ Pass | |

### Tests Needing Modernization ❌

| Test File | Issue | Severity | Status |
|-----------|-------|----------|--------|
| `test_sqlthread.py` | Skips on Python 3 | 🔴 Critical | **Blocked** - Requires full app initialization |
| `test_crypto.py` | Python 2 ABC syntax | 🟡 Medium | ✅ **FIXED** |
| `test_openclpow.py` | Requires OpenCL GPU | 🟡 Low | Future |
| `test_proofofwork::TestProofofwork` | Extended tests skipped | 🟢 Info | Easy fix |

---

## Priority 0: Critical - BLOCKED

### test_sqlthread.py

**Problem:** Entire test module skips on Python 3 due to legacy `skip_python3()` decorator.

**Initial Attempt:** Removed `skip_python3()` call - test hung.

**Root Cause:** The SQL thread (`class_sqlThread`) requires:
- Full application state initialization (`state.appdata`)
- Config to be loaded (`config.read()`)
- `config_ready` event to be signaled
- SQLite database to be created

These are not set up by the test in isolation.

**Solution Options:**

1. **Rewrite test to use `TestPartialRun`** - Requires significant refactoring
2. **Add proper test setup** - Mock dependencies, set up state/config
3. **Keep as skip for now** - Document as technical debt

**Current Status:** BLOCKED - Requires significant refactoring

**Files to modify:**
- `src/tests/test_sqlthread.py` - Rewrite test setup
- Potentially add mocking for state/config

**Estimated effort:** 8-16 hours (significant test redesign)

---

## Priority 1: Medium - COMPLETED ✅

### test_crypto.py - Python 2 ABC Syntax

**Problem:**
```python
class RIPEMD160TestCase(object):
    __metaclass__ = ABCMeta  # Python 2 syntax, doesn't work in Python 3
```

**Solution:**
```python
class RIPEMD160TestCase(object, metaclass=ABCMeta):  # Python 3 syntax
```

**Files modified:**
- `src/tests/test_crypto.py` (line 42-45)

**Status:** ✅ COMPLETED
**Verification:**
```bash
uv run pytest src/tests/test_crypto.py -v
# Result: 9 passed, 1 skipped (OpenSSL 3 has no RIPEMD160)
```

---

## CRITICAL UPDATE COMPLETED: pycrypto → pycryptodome ✅

**Status:** Completed on 2026-01-11

**What was changed:**

| File | Change | Status |
|------|--------|--------|
| `setup.py` | Added `pycryptodome` to `install_requires` | ✅ Changed |
| `helper_bitcoin.py` | Added `_ripemd160()` helper with pycryptodome fallback | ✅ Changed |
| `arithmetic.py` | Added `_ripemd160()` helper with pycryptodome fallback | ✅ Changed |
| `highlevelcrypto.py` | No change needed (pycryptodome provides `Crypto` namespace) | ✅ Verified |
| `depends.py` | No change needed (pycryptodome provides `Crypto` namespace) | ✅ Verified |
| `tests/test_crypto.py` | No change needed (pycryptodome provides `Crypto` namespace) | ✅ Verified |

**Key Insight:** `pycryptodome` is a **drop-in replacement** for `pycrypto`. It provides the same `Crypto` namespace, so imports like `from Crypto.Hash import RIPEMD160` work without modification.

**Why this matters:**
- `pycrypto` is abandoned since 2013 (no Python 3.13 support)
- `pycryptodome` is actively maintained with Python 3.13 support
- Fixes RIPEMD160 on OpenSSL 3 systems (no longer requires OpenSSL RIPEMD160)

**Verification:**
```bash
uv run pytest src/tests/test_crypto.py -v
# Result: 9 passed, 1 skipped (OpenSSL 3 has no RIPEMD160)
```

---

## Priority 2: Critical Bug - FIXED ✅

### helper_bitcoin.py & arithmetic.py - RIPEMD160 on OpenSSL 3

**Problem:**
```python
# Old code - fails on OpenSSL 3
ripe = hashlib.new('ripemd160')  # Uses OpenSSL - FAILS on OpenSSL 3
```

**Root Cause:** OpenSSL 3.0+ removed RIPEMD160 from the default build. Code using `hashlib.new('ripemd160')` fails on modern Linux systems.

**Affected Files:**
- `src/helper_bitcoin.py:18,42` - Bitcoin/Testnet address calculation
- `src/arithmetic.py:144` - Hash 160 function

**Solution:**
```python
# Try pycryptodome first for RIPEMD160 (works on all OpenSSL versions)
try:
    from Crypto.Hash import RIPEMD160 as _RIPEMD160
    def _ripemd160(data: bytes) -> bytes:
        return _RIPEMD160.new(data).digest()
except ImportError:
    # Fallback to hashlib (may fail on OpenSSL 3)
    def _ripemd160(data: bytes) -> bytes:
        return hashlib.new("ripemd160", data).digest()
```

**Files Modified:**
- `src/helper_bitcoin.py` (lines 10-22)
- `src/arithmetic.py` (lines 7-20)

**Status:** ✅ FIXED
**Verification:**
```bash
uv run pytest src/tests/test_crypto.py -v
# Result: 9 passed, 1 skipped

python3 -c "from pybitmessage import arithmetic; print(arithmetic.hash_160(b'test').hex())"
# Result: 2091fb1b9b6f25de1e430a5188348aa741233493
```

---

## Priority 3: Easy - Quick Win

### test_proofofwork.py Extended Tests

**Problem:** Extended proof-of-work tests are skipped by default.

**Current status:**
```python
@unittest.skipUnless(
    os.getenv('BITMESSAGE_TEST_POW'), "BITMESSAGE_TEST_POW is not set")
class TestProofofwork(TestProofofworkBase):
```

**Solution:** Document how to run extended tests in `src/tests/AGENTS.md`.

```bash
# Run extended PoW tests (computationally expensive, ~44 seconds)
BITMESSAGE_TEST_POW=1 uv run pytest src/tests/test_proofofwork.py::TestProofofwork -v
```

**Files to modify:**
- `src/tests/AGENTS.md` (already updated)

**Status:** ✅ Done

---

## Dependency Matrix

| Test | Python 3 | PyQt6 | cryptography | pycryptodome | OpenCL |
|------|----------|-------|--------------|--------------|--------|
| `test_sqlthread.py` | ❌ Skips | ✅ | ✅ | N/A | N/A |
| `test_crypto.py` | ✅ | N/A | ✅ (main) | ✅ (RIPEMD160) | N/A |
| `test_openclpow.py` | ✅ | N/A | ✅ | N/A | ⚠️ GPU req |
| Other tests | ✅ | ✅ | ✅ | ✅ | N/A |

### Note on Cryptography Libraries

PyBitmessage uses two crypto libraries:

1. **`cryptography` package** (primary) - For EC, AES, HMAC, SHA, padding (modern crypto)
2. **`pycryptodome`** (secondary) - For RIPEMD160 only (drop-in replacement for deprecated pycrypto)

**No code changes required** - pycryptodome provides the same `Crypto` namespace as pycrypto.

This is intentional because RIPEMD160 is a legacy algorithm not included in the modern `cryptography` package.

---

## Migration Checklist

- [x] Add `pycryptodome` to `install_requires` in `setup.py`
- [x] Verify pycryptodome works as drop-in replacement for pycrypto
- [x] Fix `__metaclass__` syntax in `test_crypto.py` (Python 2 → Python 3 ABCMeta)
- [x] Fix `helper_bitcoin.py` - Replace `hashlib.new('ripemd160')` with pycryptodome ✅
- [x] Fix `arithmetic.py` - Replace `hashlib.new('ripemd160')` with pycryptodome ✅
- [ ] Remove `skip_python3()` from `test_sqlthread.py` (BLOCKED - requires full app initialization)
- [ ] Verify all tests pass after changes
- [ ] Update `src/tests/AGENTS.md` with final status

---

## Commands Reference

```bash
# Run all tests
uv run pytest src/tests/ -v

# Run specific test
uv run pytest src/tests/test_sqlthread.py -v

# Run extended PoW tests
BITMESSAGE_TEST_POW=1 uv run pytest src/tests/test_proofofwork.py::TestProofofwork -v

# Run with coverage
uv run pytest src/tests/ --cov=pybitmessage

# Run tests matching pattern
uv run pytest src/tests/ -k "crypto" -v
```

---

## References

- [Python 3 Porting Guide](https://docs.python.org/3/howto/pyporting.html)
- [PyCryptodome Documentation](https://www.pycryptodome.org/)
- [OpenCL Deprecation on macOS](https://developer.apple.com/support/opencl/)
- [Python ABCMeta Migration](https://docs.python.org/3/library/abc.html#abc.ABCMeta)

---

## Notes

### Why pycryptodome instead of pycrypto?

| Feature | pycrypto | pycryptodome |
|---------|----------|--------------|
| RIPEMD160 support | ✅ | ✅ |
| Last release | 2013 | 2024 |
| Python 3.13 | ❌ | ✅ |
| Actively maintained | ❌ | ✅ |
| Same API | N/A | ✅ |

`pycryptodome` is a drop-in replacement for `pycrypto` specifically for RIPEMD160. The `cryptography` package does NOT include RIPEMD160, so an external library is required.

### Why not use `cryptography` package for everything?

The `cryptography` package intentionally excludes legacy algorithms like RIPEMD160. PyBitmessage needs RIPEMD160 for:
- Address generation (ripe-md160 of public key)
- Bitcoin-compatible address format

This is a protocol requirement, not a code choice.

### CRITICAL: Two RIPEMD160 Implementations Found

**Production code uses TWO different RIPEMD160 sources:**

| File | Line | Method | Works on OpenSSL 3? |
|------|------|--------|---------------------|
| `highlevelcrypto.py` | 127 | `RIPEMD160Hash.new(h).digest()` | ✅ Yes (pycryptodome) |
| `helper_bitcoin.py` | 18, 42 | `hashlib.new('ripemd160')` | ❌ No (OpenSSL) |
| `arithmetic.py` | 144 | `hashlib.new('ripemd160')` | ❌ No (OpenSSL) |

**The `TestHashlib` test correctly identifies a production bug:**
- On OpenSSL 3 systems, `helper_bitcoin.py` and `arithmetic.py` will fail
- This affects Bitcoin address calculation

**Fix required:** Replace `hashlib.new('ripemd160')` with pycryptodome in production code.
