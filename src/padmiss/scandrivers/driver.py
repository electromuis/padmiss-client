import logging
import sys
import urllib
import zipfile
from os import makedirs, path, unlink, rename
from shutil import rmtree
import tempfile

from ..sm5_profile import *

log = logging.getLogger(__name__)

class ScanDriver(object):
    def __init__(self, config, poller):
        self.config = config
        self.poller = poller
        self.actions = []
        self.threaded = False

    def togglePlayer(self, playerId, mode):
        self.actions.append({'playerId': playerId, 'mode': mode})

    def getPlayer(self, playerId):
        p = self.poller.api.get_player(playerId=playerId)
        if p:
            p.driver = self
            return p

        return None

    def handleAction(self, action):
        if action.mode == 'out':
            self.checkOut()
            return True
        if action.mode == 'in':
            p = self.getPlayer(action.playerId)
            if p == None:
                log.debug('Player not found for: ' + str(action.playerId))
                return False
            return self.checkIn(p)

        return False

    # Can be overidden to poll for a detected player, this runs on the poller thread
    def update(self):
        for a in self.actions:
            self.handleAction(a)
            self.actions.remove(a)
            pass

    def checkOut(self):
        self.poller.unmount()

    def checkIn(self, player):
        if self.poller.isMounted():
            log.debug('Mount exists, not overwriting. First unmount!')

        d = tempfile.mkdtemp(prefix='padmiss')
        generate_profile(d, player, self.poller.api)
        self.downloadPacks(d, player)
        rename(d, self.config.path)

        if not path.exists(self.config.path):
            log.debug('Mounting failed')
            return False

        self.poller.mounted = player
        return True

    def downloadPacks(self, folder, player):
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

                    spath = path.join(folder, self.config.profile_dir_name, "Songs")
                    filename = path.join(spath, "custom" + str(i))

                    if not path.exists(spath):
                        makedirs(spath)
                    with open(filename, "wb") as f:
                        f.write(u.read())
                    with zipfile.ZipFile(filename) as zf:
                        zf.extractall(spath)
                except Exception as e:
                    print(('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e))