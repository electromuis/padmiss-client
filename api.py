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

    def post_score(self, player):
        try:
            data = { 'apiKey' : self.key, 'player': player }
            r = requests.post(self.url + '/post-score', data=data)
            json = r.json()
            print json
            return json['success']
        except:
            return False


if __name__ == '__main__':
    api = TournamentApi('http://localhost:3020', 've324mkvvk4k')
    p = api.get_player('0010546583')
    print p
    api.post_score('foo')
