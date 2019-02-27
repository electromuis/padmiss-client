#!/usr/bin/env python

from os import path, makedirs
from xml.etree.ElementTree import Element, SubElement, tostring, parse

import config
from api import TournamentApi, ScoreBreakdown, Score, Song, ChartUpload, TimingWindows
api = TournamentApi(config.url, config.apikey)

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
		for k,v in self.__fields__.iteritems():
			ret += k + ' ' + str(v) + "\n"
		return ret
	
	def from_score(self, score):
		if score['speedMod']['type'] == 'MaxBPM':
			self.__fields__['SpeedModType'] = 'M'
		if score['speedMod']['type'] == 'Multiplier':
			self.__fields__['SpeedModType'] = 'X'
		if score['speedMod']['type'] == 'ConstantBPM':
			self.__fields__['SpeedModType'] = 'C'

		speed = float(score['speedMod']['value'])
		if speed > 0:
			if self.__fields__['SpeedModType'] == 'C':
				speed = int(speed * 100) / 100
			else:
				speed = int(speed)
			self.__fields__['SpeedMod'] = str(speed)

		if score['noteSkin']:
			self.__fields__['NoteSkin'] = score['noteSkin']

		for mod in score['modsOther']:
			if mod['name'] == 'EFFECT_MINI':
				value = int(mod['value'] * 100)
				self.__fields__['Mini'] = str(value) + '%'
		

def generate_statsxml(player_name, player_guid, score):
	stats = Element('Stats')
	general = SubElement(stats, 'GeneralData')
	SubElement(general, 'DisplayName').text = player_name
	SubElement(general, 'Guid').text = player_guid
	if score != None:
		modifiers = SubElement(general, 'DefaultModifiers')
		mods = []
		if score['speedMod']['type'] == 'MaxBPM':
			mods.append('m' + str(score['speedMod']['value']))
		if score['speedMod']['type'] == 'Multiplier':
			mods.append(str(score['speedMod']['value']) + 'x')
		mods.append('Overhead')
		if score['noteSkin']:
			mods.append(score['noteSkin'])
		SubElement(modifiers, 'dance').text = ', '.join(mods)

	return stats


def generate_editableini(player_name):
	ini_template = \
'''
[Editable]
DisplayName={displayname}
'''[1:]
	return ini_template.format(displayname=player_name)

def generate_sl_ini(score):
	if score == None:
		return None
	ini = SLIni()
	ini.from_score(score)

	return ini.write_string()

def generate_profile(dirname, player_name, player_guid):
	makedirs(dirname)

	score = api.get_last_sore(player_guid)

	with open(path.join(dirname, 'Stats.xml'), 'w') as statsxml:
		statsxml.write(tostring(generate_statsxml(player_name, player_guid, score)))

	with open(path.join(dirname, 'Editable.ini'), 'w') as editableini:
		editableini.write(generate_editableini(player_name))

	ini = generate_sl_ini(score)
	if ini != None:
		with open(path.join(dirname, 'Simply Love UserPrefs.ini'), 'w') as slini:
			slini.write(ini)


def parse_profile_scores(dirname):
	tree = parse(path.join(dirname, 'Stats.xml'))
	root = tree.getroot()
	for song in root.findall('./SongScores/Song'):
		print song.attrib['Dir']
		for steps in song.findall('./Steps'):
			print steps.attrib['Difficulty'], steps.attrib['StepsType']
			for score in steps.findall('./HighScoreList/HighScore'):
				print 'score'
				print score.find('PercentDP').text
				tns = score.find('TapNoteScores')
				print tns.find('HitMine').text


if __name__ == '__main__':
#	print tostring(generate_statsxml('Testaaja', '123456789abcdefgh'))
#	print generate_editableini('Testaaja')
	generate_profile('/tmp/p1/StepMania 5', 'Testaaja', '5ad12d9f07b73e108861bf9b')
#	parse_profile_scores('/tmp/p1/StepMania 5')