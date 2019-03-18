#!/usr/bin/env python

import os


class FIFOReader(object):
    def __init__(self, path):
        self.path = path
        self.match = {}
        try:
            os.remove(path)
        except:
            pass
        os.mkfifo(path)


    def poll(self):
        with open(self.path, 'r') as fh:
            return fh.readline()


    def release(self):
        os.remove(self.path)
