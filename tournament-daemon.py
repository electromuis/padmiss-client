#!/usr/bin/env python

import config

from threading import Thread

from flask import Flask
from flask_restful import Resource, Api, reqparse

from api import TournamentApi
from hid import RFIDReader


class CurrentPlayers(Resource):
    def get(self):
        return current_players


class ScoreUpload(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('hash', required=True)
    parser.add_argument('meter', required=True)
    parser.add_argument('title', required=True)
    parser.add_argument('subtitle', required=True)
    parser.add_argument('artist', required=True)
    parser.add_argument('player', required=True)
    parser.add_argument('stepartist', required=True)
    parser.add_argument('stepstype', required=True)
    parser.add_argument('stepsdata', required=True)
    parser.add_argument('duration', required=True)

    def post(self):
        args = ScoreUpload.parser.parse_args(strict=True)
        print args


def poller(side, reader):
    while True:
        data = reader.poll()

        if data:
            data = data.strip()
            p = api.get_player(data)
            if p:
                current_players[side] = p['nickname']
            else:
                current_players[side] = None


current_players = {}
api = TournamentApi(config.url)

app = Flask(__name__)
rest = Api(app)

rest.add_resource(CurrentPlayers, '/currentplayers')
rest.add_resource(ScoreUpload, '/scoreupload')

for side, lookup in config.readers.iteritems():
    current_players[side] = None
    reader = RFIDReader(**lookup)
    thread = Thread(target=poller, args=(side, reader))
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    app.run()
