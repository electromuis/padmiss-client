# building on above and http://stackoverflow.com/questions/827371/is-there-a-way-to-list-all-the-available-drive-letters-in-python
import string
from ctypes import windll
import time
import os

def get_drives():
    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for letter in string.uppercase:
        if bitmask & 1:
            drives.append(letter)
        bitmask >>= 1
    return drives


if __name__ == '__main__':
    before = set(get_drives())
    pause = raw_input("Please insert the USB device, then press ENTER")
    print ('Please wait...')
    time.sleep(5)
    after = set(get_drives())
    drives = after - before
    delta = len(drives)

    if (delta):
        for drive in drives:
            if os.system("cd " + drive + ":") == 0:
                newly_mounted = drive
                print "There were %d drives added: %s. Newly mounted drive letter is %s" % (delta, drives, newly_mounted)
    else:
        print "Sorry, I couldn't find any newly mounted drives."