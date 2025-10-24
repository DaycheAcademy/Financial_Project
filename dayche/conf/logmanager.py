from .configmanager import ConfigManager
import logging
import os
from datetime import datetime, timedelta, timezone
# from typing import Any


class LogManager(object):
    """
    create timestamped filename from a pattern
    configure a logger (root logger) with FileHandler + StreamHandler
    clean up old log files (passed a certain timestamp threshold)

    priority: input argument > config file > default value
    """

    LOG_LEVEL = {'DEBUG': logging.DEBUG,
                 'INFO': logging.INFO,
                 'WARNING': logging.WARNING,
                 'ERROR': logging.ERROR,
                 'CRITICAL': logging.CRITICAL}

    DEFAULT_FILE_PATTERN = "{prefix}_{run_id}_{pid}.log"
    DEFAULT_FILE_FORMAT = "%(asctime)s ; %(levelname)s ; %(name)s - %(message)s)"
    DEFAULT_CONSOLE_FORMAT = "%(levelname)s - %(message)s)"

    def __init__(
            self,
            prefix: str = "app",
            level: str|int|None = 'INFO',
            base_dir: str = None,
            file_pattern: str = None,
            console = False) -> None:

        self.cfg = ConfigManager()
        self.prefix = prefix
        self.console = console

        # pulling values from config file
        cfg_dir = getattr(self.cfg, "log_dir", None)  # self.cfg.log_dir
        cfg_level = getattr(self.cfg, "log_level", None)
        cfg_pattern = getattr(self.cfg, "log_name_pattern", None)

        # applying precedences
        self.base_dir = base_dir or cfg_dir or 'logs'
        self.level = level if level else cfg_level if cfg_level else 'INFO'
        self.file_pattern = file_pattern or cfg_pattern or self.DEFAULT_FILE_PATTERN


    def _resolve_level(self, level=None) -> int:
        if not level:
            return logging.INFO
        if isinstance(level, int):
            return level
        if str(level).upper() in LogManager.LOG_LEVEL:
            return LogManager.LOG_LEVEL[str(level).upper()]

        mapping = getattr(logging, "getLevelNamesMapping", None)
        if callable(mapping):
            N = mapping().get(name)
            if isinstance(N, int):
                return N

        return logging.INFO


    def _build_log_path(self):
        now = datetime.now(timezone.utc)  # datetime.now()
        date_s = now.strftime("%Y%m%d")
        time_s = now.strftime("%H%M%S")
        run_id = f'{date_s}_{time_s}'
        file_name = self.file_pattern.format(prefix=prefix,
                                             run_id=run_id,
                                             pid=os.getpid())
        log_dir = Path(self.base_dir)
        log_dir.mkdir(exist_ok=True, parents=True)
        return log_dir / file_name, run_id

    def logger_setup(self):
        _log_path, _run_id = self._build_log_path()
        root = logging.getLogger()

        for handler in root.handlers:
            root.removeHandler(handler)

        _level = self._resolve_level(self.level)
        root.setLevel(_level)

        fh = logging.FileHandler(_log_path, encoding='utf-8')
        fhff = logging.Formatter(self.DEFAULT_FILE_FORMAT)
        fh.setFormatter(fhff)
        fh.setLevel(logging.DEBUG)
        root.addHandler(fh)

        if self.console:
            sh = logging.StreamHandler()
            shcf = logging.Formatter(self.DEFAULT_CONSOLE_FORMAT)
            sh.setFormatter(shcf)
            sh.setLevel(_level)
            root.addHandler(sh)

        logging.getLogger(__name__).debug(
            "Logger initialized | path={} | run_id={} | prefix={} | level={}".format(
                _log_path, _run_id, self.prefix, _level
            )
        )

        return _log_path, _run_id


    def logger_cleanup(self, keep_days: int = 14, recursive: bool = False) -> int:
        base = Path(self.base_dir)
        if not base.exists():
            return 0

        cut_off_ts = (datetime.now(timezone.utc) - timedelta(days=keep_days)).timestamp()
        lf = base.rglob("*.log") if recursive else base.glob("*.log")

        file_removed = 0
        for f in lf:
            try:
                if f.is_file() and f.stat().st_mtime < cut_off_ts:
                    f.unlink(missing_ok=True)
                    file_removed += 1
            except PermissionError:
                pass
            except FileNotFoundError:
                pass

        return file_removed









