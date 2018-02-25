#!/usr/bin/env python

from os import path, makedirs
from xml.etree.ElementTree import Element, SubElement, tostring, parse


def generate_statsxml(player_name, player_guid):
	stats = Element('Stats')
	general = SubElement(stats, 'GeneralData')
	SubElement(general, 'DisplayName').text = player_name
	SubElement(general, 'Guid').text = player_guid
	
	return stats


def generate_editableini(player_name):
	ini_template = \
'''
[Editable]
DisplayName={displayname}
'''[1:]
	return ini_template.format(displayname=player_name)


def generate_profile(dirname, player_name, player_guid):
	makedirs(dirname)

	with open(path.join(dirname, 'Stats.xml'), 'w') as statsxml:
		statsxml.write(tostring(generate_statsxml(player_name, player_guid)))

	with open(path.join(dirname, 'Editable.ini'), 'w') as editableini:
		editableini.write(generate_editableini(player_name))


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
#	generate_profile('/tmp/p1/StepMania 5', 'Testaaja', '12765')
	parse_profile_scores('/tmp/p1/StepMania 5')
