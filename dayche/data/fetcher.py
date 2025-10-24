import abc
from typing import Iterable, Dict, List, Any, Iterable, Tuple, Mapping, Hashable

from dayche.conf.logmanager import LogManager
from dayche.conf.configmanager import ConfigManager
from dayche.exceptions.cryptoexceptions import *
from dayche.database.connection import PyMSSQLClient

import requests
import logging
from urllib.parse import urlparse, urlsplit, urlunsplit



class CryptoFetcherBase(abc.ABC):
    """

    """

    def __init__(self, autocommit: bool = False, console_log: bool = False) -> None:
        pass

    @abc.abstractmethod
    def fetch_ohlcv(self, symbol: str, **kwargs):
        pass

    @abc.abstractmethod
    def store_historical(self, symbol: str, rows: Iterable[Dict[str, Any]], **kwargs):
        pass

    @abc.abstractmethod
    def fetch_intraday(self, symbol: str, interval_seconds: int = 60, **kwargs) -> List[Dict[str, Any]]:
        pass

    @abc.abstractmethod
    def store_intraday(self, symbol: str, rows: Iterable[Dict[str, Any]], interval_seconds: int = 60) -> None:
        pass


class CryptoAPIFetcher(CryptoFetcherBase):
    """
    Concrete class using JSON API to fetch data from financialmodelingprep.com
    """
    def __init__(self, autocommit: bool = False, console_log: bool = False) -> None:
        self.lm = LogManager(prefix='data', console=console_log)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cfg = ConfigManager()
        self.db = PyMSSQLClient(autocommit=autocommit)
        self.db.connect_sql_auth(
            server=self.cfg.database_server,
            database=self.cfg.database_name,
            user=self.cfg.database_user,
            password=self.cfg.database_password
        )

    # --------- helper methods ---------


    def _get_base_url(self) -> str:
        base = getattr(self.cfg, 'api_url', None)
        if not base:
            raise APIURLNotFound("API base URL not found | not configured in configuration file")
        return str(base).rstrip('/')

    def _full_path(self, base: str, wanted_tail: str) -> str:
        """
        this is to return full API path:
        https://financialmodelingprep.com/stable/historical*
        """
        scheme, netloc, path, query, fragment = urlsplit(base)
        path = path.rstrip('/')
        if path.endswith('stable'):
            final_path = f"{path}/{wanted_tail.lstrip('/')}"
        else:
            final_path = f"{path}/stable/{wanted_tail.lstrip('/')}"
        return urlunsplit((scheme, netloc, final_path, query, fragment))



    def fetch_ohlcv(self, symbol: str, **kwargs):
        pass

    def store_historical(self, symbol: str, rows: Iterable[Dict[str, Any]], **kwargs):
        pass

    def fetch_intraday(self, symbol: str, interval_seconds: int = 60, **kwargs) -> List[Dict[str, Any]]:
        pass

    def store_intraday(self, symbol: str, rows: Iterable[Dict[str, Any]], interval_seconds: int = 60) -> None:
        pass


if __name__ == '__main__':
    caf = CryptoAPIFetcher()
    print(caf._get_base_url())



