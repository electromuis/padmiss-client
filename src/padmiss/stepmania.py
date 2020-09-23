import configparser
import os
from os import path

def findBinary(path):
    binary = path.join(path, 'stepmania')
    if path.exists(binary):
        return binary

    binary = path.join(path, 'Program', 'StepMania.exe')
    if path.exists(binary):
        return binary

    return False

def findPreferences(path):
    pref = path.join(path, 'Save', 'Preferences.ini')
    if path.exists(pref):
        return pref

    if path.exists(path.join(path, 'Portable.ini')):
        return False

    if os.name == 'nt':
        pref = os.path.join(os.getenv('APPDATA'), 'StepMania 5', 'Save', 'Preferences.ini')
        if path.exists(pref):
            return pref

        pref = os.path.join(os.getenv('APPDATA'), 'StepMania 5.1', 'Save', 'Preferences.ini')
        if path.exists(pref):
            return pref
    else:
        pref = os.path.join(os.path.expanduser('~'), '.stepmania5', 'Save', 'Preferences.ini')
        if path.exists(pref):
            return pref

        pref = os.path.join(os.path.expanduser('~'), '.stepmania5.1', 'Save', 'Preferences.ini')
        if path.exists(pref):
            return pref

    return False

def findReaders():
    return False

def checkOptions(options, useReaders):
    wrongOptions = []
    check = {
        'MemoryCardPadmissEnabled'
    }

def autoConfig():
    currentPath = os.path.dirname(os.path.realpath(__file__))
    binary = findBinary(currentPath)

    if binary == False:
        currentPath = path.join(currentPath, '..')
        binary = findBinary(currentPath)
        if binary == False:
            print("I don't think this is a stepmania folder")
            return False

    preferences = findPreferences(currentPath)
    if preferences == False:
        print("Couldn't find Preferences.ini, did you run the game at lease once?")
        return False

    iniConfig = configparser.ConfigParser()
    iniConfig.optionxform = lambda option: option
    iniConfig.read(preferences)

    if 'Options' not in iniConfig:
        print('Invalid Preferences detected')
        return False

    if 'MemoryCardPadmissEnabled' not in iniConfig['Options']:
        print("Your'e trying to use a stepmania build without padmiss support")
        return False

    wrongOptions = checkOptions(iniConfig['Options'])


class Stepmania:
    preferences = None
    padmiss = None
    loaded = False

    def __init__(self, folder):
        if folder == None:
            return

        self.folder = folder
        self.saveFolder = folder

        if not path.exists(path.join(folder, 'Portable.ini')):
            if os.name == 'nt':
                self.saveFolder = os.path.join(os.getenv('APPDATA'), 'Padmiss')
            else:
                self.saveFolder = os.path.join(os.path.expanduser('~'), '.padmiss')


        self.loaded = self.detectFolders()

    def detectFolders(self):
        all = True

        if not path.exists(self.folder) or not path.exists(self.saveFolder):
            return False

        preferences = path.join(self.saveFolder, 'Save', 'Preferences.ini')
        if path.exists(preferences):
            self.preferences = preferences
            all = False

        padmiss = path.join(self.saveFolder, 'Save', 'Padmiss')
        if not path.exists(padmiss):
            if not os.mkdir(padmiss):
                all = False
        self.padmiss = padmiss

        return all

    def updateConfig(self, data):
        if self.preferences == None:
            return False

        iniConfig = configparser.ConfigParser()
        iniConfig.optionxform = lambda option: option

        iniConfig.read(self.preferences)
        iniConfig['Options']['MemoryCardProfiles'] = '1'
        iniConfig['Options']['MemoryCardPadmissEnabled'] = '1'
        iniConfig['Options']['MemoryCards'] = '1'
        iniConfig['Options']['MemoryCardDriver'] = 'Directory'
        iniConfig['Options']['MemoryCardProfileSubdir'] = myConfig.profile_dir_name

        c = 1
        for i, dev in enumerate(myConfig.devices):
            iniConfig['Options']['MemoryCardUsbBusP' + str(c)] = '-1'
            iniConfig['Options']['MemoryCardUsbBusP' + str(c)] = '-1'
            iniConfig['Options']['MemoryCardUsbPortP' + str(c)] = '-1'
            iniConfig['Options']['MemoryCardOsMountPointP' + str(c)] = dev.path
            c = c + 1

        with open(file, 'w') as configfile:
            iniConfig.write(configfile, space_around_delimiters=False)