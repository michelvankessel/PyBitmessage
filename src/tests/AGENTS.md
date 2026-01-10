# PyBitmessage Test Suite Agents

**Branch:** `(based on working dir)` | **Generated:** 2026-01-10 | **Updated:** 2026-01-10

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
# Run all tests
uv run pytest src/tests/

# Run specific module
uv run pytest src/tests/test_addresses.py

# Run with unittest
python3.13 -m unittest pybitmessage.tests.test_addresses

# Custom runner with random order
python3.13 tests_runner.py
```

## Conventions

- **Test files**: `test_*.py` pattern required for discovery
- **Import pattern**: `from pybitmessage import pathmagic; pathmagic.setup()`
- **Random order**: `tests_runner.py` uses `random.randint(-1, 1)` for test method ordering
- **Pytest config**: setup.cfg ignores bitmessagekivy/tests, testpaths = [src/tests]
- **Mock isolation**: `mockbm/` provides standalone components without full PyBitmessage setup

## Defensive Coding in Tests

### Pathlib Migration Status
- ✅ **common.py**: 4/4 os.path usages migrated
- ✅ **core.py**: 1/1 os.path usage migrated
- ✅ **test_process.py**: 2/2 os.path usages migrated
- ✅ **test_config_process.py**: 1/1 os.path usage migrated
- ✅ **test_inventory.py**: 2/2 os.path usages migrated
- ✅ **test_logger.py**: 2/2 os.path usages migrated
- ✅ **partial.py**: 1/1 os.path usage migrated

### Test Best Practices

| Practice | Implementation | Notes |
|----------|----------------|-------|
| **Assert messages** | Always provide descriptive assert messages | Helps debugging CI failures |
| **Exception testing** | Use `assertRaises` with context | Don't use try/except in tests |
| **Temporary files** | Use `tempfile` module + cleanup | Pathlib for path operations |
| **Isolation** | Each test independent | No shared state between tests |

### Pydantic for Test Fixtures (Recommended)

```python
# Example: Validated test fixture with Pydantic
from pydantic import BaseModel
from datetime import datetime

class TestAddress(BaseModel):
    address: str
    label: str
    stream: int

    @field_validator('address')
    @classmethod
    def valid_bm_address(cls, v: str) -> str:
        assert v.startswith('BM-'), f"Invalid test address: {v}"
        return v

# In test:
fixture = TestAddress(address="BM-xxxx", label="Test", stream=1)
```

## Anti-Patterns (This Module)

- **TODO**: uncovered API commands in test_api.py (lines 45-47)
- **Hardcoded paths**: Some tests assume specific directory structure (migrated to pathlib)
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