# PyBitmessage Agent Guidelines

**Branch:** `(based on working dir)` | **Generated:** 2026-01-10 | **Updated:** 2026-01-12

## Overview

PyBitmessage: P2P encrypted messaging protocol client (Python 3.13, PyQt6). Multi-interface architecture (GUI, TUI, daemon, mobile Kivy).

## Structure

```
./src/
├── network/          # P2P protocol (connections, addr, inv, bmproto)
├── storage/          # SQLite + filesystem persistence
├── bitmessageqt/     # PyQt6 GUI (mainwindow, dialogs, settings)
├── bitmessagekivy/   # Kivy mobile UI
├── bitmessagecurses/ # Curses TUI
├── plugins/          # Optional features (audio, notification, QR)
├── tests/            # Core test suite
├── backend/          # Address generation worker
├── messagetypes/     # Protocol message definitions
└── bitmessagemain.py # Startup orchestrator (NOT __main__.py)
```

## Commands

```bash
# Tests
uv run pytest src/tests/                       # All tests
uv run pytest src/tests/test_addresses.py     # Specific module
uv run python -m unittest pybitmessage.tests.test_addresses.TestAddresses.test_decode  # Single test

# Lint
uv run bandit -r src/              # Security
uv run mypy src/                   # Type check
uv run pyright src/                # Alternative type checker
uv run flake8 src/ --max-line-length=180

# Build
uv pip install -e .                   # Dev install
uv run python setup.py build_ext --inplace  # C extension (bitmsghash)
uv run python setup.py sdist bdist_wheel    # Package build
```

## Conventions

| Category | Rule | Notes |
|----------|------|-------|
| **Python** | 3.13+ only | No Python 2 compatibility |
| **GUI** | PyQt6 only | No PyQt4/5 code |
| **Style** | flake8 max-line-length=180 | setup.cfg |
| **Imports** | stdlib → third-party → local | Blank line between groups |
| **Naming** | snake_case func/var, PascalCase class, UPPER_SNAKE_CONST | |
| **Logging** | `logger = logging.getLogger('default')` | Module-level |
| **Exceptions** | Custom exceptions end in `Error` | e.g., `varintEncodeError` |
| **Type hints** | Full annotations | Use `TYPE_CHECKING` guard |
| **Forbidden** | `type: ignore`, empty `except:`, `.format()` in new code | |
| **Architecture** | No impl in `__init__.py`, UI/core separation | |

## Defensive Coding Strategy

PyBitmessage follows a **defensive coding** approach to ensure security, reliability, and maintainability in a P2P encrypted messaging system where security is paramount.

### Core Principles

| Principle | Implementation | Benefit |
|-----------|----------------|---------|
| **Type Safety** | Zero `type: ignore` violations, mypy/pyright strict | Catches bugs at compile-time, prevents runtime type errors in critical paths |
| **Modern Path Handling** | `pathlib.Path` over `os.path` | Cross-platform path handling, better error messages, safer file operations |
| **String Safety** | f-strings over `.format()` | Compile-time validation, prevents injection vulnerabilities |
| **Explicit Error Handling** | No empty `except:` blocks, specific exception types | Prevents silent failures in encryption, network, and storage code |
| **Input Validation** | Type hints + Pydantic models for untrusted data | Validates all P2P messages and API inputs at runtime |
| **Thread Safety** | Thread-local storage, explicit locking for free-threading | Safe concurrent operation for Python 3.13+ GIL-free builds |

### Python 3.13+ Specific Features

| Feature | Recommendation | Status |
|---------|----------------|--------|
| **Free-threading (GIL optional)** | Use `threading.local()` for thread-safe state | Future-proofing |
| **Enhanced SSL/TLS** | Python 3.13 has hardened security - ensure compatibility | Verified |
| **Type Hints** | Full coverage required, use `TYPE_CHECKING` guard | In Progress |
| **Zero-cost exceptions** | Use specific exceptions, avoid bare `except:` | Enforced |

### Pydantic for Runtime Validation (Recommended)

Pydantic is the industry standard for runtime type validation in Python. For a P2P encrypted messaging system, we should use Pydantic to validate:

```python
# Example: Network message validation
from pydantic import BaseModel, ValidationError

class NetworkMessage(BaseModel):
    payload: bytes
    signature: bytes
    sender: str
    stream: int
    version: int

    @classmethod
    def validate_message(cls, data: dict) -> "NetworkMessage | None":
        try:
            return cls.model_validate(data)
        except ValidationError as e:
            logger.error("Invalid network message: %s", e)
            return None
```

### Recommended Pydantic Usage Areas

| Area | Priority | Benefit |
|------|----------|---------|
| **Network protocol messages** | High | Validate all incoming P2P messages |
| **API parameters** | High | Prevent injection attacks via API |
| **Configuration files** | Medium | Validate keys.dat and settings |
| **User input** | Medium | Sanitize all user-provided data |

### Why Defensive Coding Matters for PyBitmessage

1. **P2P Security**: Nodes receive untrusted data from unknown peers - type safety prevents exploitation
2. **Cryptographic Operations**: Filesystem bugs can leak private keys or corrupt wallets
3. **Network Protocol**: Malformed messages should fail safely, not crash the node
4. **Long-Running Process**: Memory safety and type correctness prevent daemon crashes
5. **Multi-Platform**: Path handling must work on Windows, macOS, Linux, and Android
6. **Future-proofing**: Python 3.13 free-threading requires explicit thread safety

