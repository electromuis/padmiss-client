from hid import RFIDReader
from util import FIFOReader
import json

url = ''
apikey = ''
scores_dir = ''
backup_dir = ''
profile_dir = 'StepMania 5'

readers = {}

with open('config.json') as c:
    data = json.load(c)
    url = data["url"]
    apikey = data["apikey"]
    scores_dir = data["scores_dir"]
    backup_dir = data["backup_dir"]
    profile_dir = data["profile_dir"]

    for s in data["scanners"]:
        readers[s["path"]] = RFIDReader(**s["config"])
