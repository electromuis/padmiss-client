import os
if os.name == 'nt':
    from hidwin import RFIDReader
else:
    from hid import RFIDReader

import json

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
        readers[s["path"]] = RFIDReader(**s["config"])
