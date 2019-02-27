Instructions

All platforms:
 - After installing a supported stepmania version, edit your Preferences.ini (https://github.com/stepmania/stepmania/wiki/Manually-Changing-Preferences)
```
MemoryCardPadmissEnabled=1
```


Windows:
 - Install stepmania version with padmiss support (https://drive.google.com/open?id=1_VFzXZg-fO4fxmYPV-k0ZCIalmlXM2LX)
 - Install python 2.7 32x (https://www.python.org/ftp/python/2.7.15/python-2.7.15.msi)
 - Download latest daemon code (https://github.com/electromuis/padmiss-daemon/archive/master.zip)
 - Edit config.json, change [[StepmaniaDir]] to your stepmania installation dir
 - Run win-dependencies.bat
 - Configure scanners if needed (see header Scanners windows)
 - To start, run win-run.bat

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