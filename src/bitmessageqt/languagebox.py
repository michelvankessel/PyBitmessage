"""Language Box Module for Locale Settings"""

from pathlib import Path

from PyQt6 import QtCore, QtWidgets

import paths
from bmconfigparser import config


class LanguageBox(QtWidgets.QComboBox):
    """LanguageBox class for Qt UI"""
    languageName = {
        "system": "System Settings", "eo": "Esperanto",
        "en_pirate": "Pirate English"
    }

    def __init__(self, parent=None):
        super(QtWidgets.QComboBox, self).__init__(parent)
        self.populate()

    def populate(self):
        """Populates drop down list with all available languages."""
        self.clear()
        code_path = paths.codePath()
        if code_path is None:
            return
        localesPath = str(Path(code_path) / 'translations')
        self.addItem(QtWidgets.QApplication.translate(
            "settingsDialog", "System Settings", "system"), "system")
        self.setCurrentIndex(0)
        self.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.InsertAlphabetically)
        for translationFile in sorted(
            list((Path(localesPath)).glob("bitmessage_*.qm"))
        ):
            localeShort = \
                Path(translationFile).stem.split("_", 1)[1]
            if localeShort in LanguageBox.languageName:
                self.addItem(
                    LanguageBox.languageName[localeShort], localeShort)
            else:
                locale = QtCore.QLocale(localeShort)
                self.addItem(
                    locale.nativeLanguageName() or localeShort, localeShort)

        configuredLocale = config.safeGet(
            'bitmessagesettings', 'userlocale', "system")
        for i in range(self.count()):
            if self.itemData(i) == configuredLocale:
                self.setCurrentIndex(i)
                break
