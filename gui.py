"""
Padmiss daemon, GUI version.

Initial code from https://evileg.com/en/post/68/.
"""

import io
import logging, logging.handlers
import os
import queue
import sys
import configparser
import getpass
from PyQt5.QtWidgets import QMainWindow, QApplication, QSystemTrayIcon, QMenu, QAction, QStyle, qApp, QFileDialog, QMessageBox, QInputDialog
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5 import uic, QtGui
import pkgutil

from config import PadmissConfig, ScannerConfig, DeviceConfig, getManager
from hid import listDevices
from daemon import PadmissDaemon
from thread_utils import start_and_wait_for_threads

log = logging.getLogger(__name__)

# from https://stackoverflow.com/a/51061279
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

#
# Threads
#

class LogThread(QThread):
    log_event = pyqtSignal('PyQt_PyObject')
    threadactive = False
    log_queue = None

    def __init__(self):
        QThread.__init__(self)
        self.log_queue = queue.Queue()
        queue_handler = logging.handlers.QueueHandler(self.log_queue)
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(queue_handler)

    def run(self):
        formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s: %(message)s')

        while True:
            try:
                log_record = self.log_queue.get(block=True, timeout=1)
                log_string = formatter.format(log_record)
                self.log_event.emit(log_string)
            except queue.Empty:
                pass # no logs? it's ok. maybe next time.


class PadmissThread(QThread):
    def run(self):
        try:
            start_and_wait_for_threads([PadmissDaemon()], lambda: self.isInterruptionRequested())
        except:
            log.exception("Exception on Padmiss daemon")


#
# Windows & Widgets
#

Ui_MainWindow, MainWindowBaseClass = uic.loadUiType(resource_path('main-window.ui'))
Ui_ConfigWindow, ConfigWindowBaseClass = uic.loadUiType(resource_path('config-window.ui'))
Ui_DeviceConfigWidget, DeviceConfigWidgetBaseClass = uic.loadUiType(resource_path('device-config-widget.ui'))
Ui_ScannerConfigWidget, ScannerConfigWidgetBaseClass = uic.loadUiType(resource_path('scanner-config-widget.ui'))

class ScannerConfigWidget(Ui_ScannerConfigWidget, ScannerConfigWidgetBaseClass):
    def __init__(self, scanner: ScannerConfig):
        ScannerConfigWidgetBaseClass.__init__(self)
        Ui_ConfigWindow.__init__(self)
        self.setupUi(self)

        # setup
        self.idVendor.setText(scanner.id_vendor)
        self.idProduct.setText(scanner.id_product)
        self.portNumber.setText(str(scanner.port_number) if scanner.port_number is not None else "")
        self.bus.setText(str(scanner.bus) if scanner.bus is not None else "")
        self.pickDeviceButton.clicked.connect(self.findScanner)

    def getConfig(self):
        return ScannerConfig(
            id_vendor=self.idVendor.text(),
            id_product=self.idProduct.text(),
            port_number=int(self.portNumber.text()) if self.portNumber.text() else None,
            bus=int(self.bus.text()) if self.bus.text() else None
        )

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


