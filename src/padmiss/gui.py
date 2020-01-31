"""
Padmiss daemon, GUI version.

Initial code from https://evileg.com/en/post/68/.
"""

import sys
import logging, logging.handlers, os, queue, configparser

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, qApp, QFileDialog, QMessageBox, QCheckBox
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5 import uic, QtGui

from src.padmiss.stepmania import Stepmania
from .config import PadmissConfig, ScannerConfig, DeviceConfig, PadmissConfigManager
from .config.utils import getConfigFromUi, setConfigToUi
from .daemon import PadmissDaemon
from .thread_utils import start_and_wait_for_threads
from .util import resource_path
from .scandrivers import drivers

log = logging.getLogger(__name__)

#
# Threads
#

configManager = PadmissConfigManager()

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

Ui_MainWindow, MainWindowBaseClass = uic.loadUiType(resource_path('ui/main-window.ui'))
Ui_ConfigWindow, ConfigWindowBaseClass = uic.loadUiType(resource_path('ui/config-window.ui'))
Ui_DeviceConfigWidget, DeviceConfigWidgetBaseClass = uic.loadUiType(resource_path('ui/device-config-widget.ui'))

class toggle():
    def __init__(self, checkbox, widget):
        self.widget = widget
        self.checkbox = checkbox
        checkbox.clicked.connect(self.toggle)

    def toggle(self):
        self.widget.setVisible(self.checkbox.isChecked())

class DeviceConfigWidget(Ui_DeviceConfigWidget, DeviceConfigWidgetBaseClass):
    def __init__(self, device: DeviceConfig):
        DeviceConfigWidgetBaseClass.__init__(self)
        Ui_ConfigWindow.__init__(self)


        self.setupUi(self)

        self.device = device
        self.path.setText(device.path)
        self.browsePath.clicked.connect(self.pickBackupDir)

        self.configWidget = None
        self.driverWidgets = {}
        self.toggles = []

        # if device.type == 'scanner':
        #     self.configWidget = ScannerConfigWidget(device.config)
                
        # self.deviceSpecificContent.addWidget(self.configWidget)

        for name, module in drivers.items():
            if hasattr(module, 'ScannerConfigWidget'):
                enabled = False

                moduleConfig = getattr(device, module.configProp)
                if moduleConfig == None:
                    moduleConfig = module.ReaderConfig.emptyInstance()

                moduleWidget = module.ScannerConfigWidget(moduleConfig)
                moduleWidget.setVisible(moduleConfig.enabled == True)
                self.driverWidgets[name] = moduleWidget

                checkbox = QCheckBox(module.Reader.name)
                self.deviceSpecificContent.addWidget(checkbox)

                self.toggles.append(toggle(checkbox, moduleWidget))

                self.deviceSpecificContent.addWidget(moduleWidget)

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
    stepmania = None

    # Override the class constructor
    def __init__(self, mainWindow):
        ConfigWindowBaseClass.__init__(self)
        Ui_ConfigWindow.__init__(self)
        self.setupUi(self)
        self.configManager = configManager
        self.mainWindow = mainWindow

        icon = QtGui.QIcon(resource_path('icon.ico'))
        self.setWindowIcon(icon)

        # Init buttons
        self.stepmania_dir_browse.clicked.connect(self.pickStepmaniaDir)
        self.backup_dir_browse.clicked.connect(self.pickBackupDir)
        self.save.clicked.connect(self.saveAndClose)
        self.newScannerButton.clicked.connect(self.newScanner)
        self.sm5_config.clicked.connect(self.fixSm5Config)

    def showEvent(self, event):
        if self.configManager.hasValidConfig():
            config = self.configManager.load_config()
        else:
            config = self.configManager._get_default_config()

        setConfigToUi(self, config)

        self.deviceTabs.setTabsClosable(True)
        self.deviceTabs.tabCloseRequested.connect(self.closeTab)
        self.deviceTabs.clear()
        for i, device in enumerate(config.devices):
            self.deviceTabs.addTab(DeviceConfigWidget(device), str(i + 1))

    def closeTab(self, index):
        self.deviceTabs.removeTab(index)

        x = 1
        for i in range(self.deviceTabs.count()):
            self.deviceTabs.setTabText(i, str(x))
            x += 1

    # def createApi(self):

    def pickStepmaniaDir(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select StepMania 5 directory"))
        if folder:
            self.stepmania_dir.setText(folder)

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
        devices = [self.deviceTabs.widget(index).getConfig() for index in range(self.deviceTabs.count())]

        return getConfigFromUi(self, PadmissConfig, {'devices': devices})

        # return PadmissConfig(
        #     padmiss_api_url=self.padmiss_api_url.text(),
        #     api_key=self.api_key.text(),
        #     scores_dir=self.scores_dir.text(),
        #     backup_dir=self.backup_dir.text(),
        #     profile_dir_name=self.profile_dir_name.text(),
        #     hide_on_start=self.hide_on_start.isChecked(),
        #     # webserver=self.webserver.isChecked(),
        #     devices=[self.deviceTabs.widget(index).getConfig() for index in range(self.deviceTabs.count())]
        # )

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

            # iniConfig = configparser.ConfigParser()
            # iniConfig.optionxform = lambda option: option

            # iniConfig.read(file)
            iniConfig = {}
            iniConfig['Options']['MemoryCardProfiles'] = '1'
            iniConfig['Options']['MemoryCardPadmissEnabled'] = '1'
            iniConfig['Options']['MemoryCards'] = '1'
            iniConfig['Options']['MemoryCardDriver'] = 'Directory'
            iniConfig['Options']['MemoryCardProfileSubdir'] = myConfig.profile_dir_name

            # self.scores_dir.setText(os.path.dirname(file) + '/Padmiss')

            c = 1
            for i, dev in enumerate(myConfig.devices):
                iniConfig['Options']['MemoryCardUsbBusP' + str(c)] = '-1'
                iniConfig['Options']['MemoryCardUsbBusP' + str(c)] = '-1'
                iniConfig['Options']['MemoryCardUsbPortP' + str(c)] = '-1'
                iniConfig['Options']['MemoryCardOsMountPointP' + str(c)] = dev.path
                c = c + 1

            # with open(file, 'w') as configfile:
            #     iniConfig.write(configfile, space_around_delimiters = False)

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
        configManager.changed.append(self.restartThreads)

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
        self.configManager = configManager

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