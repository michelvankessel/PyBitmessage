"""
Module for using filesystem (directory with files) for inventory storage
"""

import logging
import time
from binascii import hexlify, unhexlify
from pathlib import Path
from threading import RLock

from paths import lookupAppdataFolder
from .storage import InventoryItem, InventoryStorage

logger = logging.getLogger("default")


class FilesystemInventory(InventoryStorage):
    """Filesystem for inventory storage"""

    topDir = "inventory"
    objectDir = "objects"
    metadataFilename = "metadata"
    dataFilename = "data"

    def __init__(self):
        super(FilesystemInventory, self).__init__()
        self.baseDir = Path(lookupAppdataFolder()) / FilesystemInventory.topDir
        for createDir in [self.baseDir, self.baseDir / FilesystemInventory.objectDir]:
            if createDir.exists():
                if not createDir.is_dir():
                    raise IOError(f"{createDir} exists but it's not a directory")
            else:
                createDir.mkdir(parents=True, exist_ok=True)
        # Guarantees that two receiveDataThreads
        # don't receive and process the same message
        # concurrently (probably sent by a malicious individual)
        self.lock = RLock()
        self._inventory = {}
        self._load()

    def __contains__(self, hashval):
        for streamDict in self._inventory.values():
            if hashval in streamDict:
                return True
        return False

    def __delitem__(self, hash_):
        raise NotImplementedError

    def __getitem__(self, hashval):
        for streamDict in self._inventory.values():
            try:
                retval = streamDict[hashval]
            except KeyError:
                continue
            if retval.payload is None:
                retval = InventoryItem(
                    retval.type,
                    retval.stream,
                    self.getData(hashval),
                    retval.expires,
                    retval.tag,
                )
            return retval
        raise KeyError(hashval)

    def __setitem__(self, hashval, value):
        with self.lock:
            value = InventoryItem(*value)
            objectPath = (
                self.baseDir / FilesystemInventory.objectDir / hexlify(hashval).decode()
            )
            try:
                objectPath.mkdir(parents=True, exist_ok=True)
            except OSError:
                pass
            try:
                metadataFile = objectPath / FilesystemInventory.metadataFilename
                with open(metadataFile, "w") as f:
                    f.write(
                        f"{value.type},{value.stream},{value.expires},{hexlify(value.tag).decode()},"
                    )
                dataFile = objectPath / FilesystemInventory.dataFilename
                with open(dataFile, "wb") as f:
                    f.write(value.payload)
            except IOError:
                raise KeyError
            try:
                self._inventory[value.stream][hashval] = value
            except KeyError:
                self._inventory[value.stream] = {}
                self._inventory[value.stream][hashval] = value

    def delHashId(self, hashval):
        """Remove object from inventory"""
        for stream in self._inventory:
            try:
                del self._inventory[stream][hashval]
            except KeyError:
                pass
        with self.lock:
            objectPath = (
                self.baseDir / FilesystemInventory.objectDir / hexlify(hashval).decode()
            )
            try:
                metadataFile = objectPath / FilesystemInventory.metadataFilename
                metadataFile.unlink()
            except IOError:
                pass
            try:
                dataFile = objectPath / FilesystemInventory.dataFilename
                dataFile.unlink()
            except IOError:
                pass
            try:
                objectPath.rmdir()
            except IOError:
                pass

    def __iter__(self):
        elems = []
        for streamDict in self._inventory.values():
            elems.extend(streamDict.keys())
        return elems.__iter__()

    def __len__(self):
        retval = 0
        for streamDict in self._inventory.values():
            retval += len(streamDict)
        return retval

    def _load(self):
        newInventory = {}
        for hashId in self.object_list():
            try:
                objectType, streamNumber, expiresTime, tag = self.getMetadata(hashId)
                try:
                    newInventory[streamNumber][hashId] = InventoryItem(
                        objectType, streamNumber, None, expiresTime, tag
                    )
                except KeyError:
                    newInventory[streamNumber] = {}
                    newInventory[streamNumber][hashId] = InventoryItem(
                        objectType, streamNumber, None, expiresTime, tag
                    )
            except KeyError:
                logger.debug("error loading %s", hexlify(hashId), exc_info=True)
        self._inventory = newInventory

    def stream_list(self):
        """Return list of streams"""
        return self._inventory.keys()

    def object_list(self):
        """Return inventory vectors (hashes) from a directory"""
        objectDir = self.baseDir / FilesystemInventory.objectDir
        return [unhexlify(x.name) for x in objectDir.iterdir() if x.is_dir()]

    def getData(self, hashId):
        """Get object data"""
        objectPath = (
            self.baseDir / FilesystemInventory.objectDir / hexlify(hashId).decode()
        )
        dataFile = objectPath / FilesystemInventory.dataFilename
        try:
            with open(dataFile, "r") as f:
                return f.read()
        except IOError:
            raise AttributeError

    def getMetadata(self, hashId):
        """Get object metadata"""
        objectPath = (
            self.baseDir / FilesystemInventory.objectDir / hexlify(hashId).decode()
        )
        metadataFile = objectPath / FilesystemInventory.metadataFilename
        try:
            with open(metadataFile, "r") as f:
                objectType, streamNumber, expiresTime, tag = f.read().split(",", 4)[:4]
                return [
                    int(objectType),
                    int(streamNumber),
                    int(expiresTime),
                    unhexlify(tag),
                ]
        except IOError:
            raise KeyError

    def by_type_and_tag(self, objectType, tag):
        """Get a list of objects filtered by object type and tag"""
        retval = []
        for streamDict in self._inventory.values():
            for hashId, item in streamDict:
                if item.type == objectType and item.tag == tag:
                    try:
                        if item.payload is None:
                            item.payload = self.getData(hashId)
                    except IOError:
                        continue
                    retval.append(
                        InventoryItem(
                            item.type, item.stream, item.payload, item.expires, item.tag
                        )
                    )
        return retval

    def hashes_by_stream(self, stream):
        """Return inventory vectors (hashes) for a stream"""
        try:
            return self._inventory[stream].keys()
        except KeyError:
            return []

    def unexpired_hashes_by_stream(self, stream):
        """Return unexpired hashes in the inventory for a particular stream"""
        try:
            return [
                x
                for x, value in self._inventory[stream].items()
                if value.expires > int(time.time())
            ]
        except KeyError:
            return []

    def flush(self):
        """Flush the inventory and create a new, empty one"""
        self._load()

    def clean(self):
        """Clean out old items from the inventory"""
        minTime = int(time.time()) - 60 * 60 * 30
        deletes = []
        for streamDict in self._inventory.values():
            for hashId, item in streamDict.items():
                if item.expires < minTime:
                    deletes.append(hashId)
        for hashId in deletes:
            self.delHashId(hashId)
