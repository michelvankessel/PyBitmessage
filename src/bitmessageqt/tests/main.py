"""Common definitions for bitmessageqt tests"""

import sys
import unittest

from PyQt6 import QtCore, QtWidgets
import queue

import bitmessageqt
import queues
from bmconfigparser import config

_translate = QtCore.QCoreApplication.translate


class TestBase(unittest.TestCase):
    """Base class for bitmessageqt test case"""

    @classmethod
    def setUpClass(cls):
        """Provide the UI test cases with common settings"""
        cls.config = config

    def setUp(self):
        self.app = (
            QtWidgets.QApplication.instance()
            or bitmessageqt.BitmessageQtApplication(sys.argv)
        )
        self.window = QtWidgets.QApplication.activeWindow()
        if not self.window:
            self.window = bitmessageqt.MyForm()
            self.window.appIndicatorInit(self.app)

    def tearDown(self):
        """Search for exceptions in closures called by timer and fail if any"""
        # self.app.deleteLater()
        concerning = []
        while True:
            try:
                thread, exc = queues.excQueue.get(block=False)
            except queue.Empty:
                break
            if thread == "tests":
                concerning.append(exc)
        if concerning:
            self.fail(
                "Exceptions found in the main thread:\n%s"
                % "\n".join((str(e) for e in concerning))
            )


class TestMain(unittest.TestCase):
    """Test case for main window - basic features"""

    def test_translate(self):
        """Check the results of _translate() with various args"""
        self.assertIsInstance(
            _translate("MainWindow", "Test", None),
            str,  # PyQt6 returns Python strings, not QString
        )


class TestUISignaler(TestBase):
    """Test case for UISignalQueue"""

    def test_updateStatusBar(self):
        """Check arguments order of updateStatusBar command"""
        queues.UISignalQueue.put(
            (
                "updateStatusBar",
                (_translate("test", "Testing updateStatusBar...", None), 1),
            )
        )

        QtCore.QTimer.singleShot(60, self.app.quit)
        self.app.exec()
        # self.app.processEvents(QtCore.QEventLoop.AllEvents, 60)
