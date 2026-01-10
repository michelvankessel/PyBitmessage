from pathlib import Path
from PyQt6 import uic
import paths


def resource_path(resFile):
    baseDir = paths.codePath()
    if baseDir is None:
        return None
    for subDir in ["ui", "bitmessageqt"]:
        sub_path = Path(baseDir) / subDir
        if sub_path.is_dir() and (sub_path / resFile).is_file():
            return str(sub_path / resFile)
    return None


def load(resFile, widget):
    res_path = resource_path(resFile)
    if res_path is not None:
        getattr(uic, "loadUi")(res_path, widget)
