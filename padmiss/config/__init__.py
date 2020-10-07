import json
import os
import sys
import logging
from typing import Union, List, Optional
from enum import Enum
from pydantic import BaseModel, UrlStr, DirectoryPath, Schema
from typing import get_type_hints
from PyQt5 import uic, QtGui

from padmiss.stepmania import Stepmania
from ..scandrivers import loadConfigSchema
DeviceConfig = loadConfigSchema()

from ..util import resource_path

log = logging.getLogger(__name__)

class ScannerConfig(BaseModel):
    id_vendor: str
    id_product: str
    port_number: Optional[int]
    bus: Optional[int]

class FifoConfig(BaseModel):
    path: str

class UsbConfig(BaseModel):
    hw_path: str

# class DeviceConfig(BaseModel):
#     path: str
#     type: str
#     config: Optional[ScannerConfig]
#     fifo_config: Optional[FifoConfig]
#     usb_config: Optional[UsbConfig]

class RestConfig(BaseModel):
    host: str
    port: int
    broadcast: bool
    enabled: bool

class PadmissConfig(BaseModel):
    padmiss_api_url: Optional[UrlStr]
    api_key: str
    use_readers: Optional[bool]
    scores_dir: Optional[str]
    stepmania_dir: Optional[str]
    backup_dir: Optional[str]
    profile_dir_name: Optional[str]
    hide_on_start: Optional[bool]
    webserver: Optional[RestConfig]
    devices: Optional[List[DeviceConfig]]

uis = {
    ScannerConfig: 'hid-config-widget.ui',
    DeviceConfig: 'device-config-widget.ui',
    PadmissConfig: 'config-window'
}

def configUi(configItem):
    Ui_Window, WindowBaseClass = uic.loadUiType(resource_path('ui/' + uis[configItem.__class__]))

    class ConfigUi(Ui_Window, WindowBaseClass):
        def __init__(self):
            WindowBaseClass.__init__(self)
            Ui_Window.__init__(self)
            self.setupUi(self)
            self.setupWidgets()

            self.setConfigToUi(configItem)

        def setupWidgets(self):
            pass

        def setConfigToUi(self, config):
            for k, type in config.__class__.__fields__.items():
                if not hasattr(self, k):
                    continue

                v = getattr(config, k)
                field = getattr(self, k)

                type = type.type_
                if hasattr(type, '__args__') and len(type.__args__) == 2:
                    type = type.__args__[0]

                if type == UrlStr:
                    type = str

                if type == str and v != None and len(v) > 0:
                    field.setText(v)

                if type == int and v != None:
                    field.setText(str(v))

                if type == bool and v != None:
                    field.setChecked(bool(v))

        def getConfig(self):
            return self.getConfigFromUi()

        def getConfigFromUi(self, defaults={}):
            types = configItem.__class__.__fields__.items()
            ret = defaults

            for k, type in types:
                if hasattr(self, k) == False:
                    continue

                field = getattr(self, k)
                type = type.type_
                if hasattr(type, '__args__') and len(type.__args__) == 2:
                    type = type.__args__[0]

                if type == UrlStr:
                    type = str

                if type == str and len(field.text()) > 0:
                    ret[str(k)] = field.text()

                if type == int and len(field.text()) > 0:
                    ret[str(k)] = int(field.text())

                if type == bool:
                    ret[str(k)] = field.isChecked()

            return configItem.__class__(**ret)

class PadmissConfigManager(object):
    changed = []

    def hasValidConfig(self):
        path = self._get_config_path()
        return os.path.isfile(path)

    def __init__(self, custom_config_file_path=None, defaultDirs = True):
        if custom_config_file_path == None and os.path.exists(os.path.join('.', 'config.json')):
            custom_config_file_path = os.path.join('.', 'config.json')

        self._custom_config_file_path = custom_config_file_path
        self.defaultDirs = defaultDirs

    def _get_path_inside_padmiss_dir(self, *path):
        if os.name == 'nt':
            return os.path.join(os.getenv('APPDATA'), 'Padmiss', *path)
        else:
            return os.path.join(os.path.expanduser('~'), '.padmiss', *path)

    def _load_defaults(self, config):
        if config.stepmania_dir:
            try:
                stepmania = Stepmania(config.stepmania_dir)
                if not config.scores_dir and stepmania.padmiss:
                    config.scores_dir = stepmania.padmiss
            except:
                pass

    def _get_default_config(self):

        return PadmissConfig(
            padmiss_api_url='https://api.padmiss.com/',
            stepmania_dir='',
            api_key='',
            scores_dir='',
            backup_dir=self._get_path_inside_padmiss_dir('backups'),
            profile_dir_name='StepMania 5',
            hide_on_start=False,
            webserver=False,
            devices=[]
        )

    def _get_config_path(self):
        if self._custom_config_file_path is not None:
            return self._custom_config_file_path

        return self._get_path_inside_padmiss_dir('config.json')

    def _create_initial_directories_if_necessary(self):
        if self._custom_config_file_path is not None:
            return

        initial_dirs = [
            self._get_path_inside_padmiss_dir(),
            self._get_path_inside_padmiss_dir('backups')
        ]

        root_config_path = self._get_path_inside_padmiss_dir()

        if not os.path.isdir(root_config_path):
            for dir_to_create in initial_dirs:
                log.info('Directory "%s" does not exist, creating', dir_to_create)
                os.makedirs(dir_to_create)

        path = self._get_config_path()
        if not os.path.exists(path):
            log.info('Saving default config')
            self.save_config(self._get_default_config())


    def save_config(self, config):
        folder = self._get_path_inside_padmiss_dir()
        if not os.path.isdir(folder):
            os.makedirs(folder)

        path = self._get_config_path()
        log.info("Saving to: " + path)

        with open(path, 'w') as f:
            f.write(config.json(sort_keys=True, indent=4))

        for f in self.changed:
            f()

    def load_config(self):
        if self.defaultDirs:
            self._create_initial_directories_if_necessary()

        return PadmissConfig.parse_file(self._get_config_path())