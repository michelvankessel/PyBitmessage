"""
Folder tree and messagelist widgets definitions.
"""

from html import escape
from typing import Optional, Any

from PyQt6 import QtCore, QtGui, QtWidgets

from bmconfigparser import config
from helper_sql import sqlExecute, sqlQuery
from .settingsmixin import SettingsMixin
from tr import _translate
from .utils import avatarize

# for pylupdate
_translate("MainWindow", "inbox")
_translate("MainWindow", "new")
_translate("MainWindow", "sent")
_translate("MainWindow", "trash")

TimestampRole = QtCore.Qt.ItemDataRole.UserRole + 1


class AccountMixin(object):
    """UI-related functionality for accounts"""

    ALL = 0
    NORMAL = 1
    CHAN = 2
    MAILINGLIST = 3
    SUBSCRIPTION = 4
    BROADCAST = 5

    # Type hints and defaults for common attributes
    type_: int = NORMAL
    address: Optional[str] = None
    unreadCount: int = 0

    def accountColor(self) -> QtGui.QColor:
        """QT UI color for an account"""
        is_enabled = getattr(self, "isEnabled", True)
        if not is_enabled:
            return QtGui.QColor(128, 128, 128)
        type_val = getattr(self, "type", self.NORMAL)
        if type_val == self.CHAN:
            return QtGui.QColor(216, 119, 0)
        elif type_val in [self.MAILINGLIST, self.SUBSCRIPTION]:
            return QtGui.QColor(137, 4, 177)
        return QtWidgets.QApplication.palette().text().color()

    def folderColor(self) -> QtGui.QColor:
        """QT UI color for a folder"""
        parent_widget: Optional[QtWidgets.QTreeWidgetItem] = getattr(
            self, "parent", lambda: None
        )()
        if (
            parent_widget is not None
            and hasattr(parent_widget, "isEnabled")
            and not getattr(parent_widget, "isEnabled", True)
        ):
            return QtGui.QColor(128, 128, 128)
        return QtWidgets.QApplication.palette().text().color()

    def accountBrush(self) -> QtGui.QBrush:
        """Account brush (for QT UI)"""
        brush = QtGui.QBrush(self.accountColor())
        brush.setStyle(QtCore.Qt.BrushStyle.NoBrush)
        return brush

    def folderBrush(self) -> QtGui.QBrush:
        """Folder brush (for QT UI)"""
        brush = QtGui.QBrush(self.folderColor())
        brush.setStyle(QtCore.Qt.BrushStyle.NoBrush)
        return brush

    def accountString(self) -> str:
        """Account string suitable for use in To: field: label <address>"""
        label = getattr(self, "_getLabel", lambda: self.address or "")()
        return (
            (
                self.address
                if label == self.address
                else "%s <%s>" % (label, self.address)
            )
            if self.address is not None
            else ""
        )

    def setAddress(self, address: Optional[str]) -> None:
        """Set bitmessage address of the object"""
        if address is None:
            self.address = None
        else:
            self.address = str(address)

    def setUnreadCount(self, cnt: int) -> None:
        """Set number of unread messages"""
        try:
            if self.unreadCount == int(cnt):
                return
        except AttributeError:
            pass
        self.unreadCount = int(cnt)
        if isinstance(self, QtWidgets.QTreeWidgetItem):
            self.emitDataChanged()

    def setType(self) -> None:
        """Set account type (QT UI)"""
        if not hasattr(self, "address") or self.address is None:
            self.type_ = self.ALL
            if isinstance(self, QtWidgets.QTreeWidgetItem):
                self.setFlags(self.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            return

        if isinstance(self, QtWidgets.QTreeWidgetItem):
            self.setFlags(self.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)

        if config.safeGetBoolean(self.address, "chan"):
            self.type_ = self.CHAN
        elif config.safeGetBoolean(self.address, "mailinglist"):
            self.type_ = self.MAILINGLIST
        elif sqlQuery(
            """select label from subscriptions where address=?""", self.address
        ):
            self.type_ = self.SUBSCRIPTION
        else:
            self.type_ = self.NORMAL

    def defaultLabel(self) -> str:
        """Default label (in case no label is set manually)"""
        queryreturn = retval = None
        type_val = getattr(self, "type_", self.NORMAL)
        if type_val in (self.NORMAL, self.CHAN, self.MAILINGLIST):
            try:
                retval = str(config.get(self.address, "label"))
            except Exception:
                queryreturn = sqlQuery(
                    "SELECT label FROM addressbook WHERE address=?",
                    self.address
                )
        elif type_val == self.SUBSCRIPTION:
            queryreturn = sqlQuery(
                "SELECT label FROM subscriptions WHERE address=?",
                self.address
            )
        if queryreturn:
            label_val = queryreturn[-1][0]
            if isinstance(label_val, bytes):
                retval = label_val.decode('utf-8', 'replace')
            else:
                retval = str(label_val)
        elif not hasattr(self, "address") or self.address is None or type_val == self.ALL:
            return _translate("MainWindow", "All accounts")

        return retval or self.address or ""


# Define UI widget classes before they're referenced in AccountMixin
class Ui_FolderWidget(QtWidgets.QTreeWidgetItem, AccountMixin):
    """Item in the account/folder tree representing a folder"""

    folderWeight = {"inbox": 1, "new": 2, "sent": 3, "trash": 4}

    def __init__(
        self,
        parent: Optional[QtWidgets.QTreeWidgetItem] = None,
        pos: int = 0,
        address: Optional[str] = "",
        folderName: str = "",
        unreadCount: int = 0,
    ) -> None:
        QtWidgets.QTreeWidgetItem.__init__(self)
        self.setFolderName(folderName)
        self.setAddress(address)
        self.setUnreadCount(unreadCount)
        self.setType()
        if parent is not None and pos is not None:
            parent.insertChild(pos, self)

    def _setup(self, parent: QtWidgets.QTreeWidgetItem, pos: int) -> None:
        parent.insertChild(pos, self)

    def _getLabel(self) -> str:
        return _translate("MainWindow", self.folderName)

    def setFolderName(self, fname: str) -> None:
        """Set folder name (for QT UI)"""
        self.folderName = str(fname)
        self.setText(0, _translate("MainWindow", self.folderName))

    def data(self, column: int, role: int) -> Any:
        """Override internal QT method for returning object data"""
        if column == 0:
            if role == QtCore.Qt.ItemDataRole.ForegroundRole:
                return self.folderBrush()
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return self._getLabel()
        # Use QTreeWidgetItem.data() which takes (column, role)
        try:
            return QtWidgets.QTreeWidgetItem.data(self, column, role)
        except (AttributeError, TypeError):
            # Defensive fallback for missing data
            return None

    # inbox, sent, thrash first, rest alphabetically
    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Ui_FolderWidget):
            reverse = False
            tree_widget = self.treeWidget()
            if tree_widget is not None:
                header = tree_widget.header()
                if header is not None:
                    sort_order = header.sortIndicatorOrder()
                    reverse = QtCore.Qt.SortOrder.DescendingOrder == sort_order

            if self.folderName in self.folderWeight:
                x = self.folderWeight[self.folderName]
            else:
                x = 99
            if other.folderName in self.folderWeight:
                y = self.folderWeight[other.folderName]
            else:
                y = 99

            if x == y:
                return self.folderName < other.folderName
            return x >= y if reverse else x < y

        try:
            return QtWidgets.QTreeWidgetItem.__lt__(self, other)
        except (AttributeError, TypeError):
            return False


