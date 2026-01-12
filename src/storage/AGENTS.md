# PyBitmessage Storage Layer

**Branch:** `(based on working dir)` | **Generated:** 2026-01-10 | **Updated:** 2026-01-12

## Overview

SQLite database + filesystem storage for messages, addresses, inventory. Dual backend architecture with thread-safe abstractions.

## Structure

```
src/storage/
├── storage.py         # Base storage interface (InventoryStorage)
├── sqlite.py          # SQLite implementation (SqliteInventory)
├── filesystem.py      # File-based attachment storage (FilesystemInventory)
└── __init__.py        # Empty (no exports)
```

## Database Schema

**inventory table** (messages.dat):
```sql
CREATE TABLE inventory (
    hash blob,              -- Object hash identifier
    objecttype int,         -- Message type enum
    streamnumber int,       -- Bitmessage stream
    payload blob,           -- Message data
    expirestime integer,    -- Unix timestamp
    tag blob,               -- Optional tag
    UNIQUE(hash) ON CONFLICT REPLACE
);
```

## Key Classes

- **InventoryStorage**: Abstract base defining inventory interface
- **SqliteInventory**: SQLite backend with connection pooling
- **FilesystemInventory**: Directory-based storage (objects/ per stream)

## Filesystem Layout

```
~/.config/PyBitmessage/storage/
├── objects/             # Inventory objects by stream
│   ├── 1/              # Stream 1 objects
│   ├── 2/              # Stream 2 objects
│   └── ...
└── messages.dat        # SQLite database
```

## Defensive Coding for Storage

### Pathlib Migration Status
- ✅ **filesystem.py**: 13/13 os.path usages migrated to pathlib.Path

### Thread Safety Considerations

| Concern | Implementation | Notes |
|---------|----------------|-------|
| **SQLite concurrency** | Connection pooling per thread | `threading.local()` for connections |
| **Filesystem locking** | Module-level locks | Prevent race conditions on object files |
| **Object expiration** | SQL DELETE with expirestime | Cleanup runs periodically |

### Pydantic for Data Validation (Recommended)

Storage layer validates data before writing:

```python
# Example: Inventory item validation with Pydantic
from pydantic import BaseModel, field_validator
from datetime import datetime

class InventoryItem(BaseModel):
    hash: bytes  # Exactly 64 hex characters
    object_type: int
    stream_number: int
    payload: bytes
    expires_time: datetime
    tag: bytes | None = None

    @field_validator('hash')
    @classmethod
    def validate_hash(cls, v: bytes) -> bytes:
        if len(v) != 32:
            raise ValueError('Hash must be 32 bytes')
        return v
```

## Anti-Patterns (This Module)

- **Type hints**: filesystem.py needs full coverage (Phase 4)
- **Pydantic models**: Not yet implemented for storage validation (Phase 4)

## Migration Notes

- knownnodes.py handles peer storage (separate from inventory)
- Object expiration handled via expirestime column
- Thread safety via module-level locks in both backends
- ✅ Pathlib migration complete (filesystem.py)