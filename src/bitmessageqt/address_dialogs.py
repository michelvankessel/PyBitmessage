"""
Dialogs that work with BM address.
"""

import hashlib
from typing import Optional, Any, Union

from PyQt6 import QtGui, QtWidgets
from PyQt6.QtWidgets import (
    QLineEdit,
    QLabel,
    QRadioButton,
    QCheckBox,
    QSpinBox,
    QGroupBox,
)

import queues
from . import widgets
import state
from .account import AccountMixin, GatewayAccount, MailchuckAccount, accountClass
from addresses import addBMIfNotPresent, decodeAddress, encodeVarint
from bmconfigparser import config as global_config
from debug import logger
from tr import _translate


class AddressCheckMixin(object):
    """Base address validation class for QT UI"""

    # Type hints for UI widgets loaded from .ui files
    lineEditAddress: QLineEdit
    labelAddressCheck: QLabel

    def __init__(self):
        self.valid = False
        # Guard against MRO calling this before UI is loaded
        if hasattr(self, "lineEditAddress"):
            self.lineEditAddress.textChanged.connect(self.addressChanged)

    def _onSuccess(
        self,
        addressVersion: Optional[int],
        streamNumber: Optional[int],
        ripe: Optional[Union[bytes, str]],
    ) -> None:
        pass

    def addressChanged(self, text: str) -> None:
        """
        Address validation callback, performs validation and gives feedback
        """
        if not text:
            self.valid = False
            return

        result = decodeAddress(str(text))
        if not result or len(result) != 4:
            self.valid = False
            if hasattr(self, "labelAddressCheck"):
                self.labelAddressCheck.setText("")
            return

        status, addressVersion, streamNumber, ripe = result
        self.valid = status == "success"

        if not hasattr(self, "labelAddressCheck"):
            return

        if self.valid:
            self.labelAddressCheck.setText(
                _translate("MainWindow", "Address is valid.")
            )
            # Ensure parameters are valid before calling _onSuccess
            if (
                addressVersion is not None
                and streamNumber is not None
                and ripe is not None
                and isinstance(ripe, bytes)
            ):
                self._onSuccess(addressVersion, streamNumber, ripe)
        elif status == "missingbm":
            self.labelAddressCheck.setText(
                _translate(
                    "MainWindow",  # dialog name should be here
                    "The address should start with ''BM-''",
                )
            )
        elif status == "checksumfailed":
            self.labelAddressCheck.setText(
                _translate(
                    "MainWindow",
                    "The address is not typed or copied correctly"
                    " (the checksum failed).",
                )
            )
        elif status == "versiontoohigh":
            self.labelAddressCheck.setText(
                _translate(
                    "MainWindow",
                    "The version number of this address is higher than this"
                    " software can support. Please upgrade Bitmessage.",
                )
            )
        elif status == "invalidcharacters":
            self.labelAddressCheck.setText(
                _translate("MainWindow", "The address contains invalid characters.")
            )
        elif status == "ripetooshort":
            self.labelAddressCheck.setText(
                _translate(
                    "MainWindow", "Some data encoded in the address is too short."
                )
            )
        elif status == "ripetoolong":
            self.labelAddressCheck.setText(
                _translate(
                    "MainWindow", "Some data encoded in the address is too long."
                )
            )
        elif status == "varintmalformed":
            self.labelAddressCheck.setText(
                _translate(
                    "MainWindow", "Some data encoded in the address is malformed."
                )
            )


class AddressDataDialog(QtWidgets.QDialog, AddressCheckMixin):
    """QDialog with Bitmessage address validation"""

    # Type hints for UI widgets loaded from .ui files
    lineEditAddress: QLineEdit
    lineEditLabel: QLineEdit

    def __init__(self, parent):
        super(AddressDataDialog, self).__init__(parent)
        self.parent = parent

    def accept(self) -> None:
        """Callback for QDIalog accepting value"""
        if self.valid:
            self.data = (
                addBMIfNotPresent(str(self.lineEditAddress.text())),
                self.lineEditLabel.text(),
            )
        else:
            queues.UISignalQueue.put(
                (
                    "updateStatusBar",
                    _translate(
                        "MainWindow",
                        "The address you entered was invalid. Ignoring it.",
                    ),
                )
            )
        super(AddressDataDialog, self).accept()


