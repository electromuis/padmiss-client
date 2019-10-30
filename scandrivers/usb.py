from config import DeviceConfig
import scandrivers
import os
import string
import glob
from dirsync import sync

class UsbDriverBase(scandrivers.driver.ScanDriver):
    def __init__(self, config: DeviceConfig):
        super().__init__(config)
        self.drive = config.usb_config.hw_path
        self.lastFiles = []

    def getMountDir(self):
        return self.drive

    def checkOut(self):
        self.lastFiles = []
        return False

    def listUsbs(self):
        return []

    def update(self):
        drives = self.listUsbs()
        if self.poller.mounted and self.poller.mounted.driver == self:
            if self.drive not in drives:
                #unmount
                pass
            else:
                self.syncDisk()
        else:
            if self.drive in drives:
                #mount
                pass

    def syncDisk(self):
        path = os.path.join(self.config.path, self.poller.config.profile_dir_name)

        if not os.path.exists(path):
            return

        files = [f for f in glob.glob(path + "**/*", recursive=True)
                 if not 'Songs' in f]
        files = map(lambda f: f+os.path.getmtime(f), files)

        if files != self.lastFiles:
            target = os.path.join(self.getMountDir(), self.poller.config.profile_dir_name)
            sync(path, target, create = True, sync = True, update = True, content = True)

            pass

if os.name == 'nt':
    from ctypes import windll

    class UsbDriver(UsbDriverBase):
        def listUsbs(self):
            drives = []
            bitmask = windll.kernel32.GetLogicalDrives()
            for letter in string.uppercase:
                if bitmask & 1:
                    drives.append(letter + ':\\')
                bitmask >>= 1

            return drives
else:
    class UsbDriver(UsbDriverBase):
        def getMountDir(self):
            return self.config.path + 'mnt'

        def listUsbs(self):
            p = os.subprocess.Popen(["ls", "/dev/disk/by-path/"], stdout=os.subprocess.PIPE)
            out = p.stdout.read().split("\n")
            return out

        def syncDisk(self):
            #mount
            super().syncDisk()
            #unmount