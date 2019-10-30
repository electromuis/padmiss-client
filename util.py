#!/usr/bin/env python

import os
import sys
from scandrivers.hid import RFIDReader
from config import PadmissConfig
import logging, time
log = logging.getLogger(__name__)

# from https://stackoverflow.com/a/51061279
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class FIFOReader(object):
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


class NULLReader(object):
    def __init__(self, **args):
        pass

    def poll(self):
        return

    def release(self):
        log.debug('released')


def construct_readers(config: PadmissConfig):
    readers = {}
    for device in config.devices:
        if device.type == "scanner":
            try:
                readers[device.path] = RFIDReader(device)
            except Exception as e:
                log.debug('Failed constructing reader:')
                log.debug(str(e))
        elif device.type == "fifo":
            readers[device.path] = FIFOReader(device.fifo_config)
        elif device.type == "dummy":
            readers[device.path] = NULLReader()
#            readers[s["path"]] = NULLReader(**s["config"])
    return readers