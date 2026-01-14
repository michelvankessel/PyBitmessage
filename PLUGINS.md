# PyBitmessage Plugins Documentation

PyBitmessage uses a plugin-based architecture for various system integrations. Most of these are discovered automatically at startup.

## OS Compatibility Matrix

| Category | Plugin Name | Source File | Compatibility | Primary OS / Requirements |
| :--- | :--- | :--- | :--- | :--- |
| **Notifications** | `notify2` | `notification_notify2.py` | Linux | Requires `gi` (GObject) & `notify2` |
| **Indicators** | `libmessaging` | `indicator_libmessaging.py` | Linux | Integration with Ubuntu/GNOME Messaging Menu. Requires `gi`. |
| **Desktop** | `freedesktop` | `desktop_xdg.py` | Linux | Follows XDG standards. Requires `pyxdg`. |
| **Sound** | `theme.canberra` | `sound_canberra.py` | Linux | Uses Libcanberra. Requires `pycanberra`. |
| **Sound** | `file.gstreamer` | `sound_gstreamer.py` | Linux (Hybrid) | Requires GStreamer & `gi`. |
| **Sound** | `file.fallback` | `sound_playfile.py` | Universal | Uses `winsound` on Windows; command line players on others. |
| **GUI Menus** | `address.qrcode` | `menu_qrcode.py` | Universal | Generates QR codes. Requires `qrcode` library. |
| **Network** | `proxyconfig` | `proxyconfig_stem.py` | Universal | Tor integration. Requires `stem`. |

---

## Detailed Breakdown

### 🐧 Linux Specific

These plugins rely on the **Freedesktop** standards or **GNOME** libraries (`gi`). On macOS or Windows, the application will attempt to load them, fail silently (at `DEBUG` level), and skip them.

- **`notify2`**: Native desktop notifications using the DBus protocol.
- **`libmessaging`**: The envelope icon in the Ubuntu top bar that turns green/blue.
- **`freedesktop`**: Used for locating system icons and creating `.desktop` files.
- **`theme.canberra`**: A specialized driver for themed system sounds.

### 🍏 macOS Support

macOS support is largely handled by the **Qt Framework** directly rather than external plugins.

- **Notifications**: Handled via Qt's native system tray integration.
- **Sound**: Handled either by Qt or the `sound_playfile` fallback.
- **Icons**: Handled by the Mac-specific resource bundle (.icns).

### 🖥️ Windows Support

- **Sound**: The `file.fallback` plugin has a special case for `winsound` which is native to Windows.
- **Notifications**: Handled by Qt's system tray alerts.

### 🌐 Universal Plugins

- **`address.qrcode`**: Adds a "Show QR Code" option to the right-click menu of any address. It is pure Python and works everywhere if the `qrcode` library is installed.
- **`proxyconfig_stem`**: Allows advanced Tor configuration. Works on all platforms where Tor can be run.

## Why do I see errors on macOS?

If you see `ModuleNotFoundError: No module named 'gi'` in your logs, it is simply the Plugin Manager testing if the Linux notification systems are available. Since you are on macOS, these are skipped, and the app uses the built-in Qt notification system instead.
