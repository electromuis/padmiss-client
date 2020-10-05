#!/usr/bin/env python

import sys
import usb
import logging
import time
import os
from pprint import pprint

from PyQt5.QtWidgets import QMessageBox
from PyQt5 import uic, QtGui

from padmiss.config.utils import setConfigToUi, getConfigFromUi, ReaderConfigBase
from padmiss.util import resource_path
from ..thread_utils import CancellableThrowingThread
from . import driver

log = logging.getLogger(__name__)

def listDevices():
    ret = []
    dev = usb.core.find(find_all=True)
    for d in dev:
        vendor = str(("%x" % d.idVendor).zfill(4))
        product = str(("%x" % d.idProduct).zfill(4))
        ret.append({'idVendor': vendor, 'idProduct': product, 'port_number': d.port_number, 'bus': d.bus})
    return ret

class Reader(driver.ScanDriver, CancellableThrowingThread):
    name = 'RFID Driver'

    def __init__(self, config, poller):
        super(Reader, self).__init__(config, poller)
        super(CancellableThrowingThread, self).__init__()

        self.threaded = True
        self.scannerConfig = config.config

        result = self.connect()
        if result == False:
            raise RuntimeError('RFID Device not found')

    def exc_run(self):
        while not self.stop_event.wait(0.2):
            try:
                data = self.poll()
                if data:
                    data = data.strip()

                    if data:
                        self.togglePlayer(data, None)

            except Exception:
                log.exception('Error getting player info from server')

        self.release()

    def getPlayer(self, playerId):
        p = self.poller.api.get_player(rfidUid=playerId)
        if p:
            p.driver = self
            p.rfidUid = self
            return p

        return None

    def handleAction(self, action):
        # no in/out mode, which means always toggle
        if not action.playerId:
            return

        if self.poller.mounted:
            if self.poller.mounted.driver == self and self.poller.mounted.rfidUid == action.playerId:
                self.checkOut()
            else:
                p = self.getPlayer(action.playerId)
                if p:
                    self.checkOut()
                    self.checkIn(p)
        else:
            p = self.getPlayer(action.playerId)
            if p:
                self.checkIn(p)

    def _get_find_match(self):
        match = {}
        if (len(self.scannerConfig.id_vendor) != 0):
            match["idVendor"] = int(self.scannerConfig.id_vendor, 16)
        if (len(self.scannerConfig.id_product) != 0):
            match["idProduct"] = int(self.scannerConfig.id_product, 16)
        if (self.scannerConfig.port_number is not None):
            match["port_number"] = self.scannerConfig.port_number
        if (self.scannerConfig.bus is not None):
            match["bus"] = self.scannerConfig.bus
        return match

    def connect(self):
        self.cfg = None
        self.intf = None
        self.detached = False
        self.last_pressed = set()
        
        match = self._get_find_match()
        self.dev = usb.core.find(**match)

        if self.dev is None:
            log.debug('Device not found with search: %s', match)
            return False

        log.debug('Found device %s', repr(self.dev))
        try:
            self._find_intf()
        except RuntimeError:
            return False

        if os.name != 'nt':
            try:
                if self.dev.is_kernel_driver_active(self.intf.bInterfaceNumber):
                    log.debug('Detaching kernel driver from %s', repr(self))
                    self.dev.detach_kernel_driver(self.intf.bInterfaceNumber)
                    self.detached = True
            except NotImplementedError:
                log.debug('Detaching kernel driver not supported on this platform')

        try:
            log.debug('Setting BOOT protocol on %s', repr(self))
            self.dev.ctrl_transfer(0b00100001, 0x0B, 0, self.intf.bInterfaceNumber, 0)
        except:
            self.release()
            raise

        return True

    def _find_intf(self):
        for cfg in self.dev:
            for intf in cfg:
                if intf.bInterfaceClass == 3 and intf.bInterfaceSubClass == 1 and intf.bInterfaceProtocol == 1:
                    self.cfg = cfg
                    self.intf = intf
                    return

        raise RuntimeError('%s does not appear to be RFID reader' % repr(self))

    def find(self):
        result = False
        while result == False:
            time.sleep(1)
            log.debug('Searching ...')
            try:
                self.release()
                result = self.connect()
            except usb.core.USBError as e:
                result = False

        log.debug('Found it again')

    def poll(self, initial_timeout = 500, key_timeout = 20):
        typed = []
        timeout = initial_timeout

        while True:
            try:
                ep = self.intf[0]
                data = ep.read(8, timeout)

                # Hardcoded BOOT protocol decoding
                mods = data[0]
                pressed = set()
                new_keys = []
                for key in data[2:]:
                    # Specials:
                    # 0 = NoEvent
                    # 1 = ErrorRollOver
                    # 2 = POSTFail
                    # 3 = ErrorUndefined
                    if key == 0:
                        continue
                    elif key == 1:
                        return None
                    elif key == 2:
                        raise RuntimeError('%s reports POSTFail' % repr(self))
                    elif key == 3:
                        raise RuntimeError('%s reports ErrorUndefined' % repr(self))
                    else:
                        if not key in self.last_pressed:
                            new_keys.append(key)
                        pressed.add(key)

                self.last_pressed = pressed

                typed.extend(new_keys)
            except usb.core.USBError as e:
                # Ignore timeouts, why isn't there a better way to do this in PyUSB?!
                if e.errno == 110 or e.errno == 10060: # 110 for linux, 10060 for windows
                    break
                elif e.errno == 19 or e.errno == 5:
                    log.debug("Disconnect err")
                    self.find()
                    return ''
                else:
                    raise

            timeout = key_timeout

        return ''.join(self._translate(key) for key in typed)


    def _translate(self, key):
        if key < 30 or key > 40:
            raise RuntimeError('Missing lookup entry for key code %d' % key)

        if key < 39:
            return chr(ord('1') + (key - 30))
        elif key == 39:
            return '0'
        elif key == 40:
            return '\n'


    def release(self):
        usb.util.dispose_resources(self.dev)

        if os.name != 'nt':
            if self.detached:
                log.debug('Reattaching kernel driver to %s', repr(self))
                try:
                    self.dev.attach_kernel_driver(self.intf.bInterfaceNumber)
                except usb.core.USBError:
                    log.exception('Error while reattaching kernel driver')
                finally:
                    self.detached = False


    def __repr__(self):
        if self.intf:
            return 'Bus %d device %d interface %d' % (self.dev.bus, self.dev.address, self.intf.bInterfaceNumber)
        else:
            return 'Bus %d device %d' % (self.dev.bus, self.dev.address)

