# PyBitmessage Test Suite Agents

**Branch:** `(based on working dir)` | **Generated:** 2026-01-10

## Overview

PyBitmessage core test suite using unittest + custom runner with randomized test order. 33+ files covering protocol, crypto, API, network, and UI components.

## Structure

```
src/tests/
├── test_*.py           # 27 test modules (addresses, api, crypto, network, etc.)
├── samples.py          # Test fixtures (addresses, keys, deterministic data)
├── core.py             # Core integration tests requiring full setup
├── mockbm/             # Mock components for isolated testing
│   ├── bitmessagemock.py    # Main mock interface
│   ├── kivy_main.py         # Kivy UI mocks
│   └── pybitmessage/        # Mocked PyBitmessage modules
├── sql/                # SQL test data and fixtures
└── common.py           # Shared test utilities
```

## Commands

```bash
PYTHONPATH=src python3.13 tests.py                    # All tests
python3.13 -m unittest pybitmessage.tests.test_addresses  # Specific module
python3.13 tests_runner.py                            # Custom runner with random order
python3.13 -m unittest discover -s pybitmessage/tests -v  # Standard discovery
```

## Conventions

- **Test files**: `test_*.py` pattern required for discovery
- **Import pattern**: `from pybitmessage import pathmagic; pathmagic.setup()`
- **Random order**: `tests_runner.py` uses `random.randint(-1, 1)` for test method ordering
- **Pytest config**: setup.cfg ignores bitmessagekivy/tests, testpaths = [src/tests]
- **Mock isolation**: `mockbm/` provides standalone components without full PyBitmessage setup

## Anti-Patterns (This Module)

- **TODO**: uncovered API commands in test_api.py (lines 45-47)
- **type: ignore** on mockbm/kivy_main.py import (line 15)
- **Hardcoded paths**: Some tests assume specific directory structure
- **Integration leaks**: core.py tests require full PyBitmessage initialization

## Where to Look

| Component | Test Files |
|-----------|------------|
| **Protocol** | test_packets.py, test_protocol.py |
| **API** | test_api.py, test_api_thread.py |
| **Network** | test_network.py, test_connection.py |
| **Crypto** | test_crypto.py, test_proofofwork.py |
| **Addresses** | test_addresses.py, test_addressgenerator.py |
| **Storage** | test_inventory.py, test_helper_sql.py |
| **UI/Core** | test_shared.py, test_config.py, core.py |

## Key Test Data

- **samples.py**: Contains protocol test vectors, sample addresses, hash data
- **sql/**: Database fixtures for SQL-related tests
- **mockbm/**: Provides isolated testing environment without daemon/GUI dependencies