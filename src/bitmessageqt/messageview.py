"""
Custom message viewer with support for switching between HTML and plain
text rendering, HTML sanitization, lazy rendering (as you scroll down),
zoom and URL click warning popup

"""

from PyQt6 import QtCore, QtGui, QtWidgets

from .safehtmlparser import SafeHTMLParser
from tr import _translate


class MessageView(QtWidgets.QTextBrowser):
    """Message content viewer class, can switch between plaintext and HTML"""

    MODE_PLAIN = 0
    MODE_HTML = 1

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super(MessageView, self).__init__(parent)
        self.mode = MessageView.MODE_PLAIN
        self.html: SafeHTMLParser | None = None
        self.setOpenExternalLinks(False)
        self.setOpenLinks(False)
        self.anchorClicked.connect(self.confirmURL)
        self.out = ""
        self.outpos = 0
        doc = self.document()
        if doc is not None:
            doc.setUndoRedoEnabled(False)
        self.rendering = False
        self.defaultFontPointSize = self.currentFont().pointSize()
        scrollbar = self.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.valueChanged.connect(self.lazyRender)
        self.setWrappingWidth()

    def resizeEvent(self, a0):
        """View resize event handler"""
        super(MessageView, self).resizeEvent(a0)
        if a0 is not None:
            self.setWrappingWidth(a0.size().width())

    def mousePressEvent(self, ev):
        """Mouse press button event handler"""
        if ev is None:
            return
        if (
            ev.button() == QtCore.Qt.MouseButton.LeftButton
            and self.html
            and self.html.has_html
            and self.cursorForPosition(ev.position().toPoint()).block().blockNumber()
            == 0
        ):
            if self.mode == MessageView.MODE_PLAIN:
                self.showHTML()
            else:
                self.showPlain()
        else:
            super(MessageView, self).mousePressEvent(ev)

    def wheelEvent(self, e):
        """Mouse wheel scroll event handler"""
        # super will actually automatically take care of zooming
        super(MessageView, self).wheelEvent(e)
        if e is None:
            return
        # Check for wheel orientation if available
        angle_delta = e.angleDelta()
        is_vertical = angle_delta is not None and angle_delta.y() != 0
        if (
            QtWidgets.QApplication.queryKeyboardModifiers()
            & QtCore.Qt.KeyboardModifier.ControlModifier
        ) == QtCore.Qt.KeyboardModifier.ControlModifier and is_vertical:
            zoom = self.currentFont().pointSize() * 100 / self.defaultFontPointSize
            active_window = QtWidgets.QApplication.activeWindow()
            if active_window is not None:
                status_bar_func = getattr(active_window, "statusBar", None)
                if status_bar_func is not None and callable(status_bar_func):
                    status_bar = status_bar_func()
                    if status_bar is not None:
                        status_bar.showMessage(
                            _translate("MainWindow", f"Zoom level {int(zoom)}%")
                        )

    def setWrappingWidth(self, width=None):
        """Set word-wrapping width"""
        self.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.FixedPixelWidth)
        if width is None:
            width = self.width()
        self.setLineWrapColumnOrWidth(width)

    def confirmURL(self, link):
        """Show a dialog requesting URL opening confirmation"""
        if link.scheme() == "mailto":
            window = QtWidgets.QApplication.activeWindow()
            if window is not None:
                ui = getattr(window, "ui", None)
                if ui is not None:
                    if hasattr(ui, "lineEditTo"):
                        ui.lineEditTo.setText(link.path())
                    if link.hasQueryItem("subject") and hasattr(ui, "lineEditSubject"):
                        ui.lineEditSubject.setText(link.queryItemValue("subject"))
                    if link.hasQueryItem("body") and hasattr(ui, "textEditMessage"):
                        ui.textEditMessage.setText(link.queryItemValue("body"))
                set_send_func = getattr(window, "setSendFromComboBox", None)
                if set_send_func is not None and callable(set_send_func):
                    set_send_func()
                if ui is not None:
                    if hasattr(ui, "tabWidgetSend"):
                        ui.tabWidgetSend.setCurrentIndex(0)
                    if hasattr(ui, "tabWidget") and hasattr(ui, "send"):
                        ui.tabWidget.setCurrentIndex(ui.tabWidget.indexOf(ui.send))
                    if hasattr(ui, "textEditMessage"):
                        ui.textEditMessage.setFocus()
            return
        reply = QtWidgets.QMessageBox.warning(
            self,
            QtWidgets.QApplication.translate("MessageView", "Follow external link"),
            QtWidgets.QApplication.translate(
                "MessageView",
                f'The link "{link.toString()}" will open in a browser. It may be a security risk, it could de-anonymise you'
                f" or download malicious data. Are you sure?",
            ),
            QtWidgets.QMessageBox.StandardButton.Yes,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            QtGui.QDesktopServices.openUrl(link)

    def loadResource(self, type, name):
        """
        Callback for loading referenced objects, such as an image. For security reasons at the moment doesn't do
        anything)
        """
        pass

    def lazyRender(self):
        """
        Partially render a message. This is to avoid UI freezing when loading huge messages. It continues loading as
        you scroll down.
        """
        if self.rendering:
            return
        self.rendering = True
        scrollbar = self.verticalScrollBar()
        doc = self.document()
        if scrollbar is None or doc is None:
            return
        position = scrollbar.value()
        cursor = QtGui.QTextCursor(doc)
        while (
            self.outpos < len(self.out)
            and scrollbar.value() >= doc.size().height() - 2 * self.size().height()
        ):
            startpos = self.outpos
            self.outpos += 10240
            # find next end of tag
            if self.mode == MessageView.MODE_HTML:
                pos = self.out.find(">", self.outpos)
                if pos > self.outpos:
                    self.outpos = pos + 1
            cursor.movePosition(
                QtGui.QTextCursor.MoveOperation.End,
                QtGui.QTextCursor.MoveMode.MoveAnchor,
            )
            cursor.insertHtml(self.out[startpos:self.outpos])
        scrollbar.setValue(position)
        self.rendering = False

    def showPlain(self):
        """Render message as plain text."""
        self.mode = MessageView.MODE_PLAIN
        if self.html is None:
            return
        out = self.html.raw
        if self.html.has_html:
            out = (
                '<div align="center" style="text-decoration: underline;"><b>'
                + str(
                    QtWidgets.QApplication.translate(
                        "MessageView", "HTML detected, click here to display"
                    )
                )
                + "</b></div><br/>"
                + out
            )
        self.out = out
        self.outpos = 0
        self.setHtml("")
        self.lazyRender()

    def showHTML(self):
        """Render message as HTML"""
        self.mode = MessageView.MODE_HTML
        if self.html is None:
            return
        out = self.html.sanitised
        out = (
            '<div align="center" style="text-decoration: underline;"><b>'
            + str(
                QtWidgets.QApplication.translate(
                    "MessageView", "Click here to disable HTML"
                )
            )
            + "</b></div><br/>"
            + out
        )
        self.out = out
        self.outpos = 0
        self.setHtml("")
        self.lazyRender()

    def setContent(self, data):
        """Set message content from argument"""
        self.html = SafeHTMLParser()
        self.html.reset()
        self.html.reset_safe()
        self.html.allow_picture = True
        self.html.feed(data)
        self.html.close()
        self.showPlain()
