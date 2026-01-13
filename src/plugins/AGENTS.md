# PyBitmessage Plugins Agent Guidelines

**Generated:** 2026-01-13

## OVERVIEW
Optional plugin system for QR codes, notifications, audio alerts, desktop integration via setuptools entry points with conditional loading based on extras_require dependencies.

## STRUCTURE
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

## WHERE TO LOOK
- **Plugin Discovery**: `plugin.py` - `get_plugins()` iterates entry points using importlib.metadata
- **QR codes**: `menu_qrcode.py` - Shows BM address QR in modal dialog, requires `[qrcode]`
- **Notifications**: `notification_notify2.py` - Uses gi.repository.Notify, requires `[gir,notify2]`
- **Audio**: `sound_canberra.py` - pycanberra theme sounds, `sound_gstreamer.py` - gstreamer playback
- **Desktop**: `desktop_xdg.py` - XDG autostart via pyxdg, requires `[xdg]`
- **Tor**: `proxyconfig_stem.py` - Stem-based hidden service config, requires `[tor]`

## PLUGIN REGISTRATION
Entry points in setup.py define plugin groups:
- `bitmessage.gui.menu` - Context menu extensions
- `bitmessage.notification.message` - Desktop notifications  
- `bitmessage.notification.sound` - Audio alerts
- `bitmessage.indicator` - System tray indicators
- `bitmessage.desktop` - Desktop environment integration
- `bitmessage.proxyconfig` - Proxy configuration

## HOOK SYSTEM
Each plugin exports `connect_plugin()` function returning callback tuple:
`(callback_function, menu_text)` for menus or direct function for notifications.

## ISOLATION
Plugins load conditionally - missing dependencies don't break core. Entry point brackets specify extras: `[qrcode]`, `[gir]`, `[notify2]`, `[sound]`, `[xdg]`, `[tor]`.
