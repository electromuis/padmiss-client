Instructions:

Windows:
 - Install the newest Stepmaia 5 (Until 5.3 gets released, use this one https://drive.google.com/open?id=1_VFzXZg-fO4fxmYPV-k0ZCIalmlXM2LX)
 - Download the latest release from github (https://github.com/electromuis/padmiss-daemon/releases)
 - Run the Padmiss.exe
 - It should open the config panel (If not delete %AppData%\Padmiss)

Debian/Ubuntu:
 - Install the newest Stepmania, for now the 5.1 branch (https://github.com/stepmania/stepmania/tree/5_1-new)
    - How to: https://github.com/stepmania/stepmania/wiki/Compiling-StepMania
 - Run the following commands:
```
~/ cd ~
~/ sudo apt-get install git python3 pip3
~/ git clone https://github.com/electromuis/padmiss-daemon
~/ cd padmiss-daemon
~/padmiss-daemon sudo pip3 install -r requirements.txt
~/padmiss-daemon python3 gui.py
```
- It should open the config panel (If not delete ~/.padmiss)

Both systems:
 - Go to https://app.itgec2019.com and register/login with your existing padmiss account
 - Go to cabs, and create a new one
 - Copy the new token to the config panel
 - (For both scanners)
    - Click Add new scanner
    - Click pick a device, and follow the steps
 - Click FixSM5Config and select your Preferences.ini (https://github.com/stepmania/stepmania/wiki/Manually-Changing-Preferences)
 - Click Save and close
 - Start Stepmania 5.1
 - Donnnnnnnnnnn