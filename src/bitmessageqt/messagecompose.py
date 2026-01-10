"""
Message editor with a wheel zoom functionality
"""


from PyQt6 import QtCore, QtWidgets


class MessageCompose(QtWidgets.QTextEdit):
    """Editor class with wheel zoom functionality"""
    def __init__(self, parent=None):
        super(MessageCompose, self).__init__(parent)
        self.setAcceptRichText(False)
        self.defaultFontPointSize = self.currentFont().pointSize()

    def wheelEvent(self, e):
        """Mouse wheel scroll event handler"""
        if e is None:
            return
        if (
            QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.KeyboardModifier.ControlModifier
        ) == QtCore.Qt.KeyboardModifier.ControlModifier:
            angle_delta = e.angleDelta()
            delta = angle_delta.y() if angle_delta is not None else 0
            if delta > 0:
                self.zoomIn(1)
            elif delta < 0:
                self.zoomOut(1)
            zoom = self.currentFont().pointSize() * 100 / self.defaultFontPointSize
            active_window = QtWidgets.QApplication.activeWindow()
            if active_window is not None:
                status_bar_func = getattr(active_window, 'statusBar', None)
                if status_bar_func is not None and callable(status_bar_func):
                    status_bar = status_bar_func()
                    if status_bar is not None:
                        status_bar.showMessage(
                            QtWidgets.QApplication.translate("MainWindow", "Zoom level {}%").format(
                                int(zoom)
                            )
                        )
        else:
            # in QTextEdit, super does not zoom, only scroll
            super(MessageCompose, self).wheelEvent(e)

    def reset(self):
        """Clear the edit content"""
        self.setText('')
