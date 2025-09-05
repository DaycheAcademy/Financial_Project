from configobj import ConfigObj
from pathlib import Path
import logging

# best practice (absolute path)
from dayche.exceptions import ConfigFileNotFound

# # relative path
# from ..exceptions import ConfigFileNotFound


# sys.path tweaking
# import sys
# sys.path.append(str(Path(__file__).resolve().parents[1]))
# from exceptions import ConfigFileNotFound


# using setup.py OR pyproject.toml


class ConfigManager(object):

    LOG_LEVEL = {'DEBUG': logging.DEBUG,
                 'INFO': logging.INFO,
                 'WARNING': logging.WARNING,
                 'ERROR': logging.ERROR,
                 'CRITICAL': logging.CRITICAL}

    def __init__(self, path: str = 'config.cfg'):
        cfg_path = Path(path)
        if not cfg_path.exists():
            raise ConfigFileNotFound(message=f'file {cfg_path} not found')
        self.config = ConfigObj(cfg_path)


    @property
    def database_server(self):
        return self.config['database']['server']

    @property
    def database_name(self):
        return self.config['database']['name']

    @property
    def database_user(self):
        return self.config['database']['user']

    @property
    def database_password(self):
        return self.config['database']['password']

    @property
    def api_key(self):
        return self.config['api']['api_key']

    @property
    def api_url(self):
        return self.config['api']['api_url']

    @property
    def log_dir(self):
        return self.config['log'].get('log_dir', './logs')

    @property
    def log_name_pattern(self):
        return self.config['log'].get('log_name_pattern', 'app_{run_id}.log')

    @property
    def log_level(self):
        return self.config['log'].get('log_level', 'INFO')




if __name__ == '__main__':
    for elem in sys.path:
        print(elem)
    print('===============')
    for p in (Path(__file__)).resolve().parents:
        print(p)


# sibling package error

