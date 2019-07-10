#!/usr/bin/env python

import os

from hid import RFIDReader
from config import PadmissConfig
import logging, time
log = logging.getLogger(__name__)

class FIFOReader(object):
    def __init__(self, config):
        log.debug('reader')
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
        self.file.close()
        os.remove(self.path)

    def release(self):
        log.debug('released')


class NULLReader(object):
    def __init__(self, **args):
        pass

    def poll(self):
        return


def construct_readers(config: PadmissConfig):
    readers = {}
    for device in config.devices:
        if device.type == "scanner":
            try:
                readers[device.path] = RFIDReader(device.config)
            except Exception as e:
                log.debug('Failed constructing reader:')
                log.debug(str(e))
        elif device.type == "fifo":
            readers[device.path] = FIFOReader(device.fifo_config)
#        else:
#            readers[s["path"]] = NULLReader(**s["config"])
    return readers