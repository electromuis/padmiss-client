#!/usr/bin/env python

import requests


class SongInfo(object):
    def __init__(self):
        pass


class TournamentApi(object):
    def __init__(self, url, key):
        self.url = url
        self.key = key

    def get_player(self, rfidUid):
        r = requests.get(self.url + '/api/players', params={ 'rfidUid' : rfidUid })
        matches = r.json()

        if len(matches) != 1:
            return None

        return matches[0]

    def post_score(self, player, songinfo, score, details):
        data = { 'apiKey' : self.key, 'player': player, 'scoreValue' : score }
        data.update(songinfo)
        data.update(details)
        r = requests.post(self.url + '/post-score', data=data)
        json = r.json()
        print json
        return json['success']


if __name__ == '__main__':
    api = TournamentApi('http://localhost:3020', 've324mkvvk4k')
    p = api.get_player('0010546583')
    print p
    score = {
        'fantastics' : 10,
        'excellents' : 9,
        'greats'     : 8,
        'decents'    : 7,
        'wayoffs'    : 6,
        'misses'     : 5,
        'holds'      : 4,
        'holdsTotal' : 6,
        'minesHit'   : 0,
        'rolls'      : 3,
        'rollsTotal' : 6
    }
    song = {
        'title' : 'kukkuu',
        'subTitle' : 'subi',
        'artist' : 'artisti maksaa',
        'stepArtist' : 'steppaaja',
        'hash' : 12345,
        'meter' : 12,
        'playMode' : 'Single',
        'stepData' : '0010',
        'durationSeconds' : 123,
        'cabSide' : 'Left'
    }
    api.post_score('renbrandt', song, 99.99, score)
