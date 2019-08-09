import sys
import time
import threading
import logging

from config import PadmissConfigManager
from new_poller import Poller
from score_uploader import ScoreUploader
from thread_utils import CancellableThrowingThread, start_and_wait_for_threads
from socket_server import RestServerThread
from util import construct_readers

log = logging.getLogger(__name__)

class PadmissDaemon(CancellableThrowingThread):
    def __init__(self):
        super().__init__()
        self.setName(__name__)

    def exc_run(self):
        config_manager = PadmissConfigManager()
        config = config_manager.load_config()

        # initialize pollers
        readers = construct_readers(config)
        pollers = [Poller(config, side, reader) for side, reader in readers.items()]

        # initialize http servers
        rest_server = RestServerThread(pollers)

        # initialize score uploader
        score_uploader = ScoreUploader(config, pollers)
        threads = pollers + [rest_server, score_uploader]

        start_and_wait_for_threads(threads, lambda: self.stop_event.is_set())
