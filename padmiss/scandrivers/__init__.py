from typing import Optional

from pydantic import BaseModel, create_model
import importlib

drivers = {}

def loadConfigSchema():
    driverNames = [
        'fifo',
        'hid',
        'fs',
        'usb',
        'web'
    ]

    for n in driverNames:
        drivers[n] = importlib.import_module('.' + n, package=__package__)

    class DeviceConfigBase(BaseModel):
        path: str
        type: Optional[str]

    modelInfo = {
        'model_name': 'DeviceConfig',
        '__base__': DeviceConfigBase
    }

    for k, module in drivers.items():
        if not hasattr(module, 'ReaderConfig'):
            continue

        configProp = k + '_config'
        if hasattr(module, 'configProp'):
            configProp = getattr(module, 'configProp')
        else:
            drivers[k].configProp = configProp

        modelInfo[configProp] = module.ReaderConfig.emptyInstance()

    return create_model(**modelInfo)

import logging
log = logging.getLogger(__name__)

def construct_reader(device, poller):
    reader = False

    type = device.type
    if type == 'scanner':
        type = 'hid'

    if type in drivers:
        try:
            reader = drivers[type].Reader(device, poller)
        except Exception as e:
            log.debug('Failed constructing:' + type + ', ' + str(e) + str(e.__traceback__))
            reader = False
    else:
        log.debug(drivers)
        log.debug('Unknown type:' + type)

    return reader