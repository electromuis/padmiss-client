import os
if os.name == 'nt':
    from hidwin import RFIDReader
else:
    from hid import RFIDReader

import json

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
        if s.has_key('vid'):
            readers[s["path"]] = RFIDReader(**s["config"])
        else:
            readers[s["path"]] = NULLReader(**s["config"])
