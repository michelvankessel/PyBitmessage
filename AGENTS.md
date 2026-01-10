# PyBitmessage Agent Guidelines

## Current Upgrade Status: Python 3.13 + PyQt6 Migration (COMPLETE)

### ✅ **COMPLETED**

- **Python 3.13+ target**: Achieved (`setup.py` specifies `python_requires=">=3.13"`)
- **PyQt6 migration**: Complete - all UI imports use `from PyQt6`
- **Legacy syntax**: Removed (no Python 2 `print`, `unicode`, `xrange`)
- **Modern Qt6 patterns**: `QSoundEffect` implemented, native signal/slot syntax
- **Future imports**: **FULLY REMOVED** - 0 remaining `from __future__ import` statements
- **Six library**: **FULLY REMOVED** - 0 occurrences in codebase
- **Test Discovery**: Fixed by adding `src/__init__.py`
- **OpenSSL 3.x Compatibility**: **FIXED** - Corrected `EVP_CipherInit_ex` signature in `pyelliptic/openssl.py`
- **Blind Signature Expiration**: **FIXED** - Dynamic expiration in `pyelliptic/eccblind.py`
- **Test Suite**: **128 tests passing** (as of Jan 8, 2026)

### ⚠️ **FUTURE IMPROVEMENTS (Low Priority)**

- **F-string conversion**: Systematic conversion from `.format()` to f-strings
- **Pathlib migration**: ~200 `os.path` occurrences remain
- **Type hints**: Systematic adoption needed across the codebase

## Build/Test/Lint Commands

### Running Tests

```bash
# Run all tests (recommended)
PYTHONPATH=src python3.13 tests.py

# Run specific test module
python3.13 -m unittest pybitmessage.tests.test_addresses
```

### Linting and Code Quality

```bash
# Security analysis
bandit -r src/

# Type checking (work in progress)
# Type checking (work in progress)
mypy src/
```

## Code Style Guidelines

### Modernization Requirements

1. **Python 3.13 only**: No legacy Python 2.x code.
2. **PyQt6 only**: No PyQt4/5 compatibility code.
3. **Use f-strings**: Prefer `f"{var}"` over `.format()` or `%`.
4. **Use pathlib**: Replace `os.path` with `pathlib.Path`.
5. **Add type hints**: Annotate function signatures for clarity.
6. **Defensive Coding**: **DO NOT use `type: ignore`**. Fix the underlying issue or create a stub.

### Architecture Patterns

- **Keep UI logic separate** from core functionality.
- **Never put implementation in `__init__.py` files**.
- **Use absolute imports**.
- **Maintain separation** between network, storage, and UI layers.
