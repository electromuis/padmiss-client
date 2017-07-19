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
    parser.add_argument('percent', required=True)
    parser.add_argument('side', required=True)
    parser.add_argument('judgements', required=True)

    def post(self):
        args = ScoreUpload.parser.parse_args(strict=True)
        for k, v in args.iteritems():
            print k, '->', v

        return '', 500


def poller(side, reader):
    while True:
        data = reader.poll()

        if data:
            data = data.strip()
            current_players[side] = None
            try:
                p = api.get_player(data)
                if p:
                    current_players[side] = p['nickname']
            except Exception as e:
                print e


current_players = {}
api = TournamentApi(config.url, config.apikey)

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
