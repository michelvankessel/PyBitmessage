#!/usr/bin/env python
"""
Utility configured as apinotifypath in bitmessagesettings
when pybitmessage started in test mode.
"""

import importlib
import sys
import tempfile

# Handle both relative import (as module) and absolute import (as standalone script)
if __name__ == '__main__':
    common = importlib.import_module('common')
else:
    common = importlib.import_module('.common', package=__package__)


if __name__ == '__main__':
    if sys.argv[1] == 'startingUp':
        common.put_signal_file(tempfile.gettempdir(), '.api_started')
