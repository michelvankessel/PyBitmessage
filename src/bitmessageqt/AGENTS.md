# PyBitmessage Qt6 GUI Agent Guidelines

**Branch:** `(based on working dir)` | **Generated:** 2026-01-10

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
└── *.ui              # Qt Designer files (compiled to bitmessageui.py)
```

## Anti-Patterns (This Module)

- **25+ .format() calls** (mainwindow.py) - convert to f-strings
- **11 os.path usages** (mainwindow.py) - migrate to pathlib
- **FIXME: newlocale, impossible condition** (mainwindow.py)
- **FIXME: rewrite loops, reuse utils** (mainwindow.py)
- **TODO: move to l10n, popMenu** (mainwindow.py)
- **WARNING: manual changes lost** (bitmessageui.py - generated file)

## Qt6 Specifics

- Native signal/slot syntax: `self.signal.connect(self.slot)`
- UI files: `.ui` → `pyuic6` → `bitmessageui.py`
- Custom widgets: Extend generated classes, don't modify
- Thread safety: Use `QtCore.QTimer` for UI updates from workers

## Where to Look

| Task | Location |
|------|----------|
| Main window logic | `mainwindow.py` |
| Settings dialog | `settings.py` |
| Message dialogs | `dialogs.py` |
| Connection status | `networkstatus.py` |
| UI definitions | `*.ui` files |
| Generated UI code | `bitmessageui.py` |

## Known Issues

- `mainwindow.py`: Needs complete rewrite (1000+ line complexity)
- `dialogs.py`: Window title visibility issues
- `settings.py`: Should be plugin function, not core dialog
- `networkstatus.py`: Hardcoded stream number
- `bitmessageui.py`: Auto-generated, manual edits will be lost