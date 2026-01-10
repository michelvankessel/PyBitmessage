"""Status bar Module"""

from time import time
from PyQt6 import QtWidgets, QtCore


class BMStatusBar(QtWidgets.QStatusBar):
    """Status bar with queue and priorities"""
    duration = 10000
    deleteAfter = 60

    def __init__(self, parent=None):
        super(BMStatusBar, self).__init__(parent)
        self.important = []
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.processQueue)
        self.timer.start(BMStatusBar.duration)
        self.iterator = 0

    def setStatus(self, message):
        self.showMessage(message)

    def setSpeed(self, speed):
        self.speed = speed
        self.updateStatus()

    def processQueue(self):
        currentTime = time()
        # Filter out expired messages
        self.important = [
            m for m in self.important
            if currentTime <= m[1] + BMStatusBar.deleteAfter
        ]

        if not self.important:
            super(BMStatusBar, self).showMessage("", 0)
            self.iterator = 0
            return

        # Advance iterator and wrap around
        self.iterator = (self.iterator + 1) % len(self.important)

        # Show the current message
        super(BMStatusBar, self).showMessage(self.important[self.iterator][0], 0)

    def addImportant(self, message):
        self.important.append([message, time()])
        self.iterator = len(self.important) - 2
        self.processQueue()
