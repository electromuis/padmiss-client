from hid import RFIDReader
from util import FIFOReader

url = 'http://127.0.0.1:3020'
apikey = 've324mkvvk4k'

scores_dir = '/home/lonewolf/.stepmania-5.0/Save/Padmiss'

backup_dir = '/tmp/kalakala'

profile_dir = 'StepMania 5'

readers = {
#    '/tmp/p1' : lambda: RFIDReader(idVendor=0x08ff, idProduct=0x0009),
    '/tmp/p1' : lambda: FIFOReader('/tmp/foo'),
}
