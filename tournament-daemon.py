#!/usr/bin/env python

import config
from api import TournamentApi, ScoreBreakdown, Score, Song, ChartUpload
from sm5_profile import generate_profile

import os
import shutil
import logging
import tempfile

from threading import Thread
from os import path
from signal import pause
from shutil import rmtree
from time import sleep
from xml.etree import ElementTree


api = TournamentApi(config.url, config.apikey)
log = logging.getLogger(__name__)


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


text_by_xpath = lambda parent, xpath: parent.find(xpath).text


def xpath_items(root, items, mapper):
    return { typ: mapper(text_by_xpath(root, path)) for typ, path in items.iteritems() }


def parse_score(root):
    tap_to_path = {
        'fantastics' : 'TapNoteScores/W1',
        'excellents' : 'TapNoteScores/W2',
        'greats'     : 'TapNoteScores/W3',
        'decents'    : 'TapNoteScores/W4',
        'wayoffs'    : 'TapNoteScores/W5',
        'misses'     : 'TapNoteScores/Miss',
        'holds'      : 'RadarActual/RadarValues/Holds',
        'holdsTotal' : 'RadarPossible/RadarValues/Holds',
        'minesHit'   : 'RadarActual/RadarValues/Mines',
        'rolls'      : 'RadarActual/RadarValues/Rolls',
        'rollsTotal' : 'RadarPossible/RadarValues/Rolls'
    }
    breakdown = ScoreBreakdown(**xpath_items(root, tap_to_path, int))
    score = Score(
            scoreBreakdown=breakdown,
            scoreValue=float(text_by_xpath(root, 'ScoreValue')),
            passed=False
            )
    return score


def parse_song(root):
    inf_to_path = {
        'title'                   : 'SongData/Title',
        'titleTransliteration'    : 'SongData/TitleTranslit',
        'subTitle'                : 'SongData/SubTitle',
        'subTitleTransliteration' : 'SongData/SubTitleTranslit',
        'artist'                  : 'SongData/Artist',
        'artistTransliteration'   : 'SongData/ArtistTranslit',
    }
    song = Song(
            durationSeconds=int(float(text_by_xpath(root, 'SongData/Duration'))),
            **xpath_items(root, inf_to_path, lambda x: x)
            )
    return song


def parse_playmode(root):
    val = text_by_xpath(root, 'Steps/StepsType')
    if val == 'dance-single':
        return 'Single'
    elif val == 'dance-double':
        return 'Double'
    else:
        raise Exception('Unsupported steps type: ' + val)


def parse_cabside(root):
    val = int(text_by_xpath(root, 'PlayerNumber'))
    if val == 0:
        return 'Left'
    elif val == 1:
        return 'Right'
    else:
        raise Exception('Invalid player number: ' + val)


def parse_upload(root):
    upload = ChartUpload(
            hash       = text_by_xpath(root, 'Steps/Hash'),
            meter      = int(text_by_xpath(root, 'Steps/Meter')),
            playMode   = parse_playmode(root),
            stepData   = text_by_xpath(root, 'Steps/StepData'),
            stepArtist = text_by_xpath(root, 'Steps/StepArtist'),
            song       = parse_song(root),
            score      = parse_score(root),
            cabSide    = parse_cabside(root)
            )
    return upload


def main():
    logging.basicConfig(level=logging.DEBUG)

    for side, init in config.readers.iteritems():
        reader = init()
        thread = Thread(target=poller, args=(side, reader))
        thread.daemon = True
        thread.start()

    while True:
        for n in os.listdir(config.scores_dir):
            if not n.endswith('.xml'):
                continue
            fn = path.join(config.scores_dir, n)
            try:
                log.debug('Uploading score from ' + fn)

                root = ElementTree.parse(fn).getroot()
                upload = parse_upload(root)
                playerGuid = text_by_xpath(root, 'PlayerGuid')
                player = api.get_player(playerGuid)
                if player:
                    log.debug('Uploading score for ' + player.nickname + ': ' + repr(upload))
                    api.post_score(player, upload)
                else:
                    log.warning('Player not found: ' + playerGuid)

            except:
                log.exception('Failed to upload score')
                backup = tempfile.mkstemp(suffix='.xml', prefix='failed_', dir=config.backup_dir)[1]
                shutil.copy(fn, backup)
                log.debug('Backed up failed score to ' + backup)
                    
            os.remove(fn)

            sleep(1)


if __name__ == '__main__':
    main()
