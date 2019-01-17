from shutil import rmtree
from sm5_profile import generate_profile
import config
import logging
from os import path, makedirs, remove
from api import TournamentApi, Player
import urlparse
import urllib2
import zipfile
import sys

log = logging.getLogger(__name__)
api = TournamentApi(config.url, config.apikey)

def downloadPacks(folder, player):
    log.debug(folder)
    packs = player.getMeta("songs")
    if isinstance(packs, list):
        for p in packs:
            try:
                log.debug(p)
                u = urllib2.urlopen(p)
                meta = u.info()
                if int(meta.getheaders("Content-Length")[0]) > 1024 * 1024 * 5:
                    log.debug('Toobig')
	            continue
                file_name = p.split('/')[-1]
                ext = path.splitext(file_name)[1]
                if ext != '.zip':
                    log.debug('Nozip: ' + str(ext))
                    continue
                spath = folder + "/Songs"
                filename = spath + "/" + file_name
                if not path.exists(spath):
                    makedirs(spath)
                with open(filename, "wb") as f:
                    f.write(u.read())
                with zipfile.ZipFile(filename) as zf:
                    zf.extractall(spath)
            except Exception as e:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)


            

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