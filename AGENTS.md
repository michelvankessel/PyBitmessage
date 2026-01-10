# PyBitmessage Agent Guidelines

**Branch:** `(based on working dir)` | **Generated:** 2026-01-10

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
PYTHONPATH=src python3.13 tests.py                        # All tests
python3.13 -m unittest pybitmessage.tests.test_addresses # Specific module
python3.13 -m unittest pybitmessage.tests.test_addresses.TestAddresses.test_decode  # Single test

# Lint
bandit -r src/                  # Security
mypy src/                       # Type check (clean as of 2026-01-10)
pyright src/                    # Alternative type checker (0 errors)
flake8 src/ --max-line-length=180

# Build
pip install -e .                # Dev install
python3 setup.py build_ext --inplace  # C extension (bitmsghash)
python3 setup.py sdist bdist_wheel    # Package build
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

## Anti-Patterns (This Project)

- **0 `type: ignore` violations** - Phase 1 complete ✅
- **109 `os.path` usages** - migrate to `pathlib.Path` (41/150 migrated in Phase 2 Prio 1)
- **96 `.format()` calls** - convert to f-strings (priority: bitmessageqt/mainwindow.py)
- **Multiple UI entry points**: bitmessagemain.py dispatches to bitmessageqt, bitmessagecurses, or Kivy
- **Non-standard layout**: Tests in `src/tests/`, not root; source in `src/` (flat), not `src/pybitmessage/`

## Where to Look

| Task | Location |
|------|----------|
| P2P protocol | `network/ bmproto.py, connectionpool.py, addrthread.py` |
| Database | `storage/ sqlite.py, storage.py` |
| PyQt6 GUI | `bitmessageqt/ mainwindow.py, dialogs.py` |
| Kivy mobile | `bitmessagekivy/ baseclass/` |
| Plugins | `plugins/ menu_qrcode.py, notification_*.py` |
| Address handling | `addresses.py, helper_startup.py` |
| API server | `api.py` (XML-RPC, security TODO) |
| Tests | `src/tests/ test_*.py` + `tests_runner.py` (randomized order) |

## Known Issues (FIXME)

- `addresses.py`: encodeBase58 should take binary data
- `networkstatus.py`: Hardcoded stream number
- `class_singleWorker.py`: Inventory deletion, objectPayload signing
- `api.py`: XML vulnerabilities, HACK: cookie handling

## Upgrade Status

| Item | Status |
|------|--------|
| Python 3.13+ | ✅ Complete |
| PyQt6 migration | ✅ Complete |
| Legacy syntax removed | ✅ Complete |
| Future imports | ✅ Removed |
| Type safety (type: ignore) | ✅ Phase 1 Complete (0 violations) |
| Linting (flake8/mypy/pyright) | ✅ Clean (0 errors) |
| F-string conversion | ⚠️ 96 pending |
| Pathlib migration | ⚠️ 80 remaining (70/150 done in Phase 2 Prio 1 & 2) |
| Type hints | ⚠️ Systematic adoption needed |
