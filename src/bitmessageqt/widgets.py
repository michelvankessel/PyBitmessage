from PyQt6 import uic
import os.path
import paths


def resource_path(resFile):
    baseDir = paths.codePath()
    if baseDir is None:
        return None
    for subDir in ["ui", "bitmessageqt"]:
        sub_path = os.path.join(baseDir, subDir)
        if os.path.isdir(sub_path) and os.path.isfile(os.path.join(sub_path, resFile)):
            return os.path.join(sub_path, resFile)
    return None


def load(resFile, widget):
    res_path = resource_path(resFile)
    if res_path is not None:
        uic.loadUi(res_path, widget)
