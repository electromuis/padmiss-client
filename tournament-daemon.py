#!/usr/bin/env python

import config
from api import TournamentApi, ScoreBreakdown, Score, Song, ChartUpload, TimingWindows
from new_poller import poller

import os
import shutil
import logging
import tempfile

from threading import Thread
from os import path

from time import sleep
from xml.etree import ElementTree


api = TournamentApi(config.url, config.apikey)
log = logging.getLogger(__name__)

text_by_xpath = lambda parent, xpath: parent.find(xpath).text


def xpath_items(root, items, mapper):
    return { typ: mapper(text_by_xpath(root, path)) for typ, path in items.iteritems() }


def parse_score(root):
    tap_to_path = {
        'fantastics'   : 'TapNoteScores/W1',
        'excellents'   : 'TapNoteScores/W2',
        'greats'       : 'TapNoteScores/W3',
        'decents'      : 'TapNoteScores/W4',
        'wayoffs'      : 'TapNoteScores/W5',
        'misses'       : 'TapNoteScores/Miss',
        'holds'        : 'RadarActual/RadarValues/Holds',
        'holdsTotal'   : 'RadarPossible/RadarValues/Holds',
        'minesHit'     : 'TapNoteScores/HitMine',
        'minesAvoided' : 'TapNoteScores/AvoidMine',
        'minesTotal'   : 'RadarPossible/RadarValues/Mines',
        'rolls'        : 'RadarActual/RadarValues/Rolls',
        'rollsTotal'   : 'RadarPossible/RadarValues/Rolls',
        'jumps'        : 'RadarActual/RadarValues/Jumps',
        'jumpsTotal'   : 'RadarPossible/RadarValues/Jumps',
        'hands'        : 'RadarActual/RadarValues/Hands',
        'handsTotal'   : 'RadarPossible/RadarValues/Hands'
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


def parse_speedmod(root):
    node = root.find('Mods/ScrollSpeed')
    val = float(node.text)
    typ = node.get('Type')
    return dict(type=typ, value=val)


def parse_mods(root, paths, conv):
    mods = []
    for p in paths:
        container = root.find(p)
        for mod in container:
            mods.append(conv(mod))
    return mods


def parse_perspective(root):
    return dict(
        tilt=float(text_by_xpath(root, 'Mods/Perspectives/Tilt')),
        skew=float(text_by_xpath(root, 'Mods/Perspectives/Skew')))


def parse_timing_windows(root):
    window_to_path = {
        'fantasticTimingWindow' : 'TimingWindows/W1',
        'excellentTimingWindow' : 'TimingWindows/W2',
        'greatTimingWindow'     : 'TimingWindows/W3',
        'decentTimingWindow'    : 'TimingWindows/W4',
        'wayoffTimingWindow'    : 'TimingWindows/W5',
        'mineTimingWindow'      : 'TimingWindows/Mine',
        'holdTimingWindow'      : 'TimingWindows/Hold',
        'rollTimingWindow'      : 'TimingWindows/Roll'
    }
    return TimingWindows(**xpath_items(root, window_to_path, lambda x: float(x)))


conv_toggle_mod = lambda mod: mod.tag
conv_float_mod = lambda mod: dict(name=mod.tag, value=float(mod.text))


def parse_upload(root):
    upload = ChartUpload(
            hash          = text_by_xpath(root, 'Steps/Hash'),
            meter         = int(text_by_xpath(root, 'Steps/Meter')),
            playMode      = parse_playmode(root),
            stepData      = text_by_xpath(root, 'Steps/StepData'),
            stepArtist    = text_by_xpath(root, 'Steps/StepArtist'),
            song          = parse_song(root),
            score         = parse_score(root),
            cabSide       = parse_cabside(root),
            speedMod      = parse_speedmod(root),
            musicRate     = float(text_by_xpath(root, 'Mods/MusicRate')),
            modsTurn      = parse_mods(root, ('Mods/Turns',), conv_toggle_mod),
            modsTransform = parse_mods(root, ('Mods/Transforms',), conv_toggle_mod),
            modsOther     = parse_mods(root, ('Mods/Accels', 'Mods/Effects', 'Mods/Appearances', 'Mods/Scrolls'), conv_float_mod),
            noteSkin      = text_by_xpath(root, 'Mods/NoteSkin'),
            perspective   = parse_perspective(root),
            timingWindows = parse_timing_windows(root)
            )
    return upload


def main():
    logging.basicConfig(level=logging.DEBUG)
    log.debug('Hello')

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
