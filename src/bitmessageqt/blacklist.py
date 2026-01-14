from PyQt6 import QtCore, QtGui, QtWidgets
from typing import Optional

from . import widgets
from addresses import addBMIfNotPresent
from bmconfigparser import config
from .dialogs import AddAddressDialog
from helper_sql import sqlExecute, sqlQuery
from queues import UISignalQueue
from .retranslateui import RetranslateMixin
from tr import _translate
from .uisignaler import UISignaler
from .utils import avatarize


class Blacklist(QtWidgets.QWidget, RetranslateMixin):
    # Type annotations for dynamically loaded UI widgets
    radioButtonBlacklist: QtWidgets.QRadioButton
    radioButtonWhitelist: QtWidgets.QRadioButton
    pushButtonAddBlacklist: QtWidgets.QPushButton
    tableWidgetBlacklist: QtWidgets.QTableWidget
    blacklistContextMenuToolbar: QtWidgets.QToolBar
    popMenuBlacklist: QtWidgets.QMenu

    # Action widgets
    actionBlacklistNew: Optional[QtGui.QAction]
    actionBlacklistDelete: Optional[QtGui.QAction]
    actionBlacklistClipboard: Optional[QtGui.QAction]
    actionBlacklistEnable: Optional[QtGui.QAction]
    actionBlacklistDisable: Optional[QtGui.QAction]
    actionBlacklistSetAvatar: Optional[QtGui.QAction]

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super(Blacklist, self).__init__(parent)
        widgets.load("blacklist.ui", self)

        self.radioButtonBlacklist.clicked.connect(self.click_radioButtonBlacklist)
        self.radioButtonWhitelist.clicked.connect(self.click_radioButtonWhitelist)
        self.pushButtonAddBlacklist.clicked.connect(self.click_pushButtonAddBlacklist)

        self.init_blacklist_popup_menu()

        # Initialize blacklist
        self.tableWidgetBlacklist.itemChanged.connect(
            self.tableWidgetBlacklistItemChanged
        )

        # Set the icon sizes for the identicons
        identicon_size = 3 * 7
        self.tableWidgetBlacklist.setIconSize(
            QtCore.QSize(identicon_size, identicon_size)
        )

        self.UISignalThread = UISignaler.get()
        self.UISignalThread.rerenderBlackWhiteList.connect(self.rerenderBlackWhiteList)

    def loadSettings(self):
        """Load blacklist settings."""
        settings = QtCore.QSettings()
        settings.beginGroup(self.tableWidgetBlacklist.objectName())
        state = settings.value("state")
        if state:
            self.tableWidgetBlacklist.horizontalHeader().restoreState(state if isinstance(state, QtCore.QByteArray) else QtCore.QByteArray(state))
        settings.endGroup()

    def saveSettings(self):
        """Save blacklist settings."""
        settings = QtCore.QSettings()
        settings.beginGroup(self.tableWidgetBlacklist.objectName())
        settings.setValue("state", self.tableWidgetBlacklist.horizontalHeader().saveState())
        settings.endGroup()

    def click_radioButtonBlacklist(self) -> None:
        if config.get("bitmessagesettings", "blackwhitelist") == "white":
            config.set("bitmessagesettings", "blackwhitelist", "black")
            config.save()
            # self.tableWidgetBlacklist.clearContents()
            self.tableWidgetBlacklist.setRowCount(0)
            self.rerenderBlackWhiteList()

    def click_radioButtonWhitelist(self):
        if config.get("bitmessagesettings", "blackwhitelist") == "black":
            config.set("bitmessagesettings", "blackwhitelist", "white")
            config.save()
            # self.tableWidgetBlacklist.clearContents()
            self.tableWidgetBlacklist.setRowCount(0)
            self.rerenderBlackWhiteList()

    def click_pushButtonAddBlacklist(self):
        self.NewBlacklistDialogInstance = AddAddressDialog(self)
        if self.NewBlacklistDialogInstance.exec():
            if self.NewBlacklistDialogInstance.valid:
                address = addBMIfNotPresent(
                    str(self.NewBlacklistDialogInstance.lineEditAddress.text())
                )
                # First we must check to see if the address is already in the
                # address book. The user cannot add it again or else it will
                # cause problems when updating and deleting the entry.
                t = (address,)
                if config.get("bitmessagesettings", "blackwhitelist") == "black":
                    sql = """select * from blacklist where address=?"""
                else:
                    sql = """select * from whitelist where address=?"""
                queryreturn = sqlQuery(sql, *t)
                if queryreturn == []:
                    self.tableWidgetBlacklist.setSortingEnabled(False)
                    self.tableWidgetBlacklist.insertRow(0)
                    newItem = QtWidgets.QTableWidgetItem(
                        self.NewBlacklistDialogInstance.lineEditLabel.text()
                    )
                    avatar_icon = avatarize(address)
                    if avatar_icon is not None:
                        newItem.setIcon(avatar_icon)
                    self.tableWidgetBlacklist.setItem(0, 0, newItem)
                    newItem = QtWidgets.QTableWidgetItem(address)
                    newItem.setFlags(
                        QtCore.Qt.ItemFlag.ItemIsSelectable
                        | QtCore.Qt.ItemFlag.ItemIsEnabled
                    )
                    self.tableWidgetBlacklist.setItem(0, 1, newItem)
                    self.tableWidgetBlacklist.setSortingEnabled(True)
                    t = (
                        str(self.NewBlacklistDialogInstance.lineEditLabel.text()),
                        address,
                        True,
                    )
                    if config.get("bitmessagesettings", "blackwhitelist") == "black":
                        sql = """INSERT INTO blacklist VALUES (?,?,?)"""
                    else:
                        sql = """INSERT INTO whitelist VALUES (?,?,?)"""
                    sqlExecute(sql, *t)
                else:
                    UISignalQueue.put(
                        (
                            "updateStatusBar",
                            _translate(
                                "MainWindow",
                                "Error: You cannot add the same address to your"
                                " list twice. Perhaps rename the existing one"
                                " if you want.",
                            ),
                        )
                    )
            else:
                pass

    def tableWidgetBlacklistItemChanged(self, item):
        if item.column() == 0:
            addressitem = self.tableWidgetBlacklist.item(item.row(), 1)
            if isinstance(addressitem, QtWidgets.QTableWidgetItem):
                if self.radioButtonBlacklist.isChecked():
                    sqlExecute(
                        """UPDATE blacklist SET label=? WHERE address=?""",
                        str(item.text()),
                        str(addressitem.text()),
                    )
                else:
                    sqlExecute(
                        """UPDATE whitelist SET label=? WHERE address=?""",
                        str(item.text()),
                        str(addressitem.text()),
                    )

    def init_blacklist_popup_menu(self, connectSignal=True):
        # Popup menu for the Blacklist page
        self.blacklistContextMenuToolbar = QtWidgets.QToolBar()
        # Actions
        self.actionBlacklistNew = self.blacklistContextMenuToolbar.addAction(
            _translate("MainWindow", "Add new entry"), self.on_action_BlacklistNew
        )
        self.actionBlacklistDelete = self.blacklistContextMenuToolbar.addAction(
            _translate("MainWindow", "Delete"), self.on_action_BlacklistDelete
        )
        self.actionBlacklistClipboard = self.blacklistContextMenuToolbar.addAction(
            _translate("MainWindow", "Copy address to clipboard"),
            self.on_action_BlacklistClipboard,
        )
        self.actionBlacklistEnable = self.blacklistContextMenuToolbar.addAction(
            _translate("MainWindow", "Enable"), self.on_action_BlacklistEnable
        )
        self.actionBlacklistDisable = self.blacklistContextMenuToolbar.addAction(
            _translate("MainWindow", "Disable"), self.on_action_BlacklistDisable
        )
        self.actionBlacklistSetAvatar = self.blacklistContextMenuToolbar.addAction(
            _translate("MainWindow", "Set avatar..."), self.on_action_BlacklistSetAvatar
        )
        self.tableWidgetBlacklist.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        if connectSignal:
            self.tableWidgetBlacklist.customContextMenuRequested.connect(
                self.on_context_menuBlacklist
            )
        self.popMenuBlacklist = QtWidgets.QMenu(self)
        # self.popMenuBlacklist.addAction( self.actionBlacklistNew )
        self.popMenuBlacklist.addAction(self.actionBlacklistDelete)
        self.popMenuBlacklist.addSeparator()
        self.popMenuBlacklist.addAction(self.actionBlacklistClipboard)
        self.popMenuBlacklist.addSeparator()
        self.popMenuBlacklist.addAction(self.actionBlacklistEnable)
        self.popMenuBlacklist.addAction(self.actionBlacklistDisable)
        self.popMenuBlacklist.addAction(self.actionBlacklistSetAvatar)

    def rerenderBlackWhiteList(self) -> None:
        # Safe parent chain navigation with defensive programming
        parent_widget: Optional[QtCore.QObject] = self.parent()
        if parent_widget is not None:
            tabs: Optional[QtCore.QObject] = parent_widget.parent()
            if tabs is not None:
                # Use getattr with default values for safe attribute access
                setTabText = getattr(tabs, "setTabText", None)
                indexOf = getattr(tabs, "indexOf", None)

                if (
                    setTabText is not None
                    and indexOf is not None
                    and callable(setTabText)
                    and callable(indexOf)
                ):
                    try:
                        if (
                            config.get("bitmessagesettings", "blackwhitelist")
                            == "black"
                        ):
                            setTabText(
                                indexOf(self), _translate("blacklist", "Blacklist")
                            )
                        else:
                            setTabText(
                                indexOf(self), _translate("blacklist", "Whitelist")
                            )
                    except Exception:
                        # Graceful fallback if method calls fail
                        pass

        self.tableWidgetBlacklist.setRowCount(0)
        listType = config.get("bitmessagesettings", "blackwhitelist")
        if listType == "black":
            queryreturn = sqlQuery("""SELECT label, address, enabled FROM blacklist""")
        else:
            queryreturn = sqlQuery("""SELECT label, address, enabled FROM whitelist""")
        self.tableWidgetBlacklist.setSortingEnabled(False)
        for row in queryreturn:
            label, address, enabled = row
            self.tableWidgetBlacklist.insertRow(0)
            if isinstance(label, bytes):
                label = label.decode("utf-8", "replace")
            newItem = QtWidgets.QTableWidgetItem(str(label))
            if not enabled:
                newItem.setForeground(QtGui.QBrush(QtGui.QColor(128, 128, 128)))
            avatar_icon = avatarize(address)
            if avatar_icon is not None:
                newItem.setIcon(avatar_icon)
            self.tableWidgetBlacklist.setItem(0, 0, newItem)
            newItem = QtWidgets.QTableWidgetItem(address)
            newItem.setFlags(
                QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled
            )
            if not enabled:
                newItem.setForeground(QtGui.QBrush(QtGui.QColor(128, 128, 128)))
            self.tableWidgetBlacklist.setItem(0, 1, newItem)
        self.tableWidgetBlacklist.setSortingEnabled(True)

    # Group of functions for the Blacklist dialog box
    def on_action_BlacklistNew(self):
        self.click_pushButtonAddBlacklist()

    def on_action_BlacklistDelete(self) -> None:
        currentRow = self.tableWidgetBlacklist.currentRow()
        labelItem: Optional[QtWidgets.QTableWidgetItem] = (
            self.tableWidgetBlacklist.item(currentRow, 0)
        )
        addressItem: Optional[QtWidgets.QTableWidgetItem] = (
            self.tableWidgetBlacklist.item(currentRow, 1)
        )

        if labelItem is not None and addressItem is not None:
            labelAtCurrentRow = labelItem.text()
            addressAtCurrentRow = addressItem.text()
            if config.get("bitmessagesettings", "blackwhitelist") == "black":
                sqlExecute(
                    """DELETE FROM blacklist WHERE label=? AND address=?""",
                    str(labelAtCurrentRow),
                    str(addressAtCurrentRow),
                )
            else:
                sqlExecute(
                    """DELETE FROM whitelist WHERE label=? AND address=?""",
                    str(labelAtCurrentRow),
                    str(addressAtCurrentRow),
                )
            self.tableWidgetBlacklist.removeRow(currentRow)

    def on_action_BlacklistClipboard(self) -> None:
        currentRow = self.tableWidgetBlacklist.currentRow()
        addressItem: Optional[QtWidgets.QTableWidgetItem] = (
            self.tableWidgetBlacklist.item(currentRow, 1)
        )
        if addressItem is not None:
            addressText: str = addressItem.text()
            if addressText:  # Additional safety check
                clipboard = QtWidgets.QApplication.clipboard()
                if clipboard is not None:  # Safety check for clipboard
                    clipboard.setText(addressText)

    def on_context_menuBlacklist(self, point):
        self.popMenuBlacklist.exec(self.tableWidgetBlacklist.mapToGlobal(point))

    def on_action_BlacklistEnable(self) -> None:
        currentRow = self.tableWidgetBlacklist.currentRow()
        labelItem: Optional[QtWidgets.QTableWidgetItem] = (
            self.tableWidgetBlacklist.item(currentRow, 0)
        )
        addressItem: Optional[QtWidgets.QTableWidgetItem] = (
            self.tableWidgetBlacklist.item(currentRow, 1)
        )

        if labelItem is not None and addressItem is not None:
            addressAtCurrentRow = addressItem.text()
            # Use setForeground instead of deprecated setTextColor for PyQt6
            normal_color = QtWidgets.QApplication.palette().text().color()
            labelItem.setForeground(QtGui.QBrush(normal_color))
            addressItem.setForeground(QtGui.QBrush(normal_color))

            if config.get("bitmessagesettings", "blackwhitelist") == "black":
                sqlExecute(
                    """UPDATE blacklist SET enabled=1 WHERE address=?""",
                    str(addressAtCurrentRow),
                )
            else:
                sqlExecute(
                    """UPDATE whitelist SET enabled=1 WHERE address=?""",
                    str(addressAtCurrentRow),
                )

    def on_action_BlacklistDisable(self) -> None:
        currentRow = self.tableWidgetBlacklist.currentRow()
        labelItem: Optional[QtWidgets.QTableWidgetItem] = (
            self.tableWidgetBlacklist.item(currentRow, 0)
        )
        addressItem: Optional[QtWidgets.QTableWidgetItem] = (
            self.tableWidgetBlacklist.item(currentRow, 1)
        )

        if labelItem is not None and addressItem is not None:
            addressAtCurrentRow = addressItem.text()
            # Use setForeground instead of deprecated setTextColor for PyQt6
            gray_color = QtGui.QColor(128, 128, 128)
            labelItem.setForeground(QtGui.QBrush(gray_color))
            addressItem.setForeground(QtGui.QBrush(gray_color))

            if config.get("bitmessagesettings", "blackwhitelist") == "black":
                sqlExecute(
                    """UPDATE blacklist SET enabled=0 WHERE address=?""",
                    str(addressAtCurrentRow),
                )
            else:
                sqlExecute(
                    """UPDATE whitelist SET enabled=0 WHERE address=?""",
                    str(addressAtCurrentRow),
                )

    def on_action_BlacklistSetAvatar(self) -> None:
        main_window = self.window()
        if main_window is not None:
            # Use getattr for safe method access
            set_avatar_method = getattr(main_window, "on_action_SetAvatar", None)
            if set_avatar_method is not None and callable(set_avatar_method):
                set_avatar_method(self.tableWidgetBlacklist)
