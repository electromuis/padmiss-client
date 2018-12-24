import pyudev
from fstab import Fstab
import pprint

myEntry = None

fstab = Fstab()

for entry in fstab.entries:
     if entry.mountpoint  == '/media/anton/Windows/':
		 myEntry = entry
		 break

print('{} connected'.format(myEntry))

context = pyudev.Context()
monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by(subsystem='usb')

#for device in iter(monitor.poll, None):
#    if device.action == 'add':
#        print('{} connected'.format(device))
#        # do something
#	if device.action == 'delete':
#		print('{} disconnected'.format(device))