### Defensive Coding Checklist

- [x] **Phase 1**: Eliminate `type: ignore` (0 violations)
- [x] **Phase 2**: Migrate to `pathlib.Path` (0 `os.path` usages)
- [x] **Phase 3**: Convert `.format()` to f-strings (95/96 complete, 99%)
- [x] **Phase 3.5**: Fix RIPEMD160 on OpenSSL 3 (pycrypto → pycryptodome)
- [ ] **Phase 4**: Systematic type hints + Pydantic adoption
- [x] **Phase 5A**: Address FIXME security issues (0 High/Medium Bandit issues)
- [ ] **Phase 5B**: Thread-safety for Python 3.13 GIL-free builds

## Anti-Patterns (This Project)

- **0 `type: ignore` violations** - Phase 1 Complete ✅
- **0 `os.path` usages** - Phase 2 Complete ✅
- **1 `.format()` call** - in test_logger.py (legitimate test case, 99% complete) ✅
- **0 High Severity Bandit Issues** - Phase 5 Complete ✅
- **Multiple UI entry points**: bitmessagemain.py dispatches to bitmessageqt, bitmessagecurses, or Kivy
- **Non-standard layout**: Tests in `src/tests/`, not root; source in `src/` (flat), not `src/pybitmessage/`
- **RIPEMD160**: Fixed for OpenSSL 3 (pycryptodome provides cross-platform RIPEMD160) ✅

## Where to Look

| Task | Location |
|------|----------|
| P2P protocol | `network/ bmproto.py, connectionpool.py, addrthread.py` |
| Database | `storage/ sqlite.py, storage.py` |
| PyQt6 GUI | `bitmessageqt/ mainwindow.py, dialogs.py` |
| Kivy mobile | `bitmessagekivy/ baseclass/` |
| Plugins | `plugins/ menu_qrcode.py, notification_*.py` |
| Address handling | `addresses.py, helper_startup.py` |
| API server | `api.py` (XML-RPC, security hardened) |
| Tests | `src/tests/ test_*.py` + `tests_runner.py` (randomized order) |

## Known Issues (FIXME)

- `addresses.py`: encodeBase58 should take binary data
- `networkstatus.py`: Hardcoded stream number
- `class_singleWorker.py`: Inventory deletion, objectPayload signing (Protocol limitation: onionpeer messages are unsigned)
- `api.py`: HACK: cookie handling
- `test_sqlthread.py`: Skipped on Python 3 (needs full app initialization)

## Upgrade Status

| Item | Status |
|------|--------|
| Python 3.13+ | ✅ Complete |
| PyQt6 migration | ✅ Complete |
| Legacy syntax removed | ✅ Complete |
| Future imports | ✅ Removed |
| Type safety (type: ignore) | ✅ Phase 1 Complete (0 violations) |
| Linting (flake8/mypy/pyright) | ✅ Clean with relaxed config |
| F-string conversion | ⚠️ 95/96 complete (99%) |
| Pathlib migration | ✅ Phase 2 Complete (150/150 done) |
| RIPEMD160 on OpenSSL 3 | ✅ Fixed (pycryptodome) |
| Security Hardening | ✅ Phase 5A Complete (0 High issues) |
| Thread Safety | ⏳ Phase 5B Pending (GIL-free audit) |
| Type hints | ⚠️ Partial coverage (Phase 4 in progress) |

## Test Suite Status

| Metric | Value |
|--------|-------|
| Total tests | 101 |
| Passed | 88 |
| Skipped | 13 |
| Duration | ~28s |

### Skipped Tests (Expected)

| Test | Reason |
|------|--------|
| `test_hashlib` | OpenSSL 3 has no RIPEMD160 - pycryptodome handles this |
| `test_openclpow.py` | No OpenCL GPU available |
| `test_proofofwork::TestProofofwork` | Requires `BITMESSAGE_TEST_POW=1` env var |
| `test_sqlthread.py` | Blocked - needs full app initialization |

### Recent Fixes

**Security Hardening** (Fixed 2026-01-12)
- **XML-RPC**: Patched `api.py` and `bitmessagecli.py` with `defusedxml` to prevent DoS attacks.
- **Dependencies**: Added `defusedxml` to `setup.py` and `requirements.txt`.
- **False Positives**: Suppressed Bandit warnings for MD5 (avatars) and pyCrypto (using pycryptodome).
- **Result**: 0 High Severity issues in Bandit scan.

**RIPEMD160 on OpenSSL 3** (Fixed 2026-01-11)
- `setup.py`: Added `pycryptodome` dependency
- `helper_bitcoin.py`: Added `_ripemd160()` helper with pycryptodome fallback
- `arithmetic.py`: Added `_ripemd160()` helper with pycryptodome fallback
- `highlevelcrypto.py`: No change needed (pycryptodome provides `Crypto` namespace)

**Test Modernization**
- `test_crypto.py`: Fixed `__metaclass__` → `metaclass=ABCMeta` (Python 2 → 3)
