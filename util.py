#!/usr/bin/env python

import os

from hid import RFIDReader
from config import PadmissConfig, ScannerConfig
import logging
log = logging.getLogger(__name__)

class FIFOReader(object):
    def __init__(self, scannerConfig: ScannerConfig):
        self.scannerConfig = scannerConfig

        try:
            os.remove(self.scannerConfig.file_path)
        except:
            pass
        os.mkfifo(self.scannerConfig.file_path)


    def poll(self):
        with open(self.scannerConfig.file_path, 'r') as fh:
            return fh.readline()


    def release(self):
        os.remove(self.scannerConfig.file_path)


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
            try:
                readers[device.path] = FIFOReader(device.config)
            except Exception as e:
                log.debug('Failed constructing reader:')
                log.debug(str(e))
#        else:
#            readers[s["path"]] = NULLReader(**s["config"])
    return readers