class Ui_AddressWidget(QtWidgets.QTreeWidgetItem, AccountMixin):
    """Item in the account/folder tree representing an account"""

    def __init__(
        self,
        parent: Optional[QtWidgets.QTreeWidget] = None,
        pos: int = 0,
        address: Optional[str] = None,
        unreadCount: int = 0,
        enabled: bool = True,
    ) -> None:
        QtWidgets.QTreeWidgetItem.__init__(self)
        self.setAddress(address)
        self.setUnreadCount(unreadCount)
        # Safe attribute setting
        if hasattr(self, "isEnabled"):
            self.isEnabled = enabled
        self.setType()
        if parent is not None and pos is not None:
            parent.insertTopLevelItem(pos, self)

    def _setup(self, parent: QtWidgets.QTreeWidgetItem, pos: int) -> None:
        self.setType()
        parent.insertChild(pos, self)

    def _getLabel(self) -> str:
        if self.address is None:
            return _translate("MainWindow", "All accounts")
        else:
            try:
                result = config.get(self.address, "label")
                return str(result) if result is not None else self.address or ""
            except Exception:
                return self.address or ""

    def defaultLabel(self) -> str:
        return self._getLabel()

    def _getAddressBracket(self, unreadCount: bool = False) -> str:
        label = self._getLabel()
        if self.address is not None:
            return f"{label} ({self.address})"
        return label

    def data(self, column: int, role: int) -> Any:
        """Override internal QT method for returning object data"""
        if column == 0:
            if role == QtCore.Qt.ItemDataRole.DecorationRole:
                label_func = getattr(self, "_getLabel", lambda: self.address)
                label_val = label_func()
                avatar_data = self.address or (
                    label_val.encode("utf8") if label_val else None
                )
                return avatarize(avatar_data) if avatar_data else None
            elif role == QtCore.Qt.ItemDataRole.ForegroundRole:
                return self.accountBrush()
            elif role == QtCore.Qt.ItemDataRole.DisplayRole:
                return self._getAddressBracket(self.unreadCount > 0)
        return QtWidgets.QTreeWidgetItem.data(self, column, role)

    def setData(self, column: int, role: int, value: Any) -> None:
        """Save account label (if you edit in the the UI, this will be triggered and will save it to keys.dat)"""
        if (
            role == QtCore.Qt.ItemDataRole.EditRole
            and hasattr(self, "type_")
            and getattr(self, "type_", None) != AccountMixin.SUBSCRIPTION
        ):
            if hasattr(self, "address") and self.address is not None:
                config.set(str(self.address), "label", str(value))
                config.save()
        return QtWidgets.QTreeWidgetItem.setData(self, column, role, value)

    def setAddress(self, address: Optional[str]) -> None:
        """Set address to object (for QT UI)"""
        # Safe setData call with proper type handling
        if address is not None:
            QtWidgets.QTreeWidgetItem.setData(
                self, 0, QtCore.Qt.ItemDataRole.UserRole, address
            )
        if hasattr(self, "address"):
            self.address = address
        # Update text explicitly
        self.setText(0, self._getAddressBracket(self.unreadCount > 0))

    def setEnabled(self, enabled: bool) -> None:
        """Set account enabled (QT UI)"""
        self.isEnabled = enabled
        try:
            self.setExpanded(enabled)
        except AttributeError:
            pass
        if isinstance(self, Ui_AddressWidget):
            for i in range(self.childCount()):
                child: Optional[QtWidgets.QTreeWidgetItem] = self.child(i)
                if (
                    child is not None
                    and isinstance(child, Ui_FolderWidget)
                    and hasattr(child, "isEnabled")
                ):
                    setattr(child, "isEnabled", enabled)
        if isinstance(self, QtWidgets.QTreeWidgetItem):
            self.emitDataChanged()

    def _getSortRank(self) -> int:
        # Check _account_type first, then type (but handle if type is a method)
        type_val = getattr(self, "_account_type", None)
        if type_val is None:
            type_attr = getattr(self, "type", 0)
            if callable(type_attr):
                type_val = 0  # Fallback if type is a method (e.g. QTreeWidgetItem.type)
            else:
                type_val = type_attr

        is_enabled_attr = getattr(self, "isEnabled", True)
        if callable(is_enabled_attr):
            is_enabled = is_enabled_attr()
        else:
            is_enabled = is_enabled_attr
        return type_val if is_enabled else (type_val + 100)

    # label (or address) alphabetically, disabled at the end
    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Ui_AddressWidget):
            reverse = False
            tree_widget = self.treeWidget()
            if tree_widget is not None:
                header = tree_widget.header()
                if header is not None:
                    sort_order = header.sortIndicatorOrder()
                    reverse = QtCore.Qt.SortOrder.DescendingOrder == sort_order

            if self._getSortRank() == other._getSortRank():
                x = self._getLabel().lower()
                y = other._getLabel().lower()
                return x < y
            return (
                not reverse if self._getSortRank() < other._getSortRank() else reverse
            )

        try:
            return QtWidgets.QTreeWidgetItem.__lt__(self, other)
        except (AttributeError, TypeError):
            return False


