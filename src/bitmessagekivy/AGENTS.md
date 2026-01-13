# PyBitmessage Kivy Mobile UI Agent Guidelines

**Branch:** `(based on working dir)` | **Generated:** 2026-01-13

## OVERVIEW
Kivy-based mobile interface for iOS/Android with Material Design components, touch-first UX, and platform-specific adaptations.

## STRUCTURE
```
src/bitmessagekivy/
├── baseclass/         # Screen controllers (MVC pattern)
├── kv/               # Kivy language UI templates
├── tests/            # Telenium-based mobile UI tests
├── mpybit.py         # Main app entry (NavigateApp)
├── kivy_state.py     # Mobile app state management
├── get_platform.py   # iOS/Android/desktop detection
├── screens_data.json # Screen routing configuration
└── main.kv           # Root layout definition
```

## WHERE TO LOOK
| Task | Location | Kivy Pattern |
|------|----------|--------------|
| **Screen navigation** | `screens_data.json` + `baseclass/` | JSON-defined routes |
| **UI layouts** | `kv/*.kv` files | Kivy language declarative UI |
| **Touch interactions** | `baseclass/common.py` | Mobile gesture handling |
| **Platform detection** | `get_platform.py` | Android/iOS/desktop branching |
| **State management** | `kivy_state.py` | Screen-specific state vars |
| **QR scanning** | `baseclass/scan_screen.py` | Camera integration |
| **File management** | `mpybit.py` file_manager methods | Android storage permissions |

## CONVENTIONS
- **KivyMD components**: Material Design for mobile consistency
- **Screen-based architecture**: Each screen = separate controller + .kv template
- **Touch-first design**: dp() units, swipe gestures, bottom sheets
- **Platform branching**: `platform == "android"` for mobile-specific logic
- **Async operations**: `Clock.schedule_once()` for non-blocking UI updates
- **State separation**: `KivyStateVariables` isolated from core `state.py`

## ANDROID SPECIFICS
- **Storage permissions**: Runtime permission requests for file access
- **Camera handling**: `KIVY_CAMERA=opencv` env var for non-mobile platforms
- **Path adaptation**: `ANDROID_PRIVATE` env var for app-specific directories
- **Dialog sizing**: Different width constants for mobile vs desktop
- **Toast notifications**: Platform-appropriate feedback messages

## ANTI-PATTERNS
- **Never block UI thread**: Long operations must use `Clock.schedule()`
- **No hardcoded paths**: Use `get_platform()` for platform-specific logic
- **Avoid global state**: Keep screen state in `KivyStateVariables`, not globals
- **Don't mix UI logic**: Keep business logic out of .kv files
- **No direct file system access**: Always check Android permissions first

## MOBILE UI PATTERNS
- **Navigation drawer**: Material Design side navigation pattern
- **Bottom sheets**: `MDCustomBottomSheet` for contextual actions
- **Swipe actions**: `MDCardSwipe` for message operations
- **Floating buttons**: Primary actions in lower-right corner
- **Responsive dialogs**: Different sizes for mobile vs desktop
- **Avatar handling**: Identicon generation with custom image override