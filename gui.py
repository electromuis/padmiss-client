"""
Padmiss daemon, GUI version.

Initial code from https://evileg.com/en/post/68/.
"""

import io
import logging, logging.handlers
import os
import queue
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QSystemTrayIcon, QMenu, QAction, QStyle, qApp
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5 import uic

from daemon import PadmissDaemon

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
        formatter = logging.Formatter('%(asctime)s - %(threadName)s %(name)s - %(levelname)s: %(message)s')

        while True:
            try:
                log_record = self.log_queue.get(block=True, timeout=1)
                log_string = formatter.format(log_record)
                self.log_event.emit(log_string)
            except queue.Empty:
                pass # no logs? it's ok. maybe next time.


class PadmissThread(QThread):
    def run(self):
        padmissDaemon = PadmissDaemon()
        padmissDaemon.start()

        while not self.isInterruptionRequested():
            padmissDaemon.join(0.1)

        padmissDaemon.stop()
        padmissDaemon.join()


Ui_MainWindow, QtBaseClass = uic.loadUiType(resource_path('main-window.ui'))

class MainWindow(Ui_MainWindow, QtBaseClass):
    trayIcon = None
    logThread = None
    padmissThread = None

    # Override the class constructor
    def __init__(self):
        QMainWindow.__init__(self)
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
        quit_action.triggered.connect(qApp.quit)
        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.trayIcon.setContextMenu(tray_menu)
        self.trayIcon.show()

        # Init padmiss thread
        self.padmissThread = PadmissThread()
        self.padmissThread.finished.connect(self.padmissDaemonFinished)

        # Init start button
        self.startStopButton.clicked.connect(self.togglePadmissThread)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())