"""
Padmiss daemon, GUI version.

Initial code from https://evileg.com/en/post/68/.
"""

import io
import logging, logging.handlers
import os
import queue
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QSystemTrayIcon, QMenu, QAction, QStyle, qApp, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5 import uic

from config import PadmissConfigManager, PadmissConfig, ScannerConfig, DeviceConfig
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

    def getConfig(self):
        return ScannerConfig(
            id_vendor=self.idVendor.text(),
            id_product=self.idProduct.text(),
            port_number=int(self.portNumber.text()) if self.portNumber.text() else None,
            bus=int(self.bus.text()) if self.bus.text() else None
        )


class DeviceConfigWidget(Ui_DeviceConfigWidget, DeviceConfigWidgetBaseClass):
    def __init__(self, device: DeviceConfig):
        ScannerConfigWidgetBaseClass.__init__(self)
        Ui_ConfigWindow.__init__(self)
        self.setupUi(self)

        self.device = device
        self.path.setText(device.path)
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

        return None


class ConfigWindow(Ui_ConfigWindow, ConfigWindowBaseClass):
    configManager = None

    # Override the class constructor
    def __init__(self):
        ConfigWindowBaseClass.__init__(self)
        Ui_ConfigWindow.__init__(self)
        self.setupUi(self)
        self.configManager = PadmissConfigManager()

        # Init buttons
        self.backup_dir_browse.clicked.connect(self.pickBackupDir)
        self.scores_dir_browse.clicked.connect(self.pickScoresDir)
        self.save.clicked.connect(self.saveAndClose)

    def showEvent(self, event):
        config = self.configManager.load_config()

        # Load current config values
        self.padmiss_api_url.setText(config.padmiss_api_url)
        self.api_key.setText(config.api_key)
        self.profile_dir_name.setText(config.profile_dir_name)
        self.backup_dir.setText(config.backup_dir)
        self.scores_dir.setText(config.scores_dir)

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
        config = PadmissConfig(
            padmiss_api_url=self.padmiss_api_url.text(),
            api_key=self.api_key.text(),
            scores_dir=self.scores_dir.text(),
            backup_dir=self.backup_dir.text(),
            profile_dir_name=self.profile_dir_name.text(),
            devices=[self.deviceTabs.widget(index).getConfig() for index in range(self.deviceTabs.count())]
        )

        self.configManager.save_config(config)
        self.close()


class MainWindow(Ui_MainWindow, MainWindowBaseClass):
    trayIcon = None
    logThread = None
    padmissThread = None
    configWindow = None

    # Override the class constructor
    def __init__(self):
        MainWindowBaseClass.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        # Init log thread
        self.logThread = LogThread()
        self.logThread.log_event.connect(self.newLogEvent)
        self.logThread.start()

        # Init tray icon
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
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
        self.configWindow = ConfigWindow()
        self.configureButton.clicked.connect(self.openConfigWindow)

        # Start daemon
        self.togglePadmissThread()

        # Done!
        log.info("Window initialized")

    def padmissDaemonFinished(self):
        self.startStopButton.setDisabled(False)
        self.startStopButton.setText('Start')

    def togglePadmissThread(self):
        if self.padmissThread.isRunning():
            self.startStopButton.setDisabled(True)
            self.startStopButton.setText('Stopping...')
            self.padmissThread.requestInterruption()
        else:
            self.startStopButton.setText('Stop')
            self.padmissThread.start()

    def newLogEvent(self, data):
        self.logView.appendPlainText(data)

    # Override closeEvent, to intercept the window closing event
    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def openConfigWindow(self):
        self.configWindow.show()

    def quitEvent(self, event):
        self.trayIcon.hide()
        self.padmissThread.finished.connect(qApp.quit)

        if self.padmissThread.isRunning():
            self.padmissThread.requestInterruption()
            # will quit upon thread stopping
        else:
            qApp.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())