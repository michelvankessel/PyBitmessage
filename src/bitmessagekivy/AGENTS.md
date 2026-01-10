# PyBitmessage Kivy Mobile UI Agent Guidelines

**Branch:** `(based on working dir)` | **Generated:** 2026-01-10 | **Updated:** 2026-01-10

## Overview

Kivy-based mobile interface for iOS/Android. Separate test suite (bitmessagekivy/tests/). Uses KivyMD for Material Design components.

## Structure

```
src/bitmessagekivy/
├── baseclass/         # Screen implementations (inbox, sent, drafts, settings, etc.)
│   ├── inbox.py       # Inbox screen logic
│   ├── sent.py        # Sent messages screen
│   ├── draft.py       # Draft messages screen
│   ├── addressbook.py # Address book management (pathlib migrated)
│   ├── maildetail.py  # Message detail view (pathlib migrated)
│   ├── myaddress.py   # My addresses screen (pathlib migrated)
│   ├── scan_screen.py # QR code scanner (pathlib migrated)
│   └── common.py      # Shared widgets and utilities (pathlib migrated)
├── tests/             # Kivy-specific tests (16 files)
│   ├── test_*.py      # Screen-specific test modules
│   └── telenium_process.py # Telenium test runner (pathlib migrated)
├── mpybit.py          # Main Kivy app class (pathlib migrated - 20 os.path → 0)
├── kivy_helper_search.py # Search utilities
├── kivy_state.py      # Kivy app state management (pathlib migrated)
├── base_navigation.py # Navigation drawer logic
├── uikivysignaler.py  # UI signal handling
├── kv/                # Kivy template files (.kv)
├── main.kv            # Main app layout
└── screens_data.json  # Screen configuration (pathlib migrated)

Pathlib Migration Status: ✅ Complete (all 8 files migrated)
```

## Commands

```bash
# Run Kivy tests
uv run pytest src/bitmessagekivy/tests/

# Run specific Kivy screen test
uv run pytest src/bitmessagekivy/tests/test_inbox.py

# Mobile app entry point
uv run python3.13 src/mockbm/kivy_main.py
```

## Conventions

- **Python 3.13+** (inherits from parent)
- **KivyMD** for Material Design components
- **Kivy language (.kv)** for UI layouts
- **Telenium** for UI testing framework
- **Screen-based navigation** with JSON configuration
- **Mobile-first** touch interface patterns
- **Pathlib** for all path operations (migrated)

## Defensive Coding for Mobile

### Mobile-Specific Considerations

| Concern | Implementation | Notes |
|---------|----------------|-------|
| **Android storage** | Use `Path.home() / ".config"` on Android | Environment detection needed |
| **Image paths** | Use `pathlib.Path` for avatar/image directories | Migrated in Phase 2 |
| **QR code scanning** | Validate scanned addresses before use | TODO: add Pydantic validation |
| **Offline storage** | SQLite + filesystem with proper escaping | Already implemented |
| **Thread safety** | Use `threading.local()` for app state | Future-proof for GIL-free |

### Pydantic for User Input (Recommended)

Mobile users provide input through touch interfaces - validation is critical:

```python
# Example: Address input validation
from pydantic import BaseModel, ValidationError, field_validator

class AddressInput(BaseModel):
    address: str
    label: str | None = None

    @field_validator('address')
    @classmethod
    def validate_address(cls, v: str) -> str:
        if not v.startswith('BM-'):
            raise ValueError('Address must start with BM-')
        # Add more validation as per protocol
        return v
```

## Anti-Patterns (This Module)

- **18 .format() calls** in tests - convert to f-strings (Phase 3)
- **TODO: get_free_credits, sc18 screen** (payment.py)
- **TODO: checkLabel_valid, checkAddress_valid** (popup.kv)
- **Type hints**: Partial coverage - needs Phase 4 completion

## Where to Look

| Task | Location |
|------|----------|
| Main app | `mpybit.py` - NavigateApp class ✅ pathlib complete |
| Screen logic | `baseclass/` - individual screen files (8/8 migrated) |
| UI layouts | `kv/` - Kivy template files |
| Navigation | `base_navigation.py` - drawer and routing |
| State management | `kivy_state.py` - app state variables ✅ pathlib complete |
| Tests | `bitmessagekivy/tests/` - Telenium-based UI tests ✅ pathlib complete |
| Mock testing | `src/mockbm/kivy_main.py` - test entry point |

## Known Issues (FIXME)

- Test files: 18 .format() calls need f-string conversion (Phase 3)
- Payment screen: incomplete get_free_credits implementation
- Address validation: TODO in popup.kv templates
- Type hints: Partial coverage in screen modules (Phase 4)