class Ui_SubscriptionWidget(Ui_AddressWidget):
    """Special treating of subscription addresses"""

    def __init__(
        self,
        parent: Optional[QtWidgets.QTreeWidget] = None,
        pos: int = 0,
        address: str = "",
        unreadCount: int = 0,
        label: str = "",
        enabled: bool = True,
    ) -> None:
        # Call parent init with matching signature (no label param in parent)
        super(Ui_SubscriptionWidget, self).__init__(
            parent, pos, address, unreadCount, enabled
        )
        self.setType()
        # Store label separately if provided
        if label:
            setattr(self, "_label", label)

    def _getLabel(self) -> str:
        if hasattr(self, "_label") and self._label:
            return self._label

        queryreturn = sqlQuery(
            """select label from subscriptions where address=?""", self.address
        )
        retval = None  # Initialize retval
        if queryreturn != []:
            for row in queryreturn:
                (retval,) = row
                if isinstance(retval, bytes):
                    retval = retval.decode("utf-8", "ignore")
                # Handle stringified bytes representation (e.g., "b'foo'")
                elif isinstance(retval, str) and retval.startswith("b'") and retval.endswith("'"):
                    try:
                        # Strip b'' wrapper
                        inner = retval[2:-1]
                        # If it was a repr(bytes), it might have escaped chars, but for simple labels
                        # it's usually just the content. Ideally we'd use ast.literal_eval but that's risky.
                        # For now, just stripping the wrapper is a good heuristic for this specific issue.
                        retval = inner
                    except Exception:
                        pass
        return retval if retval is not None else (self.address or "")

    def setType(self) -> None:
        """Set account type"""
        super(Ui_SubscriptionWidget, self).setType()
        self.type_ = AccountMixin.SUBSCRIPTION

    def setData(self, column: int, role: int, value: Any) -> None:
        """Save subscription label to database"""
        if role == QtCore.Qt.ItemDataRole.EditRole:
            label = str(value)
            sqlExecute(
                """UPDATE subscriptions SET label=? WHERE address=?""",
                label,
                self.address,
            )
        return Ui_AddressWidget.setData(self, column, role, value)

    def setEnabled(self, enabled: bool) -> None:
        """Set account enabled (QT UI)"""
        self.isEnabled = enabled
        try:
            self.setExpanded(enabled)
        except AttributeError:
            pass
        if isinstance(self, Ui_AddressWidget):
            for i in range(self.childCount()):
                child: Optional[QtWidgets.QTreeWidgetItem] = self.child(i)
                if (
                    child is not None
                    and isinstance(child, Ui_FolderWidget)
                    and hasattr(child, "isEnabled")
                ):
                    setattr(child, "isEnabled", enabled)
        if isinstance(self, QtWidgets.QTreeWidgetItem):
            self.emitDataChanged()


