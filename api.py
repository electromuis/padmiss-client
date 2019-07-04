#!/usr/bin/env python

import requests
import json
from graphqlclient import GraphQLClient

class Base(object):
    __repr_suppress__ = set()


    def __init__(self, **kwargs):
        for k, c in self.__fields__.items():
            if not k in kwargs:
                if c == None:
                    raise TournamentApiError('Required parameter \'%s\' missing' % k)
                else:
                    val = c
            else:
                    val = kwargs[k]
            if c and isinstance(val, dict):
                val = c(**val)
            setattr(self, k, val)


    def __repr__(self):
        return '(%s %s)' % (
                type(self).__name__ ,
                ' '.join('%s=%s' % (k, repr(v)) for k, v in self.__dict__.items() if not k in self.__repr_suppress__)
                )


class FlattenedBase(Base):
    pass


class Player(FlattenedBase):
    __fields__ = {
        'nickname' : None,
        'shortNickname' : '',
        'rfidUid': '',
        '_id'      : None,
	    'metaData' : "{}",
        'mountType': False
    }

    def getMeta(self, field):
        if self.metaData == None:
            return None

        data = json.loads(self.metaData)
        if field in data:
            return data[field]

        return None


class ScoreBreakdown(FlattenedBase):
    __fields__ = {
        'fantastics'   : None,
        'excellents'   : None,
        'greats'       : None,
        'decents'      : None,
        'wayoffs'      : None,
        'misses'       : None,
        'holds'        : None,
        'holdsTotal'   : None,
        'minesHit'     : None,
        'minesAvoided' : None,
        'minesTotal'   : None,
        'rolls'        : None,
        'rollsTotal'   : None,
        'jumps'        : None,
        'jumpsTotal'   : None,
        'hands'        : None,
        'handsTotal'   : None
    }


class Score(FlattenedBase):
    __fields__ = {
        'scoreBreakdown' : ScoreBreakdown,
        'scoreValue'     : None,
        'passed'         : None
    }


class Song(FlattenedBase):
    __fields__ = {
        'title'                   : None,
        'titleTransliteration'    : None,
        'subTitle'                : None,
        'subTitleTransliteration' : None,
        'artist'                  : None,
        'artistTransliteration'   : None,
        'durationSeconds'         : None
    }


class TimingWindows(Base):
    __fields__ = {
        'fantasticTimingWindow' : None,
        'excellentTimingWindow' : None,
        'greatTimingWindow'     : None,
        'decentTimingWindow'    : None,
        'wayoffTimingWindow'    : None,
        'mineTimingWindow'      : None,
        'holdTimingWindow'      : None,
        'rollTimingWindow'      : None
    }


class ChartUpload(Base):
    __repr_suppress__ = set(('stepData',))


    __fields__ = {
        'hash'          : None,
        'meter'         : None,
        'playMode'      : None,
        'stepData'      : None,
        'stepArtist'    : None,
        'song'          : Song,
        'score'         : Score,
        'cabSide'       : None,
        'speedMod'      : None,
        'musicRate'     : None,
        'modsTurn'      : None,
        'modsTransform' : None,
        'modsOther'     : None,
        'noteSkin'      : None,
        'perspective'   : None,
        'timingWindows' : TimingWindows
    }


class TournamentApiError(Exception):
    pass


class TournamentApi(object):
    def __init__(self, url, key):
        self.url = url
        self.key = key
        self.graph = GraphQLClient(url + '/graphiql')


    def get_player(self, playerId=None, rfidUid=None, nickname=None):
        # r = requests.get(self.url + '/api/players', params={ '_id' : playerId, 'rfidUid' : rfidUid, 'nickname' : nickname })
        # matches = r.json()

        filter = {}
        if playerId:
            filter['_id'] = playerId
        if rfidUid:
            filter['rfidUid'] = rfidUid
        if nickname:
            filter['nickname'] = nickname

        result = self.graph.execute('''
        {
          Players (queryString: ''' + json.dumps(json.dumps(filter)) + ''') {
            docs {
              _id
              nickname
              shortNickname
              avatarIconUrl
              playerLevel
              playerExperiencePoints
              globalLadderRank
              globalLadderRating
              accuracy
              stamina
              totalSteps
              totalPlayTimeSeconds
              totalSongsPlayed
              metaData
            }
          }
        }
        ''')
        matches = json.loads(result)['data']['Players']['docs']

        if len(matches) != 1:
            return None

        return Player(**matches[0])


    def get_player_highscores(self, playerId):
        r = requests.get(self.url + '/api/players/%s/highscores' % playerId)
        j = r.json()
        if j['success'] != True:
            raise TournamentApiError(j['message'])
        return tuple((Score(**score) for score in j['highScores']))

    def get_last_sore(self, playerId):
        return None

        filter = {"player": playerId}

        result = self.graph.execute('''
        {
          Scores (sort: "-playedAt", limit: 1, queryString: ''' + json.dumps(json.dumps(filter)) + ''') {
            docs {
              stepChart {
                song {
                  title
                  artist
                }
              }
              isRecalced
              originalScore
              stepsInfo
              modTurn
              modMines
              modAttacks
              playedAt
            }
          }
        }
        ''')
        print(('''
        {
          Scores (sort: "-playedAt", limit: 1, queryString: ''' + json.dumps(json.dumps(filter)) + ''') {
            docs {
              stepChart {
                song {
                  title
                  artist
                }
              }
              isRecalced
              originalScore
              stepsInfo
              modTurn
              modMines
              modAttacks
              playedAt
            }
          }
        }
        '''))
        scores = json.loads(result)['data']['Scores']['docs']

        if len(scores) != 1:
            return None
        return scores[0]

    def post_score(self, player, upload):
        data = {
            'apiKey' : self.key,
            'playerId': player._id,
            'scoreValue' : upload.score.scoreValue,
            'passed' : upload.score.passed,
        }
        data.update(upload.score.scoreBreakdown.__dict__)
        data.update(upload.song.__dict__)
        data.update({ k: v for k, v in upload.__dict__.items() if not isinstance(v, FlattenedBase)  })
        dumpable = lambda v: v.__dict__ if isinstance(v, Base) else v
        r = requests.post(self.url + '/post-score', json={ k: dumpable(v) for k, v in data.items() if v is not None })
        j = r.json()
        if j['success'] != True:
            raise TournamentApiError(j['message'])


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    api = TournamentApi('http://localhost:3020', 've324mkvvk4k')
    p = api.get_player(nickname='hippaheikki')
    p = api.get_player(rfidUid='0014357364')
    print(p)
    if p:
        print(api.get_player_highscores(p._id))
    breakdown = ScoreBreakdown(
        fantastics = 10,
        excellents = 9,
        greats     = 8,
        decents    = 7,
        wayoffs    = 6,
        misses     = 5,
        holds      = 4,
        holdsTotal = 6,
        minesHit   = 0,
        rolls      = 3,
        rollsTotal = 6
    )
    score = Score(scoreBreakdown=breakdown, scoreValue=99.9, passed=False)
    song = Song(
        title                   = 'kukkuu',
        titleTransliteration    = None,
        subTitle                = 'subi',
        subTitleTransliteration = None,
        artist                  = 'artisti maksaa',
        artistTransliteration   = None,
        durationSeconds         = 123,
    )
    chart = ChartUpload(
        hash            = 12345,
        meter           = 12,
        playMode        = 'Single',
        stepData        = '0010',
        stepArtist      = 'steppaaja',
        song            = song,
        score           = score,
        cabSide         = 'Left'
    )
    api.post_score(p, chart)
