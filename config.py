import json
import os
from util import FIFOReader

if os.name == 'nt':
    from hidwin import RFIDReader
else:
    from hid import RFIDReader



class NULLReader(object):
    def __init__(self, **match):
        self.match = match

    def poll(self):
        return

url = ''
apikey = ''
scores_dir = ''
backup_dir = ''
profile_dir = 'StepMania 5'

readers = {}
readerConfig = {}

with open('config.json') as c:
    data = json.load(c)
    url = data["url"]
    apikey = data["apikey"]
    scores_dir = data["scores_dir"]
    backup_dir = data["backup_dir"]
    profile_dir = data["profile_dir"]
    readerConfig = data["scanners"]

    for s in readerConfig:
        if s["type"] == "scanner":
            readers[s["path"]] = RFIDReader(**s["config"])
        elif s["type"] == "fifo":
            readers[s["path"]] = FIFOReader(s["config"]["swPath"])
        else:
            readers[s["path"]] = NULLReader(**s["config"])