class BMTableWidgetItem(QtWidgets.QTableWidgetItem, SettingsMixin):
    """A common abstract class for Table widget item"""

    def __init__(self, label=None, unread=False):
        super(QtWidgets.QTableWidgetItem, self).__init__()
        self.setLabel(label)
        self.setUnread(unread)
        self._setup()

    def _setup(self):
        self.setFlags(
            QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled
        )

    def setLabel(self, label):
        """Set object label"""
        self.label = label

    def setUnread(self, unread):
        """Set/unset read state of an item"""
        self.unread = unread

    def data(self, role):
        """Return object data (QT UI)"""
        if role in (
            QtCore.Qt.ItemDataRole.DisplayRole,
            QtCore.Qt.ItemDataRole.EditRole,
            QtCore.Qt.ItemDataRole.ToolTipRole,
        ):
            return self.label
        elif role == QtCore.Qt.ItemDataRole.FontRole:
            font = QtGui.QFont()
            font.setBold(self.unread)
            return font
        return super(BMTableWidgetItem, self).data(role)


class BMAddressWidget(BMTableWidgetItem, AccountMixin):
    """A common class for Table widget item with account"""

    def _setup(self) -> None:
        super(BMAddressWidget, self)._setup()
        if hasattr(self, "isEnabled"):
            setattr(self, "isEnabled", True)
        set_type_method = getattr(self, "setType", None)
        if set_type_method is not None and callable(set_type_method):
            set_type_method()

    def _getLabel(self):
        return self.label

    def data(self, role):
        """Return object data (QT UI)"""
        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            return self.label + " (" + self.address + ")"
        elif role == QtCore.Qt.ItemDataRole.DecorationRole:
            if config.safeGetBoolean("bitmessagesettings", "useidenticons"):
                return avatarize(self.address or self.label)
        elif role == QtCore.Qt.ItemDataRole.ForegroundRole:
            return self.accountBrush()
        return super(BMAddressWidget, self).data(role)


