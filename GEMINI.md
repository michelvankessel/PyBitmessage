# PyBitmessage

## Project Overview

PyBitmessage is the reference implementation of the Bitmessage protocol, a decentralized, trustless, peer-to-peer (P2P) communications protocol used to send encrypted messages. It is designed to hide metadata from passive eavesdroppers, ensuring sender and receiver anonymity.

The application offers multiple user interfaces:
*   **Qt GUI:** The primary desktop interface (PyQt6).
*   **Kivy GUI:** For mobile and touch-enabled devices.
*   **Curses:** A terminal-based interface.
*   **CLI:** Command-line interface and daemon mode.

## Key Technologies

*   **Language:** Python 3.13+
*   **GUI Frameworks:** PyQt6, Kivy, Curses
*   **Cryptography:** OpenSSL 3.x, `cryptography`, `pycryptodome`
*   **Dependency Management:** `uv` (highly recommended), `setuptools`
*   **Testing:** `tox`, `unittest` (via `tests.py`), `coverage`

## Active Modernization (2026)
The project is undergoing a significant modernization effort (see `MODERNIZATION_PLAN.md`).
*   **Completed:** Pathlib migration (`os.path` -> `pathlib`), F-strings conversion (`.format()` -> f-strings), Critical type safety (`type: ignore` removal), Security hardening (`defusedxml`).
*   **Pending/In-Progress:**
    *   **Type Hints:** Systematic adoption of type hints across the codebase.
    *   **Pydantic:** Adoption for runtime validation (Network protocol, API, Config).
    *   **Thread Safety:** Preparation for Python 3.13+ free-threading (`threading.local()`).

## Building and Running

### Prerequisites
*   Python 3.13 or later
*   `uv` (for dependency management)
*   OpenSSL 3.x
*   System dependencies for Qt (e.g., `libssl-dev` on Linux)

### Installation
It is recommended to use `uv` for a fast and isolated development environment.

```bash
# Create virtual environment and install dependencies
uv venv --python 3.13
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Running the Application
```bash
# Run the main application (detects available GUI or runs in background)
uv run src/bitmessagemain.py

# Run with specific UI (examples)
# Note: UI selection logic is handled within the app, but flags exist
uv run src/bitmessagemain.py --help
```

Alternatively, use the helper script:
```bash
./start.sh
```

## Development Conventions

### Directory Structure
*   `src/`: Main source code. The `pybitmessage` package is located here.
*   `src/bitmessageqt/`: Qt GUI code.
*   `src/bitmessagekivy/`: Kivy GUI code.
*   `src/bitmessagecurses/`: Curses interface code.
*   `tests/`: Test suite (located in `src/tests` or `tests.py` runner).
*   `packages/`: Packaging scripts for various platforms (Android, AppImage, Snap, etc.).

### Where to Look
| Task | Location | Notes |
|------|----------|-------|
| **Entry Point** | `src/bitmessagemain.py` | Parses args, launches GUI/Daemon |
| **Protocol** | `src/network/bmproto.py` | Message encoding/decoding, handshake |
| **Cryptography** | `src/highlevelcrypto.py` | ECDH, AES-256, HMAC-SHA256 |
| **PoW** | `src/bitmsghash/` | C++ extension for SHA512 hashing |
| **Config** | `src/bmconfigparser.py` | Handles `keys.dat` and settings |
| **Database** | `src/storage/sqlite.py` | Message/Inventory persistence |

### Testing
The project uses `tox` for orchestrating tests and `unittest` for the test suite.

```bash
# Run full test suite using uv
uv run tests.py

# Run tests via tox (includes linting and coverage)
tox

# Run specific environments
tox -e py313
tox -e lint
```

### Code Quality
*   **Linting:** `flake8` and `pylint` are configured in `tox.ini`.
*   **Security:** `bandit` is used for security linting.
*   **Coverage:** Code coverage is tracked and can be reported via `tox -e stats`.

### Dependencies
Dependencies are managed in `requirements.txt` (core) and `kivy-requirements.txt` (mobile). The `setup.py` file also defines dependencies for the package build. `checkdeps.py` is a utility to verify the environment.