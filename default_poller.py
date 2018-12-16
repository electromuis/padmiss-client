from shutil import rmtree
from sm5_profile import generate_profile
import config
import logging
from os import path
from api import TournamentApi

log = logging.getLogger(__name__)
api = TournamentApi(config.url, config.apikey)

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
        except Exception:
            log.exception('Error getting player info from server')
