from shutil import rmtree
from sm5_profile import generate_profile
import config
import logging
from os import path, makedirs, remove
from api import TournamentApi, Player
import urlparse
import urllib
import zipfile

log = logging.getLogger(__name__)
api = TournamentApi(config.url, config.apikey)

def downloadPacks(side, player):
    packs = player.getMeta('packs')
    if packs != None and isinstance(packs, list):
        dir = path.join(side, config.profile_dir, "Songs")
        # makedirs(dir)

        for pack in packs:
            site = urllib.urlopen(pack)
            meta = site.info()
            if len(meta.getheaders("Content-Length")) == 0:
                raise Exception("No size")

            size = int(meta.getheaders("Content-Length")[0])
            if size == 0 or (size / 1024 / 1024) > 10 :
                raise Exception("File too big")

            name = path.basename(urlparse.urlparse(pack).path)
            if path.splitext(name)[1] != '.zip':
                raise Exception("Not a zip file")

            file = path.join(dir, name)

            f = open(file, "wb")
            f.write(site.read())
            site.close()
            f.close()

            with zipfile.ZipFile(file, 'r') as zip_ref:
                zip_ref.extractall(dir)

            remove(file)

def poller(side, reader):
    last_data = None
    while True:
        data = reader.poll()

        try:
            if data:
                data = data.strip()
                if data != last_data:
                    last_data = data

                    if path.isdir(side):
                        rmtree(side)
                    log.debug('Requesting player data for %s', data)
                    p = api.get_player(rfidUid=data)
                    if p:
                        log.debug('Generating profile for %s to %s', p.nickname, side)
                        generate_profile(path.join(side, config.profile_dir), p.nickname, p._id)
                        downloadPacks(side, p)

        except Exception:
            log.exception('Error getting player info from server')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    p = Player(_id="123123", nickname="test", metaData="{\"packs\":[\"http://dutchrhythm.com/dlm/[Electromuis] Hentai.zip\"]}")
    downloadPacks("C:\\dev\\stepmania\\Save\\test1", p)