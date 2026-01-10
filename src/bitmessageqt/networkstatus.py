"""
Network status tab widget definition.
"""

import time

from PyQt6 import QtCore, QtGui, QtWidgets

import l10n
import network.stats
import state
from . import widgets
from network import connectionpool, knownnodes
from .retranslateui import RetranslateMixin
from tr import _translate
from .uisignaler import UISignaler


class NetworkStatus(QtWidgets.QWidget, RetranslateMixin):
    """Network status tab"""

    # UI widgets loaded from networkstatus.ui - type annotations for pyright
    tableWidgetConnectionCount: QtWidgets.QTableWidget
    labelSyncStatus: QtWidgets.QLabel
    labelMessageCount: QtWidgets.QLabel
    labelBroadcastCount: QtWidgets.QLabel
    labelPubkeyCount: QtWidgets.QLabel
    labelBytesRecvCount: QtWidgets.QLabel
    labelBytesSentCount: QtWidgets.QLabel
    labelTotalConnections: QtWidgets.QLabel
    labelLookupsPerSecond: QtWidgets.QLabel
    labelStartupTime: QtWidgets.QLabel

    def __init__(self, parent=None):
        super(NetworkStatus, self).__init__(parent)
        widgets.load("networkstatus.ui", self)

        header = self.tableWidgetConnectionCount.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(
                QtWidgets.QHeaderView.ResizeMode.ResizeToContents
            )

            # Somehow this value was 5 when I tested
            if header.sortIndicatorSection() > 4:
                header.setSortIndicator(0, QtCore.Qt.SortOrder.AscendingOrder)

        self.startup = time.localtime()

        self.UISignalThread = UISignaler.get()

        self.UISignalThread.updateNumberOfMessagesProcessed.connect(
            self.updateNumberOfMessagesProcessed
        )
        self.UISignalThread.updateNumberOfPubkeysProcessed.connect(
            self.updateNumberOfPubkeysProcessed
        )
        self.UISignalThread.updateNumberOfBroadcastsProcessed.connect(
            self.updateNumberOfBroadcastsProcessed
        )
        self.UISignalThread.updateNetworkStatusTab.connect(self.updateNetworkStatusTab)

        self.timer = QtCore.QTimer()

        self.timer.timeout.connect(self.runEveryTwoSeconds)
        # pylint: enable=no-member

    def startUpdate(self):
        """Start a timer to update counters every 2 seconds"""
        state.Inventory.numberOfInventoryLookupsPerformed = 0
        self.runEveryTwoSeconds()
        self.timer.start(2000)  # milliseconds

    def stopUpdate(self):
        """Stop counter update timer"""
        self.timer.stop()

    def formatBytes(self, num):
        """Format bytes nicely (SI prefixes)"""

        for x in [
            _translate("networkstatus", "byte(s)", None, num),
            "kB",
            "MB",
            "GB",
        ]:
            if num < 1000.0:
                return "%3.0f %s" % (num, x)
            num /= 1000.0
        return "%3.0f %s" % (num, "TB")

    def formatByteRate(self, num):
        """Format transfer speed in kB/s"""

        num /= 1000
        return "%4.0f kB" % num

    def updateNumberOfObjectsToBeSynced(self):
        """Update the counter for number of objects to be synced"""
        self.labelSyncStatus.setText(
            _translate(
                "networkstatus",
                "Object(s) to be synced: %n",
                None,
                n=network.stats.pendingDownload() + network.stats.pendingUpload(),
            )
        )

    def updateNumberOfMessagesProcessed(self):
        """Update the counter for number of processed messages"""
        self.updateNumberOfObjectsToBeSynced()
        self.labelMessageCount.setText(
            _translate(
                "networkstatus",
                "Processed %n person-to-person message(s).",
                None,
                n=state.numberOfMessagesProcessed,
            )
        )

    def updateNumberOfBroadcastsProcessed(self):
        """Update the counter for the number of processed broadcasts"""
        self.updateNumberOfObjectsToBeSynced()
        self.labelBroadcastCount.setText(
            _translate(
                "networkstatus",
                "Processed %n broadcast message(s).",
                None,
                n=state.numberOfBroadcastsProcessed,
            )
        )

    def updateNumberOfPubkeysProcessed(self):
        """Update the counter for the number of processed pubkeys"""
        self.updateNumberOfObjectsToBeSynced()
        self.labelPubkeyCount.setText(
            _translate(
                "networkstatus",
                "Processed %n public key(s).",
                None,
                n=state.numberOfPubkeysProcessed,
            )
        )

    def updateNumberOfBytes(self):
        """
        This function is run every two seconds, so we divide the rate of bytes
        sent and received by 2.
        """
        self.labelBytesRecvCount.setText(
            _translate(
                "networkstatus",
                f"Down: {self.formatByteRate(network.stats.downloadSpeed())}/s  Total: {self.formatBytes(network.stats.receivedBytes())}",
            )
        )
        self.labelBytesSentCount.setText(
            _translate(
                "networkstatus",
                f"Up: {self.formatByteRate(network.stats.uploadSpeed())}/s  Total: {self.formatBytes(network.stats.sentBytes())}",
            )
        )

    def updateNetworkStatusTab(self, outbound, add, destination):
        """Add or remove an entry to the list of connected peers"""

        c = None
        if outbound:
            try:
                c = connectionpool.pool.outboundConnections[destination]
            except KeyError:
                if add:
                    return
        else:
            try:
                c = connectionpool.pool.inboundConnections[destination]
            except KeyError:
                try:
                    c = connectionpool.pool.inboundConnections[destination.host]
                except KeyError:
                    if add:
                        return

        self.tableWidgetConnectionCount.setUpdatesEnabled(False)
        self.tableWidgetConnectionCount.setSortingEnabled(False)

        if add:
            self.tableWidgetConnectionCount.insertRow(0)
            self.tableWidgetConnectionCount.setItem(
                0,
                0,
                QtWidgets.QTableWidgetItem(
                    "%s:%i" % (destination.host, destination.port)
                ),
            )
            if c is not None:
                self.tableWidgetConnectionCount.setItem(
                    0, 2, QtWidgets.QTableWidgetItem("%s" % (c.userAgent))
                )
                self.tableWidgetConnectionCount.setItem(
                    0, 3, QtWidgets.QTableWidgetItem("%s" % (c.tlsVersion))
                )
                self.tableWidgetConnectionCount.setItem(
                    0,
                    4,
                    QtWidgets.QTableWidgetItem("%s" % (",".join(map(str, c.streams)))),
                )
            try:
                # .. todo:: FIXME: hard coded stream no
                rating = "%.1f" % (knownnodes.knownNodes[1][destination]["rating"])
            except KeyError:
                rating = "-"
            self.tableWidgetConnectionCount.setItem(
                0, 1, QtWidgets.QTableWidgetItem("%s" % (rating))
            )
            brush = QtGui.QBrush(
                QtGui.QColor("yellow" if outbound else "green"),
                QtCore.Qt.BrushStyle.SolidPattern,
            )
            for j in range(1):
                item = self.tableWidgetConnectionCount.item(0, j)
                if item is not None:
                    item.setBackground(brush)
                    item.setForeground(
                        QtGui.QBrush(
                            QtGui.QColor("black"), QtCore.Qt.BrushStyle.SolidPattern
                        )
                    )
            item0 = self.tableWidgetConnectionCount.item(0, 0)
            if item0 is not None:
                item0.setData(QtCore.Qt.ItemDataRole.UserRole, destination)
            item1 = self.tableWidgetConnectionCount.item(0, 1)
            if item1 is not None:
                item1.setData(QtCore.Qt.ItemDataRole.UserRole, outbound)
        else:
            if not connectionpool.pool.inboundConnections:
                window = self.window()
                if window is not None and hasattr(window, "setStatusIcon"):
                    window.setStatusIcon("yellow")
            for i in range(self.tableWidgetConnectionCount.rowCount()):
                item_0 = self.tableWidgetConnectionCount.item(i, 0)
                if (
                    item_0 is None
                    or item_0.data(QtCore.Qt.ItemDataRole.UserRole) != destination
                ):
                    continue
                item_outbound = self.tableWidgetConnectionCount.item(i, 1)
                if (
                    item_outbound is not None
                    and item_outbound.data(QtCore.Qt.ItemDataRole.UserRole) == outbound
                ):
                    self.tableWidgetConnectionCount.removeRow(i)
                    break

        self.tableWidgetConnectionCount.setUpdatesEnabled(True)
        self.tableWidgetConnectionCount.setSortingEnabled(True)
        self.labelTotalConnections.setText(
            _translate(
                "networkstatus",
                f"Total Connections: {self.tableWidgetConnectionCount.rowCount()}",
            )
        )
        # FYI: The 'singlelistener' thread sets the icon color to green when it
        # receives an incoming connection, meaning that the user's firewall is
        # configured correctly.
        if (
            self.tableWidgetConnectionCount.rowCount()
            and state.statusIconColor == "red"
        ):
            window = self.window()
            if window is not None and hasattr(window, "setStatusIcon"):
                window.setStatusIcon("yellow")
        elif (
            self.tableWidgetConnectionCount.rowCount() == 0
            and state.statusIconColor != "red"
        ):
            window = self.window()
            if window is not None and hasattr(window, "setStatusIcon"):
                window.setStatusIcon("red")

    # timer driven
    def runEveryTwoSeconds(self):
        """Updates counters, runs every 2 seconds if the timer is running"""
        lookups = getattr(state.Inventory, "numberOfInventoryLookupsPerformed", 0)
        self.labelLookupsPerSecond.setText(
            _translate(
                "networkstatus", f"Inventory lookups per second: {int(lookups / 2)}"
            )
        )
        state.Inventory.numberOfInventoryLookupsPerformed = 0
        self.updateNumberOfBytes()
        self.updateNumberOfObjectsToBeSynced()

    def retranslateUi(self):
        """Conventional Qt Designer method for dynamic l10n"""
        super(NetworkStatus, self).retranslateUi()
        self.labelTotalConnections.setText(
            _translate("networkstatus", "Total Connections: %1").replace(
                "%1", str(self.tableWidgetConnectionCount.rowCount())
            )
        )
        self.labelStartupTime.setText(
            _translate("networkstatus", "Since startup on %1").replace(
                "%1", l10n.formatTimestamp(self.startup)
            )
        )
        self.updateNumberOfMessagesProcessed()
        self.updateNumberOfBroadcastsProcessed()
        self.updateNumberOfPubkeysProcessed()
