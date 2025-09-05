# Python Logging: `getLogger`, `FileHandler`, `addHandler`, `StreamHandler`

This guide explains how Python's logging pieces fit together — and specifically what **`getLogger`**, **`FileHandler`**, **`addHandler`**, and **`StreamHandler`** do — with ready‑to‑paste patterns.

---

## Logging model in a nutshell

- **Logger** — where you log messages (`logger.info(...)`). There is a special **root** logger obtained via `logging.getLogger()` with no name. Named loggers (e.g., `logging.getLogger("myapp.db")`) inherit settings from the root unless you override them.
- **Handler** — where records go: file, console, HTTP, syslog, etc. You can attach **multiple** handlers to one logger.
- **Formatter** — how a record becomes text (timestamp, level, message, etc.).
- **Filter** (optional) — include/exclude logic for records.
- **Levels** — `DEBUG < INFO < WARNING < ERROR < CRITICAL`. A record must pass **both** the logger’s level **and** the handler’s level to be emitted.

---

## `logging.getLogger()`

```python
root = logging.getLogger()            # root logger (unnamed)
app  = logging.getLogger("myapp")     # named logger
mod  = logging.getLogger(__name__)    # per‑module logger (best practice)
```

- The **root logger** controls defaults for everything that propagates to it.
- Named loggers **propagate** to their parent (ultimately the root) unless `logger.propagate = False`.
- Configure **once** at the entry point (often the root); use `logging.getLogger(__name__)` inside modules.

---

## `FileHandler` — write logs to a file

```python
fh = logging.FileHandler("logs/app_20250905_101500.log", mode="a", encoding="utf-8")
fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s – %(message)s")
fh.setFormatter(fmt)
fh.setLevel(logging.DEBUG)     # file captures everything
```

**Key args**

- `filename`: path to the log file (create parent dirs first).
- `mode`: `'a'` append (default) or `'w'` overwrite.
- `encoding`: usually `'utf-8'`.
- `delay=True`: open file on first use (optional).

**Useful variants**

- `logging.handlers.RotatingFileHandler(maxBytes=10_000_000, backupCount=5)` — rotate by size.
- `logging.handlers.TimedRotatingFileHandler(when="midnight", interval=1, backupCount=7)` — rotate by time.

---

## `StreamHandler` — write logs to console (stdout/stderr)

```python
import sys
ch = logging.StreamHandler(sys.stderr)  # default is stderr
cfmt = logging.Formatter("%(levelname)s %(message)s")
ch.setFormatter(cfmt)
ch.setLevel(logging.INFO)               # console shows INFO+
```

- Use `sys.stdout` if you want logs to standard output (e.g., container logs).
- Keep console format concise; keep the file detailed.

---

## `addHandler` — attach sinks to a logger

```python
root = logging.getLogger()
root.addHandler(fh)  # file
root.addHandler(ch)  # console
```

- You can attach **multiple handlers** (e.g., file + console + external service).
- Records pass through **each** handler that permits their level.

**Avoid duplicates** when re-running (e.g., notebooks/reloaders):

```python
root = logging.getLogger()
for h in list(root.handlers):
    root.removeHandler(h)
```

---

## Level flow & propagation

```python
root.setLevel(logging.DEBUG)       # global min level
fh.setLevel(logging.DEBUG)         # file gets everything
ch.setLevel(logging.WARNING)       # console only warnings+
```

A record must pass:
1) the **emitting logger’s** level (or its ancestors’ levels), **and**
2) the **handler’s** level.

If a library is too chatty:
```python
logging.getLogger("urllib3").setLevel(logging.WARNING)
```

To stop propagation to the root (rare but useful):
```python
logger = logging.getLogger("myapp.verbose")
logger.propagate = False
```

---

## Production‑style setup (copy/paste)

```python
import logging, sys, time
from pathlib import Path
from datetime import datetime, timezone

def setup_logger(level="INFO", log_dir="logs", prefix="app"):
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(log_dir) / f"{prefix}_{run_ts}.log"

    root = logging.getLogger()

    # clear handlers to avoid duplicates on re-runs
    for h in list(root.handlers):
        root.removeHandler(h)

    root.setLevel(getattr(logging, level))

    # file handler (detailed)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    ffmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s – %(message)s")
    # optional: UTC timestamps in the file
    # ffmt.converter = time.gmtime
    fh.setFormatter(ffmt)
    fh.setLevel(logging.DEBUG)
    root.addHandler(fh)

    # console handler (concise)
    ch = logging.StreamHandler(sys.stderr)
    cfmt = logging.Formatter("%(levelname)s %(message)s")
    ch.setFormatter(cfmt)
    ch.setLevel(logging.INFO)
    root.addHandler(ch)

    return log_path
```

- Creates a **timestamped file per run** (UTC-safe) and logs to console.
- Use handler levels to control verbosity per sink.

---

## Patterns & recipes

**Per-run files with local timestamps**  
Replace `datetime.now(timezone.utc)` with `datetime.now()` if you prefer local time in the filename.

**Rotate logs by size**  
```python
from logging.handlers import RotatingFileHandler
fh = RotatingFileHandler("logs/app.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8")
```

**Rotate logs nightly**  
```python
from logging.handlers import TimedRotatingFileHandler
fh = TimedRotatingFileHandler("logs/app.log", when="midnight", interval=1, backupCount=14, encoding="utf-8")
```

**Structured (JSON) logs**  
```python
from pythonjsonlogger import jsonlogger  # pip install python-json-logger
fh.setFormatter(jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
```

**Silence third‑party modules**  
```python
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
```

**Windows notes**  
- Ensure the directory exists before creating `FileHandler`.
- On Windows, files can be locked by other processes; use rotating handlers carefully.

---

## Common pitfalls

- **Duplicate output**: adding handlers multiple times (fix: clear them first).
- **Nothing appears**: the logger level or handler level is too high.
- **File not created**: parent directory missing or insufficient permissions.
- **Timezones**: `%(asctime)s` uses local time; set a UTC converter if required.
- **Running inside reloaders/notebooks**: always clear handlers to avoid repeated lines.

---

## TL;DR

- `getLogger()` — get the root or a named logger; configure at the app entry point.
- `FileHandler` — write logs to a file; set a detailed formatter and (optionally) rotation.
- `StreamHandler` — write logs to console; set a concise formatter; choose stderr/stdout.
- `addHandler` — attach one or more sinks; clear old handlers to avoid duplicates.

With these, you can build a reliable, production‑ready logging setup in a few lines.
