from configobj import ConfigObj
from pathlib import Path

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
    def __init__(self, path: str = 'config.cfg'):
        cfg_path = Path(path)
        if not cfg_path.exists():
            raise ConfigFileNotFound(message=f'file {cfg_path} not found')
        self.config = ConfigObj(cfg_path)


    def database_server(self):
        return self.config['database']['server']



if __name__ == '__main__':
    for elem in sys.path:
        print(elem)
    print('===============')
    for p in (Path(__file__)).resolve().parents:
        print(p)


# sibling package error

