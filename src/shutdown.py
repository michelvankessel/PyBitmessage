"""shutdown function"""

import os
import threading
import time

import queue

import state
from debug import logger
from helper_sql import sqlStoredProcedure
from network import StoppableThread
from network.knownnodes import saveKnownNodes
from queues import (
    addressGeneratorQueue,
    objectProcessorQueue,
    UISignalQueue,
    workerQueue,
)


def doCleanShutdown():
    """
    Used to tell all the treads to finish work and exit.
    """
    state.shutdown = 1

    objectProcessorQueue.put(("checkShutdownVariable", "no data"))
    for thread in threading.enumerate():
        if thread.is_alive() and isinstance(thread, StoppableThread):
            thread.stopThread()

    UISignalQueue.put(
        ("updateStatusBar", "Saving the knownNodes list of peers to disk...")
    )
    logger.info("Saving knownNodes list of peers to disk")
    saveKnownNodes()
    logger.info("Done saving knownNodes list of peers to disk")
    UISignalQueue.put(
        ("updateStatusBar", "Done saving the knownNodes list of peers to disk.")
    )
    logger.info("Flushing inventory in memory out to disk...")
    UISignalQueue.put(
        (
            "updateStatusBar",
            "Flushing inventory in memory out to disk."
            " This should normally only take a second...",
        )
    )
    try:
        inventory = getattr(state, "Inventory", None)
        if inventory is not None:
            inventory.flush()
    except Exception as e:
        logger.info(f"Inventory not available for flushing: {e}")

    # Verify that the objectProcessor has finished exiting. It should have
    # incremented the shutdown variable from 1 to 2. This must finish before
    # we command the sqlThread to exit.
    # Add a timeout to prevent indefinite hang if objectProcessor is stuck
    shutdown_wait_count = 0
    while state.shutdown == 1:
        time.sleep(0.1)
        shutdown_wait_count += 1
        if shutdown_wait_count > 100:  # 10 second timeout
            logger.warning(
                "Timeout waiting for objectProcessor to acknowledge shutdown."
                " Forcing shutdown."
            )
            state.shutdown = 2
            break

    # Wait long enough to guarantee that any running proof of work worker
    # threads will check the shutdown variable and exit. If the main thread
    # closes before they do then they won't stop.
    time.sleep(0.25)

    for thread in threading.enumerate():
        if (
            thread is not threading.currentThread()
            and isinstance(thread, StoppableThread)
            and thread.name != "SQL"
        ):
            logger.debug("Waiting for thread %s", thread.name)
            thread.join(timeout=5)
            if thread.is_alive():
                logger.warning("Thread %s did not stop within timeout", thread.name)

    # This one last useless query will guarantee that the previous flush
    # committed and that the
    # objectProcessorThread committed before we close the program.
    # sqlQuery("SELECT address FROM subscriptions")
    logger.info("Finished flushing inventory.")
    sqlStoredProcedure("exit")

    # flush queues
    for q in (workerQueue, UISignalQueue, addressGeneratorQueue, objectProcessorQueue):
        while True:
            try:
                q.get(False)
                q.task_done()
            except queue.Empty:
                break

    try:
        if state.thisapp and (state.thisapp.daemon or not state.enableGUI):
            logger.info("Clean shutdown complete.")
            state.thisapp.cleanup()
            os._exit(0)
        else:
            logger.info("Core shutdown complete.")
    except (AttributeError, NameError):
        logger.info("Core shutdown complete (state.thisapp not available).")
    for thread in threading.enumerate():
        logger.debug("Thread %s still running", thread.name)
