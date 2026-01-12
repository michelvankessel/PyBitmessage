"""Building osx."""

import os
from pathlib import Path
from glob import glob
from typing import List, Tuple, Sequence, Dict, Any
from PyQt6 import QtCore
from setuptools import setup

name = "Bitmessage"
version = os.getenv("PYBITMESSAGEVERSION", "custom")
mainscript = ["bitmessagemain.py"]

translations_path = QtCore.QLibraryInfo.path(
    QtCore.QLibraryInfo.LibraryPath.TranslationsPath
)

DATA_FILES: List[Tuple[str, Sequence[str]]] = [
    ("", ["sslkeys", "images", "default.ini"]),
    ("sql", glob("sql/*.sql")),
    (
        "bitmsghash",
        glob("bitmsghash/bitmsghash*.so") + glob("bitmsghash/bitmsghash.cl"),
    ),
    ("translations", glob("translations/*.qm")),
    ("ui", glob("bitmessageqt/*.ui")),
    ("translations", [str(p) for p in Path(translations_path).glob("qt_??.qm")]),
    ("translations", [str(p) for p in Path(translations_path).glob("qt_??_??.qm")]),
]

OPTIONS: Dict[str, Any] = {
    "py2app": {
        "includes": ["PyQt6._qt"],
        "iconfile": "images/bitmessage.icns",
        "prescripts": ["suppress_warning.py"],
    }
}

setup(
    name=name,
    version=version,
    app=mainscript,
    data_files=DATA_FILES,
    setup_requires=["py2app"],
    options=OPTIONS,
)
