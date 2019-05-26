import logging
import sys
import time

from util import construct_readers
from new_poller import Poller
from score_uploader import ScoreUploader
from config import PadmissConfigManager

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format=' %(threadName)s %(name)s - %(levelname)s: %(message)s')
    config_manager = PadmissConfigManager()
    config = config_manager.load_config()

    # initialize pollers
    readers = construct_readers(config)
    pollers = [Poller(config, side, reader) for side, reader in readers.items()]

    # initialize score uploader
    score_uploader = ScoreUploader(config)

    # initialize and wait for threads to complete
    threads = pollers + [score_uploader]

    for thread in threads:
        thread.daemon = True
        thread.start()

    while True:
        time.sleep(1)
