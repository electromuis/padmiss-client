import sys
import os
import json
import logging
import pystray
import threading

# before kivy imports
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format=' %(threadName)s %(name)s - %(levelname)s: %(message)s')

from kivy.app import App
from kivy.uix.label import Label
from pystray import Menu, MenuItem

from PIL import Image, ImageDraw


def start_tray_application(menu):
    icon = pystray.Icon('Padmiss', title="Padmiss", menu=menu)

    def setup(self):
        icon.visible = True

    # Generate a silly image
    width = 32
    height = 32
    color1 = '#000'
    color2 = '#fff'
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle((width // 2, 0, width, height // 2), fill=color2)
    dc.rectangle((0, height // 2, width // 2, height), fill=color2)
    icon.icon = image

    icon.run(setup)


class PadmissGUI(App):
    def build(self):
        return Label(text='Hello world')


class GUIThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._padmiss_gui = PadmissGUI()

    def run(self):
        self._padmiss_gui.run()
    
    def stop(self):
        self._padmiss_gui.stop()


if __name__ == '__main__':
    padmiss_gui = None

    def show_gui():
        padmiss_gui = GUIThread()
        padmiss_gui.daemon = True
        padmiss_gui.run()

    def quit_app(icon):
        if padmiss_gui:
            padmiss_gui.stop()
        icon.stop()

    menu = Menu(
        MenuItem('Settings...', show_gui),
        MenuItem('Quit', quit_app)
    )

    start_tray_application(menu=menu)