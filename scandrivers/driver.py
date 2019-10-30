import logging
import sys
import urllib
import zipfile
from os import makedirs, path

from config import DeviceConfig
from api import TournamentApi, Player
from new_poller import Poller

log = logging.getLogger(__name__)

class ScanDriver(object):
    def __init__(self, config: DeviceConfig, poller: Poller):
        self.config = config
        self.poller = poller

    def update(self):
        pass

    def hasPlayer(self):
        return False

    def checkOut(self):
        return True

    def checkIn(self, player):
        dir = ''
        self.buildProfile(player, dir)
        return True

    def findPlayer(self, cardId):
        return None

    def detectPlayer(self):
        return None

    def buildProfile(self, player, dir):
        return True

    def downloadPacks(self, folder, player):
        log.debug(folder)
        packs = player.getMeta("songs")
        if isinstance(packs, list):
            i = 1
            for p in packs:
                try:
                    i = i + 1
                    log.debug(p)
                    u = urllib.request.urlopen(p)
                    if int(u.getheader("Content-Length")) > 1024 * 1024 * 10:
                        log.debug('Toobig')
                        continue
                    file_name = p.split('/')[-1]
                    ext = path.splitext(file_name)[1]
                    if ext != '.zip':
                        log.debug('Nozip: ' + str(ext))
                        continue
                    spath = folder + "/" + self.config.profile_dir_name + "/Songs"
                    filename = spath + "/custom" + str(i)
                    if not path.exists(spath):
                        makedirs(spath)
                    with open(filename, "wb") as f:
                        f.write(u.read())
                    with zipfile.ZipFile(filename) as zf:
                        zf.extractall(spath)
                except Exception as e:
                    print(('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e))