class MessageList_AddressWidget(BMAddressWidget):
    """Address item in a messagelist"""

    def __init__(self, address=None, label=None, unread=False):
        self.setAddress(address)
        super(MessageList_AddressWidget, self).__init__(label, unread)

    def setLabel(self, label=None):
        """Set label"""
        super(MessageList_AddressWidget, self).setLabel(label)
        if label is not None:
            return
        newLabel = self.address
        queryreturn = None
        if self.type_ in (
            AccountMixin.NORMAL,
            AccountMixin.CHAN,
            AccountMixin.MAILINGLIST,
        ):
            try:
                label_val = config.get(self.address, "label")
                if isinstance(label_val, bytes):
                    newLabel = label_val.decode("utf-8", "ignore")
                else:
                    newLabel = str(label_val)
            except Exception:
                queryreturn = sqlQuery(
                    """select label from addressbook where address=?""", self.address
                )
        elif self.type_ == AccountMixin.SUBSCRIPTION:
            queryreturn = sqlQuery(
                """select label from subscriptions where address=?""", self.address
            )
        if queryreturn:
            for row in queryreturn:
                label_val = row[0]
                if isinstance(label_val, bytes):
                    newLabel = label_val.decode('utf-8', 'replace')
                else:
                    newLabel = str(label_val)

        self.label = newLabel

    def data(self, role):
        """Return object data (QT UI)"""
        if role == QtCore.Qt.ItemDataRole.UserRole:
            return self.address
        return super(MessageList_AddressWidget, self).data(role)

    def setData(self, role, value):
        """Set object data"""
        if role == QtCore.Qt.ItemDataRole.EditRole:
            self.setLabel()
        return super(MessageList_AddressWidget, self).setData(role, value)

    # label (or address) alphabetically, disabled at the end
    def __lt__(self, other):
        if isinstance(other, MessageList_AddressWidget):
            self_label = self.label if self.label is not None else ""
            other_label = other.label if other.label is not None else ""
            return self_label.lower() < other_label.lower()
        try:
            return QtWidgets.QTableWidgetItem.__lt__(self, other)
        except (AttributeError, TypeError):
            return False


class MessageList_SubjectWidget(BMTableWidgetItem):
    """Message list subject item"""

    def __init__(self, subject=None, label=None, unread=False):
        self.setSubject(subject)
        super(MessageList_SubjectWidget, self).__init__(label, unread)

    def setSubject(self, subject):
        """Set subject"""
        self.subject = subject

    def data(self, role):
        """Return object data (QT UI)"""
        if role == QtCore.Qt.ItemDataRole.UserRole:
            return self.subject
        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            return escape(self.subject)
        return super(MessageList_SubjectWidget, self).data(role)

    # label (or address) alphabetically, disabled at the end
    def __lt__(self, other):
        if isinstance(other, MessageList_SubjectWidget):
            self_label = self.label if self.label is not None else ""
            other_label = other.label if other.label is not None else ""
            return self_label.lower() < other_label.lower()
        try:
            return QtWidgets.QTableWidgetItem.__lt__(self, other)
        except (AttributeError, TypeError):
            return False


