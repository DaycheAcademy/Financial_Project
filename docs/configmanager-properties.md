# Why use `@property` in `ConfigManager`?

This note explains *why* `@property` is used on the accessor methods in `ConfigManager`, what you gain from it, and practical alternatives if you prefer a different style.

---

## Benefits of `@property`

- **Clean, attribute-like access**  
  `cfg.api_key` is clearer than `cfg.config['api']['key']`, while still reading from the config file.

- **Read-only semantics**  
  Configuration is typically not mutated at runtime. Properties make that intention clear. Attempting to assign `cfg.api_key = ...` raises by default.

- **Inline validation & normalization**  
  Each getter can validate values (e.g., non-empty key), coerce types, and normalize formats (`rstrip('/')`, upper-casing levels) without changing any calling code.

- **Refactor-friendly interface**  
  If you switch from ConfigObj to environment variables, a secrets manager, or Pydantic, callers keep using `cfg.api_key` without changes.

- **Computed fields**  
  Properties can derive values (e.g., building a base URL) transparently.

- **Optional hot‑reload**  
  If you re-read the file, a property always fetches the current value (instead of a stale cached attribute).

> Overhead is negligible for typical config reads.

---

## Trade‑offs

- **Tiny call overhead** compared to a plain attribute (usually irrelevant).
- **Avoid heavy side-effects** inside getters. If a getter must do I/O repeatedly, consider caching (see below).

---

## Patterns

### 1) Current pattern — read‑only, validated

```python
class ConfigManager:
    def __init__(self, path='config.cfg'):
        from configobj import ConfigObj
        self.config = ConfigObj(path)

    @property
    def api_base_url(self) -> str:
        return self.config['api'].get('base_url', 'https://financialmodelingprep.com/stable').rstrip('/')

    @property
    def api_key(self) -> str:
        key = self.config['api']['key']
        if not key:
            raise ValueError('API key missing in [api].key')
        return key

    @property
    def log_level(self) -> str:
        lvl = self.config['logging'].get('log_level', 'INFO').upper()
        if lvl not in {'DEBUG','INFO','WARNING','ERROR','CRITICAL'}:
            raise ValueError(f'Invalid log_level: {lvl}')
        return lvl
```

**When to use:** prefer simple, validated, read-only access.

---

### 2) Cache once — `cached_property`

If values won’t change during the run, cache them after first access.

```python
from functools import cached_property

class ConfigManager:
    def __init__(self, path='config.cfg'):
        from configobj import ConfigObj
        self.config = ConfigObj(path)

    @cached_property
    def api_base_url(self) -> str:
        return self.config['api'].get('base_url', 'https://financialmodelingprep.com/stable').rstrip('/')

    @cached_property
    def api_key(self) -> str:
        key = self.config['api']['key']
        if not key:
            raise ValueError('API key missing')
        return key
```

**When to use:** reduce repeated parsing or normalization cost.

---

### 3) Plain attributes (no properties)

```python
class ConfigManager:
    def __init__(self, path='config.cfg'):
        from configobj import ConfigObj
        cfg = ConfigObj(path)
        self.database_server = cfg['database']['server']
        self.database_name   = cfg['database']['database']
        self.database_user   = cfg['database']['user']
        self.database_password = cfg['database']['password']

        self.api_base_url = cfg['api'].get('base_url', 'https://financialmodelingprep.com/stable').rstrip('/')
        self.api_key      = cfg['api']['key']

        self.log_level = cfg['logging'].get('log_level','INFO').upper()
        self.log_file  = cfg['logging']['log_file']
```

**Pros:** simplest, zero call overhead.  
**Cons:** later validation/normalization changes require touching callers or adding wrappers.

---

### 4) Strong typing with `dataclasses`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    database_server: str
    database_name: str
    database_user: str
    database_password: str
    api_base_url: str
    api_key: str
    log_level: str
    log_file: str

class ConfigManager:
    def __init__(self, path='config.cfg'):
        from configobj import ConfigObj
        cfg = ConfigObj(path)
        self.value = AppConfig(
            database_server = cfg['database']['server'],
            database_name   = cfg['database']['database'],
            database_user   = cfg['database']['user'],
            database_password = cfg['database']['password'],
            api_base_url    = cfg['api'].get('base_url','https://financialmodelingprep.com/stable').rstrip('/'),
            api_key         = cfg['api']['key'],
            log_level       = cfg['logging'].get('log_level','INFO').upper(),
            log_file        = cfg['logging']['log_file']
        )
```

**Pros:** immutability, IDE auto-complete, clear types.  
**Cons:** access is `cfg.value.api_key` (one extra hop).

---

## Recommendation

Stick with `@property` for **clean, read-only, validated** access.  
If you need speed or immutable snapshots, use `cached_property` or a `dataclass`.  
All three patterns are good — choose the one that best matches your team’s style and operational needs.
