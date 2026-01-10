# Refactoring Plan: Python 3.13 + PyQt6 Migration

## 📊 CURRENT STATUS (Jan 8, 2026) - COMPLETE

The project has successfully completed its migration from a legacy Python 2.7/3.x hybrid to a **native Python 3.13 + PyQt6** codebase. **All 128 tests are passing.**

### ✅ COMPLETED

- **Python 3.13 Enforcement**: Strictly enforced in `setup.py` and `src/depends.py`.
- **PyQt6 Migration**: All imports updated; `INSTALL.md` cleaned of legacy PyQt references.
- **Six library Removal**: 100% complete. Native types are now used everywhere.
- **Future Imports Removal**: 100% complete. All `from __future__` statements purged.
- **Legacy Syntax Removal**: Fixed legacy `print` and `unicode()` survivors.
- **Test Discovery Fix**: Modern `src/__init__.py` structure implemented.
- **OpenSSL 3.x Compatibility**: **FIXED** - Corrected `EVP_CipherInit_ex` argtypes in `pyelliptic/openssl.py`.
- **Blind Signature Bug**: **FIXED** - Dynamic expiration in `pyelliptic/eccblind.py`.
- **Test Suite**: **128 tests passing** (14 skipped for optional GUI).

### ⚠️ FUTURE IMPROVEMENTS (Technical Debt)

1. **Systematic Code Modernization**
    - **F-string Conversion**: Converting remaining `.format()` calls.
    - **Pathlib Migration**: Replacing `os.path` with `pathlib.Path` (~200 occurrences).
    - **Type Hints**: Adding PEP 484 type annotations for improved maintainability.

## 🎯 FUTURE ROADMAP (Optional)

### **PHASE 1: Structural Refactoring**

- **Pathlib Migration**: Systematically replace `os.path` throughout `src/`.
- **Typing Adoption**: Add type hints to all function signatures in the API and network layers.
- **Cleanup legacy artifacts**: Remove unused build scripts and old documentation.

### **PHASE 2: UI & Performance Polish**

- **Systematic f-string adoption**: Complete the transition to f-strings for all user-facing strings.
- **Performance Audit**: Optimize inventory lookups and SQLite interactions.

## 📋 SUMMARY

**The primary Python 3.13, PyQt6, and OpenSSL 3.x migration is COMPLETE.** The project is now stable and fully operational on modern platforms. Future work focuses on code quality improvements rather than compatibility fixes.
