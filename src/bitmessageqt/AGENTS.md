# PyBitmessage Qt6 GUI Agent Guidelines

**Branch:** `(based on working dir)` | **Generated:** 2026-01-10 | **Updated:** 2026-01-11

## Overview

PyQt6 desktop GUI - main window, dialogs, settings, account management. Native signal/slot syntax, Qt Designer UI files compiled to Python.

## Structure

```
src/bitmessageqt/
├── mainwindow.py      # Main app window (~1000+ lines, FIXME: rewrite)
├── dialogs.py         # Message/address dialogs (FIXME: window title visibility)
├── settings.py        # Settings dialog (FIXME: should be function in plugin)
├── networkstatus.py   # Connection status (FIXME: hardcoded stream no)
├── blacklist.py       # Address blacklisting
├── migrationwizard.py # Database migration UI
├── bitmessageui.py    # Generated UI classes (WARNING: manual changes lost)
├── *.ui              # Qt Designer files (compiled to bitmessageui.py)
├── widgets.py         # UI utilities (pathlib migrated)
├── utils.py          # Avatar/identicon utilities (pathlib migrated)
└── languagebox.py     # Locale selector (pathlib migrated)
```

## Defensive Coding for GUI

### Pathlib Migration Status
- ✅ **widgets.py**: 3/3 os.path usages migrated
- ✅ **utils.py**: 4/4 os.path usages migrated
- ✅ **languagebox.py**: 3/3 os.path usages migrated
- ✅ **settings.py**: 1/1 os.path usage migrated

### Pydantic for User Input (Critical)

GUI validates all user input before processing:

```python
# Example: Address input validation with Pydantic
from pydantic import BaseModel, field_validator, ValidationError

class AddressInput(BaseModel):
    address: str
    label: str | None = None
    channel: int | None = None

    @field_validator('address')
    @classmethod
    def validate_address(cls, v: str) -> str:
        if not v.startswith('BM-'):
            raise ValueError('Must be a Bitmessage address')
        # Additional validation per protocol spec
        return v

# Usage in dialog:
try:
    validated = AddressInput(address=user_input)
except ValidationError as e:
    self.show_error(f"Invalid address: {e}")
```

### Qt6 Specifics

- Native signal/slot syntax: `self.signal.connect(self.slot)`
- UI files: `.ui` → `pyuic6` → `bitmessageui.py`
- Custom widgets: Extend generated classes, don't modify
- Thread safety: Use `QtCore.QTimer` for UI updates from workers
- **Never** block the main event loop with long operations

## Anti-Patterns (This Module)

- **0 .format() calls** (mainwindow.py) - convert to f-strings (Phase 3 complete ✅)
- **Type hints**: Partial coverage in main modules (Phase 4)
- **FIXME: newlocale, impossible condition** (mainwindow.py)
- **FIXME: rewrite loops, reuse utils** (mainwindow.py)
- **TODO: move to l10n, popMenu** (mainwindow.py)
- **WARNING: manual changes lost** (bitmessageui.py - generated file)

## Where to Look

| Task | Location |
|------|----------|
| Main window logic | `mainwindow.py` |
| Settings dialog | `settings.py` |
| Message dialogs | `dialogs.py` |
| Connection status | `networkstatus.py` |
| UI definitions | `*.ui` files |
| Generated UI code | `bitmessageui.py` |
| UI utilities | `widgets.py`, `utils.py` |

## Known Issues

- `mainwindow.py`: Needs complete rewrite (1000+ line complexity)
- `dialogs.py`: Window title visibility issues
- `settings.py`: Should be plugin function, not core dialog
- `networkstatus.py`: Hardcoded stream number
- `bitmessageui.py`: Auto-generated, manual edits will be lost