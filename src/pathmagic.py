from pathlib import Path
import sys


def setup():
    """Add path to this file to sys.path"""
    app_dir = str(Path(__file__).resolve().parent)
    Path.cwd()
    sys.path.insert(0, app_dir)
    return app_dir


app_dir = setup()
