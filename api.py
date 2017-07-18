#!/usr/bin/env python

import requests


class TournamentApi(object):
    def __init__(self, url):
        self.url = url

    def get_player(self, rfidUid):
        r = requests.get(self.url + '/players', params={ 'rfidUid' : rfidUid })
        matches = r.json()

        if len(matches) != 1:
            return None

        return matches[0]


if __name__ == '__main__':
    api = TournamentApi('http://localhost:3020/api')
    p = api.get_player('0010546583')
    print p.nickname
