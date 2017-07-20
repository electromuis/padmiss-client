#!/usr/bin/env python

import usb

devs = usb.core.find(find_all=True)

for dev in devs:
    print repr(dev), 'on bus', dev.bus, 'port', dev.port_number
