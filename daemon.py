import sys
import time
import threading
import logging

from config import PadmissConfigManager
from new_poller import Poller
from score_uploader import ScoreUploader
from thread_utils import CancellableThrowingThread, start_and_wait_for_threads

log = logging.getLogger(__name__)

class PadmissDaemon(CancellableThrowingThread):
    def __init__(self):
        super().__init__()
        self.setName(__name__)

    def exc_run(self):
        config_manager = PadmissConfigManager()
        config = config_manager.load_config()

        readers = {}
        for r in config.devices:
            print(r.path)
            if r.path not in readers:
                readers[r.path] = []
            readers[r.path].append(r)

        pollers = []
        for p,r in readers.items():
            pollers.append(Poller(config, p, r))

        # initialize score uploader
        score_uploader = ScoreUploader(config, pollers)
        threads = pollers + [score_uploader]

        # initialize http servers
        if config.webserver and config.webserver.enabled:
            from socket_server import RestServerThread
            threads.append(RestServerThread(pollers))

        start_and_wait_for_threads(threads, lambda: self.stop_event.is_set())