# In order for the time columns on the Inbox and Sent tabs to be sorted
# correctly (rather than alphabetically), we need to overload the <
# operator and use this class instead of QTableWidgetItem.
class MessageList_TimeWidget(BMTableWidgetItem):
    """
    A subclass of QTableWidgetItem for received (lastactiontime) field.
    '<' operator is overloaded to sort by TimestampRole == 33
    msgid is available by QtCore.Qt.ItemDataRole.UserRole
    """

    def __init__(self, label=None, unread=False, timestamp=None, msgid=""):
        super(MessageList_TimeWidget, self).__init__(label, unread)
        self.setData(QtCore.Qt.ItemDataRole.UserRole, msgid if msgid else b"")
        self.setData(TimestampRole, int(timestamp) if timestamp is not None else 0)

    def __lt__(self, other):
        return self.data(TimestampRole) < other.data(TimestampRole)

    def data(self, role: int = QtCore.Qt.ItemDataRole.UserRole):
        """
        Returns expected python types for QtCore.Qt.ItemDataRole.UserRole and TimestampRole
        custom roles and super for any Qt role
        """
        data = super(MessageList_TimeWidget, self).data(role)
        if role == TimestampRole:
            if data is None:
                return 0
            if isinstance(data, (int, float)):
                return int(data)
            # Defensive: try to convert, fallback to 0
            try:
                return int(data)
            except (TypeError, ValueError):
                return 0
        if role == QtCore.Qt.ItemDataRole.UserRole:
            if isinstance(data, str):
                return data.encode()
            elif isinstance(data, bytes):
                return data
            else:
                try:
                    return bytes(data) if data else b""
                except (TypeError, ValueError):
                    return b""
        return data


class Ui_AddressBookWidgetItem(BMAddressWidget):
    """Addressbook item"""

    def __init__(self, label=None, acc_type: int = AccountMixin.NORMAL):
        self._type = acc_type
        super(Ui_AddressBookWidgetItem, self).__init__(label=label)
        self.setFlags(self.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)

    # Note: We use _type internally to avoid conflicting with QTableWidgetItem.type() method
    # Access via get_account_type() and set_account_type() methods instead of property

    def get_account_type(self) -> int:
        """Return account type"""
        return self._type

    def set_account_type(self, value: int) -> None:
        """Set account type"""
        self._type = value

    def data(self, role):
        """Return object data"""
        if role == QtCore.Qt.ItemDataRole.UserRole:
            return self._type
        return super(Ui_AddressBookWidgetItem, self).data(role)

    def setData(self, role, value):
        """Set data"""
        if role == QtCore.Qt.ItemDataRole.EditRole:
            self.label = str(value)
            if self._type in (
                AccountMixin.NORMAL,
                AccountMixin.MAILINGLIST,
                AccountMixin.CHAN,
            ):
                try:
                    config.get(self.address, "label")
                    if hasattr(self, "address") and self.address is not None:
                        config.set(self.address, "label", self.label)
                    config.save()
                except Exception:
                    sqlExecute(
                        """UPDATE addressbook set label=? WHERE address=?""",
                        self.label,
                        self.address,
                    )
            elif self._type == AccountMixin.SUBSCRIPTION:
                sqlExecute(
                    """UPDATE subscriptions set label=? WHERE address=?""",
                    self.label,
                    self.address,
                )
            else:
                pass
        return super(Ui_AddressBookWidgetItem, self).setData(role, value)

    def __lt__(self, other):
        if isinstance(other, Ui_AddressBookWidgetItem):
            reverse = False
            # Use getattr for defensive access since this inherits from BMAddressWidget
            tree_widget_func = getattr(self, "treeWidget", None)
            if tree_widget_func is not None:
                tree_widget = tree_widget_func()
                if tree_widget is not None:
                    header = tree_widget.header()
                    if header is not None:
                        sort_order = header.sortIndicatorOrder()
                        reverse = QtCore.Qt.SortOrder.DescendingOrder == sort_order

            self_type = getattr(self, "_type", 0)
            other_type = getattr(other, "_type", 0)
            if self_type == other_type:
                self_label = self.label if self.label is not None else ""
                other_label = other.label if other.label is not None else ""
                return self_label.lower() < other_label.lower()
            return not reverse if self_type < other_type else reverse

        # For non-AddressBookWidgetItem objects, use direct QTableWidgetItem comparison
        # This avoids the Pylance issue with super() method resolution
        try:
            return QtWidgets.QTableWidgetItem.__lt__(self, other)
        except (AttributeError, TypeError):
            # Fallback: compare by label if both objects have labels
            self_label = getattr(self, "label", None)
            other_label = getattr(other, "label", None)
            if self_label is not None and other_label is not None:
                return str(self_label).lower() < str(other_label).lower()
            # Final fallback: return False for incomparable objects
            return False


