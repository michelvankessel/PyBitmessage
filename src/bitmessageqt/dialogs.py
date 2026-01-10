"""
Custom dialog classes
"""

from PyQt6 import QtWidgets
from typing import Optional

import paths
from . import widgets
from .address_dialogs import (
    AddAddressDialog,
    EmailGatewayDialog,
    NewAddressDialog,
    NewSubscriptionDialog,
    RegenerateAddressesDialog,
    SpecialAddressBehaviorDialog,
)
from .newchandialog import NewChanDialog
from .settings import SettingsDialog
from tr import _translate
from version import softwareVersion


__all__ = [
    "NewChanDialog",
    "AddAddressDialog",
    "NewAddressDialog",
    "NewSubscriptionDialog",
    "RegenerateAddressesDialog",
    "SpecialAddressBehaviorDialog",
    "EmailGatewayDialog",
    "SettingsDialog",
]


class AboutDialog(QtWidgets.QDialog):
    """The `About` dialog"""

    # Type annotations for dynamically loaded UI widgets
    labelVersion: QtWidgets.QLabel
    label_2: QtWidgets.QLabel

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super(AboutDialog, self).__init__(parent)
        widgets.load("about.ui", self)
        last_commit = paths.lastCommit()
        version = softwareVersion
        commit = last_commit.get("commit")
        if commit:
            version += "-" + commit[:7]
        self.labelVersion.setText(
            self.labelVersion.text()
            .replace(":version:", version)
            .replace(":branch:", commit or "v%s" % version)
        )
        self.labelVersion.setOpenExternalLinks(True)

        try:
            last_commit_time = last_commit.get("time")
            if last_commit_time is not None and hasattr(last_commit_time, "year"):
                self.label_2.setText(
                    self.label_2.text().replace("2022", str(last_commit_time.year))
                )
        except AttributeError:
            pass

        self.setFixedSize(QtWidgets.QWidget.sizeHint(self))


class IconGlossaryDialog(QtWidgets.QDialog):
    """The `Icon Glossary` dialog, explaining the status icon colors"""

    # Type annotations for dynamically loaded UI widgets
    groupBox: QtWidgets.QGroupBox
    labelPortNumber: QtWidgets.QLabel

    def __init__(
        self,
        parent: Optional[QtWidgets.QWidget] = None,
        config: Optional[object] = None,
    ) -> None:
        super(IconGlossaryDialog, self).__init__(parent)
        widgets.load("iconglossary.ui", self)

        # .. todo:: FIXME: check the window title visibility here
        self.groupBox.setTitle("")

        # Safe config access with defensive programming
        port_text = _translate(
            "iconGlossaryDialog",
            "You are using TCP port %1. (This can be changed in the settings).",
        )

        if config is not None:
            getint_method = getattr(config, "getint", None)
            if getint_method is not None and callable(getint_method):
                try:
                    port = getint_method("bitmessagesettings", "port")
                    port_text = port_text.arg(port)
                except (AttributeError, ValueError, KeyError):
                    # Graceful fallback if getint fails
                    port_text = _translate(
                        "iconGlossaryDialog",
                        "You are using TCP port (config not available).",
                    )

        self.labelPortNumber.setText(port_text)
        self.setFixedSize(QtWidgets.QWidget.sizeHint(self))


class HelpDialog(QtWidgets.QDialog):
    """The `Help` dialog"""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super(HelpDialog, self).__init__(parent)
        widgets.load("help.ui", self)
        self.setFixedSize(QtWidgets.QWidget.sizeHint(self))


class ConnectDialog(QtWidgets.QDialog):
    """The `Connect` dialog"""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super(ConnectDialog, self).__init__(parent)
        widgets.load("connect.ui", self)
        self.setFixedSize(QtWidgets.QWidget.sizeHint(self))
