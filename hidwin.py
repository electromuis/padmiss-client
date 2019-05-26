#!/usr/bin/env python

import sys
from winusbpy import *
import logging
import time
import binascii
from pprint import pprint
import winreg
import re

log = logging.getLogger(__name__)

def listDevices():
    ret = []
    api = WinUsbPy()

    if api.list_usb_devices(deviceinterface=True, present=True) == False:
        return ret

    for path in api.device_paths:
        pts = path.split('#')
        pt = pts[2]
        ids = pts[1].split('&')

        reg = r"SYSTEM\\CurrentControlSet\\Enum\USB\\" + ids[0].upper() + "&" + ids[1].upper() + "\\" + pt
        hKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg)
        result = winreg.QueryValueEx(hKey, "LocationInformation")
        if result:
            result = result[0]

            ids[0] = '0x' + ids[0].split('_')[1]
            ids[1] = '0x' + ids[1].split('_')[1]

            matchObj = re.match(r'Port_#0*(\d+)\.Hub_#0*(\d+)', result, re.I)
            ret.append({'idVendor': ids[0], 'idProduct': ids[1], 'port_number': matchObj.group(1), 'bus': matchObj.group(2)})

    return ret


class RFIDReader(object):
    def __init__(self, **match):
        self.match = match

        if self.match['idVendor']:
            self.match['vid'] = "vid_" + match['idVendor']
        if self.match['idProduct']:
            self.match['pid'] = "pid_" + match['idProduct']

        result = self.connect()
        if result == False:
            raise RuntimeError('Not found')

    def connect(self):
        self.api = WinUsbPy()

        if self.api.list_usb_devices(deviceinterface=True, present=True) == False:
            print('E1')
            return False

        device = None

        for path in self.api.device_paths:
            print((self.match['vid'] + "-" + self.match['pid'] + "-" + path))
            if path.find(self.match['vid']) != -1 and path.find(self.match['pid']) != -1:
                if 'port_number' in self.match or 'hub_number' in self.match:
                    pt = path.split('#')[2]
                    reg = r"SYSTEM\\CurrentControlSet\\Enum\USB\\" + self.match['vid'].upper() + "&" + self.match['pid'].upper() + "\\" + pt
                    pprint(reg)
                    hKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg)
                    result = winreg.QueryValueEx(hKey, "LocationInformation")
                    if result:
                        result = result[0]
                        if 'port_number' in self.match:
                            val = 'Port_#' + str(self.match['port_number']).zfill(4)
                            if result.find(val) == -1:
                                continue
                        if 'bus' in self.match:
                            val = 'Hub_#' + str(self.match['bus']).zfill(4)
                            if result.find(val) == -1:
                                continue
                    device = path
                    break
                else:
                    device = path
                    break


        if device == None:
            print('E2')
            return False

        if self.api.init_winusb_device_by_path(device) == False:
            print('E3')
            return False

        print('Found device')
        self._find_intf()

        try:
            print('Setting BOOT protocol')
            pkt1 = UsbSetupPacket(0b00100001)
            self.api.control_transfer(pkt1, buff=[0])
        except:
            print('err3')
            return False

        return True

    def _find_intf(self):
        intf = self.api.query_interface_settings(0)

        if intf == None:
            raise RuntimeError('No interface found')

        if intf.b_interface_class == 3 and intf.b_interface_sub_class == 1 and intf.b_interface_protocol == 1:
            self.intf = intf
        else:
            raise RuntimeError('Does not appear to be RFID reader (1)')

        pipe_info_list = list(map(self.api.query_pipe, list(range(intf.b_num_endpoints))))
        for item in pipe_info_list:
            self.pipe = item.pipe_id
            return

        raise RuntimeError('Does not appear to be RFID reader (2)')

    def find(self):
        result = False
        while result == False:
            time.sleep(5)
            print('Searching ...')
            try:
                result = self.connect()
            except:
                result = False

        print('Found it again')

    def poll(self, initial_timeout = 200, key_timeout = 50):
        typed = []

        try:
            while True:
                res = self.api.read(self.pipe, 8)
                c = ord(res[2])

                if c > 0:
                    key = self._translate(c)
                    if key == '\n':
                        return ''.join(typed)
                    else:
                        typed.append(key)
                    # print("Disconnect err")
                    # self.find()
                    # return ''
        except:
            print("Disconnect err")
            self.find()
            return ''

    def _translate(self, key):
        if key < 30 or key > 40:
            raise RuntimeError('Missing lookup entry for key code %d' % key)

        if key < 39:
            return chr(ord('1') + (key - 30))
        elif key == 39:
            return '0'
        elif key == 40:
            return '\n'

    def __repr__(self):
        if self.intf:
            return 'Bus %d device %d interface %d' % (self.dev.bus, self.dev.address, self.intf.bInterfaceNumber)
        else:
            return 'Bus %d device %d' % (self.dev.bus, self.dev.address)


#  idVendor           0x08ff AuthenTec, Inc.
#  idProduct          0x0009 

if __name__ == '__main__':
    pprint(listDevices())
    #r = RFIDReader(idVendor=0x08ff, idProduct=0x0009)
    #print 'Starting read loop'
    #while True:
    #data = r.poll()
    #if data:
    #    print 'poll result:'
    #    print data