class AddAddressDialog(AddressDataDialog):
    """QDialog for adding a new address"""

    def __init__(
        self, parent: Optional[Any] = None, address: Optional[str] = None
    ) -> None:
        super(AddAddressDialog, self).__init__(parent)
        widgets.load("addaddressdialog.ui", self)
        AddressCheckMixin.__init__(self)
        if address:
            self.lineEditAddress.setText(address)


class NewAddressDialog(QtWidgets.QDialog):
    """QDialog for generating a new address"""

    # Type hints for UI widgets loaded from .ui files
    radioButtonExisting: QRadioButton
    comboBoxExisting: QtWidgets.QComboBox
    groupBoxDeterministic: QGroupBox
    radioButtonRandomAddress: QRadioButton
    radioButtonMostAvailable: QRadioButton
    newaddresslabel: QLineEdit
    checkBoxEighteenByteRipe: QCheckBox
    lineEditPassphrase: QLineEdit
    lineEditPassphraseAgain: QLineEdit
    spinBoxNumberOfAddressesToMake: QSpinBox

    def __init__(self, parent: Optional[Any] = None) -> None:
        super(NewAddressDialog, self).__init__(parent)
        widgets.load("newaddressdialog.ui", self)

        # Let's fill out the 'existing address' combo box with addresses
        # from the 'Your Identities' tab.
        for address in global_config.addresses(True):
            self.radioButtonExisting.click()
            self.comboBoxExisting.addItem(address)
        self.groupBoxDeterministic.setHidden(True)
        QtWidgets.QWidget.resize(self, QtWidgets.QWidget.sizeHint(self))
        self.show()

    def accept(self) -> None:
        """accept callback"""
        self.hide()
        # self.buttonBox.enabled = False
        if self.radioButtonRandomAddress.isChecked():
            if self.radioButtonMostAvailable.isChecked():
                streamNumberForAddress = 1
            else:
                # User selected 'Use the same stream as an existing
                # address.'
                try:
                    result = decodeAddress(self.comboBoxExisting.currentText())
                    if result and len(result) == 4:
                        streamNumberForAddress = result[2]
                    else:
                        streamNumberForAddress = 1
                except (AttributeError, IndexError, TypeError):
                    streamNumberForAddress = 1

            logger.info("NewAddressDialog: Attempting to create random address. label=%s", self.newaddresslabel.text() if hasattr(self, "newaddresslabel") else "N/A")
            if hasattr(self, "newaddresslabel") and hasattr(
                self, "checkBoxEighteenByteRipe"
            ):
                queues.addressGeneratorQueue.put(
                    (
                        "createRandomAddress",
                        4,
                        streamNumberForAddress,
                        self.newaddresslabel.text(),
                        1,
                        "",
                        self.checkBoxEighteenByteRipe.isChecked(),
                    )
                )
                logger.info("NewAddressDialog: Request put in addressGeneratorQueue")
            else:
                logger.error("NewAddressDialog: Missing required widgets! newaddresslabel=%s, checkBoxEighteenByteRipe=%s",
                             hasattr(self, "newaddresslabel"), hasattr(self, "checkBoxEighteenByteRipe"))
        else:
            if hasattr(self, "lineEditPassphrase") and hasattr(
                self, "lineEditPassphraseAgain"
            ):
                if (
                    self.lineEditPassphrase.text()
                    != self.lineEditPassphraseAgain.text()
                ):
                    QtWidgets.QMessageBox.about(
                        self,
                        _translate("MainWindow", "Passphrase mismatch"),
                        _translate(
                            "MainWindow",
                            "The passphrase you entered twice doesn't match. Try again.",
                        ),
                    )
                elif self.lineEditPassphrase.text() == "":
                    QtWidgets.QMessageBox.about(
                        self,
                        _translate("MainWindow", "Choose a passphrase"),
                        _translate("MainWindow", "You really do need a passphrase."),
                    )
                else:
                    # this will eventually have to be replaced by logic
                    # to determine the most available stream number.
                    streamNumberForAddress = 1
                    if (
                        hasattr(self, "spinBoxNumberOfAddressesToMake")
                        and hasattr(self, "lineEditPassphrase")
                        and hasattr(self, "checkBoxEighteenByteRipe")
                    ):
                        queues.addressGeneratorQueue.put(
                            (
                                "createDeterministicAddresses",
                                4,
                                streamNumberForAddress,
                                "unused deterministic address",
                                self.spinBoxNumberOfAddressesToMake.value(),
                                self.lineEditPassphrase.text(),
                                self.checkBoxEighteenByteRipe.isChecked(),
                            )
                        )


