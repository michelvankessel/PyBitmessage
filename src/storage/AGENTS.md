# PyBitmessage Storage Layer

**Generated:** 2026-01-13 | **Status:** Dual backend operational

## OVERVIEW

Dual backend persistence layer: SQLite for inventory metadata, filesystem for payload storage. Thread-safe with RLock coordination.

## STRUCTURE

```
src/storage/
├── storage.py      # Abstract InventoryStorage base class
├── sqlite.py       # SqliteInventory (metadata + caching)
├── filesystem.py   # FilesystemInventory (payload storage)
└── __init__.py     # Empty module
```

## WHERE TO LOOK

- **Inventory operations**: `sqlite.py` - SQL queries, connection pooling, caching
- **Payload storage**: `filesystem.py` - Stream-based directory layout, file I/O
- **Base interface**: `storage.py` - InventoryStorage abstract class
- **Thread safety**: Both backends use `RLock` for concurrent access
- **Schema**: `messages.dat` - inventory table with hash, type, stream, payload, expires

## CONVENTIONS

- **Lock hierarchy**: Acquire `self.lock` before any storage operation
- **Hash format**: 32-byte binary keys, never hex strings in storage
- **Stream directories**: `objects/{stream_number}/` for filesystem layout
- **Connection pooling**: SQLite uses `threading.local()` per-thread connections
- **Expiration**: `expirestime` column drives cleanup, not filesystem timestamps

## ANTI-PATTERNS

- **Direct SQL**: Never bypass InventoryStorage interface for database access
- **Stream hardcoding**: Use `streamnumber` from inventory, never assume stream=1
- **Path manipulation**: Use pathlib.Path exclusively (no os.path.join)
- **Lock bypass**: Never access `_inventory` or `_objects` without acquiring lock
- **Binary/hash confusion**: Always use binary hashes in storage, convert to hex only for UI