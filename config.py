from collections import namedtuple
import json
import os
import sys
import logging

log = logging.getLogger(__name__)

PadmissConfig = namedtuple('PadmissConfig', (
    'url',
    'apikey',
    'scores_dir',
    'backup_dir',
    'profile_dir',
    'scanners'
))

class PadmissConfigManager(object):
    def __init__(self, custom_config_file_path=None):
        self._custom_config_file_path = custom_config_file_path

    def _get_path_inside_padmiss_dir(self, *path):
        if os.name == 'nt':
            return os.path.join(os.getenv('APPDATA'), 'Padmiss', *path)
        else:
            return os.path.join(expanduser('~'), '.padmiss', *path)

    def _get_default_config(self):
        return PadmissConfig(
            url='https://api.padmiss.com/',
            apikey='',
            scores_dir=self._get_path_inside_padmiss_dir('scores'),
            backup_dir=self._get_path_inside_padmiss_dir('backups'),
            profile_dir='StepMania 5',
            scanners=[]
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
            self._get_path_inside_padmiss_dir('scores'),
            self._get_path_inside_padmiss_dir('backups')
        ]

        root_config_path = self._get_path_inside_padmiss_dir()

        if not os.path.isdir(root_config_path):
            for dir_to_create in initial_dirs:
                log.info('Directory "%s" does not exist, creating', dir_to_create)
                os.makedirs(dir_to_create)

            log.info('Saving default config')
            self.save_config(self._get_default_config())

    def save_config(self, config):
        path = self._get_config_path()

        with open(path, 'w') as f:
            # https://stackoverflow.com/a/15800273
            f.write(json.dumps(config._asdict()))

    def load_config(self):
        self._create_initial_directories_if_necessary()
        path = self._get_config_path()

        with open(path) as c:
            data = json.load(c)
            return PadmissConfig(**data)
