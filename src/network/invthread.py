"""
Thread to send inv annoucements
"""
import queue
import random
from time import time

import addresses
import protocol
import state
from . import connectionpool
from . import dandelion_ins, invQueue
from .threads import StoppableThread


def handleExpiredDandelion(expired):
    """For expired dandelion objects, mark all remotes as not having
       the object"""
    if not expired:
        return
    for i in connectionpool.pool.connections():
        if not i.fullyEstablished:
            continue
        for x in expired:
            streamNumber, hashid, _ = x
            try:
                del i.objectsNewToMe[hashid]
            except KeyError:
                if streamNumber in i.streams:
                    with i.objectsNewToThemLock:
                        i.objectsNewToThem[hashid] = time()


class InvThread(StoppableThread):
    """Main thread that sends inv annoucements"""

    name = "InvBroadcaster"

    @staticmethod
    def handleLocallyGenerated(stream, hashId):
        """Locally generated inventory items require special handling"""
        dandelion_ins.addHash(hashId, stream=stream)
        for connection in connectionpool.pool.connections():
            if dandelion_ins.enabled and connection != \
                    dandelion_ins.objectChildStem(hashId):
                continue
            connection.objectsNewToThem[hashId] = time()

    def run(self):
        while not state.shutdown:
            chunk = []
            while True:
                # Dandelion fluff trigger by expiration
                handleExpiredDandelion(dandelion_ins.expire(invQueue))
                try:
                    data = invQueue.get(False)
                    print(f"DEBUG_TRACE: invThread got from queue: stream={data[0]}, hash={data[1].hex()}", flush=True)
                    chunk.append((data[0], data[1]))
                    # locally generated
                    if len(data) == 2 or data[2] is None:
                        print("DEBUG_TRACE: invThread calling handleLocallyGenerated", flush=True)
                        self.handleLocallyGenerated(data[0], data[1])
                except queue.Empty:
                    break

            if chunk:
                print(f"DEBUG_TRACE: invThread processing chunk of {len(chunk)} items", flush=True)
                for connection in connectionpool.pool.connections():
                    fluffs = []
                    stems = []
                    for inv in chunk:
                        if inv[0] not in connection.streams:
                            continue
                        try:
                            with connection.objectsNewToThemLock:
                                del connection.objectsNewToThem[inv[1]]
                        except KeyError:
                            continue
                        try:
                            if connection == dandelion_ins.objectChildStem(inv[1]):
                                # Fluff trigger by RNG
                                # auto-ignore if config set to 0, i.e. dandelion is off
                                if random.randint(1, 100) >= dandelion_ins.enabled:
                                    fluffs.append(inv[1])
                                # send a dinv only if the stem node supports dandelion
                                elif connection.services & protocol.NODE_DANDELION > 0:
                                    stems.append(inv[1])
                                else:
                                    fluffs.append(inv[1])
                        except KeyError:
                            fluffs.append(inv[1])

                    if fluffs:
                        print(f"DEBUG_TRACE: Sending {len(fluffs)} fluffs to {connection.destination}", flush=True)
                        random.shuffle(fluffs)
                        connection.append_write_buf(protocol.CreatePacket(
                            'inv',
                            addresses.encodeVarint(
                                len(fluffs)) + b''.join(fluffs)))
                    if stems:
                        print(f"DEBUG_TRACE: Sending {len(stems)} stems to {connection.destination}", flush=True)
                        random.shuffle(stems)
                        connection.append_write_buf(protocol.CreatePacket(
                            'dinv',
                            addresses.encodeVarint(
                                len(stems)) + b''.join(stems)))

            invQueue.iterate()
            for _ in range(len(chunk)):
                invQueue.task_done()

            dandelion_ins.reRandomiseStems()

            self.stop.wait(1)
