# PyBitmessage Kivy Mobile UI Agent Guidelines

**Branch:** `(based on working dir)` | **Generated:** 2026-01-10

## Overview

Kivy-based mobile interface for iOS/Android. Separate test suite (bitmessagekivy/tests/). Uses KivyMD for Material Design components.

## Structure

```
src/bitmessagekivy/
├── baseclass/         # Screen implementations (inbox, sent, drafts, settings, etc.)
│   ├── inbox.py       # Inbox screen logic
│   ├── sent.py        # Sent messages screen
│   ├── draft.py       # Draft messages screen
│   ├── addressbook.py # Address book management
│   ├── maildetail.py  # Message detail view
│   ├── msg_composer.py # Message composition
│   └── common.py      # Shared widgets and utilities
├── tests/             # Kivy-specific tests (16 files)
│   ├── test_*.py      # Screen-specific test modules
│   └── telenium_process.py # Telenium test runner
├── mpybit.py          # Main Kivy app class (20 os.path usages)
├── kivy_helper_search.py # Search utilities
├── kivy_state.py      # Kivy app state management
├── base_navigation.py # Navigation drawer logic
├── uikivysignaler.py  # UI signal handling
├── kv/                # Kivy template files (.kv)
├── main.kv            # Main app layout
└── screens_data.json  # Screen configuration
```

## Commands

```bash
# Run Kivy tests
PYTHONPATH=src python3.13 -m pytest src/bitmessagekivy/tests/

# Run specific Kivy screen test
PYTHONPATH=src python3.13 -m pytest src/bitmessagekivy/tests/test_inbox.py

# Mobile app entry point
PYTHONPATH=src python3.13 src/mockbm/kivy_main.py
```

## Conventions

- **Python 3.13+** (inherits from parent)
- **KivyMD** for Material Design components
- **Kivy language (.kv)** for UI layouts
- **Telenium** for UI testing framework
- **Screen-based navigation** with JSON configuration
- **Mobile-first** touch interface patterns

## Anti-Patterns (This Module)

- **20 os.path usages** (mpybit.py) - migrate to pathlib
- **18 .format() calls** in tests - convert to f-strings
- **TODO: get_free_credits, sc18 screen** (payment.py)
- **TODO: checkLabel_valid, checkAddress_valid** (popup.kv)
- **type: ignore** on kivy_main.py import (src/mockbm/)

## Where to Look

| Task | Location |
|------|----------|
| Main app | `mpybit.py` - NavigateApp class |
| Screen logic | `baseclass/` - individual screen files |
| UI layouts | `kv/` - Kivy template files |
| Navigation | `base_navigation.py` - drawer and routing |
| State management | `kivy_state.py` - app state variables |
| Tests | `bitmessagekivy/tests/` - Telenium-based UI tests |
| Mock testing | `src/mockbm/kivy_main.py` - test entry point |

## Known Issues (FIXME)

- `mpybit.py`: 20 os.path.join() calls need pathlib migration
- Test files: 18 .format() calls need f-string conversion
- Payment screen: incomplete get_free_credits implementation
- Address validation: TODO in popup.kv templates