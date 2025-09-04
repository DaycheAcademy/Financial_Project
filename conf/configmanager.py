from configobj import ConfigObj
from pathlib import Path


class ConfigManager(object):
    def __init__(self, path: str = 'config.cfg'):
        cfg_path = Path(path)
        if not cfg_path.exists():
            raise FileNotFoundError(f'config file {path} not found')
        self.config = ConfigObj(cfg_path)


    def database_server(self):
        return self.config['database']['server']





