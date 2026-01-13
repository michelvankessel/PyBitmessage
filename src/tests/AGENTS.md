# PyBitmessage Test Suite Agents

**Generated:** 2026-01-13

## OVERVIEW
Test suite using unittest + custom randomized runner with extensive mocking patterns for protocol, crypto, and API testing.

## STRUCTURE
```
src/tests/
├── test_*.py           # 27 test modules
├── samples.py          # Deterministic test fixtures  
├── mockbm/             # Mock components for isolation
├── sql/                # Database test fixtures
├── common.py           # Shared cleanup utilities
└── apinotify_handler.py # API test notifications
```
└── common.py           # Shared test utilities
```

## WHERE TO LOOK

### Mocking Patterns
- **SQL mocking**: `@patch('helper_sql.sql_execute')` for database operations
- **Network mocking**: `mockbm/network.py` for connection stats
- **API mocking**: `apinotify_handler.py` for XML-RPC responses
- **File mocking**: `@patch('os.stat')` for permission tests

### Fixture Usage
- **samples.py**: Contains deterministic test vectors (addresses, keys, hashes)
- **sql/**: Database initialization scripts for version testing
- **mockbm/**: Provides isolated components without daemon dependencies

### Randomized Runner Quirks
- **tests_runner.py**: Uses `random.randint(-1, 1)` for test method ordering
- **test_randomtrackingdict.py**: Generates random strings for dictionary testing
- **core.py**: Random IP generation for network simulation

## CONVENTIONS
- **Import order**: `from pybitmessage import pathmagic; pathmagic.setup()` first
- **Test discovery**: `test_*.py` pattern required
- **Mock isolation**: Use `unittest.mock.patch` for external dependencies
- **Cleanup**: `common.cleanup()` removes test files after execution

## ANTI-PATTERNS
- **Hardcoded paths**: Use `pathlib.Path` (migration complete)
- **Integration leaks**: `core.py` requires full app initialization
- **Random failures**: Randomized order may expose hidden dependencies
- **SQL coupling**: Database tests need proper isolation with mocks
