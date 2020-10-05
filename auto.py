import configparser
import logging
import time

from os import path
import usb
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

log = logging.getLogger(__name__)

def confirm(question):
    return askQuestion(question, ['Y', 'n', '']).lower() != 'n'

def askQuestion(question, options):
    answer = None

    while answer == None:
        result = input(question + ' [' + (' / '.join(filter(len, options))) + ']: ')
        if result in options:
            answer = result

    return answer

def findBinary(searchPath):
    binary = path.join(searchPath, 'stepmania')
    if path.exists(binary):
        return binary

    binary = path.join(searchPath, 'Program', 'StepMania.exe')
    if path.exists(binary):
        return binary

    return False

def findPreferences(rootPath):
    pref = path.join(rootPath, 'Save', 'Preferences.ini')
    if path.exists(pref):
        return pref

    if path.exists(path.join(rootPath, 'Portable.ini')):
        return False

    if os.name == 'nt':
        pref = path.join(os.getenv('APPDATA'), 'StepMania 5', 'Save', 'Preferences.ini')
        if path.exists(pref):
            return pref

        pref = path.join(os.getenv('APPDATA'), 'StepMania 5.1', 'Save', 'Preferences.ini')
        if path.exists(pref):
            return pref
    else:
        pref = path.join(os.path.expanduser('~'), '.stepmania5', 'Save', 'Preferences.ini')
        if path.exists(pref):
            return pref

        pref = path.join(os.path.expanduser('~'), '.stepmania5.1', 'Save', 'Preferences.ini')
        if path.exists(pref):
            return pref

    return False

def checkWinDrivers():
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
            if(input("I noticed your readers don't have the correct drivers, would you like to install?") != 'y'):
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
        else:
            print('Driver already installed')

    except Exception as e:
        print(str(e))
        return False

    return True

def checkReaders():
    # Search for most common supported scanners
    devices = list(usb.core.find(idVendor = 0x08FF, idProduct = 0x0009, find_all=True))
    numDevices = len(devices)

    for d in devices:
        usb.util.dispose_resources(d)

    if numDevices > 0:
        if(confirm('Would you like to use the connected readers?')):
            if os.name == 'nt':
                if not checkWinDrivers():
                    return False

            return numDevices

    return False

def checkOptions(preferences, useReaders):
    iniConfig = configparser.ConfigParser()
    iniConfig.optionxform = lambda option: option
    iniConfig.read(preferences)

    if 'Options' not in iniConfig:
        print('Invalid Preferences detected')
        return False

    if 'MemoryCardPadmissEnabled' not in iniConfig['Options']:
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
            check['MemoryCardOsMountPointP' + i] = path.join(path.dirname(preferences), 'PadmissProfileP' + i)

    changes = {}
    for k, v in check.items():
        if k not in iniConfig['Options'] or iniConfig['Options'][k] != v:
            changes[k] = v

    if len(changes) > 0:
        print("I'd like to make some changes to your Preferences.ini")
        for k, v in changes.items():
            print(k + '=' + v)

        if not confirm('Is this ok?'):
            return False

        for k, v in changes.items():
            iniConfig['Options'][k] = v

        with open(preferences, 'w') as configfile:
            iniConfig.write(configfile, space_around_delimiters = False)
            print('Preferences updated, restart game to apply')

    return True

def checkEnvironment(currentPath):
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

    return preferences

def detectConfig():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sm-dir', help='The root Stepmania folder to work from')
    parser.add_argument('--flip-readers', help='Swap P1 and P2 reader')
    args = parser.parse_args()

    if args.sm_dir:
        currentPath = args.sm_dir
    elif getattr(sys, 'frozen', False):
        currentPath = path.dirname(sys.executable)
    else:
        currentPath = path.dirname(__file__)

    print('Working from: ' + currentPath)

    preferences = checkEnvironment(currentPath)
    if not preferences:
        return

    print('Using preferences: ' + preferences)

    useReaders = checkReaders()

    if not checkOptions(preferences, useReaders):
        print("Couldn't get Preferences in order")
        return

    apiKey = ''

    myDevices = []
    if useReaders:
        foundDevices = list(usb.core.find(idVendor=0x08FF, idProduct=0x0009, find_all=True))

        for i in ['1', '2']:
            index = int(i) - 1

            if len(foundDevices) > index:
                myDevices.append(DeviceConfig(
                    path=path.join(path.dirname(preferences), 'PadmissProfileP' + i),
                    type='hid',
                    hid_config=hid.ReaderConfig(
                        id_vendor=foundDevices[index].idVendor,
                        id_product=foundDevices[index].idProduct,
                        port_number=foundDevices[index].port_number,
                        bus=foundDevices[index].bus
                    )
                ))

        if args.flip_readers:
            myDevices.reverse()

    detectedConfig = PadmissConfig(
        padmiss_api_url='https://api.padmiss.com/',
        api_key = apiKey,
        scores_dir=path.join(path.dirname(preferences), 'Padmiss'),
        profile_dir_name='StepMania 5',
        devices = myDevices
    )

    return detectedConfig

log = logging.getLogger(__name__)

if __name__ == '__main__':
    config = detectConfig()

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(threadName)s - %(levelname)s: %(message)s')
    padmiss_daemon = PadmissDaemon(config)

    try:
        start_and_wait_for_threads([padmiss_daemon])
    except BaseException:
        log.exception("Caught following while running daemon")