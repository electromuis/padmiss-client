Instructions

All platforms:
 - After installing a supported stepmania version, edit your Preferences.ini (https://github.com/stepmania/stepmania/wiki/Manually-Changing-Preferences)
```
MemoryCardPadmissEnabled=1
```

Relevant config options:

MemoryCardPadmissEnabled=1
Writes a special score file after each play, for each player to the (Stepmania dir)/Save/Padmiss

MemoryCardOsMountPointP1/2=
The folder that stepmania watches for the memory card/player profile

MemoryCardDriver=Directory/USB
Defines how stepmania looks for memory cards, USB is the default behaviour and Directory tells stepmania to detect the profile when the folder defined in MemoryCardOsMountPointP exists.

MemoryCards=1
MemoryCardProfiles=1
Enables the use of profiles, without these only local profiles will function

MemoryCardUsbBusP1/2
MemoryCardUsbLevelP1/2
MemoryCardUsbPortP1/2
Options to filter memory cards in USB mode, for padmiss these all need to be -1!

Linux:
 - Install python 2.7
 - Download the newest code
 - Install dependancies
 - 

In terminal terms,
```
sudo apt-get install python2.7
git clone https://github.com/electromuis/padmiss-daemon
cd padmiss-daemon
sudo pip install -r requirements.txt
```

Scanners linux:
TODO

Autostart linux:
systemd TODO


Windows:
 - Install stepmania version with padmiss support (https://drive.google.com/open?id=1_VFzXZg-fO4fxmYPV-k0ZCIalmlXM2LX)
 - Install python 2.7 32x (https://www.python.org/ftp/python/2.7.15/python-2.7.15.msi)
 - Download latest daemon code (https://github.com/electromuis/padmiss-daemon/archive/master.zip)
 - Edit config.json, change [[StepmaniaDir]] to your stepmania installation dir
 - Run win-dependencies.bat
 - Configure scanners if needed (see header Scanners windows)
 - To start, run win-run.bat

Autostart padmiss windows:
You can use a lot of ways, this is one of them: https://www.sevenforums.com/tutorials/67503-task-create-run-program-startup-log.html
In the exampe "Core Temp.exe" is used. Just replace this with win-run.bat, and change the "Start in" to your padmiss-daemon folder

Scanners windows:
 - Download zadig driver tool (https://zadig.akeo.ie/)
 - Show all devices, under menu item Options
 - Replace drivers for your scanners to WinUSB (usb id will probably be 08ff 0009, otherwise take note!)
 - Create directory C:/padmiss
 - Edit config.json, change "scanners": [] to (You might need to change the port_number according to your setup)
```
"scanners": [
		{
			"path": "C:/padmiss/player1",
			"config": {
				"idVendor": "08ff",
				"idProduct": "0009",
				"port_number": 1
			}
		},
		{
			"path": "C:/padmiss/player2",
			"config": {
				"idVendor": "08ff",
				"idProduct": "0009",
				"port_number": 2
			}
		}
	]
```
 - Edit stepmania Preferences.ini (https://github.com/stepmania/stepmania/wiki/Manually-Changing-Preferences)
```
MemoryCardPadmissEnabled=1
MemoryCardOsMountPointP1=C:/padmiss/player1
MemoryCardOsMountPointP2=C:/padmiss/player2
MemoryCardDriver=Directory
MemoryCardProfiles=1
MemoryCardUsbBusP1=-1
MemoryCardUsbBusP2=-1
MemoryCardUsbLevelP1=-1
MemoryCardUsbLevelP2=-1
MemoryCardUsbPortP1=-1
MemoryCardUsbPortP2=-1
MemoryCards=1
```