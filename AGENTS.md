# PyBitmessage Agent Guidelines

## Build/Test/Lint Commands

### Running Tests

```bash
# Run all tests (recommended)
PYTHONPATH=src python3.13 tests.py

# Run specific test module
python3.13 -m unittest pybitmessage.tests.test_addresses

# Run a single test case
python3.13 -m unittest pybitmessage.tests.test_addresses.TestAddresses.test_decode

# Run with verbose output
PYTHONPATH=src python3.13 -m unittest discover -s pybitmessage/tests -v
```

### Linting and Code Quality

```bash
# Security analysis
bandit -r src/

# Type checking (work in progress)
mypy src/

# Run the test runner directly
python3.13 tests_runner.py
```

### Build Commands

```bash
# Development installation
pip install -e .

# Build C extension (bitmsghash)
python3 setup.py build_ext --inplace

# Full package build
python3 setup.py sdist bdist_wheel
```

---

## Code Style Guidelines

### Modernization Requirements

1. **Python 3.13 only**: No legacy Python 2.x code.
2. **PyQt6 only**: No PyQt4/5 compatibility code.
3. **Use f-strings**: Prefer `f"{var}"` over `.format()` or `%` formatting.
4. **Use pathlib**: Replace `os.path` with `pathlib.Path` where feasible.
5. **Add type hints**: Annotate function signatures for clarity and mypy compatibility.
6. **Defensive Coding**: **DO NOT use `type: ignore`**. Fix the underlying issue or create a stub.

### Imports

- **Order**: Standard library → Third-party → Local/absolute imports (blank line between groups)
- **Style**: Use absolute imports (`from module import name`)
- **Avoid**: Relative imports (`from .module import name`) unless necessary

```python
# Correct order
import logging
import os
from binascii import hexlify, unhexlify
from struct import pack, unpack

import highlevelcrypto
from addresses import decodeAddress, encodeVarint
```

### Naming Conventions

- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private attributes**: `_leading_underscore`

```python
# Examples
class varintEncodeError(Exception): ...
def encode_varint(integer): ...
ALPHABET = "123456789..."
logger = logging.getLogger('default')
```

### Docstrings

Use Google-style docstrings with `Args:` and `Returns:` sections:

```python
def encodeBase58(num):
    """Encode a number in Base X

    Args:
      num: The number to encode
      alphabet: The alphabet to use for encoding

    Returns:
      The encoded string or None if num < 0
    """
```

### Type Hints

Use modern Python 3.13 type hints:

```python
# Simple types
def process_address(address: str) -> bool: ...

# Complex types
myECCryptorObjects: dict[bytes, Any] = {}
MyECSubscriptionCryptorObjects: dict[bytes, Any] = {}

# Type checking import guard
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from module import SomeType
```

### Error Handling

- **Custom exceptions**: Name ending with `Error` (e.g., `varintEncodeError`)
- **Never suppress errors**: No empty `except:` blocks
- **Specific exceptions**: Catch only the exceptions you handle

```python
class varintEncodeError(Exception):
    """Exception class for encoding varint"""
    pass

try:
    result = operation()
except ValueError:
    return 0  # Handle specific error
```

### Logging

Use the module-level logger pattern:

```python
logger = logging.getLogger('default')

# In functions
logger.info('Loading config files from %s', path)
logger.error("Error in function: %s", detail)
```

### String Formatting

**Prefer f-strings** for all new code:

```python
# Preferred (new code)
f"Loading config from {path}"

# Acceptable (existing code - don't convert unless modifying)
"Loading config from %s" % path
"Loading config from {}".format(path)
```

### Architecture Patterns

- **Keep UI logic separate** from core functionality
- **Never put implementation in `__init__.py` files**
- **Use absolute imports** for all cross-module references
- **Maintain separation** between network, storage, and UI layers
- **Import pathmagic first** in test files when needed:

```python
from pybitmessage import pathmagic
pathmagic.setup()
```

### Module Structure

- **Source location**: `src/` directory (not `pybitmessage/` root)
- **Package structure**: `pybitmessage.{module}` imports
- **Test location**: `src/tests/` for core tests, `src/bitmessagekivy/tests/` for UI tests
- **Entry points**: Defined in `setup.py` under `console_scripts`

---

## Current Upgrade Status

- ✅ **Python 3.13+ target**: Complete
- ✅ **PyQt6 migration**: Complete
- ✅ **Legacy syntax removed**: No Python 2 `print`, `unicode`, `xrange`
- ✅ **Future imports removed**: 0 remaining
- ✅ **Six library removed**: 0 occurrences
- ⚠️ **F-string conversion**: Pending (~200 occurrences)
- ⚠️ **Pathlib migration**: Pending (~200 `os.path` occurrences)
- ⚠️ **Type hints**: Systematic adoption needed
