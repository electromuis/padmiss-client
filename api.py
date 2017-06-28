#!/usr/bin/env python

import requests


class Player(object):
    def __init__(self, data):
        self.nickname = data['nickname']


class TournamentApi(object):
    def __init__(self, url):
        self.url = url

    def get_player(self, rfidUid):
        r = requests.get(self.url + '/players', params={ 'rfidUid' : rfidUid })
        matches = r.json()

        if len(matches) != 1:
            return None

        return Player(matches[0])


api = TournamentApi('http://dhcp-194:3020/api')
print api.get_player('0010546583')
