
#!/usr/bin/env python

import os
import shutil
import logging
import tempfile
import threading
import configparser
import json

from os import path
from time import sleep
from xml.etree import ElementTree
import urllib.request, urllib.error, urllib.parse

from padmiss.stepmania import Stepmania
from .api import TournamentApi, ScoreBreakdown, Score, Song, ChartUpload, TimingWindows, InputEvent, NoteScore
from .thread_utils import CancellableThrowingThread

def text_by_xpath(parent, xpath):
    e = parent.find(xpath)

    if e != None:
        return e.text
    else:
        return ''

def bool_by_xpath(parent, xpath):
    e = parent.find(xpath)

    if e != None:
        return bool(e.text == '1')
    else:
        return None

def text_by_attr(parent, attr):
    if attr in parent.attrib:
        return parent.attrib[attr]
    else:
        return ''

def bool_by_attr(parent, attr):
    if attr in parent.attrib:
        return bool(parent.attrib[attr] == '1')
    else:
        return None

log = logging.getLogger(__name__)

def xpath_items(root, items, mapper):
    return { typ: mapper(text_by_xpath(root, path)) for typ, path in items.items() }


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
    log.debug(bool_by_xpath(root, 'Passed'))
    score = Score(
            scoreBreakdown=breakdown,
            scoreValue=float(text_by_xpath(root, 'ScoreValue')),
            passed=bool_by_xpath(root, 'Passed'),
            secondsSurvived=float(text_by_xpath(root, 'SecondsSurvived'))
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

def parse_input_events(root):
    return list(map(lambda e: InputEvent(
        beat      = float(text_by_attr(e, 'Beat')),
        column    = int(text_by_attr(e, 'Col')),
        released  = bool_by_attr(e, 'Released')
    ), root.findall('InputEvents/InputEvent')))

def parse_note_scores(root):
    return list(map(lambda e: NoteScore(
        beat=float(text_by_attr(e, 'Beat')),
        column=int(text_by_attr(e, 'Col')),
        holdNoteScore=text_by_attr(e, 'HoldNoteScore'),
        tapNoteScore=text_by_attr(e, 'TapNoteScore'),
        offset=float(text_by_attr(e, 'Offset'))
    ), root.findall('NoteScoresWithBeatPosition/NoteScore')))

conv_toggle_mod = lambda mod: mod.tag
conv_float_mod = lambda mod: dict(name=mod.tag, value=float(mod.text))


def parse_upload(root):
    print(text_by_xpath(root, 'PlayerName'))

    upload = ChartUpload(
            hash                    = text_by_xpath(root, 'Steps/Hash'),
            meter                   = int(text_by_xpath(root, 'Steps/Meter')),
            playMode                = parse_playmode(root),
            stepData                = text_by_xpath(root, 'Steps/StepData'),
            stepArtist              = text_by_xpath(root, 'Steps/StepArtist'),
            song                    = parse_song(root),
            score                   = parse_score(root),
            group                   = text_by_xpath(root, 'Steps/Group'),
            cabSide                 = parse_cabside(root),
            speedMod                = parse_speedmod(root),
            musicRate               = float(text_by_xpath(root, 'Mods/MusicRate')),
            modsTurn                = parse_mods(root, ('Mods/Turns',), conv_toggle_mod),
            modsTransform           = parse_mods(root, ('Mods/Transforms',), conv_toggle_mod),
            modsOther               = parse_mods(root, ('Mods/Accels', 'Mods/Effects', 'Mods/Appearances', 'Mods/Scrolls'), conv_float_mod),
            noteSkin                = text_by_xpath(root, 'Mods/NoteSkin'),
            perspective             = parse_perspective(root),
            timingWindows           = parse_timing_windows(root),
            inputEvents             = parse_input_events(root),
            noteScoresWithBeats     = parse_note_scores(root)
            )

    return upload


class ScoreUploader(CancellableThrowingThread):
    def __init__(self, config, pollers):
        super().__init__()
        self._config = config
        self._pollers = pollers
        self.setName(__name__)

    def append_profile_data(self, poller, upload):
        iniFile = path.join(poller.profilePath, self._config.profile_dir_name, 'Simply Love UserPrefs.ini')
        if path.isfile(iniFile):
            iniConfig = configparser.ConfigParser(strict=False, interpolation=None)
            iniConfig.optionxform = lambda option: option
            iniConfig.read(iniFile)
            for k, v in iniConfig.items('Simply Love'):
                upload.modsOther.append(dict(name='SL:' + k, value=v))

    def handle_score(self, fn):
        try:
            root = ElementTree.parse(fn).getroot()
            upload = parse_upload(root)

            print(upload)

            total = upload.score.scoreBreakdown.fantastics + \
                    upload.score.scoreBreakdown.excellents + \
                    upload.score.scoreBreakdown.greats + \
                    upload.score.scoreBreakdown.decents + \
                    upload.score.scoreBreakdown.wayoffs

            if total == 0:
                log.debug('Skipping empty score: ' + fn)
            else:
                log.debug('Uploading score from: ' + fn)

                playerGuid = text_by_xpath(root, 'PlayerGuid')
                player = self._api.get_player(playerGuid)
                if player:
                    for p in self._pollers:
                        if p.mounted and p.mounted._id == player._id:
                            self.append_profile_data(p, upload)
                            break

                    log.debug('Uploading score for ' + player.nickname + ': ' + repr(upload))
                    self._api.post_score(player, upload)
                else:
                    log.warning('Player not found: ' + playerGuid)

        except:
            log.exception('Failed to upload score')
            if self._config.backup_dir:
                backupdir = self._config.backup_dir

                if not os.path.isdir(backupdir):
                    os.makedirs(backupdir)

                backup = tempfile.mkstemp(suffix='.xml', prefix='failed_', dir=backupdir)[1]
                shutil.copy(fn, backup)
                log.debug('Backed up failed score to ' + backup)

        os.remove(fn)

    def handle_json(self, fn):
        scores_dir = self._config.scores_dir

        try:
            log.debug('Handling json from ' + fn)
            f = open(fn, "r")
            request = json.load(f)
            f.close()

            if request['type'] == 'http':
                req = None
                headers = {}
                if 'headers' in request:
                    headers = request['headers']

                if request['method'] == 'POST' and 'payload' in request:
                    log.debug(request['payload'])
                    req = urllib.request.Request(request['url'], data=request['payload'].encode('utf-8'), headers=headers)
                else:
                    req = urllib.request.Request(request['url'], headers=headers)

                try:
                    u = urllib.request.urlopen(req)
                    response = u.read()
                except Exception as e:
                    log.exception('Failed handling SM json: ' + str(e))
                    response = ''.encode('utf-8')

                jsono = path.join(scores_dir, str(request['identifier']) + '.jsono')
                f = open(jsono, "wb")
                f.write(response)
                f.close()
            else:
                raise Exception('Unknown request type')
        except:
            log.exception('Failed to handle json')

        os.remove(fn)

    def exc_run(self):
        self._api = TournamentApi(self._config)

        if not self._config.scores_dir:
            log.warn('Scores directory is not set, not uploading scores')
            return
        else:
            log.debug('Reading score files from: ' + self._config.scores_dir)

        while not self.stop_event.wait(1):
            # stepmania = Stepmania(self._config.stepmania_dir)

            # if stepmania.loaded == True:
            if not path.exists(self._config.scores_dir):
                continue

            for n in os.listdir(self._config.scores_dir):
                fn = path.join(self._config.scores_dir, n)

                if n.endswith('.xml'):
                    self.handle_score(fn)

                if n.endswith('.jsoni'):
                    self.handle_json(fn)

