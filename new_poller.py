import logging
import os
import subprocess
import sys
import threading
import urllib.request, urllib.error, urllib.parse
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from collections import namedtuple
from os import path, makedirs, remove, unlink, system, makedirs
from shutil import rmtree
from threading import Thread
from time import sleep

if os.name != 'nt':
    from os import symlink

from api import TournamentApi, Player
from sm5_profile import generate_profile
from thread_utils import CancellableThrowingThread

log = logging.getLogger(__name__)

class Poller(CancellableThrowingThread):
    def __init__(self, config, profilePath, reader):
        super().__init__()
        self.setName('Poller')
        self.api = TournamentApi(config.url, config.apikey)
        self.config = config
        self.profilePath = profilePath
        self.reader = reader
        self.mounted = None

    def exc_run(self):
        log.info("Starting Poller")

        # self.processUser(False, 'usb')
        self.processUser(None, 'card')

        """if 'hwPath' in self.myConfig:
            self.myConfig['devPath'] = '/dev/disk/by-path/' + self.myConfig['hwPath']
            self.pollHw() """

        if self.reader:
            self.pollCard()

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
                    meta = u.info()
                    if int(meta.getheaders("Content-Length")[0]) > 1024 * 1024 * 10:
                        log.debug('Toobig')
                    continue
                    file_name = p.split('/')[-1]
                    ext = path.splitext(file_name)[1]
                    if ext != '.zip':
                        log.debug('Nozip: ' + str(ext))
                        continue
                    spath = folder + "/" + self.config.profile_dir + "/Songs"
                    filename = spath + "/custom" + str(i)
                    if not path.exists(spath):
                        makedirs(spath)
                    with open(filename, "wb") as f:
                        f.write(u.read())
                    with zipfile.ZipFile(filename) as zf:
                        zf.extractall(spath)
                except Exception as e:
                    print(('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e))

    def processUser(self, newUser, type):
        if newUser:
            log.debug('Processing profile for ' + type)
        else:
            log.debug('Cleaning profile for ' + type)
        
        if path.islink(self.profilePath):
            unlink(self.profilePath)
        elif path.isdir(self.profilePath):
            rmtree(self.profilePath) # dangerous

        if newUser and (self.mounted is None or self.mounted._id != newUser._id):
            log.debug('Mounting to SM5')

            if type == 'card':
                makedirs(self.profilePath)
                profileSMPath = path.join(self.profilePath, self.config.profile_dir)
                generate_profile(self.api, profileSMPath, newUser)
                self.downloadPacks(self.profilePath, newUser)

            #if type == 'usb':
            #    symlink(myConfig['usbPath'], self.profilePath)

        self.mounted = newUser

        """def pollHw(self):
        myConfig = self.myConfig
        while not self.stop_event.wait(1):
            p = subprocess.Popen(["ls", "/dev/disk/by-path/"], stdout=subprocess.PIPE)
            out = p.stdout.read().split("\n")
            found = myConfig['hwPath'] in out
            hasMounted = path.exists(myConfig['usbPath'])
            if found == hasMounted:
                continue

            if not found:
                log.debug('Lost usb')
                if path.exists(myConfig['usbPath']):
                    system('sync')
                    system('sudo umount -f ' + myConfig['usbPath'])
                    rmtree(myConfig['usbPath'])

                self.processUser(False, 'usb')
            else:
                log.debug('Found usb')

                if not path.exists(myConfig['usbPath']):
                    makedirs(myConfig['usbPath'])
                    log.debug('mount ' + myConfig['usbPath'])
                    system('mount ' + myConfig['usbPath'])

                stats = myConfig['usbPath'] + '/Stats.xml'
                p = False
                if path.exists(stats):
                    tree = ET.parse(stats)
                    root = tree.getroot()
                    guid = root.find('Guid').text

                    p = self.api.get_player(playerId=guid)

                if not p:
                    p = Player(nickname='none', _id='none')

                p.mountType = 'usb'
                self.processUser(p, 'usb') """

    def pollCard(self):
        while not self.stop_event.wait(1):
            try:
                data = self.reader.poll()
                if data:
                    data = data.strip()
                    if data:
                        if self.mounted and self.mounted.mountType == 'card' and self.mounted.rfidUid == data:
                            log.debug('Eject player %s', data)
                            self.processUser(None, 'card')
                            continue

                        p = self.api.get_player(rfidUid=data)

                        if p:
                            log.debug('Mount player %s', data)
                            p.mountType = 'card'
                            p.rfidUid = data
                            self.processUser(p, 'card')

            except Exception:
                log.exception('Error getting player info from server')

        self.reader.release()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # p = Player(_id="123123", nickname="test", metaData="{\"packs\":[\"http://dutchrhythm.com/dlm/[Electromuis] Hentai.zip\"]}")
    # downloadPacks("C:\\dev\\stepmania\\Save\\test1", p)
