"""Building osx."""
import os
from glob import glob
from typing import List, Tuple, Sequence, Dict, Any
from PyQt6 import QtCore
from setuptools import setup

name = "Bitmessage"
version = os.getenv("PYBITMESSAGEVERSION", "custom")
mainscript = ["bitmessagemain.py"]

DATA_FILES: List[Tuple[str, Sequence[str]]] = [
    ('', ['sslkeys', 'images', 'default.ini']),
    ('sql', glob('sql/*.sql')),
    ('bitmsghash', ['bitmsghash/bitmsghash.cl', 'bitmsghash/bitmsghash.so']),
    ('translations', glob('translations/*.qm')),
    ('ui', glob('bitmessageqt/*.ui')),
    (
        'translations',
        glob(os.path.join(str(QtCore.QLibraryInfo.path(
            QtCore.QLibraryInfo.LibraryPath.TranslationsPath)), 'qt_??.qm'))),
    (
        'translations',
        glob(os.path.join(str(QtCore.QLibraryInfo.path(
            QtCore.QLibraryInfo.LibraryPath.TranslationsPath)), 'qt_??_??.qm'))),
]

OPTIONS: Dict[str, Any] = {
    "py2app": {
        "includes": ['sip', 'PyQt6._qt'],
        "iconfile": "images/bitmessage.icns"
    }
}

setup(
    name=name,
    version=version,
    app=mainscript,
    data_files=DATA_FILES,
    setup_requires=["py2app"],
    options=OPTIONS
)
