import configparser
import logging
import time

from os import path
import usb
import getpass
import os
import subprocess
import win32com.client
import argparse
import sys

from padmiss.daemon import PadmissDaemon
from padmiss.thread_utils import start_and_wait_for_threads
from padmiss import stepmania
from padmiss.util import resource_path
from padmiss.config import PadmissConfig, DeviceConfig, PadmissConfigManager
from padmiss.scandrivers import hid
from padmiss.api import TournamentApi
from padmiss.sm5_profile import generate_profile

log = logging.getLogger(__name__)


class PadmissStarter():
    apiUrl = 'https://api.padmiss.com/'
    storedConfig = None
    saveDir = None
    args = None

    def __init__(self):
        self.api = TournamentApi(self.apiUrl)

        parser = argparse.ArgumentParser()
        parser.add_argument('--sm-dir', help='The root Stepmania folder to work from')
        parser.add_argument('--flip-readers', help='Swap P1 and P2 reader')
        parser.add_argument('--just-log', action='store_true', help='Disable interactive console')

        self.args = parser.parse_args()

    def confirm(self, question):
        return self.askQuestion(question, ['Y', 'n', '']).lower() != 'n'

    def askQuestion(self, question, options):
        answer = None

        while answer == None:
            result = input(question + ' [' + (' / '.join(filter(len, options))) + ']: ')
            if result in options:
                answer = result

        return answer

    def findBinary(self, searchPath):
        binary = path.join(searchPath, 'stepmania')
        if path.exists(binary) and path.isfile(binary):
            return binary

        binary = path.join(searchPath, 'Program', 'StepMania.exe')
        if path.exists(binary) and path.isfile(binary):
            return binary

        return False

    def findPreferences(self, rootPath):
        pref = path.join(rootPath, 'Save', 'Preferences.ini')
        if path.exists(pref):
            return pref

        if path.exists(path.join(rootPath, 'Portable.ini')):
            return False

        if os.name == 'nt':
            pref = path.join(os.getenv('APPDATA'), 'StepMania 5.1', 'Save', 'Preferences.ini')
            if path.exists(pref):
                return pref

            pref = path.join(os.getenv('APPDATA'), 'StepMania 5', 'Save', 'Preferences.ini')
            if path.exists(pref):
                return pref
        else:
            pref = path.join(os.path.expanduser('~'), '.stepmania5.1', 'Save', 'Preferences.ini')
            if path.exists(pref):
                return pref

            pref = path.join(os.path.expanduser('~'), '.stepmania5', 'Save', 'Preferences.ini')
            if path.exists(pref):
                return pref

        return False

    def checkWinDrivers(self):
        try:
            from winregistry import WinRegistry as Reg

            reg = Reg()
            path = r'HKLM\SYSTEM\\CurrentControlSet\\Enum\USB\\VID_08FF&PID_0009'

            hasDrivers = True
            for k in reg.read_key(path)['keys']:
                driver = reg.read_value(path + '\\' + k, 'Service')['data']
                if driver != 'libusbK':
                    hasDrivers = False
                    break

            if hasDrivers == False:
                if not self.confirm("I noticed your readers don't have the correct drivers, would you like to install?"):
                    return False
                else:
                    dir = resource_path('zadig') + '\\driver\\'

                    import ctypes, sys
                    import win32com.shell.shell as shell
                    import win32api, win32con, win32event, win32process
                    from win32com.shell import shellcon

                    tool = os.path.abspath(dir + 'InstallDriver.exe')
                    procInfo = shell.ShellExecuteEx(fMask=shellcon.SEE_MASK_NOCLOSEPROCESS, lpVerb='runas', lpFile=tool)
                    win32event.WaitForSingleObject(procInfo['hProcess'], win32event.INFINITE)
                    win32process.GetExitCodeProcess(procInfo['hProcess'])

                hasDrivers = True
                for k in reg.read_key(path)['keys']:
                    driver = reg.read_value(path + '\\' + k, 'Service')['data']
                    if driver != 'libusbK':
                        hasDrivers = False
                        break

                if hasDrivers == False:
                    print('Driver installation failed')
                    return False
                else:
                    print('Driver installed')

        except Exception as e:
            print(str(e))
            return False

        return True

    def checkReaders(self):
        # Search for most common supported scanners
        devices = list(usb.core.find(idVendor = 0x08FF, idProduct = 0x0009, find_all=True))
        numDevices = len(devices)

        for d in devices:
            usb.util.dispose_resources(d)

        if numDevices > 0:
            if((self.storedConfig and self.storedConfig.use_readers) or self.confirm('Would you like to use the connected readers?')):
                if os.name == 'nt':
                    if not self.checkWinDrivers():
                        return None

                return True
            else:
                return False

        return None

    def checkOptions(self, preferences, useReaders):
        iniConfig = configparser.ConfigParser()
        iniConfig.optionxform = lambda option: option
        iniConfig.read(preferences)

        if 'Options' not in iniConfig:
            print('Invalid Preferences detected')
            return False

        if 'MemoryCardDriver' not in iniConfig['Options']:
            print("You're trying to use a stepmania build without padmiss support")
            return False


        check = {
            'MemoryCardProfiles'        : '1',
            'MemoryCardPadmissEnabled'  : '1',
            'MemoryCards'               : '1',
            'MemoryCardDriver'          : 'Directory',
            'MemoryCardProfileSubdir'   : 'StepMania 5'
        }

        if useReaders:
            for i in ['1', '2']:
                check['MemoryCardUsbBusP' + i] = '-1'
                check['MemoryCardUsbBusP' + i] = '-1'
                check['MemoryCardUsbPortP' + i] = '-1'
                check['MemoryCardOsMountPointP' + i] = path.join(self.saveDir, 'PadmissProfileP' + i)

        changes = {}
        for k, v in check.items():
            if k not in iniConfig['Options'] or iniConfig['Options'][k] != v:
                changes[k] = v

        if len(changes) > 0:
            print("\n\nI'd like to make some changes to your Preferences.ini\n")
            for k, v in changes.items():
                print(k + '=' + v)

            if not self.confirm('Is this ok?'):
                return False

            for k, v in changes.items():
                iniConfig['Options'][k] = v

            with open(preferences, 'w') as configfile:
                iniConfig.write(configfile, space_around_delimiters = False)
                print('Preferences updated, restart game to apply')

        return True

    def checkEnvironment(self, currentPath):
        binary = self.findBinary(currentPath)

        if binary == False:
            currentPath = path.join(currentPath, '..')
            binary = self.findBinary(currentPath)
            if binary == False:
                print("I don't think this is a stepmania folder")
                return False

        print('Binary found at: ' + binary)

        preferences = self.findPreferences(currentPath)
        if preferences == False:
            print("Couldn't find Preferences.ini, did you run the game at lease once?")
            return False

        return preferences

    def checkApiKey(self):
        if self.storedConfig:
            return self.storedConfig.api_key

        token = input("Please enter your cab's API Key, leave empty to create: ")

        if not token:
            auth = False

            print("If you don't have a padmiss account yet, you can register at: https://www.padmiss.com/#/register")

            while not auth:
                try:
                    auth = self.api.authenticate(
                        input('Enter your padmiss email: '),
                        getpass.getpass('Enter your padmiss password: ')
                    )
                except Exception as e:
                    print(str(e))

            while not token:
                try :
                    result = self.api.register_cab(
                        input('What is the name of your cab/setup?: ')
                    )

                    token = result['apiKey']
                except Exception as e:
                    print('API Key creation failed: ' + str(e))

        return token

    def detectConfig(self):
        first = True

        if self.args.sm_dir:
            currentPath = self.args.sm_dir
        elif getattr(sys, 'frozen', False):
            currentPath = path.dirname(sys.executable)
        else:
            currentPath = path.dirname(os.path.realpath(__file__))

        print('Working from: ' + currentPath)

        preferences = self.checkEnvironment(currentPath)
        if not preferences:
            return False

        self.saveDir = path.dirname(preferences)

        configPath = path.join(self.saveDir, 'Padmiss.json')
        configManager = PadmissConfigManager(configPath, defaultDirs=False)

        if path.exists(configPath):
            self.storedConfig = configManager.load_config()
            first = False

        print('Using preferences: ' + preferences)

        useReaders = self.checkReaders()

        if not self.checkOptions(preferences, useReaders):
            print("Couldn't get Preferences in order")
            return False

        myDevices = []
        if useReaders:
            foundDevices = list(usb.core.find(idVendor=0x08FF, idProduct=0x0009, find_all=True))

            for i in ['1', '2']:
                index = int(i) - 1

                if len(foundDevices) > index:
                    myDevices.append(DeviceConfig(
                        path=path.join(self.saveDir, 'PadmissProfileP' + i),
                        type='hid',
                        hid_config=hid.ReaderConfig(
                            id_vendor=str(("%x" % foundDevices[index].idVendor).zfill(4)),
                            id_product=str(("%x" % foundDevices[index].idProduct).zfill(4)),
                            port_number=foundDevices[index].port_number,
                            bus=foundDevices[index].bus
                        )
                    ))

            if self.args.flip_readers:
                myDevices.reverse()

        apiKey = self.checkApiKey()

        if first:
            self.addprofile()

        storeConfig = PadmissConfig(
            api_key = apiKey,
            use_readers = useReaders
        )

        configManager.save_config(storeConfig)

        detectedConfig = PadmissConfig(
            padmiss_api_url=self.apiUrl,
            api_key = apiKey,
            scores_dir=path.join(self.saveDir, 'Padmiss'),
            profile_dir_name='StepMania 5',
            devices = myDevices
        )

        return detectedConfig

    def run(self):


        config = starter.detectConfig()

        if not config:
            return

        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(threadName)s - %(levelname)s: %(message)s')

        if self.args.just_log:
            padmiss_daemon = PadmissDaemon(config)

            try:
                start_and_wait_for_threads([padmiss_daemon])
            except BaseException:
                log.exception("Caught following while running daemon")

        else:
            logging.disable()

            self.thread = PadmissDaemon(config)
            self.thread.start()
            print("Padmiss running ... \n")
            self.interactive()

    def addprofile(self):
        nickname = True

        while nickname:
            nickname = input('Enter the nickname for a local profile do download, leave empty to continue: ')

            if not nickname:
                continue

            user = self.api.get_player(nickname=nickname)
            if not user:
                print('Player: ' + nickname + ' not found')
                continue

            dir = path.join(self.saveDir, 'LocalProfiles', nickname)
            generate_profile(dir, user, self.api)

            print('Profile downloaded for: ' + nickname)

    def help(self):
        print("")
        for k,v in self.actions.items():
            print(k + ': ' + v)

        print("")

    def quit(self):
        if self.thread and self.thread.is_alive():
            self.thread.stop()
            self.thread.join()

        self.running = False

    def log(self):
        logging.disable(logging.DEBUG)
        input("Showing log output ... \n")
        print('Logging disabled')
        logging.disable(logging.CRITICAL)

    actions = {
        'addprofile': 'Download local profiles',
        'quit': 'Close the padmiss client',
        'help': 'List all possible actions',
        'log': 'Show all log info (press "enter" to exit)'
    }

    def interactive(self):
        self.running = True

        while self.running:
            action = input('Padmiss > ')

            if not action:
                continue

            if action not in self.actions:
                print(action + ' is not a valid action, type "help" to list all possible actions')
                continue

            action = getattr(self, action)
            action()




if __name__ == '__main__':
    starter = PadmissStarter()
    starter.run()

    input("\nAt the end, goodbye (Press enter) ")