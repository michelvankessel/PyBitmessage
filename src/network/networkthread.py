"""
A thread to handle network concerns
"""
from . import asyncore_pollchoose as asyncore
from . import connectionpool
from queues import excQueue
from .threads import StoppableThread


class BMNetworkThread(StoppableThread):
    """Main network thread"""
    name = "Asyncore"

    def run(self):
        print(f"DEBUG: BMNetworkThread run() started. Name: {self.name} Stopped: {self._stopped}")
        try:
            while not self._stopped:
                # print("DEBUG: Calling connectionpool.pool.loop()")
                connectionpool.pool.loop()
        except Exception as e:
            excQueue.put((self.name, e))
            raise

    def stopThread(self):
        super(BMNetworkThread, self).stopThread()
        for i in list(connectionpool.pool.listeningSockets.values()):
            try:
                i.close()
            except Exception:
                pass
        for i in list(connectionpool.pool.outboundConnections.values()):
            try:
                i.close()
            except Exception:
                pass
        for i in list(connectionpool.pool.inboundConnections.values()):
            try:
                i.close()
            except Exception:
                pass

        # just in case
        asyncore.close_all()
