from typing import Optional

from PyQt5 import uic
from PyQt5.QtWidgets import QFileDialog
from pydantic import UrlStr, BaseModel

from src.padmiss.util import resource_path


def setConfigToUi(ui, config):
    for k,type in config.__class__.__fields__.items():
        if not hasattr(ui, k):
            continue

        v = getattr(config, k)
        field = getattr(ui, k)

        type = type.type_
        if hasattr(type, '__args__') and len(type.__args__) == 2:
            type = type.__args__[0]

        if type == UrlStr:
            type =  str

        if type == str and v != None and len(v) > 0:
            field.setText(v)

        if type == int and v != None:
            field.setText(str(v))

        if type == bool and v != None:
            field.setChecked(bool(v))

def getConfigFromUi(ui, cls, defaults = {}):
    types = cls.__fields__.items()
    ret = defaults

    for k,type in types:
        if hasattr(ui, k) == False:
            continue

        field = getattr(ui, k)
        type = type.type_
        if hasattr(type, '__args__') and len(type.__args__) == 2:
            type = type.__args__[0]

        if type == UrlStr:
            type =  str

        if type == str and len(field.text()) > 0:
            ret[str(k)] = field.text()

        if type == int and len(field.text()) > 0:
            ret[str(k)] = int(field.text())

        if type == bool:
            ret[str(k)] = field.isChecked()

    return cls(**ret)

class ReaderConfigBase(BaseModel):
    enabled: Optional[bool]

Ui_Widget, WidgetBaseClass = uic.loadUiType(resource_path('ui/path-widget.ui'))
class PathWidget(Ui_Widget, WidgetBaseClass):
    def __init__(self):
        WidgetBaseClass.__init__(self)
        Ui_Widget.__init__(self)
        self.setupUi(self)

        self.browsePath.clicked.connect(self.pickDir)

    def getText(self):
        return self.path.getText()

    def setText(self, text):
        return self.path.setText(text)

    def pickDir(self):
        folder = str(QFileDialog.getOpenFileName(self, "Select directory/file"))
        if folder:
            self.path.setText(folder)