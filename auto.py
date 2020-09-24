import configparser
import logging
import time

from os import path
import usb
import os
import subprocess
import win32com.client

from src.padmiss.daemon import PadmissDaemon
from src.padmiss.thread_utils import start_and_wait_for_threads
from src.padmiss import stepmania
from src.padmiss.util import resource_path

log = logging.getLogger(__name__)

def findBinary(searchPath):
    binary = path.join(searchPath, 'stepmania')
    if path.exists(binary):
        return binary

    binary = path.join(searchPath, 'Program', 'StepMania.exe')
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
    dev = list(usb.core.find(idVendor = 0x08FF, idProduct = 0x0009, find_all=True))

    if len(dev) > 0:
        if os.name == 'nt':
            print('Checking driver')
            print(checkWinDrivers())

    return False

def checkOptions(options, useReaders):
    wrongOptions = []
    check = {
        'MemoryCardPadmissEnabled'
    }

def autoConfig():
    currentPath = str(path.dirname(os.path.realpath(__file__)))
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


if __name__ == '__main__':
    checkReaders()

    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(threadName)s - %(levelname)s: %(message)s')
    # padmiss_daemon = PadmissDaemon()
    #
    # try:
    #     start_and_wait_for_threads([padmiss_daemon])
    # except BaseException:
    #     log.exception("Caught following while running daemon")