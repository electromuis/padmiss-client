import logging
import os
import subprocess
import sys
import threading
import urllib.request, urllib.error, urllib.parse
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from collections import namedtuple
from os import path, makedirs, remove, unlink, system, makedirs
from shutil import rmtree
from threading import Thread
from time import sleep
from scandrivers.hid import RFIDReader
from util import construct_reader

if os.name != 'nt':
	from os import symlink

from api import TournamentApi, Player
from sm5_profile import generate_profile
from thread_utils import CancellableThrowingThread

log = logging.getLogger(__name__)

class Poller(CancellableThrowingThread):
	def __init__(self, config, profilePath, readers):
		super().__init__()
		self.setName('Poller')
		self.api = TournamentApi(config)
		self.config = config
		self.profilePath = profilePath
		self.readers = {}
		self.drivers = []
		self.reader = False

		for r in readers:
			self.readers[r.type] = construct_reader(r, self)
			self.drivers.append(self.readers[r.type])
			if r.type == 'scanner':
				self.reader = self.readers[r.type]

		self.mounted = None

	def checkIn(self, player):
		if self.mounted:
			if not self.mounted.driver.checkOut(player):
				return False

		self.mounted = player
		return True

	def checkOut(self):
		if self.mounted and not self.mounted.driver.checkOut():
			return False

		self.mounted = None
		return True

	def exc_run_new(self):
		for d in self.drivers:
			d.update()

	def exc_run(self):
		log.info("Starting Poller")

		# self.processUser(False, 'usb')
		self.processUser(None, 'card')

		"""if 'hwPath' in self.myConfig:
			self.myConfig['devPath'] = '/dev/disk/by-path/' + self.myConfig['hwPath']
			self.pollHw() """

		if self.reader:
			self.pollCard()

	def downloadPacks(self, folder, player):
		log.debug(folder)
		packs = player.getMeta("songs")
		if isinstance(packs, list):
			i = 1
			for p in packs:
				try:
					i = i + 1
					log.debug(p)
					u = urllib.request.urlopen(p)
					if int(u.getheader("Content-Length")) > 1024 * 1024 * 10:
						log.debug('Toobig')
						continue
					file_name = p.split('/')[-1]
					ext = path.splitext(file_name)[1]
					if ext != '.zip':
						log.debug('Nozip: ' + str(ext))
						continue
					spath = folder + "/" + self.config.profile_dir_name + "/Songs"
					filename = spath + "/custom" + str(i)
					if not path.exists(spath):
						makedirs(spath)
					with open(filename, "wb") as f:
						f.write(u.read())
					with zipfile.ZipFile(filename) as zf:
						zf.extractall(spath)
				except Exception as e:
					print(('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e))

	def processUser(self, newUser, type):
		if newUser:
			log.debug('Processing profile for ' + type)
		else:
			log.debug('Cleaning profile for ' + type)
		
		if path.islink(self.profilePath):
			unlink(self.profilePath)
		elif path.isdir(self.profilePath):
			rmtree(self.profilePath) # dangerous

		if newUser and (self.mounted is None or self.mounted._id != newUser._id):
			log.debug('Mounting to SM5')

			if type == 'card' or type == 'service':
				makedirs(self.profilePath)
				profileSMPath = path.join(self.profilePath, self.config.profile_dir_name)
				generate_profile(self.api, profileSMPath, newUser)
			
				try:
					if len(newUser.avatarIconUrl) == 0:
						raise Exception("No avatar")
						
					u = urllib.request.urlopen(newUser.avatarIconUrl)

					if int(u.getheader("Content-Length")) > 1024 * 1024 * 2:
						raise Exception("Toobig")
						
					file_name = newUser.avatarIconUrl.split('/')[-1]
					ext = path.splitext(file_name)[1]
						
					if ext not in ['.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG'] != '.zip' :
						meta = u.getheader("Content-Type")
						if meta == 'image/png':
							ext = '.png'
						elif meta == 'image/jpeg':
							ext = '.jpg'
						else:
							raise Exception("No valid avatar")
						
					filename = path.join(self.profilePath, self.config.profile_dir_name, 'Avatar' + ext)
					with open(filename, "wb") as f:
						f.write(u.read())
						
					log.debug('Profile image loaded')

				except Exception as e:
					log.debug('Profile image: ' + str(e))
					pass
					
				self.downloadPacks(self.profilePath, newUser)

			#if type == 'usb':
			#	symlink(myConfig['usbPath'], self.profilePath)

		self.mounted = newUser

		"""def pollHw(self):
		myConfig = self.myConfig
		while not self.stop_event.wait(1):
			p = subprocess.Popen(["ls", "/dev/disk/by-path/"], stdout=subprocess.PIPE)
			out = p.stdout.read().split("\n")
			found = myConfig['hwPath'] in out
			hasMounted = path.exists(myConfig['usbPath'])
			if found == hasMounted:
				continue

			if not found:
				log.debug('Lost usb')
				if path.exists(myConfig['usbPath']):
					system('sync')
					system('sudo umount -f ' + myConfig['usbPath'])
					rmtree(myConfig['usbPath'])

				self.processUser(False, 'usb')
			else:
				log.debug('Found usb')

				if not path.exists(myConfig['usbPath']):
					makedirs(myConfig['usbPath'])
					log.debug('mount ' + myConfig['usbPath'])
					system('mount ' + myConfig['usbPath'])

				stats = myConfig['usbPath'] + '/Stats.xml'
				p = False
				if path.exists(stats):
					tree = ET.parse(stats)
					root = tree.getroot()
					guid = root.find('Guid').text

					p = self.api.get_player(playerId=guid)

				if not p:
					p = Player(nickname='none', _id='none')

				p.mountType = 'usb'
				self.processUser(p, 'usb') """

	def pollCard(self):
		while not self.stop_event.wait(1):
			try:
				data = self.reader.poll()
				if data:
					data = data.strip()

					if data:
						if self.mounted and self.mounted.mountType == 'card' and self.mounted.rfidUid == data:
							log.debug('Eject player %s', data)
							self.processUser(None, 'card')
							continue

						p = self.api.get_player(rfidUid=data)

						if p:
							log.debug('Mount player %s', data)
							p.mountType = 'card'
							p.rfidUid = data
							self.processUser(p, 'card')
						else:
							log.debug('Player not found for: ' + data)

			except Exception:
				log.exception('Error getting player info from server')

		self.reader.release()