from typing import Optional

class ReaderConfig(ReaderConfigBase):
    id_vendor: str
    id_product: str
    port_number: Optional[int]
    bus: Optional[int]

    @classmethod
    def emptyInstance(cls):
        return ReaderConfig(id_vendor="", id_product="", enabled=False)

configProp = 'config'

Ui_ScannerConfigWidget, ScannerConfigWidgetBaseClass = uic.loadUiType(resource_path('ui/hid-config-widget.ui'))

class ScannerConfigWidget(Ui_ScannerConfigWidget, ScannerConfigWidgetBaseClass):
    def __init__(self, scanner: ReaderConfig):
        ScannerConfigWidgetBaseClass.__init__(self)
        self.setupUi(self)

        setConfigToUi(self, scanner)
        # setup
        # self.idVendor.setText(scanner.id_vendor)
        # self.idProduct.setText(scanner.id_product)
        # self.portNumber.setText(str(scanner.port_number) if scanner.port_number is not None else "")
        # self.bus.setText(str(scanner.bus) if scanner.bus is not None else "")

        self.pickDeviceButton.clicked.connect(self.findScanner)

    def getConfig(self):
        ret = getConfigFromUi(self, ReaderConfig, {'type': 'scanner'})

        return ret

    def findScanner(self):
        reply = QMessageBox.information(self, 'Padmiss', 'Make sure the device is disconnected')
        devices = listDevices()
        reply = QMessageBox.information(self, 'Padmiss', 'Plug the device in, and wait 5 seconds')
        newDevices = listDevices()

        new = [x for x in newDevices if x not in devices]
        if not new:
            reply = QMessageBox.information(self, 'Padmiss', 'Device not found')
        else:
            device = new[0]
            self.idVendor.setText(device['idVendor'])
            self.idProduct.setText(device['idProduct'])
            self.portNumber.setText(str(device['port_number']))
            self.bus.setText(str(device['bus']))

            if os.name == 'nt':
                reply = QMessageBox.question(self, 'Padmiss', 'Do you want to install the driver?', QMessageBox.Yes|QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    QMessageBox.information(self, 'Padmiss',
                                            'Select the device with USB ID: ' + device['idVendor'].upper() + ' ' +
                                            device['idProduct'].upper() + ', then click Replace Driver')

                    dir = resource_path('zadig') + '\\'
                    tool = dir + 'zadig.exe'
                    import ctypes, sys
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", tool, dir, dir, 1)
            # else:
            #     rulePath = '/etc/udev/rules.d/99-usbgroup'
            #
            #     if not os.path.isfile(rulePath):
            #         reply = QMessageBox.question(self, 'Padmiss', 'Do you want to fix device permissions via udev?',
            #                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            #         if reply == QMessageBox.Yes:
            #             try :
            #                 cmd = "echo 'SUBSYSTEM==\"usb\", ENV{DEVTYPE}==\"usb_device\", MODE=\"0664\", GROUP=\"usbusers\"' > " + rulePath
            #                 password = False
            #
            #                 os.system(cmd)
            #                 if not os.path.isfile(rulePath):
            #                     password = QInputDialog.getText(self, 'Padmiss', 'Please enter your sudo password')
            #                     if not password:
            #                         raise Exception('No password entered')
            #
            #                     cmd = 'sudo -S ' + cmd
            #                     os.popen(cmd, 'w').write(password)
            #
            #                     if not os.path.isfile(rulePath):
            #                         raise Exception('wrong password?')
            #
            #
            #
            #
            #             except Exception as e:
            #                 QMessageBox.information(self, 'Padmiss', 'Failed: ' + str(e))

#  Most of the time:
#  idVendor           0x08ff AuthenTec, Inc.
#  idProduct          0x0009 

if __name__ == '__main__':
    pprint(listDevices())
