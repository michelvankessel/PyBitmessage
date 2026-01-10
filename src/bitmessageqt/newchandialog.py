"""
src/bitmessageqt/newchandialog.py
=================================

"""

from PyQt6 import QtCore, QtWidgets

from addresses import addBMIfNotPresent
from queues import addressGeneratorQueue, apiAddressGeneratorReturnQueue, UISignalQueue
from tr import _translate
from . import widgets
from .addressvalidator import AddressValidator, PassPhraseValidator
from .utils import str_chan


class NewChanDialog(QtWidgets.QDialog):
    """The `New Chan` dialog"""

    # UI widgets loaded from newchandialog.ui - type hints for pyright
    chanAddress: QtWidgets.QLineEdit
    chanPassPhrase: QtWidgets.QLineEdit
    validatorFeedback: QtWidgets.QLabel
    buttonBox: QtWidgets.QDialogButtonBox

    def __init__(self, parent=None):
        super(NewChanDialog, self).__init__(parent)
        widgets.load("newchandialog.ui", self)
        self._parent = parent  # Avoid shadowing QObject.parent()
        self.chanAddress.setValidator(
            AddressValidator(
                self.chanAddress,
                self.chanPassPhrase,
                self.validatorFeedback,
                self.buttonBox,
                False,
            )
        )
        self.chanPassPhrase.setValidator(
            PassPhraseValidator(
                self.chanPassPhrase,
                self.chanAddress,
                self.validatorFeedback,
                self.buttonBox,
                False,
            )
        )

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.delayedUpdateStatus)
        self.timer.start(500)  # milliseconds
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.show()

    def delayedUpdateStatus(self):
        """Related to updating the UI for the chan passphrase validity"""
        self.chanPassPhrase.validator().checkQueue()

    def accept(self):
        """Proceed in joining the chan"""
        self.timer.stop()
        self.hide()
        apiAddressGeneratorReturnQueue.queue.clear()
        if self.chanAddress.text() == "":
            addressGeneratorQueue.put(
                (
                    "createChan",
                    4,
                    1,
                    str_chan + " " + str(self.chanPassPhrase.text()),
                    self.chanPassPhrase.text(),
                    True,
                )
            )
        else:
            addressGeneratorQueue.put(
                (
                    "joinChan",
                    addBMIfNotPresent(self.chanAddress.text()),
                    str_chan + " " + str(self.chanPassPhrase.text()),
                    self.chanPassPhrase.text(),
                    True,
                )
            )
        addressGeneratorReturnValue = apiAddressGeneratorReturnQueue.get(True)
        if (
            addressGeneratorReturnValue
            and addressGeneratorReturnValue[0] != "chan name does not match address"
        ):
            UISignalQueue.put(
                (
                    "updateStatusBar",
                    _translate(
                        "newchandialog",
                        f"Successfully created / joined chan {self.chanPassPhrase.text()}",
                    ),
                )
            )
            if self._parent is not None and hasattr(self._parent, "ui"):
                self._parent.ui.tabWidget.setCurrentIndex(
                    self._parent.ui.tabWidget.indexOf(self._parent.ui.chans)
                )
            self.done(QtWidgets.QDialog.DialogCode.Accepted)
        else:
            UISignalQueue.put(
                (
                    "updateStatusBar",
                    _translate("newchandialog", "Chan creation / joining failed"),
                )
            )
            self.done(QtWidgets.QDialog.DialogCode.Rejected)

    def reject(self):
        """Cancel joining the chan"""
        self.timer.stop()
        self.hide()
        UISignalQueue.put(
            (
                "updateStatusBar",
                _translate("newchandialog", "Chan creation / joining cancelled"),
            )
        )
        self.done(QtWidgets.QDialog.DialogCode.Rejected)
