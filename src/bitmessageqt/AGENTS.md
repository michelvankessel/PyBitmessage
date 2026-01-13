# PyBitmessage Qt6 GUI Agent Guidelines

**Generated:** 2026-01-13

## OVERVIEW
PyQt6 desktop GUI with signal/slot architecture, Qt Designer UI files, and worker thread separation for non-blocking operations.

## STRUCTURE
```
src/bitmessageqt/
├── mainwindow.py      # Main window (1000+ lines, thread-safe UI updates)
├── uisignaler.py      # Central signal emitter (QThread singleton)
├── dialogs.py         # Message/address dialogs
├── settings.py        # Configuration UI
├── *.ui              # Qt Designer files (17 total)
├── bitmessageui.py    # Auto-generated from .ui files (DO NOT EDIT)
├── widgets.py         # Custom widget utilities
└── tests/            # GUI-specific test suite
```

## WHERE TO LOOK
| Task | Location | Key Pattern |
|------|----------|-------------|
| **Signal/Slot Central** | `uisignaler.py` | `pyqtSignal()` definitions, queue consumer |
| **Main Window Logic** | `mainwindow.py` | Signal connections, worker queue integration |
| **UI Definitions** | `*.ui` files | Qt Designer XML, compiled to `bitmessageui.py` |
| **Thread Safety** | `mainwindow.py:967-994` | UISignaler singleton pattern |
| **Worker Integration** | `account.py:256` | `queues.workerQueue.put()` calls |

## Qt6 CONVENTIONS

### Signal/Slot Pattern
```python
# Native PyQt6 syntax (preferred)
signal_name = pyqtSignal(type1, type2)
signal_name.connect(slot_method)
signal_name.emit(value1, value2)

# In mainwindow.py
self.UISignalThread.displayNewInboxMessage.connect(self.displayNewInboxMessage)
```

### UI File Handling
- **Source**: `*.ui` files (Qt Designer XML)
- **Generated**: `bitmessageui.py` (via `pyuic6`)
- **Rule**: NEVER edit `bitmessageui.py` directly - changes lost on regeneration
- **Extension**: Subclass generated classes in separate files

### Thread Safety Architecture
```python
# GUI thread: handles UI updates only
# Worker thread: processes messages, crypto, network
# Communication: queues + signals

# Safe pattern from mainwindow.py
def displayNewInboxMessage(self, inventory_hash, to_addr, from_addr, subject, body):
    # Runs in GUI thread via signal
    self.update_status_bar("New message received")
    self.add_message_to_table(inventory_hash, to_addr, from_addr, subject, body)
```

## ANTI-PATTERNS (GUI MODULE)

- **BLOCKING GUI**: Never call `queues.workerQueue.get()` in GUI thread
- **MANUAL UI EDITS**: Never edit `bitmessageui.py` - edit `.ui` files instead
- **DIRECT THREADING**: Use `UISignaler` singleton, not raw `QThread`
- **HARDCODED STREAMS**: Use config values, not `stream = 1` in networkstatus
- **SIGNAL OVERLOAD**: Avoid connecting multiple signals to same slot without disambiguation

## CRITICAL THREAD SAFETY

1. **GUI Updates**: Must use `UISignaler` signals from worker threads
2. **Worker Queue**: `queues.workerQueue.put()` from GUI, `.get()` in worker threads only
3. **UI State**: Modify Qt widgets only in GUI thread (via signals)
4. **Long Operations**: Always delegate to workers, update UI via signals

## UI UPDATE PATTERN
```python
# Worker thread (safe)
queues.UISignalQueue.put(('displayNewInboxMessage', 
    (inventory_hash, to_addr, from_addr, subject, body)))

# UISignaler converts to signal (safe)
self.displayNewInboxMessage.emit(inventory_hash, to_addr, from_addr, subject, body)

# GUI slot runs in main thread (safe)
def displayNewInboxMessage(self, inventory_hash, to_addr, from_addr, subject, body):
    # Update UI elements here
```