# Financial Data Processing & Visualization (Free FMP Endpoints)

A Python + SQL Server pipeline to pull **free** market data from Financial Modeling Prep (FMP) **stable** endpoints, store daily EOD candles, compute daily technical indicators, and generate charts. Includes DB schema, config-driven setup, typed errors, and packaging instructions.

> **Note:** Intraday tables are provided via SQL schema only (no code integration), per requirements.

---

## Table of Contents
1. [Features](#features)  
2. [Free API Endpoints](#free-api-endpoints)  
3. [Architecture](#architecture)  
4. [Project Structure](#project-structure)  
5. [Quick Start](#quick-start)  
6. [Configuration](#configuration)  
7. [Database Setup (Daily/EOD)](#database-setup-dailyeod)  
8. [Intraday SQL Schema (Optional)](#intraday-sql-schema-optional)  
9. [Technical Indicators (Daily)](#technical-indicators-daily)  
10. [Real-Time Updates (Daily Upsert)](#real-time-updates-daily-upsert)  
11. [Logging: Timestamped per Run](#logging-timestamped-per-run)  
12. [Error Handling (ABC Tree)](#error-handling-abc-tree)  
13. [Sibling Packages: Import Patterns](#sibling-packages-import-patterns)  
14. [Install & Packaging](#install--packaging)  
15. [Troubleshooting](#troubleshooting)  
16. [License](#license)

---

## Features
- ✅ **Free endpoints only** (`/stable` base) with provided API key.  
- ✅ **Daily** EOD ingestion (no intraday integration).  
- ✅ **SQL Server** schema with GUID (NEWID) keys, normalized tables, and daily uniqueness constraints.  
- ✅ **Technical indicators** (SMA, EMA) on daily candles.  
- ✅ **Config-driven** via `config.cfg` (ConfigObj).  
- ✅ **Typed errors** using an abstract base class.  
- ✅ **Per-run log file** with timestamped name.  
- ✅ **Packaging** via `setup.py` or `pyproject.toml` + console entry point.

---

## Free API Endpoints
Base URL: `https://financialmodelingprep.com/stable`  
API Key: **`5ukELNLPdcSXENT18kB55rkGA8vzTnoO`** (from prompt; consider storing privately for production)

- `GET /cryptocurrency-list?apikey={key}`  
- `GET /quote?symbol=BTCUSD&apikey={key}`  
- `GET /quote-short?symbol=BTCUSD&apikey={key}` *(preferred for realtime)*  
- `GET /historical-price-eod/full?symbol=BTCUSD&from=YYYY-MM-DD&to=YYYY-MM-DD&apikey={key}`

> **No intraday integration.** See [Intraday SQL Schema (Optional)](#intraday-sql-schema-optional) for future-proof tables.

---

## Architecture
```
┌────────────────┐        ┌───────────────────┐
│ ConfigManager  │        │ Errors (ABC tree) │
│  reads cfg     │        │ typed exceptions  │
└───────┬────────┘        └─────────┬─────────┘
        │                            
┌───────▼────────┐   DataFrame   ┌───▼────────────────┐
│ DataFetcher    │──────────────▶│ DatabaseManager    │
│  (FMP free)    │               │  SQL Server (EOD)  │
└───────┬────────┘               └─────────┬──────────┘
        │                                   
┌───────▼────────┐                          
│ Indicators     │  add SMA/EMA             
└───────┬────────┘                          
        │                                   
┌───────▼────────┐                          
│ Plotter        │  matplotlib PNGs         
└────────────────┘
```

**Modules**
- `config_manager.py` — reads `config.cfg` via ConfigObj.  
- `errors.py` — abstract base error + specific errors.  
- `data_fetcher.py` — uses free `/stable` endpoints.  
- `database_manager.py` — SQL Server connect + EOD upserts.  
- `indicator_calculator.py` — SMA/EMA on daily data.  
- `plotter.py` — save price + indicators chart.  
- `realtime_updater.py` — **daily** upsert using `quote-short` (no intraday).

---

## Project Structure
```
project_root/
├─ src/
│  ├─ __init__.py
│  ├─ config_manager.py
│  ├─ errors.py
│  ├─ data_fetcher.py
│  ├─ database_manager.py
│  ├─ indicator_calculator.py
│  ├─ plotter.py
│  ├─ realtime_updater.py
│  └─ main.py
├─ sql/
│  └─ create_schema.sql
├─ config.example.cfg
├─ requirements.txt
├─ setup.py (or pyproject.toml)
└─ README.md
```

---

## Quick Start
```bash
# 1) Environment
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2) Config
cp config.example.cfg config.cfg
# Edit if needed (API key present from prompt)

# 3) DB schema (SQL Server)
sqlcmd -S localhost -i sql/create_schema.sql

# 4) Run
python -m src.main
# (or after install) fdp-main
```

---

## Configuration
`config.cfg` (INI/ConfigObj). Example (pre-filled with your key):
```ini
[database]
server = .\SQLEXPRESS
database = FinancialData
user = sa
password = P@ssw0rd

[api]
base_url = https://financialmodelingprep.com/stable
key = 5ukELNLPdcSXENT18kB55rkGA8vzTnoO

[logging]
log_level = INFO
log_file  = logs/app.log
```
> For per-run files, see [Logging: Timestamped per Run](#logging-timestamped-per-run).

---

## Database Setup (Daily/EOD)
Minimal script (also in `sql/create_schema.sql`):
```sql
CREATE DATABASE FinancialData;
GO
USE FinancialData;
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'Finance')
    EXEC('CREATE SCHEMA Finance');
GO

CREATE TABLE Finance.Symbols(
  ID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
  SymbolName VARCHAR(50) NOT NULL,
  Description VARCHAR(255)
);

CREATE TABLE Finance.HistoricalPrices(
  ID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
  SymbolID UNIQUEIDENTIFIER NOT NULL,
  PriceDate DATE NOT NULL,
  OpenPrice  DECIMAL(18,4),
  HighPrice  DECIMAL(18,4),
  LowPrice   DECIMAL(18,4),
  ClosePrice DECIMAL(18,4),
  Volume     BIGINT,
  CONSTRAINT FK_HPrices_Symbols FOREIGN KEY(SymbolID) REFERENCES Finance.Symbols(ID)
);

CREATE UNIQUE INDEX IX_HPrices_Symbol_Date
  ON Finance.HistoricalPrices(SymbolID, PriceDate);

CREATE TABLE Finance.TechnicalIndicators(
  ID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
  SymbolID UNIQUEIDENTIFIER NOT NULL,
  IndicatorName VARCHAR(50) NOT NULL,
  CalculationDate DATE NOT NULL,
  Value DECIMAL(18,4) NOT NULL,
  CONSTRAINT FK_TechInd_Symbols FOREIGN KEY(SymbolID) REFERENCES Finance.Symbols(ID)
);
```

---

## Intraday SQL Schema (Optional)
**No code integration** — schema ready for future use:

```sql
/* Intervals */
IF OBJECT_ID('Finance.IntradayIntervals','U') IS NULL
CREATE TABLE Finance.IntradayIntervals(
  IntervalSec  INT PRIMARY KEY,       -- 60, 300, 3600
  IntervalName VARCHAR(16) UNIQUE     -- '1min','5min','1hour'
);
MERGE Finance.IntradayIntervals AS tgt
USING (VALUES (60,'1min'),(300,'5min'),(3600,'1hour')) AS src(IntervalSec,IntervalName)
ON tgt.IntervalSec=src.IntervalSec
WHEN NOT MATCHED THEN INSERT(IntervalSec,IntervalName) VALUES(src.IntervalSec,src.IntervalName);

/* Intraday bars */
IF OBJECT_ID('Finance.IntradayBars','U') IS NULL
CREATE TABLE Finance.IntradayBars(
  ID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
  SymbolID   UNIQUEIDENTIFIER NOT NULL,
  IntervalSec INT NOT NULL,
  BarStart   DATETIME2(0) NOT NULL,   -- UTC
  OpenPrice  DECIMAL(18,4) NULL,
  HighPrice  DECIMAL(18,4) NULL,
  LowPrice   DECIMAL(18,4) NULL,
  ClosePrice DECIMAL(18,4) NULL,
  Volume     BIGINT NULL,
  Source     VARCHAR(32) NULL DEFAULT 'FMP',
  IngestedAt DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
  CONSTRAINT FK_IntraBars_Symbols   FOREIGN KEY(SymbolID) REFERENCES Finance.Symbols(ID),
  CONSTRAINT FK_IntraBars_Intervals FOREIGN KEY(IntervalSec) REFERENCES Finance.IntradayIntervals(IntervalSec)
);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='UX_IntraBars_Symbol_Interval_Start' AND object_id=OBJECT_ID('Finance.IntradayBars'))
  CREATE UNIQUE INDEX UX_IntraBars_Symbol_Interval_Start ON Finance.IntradayBars(SymbolID, IntervalSec, BarStart);
```

---

## Technical Indicators (Daily)
- **SMA** (window in days)  
- **EMA** (span in days)  
- Extendable to RSI/MACD using daily candles only.

Example usage outline:
```python
from indicator_calculator import SMACalculator, EMACalculator

df = SMACalculator(10).calculate(df)
df = EMACalculator(21).calculate(df)
```

---

## Real-Time Updates (Daily Upsert)
- Prefer `GET /quote-short?symbol=BTCUSD&apikey={key}`.  
- Daily rule: upsert one row per `(SymbolID, PriceDate)` using the quote price as same-day OHLC until EOD file refresh.

---

## Logging: Timestamped per Run
Add a rotating filename per run:
```python
from datetime import datetime, timezone
from pathlib import Path
import logging

def setup_run_logger(level="INFO", base_dir="logs", prefix="app"):
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(base_dir) / f"{prefix}_{run_ts}.log"
    root = logging.getLogger()
    for h in list(root.handlers): root.removeHandler(h)
    root.setLevel(getattr(logging, level))
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s – %(message)s"))
    root.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    root.addHandler(ch)
    return log_path
```

---

## Error Handling (ABC Tree)
```python
import abc

class ProjectBaseError(Exception, metaclass=abc.ABCMeta):
    """Root for project errors"""

class DatabaseConnectionError(ProjectBaseError): pass
class DataFetchError(ProjectBaseError): pass
class RealTimeUpdateError(ProjectBaseError): pass
```

---

## Sibling Packages: Import Patterns
**Scenario:** `conf/` needs to import from sibling `exceptions/`.

1) **Top-level package + absolute imports (recommended)**  
```
myapp/conf/module_a.py → from myapp.exceptions.errors import DataFetchError
```
Run: `python -m myapp.conf.module_a`

2) **Relative imports** (when both under same parent)  
```
from ..exceptions.errors import DataFetchError
```
Run as package module: `python -m myapp.conf.module_a`

3) **No common parent (temporary)**  
Set `PYTHONPATH=.` and run `python -m conf.module_a` from the project root.

4) **Last resort**: tweak `sys.path` (brittle).

---

## Install & Packaging
### Option A: `setup.py` (classic)
```bash
pip install -e .
fdp-main
```

### Option B: `pyproject.toml` (modern)
```bash
pip install -e .
# or
python -m build
```

Console script entry: `fdp-main → main:main`

---

## Troubleshooting
- **“does not appear to be a Python project”** — add `setup.py` or `pyproject.toml` to the **project root** and run from there.  
- **Import errors between sibling packages** — ensure `__init__.py`, run with `python -m`, or set `PYTHONPATH=.`.  
- **ODBC driver issues** — install Microsoft **ODBC Driver 17/18** for SQL Server (`pyodbc`).  
- **Empty data** — verify API base and key, date ranges, and symbol (“BTCUSD”).

---

## License
MIT © 2025 Your Name
