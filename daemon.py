import sys
import time
import threading
import logging

from util import construct_readers
from new_poller import Poller
from score_uploader import ScoreUploader
from config import PadmissConfigManager

log = logging.getLogger(__name__)

class PadmissDaemon(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

    def stop(self):
        log.info("Stop signal received")
        self._stop_event.set()

    def run(self):
        log.info("Starting PadmissDaemon")

        config_manager = PadmissConfigManager()
        config = config_manager.load_config()

        # initialize pollers
        readers = construct_readers(config)
        pollers = [Poller(config, side, reader) for side, reader in readers.items()]

        # initialize score uploader
        score_uploader = ScoreUploader(config)

        threads = pollers + [score_uploader]

        # run threads as long as daemon is not stopped...
        for thread in threads:
            thread.start()
        while not self._stop_event.is_set():
            for thread in threads:
                if thread.is_alive():
                    thread.join(0.1)

        log.info("Stopping PadmissDaemon")

        # daemon stopped? clean up and wait for them to stop
        for thread in threads:
            if thread.is_alive():
                thread.stop()

        for thread in threads:
            if thread.is_alive():
                thread.join()

        log.info("Stopped PadmissDaemon")

