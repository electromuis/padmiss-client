from shutil import rmtree
from sm5_profile import generate_profile
import config
import logging
from os import path, makedirs, remove, unlink, system, makedirs, symlink
from api import TournamentApi, Player
import urlparse
import urllib2
import zipfile
import sys
import subprocess
import xml.etree.ElementTree as ET
from collections import namedtuple
from threading import Thread
from time import sleep

log = logging.getLogger(__name__)
api = TournamentApi(config.url, config.apikey)

class Poller:
    def __init__(self, profilePath, reader):
        myConfig = reader.match
        self.myConfig = myConfig
        self.reader = reader
        self.mounted = False

        myConfig['profilePath'] = profilePath
        myConfig['usbPath'] = profilePath + '-usb'

        self.processUser(False, 'usb')
        self.processUser(False, 'card')

        if myConfig.has_key('hwPath'):
            myConfig['devPath'] = '/dev/disk/by-path/' + myConfig['hwPath']
            thread = Thread(target=self.pollHw)
            thread.daemon = True
            thread.start()

        if reader:
            thread = Thread(target=self.pollCard)
            thread.daemon = True
            thread.start()

    def downloadPacks(self, folder, player):
        log.debug(folder)
        packs = player.getMeta("songs")
        if isinstance(packs, list):
            i = 1
            for p in packs:
                try:
                    i = i + 1
                    log.debug(p)
                    u = urllib2.urlopen(p)
                    meta = u.info()
                    if int(meta.getheaders("Content-Length")[0]) > 1024 * 1024 * 10:
                        log.debug('Toobig')
                    continue
                    file_name = p.split('/')[-1]
                    ext = path.splitext(file_name)[1]
                    if ext != '.zip':
                        log.debug('Nozip: ' + str(ext))
                        continue
                    spath = folder + "/" + config.profile_dir + "/Songs"
                    filename = spath + "/custom" + str(i)
                    if not path.exists(spath):
                        makedirs(spath)
                    with open(filename, "wb") as f:
                        f.write(u.read())
                    with zipfile.ZipFile(filename) as zf:
                        zf.extractall(spath)
                except Exception as e:
                    print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)


    def processUser(self, newUser, type):
        myConfig = self.myConfig
        if newUser == False:
            log.debug('Cleaning profile for ' + type)
        else:
            log.debug('Processing profile for ' + type)
        
        if path.islink(myConfig['profilePath']):
            unlink(myConfig['profilePath'])
        elif path.isdir(myConfig['profilePath']):
            rmtree(myConfig['profilePath'])

        if newUser != False and (self.mounted == False or self.mounted._id != newUser._id):
            log.debug('Mounting to SM5')

            if type == 'card':
                makedirs(myConfig['profilePath'])
                profileSMPath = path.join(myConfig['profilePath'], config.profile_dir)
                generate_profile(profileSMPath, newUser)
                self.downloadPacks(myConfig['profilePath'], newUser)

            if type == 'usb':
                symlink(myConfig['usbPath'], myConfig['profilePath'])

        self.mounted = newUser

    def pollHw(self):
        myConfig = self.myConfig
        while True:
            sleep(0.5)

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

                    p = api.get_player(playerId=guid)

                if not p:
                    p = Player(nickname='none', _id='none')

                p.mountType = 'usb'
                self.processUser(p, 'usb')

    def pollCard(self):
        myConfig = self.myConfig
        reader = self.reader

        while True:
            data = reader.poll()

            try:
                if data:
                    data = data.strip()
                    if data:
                        log.debug('Requesting player data for %s', data)
                        if self.mounted and self.mounted.mountType == 'card' and self.mounted._id == data:
                            self.processUser(False, 'card')
                            return

                        p = api.get_player(rfidUid=data)
                        if p:
                            p.mountType = 'card'
                            self.processUser(p, 'card')


            except Exception:
                log.exception('Error getting player info from server')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # p = Player(_id="123123", nickname="test", metaData="{\"packs\":[\"http://dutchrhythm.com/dlm/[Electromuis] Hentai.zip\"]}")
    # downloadPacks("C:\\dev\\stepmania\\Save\\test1", p)
