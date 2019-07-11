#Instructions:

#Windows:
 - Install a supported Stepmania build, like our one (https://drive.google.com/open?id=1_VFzXZg-fO4fxmYPV-k0ZCIalmlXM2LX)
 - Download the latest release from github (https://github.com/electromuis/padmiss-daemon/releases)
 - Run the Padmiss.exe
 - It should open the config panel (If not delete %AppData%\Padmiss)

#Debian/Ubuntu:
 - Install at least python 3.6
 - Install the newest Stepmania, from our 5.1 branch (https://github.com/electromuis/stepmania/tree/5_1-new)
    - How to: https://github.com/stepmania/stepmania/wiki/Compiling-StepMania
 - Run the following commands:
```
~/ cd ~
~/ git clone https://github.com/electromuis/padmiss-daemon
~/ cd padmiss-daemon
~/padmiss-daemon sudo pip3 install -r requirements.txt
~/padmiss-daemon python3 gui.py
```
- It should open the config panel (If not delete ~/.padmiss)

#Both systems:
 - Go to https://app.itgec2019.com and register/login with your existing padmiss account
 - Go to cabs, and create a new one
 - Copy the API Key to the config panel
 - (For both scanners)
    - Click Add new scanner
    - Click pick a device, and follow the steps
 - Make sure you run the game at least once, otherwise there will be no Preferences.ini
 - Click FixSM5Config and select your Preferences.ini (https://github.com/stepmania/stepmania/wiki/Manually-Changing-Preferences)
 - Click Save and close
 - Start Stepmania 5.1
 - Donnnnnnnnnnn

#Notes:  

- Check in/out during eventmode
  - Make use of https://github.com/electromuis/Simply-Love-SM5. This branch has a fix to make that work. If you want to add that fix to your theme, check https://github.com/electromuis/Simply-Love-SM5/commit/fbc817c95850f4d85ea660f4493e032dbe6c6181
- What scanner should i use?
  - We used the cheapest solution we could find. Search on eBay or AliExpress for: 125khz rfid reader / cards. Should be less then 20 euro's for a pair of readers and some cards
- I don't have / want readers / want to use local profiles
  - Local profiles and Usb profiles are supported. Run the same installation procedure, except don't add scanners.
  - Register and login on https://app.itgec2019.com/, then in the profile tab copy the value after, Your padmiss GUID:
  - Open your Stats.xml (For usb profiles this should be in a StepMania 5 subfoler, for LocalProfiles this should be in the same directory as your Preferences.ini)
  - Find the current \<Guid>\</Guid> value, then find & replace that with your padmiss GUID
  - (Make sure stepmania is closed) Save, start stepmania, and thats it :) 