class NewSubscriptionDialog(AddressDataDialog):
    """QDialog for subscribing to an address"""

    # Type hints for UI widgets loaded from .ui files
    checkBoxDisplayMessagesAlreadyInInventory: QCheckBox

    def __init__(self, parent=None):
        super(NewSubscriptionDialog, self).__init__(parent)
        widgets.load("newsubscriptiondialog.ui", self)
        AddressCheckMixin.__init__(self)

    def _onSuccess(self, addressVersion, streamNumber, ripe):
        if not hasattr(self, "checkBoxDisplayMessagesAlreadyInInventory"):
            return

        if addressVersion is not None and addressVersion <= 3:
            self.checkBoxDisplayMessagesAlreadyInInventory.setText(
                _translate(
                    "MainWindow",
                    "Address is an old type. We cannot display its past broadcasts.",
                )
            )
        else:
            # Safe check for state.Inventory and parameters
            if (
                hasattr(state, "Inventory")
                and state.Inventory
                and ripe is not None
                and addressVersion is not None
                and streamNumber is not None
            ):
                try:
                    # Type assertions to guarantee non-None values
                    assert state.Inventory is not None
                    assert addressVersion is not None
                    assert streamNumber is not None
                    assert ripe is not None

                    # Ensure flush method exists and is callable
                    flush_method = state.Inventory.flush
                    assert flush_method is not None
                    flush_method()  # Use the method reference

                    # Encode varints with guaranteed non-None results
                    addr_version_bytes = encodeVarint(addressVersion)
                    stream_num_bytes = encodeVarint(streamNumber)

                    # Type assertion: encodeVarint always returns bytes
                    assert addr_version_bytes is not None
                    assert stream_num_bytes is not None
                    assert isinstance(addr_version_bytes, bytes)
                    assert isinstance(stream_num_bytes, bytes)

                    # Ensure ripe is bytes for cryptographic operations
                    ripe_bytes = (
                        ripe
                        if isinstance(ripe, bytes)
                        else bytes(ripe, "utf-8")
                        if isinstance(ripe, str)
                        else b""
                    )

                    doubleHashOfAddressData = hashlib.sha512(
                        hashlib.sha512(
                            addr_version_bytes + stream_num_bytes + ripe_bytes
                        ).digest()
                    ).digest()
                    tag = doubleHashOfAddressData[32:]

                    # Type assertion for state.Inventory method
                    if hasattr(state.Inventory, "by_type_and_tag"):
                        inventory_method = state.Inventory.by_type_and_tag
                        assert inventory_method is not None
                        self.recent = inventory_method(3, tag)
                        count = len(self.recent) if self.recent else 0
                        if count == 0:
                            self.checkBoxDisplayMessagesAlreadyInInventory.setText(
                                _translate(
                                    "MainWindow",
                                    "There are no recent broadcasts from this address to display.",
                                )
                            )
                        else:
                            self.checkBoxDisplayMessagesAlreadyInInventory.setEnabled(
                                True
                            )
                            self.checkBoxDisplayMessagesAlreadyInInventory.setText(
                                _translate(
                                    "MainWindow",
                                    "Display the %n recent broadcast(s) from this address.",
                                    None,
                                    n=count,
                                )
                            )
                except (AttributeError, TypeError):
                    # Handle case where state.Inventory or its methods are not available
                    self.checkBoxDisplayMessagesAlreadyInInventory.setText(
                        _translate(
                            "MainWindow",
                            "Cannot display broadcasts from this address.",
                        )
                    )
                else:
                    # Handle case where inputs are invalid
                    self.checkBoxDisplayMessagesAlreadyInInventory.setText(
                        _translate(
                            "MainWindow",
                            "Cannot display broadcasts from this address.",
                        )
                    )

                # Type assertions to guarantee non-None values for the fallback case
                assert state.Inventory is not None
                assert addressVersion is not None
                assert streamNumber is not None
                assert ripe is not None

                # Encode varints with guaranteed non-None results
                addr_version_bytes = encodeVarint(addressVersion)
                stream_num_bytes = encodeVarint(streamNumber)

                # Type assertion: encodeVarint always returns bytes
                assert addr_version_bytes is not None
                assert stream_num_bytes is not None
                assert isinstance(addr_version_bytes, bytes)
                assert isinstance(stream_num_bytes, bytes)

                # Ensure ripe is bytes for cryptographic operations
                ripe_bytes = (
                    ripe
                    if isinstance(ripe, bytes)
                    else bytes(ripe, "utf-8")
                    if isinstance(ripe, str)
                    else b""
                )

                doubleHashOfAddressData = hashlib.sha512(
                    hashlib.sha512(
                        addr_version_bytes + stream_num_bytes + ripe_bytes
                    ).digest()
                ).digest()
                tag = doubleHashOfAddressData[32:]

                # Type assertion for state.Inventory method
                if hasattr(state.Inventory, "by_type_and_tag"):
                    inventory_method = state.Inventory.by_type_and_tag
                    assert inventory_method is not None
                    self.recent = inventory_method(3, tag)
                    count = len(self.recent) if self.recent else 0
                    if count == 0:
                        self.checkBoxDisplayMessagesAlreadyInInventory.setText(
                            _translate(
                                "MainWindow",
                                "There are no recent broadcasts from this address to display.",
                            )
                        )
                    else:
                        self.checkBoxDisplayMessagesAlreadyInInventory.setEnabled(True)
                        self.checkBoxDisplayMessagesAlreadyInInventory.setText(
                            _translate(
                                "MainWindow",
                                "Display the %n recent broadcast(s) from this address.",
                                None,
                                n=count,
                            )
                        )