class DeviceConfigWidget(Ui_DeviceConfigWidget, DeviceConfigWidgetBaseClass):
    def __init__(self, device: DeviceConfig):
        ScannerConfigWidgetBaseClass.__init__(self)
        Ui_ConfigWindow.__init__(self)
        self.setupUi(self)

        self.device = device
        self.path.setText(device.path)
        self.browsePath.clicked.connect(self.pickBackupDir)

        self.configWidget = None

        if device.type == 'scanner':
            self.configWidget = ScannerConfigWidget(device.config)
                
        self.deviceSpecificContent.addWidget(self.configWidget)

    def getConfig(self):
        if self.device.type == 'scanner':
            return DeviceConfig(
                type = 'scanner', # todo
                path = self.path.text(),
                config = self.configWidget.getConfig()
            )
        elif self.device.type == 'fifo':
            return self.device

        return None

    def pickBackupDir(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select profile directory"))
        if folder:
            self.path.setText(folder)

class ConfigWindow(Ui_ConfigWindow, ConfigWindowBaseClass):
    configManager = None
    callBack = None
    config = None

    # Override the class constructor
    def __init__(self, mainWindow):
        ConfigWindowBaseClass.__init__(self)
        Ui_ConfigWindow.__init__(self)
        self.setupUi(self)
        self.configManager = getManager()
        self.mainWindow = mainWindow

        icon = QtGui.QIcon(resource_path('icon.ico'))
        self.setWindowIcon(icon)

        # Init buttons
        self.backup_dir_browse.clicked.connect(self.pickBackupDir)
        self.scores_dir_browse.clicked.connect(self.pickScoresDir)
        self.save.clicked.connect(self.saveAndClose)
        self.newScannerButton.clicked.connect(self.newScanner)
        self.sm5_config.clicked.connect(self.fixSm5Config)

    def showEvent(self, event):
        if self.configManager.hasValidConfig():
            config = self.configManager.load_config()
        else:
            config = self.configManager._get_default_config()

        # Load current config values
        self.padmiss_api_url.setText(config.padmiss_api_url)
        self.api_key.setText(config.api_key)
        self.profile_dir_name.setText(config.profile_dir_name)
        self.backup_dir.setText(config.backup_dir)
        self.scores_dir.setText(config.scores_dir)
        self.hide_on_start.setChecked(config.hide_on_start)
        if config.webserver:
            self.webserver.setChecked(config.webserver)

        self.deviceTabs.clear()
        for i, device in enumerate(config.devices):
            self.deviceTabs.addTab(DeviceConfigWidget(device), str(i + 1))
    
    def pickBackupDir(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if folder:
            self.backup_dir.setText(folder)

    def pickScoresDir(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if folder:
            self.scores_dir.setText(folder)

    def saveAndClose(self):
        config = self.toConfig()
        self.configManager.save_config(config)
        self.close()

        if self.callBack:
            self.callBack()
            self.callBack = None

    def toConfig(self):
        return PadmissConfig(
            padmiss_api_url=self.padmiss_api_url.text(),
            api_key=self.api_key.text(),
            scores_dir=self.scores_dir.text(),
            backup_dir=self.backup_dir.text(),
            profile_dir_name=self.profile_dir_name.text(),
            hide_on_start=self.hide_on_start.isChecked(),
            webserver=self.webserver.isChecked(),
            devices=[self.deviceTabs.widget(index).getConfig() for index in range(self.deviceTabs.count())]
        )

    # def closeEvent(self, event):
    #     if self.callBack != None:
    #         if not self.configManager.hasValidConfig():
    #             event.ignore()

    def newScanner(self):
        next = len(self.deviceTabs) + 1

        empty = DeviceConfig(
            type = 'scanner',
            path = self.configManager._get_path_inside_padmiss_dir('player' + str(next)),
            config = ScannerConfig(
                id_vendor = '',
                id_product = ''
            )
        )

        for index in range(self.deviceTabs.count()):
            self.deviceTabs.widget(index).num = index + 1

        self.deviceTabs.addTab(DeviceConfigWidget(empty), str(next))

    def fixSm5Config(self):
        file = str(QFileDialog.getOpenFileName(self, "Select Preferences.ini")[0])

        if file:
            myConfig = self.toConfig()

            iniConfig = configparser.ConfigParser()
            iniConfig.optionxform = lambda option: option

            iniConfig.read(file)
            iniConfig['Options']['MemoryCardProfiles'] = '1'
            iniConfig['Options']['MemoryCardPadmissEnabled'] = '1'
            iniConfig['Options']['MemoryCards'] = '1'
            iniConfig['Options']['MemoryCardDriver'] = 'Directory'
            iniConfig['Options']['MemoryCardProfileSubdir'] = myConfig.profile_dir_name

            self.scores_dir.setText(os.path.dirname(file) + '/Padmiss')

            c = 1
            for i, dev in enumerate(myConfig.devices):
                iniConfig['Options']['MemoryCardUsbBusP' + str(c)] = '-1'
                iniConfig['Options']['MemoryCardUsbBusP' + str(c)] = '-1'
                iniConfig['Options']['MemoryCardUsbPortP' + str(c)] = '-1'
                iniConfig['Options']['MemoryCardOsMountPointP' + str(c)] = dev.path
                c = c + 1

            with open(file, 'w') as configfile:
                iniConfig.write(configfile, space_around_delimiters = False)

            QMessageBox.information(self, 'Padmiss', 'Preferences updated!')

class MainWindow(Ui_MainWindow, MainWindowBaseClass):
    trayIcon = None
    logThread = None
    padmissThread = None
    configWindow = None
    configManager = None
    threadStoppedHook = None

    # Override the class constructor
    def __init__(self):
        MainWindowBaseClass.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        getManager().changed.append(self.restartThreads)

        icon = QtGui.QIcon(resource_path('icon.ico'))
        self.setWindowIcon(icon)

        # Init log thread
        self.logThread = LogThread()
        self.logThread.log_event.connect(self.newLogEvent)
        self.logThread.start()

        def showMaybe():
            if not self.configWindow.callBack:
                self.show()

        # Init tray icon
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(icon)
        self.trayIcon.activated.connect(showMaybe)
        show_action = QAction("Settings...", self)
        quit_action = QAction("Quit", self)
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.quitEvent)
        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.trayIcon.setContextMenu(tray_menu)
        self.trayIcon.show()

        # Init padmiss thread
        self.padmissThread = PadmissThread()
        self.padmissThread.finished.connect(self.padmissDaemonFinished)
        self.startStopButton.clicked.connect(self.togglePadmissThread)

        # Init config window
        self.configWindow = ConfigWindow(self)
        self.configureButton.clicked.connect(self.openConfigWindow)

        self.quit.clicked.connect(self.quitEvent)

        # Done!
        log.info("Window initialized")

    def padmissDaemonFinished(self):
        self.startStopButton.setDisabled(False)
        self.startStopButton.setStyleSheet("background-color: red")
        self.startStopButton.setText('Start')
        if self.threadStoppedHook is not None:
            self.threadStoppedHook()
            self.threadStoppedHook = None

    def togglePadmissThread(self):
        if self.padmissThread.isRunning():
            self.stopThread()
        else:
            self.startThread()

    def newLogEvent(self, data):
        self.logView.appendPlainText(data)

    # Override closeEvent, to intercept the window closing event
    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def openConfigWindow(self):
        self.configWindow.show()

    def stopThread(self):
        self.startStopButton.setDisabled(True)
        self.startStopButton.setStyleSheet("background-color: grey")
        self.startStopButton.setText('Stopping...')
        self.padmissThread.requestInterruption()

    def startThread(self):
        self.startStopButton.setStyleSheet("background-color: green")
        self.startStopButton.setText('Stop')
        self.padmissThread.start()

    def restartThreads(self):
        if self.padmissThread.isRunning():
            self.threadStoppedHook = self.startThread
            self.stopThread()

    def quitEvent(self, event):
        self.trayIcon.hide()
        self.padmissThread.finished.connect(qApp.quit)

        if self.padmissThread.isRunning():
            self.padmissThread.requestInterruption()
            # will quit upon thread stopping
        else:
            qApp.quit()

    def attemptShow(self):
        self.configManager = getManager()

        def callBack():
            self.show()
            self.togglePadmissThread()

        if not self.configManager.hasValidConfig():
            self.configWindow.callBack = callBack
            self.openConfigWindow()
        else:
            config = self.configManager.load_config()

            # Start daemon
            self.togglePadmissThread()
            if not config.hide_on_start:
                self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.attemptShow()
    sys.exit(app.exec())