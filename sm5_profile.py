#!/usr/bin/env python

from os import path, makedirs
from xml.etree.ElementTree import Element, SubElement, tostring, parse

import config
from api import TournamentApi, ScoreBreakdown, Score, Song, ChartUpload, TimingWindows
api = TournamentApi(config.url, config.apikey)

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
    file = '[Simply Love]\n=Nothing\nBackgroundFilter=Off\nColumnFlashOnMiss=false\nHideComboActionOnMissedTarget=false\nHideDanger=true\nHideLifebar=false\nHideScore=false\nHideSongBG=false\nHideTargets=false\nJudgmentGraphic=Love\nLifeMeterType=Standard\nMeasureCounter=None\nMeasureCounterPosition=Left\nReceptorArrowsPosition=StomperZ\nSubtractiveScoring=false\nTargetBar=11\nTargetScore=false\nTargetStatus=Disabled\nVocalization=None\n'
    if score != None:
        if score['speedMod']['type'] == 'MaxBPM':
            file += 'SpeedMod=' + str(score['speedMod']['value']) + '\n'
            file += 'SpeedModType=M\n'
        if score['speedMod']['type'] == 'Multiplier':
            file += 'SpeedMod=' + str(score['speedMod']['value']) + '\n'
            file += 'SpeedModType=X\n'
        if score['noteSkin']:
            file += 'NoteSkin=' + score['noteSkin'] + '\n'
        for mod in score['modsOther']:
            if mod['name'] == 'EFFECT_MINI':
                file += 'Mini=' + str(int(mod['value'] * 100)) + '%\n'

    return file

def generate_profile(dirname, player_name, player_guid):
	makedirs(dirname)

        score = api.get_last_sore(player_guid)

	with open(path.join(dirname, 'Stats.xml'), 'w') as statsxml:
		statsxml.write(tostring(generate_statsxml(player_name, player_guid, score)))

	with open(path.join(dirname, 'Editable.ini'), 'w') as editableini:
		editableini.write(generate_editableini(player_name))

        with open(path.join(dirname, 'Simply Love UserPrefs.ini'), 'w') as slini:
                slini.write(generate_sl_ini(score))


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
