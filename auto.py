import logging
import time

from src.padmiss.daemon import PadmissDaemon
from src.padmiss.thread_utils import start_and_wait_for_threads
from src.padmiss import stepmania

log = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(threadName)s - %(levelname)s: %(message)s')
    padmiss_daemon = PadmissDaemon()

    try:
        start_and_wait_for_threads([padmiss_daemon])
    except BaseException:
        log.exception("Caught following while running daemon")