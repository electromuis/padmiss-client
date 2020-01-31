import os

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableView, QFileDialog

from src.padmiss.config.utils import ReaderConfigBase, setConfigToUi
from src.padmiss.util import resource_path
from . import driver
from ..config.utils import PathWidget

import logging, time
log = logging.getLogger(__name__)

class Reader(driver.ScanDriver):
    name = 'FileSystem Driver'

    def __init__(self, config, poller):
        super(Reader, self).__init__(config, poller)

    def poll(self):
        try:
            buffer = os.read(self.file, 200)
        except OSError as err:
            buffer = None
            time.sleep(0.2)

        return "".join(map(chr, buffer))

    def update(self):
        driver.ScanDriver.update()

class ReaderConfig(ReaderConfigBase):
    path: str

    @classmethod
    def emptyInstance(cls):
        return ReaderConfig(path="", enabled=False)

Ui_Widget, WidgetBaseClass = uic.loadUiType(resource_path('ui/path-widget.ui'))
class ScannerConfigWidget(Ui_Widget, WidgetBaseClass):
    def __init__(self, scanner: ReaderConfig):
        WidgetBaseClass.__init__(self)
        self.setupUi(self)

        setConfigToUi(self, scanner)

        self.browsePath.clicked.connect(self.pickDir)

    def pickDir(self):
        folder = str(QFileDialog.getOpenFileName(self, "Select expected card file")[0])
        if folder:
            self.path.setText(folder)
