# PyBitmessage Plugins Agent Guidelines

**Branch:** `(based on working dir)` | **Generated:** 2026-01-10 | **Updated:** 2026-01-11

## Overview

Optional plugin system for audio, notifications, QR codes, desktop integration. Plugins load conditionally based on extras_require dependencies.

## Structure

```
src/plugins/
├── plugin.py              # Plugin discovery (importlib.metadata)
├── menu_qrcode.py         # QR code in address menu
├── notification_notify2.py # Desktop notifications (notify2)
├── indicator_libmessaging.py # Desktop indicator (libmessaging)
├── sound_canberra.py      # Audio alerts (pycanberra)
├── sound_gstreamer.py     # Audio alerts (gstreamer)
├── sound_playfile.py      # Audio alerts (simple playback)
├── desktop_xdg.py         # Freedesktop integration
└── proxyconfig_stem.py    # Tor proxy configuration
```

## Entry Points

Defined in setup.py:
- `bitmessage.gui.menu` - Context menu extensions
- `bitmessage.notification.message` - Desktop notifications  
- `bitmessage.notification.sound` - Audio alerts
- `bitmessage.indicator` - System tray indicators
- `bitmessage.desktop` - Desktop environment integration
- `bitmessage.proxyconfig` - Proxy configuration

## Plugin Discovery

`plugin.py` provides `get_plugins(group, point, name, fallback)` - iterates entry points matching criteria. Uses modern importlib.metadata with pkg_resources fallback.

## Where to Look

- **QR codes**: `menu_qrcode.py` - Shows BM address QR in modal dialog
- **Notifications**: `notification_notify2.py` - Uses gi.repository.Notify
- **Audio**: `sound_canberra.py` - pycanberra theme sounds
- **Desktop**: `desktop_xdg.py` - XDG autostart via pyxdg
- **Tor**: `proxyconfig_stem.py` - Stem-based hidden service config

## Dependencies

Plugins require extras: `[qrcode]`, `[gir]`, `[notify2]`, `[sound]`, `[xdg]`, `[tor]`. Install via `pip install pybitmessage[qrcode,tor]` etc.