class RegenerateAddressesDialog(QtWidgets.QDialog):
    """QDialog for regenerating deterministic addresses"""

    # Type hints for UI widgets loaded from .ui files
    groupBox: QGroupBox

    def __init__(self, parent=None):
        super(RegenerateAddressesDialog, self).__init__(parent)
        widgets.load("regenerateaddresses.ui", self)
        self.groupBox.setTitle("")
        QtWidgets.QWidget.resize(self, QtWidgets.QWidget.sizeHint(self))


class SpecialAddressBehaviorDialog(QtWidgets.QDialog):
    """
    QDialog for special address behaviour (e.g. mailing list functionality)
    """

    # Type hints for UI widgets loaded from .ui files
    radioButtonBehaveNormalAddress: QRadioButton
    radioButtonBehaviorMailingList: QRadioButton
    lineEditMailingListName: QLineEdit

    def __init__(self, parent=None, config=global_config):
        super(SpecialAddressBehaviorDialog, self).__init__(parent)
        widgets.load("specialaddressbehavior.ui", self)
        self.address = parent.getCurrentAccount() if parent else None
        self._parent = parent  # Use different name to avoid conflict with Qt parent
        self.config = config

        if self.address:
            try:
                self.address_is_chan = config.safeGetBoolean(self.address, "chan")
            except AttributeError:
                self.address_is_chan = False
            else:
                if self.address_is_chan:  # address is a chan address
                    if hasattr(self, "radioButtonBehaviorMailingList") and hasattr(
                        self, "lineEditMailingListName"
                    ):
                        self.radioButtonBehaviorMailingList.setDisabled(True)
                        self.lineEditMailingListName.setText(
                            _translate(
                                "SpecialAddressBehaviorDialog",
                                "This is a chan address. You cannot use it as a"
                                " pseudo-mailing list.",
                            )
                        )
                else:
                    if config.safeGetBoolean(self.address, "mailinglist"):
                        if hasattr(self, "radioButtonBehaviorMailingList"):
                            self.radioButtonBehaviorMailingList.click()
                    else:
                        if hasattr(self, "radioButtonBehaveNormalAddress"):
                            self.radioButtonBehaveNormalAddress.click()
                    mailingListName = config.safeGet(
                        self.address, "mailinglistname", ""
                    )
                    if hasattr(self, "lineEditMailingListName"):
                        self.lineEditMailingListName.setText(
                            mailingListName,
                        )

        QtWidgets.QWidget.resize(self, QtWidgets.QWidget.sizeHint(self))
        self.show()

    def accept(self) -> None:
        """Accept callback"""
        self.hide()
        if self.address_is_chan:
            return
        if self.radioButtonBehaveNormalAddress.isChecked():
            self.config.set(str(self.address), "mailinglist", "false")
            # Set the color to either black or grey
            if self.config.getboolean(str(self.address), "enabled"):
                if hasattr(self._parent, "setCurrentItemColor") and self._parent:
                    self._parent.setCurrentItemColor(
                        QtWidgets.QApplication.palette().text().color()
                    )
            else:
                if hasattr(self._parent, "setCurrentItemColor") and self._parent:
                    self._parent.setCurrentItemColor(QtGui.QColor(128, 128, 128))
        else:
            self.config.set(str(self.address), "mailinglist", "true")
            self.config.set(
                str(self.address),
                "mailinglistname",
                str(self.lineEditMailingListName.text()),
            )
            if hasattr(self._parent, "setCurrentItemColor") and self._parent:
                self._parent.setCurrentItemColor(QtGui.QColor(137, 4, 177))  # magenta
        if hasattr(self._parent, "rerenderComboBoxSendFrom") and self._parent:
            self._parent.rerenderComboBoxSendFrom()
        if hasattr(self._parent, "rerenderComboBoxSendFromBroadcast") and self._parent:
            self._parent.rerenderComboBoxSendFromBroadcast()
        self.config.save()
        if hasattr(self._parent, "rerenderMessagelistToLabels") and self._parent:
            self._parent.rerenderMessagelistToLabels()


