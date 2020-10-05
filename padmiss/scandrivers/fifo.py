import os

import logging, time
log = logging.getLogger(__name__)

class Reader(object):
    name = 'FIFO Driver'

    def __init__(self, config):
        self.file = None
        self.path = config.path
        try:
            os.remove(self.path)
        except Exception as e:
            log.debug(str(e))

        os.mkfifo(self.path)
        self.file = os.open(self.path, os.O_RDONLY | os.O_NONBLOCK)

    def poll(self):
        try:
            buffer = os.read(self.file, 200)
        except OSError as err:
            buffer = None
            time.sleep(0.2)

        return "".join(map(chr, buffer))

    def __del__(self):
        if self.file:
            os.close(self.file)
        if os.path.exists(self.path):
            os.remove(self.path)

    def release(self):
        log.debug('released')