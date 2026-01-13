# PROJECT KNOWLEDGE BASE

**Generated:** 2026-01-13
**Status:** Phase 5A Complete (Security), Phase 5B Pending (Thread Safety)

## OVERVIEW
PyBitmessage is a P2P encrypted messaging client (Python 3.13, PyQt6) featuring a multi-interface architecture (GUI, TUI, daemon, mobile Kivy) and a custom Proof-of-Work protocol.

## STRUCTURE
```
.
├── buildscripts/ # OS-specific build scripts (osx.sh, winbuild.sh, etc.)
├── packages/     # Packaging configs (Snap, AppImage)
└── src/
    ├── bitmessageqt/     # PyQt6 GUI (mainwindow, dialogs)
    ├── network/          # P2P protocol logic (connectionpool, bmproto)
    ├── storage/          # SQLite + Filesystem persistence
    ├── tests/            # Core test suite (unittest + pytest)
    ├── bitmessagemain.py # Application entry point (orchestrator)
    └── bitmsghash/       # C extension for PoW (OpenSSL)
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| **Entry Point** | `src/bitmessagemain.py` | Parses args, launches GUI/Daemon |
| **Protocol** | `src/network/bmproto.py` | Message encoding/decoding, handshake |
| **Cryptography** | `src/highlevelcrypto.py` | ECDH, AES-256, HMAC-SHA256 |
| **PoW** | `src/bitmsghash/` | C++ extension for SHA512 hashing |
| **Config** | `src/bmconfigparser.py` | Handles `keys.dat` and settings |
| **Database** | `src/storage/sqlite.py` | Message/Inventory persistence |

## CONVENTIONS
- **Python 3.13+**: No Python 2 compatibility code.
- **Imports**: `stdlib` → `third-party` → `local` (blank line separated).
- **Paths**: `pathlib.Path` ONLY (0 `os.path` usages allowed).
- **Strings**: f-strings ONLY (0 `.format()` calls allowed).
- **Typing**: Full type hints required (Phase 4 in progress).
- **Security**: `defusedxml` for XML-RPC, `pycryptodome` for RIPEMD160.

## ANTI-PATTERNS (THIS PROJECT)
- **Hardcoded Streams**: Do NOT hardcode `stream = 1`. Use config.
- **Raw SQL**: NEVER use f-strings in SQL queries. Use parametrized `?`.
- **Global State**: Avoid modifying `state.py` flags at runtime.
- **Manual UI Edits**: NEVER edit `bitmessageui.py` (generated). Edit `.ui` instead.
- **Blocking GUI**: Long ops MUST run in threads (workers), sending signals to UI.

## COMMANDS
```bash
# Test
uv run pytest src/tests/
uv run pytest src/tests/test_network.py

# Lint & Security
uv run flake8 src/ --max-line-length=180
uv run bandit -r src/ -lll

# Build
uv run python setup.py build_ext --inplace
./buildscripts/osx.sh 0.7.0.0
```

## NOTES
- **Protocol Limitation**: `onionpeer` messages are unsigned (spoofing risk).
- **Thread Safety**: GIL-free audit pending (Phase 5B). Use `threading.local()`.
- **Encryption**: Uses `pycryptodome` for RIPEMD160 (OpenSSL 3 compat).