class Ui_AddressBookWidgetItemLabel(Ui_AddressBookWidgetItem):
    """Addressbook label item"""

    def __init__(self, address, label, acc_type):
        self.address = address
        super(Ui_AddressBookWidgetItemLabel, self).__init__(label, acc_type)

    def data(self, role):
        """Return object data"""
        return super(Ui_AddressBookWidgetItemLabel, self).data(role)


class Ui_AddressBookWidgetItemAddress(Ui_AddressBookWidgetItem):
    """Addressbook address item"""

    def __init__(self, address, label, acc_type):
        self.address = address
        super(Ui_AddressBookWidgetItemAddress, self).__init__(address, acc_type)

    def data(self, role):
        """Return object data"""
        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            return self.address
        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            return None
        return super(Ui_AddressBookWidgetItemAddress, self).data(role)


class AddressBookCompleter(QtWidgets.QCompleter):
    """Addressbook completer"""

    def __init__(self):
        super(AddressBookCompleter, self).__init__()
        self.cursorPos = -1

    def onCursorPositionChanged(self, oldPos, newPos):
        """Callback for cursor position change"""
        if oldPos != self.cursorPos:
            self.cursorPos = -1

    def splitPath(self, path):
        """Split on semicolon"""
        text = str(path)
        # Safe casting to QLineEdit for cursor position methods
        line_edit = self.widget()
        if isinstance(line_edit, QtWidgets.QLineEdit):
            return [text[: line_edit.cursorPosition()].split(";")[-1].strip()]
        else:
            return [text.split(";")[-1].strip()]

    def pathFromIndex(self, index):
        """Perform autocompletion (reimplemented QCompleter method)"""
        edit_data = index.data(QtCore.Qt.ItemDataRole.EditRole)
        if isinstance(edit_data, bytes):
            autoString = edit_data.decode("utf-8", "ignore")
        else:
            autoString = str(edit_data) if edit_data is not None else ""
        # Safe text extraction with proper type handling
        widget = self.widget()
        if isinstance(widget, QtWidgets.QLineEdit):
            text_val = widget.text()
            if isinstance(text_val, bytes):
                text = text_val.decode("utf-8", "ignore")
            else:
                text = str(text_val) if text_val else ""
        else:
            text = ""

        # If cursor position was saved, restore it, else save it
        if self.cursorPos != -1:
            # Safe casting to QLineEdit for cursor position methods
            line_edit = self.widget()
            if isinstance(line_edit, QtWidgets.QLineEdit):
                line_edit.setCursorPosition(self.cursorPos)
        else:
            # Safe casting to QLineEdit for cursor position methods
            line_edit = self.widget()
            if isinstance(line_edit, QtWidgets.QLineEdit):
                self.cursorPos = line_edit.cursorPosition()

        # Get current position
        widget = self.widget()
        if isinstance(widget, QtWidgets.QLineEdit):
            curIndex = widget.cursorPosition()
        else:
            curIndex = 0

        # prev_delimiter_index should actually point at final white space
        # AFTER the delimiter
        # Get index of last delimiter before current position
        prevDelimiterIndex = text[0:curIndex].rfind(";")
        while prevDelimiterIndex + 1 < len(text) and text[prevDelimiterIndex + 1] == " ":
            prevDelimiterIndex += 1

        # Get index of first delimiter after current position
        # (or EOL if no delimiter after cursor)
        nextDelimiterIndex = text.find(";", curIndex)
        if nextDelimiterIndex == -1:
            nextDelimiterIndex = len(text)

        # Get part of string that occurs before cursor
        part1 = text[0:prevDelimiterIndex + 1]

        # Get string value from before auto finished string is selected
        # pre = text[prevDelimiterIndex + 1:curIndex - 1]

        # Get part of string that occurs AFTER cursor
        part2 = text[nextDelimiterIndex:]

        return part1 + autoString + part2
