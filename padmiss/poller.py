import logging
from os import path, makedirs, remove, unlink, system, makedirs
from shutil import rmtree
from .scandrivers import construct_reader

from .api import TournamentApi, Player
from .thread_utils import CancellableThrowingThread

log = logging.getLogger(__name__)

class Poller(CancellableThrowingThread):
    def __init__(self, config, profilePath, readers, api):
        super().__init__()

        self.setName('Poller')
        self.api = api
        self.profilePath = profilePath
        self.readers = {}
        self.drivers = []

        self.unmount()
        self.mounted = None

        for r in readers:
            reader = construct_reader(r, self)
            if not reader:
                continue

            self.readers[r.type] = reader
            self.drivers.append(self.readers[r.type])

    def getThreads(self):
        return filter(lambda d: isinstance(d, CancellableThrowingThread), self.drivers)

    def getDriver(self, type):
        if type in self.readers:
            return self.readers[type]

        return None

    def exc_run(self):
        while not self.stop_event.wait(0.2):
            for d in self.drivers:
                d.update()

        for d in self.drivers:
            d.close()

    def unmount(self):
        if path.exists(self.profilePath):
            if path.islink(self.profilePath):
                unlink(self.profilePath)
            else:
                rmtree(self.profilePath)

        self.mounted = None

    def isMounted(self):
        if path.exists(self.profilePath):
            return True
        if self.mounted:
            return True

        return False