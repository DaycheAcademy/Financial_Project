# LogManager & Python Logging — Complete Guide

This document consolidates everything discussed about **LogManager**, using Python’s logging, and the details behind timestamps, `datetime`, and file cleanup logic. It’s designed as a standalone reference and “how‑to”.

---

## Contents

1. [Overview](#overview)  
2. [LogManager Class](#logmanager-class)  
   - [Class responsibilities](#class-responsibilities)  
   - [Configuration precedence](#configuration-precedence)  
   - [LOG_LEVEL mapping](#log_level-mapping)  
3. [Using LogManager](#using-logmanager)  
   - [With ConfigManager](#with-configmanager)  
   - [Without ConfigManager](#without-configmanager)  
4. [Logger Setup Explained](#logger-setup-explained)  
   - [`getLogger`](#getlogger)  
   - [`FileHandler`](#filehandler)  
   - [`StreamHandler`](#streamhandler)  
   - [`addHandler` and clearing duplicates](#addhandler-and-clearing-duplicates)  
   - [Handler vs Logger levels](#handler-vs-logger-levels)  
5. [Timestamped Filenames & Timezones](#timestamped-filenames--timezones)  
   - [Run ID and patterns](#run-id-and-patterns)  
   - [UTC vs local time](#utc-vs-local-time)  
6. [Cleanup of Old Logs](#cleanup-of-old-logs)  
   - [Why compare “smaller” timestamps?](#why-compare-smaller-timestamps)  
   - [Boundary choice: `<` vs `<=`](#boundary-choice--vs-)  
   - [Datetime vs timestamps](#datetime-vs-timestamps)  
   - [Precision, filesystems, and platforms](#precision-filesystems-and-platforms)  
   - [Recursive cleanup & prefix filters](#recursive-cleanup--prefix-filters)  
7. [Recipes & Examples](#recipes--examples)  
   - [Production-style setup function](#production-style-setup-function)  
   - [Rotate by size / time](#rotate-by-size--time)  
   - [Structured (JSON) logs](#structured-json-logs)  
   - [Silencing chatty libraries](#silencing-chatty-libraries)  
8. [Reference Code](#reference-code)  
   - [Final LogManager class (non-dataclass)](#final-logmanager-class-non-dataclass)  
   - [ConfigManager properties](#configmanager-properties)  
   - [Config file example](#config-file-example)  

---

## Overview

**LogManager** provides:
- A **timestamped log file per run** (pattern-driven names).
- A **console handler** for readable terminal output.
- **Configurable** via a `ConfigManager` instance (or constructor args).
- **Cleanup** of old log files based on age.
- Support for **user-defined log levels** and standard Python logging levels.

This guide also explains how Python logging works (root vs named loggers, handlers, formatters), and *why* comparing file modification times with a **“smaller than cutoff”** numeric check is correct and robust.

---

## LogManager Class

### Class responsibilities

- Build a log filename using a **pattern** (e.g., `{prefix}_{run_id}.log`) where `run_id` is `YYYYMMDD_HHMMSS`.
- Configure the **root logger** with:
  - **FileHandler** → detailed logs (DEBUG+).
  - **StreamHandler** → console logs (INFO+ by default, configurable).
- Clear previously attached handlers to avoid **duplicate lines** on re-runs (e.g., notebooks, reloaders).
- Provide a **cleanup** method to delete logs older than `keep_days` safely.
- Accept **ConfigManager** (optional) and read `log_dir`, `log_level`, `log_name_pattern`.
- Accept **user-defined** level names or numbers.

### Configuration precedence

| Source | Priority |
|---|---|
| **Constructor arguments** | Highest |
| **ConfigManager instance** (`cfg`) | Middle |
| **Built-in defaults** | Lowest |

### LOG_LEVEL mapping

The class exposes a mapping for common names:

```python
LOG_LEVEL = {
    'DEBUG':    logging.DEBUG,
    'INFO':     logging.INFO,
    'WARNING':  logging.WARNING,
    'ERROR':    logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}
```

It also accepts custom names (registered via `logging.addLevelName`) and raw numeric values.

---

## Using LogManager

### With ConfigManager

Ensure your `ConfigManager` exposes the following properties:

```python
class ConfigManager:
    @property
    def log_dir(self): return self.config["logging"].get("log_dir", "logs")
    @property
    def log_level(self): return self.config["logging"].get("log_level", "INFO")
    @property
    def log_name_pattern(self): return self.config["logging"].get("log_name_pattern", "{prefix}_{run_id}.log")
```

Then wire it up:

```python
from config_manager import ConfigManager
from log_manager import LogManager
import logging

cfg = ConfigManager("config.cfg")
lm = LogManager(cfg=cfg, prefix="pipeline", console=True, use_utc=True)
log_path, run_id = lm.logger_setup()
logging.info("Logging started | run_id=%s | file=%s", run_id, log_path)

# ... later ...
removed = lm.logger_cleanup(keep_days=7)
logging.info("Old logs removed: %d", removed)
```

### Without ConfigManager

```python
from log_manager import LogManager
import logging

lm = LogManager(base_dir="logs", level="INFO", file_pattern="{prefix}_{run_id}.log")
log_path, run_id = lm.logger_setup()
logging.info("Hello world")
```

Custom levels:

```python
TRACE = 15
logging.addLevelName(TRACE, "TRACE")
lm = LogManager(level="TRACE")   # or level=15
lm.logger_setup()
```

---

## Logger Setup Explained

### `getLogger`

- `logging.getLogger()` with **no name** returns the **root logger** (singleton).
- `logging.getLogger(__name__)` returns a **named logger** and usually lives in each module.
- Configure the **root once** in your app’s entry point; module loggers inherit handlers/levels.

### `FileHandler`

- Emits logs to a **file** path.
- Key args: `mode='a'` (append) vs `'w'` (overwrite), `encoding='utf-8'`, `delay=True` to open lazily.
- Use a detailed formatter for files (timestamp, level, logger name, message).

### `StreamHandler`

- Emits logs to **console** (`sys.stderr` by default; you can pass `sys.stdout`).
- Use a **concise** formatter for readability.

### `addHandler` and clearing duplicates

- A logger can have **multiple handlers** (file + console + …). Use `addHandler` to attach.
- Re-running code may **stack** handlers → duplicate lines. Remove existing handlers first:
  ```python
  root = logging.getLogger()
  for h in list(root.handlers):
      root.removeHandler(h)
  ```

### Handler vs Logger levels

A record is emitted only if it passes **both**:
1. The **logger** (or ancestor) level.
2. The **handler** level.

Typical pattern:
- Root: `INFO`
- FileHandler: `DEBUG` (capture everything)
- StreamHandler: `INFO` or `WARNING` (less noisy in console)

---

## Timestamped Filenames & Timezones

### Run ID and patterns

`run_id = YYYYMMDD_HHMMSS` (UTC by default) is embedded into the filename. The pattern supports tokens:

- `{prefix}` — your app prefix (e.g., `"pipeline"`).
- `{run_id}` — unique per run timestamp.
- `{date}` — `YYYYMMDD`.
- `{time}` — `HHMMSS`.
- `{pid}` — process id.

Default pattern: `{prefix}_{run_id}.log`  
Example: `logs/pipeline_20250905_104533.log`

### UTC vs local time

- `use_utc=True` makes filenames and file timestamps **UTC** (stable across DST).
- Local time is fine if you prefer matching local logs. Be consistent across environments.

To make the **file content timestamps** UTC as well:
```python
fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s – %(message)s")
fmt.converter = time.gmtime
file_handler.setFormatter(fmt)
```

---

## Cleanup of Old Logs

LogManager deletes logs older than `keep_days`.

### Why compare “smaller” timestamps?

- `p.stat().st_mtime` is the file’s **last modification time** as a POSIX timestamp (seconds since epoch).
- A **smaller** number is **earlier in time** (older file).  
- `cutoff_ts` is “now minus keep_days” as a timestamp.  
- So `st_mtime < cutoff_ts` means **file older than keep_days** → delete.

### Boundary choice: `<` vs `<=`

- `<` → keeps files **exactly at** the cutoff (safer).
- `<=` → deletes files exactly at the cutoff.

### Datetime vs timestamps

Comparing **numeric** timestamps avoids timezone issues. If using `datetime` objects, ensure both are either **naive** or **timezone-aware (same tz)**, otherwise Python will raise.

### Precision, filesystems, and platforms

- `st_mtime` is **float seconds**; `st_mtime_ns` gives **nanoseconds**.
- Some filesystems store coarse mtimes (1–2s), affecting exact boundaries slightly.
- On Windows, active file handles may block deletion (handle with try/except; you already do).

### Recursive cleanup & prefix filters

- Use `Path(...).rglob("*.log")` to clean nested folders.
- Optional: delete only files beginning with your prefix:
  ```python
  if not p.name.startswith(f"{prefix}_"):
      continue
  ```

---

## Recipes & Examples

### Production-style setup function

```python
import logging, sys, time
from pathlib import Path
from datetime import datetime, timezone

def setup_logger(level="INFO", log_dir="logs", prefix="app"):
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(log_dir) / f"{prefix}_{run_ts}.log"

    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    root.setLevel(getattr(logging, level))

    fh = logging.FileHandler(log_path, encoding="utf-8")
    ffmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s – %(message)s")
    # ffmt.converter = time.gmtime   # uncomment for UTC timestamps
    fh.setFormatter(ffmt)
    fh.setLevel(logging.DEBUG)
    root.addHandler(fh)

    ch = logging.StreamHandler(sys.stderr)
    cfmt = logging.Formatter("%(levelname)s %(message)s")
    ch.setFormatter(cfmt)
    ch.setLevel(getattr(logging, level))
    root.addHandler(ch)

    return log_path
```

### Rotate by size / time

```python
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

fh = RotatingFileHandler("logs/app.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8")
# or
fh = TimedRotatingFileHandler("logs/app.log", when="midnight", interval=1, backupCount=14, encoding="utf-8")
```

### Structured (JSON) logs

```python
from pythonjsonlogger import jsonlogger  # pip install python-json-logger
fh.setFormatter(jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
```

### Silencing chatty libraries

```python
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
```

---

## Reference Code

### Final LogManager class (non-dataclass)

```python
# log_manager.py
from __future__ import annotations
import logging
import sys
import time
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Tuple, Any


class LogManager:
    LOG_LEVEL = {
        'DEBUG':    logging.DEBUG,
        'INFO':     logging.INFO,
        'WARNING':  logging.WARNING,
        'ERROR':    logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }

    DEFAULT_FILE_PATTERN = "{prefix}_{run_id}.log"
    DEFAULT_FILE_FORMAT = "%(asctime)s %(levelname)s %(name)s – %(message)s"
    DEFAULT_CONSOLE_FORMAT = "%(levelname)s %(message)s"

    def __init__(
        self,
        *,
        cfg: Optional[Any] = None,
        base_dir: Optional[str] = None,
        prefix: str = "app",
        level: "str|int|None" = None,
        file_pattern: Optional[str] = None,
        console: bool = True,
        use_utc: bool = True,
    ) -> None:
        self._cfg = cfg

        cfg_dir = getattr(cfg, "log_dir", None)
        cfg_level = getattr(cfg, "log_level", None)
        cfg_pat = getattr(cfg, "log_name_pattern", None)

        self.base_dir = base_dir or cfg_dir or "logs"
        self.prefix = prefix
        self.level = level if level is not None else (cfg_level if cfg_level is not None else "INFO")
        self.file_pattern = file_pattern or cfg_pat or self.DEFAULT_FILE_PATTERN

        self.console = console
        self.use_utc = use_utc

        self._log_path: Optional[Path] = None
        self._run_id: Optional[str] = None

    def _coerce_level(self, level: "str|int|None") -> int:
        if level is None:
            return logging.INFO
        if isinstance(level, int):
            return level
        name = str(level).upper()
        if name in self.LOG_LEVEL:
            return self.LOG_LEVEL[name]
        mapping = getattr(logging, "getLevelNamesMapping", None)
        if callable(mapping):
            num = mapping().get(name)
            if isinstance(num, int):
                return num
        maybe = logging.getLevelName(name)
        if isinstance(maybe, int):
            return maybe
        return logging.INFO

    def _build_log_path(self) -> tuple[Path, str]:
        now = datetime.now(timezone.utc) if self.use_utc else datetime.now()
        date_s = now.strftime("%Y%m%d")
        time_s = now.strftime("%H%M%S")
        run_id = f"{date_s}_{time_s}"

        filename = (self.file_pattern or self.DEFAULT_FILE_PATTERN).format(
            prefix=self.prefix, run_id=run_id, date=date_s, time=time_s, pid=os.getpid()
        )

        log_dir = Path(self.base_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        return (log_dir / filename, run_id)

    def logger_setup(self) -> tuple[Path, str]:
        self._log_path, self._run_id = self._build_log_path()

        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)

        overall = self._coerce_level(self.level)
        root.setLevel(overall)

        fh = logging.FileHandler(self._log_path, encoding="utf-8")
        ffmt = logging.Formatter(self.DEFAULT_FILE_FORMAT)
        if self.use_utc:
            ffmt.converter = time.gmtime
        fh.setFormatter(ffmt)
        fh.setLevel(logging.DEBUG)
        root.addHandler(fh)

        if self.console:
            ch = logging.StreamHandler(sys.stderr)
            cfmt = logging.Formatter(self.DEFAULT_CONSOLE_FORMAT)
            ch.setFormatter(cfmt)
            ch.setLevel(overall)
            root.addHandler(ch)

        logging.getLogger(__name__).debug(
            "Logger initialized | path=%s | run_id=%s | utc=%s | level=%s",
            self._log_path, self._run_id, self.use_utc, overall
        )
        return self._log_path, self._run_id

    def logger_cleanup(self, keep_days: int = 14, recursive: bool = False) -> int:
        base = Path(self.base_dir)
        if not base.exists():
            return 0

        cutoff_ts = (datetime.now(timezone.utc) - timedelta(days=keep_days)).timestamp()
        it = base.rglob("*.log") if recursive else base.glob("*.log")

        removed = 0
        for p in it:
            try:
                if p.is_file() and p.stat().st_mtime < cutoff_ts:
                    p.unlink(missing_ok=True)
                    removed += 1
            except (PermissionError, FileNotFoundError):
                pass
        return removed

    @property
    def log_path(self) -> Optional[Path]:
        return self._log_path

    @property
    def run_id(self) -> Optional[str]:
        return self._run_id
```

### ConfigManager properties

```python
class ConfigManager:
    @property
    def log_dir(self): return self.config["logging"].get("log_dir", "logs")
    @property
    def log_level(self): return self.config["logging"].get("log_level", "INFO")
    @property
    def log_name_pattern(self): return self.config["logging"].get("log_name_pattern", "{prefix}_{run_id}.log")
```

### Config file example

```ini
[logging]
log_dir = logs
log_level = INFO                  ; or 20, or a custom name you registered with addLevelName
log_name_pattern = {prefix}_{run_id}.log
; optional
; use_utc = true
; console = true
```

---

*End of guide.*
