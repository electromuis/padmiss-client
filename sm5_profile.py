#!/usr/bin/env python

import binascii
from os import path, makedirs
from xml.etree.ElementTree import Element, SubElement, tostring, parse
from api import TournamentApi
from config import PadmissConfigManager

from api import ScoreBreakdown, Score, Song, ChartUpload, TimingWindows


class SLIni():
	__fields__ = {
		'JudgmentGraphic': "Love",
		'Mini': "0%",
		'BackgroundFilter': "Off",
		'SpeedModType': "x",
		'SpeedMod': "1.00",
		'Vocalization': "None",
		'NoteSkin': "",
		'HideTargets': "false",
		'HideSongBG': "false",
		'HideCombo': "false",
		'HideLifebar': "false",
		'HideScore': "false",
		'HideDanger': "true",
		'ColumnFlashOnMiss': "false",
		'SubtractiveScoring': "false",
		'MeasureCounterPosition': "Left",
		'MeasureCounter': "None",
		'TargetStatus': "Disabled",
		'TargetBar': 11,
		'TargetScore': "false",
		'ReceptorArrowsPosition': "StomperZ",
		'LifeMeterType': "Standard",
	}

	def write_string(self):
		ret = "[Simply Love]\n"
		for k,v in self.__fields__.items():
			ret += k + '=' + str(v) + "\n"
		return ret
	
	def from_score(self, score):
		if score['speedMod']:
			if score['speedMod']['type'] == 'MaxBPM':
				self.__fields__['SpeedModType'] = 'M'
			if score['speedMod']['type'] == 'Multiplier':
				self.__fields__['SpeedModType'] = 'X'
			if score['speedMod']['type'] == 'ConstantBPM':
				self.__fields__['SpeedModType'] = 'C'

			speed = float(score['speedMod']['value'])
			if speed > 0:
				if self.__fields__['SpeedModType'] == 'X':
					speed = int(speed * 100) / 100
				else:
					speed = int(speed)
				self.__fields__['SpeedMod'] = str(speed)

		if score['noteSkin']:
			self.__fields__['NoteSkin'] = score['noteSkin']

		for mod in score['modsOther']:
			if mod['name'] == 'EFFECT_MINI':
				value = int(float(mod['value']) * 100)
				self.__fields__['Mini'] = str(value) + '%'

		for mod in score['modsOther']:
			if mod['name'][0:3] == 'SL:':
				self.__fields__[mod['name'][3:]] = mod['value']

def generate_statsxml(player, score):
	stats = Element('Stats')
	general = SubElement(stats, 'GeneralData')
	SubElement(general, 'DisplayName').text = player.nickname
	SubElement(general, 'Guid').text = player._id
	if score != None:
		modifiers = SubElement(general, 'DefaultModifiers')
		mods = []
		if score['speedMod']:
			if score['speedMod']['type'] == 'MaxBPM':
				mods.append('m' + str(score['speedMod']['value']))
			if score['speedMod']['type'] == 'Multiplier':
				mods.append(str(score['speedMod']['value']) + 'x')
		mods.append('Overhead')
		if score['noteSkin']:
			mods.append(score['noteSkin'])
		SubElement(modifiers, 'dance').text = ', '.join(mods)

	return stats


def generate_editableini(player):
	ini_template = \
'''
[Editable]
DisplayName={displayname}
LastUsedHighScoreName={shortname}
'''[1:]
	return ini_template.format(displayname=player.nickname, shortname=player.shortNickname)

def generate_sl_ini(score):
	if score == None:
		return None
	ini = SLIni()
	ini.from_score(score)

	return ini.write_string()

def generate_profile(api, dirname, player):
	makedirs(dirname)

	score = api.get_last_sore(player._id)

	with open(path.join(dirname, 'Stats.xml'), 'w') as statsxml:
		statsxml.write(tostring(generate_statsxml(player, score), encoding="unicode"))

	with open(path.join(dirname, 'Editable.ini'), 'w') as editableini:
		editableini.write(generate_editableini(player))

	with open(path.join(dirname, 'card0.txt'), 'w') as card:
		hex_player_id = binascii.hexlify(player._id.encode()).decode()
		card.write('E004' + hex_player_id.zfill(12)[0:12])

	ini = generate_sl_ini(score)
	if ini != None and score != None:
		with open(path.join(dirname, 'Simply Love UserPrefs.ini'), 'w') as slini:
			slini.write(ini)


def parse_profile_scores(dirname):
	tree = parse(path.join(dirname, 'Stats.xml'))
	root = tree.getroot()
	for song in root.findall('./SongScores/Song'):
		print(song.attrib['Dir'])
		for steps in song.findall('./Steps'):
			print(steps.attrib['Difficulty'], steps.attrib['StepsType'])
			for score in steps.findall('./HighScoreList/HighScore'):
				print('score')
				print(score.find('PercentDP').text)
				tns = score.find('TapNoteScores')
				print(tns.find('HitMine').text)


if __name__ == '__main__':
	config = PadmissConfigManager().load_config()
	api = TournamentApi(config)
	score = api.get_last_sore('5ad12d9f07b73e108861bf9b')

	ini = generate_sl_ini(score)
	print(ini)
