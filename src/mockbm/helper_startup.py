import os
from pathlib import Path
from pybitmessage.bmconfigparser import config


def loadConfig():
    """Loading mock test data"""
    try:
        config.read(str(Path(os.environ['BITMESSAGE_HOME']) / 'keys.dat'))
    except KeyError:
        pass


def total_encrypted_messages_per_month():
    """Loading mock total encrypted message """
    encrypted_messages_per_month = 0
    return encrypted_messages_per_month