class EmailGatewayDialog(QtWidgets.QDialog):
    """QDialog for email gateway control"""

    # Type hints for UI widgets loaded from .ui files
    label: QLabel
    radioButtonRegister: QRadioButton
    radioButtonStatus: QRadioButton
    radioButtonSettings: QRadioButton
    radioButtonUnregister: QRadioButton
    lineEditEmail: QLineEdit

    def __init__(self, parent, config=global_config, account=None):
        super(EmailGatewayDialog, self).__init__(parent)
        widgets.load("emailgateway.ui", self)
        self.parent = parent
        self.config = config
        if account:
            self.acct = account
            self.setWindowTitle(
                _translate("EmailGatewayDialog", "Registration failed:")
            )
            self.label.setText(
                _translate(
                    "EmailGatewayDialog",
                    "The requested email address is not available,"
                    " please try a new one.",
                )
            )
            self.radioButtonRegister.hide()
            self.radioButtonStatus.hide()
            self.radioButtonSettings.hide()
            self.radioButtonUnregister.hide()
        else:
            address = parent.getCurrentAccount()
            self.acct = accountClass(address)
            if address:
                try:
                    label = config.get(address, "label")
                except AttributeError:
                    pass
                else:
                    if "@" in label:
                        self.lineEditEmail.setText(label)
                if isinstance(self.acct, GatewayAccount):
                    self.radioButtonUnregister.setEnabled(True)
                    self.radioButtonStatus.setEnabled(True)
                    self.radioButtonStatus.setChecked(True)
                    self.radioButtonSettings.setEnabled(True)
                    self.lineEditEmail.setEnabled(False)
                else:
                    self.acct = MailchuckAccount(address)
            else:
                self.acct = None  # Handle no address selected
        self.lineEditEmail.setFocus()
        QtWidgets.QWidget.resize(self, QtWidgets.QWidget.sizeHint(self))

    def accept(self) -> None:
        """Accept callback"""
        self.hide()
        # no chans / mailinglists
        if not self.acct or self.acct.type_ != AccountMixin.NORMAL:
            return

        if not isinstance(self.acct, GatewayAccount):
            return

        if (
            hasattr(self, "radioButtonRegister")
            and self.radioButtonRegister.isChecked()
        ) or (
            hasattr(self, "radioButtonRegister") and self.radioButtonRegister.isHidden()
        ):
            if hasattr(self, "lineEditEmail"):
                email = self.lineEditEmail.text()
                self.acct.register(email)
                if self.acct.fromAddress:
                    self.config.set(self.acct.fromAddress, "label", email)
                    self.config.set(self.acct.fromAddress, "gateway", "mailchuck")
                    self.config.save()
                queues.UISignalQueue.put(
                    (
                        "updateStatusBar",
                        _translate(
                            "EmailGatewayDialog",
                            "Sending email gateway registration request",
                        ),
                    )
                )
        elif (
            hasattr(self, "radioButtonUnregister")
            and self.radioButtonUnregister.isChecked()
        ):
            self.acct.unregister()
            if self.acct.fromAddress:
                self.config.remove_option(self.acct.fromAddress, "gateway")
                self.config.save()
            queues.UISignalQueue.put(
                (
                    "updateStatusBar",
                    _translate(
                        "EmailGatewayDialog",
                        "Sending email gateway unregistration request",
                    ),
                )
            )
        elif hasattr(self, "radioButtonStatus") and self.radioButtonStatus.isChecked():
            self.acct.status()
            queues.UISignalQueue.put(
                (
                    "updateStatusBar",
                    _translate(
                        "EmailGatewayDialog", "Sending email gateway status request"
                    ),
                )
            )
        elif (
            hasattr(self, "radioButtonSettings")
            and self.radioButtonSettings.isChecked()
        ):
            self.data = self.acct

        super(EmailGatewayDialog, self).accept()
