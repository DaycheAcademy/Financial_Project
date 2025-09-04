from configobj import ConfigObj
from pathlib import Path
# from exceptions import ConfigFileNotFound
import sys

# # tweaking sys.path
# sys.path.append(str(Path(__file__).resolve().parents[1]))
# from exceptions import ConfigFileNotFound

# using setup.py OR pyproject.toml

# best practice (absolute path)
from dayche.exceptions import ConfigFileNotFound

# relative import
from ..exceptions import ConfigFileNotFound


class ConfigManager(object):
    def __init__(self, path: str = 'config.cfg'):
        cfg_path = Path(path)
        if not cfg_path.exists():
            raise FileNotFoundError(f'config file {path} not found')
        self.config = ConfigObj(cfg_path)


    def database_server(self):
        return self.config['database']['server']


if __name__ == '__main__':
    print(sys.path)

    for elem in (Path(__file__).resolve().parents):
        print(elem)
# sibling package


