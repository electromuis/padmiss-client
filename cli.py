import logging
import time

from daemon import PadmissDaemon

log = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format=' %(threadName)s %(name)s - %(levelname)s: %(message)s')
    padmiss_daemon = PadmissDaemon()

    try:
        padmiss_daemon.start()
        while True:
            padmiss_daemon.join(0.1)

    except (Exception, KeyboardInterrupt) as e:
        log.exception("Caught following while running daemon")
        padmiss_daemon.stop()
        padmiss_daemon.join()
        log.info("Shutting down")
