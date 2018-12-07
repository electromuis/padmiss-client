#!/usr/bin/env python

import sys
from winusbpy import *
import logging
import time
import binascii


log = logging.getLogger(__name__)


class RFIDReader(object):
    def __init__(self, **match):
        self.match = match
        result = self.connect()
        if result == False:
            raise RuntimeError('Not found')

    def connect(self):
        self.api = WinUsbPy()

        if self.api.list_usb_devices(deviceinterface=True, present=True) == False:
            print('err1')
            return False

        print(self.match)

        if self.api.init_winusb_device(**self.match) == False:
            print('err2')
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

        pipe_info_list = map(self.api.query_pipe, range(intf.b_num_endpoints))
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
    r = RFIDReader(vid="08ff", pid="0009")

    print 'Starting read loop'
    while True:
        data = r.poll()
        if data:
            print 'poll result:'
            print data
