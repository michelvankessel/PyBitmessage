# PyBitmessage Storage Layer

**Branch:** `(based on working dir)` | **Generated:** 2026-01-10

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

## Anti-Patterns (This Module)

- **11 os.path usages** in filesystem.py - migrate to pathlib.Path
- No type hints in filesystem.py (sqlite.py has partial coverage)
- FilesystemInventory uses hex strings for directory names (inefficient)

## Migration Notes

- knownnodes.py handles peer storage (separate from inventory)
- Object expiration handled via expirestime column
- Thread safety via module-level locks in both backends