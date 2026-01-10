
"""Mock kivy app with mock threads."""

import os
from kivy.config import Config

from pybitmessage import state

if os.environ.get("INSTALL_TESTS", False):
    Config.set("graphics", "height", 1280)
    Config.set("graphics", "width", 720)
    Config.set("graphics", "position", "custom")
    Config.set("graphics", "top", 0)
    Config.set("graphics", "left", 0)


from pybitmessage.mockbm.class_addressGenerator import FakeAddressGenerator
from pybitmessage.bitmessagekivy.mpybit import NavigateApp
from pybitmessage.mockbm import network

stats = network.stats
objectracker = network.objectracker


def main():
    """main method for starting threads"""
    # Start the address generation thread
    addressGeneratorThread = FakeAddressGenerator()
    # close the main program even if there are threads left
    addressGeneratorThread.daemon = True
    addressGeneratorThread.start()
    state.kivyapp = NavigateApp()
    state.kivyapp.run()
    addressGeneratorThread.stopThread()


if __name__ == "__main__":
    main()
