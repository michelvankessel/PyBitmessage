
"""Mock kivy app with mock threads."""

import os

import state

from mockbm.class_addressGenerator import FakeAddressGenerator
from bitmessagekivy.mpybit import NavigateApp
from mockbm import network

stats = network.stats
objectracker = network.objectracker


def main():
    """main method for starting threads"""
    addressGeneratorThread = FakeAddressGenerator()
    addressGeneratorThread.daemon = True
    addressGeneratorThread.start()
    state.kivyapp = NavigateApp()
    state.kivyapp.run()
    addressGeneratorThread.stopThread()


if __name__ == "__main__":
    os.environ['INSTALL_TESTS'] = "True"
    main()
