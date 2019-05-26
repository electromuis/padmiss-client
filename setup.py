import sys
import os
import json
import logging

from pprint import pprint
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup

if os.name == 'nt':
    from hidwin import listDevices
else:
    from hid import listDevices

from config import PadmissConfigManager

class MyApp(App):
    def findReader(self, num):
        layout = BoxLayout(orientation='vertical', height=80)
        label = Label(text='Make sure the scanner is disconnected')
        layout.add_widget(label)
        button = Button(text='Ok')
        self.devices = None
        self.failed = False
        popup = None

        def f1(x):
            if self.failed == True:
                self.failed = False
                popup.dismiss()
            if self.devices == None:
                self.devices = listDevices()
                label.text = 'Connect the scanner now'
            else:
                newDevices = listDevices()
                new = [x for x in newDevices if x not in self.devices]
                if new:
                    self.readers[num] = new[0]
                    self.scannerButtons[num].text = 'Find reader (Found)'
                    popup.dismiss()
                else:
                    label.text = 'Reader not found'
                    button.text = 'Close'
                    self.scannerButtons[num].text = 'Find reader'
                    self.failed = True


        button.bind(on_press=f1)
        label.add_widget(button)

        popup = Popup(title='Find reader', content=layout, auto_dismiss=False)

        popup.open()

    def build(self):
        self.config_manager = PadmissConfigManager()
        self.config = self.config_manager.load_config()

        self.scannerButtons = {}
        self.textElements = {'profile': {}}
        self.readers = {}

        layout = BoxLayout(orientation='vertical')

        subLayout = BoxLayout(orientation='horizontal')
        subLayout.add_widget(Label(text='Token', size_hint_max_x=200))
        token = TextInput()
        token.text = self.config.apikey
        token.hint_text = "abc123acb123"
        self.textElements['apikey'] = token
        subLayout.add_widget(token)
        subLayout.size_hint_min_y = 30
        layout.add_widget(subLayout)

        subLayout = BoxLayout(orientation='horizontal')
        subLayout.add_widget(Label(text='Padmiss score dir', size_hint_max_x=200))
        scores = TextInput()
        scores.text = self.config.scores_dir
        scores.hint_text = "SM5DIR/Save/Padmiss"
        self.textElements['scores_dir'] = scores
        subLayout.add_widget(scores)
        subLayout.size_hint_min_y = 30
        layout.add_widget(subLayout)

        for i in [1, 2]:
            def readerF(x):
                self.findReader(i)

            subLayout = BoxLayout(orientation='horizontal')
            subLayout.add_widget(Label(text='Profile ' + str(i), size_hint_max_x=200))
            reader = Button(text='Find reader')
            reader.bind(on_press=readerF)
            self.scannerButtons[i] = reader
            subLayout.add_widget(reader)
            subLayout.size_hint_min_y = 30
            folder = TextInput()
            if i-1 in enumerate(self.config.scanners):
                folder.text = self.config.scanners[i-1]['path']
            folder.hint_text = 'C:\playerX'
            self.textElements["profile"][i] = folder
            subLayout.add_widget(folder)
            layout.add_widget(subLayout)

        save = Button(text= 'Save')
        save.size_hint_min_y = 50
        save.bind(on_press=self.save)
        layout.add_widget(save)

        return layout

    def save(self):
        values = {
            'url': 'https://api.padmiss.com',
            'backup_dir': os.path.dirname(os.path.realpath(__file__)) + os.sep + "backup",
            'scores_dir ': '',
            'apikey ': '',
            'profile_dir': 'StepMania 5',
            'scanners': {1: None, 2: None}
        }
        
        pprint(self.textElements)
        pprint(self.readers)

        # for name,e in self.textElements.iteritems():
        #     if name == "profile":
        #         for i,elm in e.iteritems():
        #             values['scanners'][i]
        #             elm.text
        #             self.readers[i]

        #     else:
        #         if e.text:
        #             values[name] = e.text

        # with open('config.json', 'w') as the_file:
        #     the_file.write(json.dumps(values))

if __name__ == '__main__':
    from kivy.config import Config
    Config.set('graphics', 'width', '800')
    Config.set('graphics', 'height', '170')
    Config.write()

    MyApp().run()
