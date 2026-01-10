"""Runtime PyInstaller hook to load plugins"""

import os
import sys

homepath = os.path.abspath(os.path.dirname(sys.argv[0]))

os.environ['PATH'] += ';' + ';'.join([
    homepath, os.path.join(homepath, 'Tor'),
    os.path.abspath(os.curdir)
])

try:
    import pybitmessage.plugins.menu_qrcode
    import pybitmessage.plugins.proxyconfig_stem
    # Silence unused import warnings (F401)
    _ = (pybitmessage.plugins.menu_qrcode, pybitmessage.plugins.proxyconfig_stem)
except ImportError:
    pass
