"""
Path related functions
"""

import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from shutil import move

logger = logging.getLogger("default")

# When using py2exe or py2app, the variable frozen is added to the sys
# namespace.  This can be used to setup a different code path for
# binary distributions vs source distributions.
frozen = getattr(sys, "frozen", None)


def lookupExeFolder() -> str:
    """Returns executable folder path"""
    if frozen:
        exeFolder = (
            Path(sys.executable).parent.parent
            if frozen == "macosx_app"
            else Path(sys.executable).parent
        )
    elif appimage := os.getenv("APPIMAGE"):
        exeFolder = Path(appimage).parent
    elif __file__:
        exeFolder = Path(__file__).parent
    else:
        return ""
    return str(exeFolder) + "/"


def lookupAppdataFolder() -> str:
    """Returns path of the folder where application data is stored"""
    APPNAME = "PyBitmessage"
    dataFolder = os.environ.get("BITMESSAGE_HOME")
    if dataFolder:
        if dataFolder[-1] not in ("/", None):
            dataFolder += "/"
    elif sys.platform == "darwin":
        try:
            dataFolder = (
                str(Path.home() / "Library" / "Application Support" / APPNAME) + "/"
            )
        except KeyError:
            sys.exit(
                "Could not find home folder, please report this message"
                " and your OS X version to the BitMessage Github."
            )
    elif sys.platform.startswith("win"):
        dataFolder = str(Path(os.environ["APPDATA"]) / APPNAME) + "/"
    else:
        try:
            dataFolder = str(Path(os.environ["XDG_CONFIG_HOME"]) / APPNAME)
        except KeyError:
            dataFolder = str(Path.home() / ".config" / APPNAME)

        # Migrate existing data to the proper location
        # if this is an existing install
        try:
            move(str(Path.home() / f".{APPNAME}"), dataFolder)
            logger.info("Moving data folder to %s", dataFolder)
        except IOError:
            # Old directory may not exist.
            pass
        dataFolder = dataFolder + "/"
    return dataFolder


def codePath() -> str:
    """Returns path to the program sources"""
    if not frozen:
        return str(Path(__file__).parent)
    if frozen == "macosx_app":
        return os.environ.get("RESOURCEPATH", "")
    meipass = getattr(sys, "_MEIPASS", "")
    return meipass if meipass else ""


def tail(f, lines=20):
    """Returns last lines in the f file object"""
    total_lines_wanted = lines

    BLOCK_SIZE = 1024
    f.seek(0, 2)
    block_end_byte = f.tell()
    lines_to_go = total_lines_wanted
    block_number = -1
    # blocks of size BLOCK_SIZE, in reverse order starting
    # from the end of the file
    blocks = []
    while lines_to_go > 0 and block_end_byte > 0:
        if block_end_byte - BLOCK_SIZE > 0:
            # read the last block we haven't yet read
            f.seek(block_number * BLOCK_SIZE, 2)
            blocks.append(f.read(BLOCK_SIZE))
        else:
            # file too small, start from begining
            f.seek(0, 0)
            # only read what was not read
            blocks.append(f.read(block_end_byte))
        lines_found = blocks[-1].count("\n")
        lines_to_go -= lines_found
        block_end_byte -= BLOCK_SIZE
        block_number -= 1
    all_read_text = "".join(reversed(blocks))
    return "\n".join(all_read_text.splitlines()[-total_lines_wanted:])


def lastCommit():
    """
    Returns last commit information as dict with 'commit' and 'time' keys
    """
    githeadfile = str(Path(codePath()).parent / ".git" / "logs" / "HEAD")
    result = {}
    if Path(githeadfile).is_file():
        try:
            with open(githeadfile, "rt") as githead:
                line = tail(githead, 1)
            result["commit"] = line.split()[1]
            result["time"] = datetime.fromtimestamp(
                float(re.search(r">\s*(.*?)\s", line).group(1))
            )
        except (IOError, AttributeError, TypeError):
            pass
    return result
