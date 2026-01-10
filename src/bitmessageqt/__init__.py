"""
PyQt based UI for bitmessage - Package initialization
This module provides the main UI components for the bitmessage client.
"""

# Import the main window class for backward compatibility
from .mainwindow import MyForm, BitmessageQtApplication

# Import utility functions that might be needed by other modules
from .mainwindow import init, run

# Define what should be exported when doing "from bitmessageqt import *"
__all__ = ["MyForm", "BitmessageQtApplication", "init", "run"]

# Additional imports that might be needed for backward compatibility
# These maintain the existing API while keeping implementation in mainwindow.py
try:
    from .mainwindow import app, myapp
except ImportError:
    # These globals might not be available during initial import
    app = None
    myapp = None
